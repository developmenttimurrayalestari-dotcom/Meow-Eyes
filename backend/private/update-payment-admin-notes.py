from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'frontend/src/pages/admin/AdminIntegrations.jsx'
s = p.read_text(encoding='utf-8')
old = '<p className="text-xs text-meow-gray">Status ini memeriksa konfigurasi.'
new = '{item.configuration_error && <p role="alert" className="text-sm text-red-600">{item.configuration_error}</p>}{item.configuration_notes?.map(note => <p key={note} className="text-sm text-amber-700">{note}</p>)}<p className="text-xs text-meow-gray">Status ini memeriksa konfigurasi.'
assert old in s
p.write_text(s.replace(old, new), encoding='utf-8')
