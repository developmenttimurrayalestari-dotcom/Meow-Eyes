"""Read-only MongoDB export; credentials come exclusively from the process environment."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'private' / 'mongo-export-tools'))
from bson import json_util
from pymongo import MongoClient


def main():
    tree = ast.parse((ROOT / 'mysql' / 'importer.py').read_text(encoding='utf-8'))
    mapping = next(ast.literal_eval(node.value) for node in tree.body
                   if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'COLLECTION_TABLES' for t in node.targets))
    expected = sorted(mapping)
    with MongoClient(os.environ['MONGO_EXPORT_URI'], serverSelectionTimeoutMS=20000,
                     connectTimeoutMS=15000, appname='meoweyes-readonly-json-export') as client:
        client.admin.command('ping')
        inventories = {}
        for name in client.list_database_names():
            if name not in {'admin', 'local', 'config'}:
                inventories[name] = sorted(client[name].list_collection_names())
        if '--export' not in sys.argv:
            print(json.dumps({'databases': {name: {'collections': cols,
                  'matched_expected': len(set(cols) & set(expected))}
                  for name, cols in inventories.items()}}, indent=2), flush=True)
            return
        database_name = os.environ['MONGO_EXPORT_DATABASE']
        present = set(inventories[database_name])
        destination = ROOT / 'private' / 'export-meow'
        destination.mkdir(parents=True, exist_ok=True)
        if any(destination.iterdir()):
            raise RuntimeError('Export destination must be empty; existing files will not be overwritten')
        report = {'database': database_name, 'started_at': datetime.now(timezone.utc).isoformat(),
                  'format': 'Extended JSON v2 canonical array', 'collections': {},
                  'extra_source_collections': sorted(present - set(expected)),
                  'consistent_snapshot_guaranteed': False, 'status': 'running'}
        report_path = ROOT / 'private' / 'mongo-export-manifest.json'
        for name in expected:
            partial = destination / (name + '.json.part')
            count = 0
            with partial.open('x', encoding='utf-8', newline='\n') as handle:
                handle.write('[\n')
                with client[database_name][name].find({}).batch_size(200) as cursor:
                    for document in cursor:
                        if count:
                            handle.write(',\n')
                        handle.write(json_util.dumps(document, json_options=json_util.CANONICAL_JSON_OPTIONS,
                                                     ensure_ascii=False))
                        count += 1
                handle.write('\n]\n')
            source_count = client[database_name][name].count_documents({})
            if source_count != count:
                raise RuntimeError('Source count changed during export: ' + name)
            target = destination / (name + '.json')
            partial.rename(target)
            report['collections'][name] = {'documents': count, 'source_collection_exists': name in present,
                'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
            report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({'collection': name, 'documents': count, 'source_collection_exists': name in present}), flush=True)
        report['status'] = 'completed'
        report['completed_at'] = datetime.now(timezone.utc).isoformat()
        report['total_documents'] = sum(item['documents'] for item in report['collections'].values())
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': 'completed', 'files': len(expected), 'documents': report['total_documents']}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Driver error text can include connection details; never emit it.
        print(json.dumps({'status': 'failed', 'error_type': type(exc).__name__,
                          'code': getattr(exc, 'code', None)}), flush=True)
        sys.exit(2)
