import { vault } from './vault';

// Shared calculation/editor components can use the website-backed workspace.
// The legacy local vault remains untouched; customer entry never opens it.
let current = vault;
export function setWorkspace(workspace) { current = workspace || vault; }
export const workspace = new Proxy({}, {
  get(_target, key) {
    const value = current[key];
    return typeof value === 'function' ? value.bind(current) : value;
  },
});
