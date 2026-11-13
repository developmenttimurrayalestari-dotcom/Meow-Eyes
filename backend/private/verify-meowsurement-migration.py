"""Compare all table counts against the completed private SQL backup."""
import asyncio
import json
from pathlib import Path
import runpy

directory = Path(__file__).resolve().parent
before_path = directory / 'backups/meowsurement-before-0004-20261110T040509Z.json'
before = json.loads(before_path.read_text(encoding='utf-8'))
namespace = runpy.run_path(str(directory / 'backup-meowsurement-migration.py'))
_, after = asyncio.run(namespace['counts']('20261110_0004'))
changes = {name: {'before': before['before_row_counts'].get(name), 'after': after.get(name)}
           for name in set(before['before_row_counts']) | set(after)
           if before['before_row_counts'].get(name) != after.get(name)}
result = {'ok': not changes, 'before_revision': before['before_revision'], 'after_revision': '20261110_0004',
          'application_table_count': len(after) - 1, 'table_counts_unchanged': not changes,
          'changed_counts': changes, 'after_row_counts': after, 'backup': before['backup']}
output = directory / 'backups/meowsurement-after-0004-20261110T040509Z.json'
output.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key != 'after_row_counts'}))
if changes:
    raise SystemExit(1)
