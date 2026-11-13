import { ServerWorkspace } from './serverWorkspace';
jest.mock('../../lib/api',()=>({api:{request:jest.fn()}}));

const profile = { user_id:'customer-a', name:'Customer A', phone:'081234567890', birth_date:'1995-05-01', version:4, prescription:{date:'2026-01-01',od:{sph:0,cyl:0,axis:null,add:null},os:{sph:-1,cyl:0,axis:null,add:null}} };
const bootstrap = (id='customer-a') => ({user:{user_id:id,name:'Customer A',role:'customer'},profile,ready:true,missing_fields:[],settings:{}});
const detail = (id='session-a',name='Customer A') => ({session:{id,createdBy:'customer-a',patientId:'customer-a',currentRevisionId:'revision-'+id},revisions:[{id:'revision-'+id,sessionId:id,data:{frame:{a:52,b:40,dbl:18,ed:55},prescription:profile.prescription,consents:{capture:true,uploadPhotos:false}}}],patient:{id:'customer-a',fullName:name},photos:[],reviews:[]});
async function setup() {
  const client={request:jest.fn().mockResolvedValue({data:bootstrap()})};let token='a';
  const store=new ServerWorkspace({client,tokenReader:()=>token});await store.bootstrap();
  return {client,store,setToken:value=>{token=value;}};
}

test('uses existing website account and snapshots without local account provisioning',async()=>{
  const {client,store}=await setup();store.applyDetail(detail());
  expect(store.getUser()).toMatchObject({id:'customer-a',role:'operator',websiteRole:'customer'});
  expect(client.request).toHaveBeenCalledTimes(1);expect(client.request.mock.calls[0][0]).toMatchObject({method:'get',url:'/meowsurement/bootstrap',withCredentials:true});
  expect(store.getState().sessionPatients['session-a'].fullName).toBe('Customer A');
  const snapshot=store.getState();snapshot.revisions[0].data.frame.a=100;
  expect(store.getState().revisions[0].data.frame.a).toBe(52);
});

test('keeps different historical profile snapshots for sessions of the same customer',async()=>{
  const {store}=await setup();store.applyDetail(detail('first','Original name'));store.applyDetail(detail('second','Updated name'));
  expect(store.getState().sessionPatients.first.fullName).toBe('Original name');
  expect(store.getState().sessionPatients.second.fullName).toBe('Updated name');
});

test('catalog deep links and history use API pagination parameters',async()=>{
  const {client,store}=await setup();client.request.mockResolvedValue({data:{sessions:[],page:3,total:40,total_pages:3}});
  await store.frames({productId:'frame-special',page:2});expect(client.request.mock.calls.at(-1)[0].params).toEqual({query:'',page:2,page_size:15,product_id:'frame-special'});
  await store.listSessions({page:3});expect(store.getState().sessionPagination).toEqual({page:3,total:40,total_pages:3});
});

test('late responses cannot restore private data after masking or account changes',async()=>{
  const {client,store,setToken}=await setup();let resolve;
  client.request.mockImplementation(()=>new Promise(done=>{resolve=done;}));
  const pending=store.loadSession('session-a');store.lock();resolve({data:detail()});
  await expect(pending).rejects.toThrow(/dikunci/);expect(store.getState()).toBeNull();
  client.request.mockResolvedValue({data:bootstrap()});await store.bootstrap();
  client.request.mockImplementation(()=>new Promise(done=>{resolve=done;}));
  const changed=store.loadSession('session-a');setToken('b');resolve({data:detail()});
  await expect(changed).rejects.toThrow(/Akun berubah/);expect(store.getUser()).toBeNull();expect(store.state).toBeNull();
});

test('photo processing stays in memory unless separate upload consent is saved',async()=>{
  const {client,store}=await setup();store.applyDetail(detail());client.request.mockClear();
  const blob=new Blob(['photo'],{type:'image/png'});
  const id=await store.putPhoto({sessionId:'session-a',patientId:'customer-a',blob,consent:true});
  expect(id).toMatch(/^local_/);expect(await store.getPhoto(id)).toBe(blob);expect(client.request).not.toHaveBeenCalled();
  expect(store.getState().photos).toEqual([]);
  store.lock();await expect(store.getPhoto(id)).rejects.toThrow(/dikunci/);
});

test('private photo upload uses session endpoint and explicit multipart consent',async()=>{
  const {client,store}=await setup();const body=detail();body.revisions[0].data.consents.uploadPhotos=true;store.applyDetail(body);
  client.request.mockResolvedValue({data:{photoId:'photo-private',photo:{id:'photo-private',sessionId:'session-a'}}});
  const id=await store.putPhoto({sessionId:'session-a',patientId:'customer-a',blob:new Blob(['photo'],{type:'image/png'}),consent:true,metadata:{view:'lateral_right'}});
  expect(id).toBe('photo-private');const request=client.request.mock.calls.at(-1)[0];
  expect(request.url).toBe('/meowsurement/sessions/session-a/photos');expect(request.data).toBeInstanceOf(FormData);
  expect(request.data.get('consent')).toBe('true');expect(request.data.get('view')).toBe('lateral_right');
  expect(store.getState().photos[0].id).toBe('photo-private');
});

test('new account bootstrap drops previous account photos and sessions',async()=>{
  const {client,store}=await setup();store.applyDetail(detail());
  await store.putPhoto({sessionId:'session-a',patientId:'customer-a',blob:new Blob(['photo'],{type:'image/png'}),consent:true});
  store.lock();client.request.mockResolvedValue({data:bootstrap('customer-b')});await store.bootstrap();
  expect(store.localPhotos.size).toBe(0);expect(store.getState().sessions).toEqual([]);expect(store.getUser().id).toBe('customer-b');
});

test('exports require confirmation and refuse ephemeral photographs',async()=>{
  const {client,store}=await setup();client.request.mockClear();
  await expect(store.recordExport({sessionId:'session-a',revisionId:'r',format:'pdf',confirmed:false})).rejects.toThrow(/Konfirmasi/);
  await expect(store.recordExport({sessionId:'session-a',revisionId:'r',format:'pdf',confirmed:true,photoIds:['local_ephemeral']})).rejects.toThrow(/Thumbnail/);
  expect(client.request).not.toHaveBeenCalled();
});

test('review permission is scoped to website staff, not a customer role',async()=>{
  const {client,store}=await setup();
  client.request.mockResolvedValue({data:{...bootstrap(),user:{...bootstrap().user,permissions:['meowsurement.review']}}});await store.bootstrap();
  expect(store.getUser().role).toBe('operator');
  client.request.mockResolvedValue({data:{...bootstrap(),user:{...bootstrap().user,role:'staff',permissions:['meowsurement.review']}}});await store.bootstrap();
  expect(store.getUser().role).toBe('reviewer');
});

test('a response after locking cannot authorize a report download',async()=>{
  const {client,store}=await setup();let resolve;client.request.mockImplementation(()=>new Promise(done=>{resolve=done;}));
  const pending=store.recordExport({sessionId:'session-a',revisionId:'r',format:'pdf',confirmed:true});
  store.lock();resolve({data:{id:'audit'}});await expect(pending).rejects.toThrow(/dikunci/);
});
