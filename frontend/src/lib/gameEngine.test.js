import { SpaceWar, puzzleBoard, shuffled } from './gameEngine';
import fixtures from './gameEngine.fixtures.json';
test.each(fixtures)('browser simulation matches server replay seed $seed', fixture => {
  const engine = new SpaceWar(fixture.seed, fixture.config);
  for (let tick = 0; tick < fixture.ticks; tick++) engine.step(tick < 40 ? -1 : tick < 120 ? 1 : 0);
  ['tick', 'y', 'lives', 'kills', 'serial'].forEach(field => expect(engine[field]).toBe(fixture[field === 'tick' ? 'ticks' : field]));
  expect(engine.enemies).toEqual(fixture.enemies); expect(engine.bullets).toEqual(fixture.bullets);
  expect(puzzleBoard(fixture.seed, 3, 4)).toEqual(fixture.board);
  expect(shuffled(fixture.seed, [...Array(8).keys(), ...Array(8).keys()])).toEqual(fixture.deck);
});
test('round ends at configured time or reward ceiling', () => {
  const timed = new SpaceWar(1, { max_duration_seconds: 10, max_points: 0, points_per_unit: 1 });
  for (let i = 0; i < 400; i++) timed.step(0);
  expect(timed.done).toBe(true); expect(timed.tick).toBe(300);
  const capped = new SpaceWar(1, { max_duration_seconds: 600, max_points: 1, points_per_unit: 1 });
  capped.enemies.push({ id: 1, x: 2795, y: 5000, kind: 0, dead: false }); capped.step(0);
  expect(capped.kills).toBe(1); expect(capped.done).toBe(true);
});
