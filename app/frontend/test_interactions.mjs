import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  
  const consoleLogs = [];
  page.on('console', msg => {
    consoleLogs.push({ type: msg.type(), text: msg.text(), timestamp: new Date().toISOString() });
  });
  page.on('pageerror', err => {
    consoleLogs.push({ type: 'error', text: `PAGE ERROR: ${err.message}`, timestamp: new Date().toISOString() });
  });
  
  try {
    console.log('\n' + '='.repeat(70));
    console.log('TEST PART A: ACCOUNT LENS - CLICK INTERACTIONS');
    console.log('='.repeat(70));
    
    await page.goto('http://127.0.0.1:8129/#/underwriting', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    
    // Clear initial logs
    const logsAtStart = consoleLogs.length;
    
    // Click Account button
    console.log('\n1. Clicking "2 · Account" button...');
    const accountBtn = await page.locator('button:has-text("Account")').first();
    await accountBtn.click();
    await page.waitForTimeout(1000);
    
    // Take screenshot
    await page.screenshot({ path: '/tmp/account_clicked.png' });
    console.log('   ✓ Screenshot: /tmp/account_clicked.png');
    
    // Verify content
    const accountPageContent = await page.evaluate(() => document.body.innerText);
    
    const accountChecks = {
      'Has customer list': accountPageContent.includes('Rivelin') || accountPageContent.includes('plc'),
      'Shows policies count': accountPageContent.includes('policies'),
      'Shows lines count': accountPageContent.includes('lines'),
      'Right panel prompt': accountPageContent.includes('pick') || accountPageContent.includes('select') || accountPageContent.includes('Choose')
    };
    
    console.log('\n   Content checks for Account view:');
    Object.entries(accountChecks).forEach(([label, found]) => {
      console.log(`   ${found ? '✓' : '✗'} ${label}`);
    });
    
    // Find and click a customer (try Helvetia Precision or first one with 6 policies)
    console.log('\n2. Clicking first customer with 6+ policies...');
    const customerButtons = await page.locator('[role="listitem"], button, [role="option"]').filter({ hasText: /\d+\s+policies/ }).all();
    
    if (customerButtons.length > 0) {
      // Find one with 6 policies specifically or just click first
      let targetBtn = customerButtons[0];
      
      // Try to find Helvetia if available
      for (let btn of customerButtons) {
        const text = await btn.textContent();
        if (text.includes('Helvetia') || text.includes('6 policies')) {
          targetBtn = btn;
          break;
        }
      }
      
      await targetBtn.click();
      await page.waitForTimeout(1000);
      console.log('   ✓ Customer clicked');
      
      // Check for 360 view
      const customerView = await page.evaluate(() => document.body.innerText);
      
      const viewChecks = {
        'Customer name displayed': customerView.includes('Helvetia') || customerView.includes('Rivelin') || customerView.includes('Fabrication'),
        'Policies stat tile': customerView.includes('policies') && customerView.includes('Policies'),
        'Claims data': customerView.includes('claim') || customerView.includes('Claim'),
        'Premium info': customerView.includes('premium') || customerView.includes('Premium'),
        'Lines of business': customerView.includes('line') || customerView.includes('Line')
      };
      
      console.log('\n   360 view checks:');
      Object.entries(viewChecks).forEach(([label, found]) => {
        console.log(`   ${found ? '✓' : '✗'} ${label}`);
      });
      
      await page.screenshot({ path: '/tmp/account_customer_detail.png' });
      console.log('   ✓ Screenshot: /tmp/account_customer_detail.png');
    }
    
    // Click back and verify other scopes work
    console.log('\n3. Testing other scopes still work...');
    const submissionBtn = await page.locator('button:has-text("Submission")').first();
    if (await submissionBtn.count() > 0) {
      await submissionBtn.click();
      await page.waitForTimeout(500);
      console.log('   ✓ Submission scope responsive');
    }
    
    const teamBtn = await page.locator('button:has-text("Team")').first();
    if (await teamBtn.count() > 0) {
      await teamBtn.click();
      await page.waitForTimeout(500);
      console.log('   ✓ Team scope responsive');
    }
    
    console.log('\n' + '='.repeat(70));
    console.log('TEST PART B: REINSURANCE WORKBENCH - LENS INTERACTIONS');
    console.log('='.repeat(70));
    
    const logsBeforeReins = consoleLogs.length;
    
    await page.goto('http://127.0.0.1:8129/#/reinsurance', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    console.log('\n1. Default view (Programme)...');
    let reinsContent = await page.evaluate(() => document.body.innerText);
    
    const programmeChecks = {
      'Treaties table': reinsContent.includes('TR-QS-PROP-2026') || reinsContent.includes('TREATY'),
      'Treaty types': reinsContent.includes('Quota Share') || reinsContent.includes('Xol'),
      'Submission funnel': reinsContent.includes('funnel') || reinsContent.includes('Funnel')
    };
    
    console.log('   Programme view checks:');
    Object.entries(programmeChecks).forEach(([label, found]) => {
      console.log(`   ${found ? '✓' : '✗'} ${label}`);
    });
    
    await page.screenshot({ path: '/tmp/reinsurance_programme.png' });
    console.log('   ✓ Screenshot: /tmp/reinsurance_programme.png');
    
    // Click Accumulation & recovery
    console.log('\n2. Clicking "Accumulation & recovery" lens...');
    const accumBtn = await page.locator('button:has-text("Accumulation")').first();
    if (await accumBtn.count() > 0) {
      await accumBtn.click();
      await page.waitForTimeout(1000);
      
      reinsContent = await page.evaluate(() => document.body.innerText);
      
      const accumChecks = {
        'Cat events listed': reinsContent.includes('Boreas') || reinsContent.includes('Ostara') || reinsContent.includes('Brentwood'),
        'Recovery bars': reinsContent.includes('recovery') || reinsContent.includes('Recovery'),
        'Gross/Net breakdown': reinsContent.includes('Gross') || reinsContent.includes('Net'),
        '£22M recovery visible': reinsContent.includes('22') && (reinsContent.includes('M') || reinsContent.includes('million'))
      };
      
      console.log('   Accumulation & recovery checks:');
      Object.entries(accumChecks).forEach(([label, found]) => {
        console.log(`   ${found ? '✓' : '✗'} ${label}`);
      });
      
      await page.screenshot({ path: '/tmp/reinsurance_accumulation.png' });
      console.log('   ✓ Screenshot: /tmp/reinsurance_accumulation.png');
    }
    
    // Click Exchange
    console.log('\n3. Clicking "Exchange" lens...');
    const exchangeBtn = await page.locator('button:has-text("Exchange")').first();
    if (await exchangeBtn.count() > 0) {
      await exchangeBtn.click();
      await page.waitForTimeout(1000);
      
      reinsContent = await page.evaluate(() => document.body.innerText);
      
      const exchangeChecks = {
        'Two-sided layout': reinsContent.includes('Bricksurance') && (reinsContent.match(/Bricksurance/g) || []).length >= 2,
        'Cedant bordereau': reinsContent.includes('Bricksurance SE') || reinsContent.includes('cedant'),
        'Reinsurer bordereau': reinsContent.includes('Reinsurer') || reinsContent.includes('received'),
        'Amount reconciliation': reinsContent.includes('510') || reinsContent.includes('reconcil'),
        'Green reconciliation banner': reinsContent.includes('penny') || reinsContent.includes('identical')
      };
      
      console.log('   Exchange lens checks:');
      Object.entries(exchangeChecks).forEach(([label, found]) => {
        console.log(`   ${found ? '✓' : '✗'} ${label}`);
      });
      
      await page.screenshot({ path: '/tmp/reinsurance_exchange.png' });
      console.log('   ✓ Screenshot: /tmp/reinsurance_exchange.png');
    }
    
    console.log('\n' + '='.repeat(70));
    console.log('CONSOLE ERRORS CAPTURED');
    console.log('='.repeat(70));
    
    const errors = consoleLogs.filter(l => l.type === 'error');
    const warnings = consoleLogs.filter(l => l.type === 'warning');
    
    console.log(`\nTotal console messages: ${consoleLogs.length}`);
    console.log(`Errors: ${errors.length}`);
    console.log(`Warnings: ${warnings.length}`);
    
    if (errors.length > 0) {
      console.log('\n⚠️  ERRORS FOUND:');
      errors.forEach((e, i) => {
        console.log(`\n  ${i+1}. [${e.timestamp}]`);
        console.log(`     ${e.text}`);
      });
    } else {
      console.log('\n✓ NO CONSOLE ERRORS');
    }
    
    if (warnings.length > 0) {
      console.log('\nWarnings (first 5):');
      warnings.slice(0, 5).forEach((w, i) => {
        console.log(`\n  ${i+1}. [${w.timestamp}]`);
        console.log(`     ${w.text.substring(0, 150)}`);
      });
      if (warnings.length > 5) console.log(`\n  ... and ${warnings.length - 5} more warnings`);
    }
    
  } catch (err) {
    console.error('Test error:', err.message);
  } finally {
    await browser.close();
  }
})();
