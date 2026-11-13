// Integer simulation shared by the rendered game and server replay contract.
export class Random {
  constructor(seed) { this.state = seed >>> 0; }
  next() { this.state = (Math.imul(this.state, 1664525) + 1013904223) >>> 0; return this.state; }
}
export function shuffled(seed, values) {
  const rng = new Random(seed), deck = [...values];
  for (let i = deck.length - 1; i > 0; i--) { const j = rng.next() % (i + 1); [deck[i], deck[j]] = [deck[j], deck[i]]; }
  return deck;
}
export function puzzleBoard(seed, rows, columns) {
  const board = Array.from({ length: rows * columns }, (_, i) => (i + 1) % (rows * columns)), rng = new Random(seed);
  let empty = board.length - 1, previous = -1;
  for (let turn = 0; turn < rows * columns * 8; turn++) {
    const adjacent = board.map((_, i) => i).filter(i => Math.abs(Math.floor(i / columns) - Math.floor(empty / columns)) + Math.abs(i % columns - empty % columns) === 1 && i !== previous);
    const chosen = adjacent[rng.next() % adjacent.length];
    [board[empty], board[chosen]] = [board[chosen], board[empty]]; previous = empty; empty = chosen;
  }
  if (board.every((v, i) => v === (i + 1) % board.length)) [board[empty], board[empty - 1]] = [board[empty - 1], board[empty]];
  return board;
}
export class SpaceWar {
  constructor(seed, config) {
    this.rng = new Random(seed); this.config = config;
    Object.assign(this, { tick: 0, y: 5000, lives: 3, kills: 0, invulnerable: 0, serial: 0, done: false, bullets: [], enemies: [], explosions: [] });
  }
  step(direction) {
    if (this.done) return;
    this.y = Math.max(600, Math.min(9400, this.y + direction * 110));
    if (this.tick % 6 === 0) this.bullets.push({ x: 2450, y: this.y, dead: false });
    const period = Math.max(8, 45 - Math.floor(this.tick / 900) * 5);
    if (this.tick % period === 0) for (let i = 0; i < Math.min(1 + Math.floor(this.tick / 1800), 5); i++) this.enemies.push({ id: ++this.serial, x: 16600 + i * 800, y: 800 + this.rng.next() % 8400, kind: this.rng.next() % 3, dead: false });
    this.bullets.forEach(b => { b.x += 280; }); this.enemies.forEach(e => { e.x -= 65 + Math.floor(this.tick / 900) * 18; });
    for (const e of this.enemies) for (const b of this.bullets) if (!e.dead && !b.dead && Math.abs(e.x - b.x) <= 420 && Math.abs(e.y - b.y) <= 380) {
      e.dead = true; b.dead = true; this.kills++; this.explosions.push({ x: e.x, y: e.y, tick: this.tick });
    }
    for (const e of this.enemies) if (!e.dead && this.tick >= this.invulnerable && Math.abs(e.x - 1800) < 650 && Math.abs(e.y - this.y) < 580) { e.dead = true; this.lives--; this.invulnerable = this.tick + 24; }
    this.bullets = this.bullets.filter(b => !b.dead && b.x < 17000); this.enemies = this.enemies.filter(e => !e.dead && e.x > -1000);
    this.explosions = this.explosions.filter(e => this.tick - e.tick < 18); this.tick++;
    this.done = this.lives <= 0 || this.tick >= this.config.max_duration_seconds * 30 || (this.config.max_points > 0 && this.kills * this.config.points_per_unit >= this.config.max_points);
  }
}
