import hashlib
import json
from pathlib import Path
import re
import httpx

response = httpx.get('http://127.0.0.1:3000/static/js/bundle.js', timeout=20)
text = response.text
start = text.find('/***/ "./src/components/PrescriptionForm.jsx":')
module = text[start:text.find('\n/***/ "', start + 10)] if start >= 0 else ''
result = {'status': response.status_code, 'prescription_module_found': bool(module), 'bytes': len(text)}
for marker in ('lens-options', 'lens_index_id', 'Resep belum berhasil disimpan.', 'cart_item'):
    result[marker] = marker in module
encoded = re.search(r'sourceMappingURL=data:application/json[^,]*;base64,([A-Za-z0-9+/=]+)', module)
if encoded:
    import base64
    mapping = json.loads(base64.b64decode(encoded[1]))
    source = mapping.get('sourcesContent', [''])[0].replace('\r\n', '\n')
    disk = (Path(__file__).resolve().parents[2]/'frontend/src/components/PrescriptionForm.jsx').read_text(encoding='utf-8').replace('\r\n', '\n')
    result['source_matches_workspace'] = source.strip() == disk.strip()
    result['bundle_source_hash'] = hashlib.sha256(source.encode()).hexdigest()
if module:
    (Path(__file__).parent/'rx-browser-bundle-module.txt').write_text(module, encoding='utf-8')
print(json.dumps(result))
