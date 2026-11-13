"""Apply the three operator-approved SKU corrections to the local export only."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
path = root / 'export-meow' / 'products.json'
original = path.read_bytes()
products = json.loads(original)
changes = {
    'prd_f27e5e8e2c274d16': ('ME-MEOWOPTIK-', 'ME-MEOWOPTIK-VINTAGE'),
    'prd_898f994b888240ab': ('ME-KITTYCRAFT', 'ME-KITTYCRAFT-CUBBY'),
    'prd_cb46f21f4ef446f3': ('ME-ESSENSEEYE', 'ME-ESSENSEEYE-AIR'),
}
records = []
for product_id, (old, new) in changes.items():
    matches = [product for product in products if product.get('id') == product_id]
    assert len(matches) == 1, 'Expected exactly one matching product'
    product = matches[0]
    assert product['sku'] == old, 'Source SKU differs from approved correction'
    records.append({'id': product_id, 'name': product['name'], 'old_sku': old, 'new_sku': new})
    product['sku'] = new
assert len({product['sku'].strip().casefold() for product in products}) == len(products)
backup = root / 'export-original-backup' / 'products.json'
backup.parent.mkdir(parents=True, exist_ok=True)
with backup.open('xb') as handle:
    handle.write(original)
encoded = (json.dumps(products, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
# Prove that only the approved SKU fields changed before writing anything.
restored = json.loads(encoded)
for product in restored:
    if product.get('id') in changes:
        product['sku'] = changes[product['id']][0]
assert restored == json.loads(original)
path.write_bytes(encoded)
report = {'scope': 'local import copy only; original MongoDB unchanged',
          'original_backup': str(backup.relative_to(root)),
          'original_sha256': hashlib.sha256(original).hexdigest(),
          'corrected_sha256': hashlib.sha256(encoded).hexdigest(),
          'changes': records,
          'note': 'mongo-export-manifest.json describes the original export; products.json now has the corrected checksum recorded here.'}
(root / 'sku-corrections.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'corrected_products': len(records), 'only_approved_fields_changed': True}))
