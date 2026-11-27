import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProductDetailPage from "./ProductDetailPage";
import { api } from "../lib/api";

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({ ...jest.requireActual("react-router-dom"), useNavigate: () => mockNavigate }));
jest.mock("../lib/api", () => ({ api: { get: jest.fn(), post: jest.fn(), patch: jest.fn() }, apiError: (err, fallback) => fallback, imageSrc: (value) => value, formatIDR: (value) => `Rp ${value}` }));
jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));
jest.mock("../contexts/AuthContext", () => ({ useAuth: () => ({ user: { user_id: "buyer" }, refreshCartCount: jest.fn() }) }));
jest.mock("../components/VirtualTryOn", () => ({productId}) => <div data-testid="product-try-on" data-product-id={productId} />);

let host, root, resolveFirst, resolveSecond;
const product = { id: "frame", slug: "frame", name: "Frame", price: 100, product_type: "frame", variants: [
  { id: "v1", sku: "SILVER", color: "Silver", stock: 10, reserved: 0, price_override: null },
  { id: "v2", sku: "BLACK", color: "Black", stock: 10, reserved: 0, price_override: 200 },
] };
const bundle = (variantId, total) => ({ data: { frame: { id: "frame", variant_id: variantId }, picks: [
  { tier: "basic", label: "Hemat",   frame_variant_id: variantId, lens_product_name: "Lensa", lens_index_id: "index", lens_index_name: "1.56", available: true, available_stock: 10, bundle_total: total, savings: 0 },
] } });
const click = async (node) => act(async () => node.dispatchEvent(new MouseEvent("click", { bubbles: true })));
beforeEach(() => {
  jest.clearAllMocks();
  host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host);
  const first = new Promise((resolve) => { resolveFirst = resolve; });
  const second = new Promise((resolve) => { resolveSecond = resolve; });
  api.get.mockImplementation((url, config) => {
    if (url === "/products/frame") return Promise.resolve({ data: { product, breadcrumb: [], reviews: [], related: [] } });
    if (url === "/products/frame/frame-specification") return Promise.resolve({ data: { specification: { a: 52, b: 38, dbl: 18, ed: 58, enabled: true }, variants: [{ variant_id: "v1", inherit_default: true }, { variant_id: "v2", inherit_default: false, specification: { a: 56, b: 40, dbl: 18, ed: 64, enabled: true } }] } });
    if(url.endsWith('/optical-options')) return Promise.resolve({data:{items:[
      {id:'clear161',name:'Clear 1.61',index_value:'1.61',additional_price:60000,lens_types:[{id:'t1',code:'clear',name:'Clear'}]},
      {id:'clear167',name:'Clear 1.67',index_value:'1.67',additional_price:90000,lens_types:[{id:'t1',code:'clear',name:'Clear'}]},
      {id:'uv161',name:'UV420 1.61',index_value:'1.61',additional_price:100000,lens_types:[{id:'t2',code:'uv420',name:'UV420'}]},
    ]}});
    if (url.startsWith("/lens/options")) return Promise.resolve({ data: { lens_products: [{ id: "lens", name: "Lensa", price: 80, discount_price: null, variants: [{ id: "lens-first", price_override: 30, stock: 10, reserved: 0 }] }], lens_indexes: [] } });
    if (url.startsWith("/lens/recommended")) return config.params.variant_id === "v2" ? second : first;
    return Promise.reject(new Error("Unexpected API"));
  });
  api.post.mockResolvedValue({ data: { ok: true } });
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
const mount = async (path='/products/frame') => act(async () => root.render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/products/:slug" element={<ProductDetailPage />} /></Routes></MemoryRouter>));

test('four active variants remain selectable and the fourth variant is used when adding to cart',async()=>{
  const variants=['Leopard','Mostgreen','Taupe','Grey'].map((color,index)=>({id:`v${index+1}`,sku:color.toUpperCase(),color,size:'M',stock:10,reserved:0,is_active:true}));
  const fallback=api.get.getMockImplementation();
  api.get.mockImplementation((url,config)=>url==='/products/frame'?Promise.resolve({data:{product:{...product,variants},breadcrumb:[],reviews:[],related:[]}}):fallback(url,config));
  await mount();
  expect(host.querySelectorAll('[data-testid="variant-list"] button')).toHaveLength(4);
  await click(host.querySelector('[data-testid="variant-GREY"]'));
  await click(host.querySelector('[data-testid="add-to-cart-btn"]'));
  await click(host.querySelector('[data-testid="addon-skip"]'));
  expect(api.post).toHaveBeenCalledWith('/cart',expect.objectContaining({product_id:'frame',variant_id:'v4',quantity:1}));
});


test.each([
  [['/green.png','/taupe.png','/grey.png'],['/leopard.png','/green.png','/taupe.png','/grey.png']],
  [['/leopard.png','/green.png','/leopard.png',''],['/leopard.png','/green.png']],
  [[],['/leopard.png']],
])('product gallery includes its main image and distinct additional photos (%j)',async(gallery,expected)=>{
  const fallback=api.get.getMockImplementation();
  api.get.mockImplementation((url,config)=>url==='/products/frame'?Promise.resolve({data:{product:{...product,main_image:'/leopard.png',gallery},breadcrumb:[],reviews:[],related:[]}}):fallback(url,config));
  await mount();
  expect([...host.querySelectorAll('[data-testid="gallery-thumbs"] img')].map(img=>img.getAttribute('src'))).toEqual(expected);
  await click(host.querySelector(`[data-testid="thumb-${expected.length-1}"]`));
  expect(host.querySelector('[data-testid="gallery-main"] img').getAttribute('src')).toBe(expected[expected.length-1]);
});


test.each(['frame','package','lens'])('product detail VTO eligibility for %s',async kind=>{
  const fallback=api.get.getMockImplementation();
  api.get.mockImplementation((url,config)=>url==='/products/frame'?Promise.resolve({data:{product:{...product,product_type:kind,variants:[]},breadcrumb:[],reviews:[],related:[]}}):fallback(url,config));
  await mount();
  expect(Boolean(host.querySelector('[data-testid="product-try-on"]'))).toBe(kind!=='lens');
});

const choosePrescriptionPhoto = async (file) => {
  await mount();
  const input = host.querySelector('input[type="file"]');
  Object.defineProperty(input, "files", { value: [file], configurable: true });
  await act(async () => input.dispatchEvent(new Event("change", { bubbles: true })));
};


test("prescription photo replaces manual fields and its private upload is linked to the cart", async () => {
  URL.createObjectURL = jest.fn(() => "blob:prescription-preview");
  URL.revokeObjectURL = jest.fn();
  const file = new File(["photo"], "resep.png", { type: "image/png" });
  await choosePrescriptionPhoto(file);
  expect(host.querySelector('[aria-label="Kanan (OD) SPH"]')).toBeNull();
  expect(host.querySelector('img[alt="Pratinjau foto resep kacamata"]').getAttribute("src")).toBe("blob:prescription-preview");
  expect(api.post).not.toHaveBeenCalled();
  api.post.mockResolvedValueOnce({ data: { id: "private-rx" } }).mockResolvedValueOnce({ data: { ok: true } });
  await click(host.querySelector('[data-testid="add-to-cart-btn"]'));
  await click(host.querySelector('[data-testid="addon-skip"]'));
  expect(api.post.mock.calls[0][0]).toBe("/uploads/prescription");
  expect(api.post.mock.calls[0][1].get("file")).toBe(file);
  expect(api.post).toHaveBeenLastCalledWith("/cart", expect.objectContaining({ prescription: expect.objectContaining({ attachment_upload_id: "private-rx" }) }));
  await click(host.querySelector('[aria-label="Hapus foto resep"]'));
  expect(host.querySelector('img[alt="Pratinjau foto resep kacamata"]')).toBeNull();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:prescription-preview");
});


test("unsupported prescription files are rejected without uploading", async () => {
  await choosePrescriptionPhoto(new File(["svg"], "resep.svg", { type: "image/svg+xml" }));
  expect(host.querySelector('[role="alert"]').textContent).toContain("maksimal 8 MB");
  expect(api.post).not.toHaveBeenCalled();
});


test("failed prescription upload prevents adding a cart item without its photo", async () => {
  URL.createObjectURL = jest.fn(() => "blob:prescription-preview");
  URL.revokeObjectURL = jest.fn();
  await choosePrescriptionPhoto(new File(["photo"], "resep.jpg", { type: "image/jpeg" }));
  api.post.mockRejectedValueOnce(new Error("Upload failed"));
  await click(host.querySelector('[data-testid="buy-now-btn"]'));
  await click(host.querySelector('[data-testid="addon-skip"]'));
  expect(api.post).toHaveBeenCalledTimes(1);
  expect(api.post.mock.calls[0][0]).toBe("/uploads/prescription");
  expect(mockNavigate).not.toHaveBeenCalled();
  expect(host.querySelector('[data-testid="add-to-cart-btn"]').disabled).toBe(false);
});


test("Meowsurement entry carries selected product and variant and shows its actual geometry", async () => {
  await mount();
  expect(host.querySelector('[data-testid="open-meowsurement"]').getAttribute("href")).toBe("/meowsurement/?product_id=frame&variant_id=v1");
  expect(host.querySelector('[data-testid="product-frame-spec-a"]').textContent).toBe("52 mm");
  await click(host.querySelector('[data-testid="variant-BLACK"]'));
  expect(host.querySelector('[data-testid="open-meowsurement"]').getAttribute("href")).toBe("/meowsurement/?product_id=frame&variant_id=v2");
  expect(host.querySelector('[data-testid="product-frame-spec-a"]').textContent).toBe("56 mm");
});

test('lens type filters indices and the chosen combination is saved after the purchase buttons',async()=>{
  await mount();
  const panel=host.querySelector('[data-testid=product-optical-options]');
  expect(host.querySelector('[data-testid=add-to-cart-btn]').compareDocumentPosition(panel)&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  const type=host.querySelector('[data-testid=product-lens-type]');
  await act(async()=>{type.value='clear';type.dispatchEvent(new Event('change',{bubbles:true}));});
  const index=host.querySelector('[data-testid=product-lens-index]');
  expect(index.options.length).toBe(3);expect(index.textContent).toContain('Rp 90000');expect(index.textContent).not.toContain('UV420');
  expect(host.querySelector('[data-testid=add-to-cart-btn]').disabled).toBe(true);
  await act(async()=>{index.value='clear167';index.dispatchEvent(new Event('change',{bubbles:true}));});
  await click(host.querySelector('[data-testid=add-to-cart-btn]'));await click(host.querySelector('[data-testid=addon-skip]'));
  expect(api.post).toHaveBeenCalledWith('/cart',expect.objectContaining({lens_index_id:'clear167',product_id:'frame',variant_id:'v1'}));
  await act(async()=>{type.value='uv420';type.dispatchEvent(new Event('change',{bubbles:true}));});
  expect(host.querySelector('[data-testid=product-lens-index]').value).toBe('');
  expect(host.querySelector('[data-testid=product-lens-index]').options.length).toBe(2);
});

test('tinting and notes stay in the product draft until one cart request saves them together',async()=>{
  const fallback=api.get.getMockImplementation();
  const color={id:'black',code:'04S',name:'Black',kind:'solid',group:'fashion',hex_color:'#000000',additional_price:60000};
  api.get.mockImplementation((url,config)=>url==='/tinting'?Promise.resolve({data:{items:[color]}}):fallback(url,config));
  await mount();await click(host.querySelector('[data-testid=choose-tinting-frame]'));await click(host.querySelector('input[type=radio]'));
  const notes=host.querySelector('textarea');
  await act(async()=>{Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(notes,'Catatan per produk');notes.dispatchEvent(new Event('input',{bubbles:true}));});
  expect(api.patch).not.toHaveBeenCalled();expect(api.post).not.toHaveBeenCalled();
  await click(host.querySelector('[data-testid=add-to-cart-btn]'));await click(host.querySelector('[data-testid=addon-skip]'));
  expect(api.post).toHaveBeenCalledWith('/cart',expect.objectContaining({tinting_id:'black',prescription:expect.objectContaining({notes:'Catatan per produk'})}));
});

test('editing from checkout updates the owned row instead of adding a duplicate product',async()=>{
  const fallback=api.get.getMockImplementation();
  api.get.mockImplementation((url,config)=>url==='/cart'?Promise.resolve({data:{items:[{id:'owned',product:{...product},variant_id:'v2',quantity:2,lens_index:{id:'clear161'},prescription:{notes:'Saved notes'}}]}}):fallback(url,config));
  api.patch.mockResolvedValue({data:{cart_item:{id:'owned'}}});
  await mount({pathname:'/products/frame',search:'?cart_item_id=owned',state:{checkout_item_ids:['owned','another']}});
  expect(host.querySelector('textarea').value).toBe('Saved notes');
  const index=host.querySelector('[data-testid=product-lens-index]');
  await act(async()=>{index.value='clear167';index.dispatchEvent(new Event('change',{bubbles:true}));});
  await click(host.querySelector('[data-testid=add-to-cart-btn]'));
  expect(api.patch).toHaveBeenCalledWith('/cart/owned/configuration',expect.objectContaining({variant_id:'v2',quantity:2,lens_index_id:'clear167',replace_lens_product:true}));
  expect(api.post).not.toHaveBeenCalled();expect(mockNavigate).toHaveBeenCalledWith('/checkout',{state:{selected_item_ids:['owned','another']}});
});
