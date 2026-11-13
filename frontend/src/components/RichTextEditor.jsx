import React, { useEffect, useId, useRef, useState } from 'react';
import { EditorContent, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import ContentImage from './ContentImage';
import { TableKit } from '@tiptap/extension-table';
import TextAlign from '@tiptap/extension-text-align';
import { TextStyleKit } from '@tiptap/extension-text-style';
import Highlight from '@tiptap/extension-highlight';
import { Bold, Italic, Underline, Strikethrough, List, ListOrdered, Quote, AlignLeft, AlignCenter, AlignRight, AlignJustify, Link, Unlink, ImagePlus, Table2, Undo2, Redo2, RemoveFormatting, Highlighter } from 'lucide-react';
import ImagePicker from './ImagePicker';
import { contentUrl, sanitizeRichContent } from '../lib/richContent';

function Tool({ label, icon: Icon, active = false, disabled = false, onClick }) {
  return <button type="button" title={label} aria-label={label} aria-pressed={active} disabled={disabled} onMouseDown={event => event.preventDefault()} onClick={onClick} className={`inline-flex items-center justify-center rounded-lg p-2 text-sm disabled:opacity-35 ${active ? 'bg-meow-midnight text-white' : 'hover:bg-white text-meow-midnight'}`}><Icon className="h-4 w-4" /></button>;
}

function colorInputValue(color) {
  if (/^#[\da-f]{6}$/i.test(color || '')) return color;
  const rgb = /^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/.exec(color || '');
  return rgb ? `#${rgb.slice(1).map(value => Number(value).toString(16).padStart(2, '0')).join('')}` : '#0b192c';
}

export default function RichTextEditor({ value = '', onChange, label = 'Konten', testId = 'rich-text-editor' }) {
  const labelId = useId();
  const lastEmitted = useRef(null), changeRef = useRef(onChange);
  changeRef.current = onChange;
  const [panel, setPanel] = useState(''), [url, setUrl] = useState(''), [alt, setAlt] = useState('');
  const [error, setError] = useState('');
  const [rows, setRows] = useState(3), [columns, setColumns] = useState(3);
  const editor = useEditor({
    extensions: [StarterKit.configure({ link: { openOnClick: false, autolink: false }, heading: { levels: [1, 2, 3, 4, 5, 6] } }),
      ContentImage.configure({ allowBase64: false }), TableKit.configure({ table: { resizable: false } }),
      TextAlign.configure({ types: ['heading', 'paragraph'] }), TextStyleKit, Highlight.configure({ multicolor: true })],
    content: sanitizeRichContent(value), shouldRerenderOnTransaction: true,
    editorProps: { attributes: { class: 'rich-content min-h-[280px] px-4 py-3 outline-none', role: 'textbox', 'aria-multiline': 'true', 'aria-labelledby': labelId },
      transformPastedHTML: html => sanitizeRichContent(html) },
    onUpdate: ({ editor: current }) => {
      const html = current.isEmpty ? '' : sanitizeRichContent(current.getHTML());
      lastEmitted.current = html; changeRef.current(html);
    },
  });
  useEffect(() => {
    if (!editor || value === lastEmitted.current) return;
    const next = sanitizeRichContent(value);
    if (editor.getHTML() !== next) editor.commands.setContent(next, { emitUpdate: false });
  }, [editor, value]);
  const openPanel = next => { setPanel(panel === next ? '' : next); setError(''); setUrl(next === 'link' ? editor.getAttributes('link').href || '' : ''); setAlt(''); };
  const insertUrl = () => {
    const safe = contentUrl(url, panel === 'image');
    if (!safe) { setError('Gunakan URL HTTP/HTTPS atau path halaman yang valid.'); return; }
    if (panel === 'image') editor.chain().focus().setImage({ src: safe, alt }).run();
    else if (editor.state.selection.empty && !editor.isActive('link')) editor.chain().focus().insertContent({ type: 'text', text: safe, marks: [{ type: 'link', attrs: { href: safe, target: '_blank', rel: 'noopener noreferrer' } }] }).run();
    else editor.chain().focus().extendMarkRange('link').setLink({ href: safe }).run();
    setPanel(''); setError('');
  };
  const selectClass = 'rounded-lg border border-zinc-200 bg-white px-2 py-1.5 text-xs min-w-0';
  const inputClass = 'w-full rounded-xl border border-zinc-200 bg-white p-2 text-sm';
  if (!editor) return <p role="status">Memuat editor…</p>;
  const inTable = editor.isActive('table');
  const imageSelected = editor.isActive('image');
  const currentImageWidth = String(editor.getAttributes('image').width || '100%');
  return <section className="min-w-0 max-w-full" data-testid={testId}>
    <p id={labelId} className="text-xs font-bold uppercase tracking-wide text-meow-gray mb-2">{label}</p>
    <div className="rounded-2xl border border-zinc-200 bg-white overflow-hidden focus-within:border-meow-salmon">
      <div role="toolbar" aria-label={`Format ${label}`} className="flex flex-wrap items-center gap-1 border-b border-zinc-200 bg-meow-bg p-2">
        <select aria-label="Gaya paragraf" className={selectClass} value={editor.isActive('heading') ? `h${editor.getAttributes('heading').level}` : 'p'} onChange={event => event.target.value === 'p' ? editor.chain().focus().setParagraph().run() : editor.chain().focus().setHeading({ level: Number(event.target.value.slice(1)) }).run()}><option value="p">Paragraf</option>{[1, 2, 3, 4, 5, 6].map(level => <option key={level} value={`h${level}`}>Heading {level} (H{level})</option>)}</select>
        <select aria-label="Jenis huruf" className={selectClass} value={editor.getAttributes('textStyle').fontFamily || ''} onChange={event => event.target.value ? editor.chain().focus().setFontFamily(event.target.value).run() : editor.chain().focus().unsetFontFamily().run()}><option value="">Font bawaan</option>{['Arial', 'Georgia', 'Verdana', '"Times New Roman"', '"Courier New"'].map(font => <option key={font} value={font}>{font.replaceAll('"', '')}</option>)}</select>
        <select aria-label="Ukuran teks" className={selectClass} value={editor.getAttributes('textStyle').fontSize || ''} onChange={event => event.target.value ? editor.chain().focus().setFontSize(event.target.value).run() : editor.chain().focus().unsetFontSize().run()}><option value="">Ukuran</option>{[12, 14, 16, 18, 20, 24, 28, 32, 40, 48].map(size => <option key={size} value={`${size}px`}>{size}px</option>)}</select>
        {[[Bold, 'Tebal', 'bold', 'toggleBold'], [Italic, 'Miring', 'italic', 'toggleItalic'], [Underline, 'Garis bawah', 'underline', 'toggleUnderline'], [Strikethrough, 'Coret', 'strike', 'toggleStrike'], [List, 'Daftar poin', 'bulletList', 'toggleBulletList'], [ListOrdered, 'Daftar nomor', 'orderedList', 'toggleOrderedList'], [Quote, 'Kutipan', 'blockquote', 'toggleBlockquote']].map(([icon, text, type, command]) => <Tool key={type} icon={icon} label={text} active={editor.isActive(type)} onClick={() => editor.chain().focus()[command]().run()} />)}
        {[[AlignLeft, 'Kiri', 'left'], [AlignCenter, 'Tengah', 'center'], [AlignRight, 'Kanan', 'right'], [AlignJustify, 'Rata kanan kiri', 'justify']].map(([icon, text, align]) => <Tool key={align} icon={icon} label={`Rata ${text.toLowerCase()}`} disabled={imageSelected && align === 'justify'} active={imageSelected ? editor.getAttributes('image').alignment === align : editor.isActive({ textAlign: align })} onClick={() => imageSelected ? editor.chain().focus().updateAttributes('image', { alignment: align }).run() : editor.chain().focus().setTextAlign(align).run()} />)}
        <label className="inline-flex items-center gap-1 px-1 text-xs font-semibold" title="Warna teks">A<input type="color" aria-label="Warna teks" value={colorInputValue(editor.getAttributes('textStyle').color)} onChange={event => editor.chain().focus().setColor(event.target.value).run()} className="h-7 w-7 cursor-pointer rounded border-0 bg-transparent" /></label>
        <Tool icon={Highlighter} label="Sorot teks" active={editor.isActive('highlight')} onClick={() => editor.chain().focus().toggleHighlight({ color: '#fff0a6' }).run()} />
        <Tool icon={Link} label="Sisipkan tautan" active={panel === 'link' || editor.isActive('link')} onClick={() => openPanel('link')} />
        <Tool icon={Unlink} label="Hapus tautan" disabled={!editor.isActive('link')} onClick={() => editor.chain().focus().extendMarkRange('link').unsetLink().run()} />
        <Tool icon={ImagePlus} label="Sisipkan gambar" active={panel === 'image'} onClick={() => openPanel('image')} />
        <Tool icon={Table2} label="Sisipkan tabel" active={panel === 'table'} onClick={() => openPanel('table')} />
        <Tool icon={RemoveFormatting} label="Hapus format" onClick={() => editor.chain().focus().unsetAllMarks().clearNodes().run()} />
        <Tool icon={Undo2} label="Urungkan" disabled={!editor.can().undo()} onClick={() => editor.chain().focus().undo().run()} />
        <Tool icon={Redo2} label="Ulangi" disabled={!editor.can().redo()} onClick={() => editor.chain().focus().redo().run()} />
      </div>
      {panel && <div className="bg-meow-bg/60 p-3 border-b space-y-3" onKeyDown={event => { if (event.key === 'Enter' && event.target.tagName === 'INPUT') event.preventDefault(); }}>
        {panel === 'image' && <><ImagePicker label="Gambar dalam konten" value={url} onChange={setUrl} testId={`${testId}-image`} /><label className="block text-xs font-semibold">Teks alternatif gambar<input className={inputClass} value={alt} onChange={event => setAlt(event.target.value)} placeholder="Deskripsi gambar" /></label></>}
        {panel === 'link' && <label className="block text-xs font-semibold">URL tautan<input aria-label="URL tautan" className={inputClass} value={url} onChange={event => setUrl(event.target.value)} placeholder="https://… atau /halaman" /></label>}
        {panel === 'table' ? <div className="flex flex-wrap items-end gap-3"><label className="text-xs font-semibold">Baris<input aria-label="Jumlah baris tabel" type="number" min="1" max="20" value={rows} onChange={event => setRows(event.target.value)} className={`${inputClass} max-w-20`} /></label><label className="text-xs font-semibold">Kolom<input aria-label="Jumlah kolom tabel" type="number" min="1" max="10" value={columns} onChange={event => setColumns(event.target.value)} className={`${inputClass} max-w-20`} /></label><button type="button" onClick={() => { if (!Number.isInteger(Number(rows)) || !Number.isInteger(Number(columns)) || rows < 1 || rows > 20 || columns < 1 || columns > 10) { setError('Gunakan 1–20 baris dan 1–10 kolom.'); return; } editor.chain().focus().insertTable({ rows: Number(rows), cols: Number(columns), withHeaderRow: true }).run(); setPanel(''); }} className="btn-secondary text-xs py-2">Tambahkan tabel</button></div> : <button type="button" onClick={insertUrl} disabled={!url.trim()} className="btn-secondary text-xs py-2 disabled:opacity-40">{panel === 'image' ? 'Tambahkan gambar ke konten' : 'Terapkan tautan'}</button>}
        {error && <p role="alert" className="text-xs text-red-600">{error}</p>}
        <button type="button" onClick={() => setPanel('')} className="text-xs underline ml-3">Tutup panel</button>
      </div>}
      {inTable && <div role="toolbar" aria-label="Pengaturan tabel" className="flex flex-wrap gap-2 bg-blue-50 p-2 border-b">{[['Tambah baris', 'addRowAfter'], ['Hapus baris', 'deleteRow'], ['Tambah kolom', 'addColumnAfter'], ['Hapus kolom', 'deleteColumn'], ['Gabung sel', 'mergeCells'], ['Pisah sel', 'splitCell'], ['Header tabel', 'toggleHeaderRow'], ['Hapus tabel', 'deleteTable']].map(([text, command]) => <button key={command} type="button" onMouseDown={event => event.preventDefault()} onClick={() => editor.chain().focus()[command]().run()} disabled={!editor.can()[command]()} className="rounded border border-blue-100 bg-white px-2 py-1 text-xs disabled:opacity-40">{text}</button>)}</div>}
      {imageSelected && <div className="flex flex-wrap items-center gap-2 p-2 bg-blue-50 border-b"><label className="text-xs font-semibold">Lebar gambar <select aria-label="Lebar gambar" value={currentImageWidth} onChange={event => editor.chain().focus().updateAttributes('image', { width: event.target.value, height: null }).run()} className={selectClass}>{!['25%', '50%', '75%', '100%'].includes(currentImageWidth) && <option value={currentImageWidth}>{currentImageWidth} (manual)</option>}{['25%', '50%', '75%', '100%'].map(width => <option key={width}>{width}</option>)}</select></label>{[[AlignLeft, 'Kiri', 'left'], [AlignCenter, 'Tengah', 'center'], [AlignRight, 'Kanan', 'right']].map(([icon, text, alignment]) => <Tool key={alignment} label={`Gambar rata ${text.toLowerCase()}`} icon={icon} active={editor.getAttributes('image').alignment === alignment} onClick={() => editor.chain().focus().updateAttributes('image', { alignment }).run()} />)}<button type="button" onClick={() => editor.chain().focus().deleteSelection().run()} className="text-xs text-red-600">Hapus gambar</button><p className="w-full text-[11px] text-meow-gray">Tarik pegangan di sudut gambar untuk mengubah ukuran. Proporsi gambar tetap dan lebarnya menyesuaikan layar.</p></div>}
      <EditorContent editor={editor} />
      <p className="border-t px-3 py-2 text-[11px] text-meow-gray">{editor.getText().trim().split(/\s+/).filter(Boolean).length} kata · Pilih teks untuk mengubah format. Klik sel tabel atau gambar untuk mengaturnya.</p>
    </div>
  </section>;
}
