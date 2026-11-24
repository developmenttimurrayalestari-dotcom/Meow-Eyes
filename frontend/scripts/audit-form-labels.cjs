/* Audit native controls in application screens; UI primitives receive labels at usage sites. */
const fs = require('fs');
const path = require('path');
const { parse } = require('@babel/parser');

const sourceRoot = path.resolve(__dirname, '../src');
const problems = [];
let controlCount = 0;
let fileCount = 0;
const controlTags = new Set(['input', 'select', 'textarea', 'Input', 'Textarea', 'SelectTrigger']);

function walk(node, ancestors, visit) {
  if (!node || typeof node !== 'object') return;
  if (node.type) visit(node, ancestors);
  for (const [key, value] of Object.entries(node)) {
    if (['loc', 'start', 'end', 'extra', 'comments', 'tokens'].includes(key)) continue;
    if (Array.isArray(value)) value.forEach(child => walk(child, [...ancestors, node], visit));
    else if (value && typeof value === 'object') walk(value, [...ancestors, node], visit);
  }
}

const tag = node => node?.openingElement?.name?.name;
const attribute = (node, key) => node.openingElement.attributes.find(item => item.type === 'JSXAttribute' && item.name.name === key);
const literal = attr => attr?.value?.type === 'StringLiteral' ? attr.value.value : attr?.value?.expression?.value;
const hidden = node => /(?:^|\s)(?:sr-only|hidden)(?:\s|$)/.test(literal(attribute(node, 'className')) || '');
const labelHasText = node => node.children.some(child => child.type === 'JSXText' ? child.value.trim() : child.type === 'JSXExpressionContainer' ? child.expression.type !== 'JSXEmptyExpression' : child.type === 'JSXElement' && !controlTags.has(tag(child)));

function inspect(file) {
  const code = fs.readFileSync(file, 'utf8');
  let ast;
  try { ast = parse(code, { sourceType: 'unambiguous', plugins: ['jsx', 'typescript'] }); }
  catch (error) { problems.push(`${path.relative(sourceRoot, file)}: ${error.message}`); return; }
  fileCount += 1;
  const labels = [];
  walk(ast, [], node => {
    if (tag(node) === 'label' && attribute(node, 'htmlFor') && labelHasText(node)) labels.push(node);
  });
  const expressionKey = attr => !attr ? null : attr.value?.type === 'StringLiteral'
    ? JSON.stringify(attr.value.value)
    : attr.value?.expression ? code.slice(attr.value.expression.start, attr.value.expression.end) : null;

  walk(ast, [], (node, ancestors) => {
    if (!controlTags.has(tag(node)) || literal(attribute(node, 'type')) === 'hidden') return;
    controlCount += 1;
    const parents = ancestors.filter(item => item.type === 'JSXElement');
    const filePicker = literal(attribute(node, 'type')) === 'file' && hidden(node);
    const wrappedLabel = parents.some(parent => tag(parent) === 'label' && labelHasText(parent) && (!hidden(parent) || filePicker));
    const field = parents.some(parent => ['Field', 'FormField'].includes(tag(parent)) && attribute(parent, 'label'));
    const id = expressionKey(attribute(node, 'id'));
    const linkedLabel = id && labels.some(label => expressionKey(attribute(label, 'htmlFor')) === id && (!hidden(label) || filePicker));
    // A six-box PIN has one visible group legend and an accessible name per digit.
    const pin = literal(attribute(node, 'type')) === 'password' && literal(attribute(node, 'maxLength')) === 1 && attribute(node, 'aria-label')
      && parents.some(parent => tag(parent) === 'fieldset' && parent.children.some(child => tag(child) === 'legend' && labelHasText(child)));
    if (!wrappedLabel && !field && !linkedLabel && !pin) problems.push(`${path.relative(sourceRoot, file)}:${node.loc.start.line} <${tag(node)}> needs a visible, associated label.`);
  });
}

function scan(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      if (file !== path.join(sourceRoot, 'components/ui') && entry.name !== '__tests__') scan(file);
    } else if (/\.(js|jsx|tsx)$/.test(entry.name) && !/\.test\.|\.spec\.|setupTests/.test(entry.name)) inspect(file);
  }
}

scan(sourceRoot);
if (problems.length) {
  console.error(problems.join('\n'));
  process.exitCode = 1;
}
console.log(`Form labels: ${controlCount} controls checked in ${fileCount} source files; ${problems.length} issues.`);
