"""Deterministic integer game replay; the browser never decides wallet rewards."""
from fastapi import HTTPException

class Random:
    def __init__(self, seed): self.state = seed & 0xffffffff
    def next(self):
        self.state = (self.state * 1664525 + 1013904223) & 0xffffffff
        return self.state

def shuffled(seed, values):
    rng, deck = Random(seed), list(values)
    for i in range(len(deck) - 1, 0, -1):
        j = rng.next() % (i + 1); deck[i], deck[j] = deck[j], deck[i]
    return deck

def puzzle_board(seed, rows, columns):
    board, empty, previous = list(range(1, rows * columns)) + [0], rows * columns - 1, -1
    rng = Random(seed)
    for _ in range(rows * columns * 8):
        adjacent = [i for i in range(len(board)) if abs(i // columns - empty // columns) + abs(i % columns - empty % columns) == 1 and i != previous]
        chosen = adjacent[rng.next() % len(adjacent)]
        board[empty], board[chosen] = board[chosen], board[empty]
        previous, empty = empty, chosen
    if board == list(range(1, len(board))) + [0]:
        board[empty], board[empty - 1] = board[empty - 1], board[empty]
    return board

def replay_matching(seed, moves):
    deck = shuffled(seed, list(range(8)) * 2)
    matched, first, pairs = set(), None, 0
    for index in moves:
        if type(index) is not int or not 0 <= index < 16 or index in matched or first == index:
            raise HTTPException(422, 'Urutan kartu tidak valid')
        if first is None: first = index
        else:
            pairs += 1
            if deck[first] == deck[index]: matched.update((first, index))
            first = None
    return len(matched) == 16, max(0, 1000 - pairs * 10), 8 if len(matched) == 16 else 0

def replay_puzzle(seed, level, moves):
    rows, columns = level['rows'], level['columns']
    board = puzzle_board(seed, rows, columns); empty = board.index(0)
    for index in moves:
        if type(index) is not int or not 0 <= index < len(board) or abs(index // columns - empty // columns) + abs(index % columns - empty % columns) != 1:
            raise HTTPException(422, 'Langkah puzzle tidak valid')
        board[empty], board[index] = board[index], board[empty]; empty = index
    solved = board == list(range(1, len(board))) + [0]
    return solved, max(0, 5000 - len(moves)), level['level'] if solved else 0

class SpaceWar:
    def __init__(self, seed, config):
        self.rng, self.config = Random(seed), config
        self.tick, self.y, self.lives, self.kills, self.invulnerable = 0, 5000, 3, 0, 0
        self.bullets, self.enemies, self.explosions = [], [], []
        self.serial, self.done = 0, False

    def step(self, direction):
        if self.done: return
        self.y = max(600, min(9400, self.y + direction * 110))
        if self.tick % 6 == 0: self.bullets.append({'x': 2450, 'y': self.y, 'dead': False})
        period = max(8, 45 - (self.tick // 900) * 5)
        if self.tick % period == 0:
            for index in range(min(1 + self.tick // 1800, 5)):
                self.serial += 1
                self.enemies.append({'id': self.serial, 'x': 16600 + index * 800, 'y': 800 + self.rng.next() % 8400, 'kind': self.rng.next() % 3, 'dead': False})
        for bullet in self.bullets: bullet['x'] += 280
        for enemy in self.enemies: enemy['x'] -= 65 + (self.tick // 900) * 18
        for enemy in self.enemies:
            for bullet in self.bullets:
                if not enemy['dead'] and not bullet['dead'] and abs(enemy['x'] - bullet['x']) <= 420 and abs(enemy['y'] - bullet['y']) <= 380:
                    enemy['dead'], bullet['dead'] = True, True; self.kills += 1
                    self.explosions.append({'x': enemy['x'], 'y': enemy['y'], 'tick': self.tick})
        for enemy in self.enemies:
            if not enemy['dead'] and self.tick >= self.invulnerable and abs(enemy['x'] - 1800) < 650 and abs(enemy['y'] - self.y) < 580:
                enemy['dead'] = True; self.lives -= 1; self.invulnerable = self.tick + 24
        self.bullets = [row for row in self.bullets if not row['dead'] and row['x'] < 17000]
        self.enemies = [row for row in self.enemies if not row['dead'] and row['x'] > -1000]
        self.explosions = [row for row in self.explosions if self.tick - row['tick'] < 18]
        self.tick += 1
        self.done = self.lives <= 0 or self.tick >= self.config['max_duration_seconds'] * 30 or (self.config['max_points'] > 0 and self.kills * self.config['points_per_unit'] >= self.config['max_points'])

def replay_space(seed, config, transcript):
    ticks, commands = transcript.get('ticks'), transcript.get('commands')
    if type(ticks) is not int or not 1 <= ticks <= config['max_duration_seconds'] * 30 or not isinstance(commands, list) or len(commands) > 4000:
        raise HTTPException(422, 'Rekaman permainan tidak valid')
    events, previous = {}, -1
    for command in commands:
        if not isinstance(command, dict) or type(command.get('t')) is not int or not previous < command['t'] < ticks or type(command.get('d')) is not int or command['d'] not in (-1, 0, 1):
            raise HTTPException(422, 'Rekaman kontrol tidak valid')
        previous = command['t']; events[previous] = command['d']
    engine, direction = SpaceWar(seed, config), 0
    for tick in range(ticks):
        if engine.done: raise HTTPException(422, 'Rekaman berlanjut setelah ronde selesai')
        direction = events.get(tick, direction); engine.step(direction)
    if not engine.done: raise HTTPException(422, 'Ronde belum berakhir')
    return engine.kills, min(config['max_points'], engine.kills * config['points_per_unit']), ticks / 30
