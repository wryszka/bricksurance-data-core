import { chromium } from 'playwright';

const routes = [
  '/entity/contract_group',
  '/entity/claim',
  '/entity/premium_transaction',
  '/entity/legal_entity',
  '/entity/csm_movement',
  '/metric/performance_metrics',
  '/code_set/currency',
  '/lineage/entity/contract_group'
];

async function testRoute(route) {
  const browser = await chromium.launch({ headless: true });

  try {
    const page = await browser.newPage();

    const consoleMessages = [];
    const pageErrors = [];

    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      });
    });

    page.on('pageerror', err => {
      pageErrors.push({
        name: err.name,
        message: err.message,
        stack: err.stack
      });
    });

    console.log(`\n${'='.repeat(70)}`);
    console.log(`Route: ${route}`);
    console.log('='.repeat(70));

    const url = `http://127.0.0.1:8125/#${route}`;

    try {
      await page.goto(url, {
        waitUntil: 'networkidle',
        timeout: 15000
      });
    } catch (e) {
      console.log(`Navigation timed out: ${e.message}`);
    }

    // Wait a bit for deferred errors
    await new Promise(r => setTimeout(r, 2000));

    // Check page content
    const bodyHTML = await page.evaluate(() => document.body.innerHTML);
    const mainElement = await page.$('main');
    const isBlank = !mainElement || bodyHTML.length < 500;

    console.log(`Page blank: ${isBlank}`);
    console.log(`Body HTML length: ${bodyHTML.length}`);

    if (pageErrors.length > 0) {
      console.log('\n>>> PAGE ERRORS (Uncaught Exceptions):');
      pageErrors.forEach((err, i) => {
        console.log(`\nError #${i + 1}:`);
        console.log(`Name: ${err.name}`);
        console.log(`Message: ${err.message}`);
        console.log(`Stack:\n${err.stack}`);
      });
    }

    const errorMsgs = consoleMessages.filter(m => m.type === 'error');
    if (errorMsgs.length > 0) {
      console.log('\n>>> CONSOLE ERRORS:');
      errorMsgs.forEach((msg, i) => {
        console.log(`\nError #${i + 1}:`);
        console.log(`${msg.text}`);
        if (msg.location) {
          console.log(`Location: ${msg.location.url}:${msg.location.lineNumber}:${msg.location.columnNumber}`);
        }
      });
    }

    const warnMsgs = consoleMessages.filter(m => m.type === 'warning');
    if (warnMsgs.length > 0) {
      console.log('\n>>> CONSOLE WARNINGS:');
      warnMsgs.forEach((msg, i) => {
        console.log(`Warning #${i + 1}: ${msg.text}`);
      });
    }

    if (pageErrors.length === 0 && errorMsgs.length === 0) {
      console.log('\n✓ No errors detected');
    }

  } finally {
    await browser.close();
  }
}

(async () => {
  for (const route of routes) {
    await testRoute(route);
  }
  console.log('\n' + '='.repeat(70));
  console.log('Test complete');
})();
