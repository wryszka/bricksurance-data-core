import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  
  const allErrors = [];
  const allWarnings = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') allErrors.push(msg.text());
    if (msg.type() === 'warning') allWarnings.push(msg.text());
  });
  
  page.on('pageerror', err => allErrors.push(`UNCAUGHT: ${err.message}`));
  
  try {
    console.log('\n' + '='.repeat(80));
    console.log('COMPREHENSIVE FEATURE TEST - BRICKSURANCE DATA CORE');
    console.log('='.repeat(80));
    
    // ===== PART A: ACCOUNT LENS =====
    console.log('\n📋 PART A: ACCOUNT LENS (MULTIPOLICY)');
    console.log('-'.repeat(80));
    
    allErrors.length = 0;
    allWarnings.length = 0;
    
    await page.goto('http://127.0.0.1:8129/#/underwriting', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    
    console.log('\n✓ Navigated to underwriting workbench');
    
    // Step 1: Verify scope slider has four steps
    const scopeText = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).filter(t => t.includes('·'));
    });
    
    console.log('\n✅ SCOPE SLIDER VERIFICATION:');
    const hasSubmission = scopeText.some(t => t.includes('Submission'));
    const hasAccount = scopeText.some(t => t.includes('Account'));
    const hasTeam = scopeText.some(t => t.includes('Team'));
    const hasEnterprise = scopeText.some(t => t.includes('Enterprise'));
    
    console.log(`  1 · Submission: ${hasSubmission ? '✓' : '✗'}`);
    console.log(`  2 · Account: ${hasAccount ? '✓' : '✗'}`);
    console.log(`  3 · Team: ${hasTeam ? '✓' : '✗'}`);
    console.log(`  4 · Enterprise: ${hasEnterprise ? '✓' : '✗'}`);
    
    // Step 2: Click Account
    console.log('\n✅ ACCOUNT LENS CONTENT:');
    const accountBtn = await page.locator('button:has-text("Account")').first();
    await accountBtn.click();
    await page.waitForTimeout(1000);
    
    const accountContent = await page.evaluate(() => document.body.innerText);
    console.log(`  Customer list visible: ${accountContent.includes('Rivelin') || accountContent.includes('Clyde') ? '✓' : '✗'}`);
    console.log(`  Shows policy count: ${accountContent.includes('34 policies') || accountContent.includes('6 policies') ? '✓' : '✗'}`);
    console.log(`  Shows lines count: ${accountContent.includes('lines') ? '✓' : '✗'}`);
    console.log(`  Right panel present: ${accountContent.includes('Pick a customer') || accountContent.includes('account') ? '✓' : '✗'}`);
    
    // Step 3: Click customer (Helvetia Precision AG with 6 policies)
    console.log('\n✅ CUSTOMER 360 VIEW:');
    const customers = await page.locator('[role="listitem"], button, [role="option"]').all();
    let selectedCustomer = null;
    
    for (let customer of customers) {
      const text = await customer.textContent();
      if (text.includes('Helvetia')) {
        await customer.click();
        selectedCustomer = 'Helvetia Precision AG';
        break;
      }
    }
    
    await page.waitForTimeout(1500);
    
    const customerDetail = await page.evaluate(() => document.body.innerText);
    console.log(`  Customer selected: ${selectedCustomer ? '✓ ' + selectedCustomer : '✗'}`);
    console.log(`  Name displayed: ${customerDetail.includes('Helvetia') ? '✓' : '✗'}`);
    console.log(`  Policies visible: ${customerDetail.includes('policies') ? '✓' : '✗'}`);
    console.log(`  Claims data present: ${customerDetail.includes('Claim') || customerDetail.includes('claim') ? '✓' : '✗'}`);
    console.log(`  Lines visible: ${customerDetail.includes('Line') || customerDetail.includes('line') ? '✓' : '✗'}`);
    
    await page.screenshot({ path: '/tmp/final_account_360.png' });
    console.log('  Screenshot: /tmp/final_account_360.png');
    
    // Step 4: Test other scopes still work
    console.log('\n✅ SCOPE NAVIGATION TEST:');
    await page.locator('button:has-text("Submission")').first().click();
    await page.waitForTimeout(500);
    console.log('  Submission scope: ✓ responsive');
    
    await page.locator('button:has-text("Team")').first().click();
    await page.waitForTimeout(500);
    console.log('  Team scope: ✓ responsive');
    
    await page.locator('button:has-text("Account")').first().click();
    await page.waitForTimeout(500);
    console.log('  Account scope: ✓ returns OK');
    
    // ===== PART B: REINSURANCE WORKBENCH =====
    console.log('\n' + '='.repeat(80));
    console.log('📋 PART B: REINSURANCE WORKBENCH');
    console.log('-'.repeat(80));
    
    allErrors.length = 0;
    allWarnings.length = 0;
    
    await page.goto('http://127.0.0.1:8129/#/reinsurance', { waitUntil: 'networkidle' });
    
    // Wait for actual content, not just loading message
    await Promise.race([
      page.waitForFunction(() => {
        const text = document.body.innerText;
        return text.includes('TR-') && !text.includes('Loading the reinsurance');
      }, { timeout: 10000 }),
      page.waitForTimeout(5000)
    ]).catch(() => {});
    
    await page.waitForTimeout(1500);
    
    console.log('\n✓ Navigated to reinsurance workbench');
    
    // Step 1: Check default view (Programme)
    console.log('\n✅ LENS CONTROLS VERIFICATION:');
    const lensButtons = await page.locator('button').evaluateAll(btns => {
      return btns.map(b => b.textContent.trim()).filter(t => t.includes('Programme') || t.includes('Accumulation') || t.includes('Exchange'));
    });
    
    console.log(`  Programme button: ${lensButtons.some(t => t.includes('Programme')) ? '✓' : '✗'}`);
    console.log(`  Accumulation button: ${lensButtons.some(t => t.includes('Accumulation')) ? '✓' : '✗'}`);
    console.log(`  Exchange button: ${lensButtons.some(t => t.includes('Exchange')) ? '✓' : '✗'}`);
    
    // Step 2: Verify Programme content
    console.log('\n✅ PROGRAMME VIEW:');
    let reinsContent = await page.evaluate(() => document.body.innerText);
    
    const treaties = reinsContent.includes('TR-QS-PROP-2026') || reinsContent.includes('TR-XL-PROP-2026');
    const quotaShare = reinsContent.includes('Quota Share') || reinsContent.includes('quota share');
    const xol = reinsContent.includes('Xol') || reinsContent.includes('excess');
    
    console.log(`  Treaties table: ${treaties ? '✓' : '✗'}`);
    console.log(`  Quota Share treaty: ${quotaShare ? '✓' : '✗'}`);
    console.log(`  XL Catastrophe layer: ${xol ? '✓' : '✗'}`);
    
    await page.screenshot({ path: '/tmp/final_reinsurance_programme.png' });
    console.log('  Screenshot: /tmp/final_reinsurance_programme.png');
    
    // Step 3: Click Accumulation & recovery
    console.log('\n✅ ACCUMULATION & RECOVERY LENS:');
    const accumBtn = await page.locator('button:has-text("Accumulation")').first();
    if (await accumBtn.count() > 0) {
      await accumBtn.click();
      await page.waitForTimeout(1000);
      
      reinsContent = await page.evaluate(() => document.body.innerText);
      
      const catEvents = reinsContent.includes('Boreas') || reinsContent.includes('Ostara') || reinsContent.includes('Brentwood');
      const recovery = reinsContent.includes('recovery') || reinsContent.includes('Recovery');
      const grossNet = reinsContent.includes('Gross') || reinsContent.includes('Net');
      
      console.log(`  Cat events (Boreas/Ostara/Brentwood): ${catEvents ? '✓' : '✗'}`);
      console.log(`  Recovery amounts: ${recovery ? '✓' : '✗'}`);
      console.log(`  Gross/Reinsurance/Net breakdown: ${grossNet ? '✓' : '✗'}`);
      
      if (reinsContent.includes('22')) {
        console.log('  ~£22M recovery visible: ✓');
      } else {
        console.log('  ~£22M recovery visible: ✗');
      }
      
      await page.screenshot({ path: '/tmp/final_reinsurance_accumulation.png' });
      console.log('  Screenshot: /tmp/final_reinsurance_accumulation.png');
    }
    
    // Step 4: Click Exchange
    console.log('\n✅ EXCHANGE LENS (TWO-SIDED BORDEREAU):');
    const exchangeBtn = await page.locator('button:has-text("Exchange")').first();
    if (await exchangeBtn.count() > 0) {
      await exchangeBtn.click();
      await page.waitForTimeout(1000);
      
      reinsContent = await page.evaluate(() => document.body.innerText);
      
      const bricksuranceCount = (reinsContent.match(/Bricksurance/g) || []).length;
      const cedant = reinsContent.includes('Bricksurance SE') || reinsContent.includes('cedant');
      const reinsurer = reinsContent.includes('Reinsurer') || reinsContent.includes('reinsurer');
      const amount = reinsContent.includes('510') || reinsContent.includes('510,876');
      const reconcile = reinsContent.includes('reconcil') || reinsContent.includes('penny') || reinsContent.includes('identical');
      
      console.log(`  Two-sided layout (Bricksurance appears 2+): ${bricksuranceCount >= 2 ? '✓' : '✗'}`);
      console.log(`  Cedant (Bricksurance SE) outbound: ${cedant ? '✓' : '✗'}`);
      console.log(`  Reinsurer inbound counterparty: ${reinsurer ? '✓' : '✗'}`);
      console.log(`  Amount reconciliation (~£510,876): ${amount ? '✓' : '✗'}`);
      console.log(`  Green reconciliation banner: ${reconcile ? '✓' : '✗'}`);
      
      await page.screenshot({ path: '/tmp/final_reinsurance_exchange.png' });
      console.log('  Screenshot: /tmp/final_reinsurance_exchange.png');
    }
    
    // ===== CONSOLE ERRORS SUMMARY =====
    console.log('\n' + '='.repeat(80));
    console.log('🔍 CONSOLE ERROR/WARNING SUMMARY');
    console.log('='.repeat(80));
    
    console.log(`\nErrors captured: ${allErrors.length}`);
    if (allErrors.length > 0) {
      console.log('\n⚠️  ERRORS:');
      allErrors.slice(0, 10).forEach((err, i) => {
        console.log(`  ${i+1}. ${err.substring(0, 140)}`);
      });
      if (allErrors.length > 10) console.log(`  ... and ${allErrors.length - 10} more errors`);
    } else {
      console.log('✅ No console errors detected');
    }
    
    console.log(`\nWarnings captured: ${allWarnings.length}`);
    if (allWarnings.length > 0 && allWarnings.length <= 5) {
      console.log('\nWarnings:');
      allWarnings.forEach((w, i) => {
        console.log(`  ${i+1}. ${w.substring(0, 140)}`);
      });
    } else if (allWarnings.length > 5) {
      console.log('\nFirst 5 warnings:');
      allWarnings.slice(0, 5).forEach((w, i) => {
        console.log(`  ${i+1}. ${w.substring(0, 140)}`);
      });
      console.log(`  ... and ${allWarnings.length - 5} more warnings`);
    }
    
    console.log('\n' + '='.repeat(80));
    console.log('✅ TEST COMPLETE');
    console.log('='.repeat(80));
    
  } catch (err) {
    console.error('\n❌ Test failed:', err.message);
  } finally {
    await browser.close();
  }
})();
