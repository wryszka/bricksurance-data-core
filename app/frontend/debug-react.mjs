import { chromium } from 'playwright';

async function debugReact() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Capture logs to detect React warnings/errors
  const consoleLogs = [];
  page.on('console', msg => {
    consoleLogs.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });

  page.on('pageerror', err => {
    console.error(`PAGE ERROR: ${err.name}: ${err.message}`);
    console.error(`Stack: ${err.stack}`);
  });

  await page.goto('http://127.0.0.1:8125/#/entity/contract_group', {
    waitUntil: 'networkidle'
  });

  await page.waitForTimeout(2000);

  // Check for React DevTools
  const hasReactDevTools = await page.evaluate(() => {
    return typeof window.__REACT_DEVTOOLS_GLOBAL_HOOK__ !== 'undefined';
  });

  console.log('Has React DevTools:', hasReactDevTools);

  // Check the rendered app structure
  const appStructure = await page.evaluate(() => {
    const app = document.querySelector('.app');
    const main = document.querySelector('main');
    const view = document.querySelector('.view');

    return {
      appExists: !!app,
      appClass: app?.className || '',
      mainExists: !!main,
      mainClass: main?.className || '',
      viewExists: !!view,
      viewClass: view?.className || '',
      mainText: main?.innerText.substring(0, 100) || 'none',
      documentTitle: document.title,
      htmlLength: document.documentElement.innerHTML.length
    };
  });

  console.log('\nApp Structure:');
  console.log(JSON.stringify(appStructure, null, 2));

  // Check for any error boundaries or error overlays
  const errorElements = await page.evaluate(() => {
    return {
      errorDivCount: document.querySelectorAll('[class*="error"]').length,
      errorOverlays: document.querySelectorAll('[class*="overlay"], [role="alertdialog"]').length,
      visibleElements: {
        h1: document.querySelectorAll('h1:visible').length,
        h2: document.querySelectorAll('h2:visible').length,
        p: document.querySelectorAll('p:visible').length,
        main: !!document.querySelector('main:visible')
      }
    };
  });

  console.log('\nError Detection:');
  console.log(JSON.stringify(errorElements, null, 2));

  console.log('\nConsole Output:');
  if (consoleLogs.length === 0) {
    console.log('  (No console messages)');
  } else {
    consoleLogs.forEach(log => {
      console.log(`  [${log.type}] ${log.text}`);
      if (log.location) {
        console.log(`      at ${log.location.url}:${log.location.lineNumber}`);
      }
    });
  }

  // Test all routes and capture their success/failure
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

  console.log('\n' + '='.repeat(70));
  console.log('Route Test Summary:');
  console.log('='.repeat(70));

  for (const route of routes) {
    const response = await page.goto(`http://127.0.0.1:8125/#${route}`, {
      waitUntil: 'networkidle'
    });

    await page.waitForTimeout(500);

    const isRendered = await page.evaluate(() => {
      const main = document.querySelector('main');
      return main && main.innerText.length > 50;
    });

    const status = response?.status();
    console.log(`${route.padEnd(40)} ${status === 200 ? '✓' : '✗'} (rendered: ${isRendered})`);
  }

  await browser.close();
}

debugReact().catch(console.error);
