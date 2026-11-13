"""Full private backup with existing revision verification; no secret logging."""
from pathlib import Path
base=Path(__file__).with_name('backup-meowsurement-migration.py')
source=base.read_text(encoding='utf-8').replace('20261109_0003','20261110_0004').replace('meowsurement-before-0004-','loyalty-before-0005-')
exec(compile(source,str(base),'exec'))
