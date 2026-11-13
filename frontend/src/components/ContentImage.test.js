import { Editor } from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import ContentImage, { imageWidth, imageAlignment } from './ContentImage';
import { sanitizeRichContent } from '../lib/richContent';
jest.mock('../lib/api', () => ({ imageSrc: value => value }));

let editor, host;
beforeEach(() => { host = document.createElement('div'); document.body.appendChild(host); });
afterEach(() => { editor?.destroy(); host.remove(); });
const mount = () => {
  editor = new Editor({ element: host, extensions: [StarterKit, ContentImage], content: '<img src="/api/uploads-files/test.png" width="40%" data-align="center">' });
  const dom = host.querySelector('.rte-image-node');
  Object.defineProperty(dom.parentElement, 'clientWidth', { value: 500, configurable: true });
  dom.getBoundingClientRect = () => ({ width: 200, height: 100, left: 0, top: 0 });
  const handle = dom.querySelector('[data-resize-handle="se"]');
  handle.setPointerCapture = jest.fn(); handle.hasPointerCapture = () => false;
  return { dom, handle };
};
const pointer = (element, type, x, y) => {
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, button: 0, clientX: x, clientY: y });
  Object.defineProperty(event, 'pointerId', { value: 1 }); element.dispatchEvent(event);
};
test('legacy widths are accepted while new percentage widths are bounded', () => {
  expect(imageWidth('42.5%')).toBe('42.5%'); expect(imageWidth('200%')).toBe('100%');
  expect(imageWidth(640)).toBe('640px'); expect(imageWidth('calc(1px)')).toBe('100%');
  expect(imageAlignment('center')).toBe('center'); expect(imageAlignment('unsafe')).toBe('left');
});
test('serialized images preserve responsive width and alignment without editing controls', () => {
  mount();
  editor.commands.updateAttributes('image', { width: '37.5%', alignment: 'right', height: null });
  const html = sanitizeRichContent(editor.getHTML());
  expect(html).toContain('width="37.5%"'); expect(html).toContain('data-align="right"');
  expect(html).toContain('width: 37.5%'); expect(html).not.toContain('button');
  expect(html).not.toContain('rte-image');
});
test('pointer resize preserves aspect ratio and commits a percentage of the content area', () => {
  const { dom, handle } = mount();
  pointer(handle, 'pointerdown', 200, 100); pointer(handle, 'pointermove', 300, 150);
  expect(dom.style.width).toBe('60%');
  pointer(handle, 'pointerup', 300, 150);
  expect(editor.getAttributes('image').width).toBe('60%');
  expect(editor.getAttributes('image').height).toBeNull();
});
test('resizing cannot exceed the container and cancellation retains the original width', () => {
  const { dom, handle } = mount();
  pointer(handle, 'pointerdown', 200, 100); pointer(handle, 'pointermove', 2000, 1000);
  expect(dom.style.width).toBe('100%');
  pointer(handle, 'pointercancel', 2000, 1000);
  expect(dom.style.width).toBe('40%'); expect(editor.getAttributes('image').width).toBe('40%');
});
test('resize handles support keyboard adjustment', () => {
  const { handle } = mount();
  handle.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
  expect(editor.getAttributes('image').width).toBe('42%');
});
