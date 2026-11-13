import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import AdminInventory from './AdminInventory';
import {api} from '../../lib/api';
jest.mock('../../lib/api',()=>({api:{get:jest.fn(),post:jest.fn()},apiError:(e,fallback)=>e.response?.data?.detail||fallback}));
jest.mock('sonner',()=>({toast:{success:jest.fn()}}));
let host,root;
const item={product_id:'new',variant_id:null,sku:'NEW',name:'New frame',variant_label:'-',stock:0,reserved:0,min_alert:5,can_adjust:true};
const click=async node=>act(async()=>node.click());
const type=async(node,value)=>act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(node,value);node.dispatchEvent(new Event('input',{bubbles:true}));});
beforeEach(()=>{jest.clearAllMocks();api.get.mockResolvedValue({data:{items:[item],deleted_items:[{...item,product_id:'old',name:'Deleted frame',deleted_at:'2026-11-12',can_adjust:false}]}});api.post.mockResolvedValue({data:{ok:true}});host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();});
test('initial stock uses receipt type, positive quantity, TTB and the selected variant ID',async()=>{
 await act(async()=>root.render(<AdminInventory/>));
 await click(host.querySelector('[data-testid="inv-adjust-0"]'));
 await type(host.querySelector('[data-testid="inv-ttb"]'),' TTB-001 ');
 await type(host.querySelector('[data-testid="inv-quantity"]'),'5');
 await act(async()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
 expect(api.post).toHaveBeenCalledWith('/admin/products/new/stock',{variant_id:null,adjustment_type:'receipt_stock',quantity:5,ttb_number:'TTB-001',note:''});
 expect(host.querySelector('[role="dialog"]')).toBeNull();
});
test('deleted product rows are grey and disabled in a separate table',async()=>{
 await act(async()=>root.render(<AdminInventory/>));
 const row=host.querySelector('[data-testid="inv-deleted-row-0"]');
 expect(row.className).toContain('bg-zinc-100');expect(row.getAttribute('aria-disabled')).toBe('true');
 expect(row.querySelector('button').disabled).toBe(true);
 expect(host.querySelector('[data-testid="inventory-table"]').textContent).not.toContain('Deleted frame');
});
test('legacy backend responses show a restart instruction instead of mixing deleted stock into the active table',async()=>{
 api.get.mockResolvedValue({data:{items:[item]}});
 await act(async()=>root.render(<AdminInventory/>));
 expect(host.querySelector('[role="alert"]').textContent).toContain('Restart backend');
 expect(host.querySelectorAll('tbody tr')).toHaveLength(0);
});
test('TTB and available stock are validated without losing the form on failure',async()=>{
 await act(async()=>root.render(<AdminInventory/>));await click(host.querySelector('[data-testid="inv-adjust-0"]'));
 await type(host.querySelector('[data-testid="inv-quantity"]'),'3');
 await act(async()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
 expect(host.querySelector('[role="alert"]').textContent).toContain('TTB');expect(api.post).not.toHaveBeenCalled();
 await type(host.querySelector('[data-testid="inv-ttb"]'),'TTB');
 await act(async()=>{const select=host.querySelector('select');select.value='issue_stock';select.dispatchEvent(new Event('change',{bubbles:true}));});
 await act(async()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
 expect(host.querySelector('[role="alert"]').textContent).toContain('melebihi');expect(api.post).not.toHaveBeenCalled();
});
