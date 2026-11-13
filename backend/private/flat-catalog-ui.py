from pathlib import Path
p=Path('../frontend/src/pages/ProductsPage.jsx');t=p.read_text(encoding='utf-8')
t=t.replace('import ProductCard from','import MasterCatalogFilters from "../components/MasterCatalogFilters";\nimport ProductCard from',1)
a=t.index('const SEGMENTS =');b=t.index('    <div>\n      <p className="font-bold mb-2 text-xs uppercase tracking-wider text-meow-salmon">Brand',a)
t=t[:a]+'''const FilterPanel = ({ params, setParam, brands, categories, setMasterFilter }) => (
  <div className="space-y-6 text-sm">
    <MasterCatalogFilters categories={categories} params={params} onChange={setMasterFilter} />
'''+t[b:]
t=t.replace('  const [brands, setBrands] = useState([]);','  const [brands, setBrands] = useState([]);\n  const [masterCategories, setMasterCategories] = useState([]);\n  const [masterError, setMasterError] = useState("");',1)
anchor='  useEffect(() => {\n    const controller = new AbortController();'
i=t.index(anchor)
t=t[:i]+'''  const setMasterFilter = ids => {
    const next = new URLSearchParams(search);
    next.delete('product_type'); next.delete('segment');
    if (ids.length) next.set('category_ids', ids.join(',')); else next.delete('category_ids');
    next.set('page', '1'); setSearch(next);
  };
  useEffect(() => {
    const controller = new AbortController(); setMasterError('');
    api.get('/categories', { signal: controller.signal }).then(({ data }) => setMasterCategories(data.categories || []))
      .catch(e => { if (!controller.signal.aborted) setMasterError(apiError(e, 'Filter master belum dapat dimuat.')); });
    return () => controller.abort();
  }, [reload]);

'''+t[i:]
t=t.replace('<FilterPanel params={params} setParam={setParam} brands={brands} />','<FilterPanel params={params} setParam={setParam} brands={brands} categories={masterCategories} setMasterFilter={setMasterFilter} />')
t=t.replace('      {children}\n','''      {masterError && <p role="alert" className="bg-amber-50 p-3 rounded-xl my-3 text-sm">{masterError} <button className="underline" onClick={() => setReload(value => value + 1)}>Muat ulang filter</button></p>}
      {children}
''',1)
p.write_text(t,encoding='utf-8')
p=Path('../frontend/src/pages/admin/AdminFlashSales.jsx');t=p.read_text(encoding='utf-8').replace('include_descendants: true','include_descendants: false')
a=t.find('<label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={rule.include_descendants}')
if a>=0:
 b=t.index('</label>',a)+len('</label>');t=t[:a]+t[b:]
t=t.replace('Kategori dan subkategori','Grup master dan koleksi').replace('kategori dan subkategori','master dan koleksi')
p.write_text(t,encoding='utf-8')
