from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
result = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', '20261112_0009:20261112_0010', '--sql'], cwd=root, capture_output=True, text=True, check=True)
(root/'sql/010_lens_index_types.sql').write_text(result.stdout, encoding='utf-8')
print('Incremental SQL exported for revision 20261112_0010')
