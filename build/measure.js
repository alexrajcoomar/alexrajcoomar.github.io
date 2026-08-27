/* Measure every piece that has changed since the last run.

   The count has to happen in a browser, after the page's own scripts have
   drawn whatever they draw: parsing the HTML text alone missed five charts on
   one essay, because that page builds its figures at runtime. So this serves
   the site on a local port, opens each stale page in headless Chromium, and
   records words, figures, tables and checkpoints.

   Only pages whose bytes changed are opened. The fingerprints are written
   next to the metrics so the next run knows what to skip. */
const { chromium } = require('playwright');
const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const path = require('path');

const ROOT = path.dirname(__dirname);
const SHELL = new Set(['index.html', 'library.html', 'about.html', '404.html',
                       'research.html', 'coursework.html', 'tools.html',
                       'reader.html', 'colophon.html', 'admin.html', 'atlas.html']);
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
                '.json': 'application/json', '.webmanifest': 'application/manifest+json',
                '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.svg': 'image/svg+xml', '.gif': 'image/gif', '.webp': 'image/webp',
                '.woff2': 'font/woff2', '.ico': 'image/x-icon', '.pdf': 'application/pdf' };

function readJSON(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { return fallback; }
}

const metricsPath = path.join(ROOT, 'content', 'metrics.json');
const printsPath  = path.join(ROOT, 'content', 'fingerprints.json');
const metrics = readJSON(metricsPath, {});
const prints  = readJSON(printsPath, {});

const files = fs.readdirSync(ROOT)
  .filter(f => f.endsWith('.html') && !SHELL.has(f));

// The build adds a return bar and a mobile stylesheet to each piece, and an
// earlier version of the build added the same bar in a slightly different
// shape. All of it is stripped before hashing, and the remaining whitespace is
// collapsed, so the build's own edits never make a page look changed and send
// it back to be measured again.
const INJECTED = new RegExp([
  '<!--__rb-->[\\s\\S]*?<!--\\/__rb-->',
  '<!--__rbp-->[\\s\\S]*?<!--\\/__rbp-->',
  '<!--__meta-->[\\s\\S]*?<!--\\/__meta-->',
  '<!-- injected by the site build[\\s\\S]*?-->',
  '<style id="__rb-style">[\\s\\S]*?<\\/style>',
  '<div id="__rb">[\\s\\S]*?<\\/div>',
  '<a id="__rb-pill"[^>]*>[\\s\\S]*?<\\/a>',
  "<script>\\s*\\(function\\(\\)\\{\\s*var p=document\\.getElementById\\('__rb-pill'\\)[\\s\\S]*?<\\/script>",
  '<style id="__mobile_fit">[\\s\\S]*?<\\/style>'
].join('|'), 'g');
const now = {};
for (const f of files) {
  const text = fs.readFileSync(path.join(ROOT, f), 'utf8').replace(INJECTED, '').replace(/\s+/g, ' ').trim();
  now[f] = crypto.createHash('sha1').update(text).digest('hex');
}

const stale = files.filter(f => prints[f] !== now[f] || !(f.replace(/\.html$/, '') in metrics));

// a piece that was removed from the folder should not keep its old numbers
for (const slug of Object.keys(metrics)) {
  if (!files.includes(slug + '.html')) delete metrics[slug];
}

(async () => {
  if (!stale.length) {
    fs.writeFileSync(printsPath, JSON.stringify(now, null, 1));
    fs.writeFileSync(metricsPath, JSON.stringify(sortKeys(metrics), null, 1));
    console.log('nothing changed, no page needed opening');
    return;
  }

  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html';
    const file = path.join(ROOT, rel);
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404); res.end('not found'); return;
    }
    res.writeHead(200, { 'content-type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  // port 0 lets the operating system pick a free one. A fixed port dies with
  // an unhandled EADDRINUSE if anything else on the machine is already there,
  // which turns a measuring step into a failed build for no reason.
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const PORT = server.address().port;

  // CI installs its own Chromium and needs no path; a local sandbox that
  // already has one can point at it with PW_CHROMIUM.
  const browser = await chromium.launch(
    process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
  let done = 0;
  for (const f of stale) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    try {
      await page.goto(`http://127.0.0.1:${PORT}/${encodeURIComponent(f)}`,
                      { waitUntil: 'networkidle', timeout: 45000 });
    } catch (e) { /* a page that never goes idle is still measurable */ }
    await page.waitForTimeout(700);
    try {
      metrics[f.replace(/\.html$/, '')] = await page.evaluate(() => {
        const clone = document.body.cloneNode(true);
        clone.querySelectorAll('script,style,noscript,#__rb,#__rb-pill,header.top,footer.site,.docbar,.toc,nav.main,.cmdk')
             .forEach(n => n.remove());
        const txt = (clone.textContent || '').replace(/\s+/g, ' ').trim();
        const words = txt.split(' ').filter(w => /[A-Za-z0-9]/.test(w)).length;
        // a figure is a top-level svg drawn on a real artboard, not an icon glyph
        let figures = 0;
        document.querySelectorAll('svg').forEach(s => {
          if (s.closest('header.top, footer.site, .docbar, #__rb, #__rb-pill')) return;
          if (s.parentElement && s.parentElement.closest('svg')) return;
          const vb = s.getAttribute('viewBox');
          let area = 0;
          if (vb) { const q = vb.split(/[\s,]+/).map(Number); area = (q[2] || 0) * (q[3] || 0); }
          else { const r = s.getBoundingClientRect(); area = r.width * r.height; }
          if (area >= 6000) figures++;
        });
        return { words, figures,
                 tables: document.querySelectorAll('table').length,
                 details: document.querySelectorAll('details').length };
      });
      done++;
    } catch (e) {
      console.log(`could not measure ${f}: ${e.message}`);
      if (!(f.replace(/\.html$/, '') in metrics)) {
        metrics[f.replace(/\.html$/, '')] = { words: 0, figures: 0, tables: 0, details: 0 };
      }
    }
    await ctx.close();
  }
  await browser.close();
  server.close();

  fs.writeFileSync(metricsPath, JSON.stringify(sortKeys(metrics), null, 1));
  fs.writeFileSync(printsPath, JSON.stringify(now, null, 1));
  const total = Object.values(metrics).reduce((a, m) => a + m.words, 0);
  console.log(`opened ${done} of ${files.length} pages · ${total.toLocaleString()} words on the site`);
})();

function sortKeys(o) {
  const out = {};
  for (const k of Object.keys(o).sort()) out[k] = o[k];
  return out;
}
