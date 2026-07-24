import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  
  const allLogs = {
    errors: [],
    warnings: [],
    logs: []
  };
  
  page.on('console', msg => {
    const entry = `${msg.text()}`;
    if (msg.type() === 'error') allLogs.errors.push(entry);
    else if (msg.type() === 'warning') allLogs.warnings.push(entry);
    else allLogs.logs.push(entry);
  });
  
  page.on('pageerror', err => allLogs.errors.push(`PAGE ERROR: ${err.message}`));
  
  try {
    console.log('\n' + '='.repeat(60));
    console.log('PART A: ACCOUNT LENS - DETAILED INSPECTION');
    console.log('='.repeat(60));
    
    await page.goto('http://127.0.0.1:8129/#/underwriting', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    
    // Get visible text to understand page structure
    const allText = await page.evaluate(() => {
      const elements = document.querySelectorAll('button, [role="tab"], h1, h2, h3, span, div');
      return Array.from(elements)
        .filter(el => el.textContent && el.textContent.trim().length < 100)
        .map(el => el.textContent.trim())
        .filter(t => t && t.length > 0)
        .slice(0, 50);
    });
    
    console.log('\nVisible page elements (first 50):');
    allText.forEach((t, i) => {
      if (i < 20) console.log(`  ${i+1}. ${t.substring(0, 60)}`);
    });
    
    // Check for scope controls
    const scopeButtons = await page.locator('button').evaluateAll(buttons => {
      return buttons
        .filter(btn => btn.textContent.includes('Submission') || btn.textContent.includes('Account') || 
                       btn.textContent.includes('Team') || btn.textContent.includes('Enterprise'))
        .map(btn => btn.textContent.trim());
    });
    
    console.log('\nScope buttons found:', scopeButtons);
    
    // Click Account button
    const accountBtn = await page.locator('button:has-text("Account")').first();
    if (await accountBtn.count() > 0) {
      console.log('✓ Account button exists, clicking...');
      await accountBtn.click();
      await page.waitForTimeout(1000);
      
      // Check for customer list
      const customers = await page.evaluate(() => {
        const text = document.body.innerText;
        const lines = text.split('\n');
        return lines.filter(l => l.includes('policies') || l.includes('Rivelin') || l.includes('Helvetia') || l.includes('Clyde')).slice(0, 5);
      });
      
      console.log('Customer content detected:');
      customers.forEach((c, i) => console.log(`  ${i+1}. ${c.substring(0, 80)}`));
    }
    
    await page.screenshot({ path: '/tmp/part_a_detailed.png' });
    console.log('✓ Screenshot: /tmp/part_a_detailed.png');
    
    console.log('\n' + '='.repeat(60));
    console.log('PART B: REINSURANCE WORKBENCH - DETAILED INSPECTION');
    console.log('='.repeat(60));
    
    // Clear logs for fresh page
    allLogs.errors = [];
    allLogs.warnings = [];
    allLogs.logs = [];
    
    await page.goto('http://127.0.0.1:8129/#/reinsurance', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    
    // Get full text content
    const reinsPageText = await page.evaluate(() => document.body.innerText);
    console.log('\nPage text content (first 800 chars):');
    console.log(reinsPageText.substring(0, 800));
    console.log('\n... [content truncated]');
    
    // Look for specific elements
    const heading = await page.evaluate(() => {
      const h1 = document.querySelector('h1')?.textContent;
      const h2 = document.querySelector('h2')?.textContent;
      return { h1, h2 };
    });
    console.log('\nHeadings found:', heading);
    
    // Find lens controls
    const lensControls = await page.locator('button, [role="tab"]').evaluateAll(buttons => {
      return buttons
        .filter(btn => btn.textContent.includes('Programme') || btn.textContent.includes('Accumulation') || 
                       btn.textContent.includes('Exchange') || btn.textContent.includes('Bordereau'))
        .map(btn => btn.textContent.trim());
    });
    
    console.log('\nLens/control buttons found:', lensControls);
    
    // Check for specific content keywords
    const hasKeywords = await page.evaluate(() => {
      const text = document.body.innerText.toLowerCase();
      return {
        programme: text.includes('programme'),
        recovery: text.includes('recovery'),
        accumulation: text.includes('accumulation'),
        exchange: text.includes('exchange'),
        bordereau: text.includes('bordereau'),
        treaty: text.includes('treaty') || text.includes('TR-'),
        cedant: text.includes('cedant'),
        reinsurer: text.includes('reinsurer')
      };
    });
    
    console.log('\nContent keywords detected:');
    Object.entries(hasKeywords).forEach(([key, found]) => {
      console.log(`  ${key}: ${found ? '✓' : '✗'}`);
    });
    
    await page.screenshot({ path: '/tmp/part_b_detailed.png' });
    console.log('\n✓ Screenshot: /tmp/part_b_detailed.png');
    
    console.log('\n' + '='.repeat(60));
    console.log('CONSOLE LOG SUMMARY');
    console.log('='.repeat(60));
    
    console.log(`\nTotal console messages: ${allLogs.logs.length + allLogs.warnings.length + allLogs.errors.length}`);
    
    if (allLogs.errors.length > 0) {
      console.log(`\n⚠️  ERRORS (${allLogs.errors.length}):`);
      allLogs.errors.slice(0, 10).forEach((e, i) => console.log(`  ${i+1}. ${e.substring(0, 100)}`));
    } else {
      console.log('\n✓ No console errors');
    }
    
    if (allLogs.warnings.length > 0) {
      console.log(`\nWarnings (${allLogs.warnings.length}):`);
      allLogs.warnings.slice(0, 5).forEach((w, i) => console.log(`  ${i+1}. ${w.substring(0, 100)}`));
    }
    
  } catch (err) {
    console.error('\nTest failed:', err.message);
  } finally {
    await browser.close();
  }
})();
