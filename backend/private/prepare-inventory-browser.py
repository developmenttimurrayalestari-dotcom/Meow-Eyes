from pathlib import Path
p=Path('private/product-actions-browser-smoke.cjs').read_text(encoding='utf-8')
a=p.index('const initial=')
b=p.index('(async()=>',a)
p=p[:a]+"""const initial=()=>[
 {product_id:'new',variant_id:null,sku:'NEW',name:'Frame Baru',variant_label:'-',stock:0,reserved:0,min_alert:5,product_active:true,variant_active:true,can_adjust:true},
 {product_id:'existing',variant_id:'v-existing',sku:'EXISTING',name:'Frame Existing',variant_label:'Hitam',stock:10,reserved:2,min_alert:5,product_active:true,variant_active:true,can_adjust:true}
];
"""+p[b:]
needle="if(endpoint==='/admin/products'){"
p=p.replace(needle,"""if(endpoint==='/admin/inventory')data={items:products,deleted_items:[{...initial()[1],product_id:'deleted',name:'Frame dihapus',deleted_at:'2026-11-12',can_adjust:false}]};
   if(endpoint.endsWith('/stock')&&req.method()==='POST'){
    const body=req.postDataJSON();calls.push(body);
    const id=endpoint.split('/')[3],item=products.find(p=>p.product_id===id);
    item.stock+=body.adjustment_type==='receipt_stock'?body.quantity:-body.quantity;
    item.variant_id=item.variant_id||'v-new';data={ok:true,stock:item.stock,variant_id:item.variant_id};
   }
   """+needle)
a=p.index('  const url=')
b=p.index('  assert.deepEqual(errors,[]);',a)
p=p[:a]+"""  const url=`http://127.0.0.1:${server.address().port}/admin/inventory`;
  await page.goto(url);await page.getByTestId('inv-row-0').waitFor();
  assert.equal(await page.getByTestId('inventory-table').locator('tbody tr').count(),2);
  assert(await page.getByTestId('inv-deleted-adjust-0').isDisabled());
  assert((await page.getByTestId('inv-deleted-row-0').getAttribute('class')).includes('bg-zinc-100'));
  await page.getByTestId('inv-adjust-0').click();
  await page.getByLabel('Nomor TTB',{exact:true}).fill('TTB-001');
  await page.getByLabel('Jumlah',{exact:true}).fill('8');
  await page.screenshot({path:path.join(__dirname,'inventory-receipt-desktop.png')});
  await page.getByTestId('inv-save').click();await page.getByRole('dialog').waitFor({state:'hidden'});
  assert.deepEqual(calls.at(-1),{variant_id:null,adjustment_type:'receipt_stock',quantity:8,ttb_number:'TTB-001',note:''});report.initialReceipt=true;
  await page.getByTestId('inv-adjust-0').click();
  await page.getByLabel('Jenis Adjust Stock',{exact:true}).selectOption('issue_stock');
  await page.getByLabel('Nomor TTB',{exact:true}).fill('TTB-002');await page.getByLabel('Jumlah',{exact:true}).fill('3');
  await page.getByTestId('inv-save').click();await page.getByRole('dialog').waitFor({state:'hidden'});
  assert.equal(calls.at(-1).variant_id,'v-new');assert.equal(calls.at(-1).adjustment_type,'issue_stock');assert.equal(products[0].stock,5);report.issueStock=true;
  await page.screenshot({path:path.join(__dirname,'inventory-tables-desktop.png')});
  await page.setViewportSize({width:390,height:844});await page.getByTestId('inv-adjust-0').click();
  await page.screenshot({path:path.join(__dirname,'inventory-receipt-mobile.png')});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));report.mobileForm=true;report.deletedDisabled=true;
"""+p[b:]
p=p.replace('product-actions-browser-report','inventory-browser-report')
Path('private/inventory-browser-smoke.cjs').write_text(p,encoding='utf-8')
print('Inventory browser checks prepared')
