from pathlib import Path

page_path = Path(__file__).resolve().parents[2] / 'frontend/src/pages/VirtualTryOnPage.jsx'
source = page_path.read_text(encoding='utf-8')
start = source.index('      <aside className="vto-catalog"')
end = source.index('      </aside>', start) + len('      </aside>')
catalog = source[start:end].strip()
source = source[:start] + source[end:]
marker = '  const productCard = selected &&'
assert source.count(marker) == 1
source = source.replace(marker, f'  const frameCatalog = {catalog};\n\n{marker}')
studio = '<TryOnStudio assets={studioAssets} name={selected.name} immersive stageOverlay={productCard} />'
assert studio in source
source = source.replace(studio, '<TryOnStudio assets={studioAssets} name={selected.name} immersive stageOverlay={productCard} stageFooter={frameCatalog} />')
fallback_start = ': <div className="vto-immersive-stage bg-white'
fallback_end = "}</div>}"
assert fallback_start in source
source = source.replace(fallback_start, ': <><div className="vto-immersive-stage bg-white')
assert source.count(fallback_end) == 1
source = source.replace(fallback_end, '}</div>{frameCatalog}</>}')
page_path.write_text(source, encoding='utf-8')
