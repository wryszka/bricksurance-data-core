import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  
  const allLogs = [];
  page.on('console', msg => allLogs.push({ type: msg.type(), text: msg.text() }));
  page.on('pageerror', err => allLogs.push({ type: 'error', text: `PAGE ERROR: ${err.message}` }));
  
  try {
    console.log('Navigating to reinsurance workbench...');
    await page.goto('http://127.0.0.1:8129/#/reinsurance', { waitUntil: 'networkidle' });
    
    console.log('Waiting for reinsurance content to load (max 10 seconds)...');
    
    // Wait for the loading message to disappear OR for actual content to appear
    await Promise.race([
      page.waitForFunction(() => {
        const text = document.body.innerText;
        return (text.includes('TR-') || text.includes('Programme') || text.includes('Accumulation')) && !text.includes('Loading');
      }, { timeout: 8000 }),
      page.waitForTimeout(5000)
    ]).catch(() => {});
    
    await page.waitForTimeout(2000);
    
    console.log('\n' + '='.repeat(70));
    console.log('REINSURANCE PAGE - CONTENT CHECK');
    console.log('='.repeat(70));
    
    const fullText = await page.evaluate(() => document.body.innerText);
    
    // Check for all expected content
    const checks = {
      'Programme lens': fullText.includes('Programme'),
      'Accumulation & recovery': fullText.includes('Accumulation') || fullText.includes('accumulation'),
      'Exchange lens': fullText.includes('Exchange') || fullText.includes('exchange'),
      'Treaty data (TR-)': fullText.includes('TR-'),
      'Bordereau content': fullText.includes('bordereau') || fullText.includes('Bordereau'),
      'Recovery amounts': fullText.includes('recovery') || fullText.includes('Recovery'),
      'Cedant label': fullText.includes('cedant') || fullText.includes('Cedant'),
      'Reinsurer label': fullText.includes('reinsurer') || fullText.includes('Reinsurer'),
      'Policies reference': fullText.includes('policies') || fullText.includes('Policies'),
      'Limit amount': fullText.includes('limit') || fullText.includes('Limit')
    };
    
    console.log('\nContent checks:');
    Object.entries(checks).forEach(([label, found]) => {
      console.log(`  ${found ? '✓' : '✗'} ${label}`);
    });
    
    // Show first 1000 chars of actual content
    console.log('\nFirst 1000 characters of page content:');
    console.log('---');
    console.log(fullText.substring(0, 1000));
    console.log('---\n');
    
    // Get all buttons
    const buttons = await page.locator('button').evaluateAll(btns => 
      btns.map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 100)
    );
    
    if (buttons.length > 0) {
      console.log('Buttons found:');
      buttons.slice(0, 15).forEach((b, i) => console.log(`  ${i+1}. ${b}`));
    }
    
    // Check for lens navigation (tabs, toggles, etc)
    const tabs = await page.locator('[role="tab"], [role="tablist"]').count();
    const radios = await page.locator('[role="radio"], [role="radiogroup"]').count();
    console.log(`\nUI controls: ${tabs} tabs, ${radios} radio groups`);
    
    // Take full screenshot
    await page.screenshot({ path: '/tmp/reinsurance_loaded.png' });
    console.log('✓ Screenshot: /tmp/reinsurance_loaded.png');
    
    console.log('\n' + '='.repeat(70));
    console.log('CONSOLE MESSAGES');
    console.log('='.repeat(70));
    
    const errors = allLogs.filter(l => l.type === 'error');
    const warnings = allLogs.filter(l => l.type === 'warning');
    const logs = allLogs.filter(l => l.type === 'log');
    
    console.log(`\nTotal: ${allLogs.length} messages (${logs.length} logs, ${warnings.length} warnings, ${errors.length} errors)`);
    
    if (errors.length > 0) {
      console.log('\nErrors:');
      errors.forEach((e, i) => console.log(`  ${i+1}. ${e.text.substring(0, 120)}`));
    } else {
      console.log('\n✓ No console errors');
    }
    
    if (warnings.length > 0) {
      console.log('\nWarnings:');
      warnings.slice(0, 5).forEach((w, i) => console.log(`  ${i+1}. ${w.text.substring(0, 120)}`));
    }
    
  } catch (err) {
    console.error('Error:', err.message);
  } finally {
    await browser.close();
  }
})();
