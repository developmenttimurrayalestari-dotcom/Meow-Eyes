"""Validate local Lucide identifiers. Arbitrary SVG/HTML is never accepted."""
import json
from pathlib import Path

LUCIDE_NAMES=frozenset(json.loads((Path(__file__).parent/'data/lucide-icon-names.json').read_text(encoding='utf-8'))['names'])
CARD_ALIASES=frozenset({'none','frame','lens','package','sparkles','tag'})
MENU_ALIASES=frozenset({'none','home','shop','games','cart','profile','sparkles','glasses','article','tag','flash','contact'})

def validate_icon(value,aliases):
    if value in aliases or value.startswith('lucide:') and value[7:] in LUCIDE_NAMES:
        return value
    raise ValueError('Pilih ikon dari koleksi Lucide yang tersedia')
