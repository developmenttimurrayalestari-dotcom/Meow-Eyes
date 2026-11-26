// Regenerate from the pinned, installed Lucide package. No network requests.
const fs = require('fs');
const path = require('path');
const parser = require('@babel/parser');
const root = path.resolve(__dirname, '..');
const packageRoot = path.dirname(require.resolve('lucide-react/package.json'));
const version = JSON.parse(fs.readFileSync(path.join(packageRoot, 'package.json'), 'utf8')).version;
function literal(node) {
  if (['StringLiteral', 'NumericLiteral', 'BooleanLiteral'].includes(node.type)) return node.value;
  if (node.type === 'NullLiteral') return null;
  if (node.type === 'ArrayExpression') return node.elements.map(literal);
  if (node.type === 'ObjectExpression') return Object.fromEntries(node.properties.map(property => {
    if (property.type !== 'ObjectProperty' || property.computed) throw Error('Unexpected icon property');
    return [property.key.name || property.key.value, literal(property.value)];
  }));
  throw Error('Unexpected icon data: ' + node.type);
}
const icons = {};
const directory = path.join(packageRoot, 'dist/esm/icons');
for (const file of fs.readdirSync(directory).filter(name => name.endsWith('.js')).sort()) {
  const source = fs.readFileSync(path.join(directory, file), 'utf8');
  const ast = parser.parse(source, { sourceType: 'module' });
  const declaration = ast.program.body.flatMap(statement => statement.type === 'VariableDeclaration' ? statement.declarations : []).find(node => node.id.name === '__iconNode');
  if (declaration) icons[file.slice(0, -3)] = literal(declaration.init);
}
if (Object.keys(icons).length < 300) throw Error('Incomplete Lucide catalog');
const license = fs.readFileSync(path.join(packageRoot, 'LICENSE'), 'utf8');
const notices = path.join(root, 'public/licenses');
fs.mkdirSync(notices, { recursive: true });
fs.writeFileSync(path.join(notices, 'lucide-react.txt'), license);
fs.writeFileSync(path.join(root, 'src/lib/iconCatalog.json'), JSON.stringify({ version, license, icons }) + '\n');
const destination = path.join(root, '../backend/mysql/data');
fs.mkdirSync(destination, { recursive: true });
fs.writeFileSync(path.join(destination, 'lucide-icon-names.json'), JSON.stringify({ version, names: Object.keys(icons) }) + '\n');
process.stdout.write(`Lucide ${version}: ${Object.keys(icons).length} icons generated.\n`);
