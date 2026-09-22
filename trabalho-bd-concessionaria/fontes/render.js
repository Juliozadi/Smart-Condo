/* Converte os SVGs de ../diagramas em PNG (2x) com o Chromium do Playwright.
 *   node render.js */
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const dir = path.join(__dirname, '..', 'diagramas');
  const browser = await chromium.launch();
  for (const nome of ['mer', 'der']) {
    const svg = fs.readFileSync(path.join(dir, `${nome}.svg`), 'utf8');
    const [, w, h] = svg.match(/width="(\d+)" height="(\d+)"/);
    const page = await browser.newPage({
      viewport: { width: +w, height: +h }, deviceScaleFactor: 2,
    });
    await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await page.screenshot({ path: path.join(dir, `${nome}.png`) });
    await page.close();
    console.log('gerado', `${nome}.png`);
  }
  await browser.close();
})();
