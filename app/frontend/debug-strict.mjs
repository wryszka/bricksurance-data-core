import { chromium } from 'playwright';

async function testContractGroup() {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--disable-blink-features=AutomationControlled',
      '--no-default-browser-check'
    ]
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  const allEvents = [];
  const errors = [];
  const warnings = [];
  const logs = [];

  // Intercept all console messages with their full text
  page.on('console', msg => {
    const entry = {
      type: msg.type(),
      text: msg.text(),
      timestamp: new Date().toISOString(),
      location: msg.location()
    };
    allEvents.push(entry);

    if (msg.type() === 'error') {
      errors.push(entry);
    } else if (msg.type() === 'warning') {
      warnings.push(entry);
    } else if (msg.type() === 'log') {
      logs.push(entry);
    }
  });

  page.on('pageerror', err => {
    errors.push({
      type: 'pageerror',
      name: err.name,
      message: err.message,
      stack: err.stack,
      timestamp: new Date().toISOString()
    });
  });

  page.on('requestfailed', req => {
    errors.push({
      type: 'request_failed',
      url: req.url(),
      failure: req.failure().errorText,
      timestamp: new Date().toISOString()
    });
  });

  console.log('Testing: /entity/contract_group');
  console.log('='.repeat(70));

  try {
    const response = await page.goto('http://127.0.0.1:8125/#/entity/contract_group', {
      waitUntil: 'networkidle',
      timeout: 20000
    });

    console.log(`Navigation response: ${response?.status()}`);

    // Wait for React rendering
    await page.waitForLoadState('networkidle');

    // Extra wait for any deferred errors
    await new Promise(r => setTimeout(r, 2000));

    // Inject error tracking into the page
    await page.evaluate(() => {
      window.__allErrors = [];
      const originalError = console.error;
      const originalWarn = console.warn;

      console.error = function(...args) {
        window.__allErrors.push({
          type: 'error',
          args: args.map(a => String(a))
        });
        originalError.apply(console, args);
      };

      console.warn = function(...args) {
        window.__allErrors.push({
          type: 'warning',
          args: args.map(a => String(a))
        });
        originalWarn.apply(console, args);
      };

      window.onerror = function(msg, url, line, col, err) {
        window.__allErrors.push({
          type: 'uncaught_error',
          message: msg,
          url: url,
          line: line,
          column: col,
          stack: err?.stack
        });
      };
    });

    // Wait a bit more after injection
    await new Promise(r => setTimeout(r, 1000));

    // Get any errors that were captured
    const pageErrors = await page.evaluate(() => window.__allErrors);

    // Check if page rendered
    const rendered = await page.evaluate(() => {
      const main = document.querySelector('main');
      const body = document.body;
      return {
        mainExists: !!main,
        mainHTML: main?.innerHTML.length || 0,
        bodyHTML: body.innerHTML.length,
        title: document.querySelector('h2')?.textContent || 'No title',
        hasContent: body.innerText.length > 100
      };
    });

    console.log(`\nPage Rendering:`);
    console.log(JSON.stringify(rendered, null, 2));

    console.log(`\n\nAll Events Captured (${allEvents.length}):`);
    if (allEvents.length === 0) {
      console.log('  (No console messages)');
    } else {
      allEvents.forEach((event, i) => {
        console.log(`  ${i + 1}. [${event.type}] ${event.text}`);
      });
    }

    console.log(`\nPage-Tracked Errors (${pageErrors.length}):`);
    if (pageErrors.length === 0) {
      console.log('  (No errors caught)');
    } else {
      pageErrors.forEach((err, i) => {
        console.log(`  ${i + 1}. [${err.type}] ${JSON.stringify(err)}`);
      });
    }

    console.log(`\nPage Errors (${errors.length}):`);
    if (errors.length === 0) {
      console.log('  (No errors)');
    } else {
      errors.forEach((err, i) => {
        console.log(`  ${i + 1}.`, err);
      });
    }

    console.log(`\nWarnings (${warnings.length}):`);
    if (warnings.length === 0) {
      console.log('  (No warnings)');
    } else {
      warnings.forEach((warn, i) => {
        console.log(`  ${i + 1}. ${warn.text}`);
      });
    }

  } catch (e) {
    console.error(`Error during navigation/testing:`, e.message);
    console.error(e.stack);
  }

  await browser.close();
}

testContractGroup();
