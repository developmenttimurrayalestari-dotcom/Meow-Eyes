"""Server-issued rounds, cooldowns and deterministic reward verification."""
from datetime import timedelta
import secrets
from sqlalchemy import select
from fastapi import HTTPException
from . import models as m, points
from .base import utcnow
from .api import row_dict
from .game_engine import replay_matching, replay_puzzle, replay_space

async def definition(s, key, *, active=True):
    game = await s.scalar(select(m.Game).where(m.Game.key == key))
    rule = await s.get(m.GameRule, key)
    if not game or not rule or (active and not game.is_active):
        raise HTTPException(404, 'Permainan tidak tersedia')
    return game, rule

async def catalog(s, *, admin=False):
    rows = (await s.execute(select(m.Game, m.GameRule).join(m.GameRule, m.GameRule.game_key == m.Game.key).order_by(m.Game.created_at, m.Game.key))).all()
    return [{**row_dict(game), 'rule': row_dict(rule)} for game, rule in rows if admin or game.is_active]

async def start(s, user, key, level=1):
    game, rule = await definition(s, key)
    if rule.engine == 'roulette': raise HTTPException(422, 'Gunakan tombol Putar Roulette')
    now = utcnow()
    previous = await s.scalar(select(m.GameSession).where(m.GameSession.user_id == user.user_id, m.GameSession.game_key == key).order_by(m.GameSession.started_at.desc()).limit(1).with_for_update())
    if previous:
        if previous.status == 'active' and previous.expires_at > now: return row_dict(previous)
        if previous.status == 'active': previous.status, previous.active_slot = 'expired', None; await s.flush()
        remaining = int((previous.started_at + timedelta(seconds=rule.cooldown_seconds) - now).total_seconds())
        if remaining > 0: raise HTTPException(429, f'Bisa bermain kembali dalam {remaining} detik', headers={'Retry-After': str(remaining)})
    config = await points.settings(s)
    snapshot = {**row_dict(rule), 'name': game.name, 'rate': str(config.rate), 'rate_version': config.version}
    if rule.engine == 'slide_puzzle':
        chosen = await s.get(m.PuzzleLevel, level)
        if not chosen or not chosen.is_active: raise HTTPException(422, 'Level belum tersedia')
        snapshot['level'] = row_dict(chosen)
    round_ = m.GameSession(user_id=user.user_id, game_key=key, active_slot=user.user_id + ':' + key, seed=secrets.randbits(32),
        snapshot=snapshot, started_at=now, expires_at=now + timedelta(seconds=rule.max_duration_seconds + 60))
    s.add(round_); await s.flush()
    return row_dict(round_)

async def finish(s, user, session_id, transcript):
    round_ = await s.scalar(select(m.GameSession).where(m.GameSession.id == session_id, m.GameSession.user_id == user.user_id).with_for_update())
    if not round_: raise HTTPException(404, 'Ronde tidak ditemukan')
    if round_.status == 'completed': return {'ok': True, 'score': round_.score, 'points_awarded': round_.points_awarded}
    now = utcnow()
    if round_.status != 'active' or round_.expires_at < now: raise HTTPException(409, 'Ronde sudah kedaluwarsa')
    rule, minimum = round_.snapshot, 0
    if rule['engine'] == 'space_war': score, award, minimum = replay_space(round_.seed, rule, transcript)
    else:
        moves = transcript.get('moves')
        if not isinstance(moves, list) or len(moves) > 10000: raise HTTPException(422, 'Rekaman langkah tidak valid')
        solved, score, units = replay_matching(round_.seed, moves) if rule['engine'] == 'matching' else replay_puzzle(round_.seed, rule['level'], moves)
        if not solved: raise HTTPException(422, 'Permainan belum diselesaikan')
        minimum = max(1, len(moves) * .03)
        award = min(rule['max_points'], units * rule['points_per_unit'])
    elapsed = (now - round_.started_at).total_seconds()
    if elapsed + 1 < minimum or (rule['engine'] != 'space_war' and elapsed > rule['max_duration_seconds'] + 2):
        raise HTTPException(422, 'Durasi permainan tidak sesuai rekaman')
    round_.status, round_.active_slot, round_.completed_at = 'completed', None, now
    round_.score, round_.points_awarded, round_.transcript = score, award, transcript
    await points.credit(s, user, award, source='earn_game', key='game:' + round_.id, expiry_days=rule['expiry_days'],
        rate=rule['rate'], version=rule['rate_version'], note=rule['name'])
    s.add(m.GameScore(user_id=user.user_id, game=round_.game_key, score=score, points_awarded=award))
    await s.flush()
    return {'ok': True, 'score': score, 'points_awarded': award}
