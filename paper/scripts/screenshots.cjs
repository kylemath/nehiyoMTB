// Headless Chromium screenshots of docs/ served locally (called by fig_screenshots.py).
// usage: node screenshots.cjs <baseUrl> <outDir> <json list of [name, path, w, h, waitMs, clickText?, thenPath?]>
const { chromium } = require('playwright');
(async () => {
  const [base, outDir, listJson] = process.argv.slice(2);
  const shots = JSON.parse(listJson);
  const browser = await chromium.launch();
  for (const [name, path, w, h, wait, click, then] of shots) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    const page = await ctx.newPage();
    // block every third-party request so the render is offline and repeatable
    await page.route('**/*', (r) => (r.request().url().startsWith(base) ? r.continue() : r.abort()));
    try {
      await page.goto(base + path, { waitUntil: 'load', timeout: 30000 });
      await page.waitForTimeout(wait);
      if (click) {
        // e.g. enter the app as a guest before capturing its screens
        await page.getByText(click, { exact: false }).first().click({ timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(wait);
      }
      if (then) {
        await page.goto(base + then, { waitUntil: 'load', timeout: 30000 });
        await page.waitForTimeout(wait);
      }
      await page.screenshot({ path: `${outDir}/${name}` });
      console.log('screenshot:', name);
    } catch (e) {
      console.log('screenshot failed:', name, String(e).split('\n')[0]);
    }
    await ctx.close();
  }
  await browser.close();
})();
