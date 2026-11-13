import json
from pathlib import Path
from mysql.game_engine import SpaceWar, puzzle_board, shuffled
fixtures=[]
for seed in (1,123456,4294967295):
    config={'max_duration_seconds':180,'max_points':50,'points_per_unit':2}
    engine=SpaceWar(seed,config)
    for tick in range(1400):
        if engine.done:break
        engine.step(-1 if tick<40 else 1 if tick<120 else 0)
    fixtures.append({'seed':seed,'config':config,'ticks':engine.tick,'y':engine.y,'lives':engine.lives,'kills':engine.kills,'serial':engine.serial,
        'enemies':engine.enemies,'bullets':engine.bullets,'board':puzzle_board(seed,3,4),'deck':shuffled(seed,list(range(8))*2)})
Path('../frontend/src/lib/gameEngine.fixtures.json').write_text(json.dumps(fixtures,indent=2),encoding='utf-8')
print('Wrote cross-language simulation fixtures')
