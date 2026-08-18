/* Render one link-preview card per piece, plus the site card.

   Every social platform, every chat app and every search result that shows a
   picture reads og:image. Without one, a link to this site pastes as a bare
   grey rectangle. The card is drawn from content/pieces.json in the site's own
   typography, so editing a title in the editor updates the card too.

   Only cards whose text changed are redrawn, on the same principle as the
   measurement step: the browser is expensive, so it opens for work that
   actually needs doing. */
const { chromium } = require('playwright');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const ROOT  = path.dirname(__dirname);
const CARDS = path.join(ROOT, 'cards');
const STAMP = path.join(ROOT, 'content', 'cards.json');

const content = JSON.parse(fs.readFileSync(path.join(ROOT, 'content', 'pieces.json'), 'utf8'));
const site = content.site;
const pieces = content.pieces;

function readJSON(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { return fallback; }
}
const old = readJSON(STAMP, {});

/* what a card depends on — nothing else forces a redraw */
function key(p) {
  return crypto.createHash('sha1')
    .update(JSON.stringify([p.t, p.s, p.k, p.c, p.d, site.short, 'v2']))
    .digest('hex').slice(0, 12);
}

const SURFACE = { independent: 'Independent work', course: 'Coursework', personal: 'Personal interest' };

function esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* The card is a page rather than an image file so the type is set by the same
   engine that sets it everywhere else, with the same fallback stack. */
function cardHTML(p) {
  const kicker = [p.k, p.c || SURFACE[p.surface], p.d].filter(Boolean).join(' &middot; ');
  const title = esc(p.t || site.short);
  const sub = esc(p.s || '');
  return `<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  @font-face{font-family:"InterVar";font-weight:100 900;font-display:block;
    src:url("https://cdnjs.cloudflare.com/ajax/libs/inter-ui/4.1.1/variable/InterVariable.woff2") format("woff2")}
  *{box-sizing:border-box;margin:0}
  body{width:1200px;height:630px;background:#faf9f6;color:#16150f;
    font-family:"InterVar",-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
    display:flex;flex-direction:column;justify-content:space-between;
    padding:72px 80px;border-left:16px solid #16150f}
  .kicker{font-size:23px;font-weight:650;letter-spacing:.13em;text-transform:uppercase;color:#6f6c63}
  h1{font-size:${title.length > 46 ? 68 : title.length > 28 ? 82 : 96}px;line-height:1.04;
     letter-spacing:-.03em;font-weight:700;max-width:15ch}
  .sub{font-size:31px;line-height:1.35;color:#55524a;max-width:30ch;margin-top:26px;font-weight:400}
  .foot{display:flex;align-items:center;gap:18px;border-top:1px solid #ddd9cf;padding-top:26px}
  .mark{display:grid;place-items:center;width:52px;height:52px;background:#16150f;color:#faf9f6;
        font-size:30px;font-weight:700;flex:none}
  .who{font-size:27px;font-weight:640}
  .host{margin-left:auto;font-size:24px;color:#6f6c63}
</style></head><body>
  <div><p class="kicker">${kicker}</p></div>
  <div><h1>${title}</h1>${sub ? `<p class="sub">${sub}</p>` : ''}</div>
  <div class="foot">
    <span class="mark">A</span>
    <span class="who">${esc(site.short)}</span>
    <span class="host">${esc(site.url.split('//')[1] || '')}</span>
  </div>
</body></html>`;
}

const siteCard = {
  t: site.short, s: 'Research, interactive study tools and references',
  k: 'Portfolio', c: '', d: '', surface: 'independent', slug: '__site'
};

(async () => {
  fs.mkdirSync(CARDS, { recursive: true });
  const wanted = {};
  const todo = [];
  for (const p of pieces.concat([siteCard])) {
    const k = key(p);
    wanted[p.slug] = k;
    const out = p.slug === '__site'
      ? path.join(ROOT, 'og-card.png')
      : path.join(CARDS, p.slug + '.png');
    if (old[p.slug] !== k || !fs.existsSync(out)) todo.push({ p, out });
  }

  // a card for a piece that no longer exists is dead weight in the repository
  for (const f of fs.readdirSync(CARDS)) {
    if (f.endsWith('.png') && !(f.replace(/\.png$/, '') in wanted)) {
      fs.unlinkSync(path.join(CARDS, f));
      console.log('removed stale card ' + f);
    }
  }

  if (!todo.length) {
    fs.writeFileSync(STAMP, JSON.stringify(wanted, null, 1));
    console.log('every card is current, nothing drawn');
    return;
  }

  const browser = await chromium.launch(
    process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
  const ctx = await browser.newContext({
    viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1
  });
  const page = await ctx.newPage();
  let drawn = 0;
  for (const { p, out } of todo) {
    try {
      await page.setContent(cardHTML(p), { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready).catch(() => {});
      await page.waitForTimeout(120);
      await page.screenshot({ path: out });
      drawn++;
    } catch (e) {
      console.log('could not draw a card for ' + p.slug + ': ' + e.message);
      delete wanted[p.slug];        // try again next run rather than record a lie
    }
  }
  await browser.close();
  fs.writeFileSync(STAMP, JSON.stringify(wanted, null, 1));
  console.log(`drew ${drawn} card(s) of ${pieces.length + 1}`);
})();
