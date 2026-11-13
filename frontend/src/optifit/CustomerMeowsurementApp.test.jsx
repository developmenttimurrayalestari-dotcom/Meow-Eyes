import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import CustomerMeowsurementApp, {NewMeasurement,ProfileSummary} from './CustomerMeowsurementApp';
import {ServerWorkspace} from './storage/serverWorkspace';
import {setWorkspace} from './storage/workspace';
import {ResultsPanel} from './components/Results';
import {blankSessionData} from './components/SessionDataForm';

jest.mock('./reports',()=>({clearReportResources:jest.fn(),generateReport:jest.fn(),downloadReport:jest.fn(),printReport:jest.fn()}));
jest.mock('../lib/api',()=>({api:{request:jest.fn()},imageSrc:value=>value}));
const profile={user_id:'c1',name:'Customer Satu',phone:'081234567890',birth_date:'1995-05-01',version:4,prescription:{date:'2026-01-01',od:{sph:0,cyl:0,axis:null,add:null},os:{sph:-1,cyl:-.5,axis:180,add:0}}};
const spec={a:52,b:40,dbl:18,ed:56,enabled:true,symmetric:true,version:3};
const frame={id:'p1',name:'Frame Catalog',brand:'Meow',specification_version:3,frame_specification:spec,variants:[{id:'v1',color:'Black',size:'52',inherit_default:false,effective_specification:{...spec,a:54}}]};
let host,root;
const render=async node=>act(async()=>{root.render(node);});
const click=async element=>act(async()=>{element.dispatchEvent(new MouseEvent('click',{bubbles:true}));});
const submit=async form=>act(async()=>{form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));});
const button=text=>[...host.querySelectorAll('button')].find(node=>node.textContent.includes(text));
beforeEach(()=>{host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);window.history.replaceState(null,'','/meowsurement/');});
afterEach(async()=>{await act(async()=>root.unmount());setWorkspace(null);host.remove();});

function fixture(ready=true,{reviewer=false}={}){
  const user={user_id:reviewer?'admin':'c1',name:reviewer?'Admin Web':profile.name,role:reviewer?'admin':'customer'};
  const client={request:jest.fn(async request=>{
    if(request.url.endsWith('/bootstrap'))return{data:{user,profile,ready,can_review:reviewer,missing_fields:ready?[]:['prescription.od.sph']}};
    if(request.url.endsWith('/frames'))return{data:{products:[frame],page:1,total:1,total_pages:1}};
    if(request.url.endsWith('/sessions'))return{data:{sessions:[],page:1,total:0,total_pages:1}};
    if(request.url.endsWith('/session-a'))return{data:{session:{id:'session-a',createdBy:'c1',patientId:'c1',currentRevisionId:'r1',status:'draft',examinationDate:'2026-01-01'},revisions:[{id:'r1',sessionId:'session-a',actorId:'c1',data:{...blankSessionData(),frame:{...spec,model:'Frame Snapshot'},prescription:profile.prescription}}],patient:{id:'c1',fullName:'Customer Snapshot'},reviews:[],photos:[]}};
    throw new Error('Unexpected endpoint '+request.url);
  })};
  return{store:new ServerWorkspace({client,tokenReader:()=>user.user_id}),client};
}

test('incomplete profile redirects to existing profile and preserves chosen frame',async()=>{
  window.history.replaceState(null,'','/meowsurement/?product_id=p1&variant_id=v1');const{store}=fixture(false);const navigate=jest.fn();
  await render(<CustomerMeowsurementApp store={store} navigate={navigate}/>);
  expect(navigate).toHaveBeenCalledWith('/profile?required=meowsurement&returnTo='+encodeURIComponent('/meowsurement/?product_id=p1&variant_id=v1'));
  expect(host.textContent).not.toMatch(/Buat organisasi|Administrator lokal|Tambah pasien|Buat vault/i);
});

test('customer entry uses profile data and never presents local onboarding',async()=>{
  const{store}=fixture();await render(<CustomerMeowsurementApp store={store} navigate={jest.fn()}/>);
  expect(host.textContent).toContain('Customer Satu');expect(host.querySelectorAll('[data-testid^="measurement-card-"]')).toHaveLength(5);expect(host.querySelector('form')).toBeNull();
  expect(host.querySelector('[data-testid="rx-od-sph"]').textContent).toBe('0');
  expect(host.textContent).not.toMatch(/Buat organisasi|Administrator lokal|Tambah pasien|Buat vault/i);
  await click(button('Privasi'));expect(host.textContent).not.toContain('Customer Satu');
  expect(host.textContent).toContain('Tampilan pengukuran disembunyikan');await click(button('Lanjutkan Meowsurement'));
  expect(host.textContent).toContain('Customer Satu');
});

test('selected variant supplies immutable geometry and only IDs/versions are submitted',async()=>{
  window.history.replaceState(null,'','/meowsurement/?product_id=p1&variant_id=v1');
  const store={frames:jest.fn().mockResolvedValue({products:[frame]}),createSession:jest.fn().mockResolvedValue({session:{id:'new'}})};const onCreated=jest.fn();
  await render(<NewMeasurement store={store} profile={profile} onCreated={onCreated}/>);
  expect(host.querySelector('[data-testid="selected-frame-spec"]').textContent).toContain('54 mm');
  expect(host.querySelector('[data-testid="selected-frame-spec"] input')).toBeNull();
  await submit(host.querySelectorAll('form')[1]);
  expect(store.createSession).toHaveBeenCalledWith(expect.objectContaining({product_id:'p1',variant_id:'v1',expected_profile_version:4,expected_spec_version:3}));
  const payload=store.createSession.mock.calls[0][0];expect(payload.prescription).toBeUndefined();expect(payload.frame).toBeUndefined();expect(payload.user_id).toBeUndefined();
  expect(onCreated).toHaveBeenCalledWith({session:{id:'new'}});
});

test('missing typed geometry disables session creation without guessing dimensions',async()=>{
  window.history.replaceState(null,'','/meowsurement/?product_id=p1&variant_id=v1');
  const incomplete={...frame,variants:[{...frame.variants[0],effective_specification:{...spec,a:null}}]};
  const store={frames:jest.fn().mockResolvedValue({products:[incomplete]}),createSession:jest.fn()};
  await render(<NewMeasurement store={store} profile={profile} onCreated={jest.fn()}/>);
  expect(button('Mulai pengukuran').disabled).toBe(true);expect(host.textContent).toContain('belum lengkap');
  await submit(host.querySelectorAll('form')[1]);expect(store.createSession).not.toHaveBeenCalled();
});

test('web reviewer can open customer session without completing own prescription',async()=>{
  const{store}=fixture(false,{reviewer:true});const navigate=jest.fn();
  await render(<CustomerMeowsurementApp store={store} navigate={navigate} reviewSessionId="session-a"/>);
  expect(navigate).not.toHaveBeenCalled();expect(host.textContent).toContain('Customer Snapshot');
  expect(button('Catat hasil alat')).toBeUndefined();expect(button('Ajukan review')).toBeUndefined();
});

test('prescription reference retains zero ADD distinctly from absent values',async()=>{
  await render(<ProfileSummary profile={profile}/>);
  expect(host.querySelector('[data-testid="rx-os-add"]').textContent).toBe('0');
  expect(host.querySelector('[data-testid="rx-od-add"]').textContent).toBe('—');
});

test('dashboard opens only the selected measurement and leaves other parameters hidden',async()=>{
  const{store}=fixture();await render(<CustomerMeowsurementApp store={store} navigate={jest.fn()}/>);
  await click(host.querySelector('[data-testid="measurement-card-near_pd"]'));
  expect(host.querySelector('[data-testid="measurement-setup-near_pd"]')).not.toBeNull();
  expect(host.querySelector('[aria-label="Jarak membaca"]')).not.toBeNull();
  expect(host.textContent).not.toMatch(/Pemeriksaan operator|Mode pengukuran|Head pitch/);
  expect(host.querySelector('[aria-label="Lebar lensa (A)"]')).not.toBeNull();
  await click(button('Semua jenis pengukuran'));
  await click(host.querySelector('[data-testid="measurement-card-vertex"]'));
  expect(host.querySelector('[aria-label="Jarak membaca"]')).toBeNull();
  expect(host.querySelector('[data-testid="measurement-setup-vertex"]')).not.toBeNull();
});

test('readonly website reviewer cannot mutate customer measurements',async()=>{
  await render(<ResultsPanel state={{reviews:[],users:[],settings:{}}} patient={{}} session={{id:'s',status:'draft'}} revision={{id:'r'}} data={blankSessionData()} actor={{id:'admin',role:'admin'}} onSave={jest.fn()} canEdit={false}/>);
  expect(button('Catat hasil alat')).toBeUndefined();expect(button('Ajukan review')).toBeUndefined();expect(button('Ekspor / cetak')).toBeDefined();
});
