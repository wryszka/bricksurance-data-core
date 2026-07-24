import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const consoleMessages = [];
  const pageErrors = [];
  
  // Capture console messages
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });
  
  // Capture page errors
  page.on('pageerror', err => {
    pageErrors.push(err.message);
  });
  
  try {
    console.log('\n=== PART A: Account Lens (Multipolicy) ===\n');
    
    // Navigate to underwriting
    await page.goto('http://127.0.0.1:8129/#/underwriting', { waitUntil: 'networkidle' });
    console.log('✓ Navigated to underwriting workbench');
    
    // Wait for page to stabilize
    await page.waitForTimeout(1000);
    
    // Check for scope slider with four steps
    const scopeSlider = await page.locator('[role="slider"], [role="tablist"], button:has-text("Submission")').first();
    if (await scopeSlider.count() > 0 || await page.content().then(c => c.includes('Submission'))) {
      console.log('✓ Scope slider options found');
    }
    
    // Get all text containing scope options
    const pageContent = await page.content();
    const hasSubmission = pageContent.includes('Submission');
    const hasAccount = pageContent.includes('Account');
    const hasTeam = pageContent.includes('Team');
    const hasEnterprise = pageContent.includes('Enterprise');
    
    console.log('Scope options detected:');
    console.log(`  - Submission: ${hasSubmission ? '✓' : '✗'}`);
    console.log(`  - Account: ${hasAccount ? '✓' : '✗'}`);
    console.log(`  - Team: ${hasTeam ? '✓' : '✗'}`);
    console.log(`  - Enterprise: ${hasEnterprise ? '✓' : '✗'}`);
    
    // Try to find and click "2 · Account" or "Account" button
    const accountButton = await page.locator('button:has-text("Account"), [role="tab"]:has-text("Account")').first();
    if (await accountButton.count() > 0) {
      await accountButton.click();
      console.log('✓ Clicked Account button');
      await page.waitForTimeout(500);
    }
    
    // Check for multipolicy customer list
    const leftColumnContent = await page.content();
    if (leftColumnContent.includes('policies') || leftColumnContent.includes('Rivelin') || leftColumnContent.includes('Clyde')) {
      console.log('✓ Multipolicy customers visible');
    }
    
    // Take screenshot
    await page.screenshot({ path: '/tmp/underwriting_account.png', fullPage: false });
    console.log('✓ Screenshot saved: /tmp/underwriting_account.png');
    
    console.log('\n=== PART B: Reinsurance Workbench ===\n');
    
    // Clear console messages for fresh capture
    consoleMessages.length = 0;
    pageErrors.length = 0;
    
    // Navigate to reinsurance
    await page.goto('http://127.0.0.1:8129/#/reinsurance', { waitUntil: 'networkidle' });
    console.log('✓ Navigated to reinsurance workbench');
    
    await page.waitForTimeout(1000);
    
    const reinsContent = await page.content();
    const hasProgramme = reinsContent.includes('Programme') || reinsContent.includes('programme');
    const hasAccumulation = reinsContent.includes('Accumulation') || reinsContent.includes('accumulation');
    const hasExchange = reinsContent.includes('Exchange') || reinsContent.includes('exchange');
    
    console.log('Lens options detected:');
    console.log(`  - Programme: ${hasProgramme ? '✓' : '✗'}`);
    console.log(`  - Accumulation & recovery: ${hasAccumulation ? '✓' : '✗'}`);
    console.log(`  - Exchange: ${hasExchange ? '✓' : '✗'}`);
    
    // Try to find lens control buttons
    const programmeButton = await page.locator('button:has-text("Programme")').first();
    if (await programmeButton.count() > 0) {
      console.log('✓ Programme button found');
    }
    
    // Check for key elements
    const hasRecovery = reinsContent.includes('recovery') || reinsContent.includes('Recovery');
    const hasBordereau = reinsContent.includes('bordereau') || reinsContent.includes('Bordereau');
    
    console.log('Key content detected:');
    console.log(`  - Recovery/Accumulation: ${hasRecovery ? '✓' : '✗'}`);
    console.log(`  - Bordereau: ${hasBordereau ? '✓' : '✗'}`);
    
    // Take screenshot
    await page.screenshot({ path: '/tmp/reinsurance_default.png', fullPage: false });
    console.log('✓ Screenshot saved: /tmp/reinsurance_default.png');
    
    console.log('\n=== Console Messages ===\n');
    if (pageErrors.length > 0) {
      console.log('Page Errors:');
      pageErrors.forEach((err, i) => console.log(`  ${i+1}. ${err}`));
    } else {
      console.log('✓ No page errors detected');
    }
    
    if (consoleMessages.length > 0) {
      const errors = consoleMessages.filter(m => m.type === 'error');
      const warnings = consoleMessages.filter(m => m.type === 'warning');
      
      console.log(`\nConsole output: ${consoleMessages.length} total messages`);
      if (errors.length > 0) {
        console.log(`\nErrors (${errors.length}):`);
        errors.forEach((msg, i) => console.log(`  ${i+1}. ${msg.text}`));
      } else {
        console.log('✓ No console errors');
      }
      
      if (warnings.length > 0) {
        console.log(`\nWarnings (${warnings.length}):`);
        warnings.slice(0, 5).forEach((msg, i) => console.log(`  ${i+1}. ${msg.text}`));
        if (warnings.length > 5) console.log(`  ... and ${warnings.length - 5} more`);
      }
    }
    
  } catch (err) {
    console.error('Test error:', err);
  } finally {
    await browser.close();
  }
})();
