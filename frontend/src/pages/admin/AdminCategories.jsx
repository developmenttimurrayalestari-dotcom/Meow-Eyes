import React, { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { Plus, Trash2, ChevronRight, FolderTree, Edit2 } from "lucide-react";
import { toast } from "sonner";

const buildTree = (cats) => {
  const byId = {};
  cats.forEach((c) => (byId[c.id] = { ...c, children: [] }));
  const roots = [];
  cats.forEach((c) => {
    if (c.parent_id && byId[c.parent_id]) byId[c.parent_id].children.push(byId[c.id]);
    else roots.push(byId[c.id]);
  });
  return roots;
};

const flatten = (nodes, depth = 0, acc = []) => {
  for (const n of nodes) {
    acc.push({ ...n, _depth: depth });
    if (n.children?.length) flatten(n.children, depth + 1, acc);
  }
  return acc;
};

const AdminCategories = () => {
  const [cats, setCats] = useState([]);
  const [editing, setEditing] = useState(null);
  const [formMode, setFormMode] = useState("create");
  const load = () => api.get("/admin/categories").then(({ data }) => setCats(data.categories));
  useEffect(() => { load(); }, []);
  const flat = flatten(buildTree(cats));

  const onAdd = (parent) => {
    setFormMode("create");
    setEditing({ parent_id: parent?.id || null, name: "", category_type: parent?.category_type || "product", is_active: true, is_featured: false });
  };
  const onEdit = (node) => {
    setFormMode("edit");
    setEditing({ ...node });
  };
  const onDelete = async (node) => {
    if (!confirm(`Hapus kategori "${node.name}"?`)) return;
    try {
      await api.delete(`/admin/categories/${node.id}`);
      toast.success("Kategori dihapus");
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Gagal");
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    try {
      if (formMode === "create") await api.post("/admin/categories", editing);
      else await api.put(`/admin/categories/${editing.id}`, editing);
      toast.success("Tersimpan");
      setEditing(null);
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Gagal");
    }
  };

  return (
    <div data-testid="admin-categories">
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-heading text-3xl font-black flex items-center gap-2"><FolderTree className="h-7 w-7 text-meow-salmon" /> Kategori</h1>
        <button onClick={() => onAdd(null)} className="btn-primary text-sm" data-testid="add-root-cat-btn">
          <Plus className="inline h-4 w-4 mr-1" /> Kategori Baru
        </button>
      </div>
      <div className="bg-white rounded-3xl p-4 border border-zinc-200" data-testid="cat-tree">
        {flat.map((node) => (
          <div key={node.id} data-testid={`cat-node-${node.slug}`} className="flex items-center justify-between py-2 px-3 hover:bg-meow-bg rounded-xl">
            <span className="flex items-center gap-2" style={{ paddingLeft: node._depth * 16 }}>
              <ChevronRight className="h-3 w-3 text-meow-gray" />
              <span className="font-bold text-sm">{node.name}</span>
              <span className="text-xs text-meow-gray uppercase">{node.category_type}</span>
              {!node.is_active && <span className="text-[10px] uppercase text-red-500">off</span>}
            </span>
            <div className="flex items-center gap-2">
              <button onClick={() => onAdd(node)} className="text-xs underline text-meow-salmon" data-testid={`add-child-${node.slug}`}>+ Sub</button>
              <button onClick={() => onEdit(node)} className="text-xs text-meow-gray hover:text-meow-amber"><Edit2 className="h-3 w-3" /></button>
              <button onClick={() => onDelete(node)} className="text-xs text-meow-gray hover:text-red-500" data-testid={`del-cat-${node.slug}`}><Trash2 className="h-3 w-3" /></button>
            </div>
          </div>
        ))}
      </div>
      {editing && (
        <div className="fixed inset-0 bg-black/60 z-50 grid place-items-center p-4" onClick={() => setEditing(null)}>
          <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="bg-white rounded-3xl p-6 max-w-md w-full space-y-3" data-testid="cat-form">
            <h3 className="font-heading font-extrabold text-xl">{formMode === "create" ? "Kategori Baru" : "Edit Kategori"}</h3>
            <input required value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} placeholder="Nama" className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none" data-testid="cat-name" />
            <select value={editing.category_type} onChange={(e) => setEditing({ ...editing, category_type: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-meow-bg outline-none">
              <option value="product">Product</option>
              <option value="frame">Frame</option>
              <option value="lens">Lens</option>
              <option value="package">Package</option>
            </select>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={editing.is_featured} onChange={(e) => setEditing({ ...editing, is_featured: e.target.checked })} /> Featured
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={editing.is_active} onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })} /> Aktif
            </label>
            <div className="flex gap-2">
              <button type="button" onClick={() => setEditing(null)} className="btn-secondary flex-1">Batal</button>
              <button type="submit" className="btn-primary flex-1" data-testid="cat-save">Simpan</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default AdminCategories;
