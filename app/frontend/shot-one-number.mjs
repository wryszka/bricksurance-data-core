import { chromium } from 'playwright';
const base = process.argv[2] || 'http://localhost:8765';
const out = '/tmp/onenum/shots';
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 1000 } });
const errs=[]; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
const beats=['question','today','no-context','rulebook','ask-again','change','path'];
for (const [i,k] of beats.entries()) {
  await p.goto(`${base}/#/one-number/${k}`); await p.waitForSelector('.on-stage', { timeout: 30000 }); await p.waitForTimeout(500);
  for (const btn of await p.locator('button:has-text("Show saved answer")').all()) { await btn.click(); await p.waitForTimeout(2500); }
  for (const btn of await p.locator('button:has-text("What am I seeing")').all()) { await btn.click(); }
  await p.screenshot({ path: `${out}/${i}-${k}.png`, fullPage: true });
}
console.log('errors:', errs.slice(0,10));
await b.close();
