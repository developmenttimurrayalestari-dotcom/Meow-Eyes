import fs from 'fs';
import path from 'path';
import { transformSync } from '@babel/core';
import traverse from '@babel/traverse';

test('development visual editing preserves text-only native Lens Index options', () => {
  const filename = path.join(__dirname, 'PrescriptionForm.jsx');
  // Jest 27 needs the installed CommonJS file instead of package exports.
  const visualEdits = require(path.join(__dirname, '../../node_modules/@emergentbase/visual-edits/dist/babel-plugin/index.js')).default;
  const { ast } = transformSync(fs.readFileSync(filename, 'utf8'), {
    filename, babelrc: false, configFile: false, ast: true, code: false,
    parserOpts: { sourceType: 'module', plugins: ['jsx'] }, plugins: [visualEdits],
  });
  let options = 0;
  const invalid = [];
  traverse(ast, {
    JSXElement(element) {
      if (element.node.openingElement.name.name === 'option') options += 1;
      else if (element.findParent(parent => parent.isJSXElement() && parent.node.openingElement.name.name === 'option')) {
        invalid.push(element.node.openingElement.name.name);
      }
    },
  });
  expect(options).toBeGreaterThan(0);
  expect(invalid).toEqual([]);
});
