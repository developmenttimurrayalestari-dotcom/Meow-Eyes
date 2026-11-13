import Image from '@tiptap/extension-image';
import { imageSrc } from '../lib/api';

export function imageWidth(value) {
  const text = String(value ?? '').trim();
  if (/^\d+(\.\d+)?%$/.test(text)) return `${Math.min(100, Math.max(1, parseFloat(text)))}%`;
  if (/^\d+(\.\d+)?(px)?$/.test(text) && parseFloat(text) > 0) return `${parseFloat(text)}px`;
  return '100%';
}
export const imageAlignment = value => ['left', 'center', 'right'].includes(value) ? value : 'left';

// The node view adds editing handles only. Stored HTML remains a responsive
// <img>, with portable upload paths and no editor controls in published content.
export default Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      width: {
        default: '100%',
        parseHTML: element => element.getAttribute('width') || element.style.width || '100%',
        renderHTML: attributes => {
          const width = imageWidth(attributes.width);
          return { width: width.endsWith('px') ? parseFloat(width) : width, style: `width: ${width}` };
        },
      },
      alignment: {
        default: 'left',
        parseHTML: element => imageAlignment(element.getAttribute('data-align')),
        renderHTML: attributes => ({ 'data-align': imageAlignment(attributes.alignment) }),
      },
    };
  },
  addNodeView() {
    return ({ node: initialNode, editor, getPos }) => {
      let node = initialNode, drag = null, destroyed = false;
      const dom = document.createElement('div');
      dom.className = 'rte-image-node'; dom.contentEditable = 'false';
      const image = document.createElement('img'); image.draggable = false;
      dom.appendChild(image);
      const listeners = [];
      const listen = (element, event, handler) => { element.addEventListener(event, handler); listeners.push(() => element.removeEventListener(event, handler)); };
      const availableWidth = () => {
        const parent = dom.parentElement;
        if (!parent) return 0;
        const style = getComputedStyle(parent);
        return parent.clientWidth - (parseFloat(style.paddingLeft) || 0) - (parseFloat(style.paddingRight) || 0);
      };
      const commit = percentage => {
        const position = getPos();
        if (destroyed || editor.isDestroyed || typeof position !== 'number') return;
        editor.chain().setNodeSelection(position).updateAttributes('image', { width: `${percentage}%`, height: null }).run();
      };
      const update = next => {
        if (next.type.name !== 'image') return false;
        node = next;
        image.src = imageSrc(node.attrs.src); image.alt = node.attrs.alt || '';
        if (node.attrs.title) image.title = node.attrs.title;
        else image.removeAttribute('title');
        if (!drag) dom.style.width = imageWidth(node.attrs.width);
        dom.dataset.align = imageAlignment(node.attrs.alignment);
        return true;
      };
      for (const corner of ['nw', 'ne', 'sw', 'se']) {
        const handle = document.createElement('button');
        handle.type = 'button'; handle.className = `rte-image-handle rte-image-handle-${corner}`;
        handle.setAttribute('aria-label', `Ubah ukuran gambar ${corner}`);
        handle.title = 'Tarik untuk mengubah ukuran. Tombol panah untuk menyesuaikan.';
        handle.dataset.resizeHandle = corner;
        dom.appendChild(handle);
        listen(handle, 'pointerdown', event => {
          if (event.button !== 0 || destroyed) return;
          event.preventDefault(); event.stopPropagation();
          const rect = dom.getBoundingClientRect(), parentWidth = availableWidth();
          if (!rect.width || !rect.height || !parentWidth) return;
          const position = getPos();
          if (typeof position !== 'number') return;
          editor.commands.setNodeSelection(position);
          drag = { pointer: event.pointerId, x: event.clientX, y: event.clientY, width: rect.width,
            ratio: rect.width / rect.height, parentWidth, percentage: rect.width / parentWidth * 100 };
          dom.classList.add('is-resizing');
          handle.setPointerCapture(event.pointerId);
        });
        listen(handle, 'pointermove', event => {
          if (!drag || drag.pointer !== event.pointerId) return;
          event.preventDefault();
          const horizontal = (event.clientX - drag.x) * (corner.includes('e') ? 1 : -1);
          const vertical = (event.clientY - drag.y) * (corner.includes('s') ? 1 : -1) * drag.ratio;
          const delta = Math.abs(horizontal) >= Math.abs(vertical) ? horizontal : vertical;
          const pixels = Math.min(drag.parentWidth, Math.max(Math.min(32, drag.parentWidth), drag.width + delta));
          drag.percentage = Math.round(pixels / drag.parentWidth * 1000) / 10;
          dom.style.width = `${drag.percentage}%`;
        });
        const finish = event => {
          if (!drag || drag.pointer !== event.pointerId) return;
          const percentage = drag.percentage;
          drag = null; dom.classList.remove('is-resizing');
          if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId);
          if (event.type === 'pointerup') commit(percentage);
          else update(node);
        };
        listen(handle, 'pointerup', finish);
        listen(handle, 'pointercancel', finish);
        listen(handle, 'lostpointercapture', finish);
        listen(handle, 'keydown', event => {
          if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return;
          event.preventDefault(); event.stopPropagation();
          const parentWidth = availableWidth();
          if (!parentWidth) return;
          const percentage = dom.getBoundingClientRect().width / parentWidth * 100;
          const delta = (event.shiftKey ? 10 : 2) * (['ArrowRight', 'ArrowUp'].includes(event.key) ? 1 : -1);
          commit(Math.round(Math.min(100, Math.max(5, percentage + delta)) * 10) / 10);
        });
      }
      update(node);
      return {
        dom, update,
        selectNode: () => dom.classList.add('is-selected'),
        deselectNode: () => dom.classList.remove('is-selected'),
        stopEvent: event => Boolean(drag || event.target.closest?.('.rte-image-handle')),
        ignoreMutation: () => true,
        destroy: () => { destroyed = true; drag = null; listeners.forEach(remove => remove()); },
      };
    };
  },
});
