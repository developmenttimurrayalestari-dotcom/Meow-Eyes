import React, { useEffect, useRef, useState } from 'react';
import { SpaceWar } from '../../lib/gameEngine';

const ROOT = '/games/space-war/';
export default function SpaceWarGame({ round, onFinish }) {
  const canvasRef = useRef(null), direction = useRef(0), finish = useRef(onFinish), [hud, setHud] = useState({ lives: 3, points: 0, seconds: 0 });
  finish.current = onFinish;
  useEffect(() => {
    let active = true, raf, timer, ready = false;
    const engine = new SpaceWar(round.seed, round.snapshot), commands = [];
    const images = {};
    Promise.all(['meow-pilot', 'aliens-explosions', 'ui-laser', 'galaxy'].map(name => new Promise(resolve => {
      const img = new Image(); img.onload = () => resolve(); img.onerror = () => resolve(); img.src = `${ROOT}${name}.png`; images[name] = img;
    }))).then(() => { ready = true; });
    const key = e => { if (['ArrowUp', 'ArrowDown', 'w', 'W', 's', 'S'].includes(e.key)) { e.preventDefault(); direction.current = e.type === 'keyup' ? 0 : ['ArrowUp', 'w', 'W'].includes(e.key) ? -1 : 1; } };
    const blur = () => { direction.current = 0; };
    window.addEventListener('keydown', key); window.addEventListener('keyup', key); window.addEventListener('blur', blur);
    const sprite = (ctx, name, cell, x, y, w, h) => {
      const img = images[name]; if (!img?.complete || !img.naturalWidth) return;
      if (cell == null) ctx.drawImage(img, x - w / 2, y - h / 2, w, h);
      else ctx.drawImage(img, (cell % 3) * 512, Math.floor(cell / 3) * 512, 512, 512, x - w / 2, y - h / 2, w, h);
    };
    const render = () => {
      if (!active) return;
      const ctx = canvasRef.current?.getContext('2d');
      if (ctx) {
        const w = 1280, h = 800, bg = images.galaxy; ctx.fillStyle = '#06152f'; ctx.fillRect(0, 0, w, h);
        if (bg?.complete && bg.naturalWidth) {
          const width = h * bg.naturalWidth / bg.naturalHeight, offset = engine.tick * 1.5 % (width * 2);
          for (let i = -1; i < 3; i++) { ctx.save(); ctx.translate(i * width - offset, 0); if (i % 2) { ctx.translate(width, 0); ctx.scale(-1, 1); } ctx.drawImage(bg, 0, 0, width, h); ctx.restore(); }
        }
        ctx.fillStyle = '#d4f5ff'; for (let i = 0; i < 30; i++) { const x = (i * 317 - engine.tick * (2 + i % 3)) % w; ctx.fillRect((x + w) % w, (i * 193) % h, 2, 2); }
        engine.bullets.forEach(b => sprite(ctx, 'ui-laser', 3, b.x * .08, b.y * .08, 110, 28));
        engine.enemies.forEach(e => sprite(ctx, 'aliens-explosions', e.kind, e.x * .08, e.y * .08, 125, 125));
        engine.explosions.forEach(e => sprite(ctx, 'aliens-explosions', 3 + Math.min(2, Math.floor((engine.tick - e.tick) / 6)), e.x * .08, e.y * .08, 140, 140));
        if (engine.tick >= engine.invulnerable || engine.tick % 4 < 2) sprite(ctx, 'meow-pilot', null, 144, engine.y * .08, 170, 85);
      }
      raf = requestAnimationFrame(render);
    };
    timer = setInterval(() => {
      if (!ready || engine.done || !active) return;
      const previous = commands.at(-1)?.d ?? 0;
      if (direction.current !== previous) commands.push({ t: engine.tick, d: direction.current });
      engine.step(direction.current);
      if (engine.tick % 3 === 0 || engine.done) setHud({ lives: engine.lives, points: Math.min(round.snapshot.max_points, engine.kills * round.snapshot.points_per_unit), seconds: Math.floor(engine.tick / 30) });
      if (engine.done) { clearInterval(timer); finish.current({ ticks: engine.tick, commands }); }
    }, 1000 / 30);
    render();
    return () => { active = false; clearInterval(timer); cancelAnimationFrame(raf); direction.current = 0; window.removeEventListener('keydown', key); window.removeEventListener('keyup', key); window.removeEventListener('blur', blur); };
  }, [round.id, round.seed, round.snapshot]);
  const button = (value, label, cell) => <button type="button" aria-label={label} className="space-control touch-none select-none"
    onPointerDown={e => { e.preventDefault(); e.currentTarget.setPointerCapture(e.pointerId); direction.current = value; }} onPointerUp={() => { direction.current = 0; }} onPointerCancel={() => { direction.current = 0; }} onLostPointerCapture={() => { direction.current = 0; }}>
    <span className="space-ui-sprite" style={{ backgroundImage: `url(${ROOT}ui-laser.png)`, backgroundPosition: `${cell * 50}% 0` }} /><span className="sr-only">{label}</span>
  </button>;
  return <div>
    <div className="space-war-stage" data-testid="space-war-stage">
      <canvas ref={canvasRef} width="1280" height="800" aria-label="Meow Space War. Gerakkan pesawat ke atas dan bawah untuk menghindari alien." />
      <div className="absolute top-3 inset-x-3 flex justify-between gap-2 text-white font-bold text-sm sm:text-lg pointer-events-none">
        <span className="space-hud flex items-center gap-1" aria-label={`${hud.lives} nyawa`}>{[0, 1, 2].map(i => <span key={i} style={{ backgroundImage: `url(${ROOT}ui-laser.png)` }} className={`space-heart ${i >= hud.lives ? 'opacity-20' : ''}`} />)}</span>
        <span className="space-hud">POIN {hud.points} / {round.snapshot.max_points}</span><span className="space-hud">{hud.seconds}s / {round.snapshot.max_duration_seconds}s</span>
      </div>
      <div className="absolute bottom-3 left-3 flex flex-col gap-1">{button(-1, 'Atas', 1)}{button(1, 'Bawah', 2)}</div>
    </div>
    <p className="text-xs text-meow-gray mt-3">Panah atas/bawah atau W/S · Laser otomatis · 3 nyawa. Alien makin cepat dan semakin banyak. Batas waktu atau poin mengakhiri ronde.</p>
  </div>;
}
