from pathlib import Path

root = Path(__file__).resolve().parent
source = (root/'checkout-lens-index-browser.cjs').read_text(encoding='utf-8')
start = source.index('  const server = http.createServer')
end = source.index('  let browser;', start)
source = source[:start] + source[end:]
source = source.replace("page.on('pageerror', error => errors.push(error.message));", """page.on('pageerror', error => errors.push(error.message));
    const consoleErrors = [];
    page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });""")
source = source.replace('`http://127.0.0.1:${server.address().port}/checkout`', "'http://localhost:3000/checkout'")
source = source.replace('`http://127.0.0.1:${server.address().port}/admin/lens-indexes`', "'http://localhost:3000/admin/lens-indexes'")
source = source.replace("assert.deepEqual(errors, []);", """assert.deepEqual(errors, []);
    assert.equal(await page.locator('option span').count(), 0);
    const invalidOptions = consoleErrors.filter(message => /cannot be a child of <option>|validateDOMNesting|hydration error/i.test(message));
    console.log(JSON.stringify({ invalidOptionErrors: invalidOptions.length, messages: invalidOptions.map(message => message.slice(0, 180)), savedRows: saves.length }));
    if (invalidOptions.length) throw new Error('Development compiler inserted invalid option descendants');""")
source = source.replace("await new Promise(resolve => server.close(resolve));", '')
source = source.replace('checkout-lens-index-browser-report.json', 'prescription-development-browser-report.json')
(root/'prescription-development-browser.cjs').write_text(source, encoding='utf-8')
print('Prepared existing development-server browser regression')
