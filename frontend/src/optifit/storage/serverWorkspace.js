import { api } from '../../lib/api';

const copy = value => value == null ? value : JSON.parse(JSON.stringify(value));
const replaceById = (items, item) => [...items.filter(old => old.id !== item.id), item];
export const DEFAULT_SERVER_SETTINGS = { calibrationMethods: ['marker', 'frame'], asymmetryWarningMm: null, photoRetentionDays: 30 };
function websiteActor(user) {
  const isReviewer = ['admin','super_admin'].includes(user.role) || (user.role === 'staff' && (user.permissions || []).includes('meowsurement.review'));
  return { id: user.user_id || user.id, displayName: user.name, role: ['admin','super_admin'].includes(user.role) ? 'admin' : isReviewer ? 'reviewer' : 'operator', websiteRole: user.role, active: user.is_active !== false };
}
export function workspaceError(error, fallback = 'Data belum dapat disimpan. Periksa koneksi lalu coba kembali.') {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail.message === 'string') return detail.message;
  if (Array.isArray(detail)) return detail.map(item => item.msg).filter(Boolean).join('; ');
  return error?.message || fallback;
}

export class ServerWorkspace {
  constructor({ client = api, tokenReader = () => { try { return localStorage.getItem('meow_token'); } catch { return null; } } } = {}) {
    this.client = client; this.tokenReader = tokenReader; this.serverMode = true;
    this.listeners = new Set(); this.generation = 0; this.locked = true;
    this.state = null; this.user = null; this.bootstrapData = null;
    this.localPhotos = new Map(); this.photoSessions = new Map(); this.activeSessionId = null;
  }
  subscribe(callback) { this.listeners.add(callback); return () => this.listeners.delete(callback); }
  notify() { for (const listener of this.listeners) listener(); }
  getUser() { return !this.locked && this.user ? copy(websiteActor(this.user)) : null; }
  getState() { return !this.locked ? copy(this.state) : null; }
  getBootstrap() { return !this.locked ? copy(this.bootstrapData) : null; }
  touch() {}
  assertAccess() { if (this.locked || !this.user) throw new Error('Tampilan dikunci. Lanjutkan dengan sesi akun Meow Eyes Anda.'); }
  lock(reason = 'privacy') { this.locked = true; this.lockReason = reason; this.generation += 1; this.notify(); }
  clear(reason = 'account-changed') {
    this.state = null; this.user = null; this.bootstrapData = null; this.activeSessionId = null;
    this.localPhotos.clear(); this.photoSessions.clear(); this.lock(reason);
  }
  async request(method, url, data, options = {}) {
    const { allowLocked = false, ...config } = options;
    if (!allowLocked) this.assertAccess();
    const generation = this.generation, token = this.tokenReader();
    const response = await this.client.request({ method, url, data, withCredentials: true, timeout: 30000, ...config });
    if (token !== this.tokenReader()) { this.clear(); throw new Error('Akun berubah. Buka kembali Meowsurement untuk akun yang sedang aktif.'); }
    if (generation !== this.generation) throw new Error('Permintaan selesai setelah tampilan dikunci. Muat ulang sesi untuk melihat kondisi tersimpan.');
    return response.data;
  }
  async bootstrap() {
    const body = await this.request('get','/meowsurement/bootstrap',undefined,{allowLocked:true});
    const user = body.user;
    if (!user || !(user.user_id || user.id)) throw new Error('Sesi customer tidak tersedia. Masuk kembali ke Meow Eyes.');
    const changed = this.user && (this.user.user_id || this.user.id) !== (user.user_id || user.id);
    if (changed) { this.generation += 1; this.state = null; this.localPhotos.clear(); this.photoSessions.clear(); this.activeSessionId = null; }
    this.user = user; this.bootstrapData = body; this.locked = false;
    if (!this.state) this.state = { patients:[], sessions:[], sessionPagination:{page:1,total:0,total_pages:1}, revisions:[], reviews:[], photos:[], users:[], sessionPatients:{}, organization:{name:'Meow Eyes'}, settings:{...DEFAULT_SERVER_SETTINGS} };
    this.state.users = replaceById(this.state.users,websiteActor(user));
    this.state.settings = {...DEFAULT_SERVER_SETTINGS,...body.settings};
    this.notify(); return copy(body);
  }
  async frames({ query = '', productId = '', page = 1 } = {}) {
    return this.request('get','/meowsurement/frames',undefined,{params:{query,page,page_size:15,...(productId?{product_id:productId}:{})}});
  }
  async listSessions({page=1}={}) {
    const body = await this.request('get','/meowsurement/sessions',undefined,{params:{page,page_size:15}});
    const rows = body.sessions || [];
    this.state.sessions = rows;
    this.state.sessionPagination = {page:body.page || page,total:body.total ?? rows.length,total_pages:body.total_pages || 1};
    this.notify(); return copy(body);
  }
  applyDetail(body) {
    const session = body.session, revisions = body.revisions || (body.revision ? [body.revision] : []);
    if (!session?.id || !revisions.length) throw new Error('Respons sesi pengukuran belum lengkap.');
    this.state.sessions = replaceById(this.state.sessions,session);
    this.state.revisions = [...this.state.revisions.filter(r=>r.sessionId!==session.id),...revisions];
    this.state.reviews = [...this.state.reviews.filter(r=>r.sessionId!==session.id),...(body.reviews || [])];
    this.state.photos = [...this.state.photos.filter(r=>r.sessionId!==session.id),...(body.photos || [])];
    this.state.settings = {...this.state.settings,...body.settings};
    if (body.patient) {
      this.state.sessionPatients[session.id] = body.patient;
      this.state.patients = replaceById(this.state.patients,body.patient);
    }
    if (session.createdBy) this.state.users = replaceById(this.state.users,{id:session.createdBy,displayName:session.operatorName || body.patient?.fullName || 'Customer',role:'operator'});
    // Preserve the signed-in website permissions after adding author labels.
    this.state.users = replaceById(this.state.users,websiteActor(this.user));
    for (const review of body.reviews || []) if (review.reviewerId) this.state.users = replaceById(this.state.users,{id:review.reviewerId,displayName:review.reviewerName || 'Reviewer Meow Eyes',role:'reviewer'});
    for (const photo of body.photos || []) this.photoSessions.set(photo.id,session.id);
    this.activeSessionId = session.id; this.notify(); return copy(body);
  }
  async loadSession(id) { return this.applyDetail(await this.request('get','/meowsurement/sessions/'+encodeURIComponent(id))); }
  async createSession(input) {
    const body = await this.request('post','/meowsurement/sessions',input);
    return this.applyDetail(body);
  }
  async appendRevision(sessionId,{data,reason,expectedRevisionId}) {
    await this.request('post','/meowsurement/sessions/'+encodeURIComponent(sessionId)+'/revisions',{data,reason,expected_revision_id:expectedRevisionId});
    return this.loadSession(sessionId);
  }
  async submitSession(sessionId,{expectedRevisionId}) {
    await this.request('post','/meowsurement/sessions/'+encodeURIComponent(sessionId)+'/submit',{expected_revision_id:expectedRevisionId});
    return this.loadSession(sessionId);
  }
  async reviewSession(sessionId,{decision,note,evidence,expectedRevisionId}) {
    await this.request('post','/meowsurement/sessions/'+encodeURIComponent(sessionId)+'/reviews',{decision,note,evidence,expected_revision_id:expectedRevisionId});
    return this.loadSession(sessionId);
  }
  async recordExport({sessionId,revisionId,format,confirmed,includePhoto=false,photoIds=[]}) {
    if (!confirmed) throw new Error('Konfirmasi ekspor diperlukan.');
    if (photoIds.some(id=>String(id).startsWith('local_'))) throw new Error('Thumbnail laporan harus berasal dari foto yang telah disimpan dengan persetujuan.');
    return this.request('post','/meowsurement/sessions/'+encodeURIComponent(sessionId)+'/exports',{revision_id:revisionId,format,confirmed,include_photos:includePhoto,photo_ids:photoIds});
  }
  async putPhoto({sessionId,patientId,blob,consent,metadata={}}) {
    this.assertAccess();
    const session = this.state.sessions.find(s=>s.id===sessionId);
    const revision = this.state.revisions.find(r=>r.id===session?.currentRevisionId);
    if (!session || !revision || patientId !== (this.user.user_id || this.user.id) || consent !== true || revision.data?.consents?.capture !== true) throw new Error('Persetujuan dan sesi milik customer diperlukan sebelum mengambil foto.');
    if (!blob || blob.size>8*1024*1024 || !['image/jpeg','image/png','image/webp'].includes(blob.type)) throw new Error('Foto harus JPEG, PNG atau WebP maksimal 8 MiB.');
    if (revision.data.consents.uploadPhotos !== true) {
      const id='local_'+crypto.randomUUID().replace(/-/g,'');
      this.localPhotos.set(id,{blob,sessionId,userId:this.user.user_id || this.user.id}); return id;
    }
    const form = new FormData(); form.append('file',blob,'capture.'+(blob.type==='image/png'?'png':blob.type==='image/webp'?'webp':'jpg'));
    form.append('consent','true'); form.append('view',metadata.view || 'frontal');
    const body = await this.request('post','/meowsurement/sessions/'+encodeURIComponent(sessionId)+'/photos',form);
    const id=body.photoId || body.id;
    if (!id) throw new Error('Identitas foto tersimpan tidak tersedia.');
    this.photoSessions.set(id,sessionId);
    if (body.photo) this.state.photos=replaceById(this.state.photos,body.photo);
    return id;
  }
  async getPhoto(id) {
    this.assertAccess();
    if (this.localPhotos.has(id)) return this.localPhotos.get(id).blob;
    const sessionId=this.photoSessions.get(id);
    if (!sessionId || String(id).startsWith('local_')) throw new Error('Foto hanya disimpan selama halaman sebelumnya terbuka, atau masa simpan telah berakhir. Titik dan hasil pengukuran tetap tersimpan.');
    return this.request('get','/meowsurement/sessions/'+encodeURIComponent(sessionId)+'/photos/'+encodeURIComponent(id),undefined,{responseType:'blob'});
  }
  async deletePhoto(id,{reason='Penghapusan foto sesuai pilihan customer.'}={}) {
    this.assertAccess();
    if (String(id).startsWith('local_')) { this.localPhotos.delete(id); return; }
    const sessionId=this.photoSessions.get(id);
    if (!sessionId) throw new Error('Foto tidak ditemukan pada sesi ini.');
    await this.request('delete','/meowsurement/sessions/'+encodeURIComponent(sessionId)+'/photos/'+encodeURIComponent(id),{reason,confirmed:true});
    this.photoSessions.delete(id); this.state.photos=this.state.photos.filter(p=>p.id!==id); this.notify();
  }
}
export const serverWorkspace = new ServerWorkspace();
