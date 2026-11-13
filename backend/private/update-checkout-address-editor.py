from pathlib import Path
root = Path(__file__).resolve().parents[2]
p = root / 'frontend/src/pages/CheckoutPage.jsx'
s = p.read_text(encoding='utf-8')
changes = [
    ('onClick={() => setShowAddForm(!showAddForm)}', 'onClick={() => { setEditingAddress(null); setShowAddForm(!showAddForm); setShipping(null); setPreview(null); if (showAddForm) setShippingReload(value => value + 1); }}'),
    ('<AddressForm defaultAddress={!addresses.length} onCancel={() => setShowAddForm(false)} onSaved={(address) => { setAddresses((items) => [...items.map((item) => address.is_default ? { ...item, is_default: false } : item), address]); setAddressId(address.id); setShowAddForm(false); }} />', '<AddressForm key={editingAddress?.id || \'new\'} initialAddress={editingAddress} defaultAddress={!addresses.length} onCancel={() => { setShowAddForm(false); setEditingAddress(null); setShippingReload(value => value + 1); }} onSaved={(address) => { setAddresses((items) => [...items.filter(item => item.id !== address.id).map((item) => address.is_default ? { ...item, is_default: false } : item), address]); setAddressId(address.id); setShowAddForm(false); setEditingAddress(null); setShipping(null); setPreview(null); setShippingReload(value => value + 1); }} />'),
    ('addresses.map((address) => <label key={address.id}', 'addresses.map((address) => <div key={address.id}'),
    ('<input type="radio" name="checkout-address"', '<label className="flex items-start gap-2 flex-1 min-w-0"><input type="radio" name="checkout-address"'),
    ('</span></span>\n              </label>)', '</span></span></label><button type="button" disabled={submitting} data-testid={`checkout-edit-address-${address.id}`} onClick={() => { setEditingAddress(address); setShowAddForm(true); setShipping(null); setPreview(null); }} className="text-xs font-bold text-meow-salmon self-start">Ubah</button>\n              </div>)'),
]
for old, new in changes:
    assert old in s, old[:100]
    s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
