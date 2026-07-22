import { chromium } from 'playwright';
import fs from 'fs';

const routes = [
  { path: '/entity/contract_group', name: 'contract_group' },
  { path: '/entity/claim', name: 'claim' },
  { path: '/entity/premium_transaction', name: 'premium_transaction' },
  { path: '/entity/legal_entity', name: 'legal_entity' },
  { path: '/entity/csm_movement', name: 'csm_movement' },
  { path: '/metric/performance_metrics', name: 'performance_metrics' },
  { path: '/code_set/currency', name: 'currency' },
  { path: '/lineage/entity/contract_group', name: 'lineage_contract_group' }
];

async function testRoute(route) {
  const browser = await chromium.launch({ headless: true });

  try {
    const page = await browser.newPage();

    const allMessages = [];
    const pageErrors = [];

    // Capture ALL console messages (log, error, warn, info, debug)
    page.on('console', msg => {
      allMessages.push({
        type: msg.type(),
        text: msg.text(),
        args: msg.args().length,
        location: msg.location()
      });
    });

    // Capture uncaught exceptions
    page.on('pageerror', err => {
      pageErrors.push({
        name: err.name,
        message: err.message,
        stack: err.stack
      });
    });

    // Also capture page crashes
    page.on('error', err => {
      pageErrors.push({
        name: 'Page Error',
        message: err.message,
        stack: err.stack
      });
    });

    console.log(`\n${'='.repeat(70)}`);
    console.log(`Route: ${route.path} (${route.name})`);
    console.log('='.repeat(70));

    const url = `http://127.0.0.1:8125/#${route.path}`;

    let navigationError = null;
    try {
      await page.goto(url, {
        waitUntil: 'load',
        timeout: 20000
      });
    } catch (e) {
      navigationError = e.message;
      console.log(`Navigation error: ${e.message}`);
    }

    // Wait longer for React to hydrate and for any deferred errors
    await new Promise(r => setTimeout(r, 3000));

    // Take a screenshot
    const screenshotPath = `/tmp/screenshot_${route.name}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`Screenshot saved: ${screenshotPath}`);

    // Check page structure
    const mainContent = await page.evaluate(() => {
      const main = document.querySelector('main');
      if (!main) return { exists: false };
      const innerText = main.innerText || '';
      const innerHTML = main.innerHTML || '';
      return {
        exists: true,
        textLength: innerText.length,
        htmlLength: innerHTML.length,
        hasContent: innerText.trim().length > 0
      };
    });

    console.log(`Main element: ${JSON.stringify(mainContent)}`);

    // Get the full error traces from the console if available
    if (allMessages.length > 0) {
      console.log(`\n>>> ALL CONSOLE MESSAGES (${allMessages.length} total):`);
      allMessages.forEach((msg, i) => {
        const prefix = msg.type === 'error' ? '✗' : msg.type === 'warning' ? '⚠' : '•';
        console.log(`${prefix} [${msg.type}] ${msg.text}`);
        if (msg.location) {
          console.log(`  └─ ${msg.location.url}:${msg.location.lineNumber}`);
        }
      });
    }

    if (pageErrors.length > 0) {
      console.log('\n>>> PAGE ERRORS (Uncaught Exceptions):');
      pageErrors.forEach((err, i) => {
        console.log(`\nError #${i + 1}: ${err.name}`);
        console.log(`Message: ${err.message}`);
        if (err.stack) {
          console.log(`Stack trace:\n${err.stack}`);
        }
      });
    }

    // Check if the page appears blank
    const bodyHTML = await page.content();
    const hasMainView = bodyHTML.includes('class="view"') || bodyHTML.includes('class="main"');
    console.log(`\nPage structure check:`);
    console.log(`  - Has main view: ${hasMainView}`);
    console.log(`  - Navigation error: ${navigationError ? 'yes' : 'no'}`);
    console.log(`  - Console errors: ${pageErrors.filter(e => e.name.includes('Error')).length}`);
    console.log(`  - Console messages: ${allMessages.length}`);

  } finally {
    await browser.close();
  }
}

(async () => {
  for (const route of routes) {
    await testRoute(route);
  }
  console.log('\n' + '='.repeat(70));
  console.log('Test complete. Screenshots in /tmp/');
})();
