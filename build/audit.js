/* Measure in a browser what the generated pages claim about themselves.

   The register on the controls page prints these results beside the claims
   they test. Each page is measured against a fingerprint of its inputs, computed
   by build/claims.py so the browser and the build agree on what "the same
   page" means; a page whose inputs moved since its record is measured again,
   the rest are kept. Results go to content/audit.json.

   Per page (every listed piece, the transcripts and the generated pages):
     ext    requests made, and how many left this origin
     idle   frames requested in the second after the page settled
     fit    whether the document is wider than a 320px viewport
     errors console errors
   The editor (admin.html), hand-maintained, on its own terms:
     admin  console errors, uncaught exceptions and failed requests, served
            from this tree with no connection saved; the tabs, the search and
            the theme button; what the connection form stores and where; then,
            connected through a stub of GitHub's API that serves this tree's
            content and refuses every write, the list, the search, the editor,
            an edit, the guard without a token, the files and the site text
   On the home page:
     theme     the selector's two states, its one pulse, its settled switch
     corona    the light behind the sphere names the faced row's origin
     descent   each featured row scrolled to the reading line at 1440 and
               at 390: the document the sphere faces, and the frames
               requested once the scroll has stopped
   Per generated page, which share site.css and site.js:
     keyboard  Tab stops, and how many had no visible focus ring
     print     under print media: sticky elements still pinned, blocks of
               text left hidden, figures allowed to break across pages
     motion    animations running under prefers-reduced-motion
   Once, for the worker:
     offline   files held before and after a simulated publish, and whether
               the page that changed was refreshed in the saved copy

   Falsified (--falsify): each runtime claim is made false on a copy of a
   page at its source (an image from another origin, a frame loop, a
   stylesheet that removes the focus ring, a print rule that lets figures
   break, an animation under reduced motion, a 900px block, a build-owned
   block carrying words, a syntax error in the editor, a stylesheet the
   editor cannot find, the editor's token written to long-term storage, a
   worker that forgets the saved copy, a worker that stores the editor), the same
   measurements are taken, and the results go to content/negatives.json
   under "runtime", where the register grades them with the same rule it
   grades the real pages by. A falsification the rule does not fail is a
   claim the register prints as untested.

   usage: node build/audit.js [--all] [--no-offline] [--only a.html,b.html] [--falsify]
   CI installs playwright beside the site; a machine with its own copy can
   point at it with PW_MODULE, and at a browser with PW_CHROMIUM. */
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const { execFileSync } = require('child_process');

const ROOT = path.dirname(__dirname);
const OUT_PATH = path.join(ROOT, 'content', 'audit.json');
const ALL = process.argv.includes('--all');
const ONLY = (() => { const i = process.argv.indexOf('--only'); return i > -1 ? process.argv[i + 1].split(',') : null; })();
const NO_OFFLINE = process.argv.includes('--no-offline');
const FALSIFY = process.argv.includes('--falsify');
const NEG_PATH = path.join(ROOT, 'content', 'negatives.json');
const { chromium } = require(process.env.PW_MODULE || 'playwright');
const LAUNCH = Object.assign({ args: ['--no-sandbox'] },
  process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});

const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
                '.json': 'application/json', '.webmanifest': 'application/manifest+json',
                '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
                '.woff2': 'font/woff2', '.pdf': 'application/pdf', '.md': 'text/markdown',
                '.csv': 'text/csv', '.py': 'text/plain', '.txt': 'text/plain' };

function serve(root) {
  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html';
    const file = path.join(root, rel);
    if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404); res.end('not found'); return;
    }
    res.writeHead(200, { 'content-type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream',
                         'cache-control': 'no-store' });
    fs.createReadStream(file).pipe(res);
  });
  return server;
}

function listen(server, port) {
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port || 0, '127.0.0.1', () => resolve(server.address().port));
  });
}

function readJSON(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { return fallback; }
}

/* The fingerprints come from the build's own module, so the build and the
   audit cannot disagree about which record belongs to which page. */
function digests() {
  const out = execFileSync('python3', [path.join(ROOT, 'build', 'claims.py'), '--digests'], { encoding: 'utf8' });
  return JSON.parse(out);
}

function git(args) {
  try { return execFileSync('git', args, { cwd: ROOT, encoding: 'utf8' }).trim(); } catch (e) { return ''; }
}

const RAF_COUNTER = `(function(){var n=0,o=window.requestAnimationFrame;
  window.requestAnimationFrame=function(cb){n++;return o.call(window,cb)};
  window.__rafReset=function(){n=0};window.__pageRaf=function(){return n};})();`;

/* The editor, admin.html, is hand-maintained and talks to GitHub, so it is
   measured on its own terms rather than under the rows the generated pages
   share. Served from this tree with no connection saved, it must load with
   no console error, no uncaught exception and no failed request, ask nothing
   of another origin, request no frame while idle, and its tabs and search
   must answer before a connection exists. Then, connected through a stub of
   GitHub's API on the same page (this tree's content/pieces.json and file
   list served back, every write refused), its controls must respond and
   nothing may be written; the repository stays in this browser and the token
   in this tab's session only. At 320px nothing may overflow. The numbers it
   is held to (the pieces, the files, a search's matches) are the tree's own. */
const EDITOR = 'admin.html';
async function measureEditor(browser, base) {
  const rec = {};
  const content = readJSON(path.join(ROOT, 'content', 'pieces.json'), { pieces: [], site: {} });
  const files = fs.readdirSync(ROOT).filter(f => { try { return fs.statSync(path.join(ROOT, f)).isFile(); } catch (e) { return false; } });
  const a = { errors: 0, failed: 0, requests: 0, external: 0, stubbed: 0, writes: 0, idleFrames: -1,
              tabs: 0, switched: 0, threwUnconnected: 0, themeSwitched: false, themeStored: false,
              cfgSaved: false, tokenInSession: false, tokenInLocal: true, rows: -1, pieces: (content.pieces || []).length,
              searched: -1, searchExpected: -1, editorOpened: false, editEnabledPublish: false, promptShown: false,
              forgotten: false, guardHeld: false, files: -1, filesExpected: -1, siteFields: 0, scrollWidth: 0, overflow: true };
  const watch = page => {
    page.on('console', m => { if (m.type() === 'error') a.errors++; });
    page.on('pageerror', () => { a.errors++; });
    page.on('response', r => { if (r.status() >= 400) a.failed++; });
    page.on('requestfailed', () => { a.failed++; });
    page.on('request', r => { const u = r.url(); a.requests++; if (!u.startsWith(base) && !u.startsWith('data:') && !u.startsWith('https://api.github.com/')) a.external++; });
    return page.route('https://api.github.com/**', route => {
      const req = route.request(); const u = new URL(req.url());
      if (req.method() !== 'GET') { a.writes++; return route.fulfill({ status: 500, contentType: 'application/json', body: '{"message":"the audit refuses writes"}' }); }
      a.stubbed++;
      if (u.pathname.endsWith('/contents/content/pieces.json')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ content: fs.readFileSync(path.join(ROOT, 'content', 'pieces.json')).toString('base64') }) });
      if (u.pathname.indexOf('/git/trees/') >= 0) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ tree: files.map(f => ({ path: f, type: 'blob' })) }) });
      return route.fulfill({ status: 404, contentType: 'application/json', body: '{"message":"Not Found"}' });
    });
  };
  {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await ctx.newPage();
    await page.addInitScript(RAF_COUNTER);
    await watch(page);
    page.on('dialog', d => { if (d.type() === 'prompt') a.promptShown = true; if (d.type() === 'confirm') d.accept(); else d.dismiss(); });
    try { await page.goto(base + '/' + EDITOR, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { a.errors++; }
    await page.waitForTimeout(700);
    a.idleFrames = await page.evaluate(async () => { window.__rafReset(); await new Promise(r => setTimeout(r, 1000)); return window.__pageRaf(); }).catch(() => 99);
    // the tabs and the search, before any connection exists
    const before = a.errors;
    for (const t of ['files', 'text', 'setup', 'pieces']) {
      a.tabs++;
      await page.click('.etab[data-tab="' + t + '"]').catch(() => {});
      await page.waitForTimeout(60);
      const ok = await page.evaluate(t => {
        const on = [...document.querySelectorAll('.etab[aria-selected="true"]')].map(b => b.dataset.tab);
        const panel = document.getElementById('tab-' + t); const shown = !!panel && getComputedStyle(panel).display !== 'none';
        const others = ['pieces', 'add', 'files', 'text', 'setup'].filter(x => x !== t).every(x => { const p = document.getElementById('tab-' + x); return !p || getComputedStyle(p).display === 'none'; });
        return on.length === 1 && on[0] === t && shown && others;
      }, t).catch(() => false);
      if (ok) a.switched++;
    }
    await page.fill('#search', 'x').catch(() => {}); await page.waitForTimeout(60);
    await page.fill('#search', '').catch(() => {}); await page.waitForTimeout(60);   // cleared, or the list below is counted through this filter
    a.threwUnconnected = a.errors - before;
    // the theme button switches the theme and remembers it
    const t0 = await page.evaluate(() => document.documentElement.getAttribute('data-theme') || '').catch(() => '');
    await page.click('#themebtn').catch(() => {}); await page.waitForTimeout(60);
    const t1 = await page.evaluate(() => [document.documentElement.getAttribute('data-theme') || '', (() => { try { return localStorage.getItem('theme') || ''; } catch (e) { return ''; } })()]).catch(() => ['', '']);
    a.themeSwitched = !!t1[0] && t1[0] !== t0; a.themeStored = !!t1[0] && t1[1] === t1[0];
    // the connection form: the repository stays in this browser, the token in this tab
    await page.click('.etab[data-tab="setup"]').catch(() => {});
    await page.fill('#owner', 'owner').catch(() => {}); await page.fill('#repo', 'repo').catch(() => {});
    await page.fill('#branch', 'main').catch(() => {}); await page.fill('#tok', 'github_pat_AUDIT_ONLY').catch(() => {});
    await page.click('#save-setup').catch(() => {});
    await page.waitForFunction(() => /Connected to|Could not/.test((document.getElementById('status') || {}).textContent || ''), null, { timeout: 15000 }).catch(() => {});
    const st = await page.evaluate(() => { try { const l = localStorage.getItem('siteeditor.v1') || ''; return { cfg: /"owner":"owner"/.test(l) && /"repo":"repo"/.test(l), tokenInLocal: /github_pat/.test(l), tokenInSession: sessionStorage.getItem('siteeditor.token') === 'github_pat_AUDIT_ONLY' }; } catch (e) { return { cfg: false, tokenInLocal: true, tokenInSession: false }; } }).catch(() => ({ cfg: false, tokenInLocal: true, tokenInSession: false }));
    a.cfgSaved = st.cfg; a.tokenInLocal = st.tokenInLocal; a.tokenInSession = st.tokenInSession;
    // the list, the search, the editor, an edit, Publish and its guard
    a.rows = await page.$$eval('#plist .prow', els => els.length).catch(() => -1);
    const q = 'afm 291';
    a.searchExpected = (content.pieces || []).filter(p => [p.t, p.s, p.c, p.k, (p.tags || []).join(' ')].join(' ').toLowerCase().indexOf(q) >= 0).length;
    await page.fill('#search', q).catch(() => {}); await page.waitForTimeout(60);
    a.searched = await page.$$eval('#plist .prow', els => els.length).catch(() => -1);
    await page.fill('#search', '').catch(() => {}); await page.waitForTimeout(60);
    await page.click('#plist .prow >> nth=0').catch(() => {});
    const first = (content.pieces || [])[0] || {};
    a.editorOpened = (await page.$eval('#f_t', el => el.value).catch(() => null)) === first.t;
    await page.fill('#f_t', (first.t || '') + ' x').catch(() => {}); await page.waitForTimeout(60);
    a.editEnabledPublish = await page.evaluate(() => !document.getElementById('publish').disabled && !!document.querySelector('#plist .prow[aria-current="true"] .badge.edit') && !document.getElementById('pending').classList.contains('hide')).catch(() => false);
    await page.click('#publish').catch(() => {}); await page.waitForTimeout(300);   // the note it asks for is declined: nothing is written
    await page.click('.etab[data-tab="setup"]').catch(() => {}); await page.click('#forget').catch(() => {}); await page.waitForTimeout(60);
    a.forgotten = await page.evaluate(() => { try { return sessionStorage.getItem('siteeditor.token') === null && document.getElementById('publish').disabled; } catch (e) { return false; } }).catch(() => false);
    await page.click('.etab[data-tab="pieces"]').catch(() => {}); await page.click('#plist .prow >> nth=0').catch(() => {});
    await page.fill('#f_t', (first.t || '') + ' xy').catch(() => {}); await page.waitForTimeout(60);
    await page.click('#publish').catch(() => {}); await page.waitForTimeout(300);
    const guard = await page.evaluate(() => /token/i.test(document.getElementById('status').textContent) && getComputedStyle(document.getElementById('tab-setup')).display !== 'none').catch(() => false);
    a.guardHeld = guard && a.writes === 0;
    // the files and the site text
    await page.click('.etab[data-tab="files"]').catch(() => {}); await page.waitForTimeout(60);
    a.filesExpected = files.filter(f => !/^(\.|build\/|\.github\/|content\/)/.test(f)).length;
    a.files = await page.$$eval('#repolist tr', els => els.length).catch(() => -1);
    await page.click('.etab[data-tab="text"]').catch(() => {}); await page.waitForTimeout(60);
    a.siteFields = await page.evaluate(s => { const i = document.getElementById('s_short'); return i && i.value === s ? document.querySelectorAll('#siteform input').length : 0; }, (content.site || {}).short || '').catch(() => 0);
    await ctx.close();
  }
  {
    const ctx = await browser.newContext({ viewport: { width: 320, height: 844 }, isMobile: true, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    try { await page.goto(base + '/' + EDITOR, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { /* measured anyway */ }
    await page.waitForTimeout(400);
    a.scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth).catch(() => 0);
    a.overflow = a.scrollWidth > 320;
    await ctx.close();
  }
  rec.ext = { requests: a.requests, external: a.external };
  rec.idle = { frames: a.idleFrames };
  rec.errors = a.errors;
  rec.fit = { scrollWidth: a.scrollWidth, overflow: a.overflow };
  rec.admin = a;
  return rec;
}

async function measurePage(browser, base, name, shell) {
  if (name === EDITOR) return measureEditor(browser, base);
  const rec = {};
  // requests, idle frames and console errors at a desktop size
  {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await ctx.newPage();
    let requests = 0, external = 0, errors = 0;
    page.on('request', r => { requests++; const u = r.url(); if (!u.startsWith(base) && !u.startsWith('data:') && !u.startsWith('blob:')) external++; });
    page.on('console', m => { if (m.type() === 'error') errors++; });
    page.on('pageerror', () => { errors++; });
    await page.addInitScript(RAF_COUNTER);
    try { await page.goto(base + '/' + name, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { errors++; }
    await page.waitForTimeout(700);
    const frames = await page.evaluate(async () => { window.__rafReset(); await new Promise(r => setTimeout(r, 1000)); return window.__pageRaf(); }).catch(() => -1);
    rec.ext = { requests, external };
    rec.idle = { frames };
    rec.errors = errors;
    // does the word count leave the chrome out: the count by the measurement's
    // own rule, against the count with every element the build injects removed
    // as well, named by the ids and classes the build's own blocks carry and
    // nothing a piece could carry itself; the two must agree, or chrome is
    // being counted
    rec.chrome = await page.evaluate(() => {
      const count = extra => {
        const clone = document.body.cloneNode(true);
        clone.querySelectorAll('script,style,noscript,#__rb,#__rb-pill,#__rb-from,#__long-idx,.docfrom,header.top,footer.site,.docbar,.toc,nav.main,.cmdk' + (extra ? ',' + extra : ''))
             .forEach(n => n.remove());
        const txt = (clone.textContent || '').replace(/\s+/g, ' ').trim();
        return txt.split(' ').filter(w => /[A-Za-z0-9]/.test(w)).length;
      };
      return { a: count(''), b: count('[id^="__rb"],[id^="__long"],[id^="__meta"],#defs,.docfrom,footer.site,dialog.cmdk,dialog.keys,dialog.prov') };
    }).catch(() => null);
    if (shell) {
      // print media: nothing pinned, nothing hidden, figures unbroken
      await page.emulateMedia({ media: 'print' });
      await page.waitForTimeout(300);
      rec.print = await page.evaluate(() => {
        const vis = el => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect(); return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
        let stickyLeft = 0, hidden = 0, figures = 0, figuresBreakable = 0;
        document.querySelectorAll('body *').forEach(el => {
          if (el.closest('dialog, noscript, script, style, svg')) return;
          const cs = getComputedStyle(el);
          if ((cs.position === 'sticky' || cs.position === 'fixed') && vis(el)) stickyLeft++;
          if ((cs.opacity === '0' || cs.visibility === 'hidden') && cs.display !== 'none' && (el.textContent || '').trim().length > 20 && !el.closest('[hidden], [aria-hidden="true"], .cmdk, .keys')) hidden++;
        });
        document.querySelectorAll('figure, .spec, .plot').forEach(el => {
          if (!vis(el)) return;
          figures++;
          const cs = getComputedStyle(el);
          if (cs.breakInside !== 'avoid' && cs.pageBreakInside !== 'avoid') figuresBreakable++;
        });
        return { stickyLeft, hidden, figures, figuresBreakable };
      }).catch(() => null);
      await page.emulateMedia({ media: 'screen' });
    }
    await ctx.close();
  }
  // does it fit a 320px viewport
  {
    const ctx = await browser.newContext({ viewport: { width: 320, height: 844 }, isMobile: true, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    try { await page.goto(base + '/' + name, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { /* measured anyway */ }
    await page.waitForTimeout(500);
    const sw = await page.evaluate(() => document.documentElement.scrollWidth).catch(() => 0);
    rec.fit = { scrollWidth: sw, overflow: sw > 320 };
    await ctx.close();
  }
  if (name === 'index.html') {
    // the descent: each featured row of the statement scrolled to the reading
    // line, at a desktop width (the sphere beside the rows) and a phone width
    // (the block pinned above them); the document the sphere reports facing
    // must be the row's, and once the scroll has stopped no frame may be
    // requested. Scrolls are instant here: the browser's own smooth scroll
    // is not what is being measured.
    rec.descent = { wide: null, phone: null };
    for (const shape of [{ key: 'wide', vp: { width: 1440, height: 900 }, touch: false }, { key: 'phone', vp: { width: 390, height: 844 }, touch: true }]) {
      const ctx = await browser.newContext({ viewport: shape.vp, hasTouch: shape.touch, isMobile: shape.touch, deviceScaleFactor: 1 });
      const page = await ctx.newPage();
      await page.addInitScript(RAF_COUNTER);
      try { await page.goto(base + '/' + name, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { /* measured anyway */ }
      await page.addStyleTag({ content: 'html{scroll-behavior:auto!important}' });
      await page.waitForTimeout(600);
      const rows = await page.$$eval('#statement table.st tr.item', trs => trs.map(tr => tr.querySelector('th a').textContent.trim()));
      let faced = 0, framesAfter = 0, framesSettle = 0, corMatched = 0;
      const aim = async title => page.evaluate(t => {
        const wrap = document.querySelector('.descent-globe'); const wb = wrap ? wrap.getBoundingClientRect() : null;
        const tr = [...document.querySelectorAll('#statement table.st tr.item')].find(x => x.querySelector('th a').textContent.trim() === t);
        if (!tr) return;
        const rr = tr.getBoundingClientRect(); const sr = tr.closest('table').getBoundingClientRect();
        const beside = wb && (wb.left >= sr.right - 1 || wb.right <= sr.left + 1);
        const line = beside ? innerHeight * 0.5 : (wb ? wb.bottom + 12 : innerHeight * 0.5);
        const target = beside ? scrollY + rr.top + rr.height / 2 - line : scrollY + rr.top - line;
        window.scrollTo(0, Math.max(0, target));
      }, title);
      for (const title of rows) {
        // aim until the target holds still: on a phone the block pins and
        // steps back as the page scrolls, which moves the reading line
        for (let k = 0; k < 4; k++) {
          const before = await page.evaluate(() => scrollY);
          await aim(title); await page.waitForTimeout(400);
          const after = await page.evaluate(() => scrollY);
          if (Math.abs(after - before) < 3) break;
        }
        const facing = await page.evaluate(() => { const h = document.getElementById('atlasmini'); return h ? h.getAttribute('data-facing') : null; });
        if (facing === title) faced++;
        // the spring settles within half a second of the last scroll; the
        // frames it takes are recorded, and after 700ms none may follow
        framesSettle += await page.evaluate(async () => { window.__rafReset(); await new Promise(r => setTimeout(r, 700)); return window.__pageRaf(); }).catch(() => 99);
        framesAfter += await page.evaluate(async () => { window.__rafReset(); await new Promise(r => setTimeout(r, 1000)); return window.__pageRaf(); }).catch(() => 99);
        // the corona names the faced row's recorded origin
        const cor = await page.evaluate(t => {
          const h = document.getElementById('atlasmini');
          const tr = [...document.querySelectorAll('#statement table.st tr.item')].find(x => x.querySelector('th a').textContent.trim() === t);
          return { drawn: h ? h.getAttribute('data-corona') : null, row: tr ? tr.getAttribute('data-o') : null };
        }, title).catch(() => ({ drawn: null, row: null }));
        if (cor.drawn && cor.drawn === cor.row) corMatched++;
      }
      await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(700);
      const framesAtTop = await page.evaluate(async () => { window.__rafReset(); await new Promise(r => setTimeout(r, 1000)); return window.__pageRaf(); }).catch(() => 99);
      const corTop = await page.evaluate(() => { const h = document.getElementById('atlasmini'); return h ? h.getAttribute('data-corona') : null; }).catch(() => null);
      rec.descent[shape.key] = { rows: rows.length, faced, framesSettle, framesAfter, framesAtTop };
      rec.corona = rec.corona || {};
      rec.corona[shape.key] = { rows: rows.length, matched: corMatched, atTop: corTop };
      await ctx.close();
    }
  }
  if (shell) {
    // keyboard: real Tab presses, a ring on every stop
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      const page = await ctx.newPage();
      try { await page.goto(base + '/' + name, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { /* measured anyway */ }
      const seen = []; let noRing = 0;
      const readStop = () => page.evaluate(() => {
          const el = document.activeElement; if (!el || el === document.body) return null;
          const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
          let ring = (parseFloat(cs.outlineWidth) > 0 && cs.outlineStyle !== 'none') || (cs.boxShadow && cs.boxShadow !== 'none') || (parseFloat(cs.borderBottomWidth) >= 2);
          if (!ring) { const hit = el.querySelector('.cf-hit'); if (hit) { const hs = getComputedStyle(hit); ring = hs.fill !== 'rgba(0, 0, 0, 0)' && hs.fill !== 'transparent' && hs.fill !== 'none'; } }
          const name = (el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + String(el.getAttribute('class') || '').split(' ')[0]) + '|' + (el.getAttribute('href') || '') + '|' + (el.textContent || '').trim().slice(0, 30);
          const visible = cs.visibility !== 'hidden' && cs.opacity !== '0' && r.width > 0 && r.height > 0;
          return { name, ok: ring && visible };
        }).catch(() => null);
      for (let i = 0; i < 400; i++) {
        await page.keyboard.press('Tab');
        await page.waitForTimeout(120);
        let info = await readStop();
        if (!info) break;
        if (seen.length && seen[0] === info.name && i > 5) break;
        seen.push(info.name);
        // a ring that arrives on a transition is read again after it has
        // had time to; only a stop still without one after that counts
        if (!info.ok) { await page.waitForTimeout(250); const again = await readStop(); if (again && again.name === info.name) info = again; }
        if (!info.ok) noRing++;
      }
      rec.keyboard = { stops: seen.length, noRing };
      await ctx.close();
    }
    // the theme selector: two named states, one of them pressed; a pulse on
    // the first visit that ends, and none on the second; a switch that
    // changes the theme and requests no frame once it has settled; a
    // focus ring on the offer when reached from the keyboard
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      const page = await ctx.newPage();
      await page.addInitScript(RAF_COUNTER);
      try { await page.goto(base + '/' + name, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { /* measured anyway */ }
      const theme = { options: 0, pressed: 0, pulsed: false, pulseEnded: false, repeated: true, switched: false, framesAfterSwitch: -1, focusRing: false };
      const sel = await page.evaluate(() => {
        const g = document.getElementById('themesel'); if (!g) return null;
        const opts = [...g.querySelectorAll('.tsel')];
        return { options: opts.length, pressed: opts.filter(o => o.getAttribute('aria-pressed') === 'true').length, pulsed: g.getAttribute('data-pulse') === '1' };
      }).catch(() => null);
      if (sel) {
        theme.options = sel.options; theme.pressed = sel.pressed; theme.pulsed = sel.pulsed;
        await page.waitForTimeout(3000);
        theme.pulseEnded = await page.evaluate(() => !document.getElementById('themesel').hasAttribute('data-pulse') && document.getAnimations().filter(a => a.playState === 'running').length === 0).catch(() => false);
        for (let i = 0; i < 16; i++) {
          await page.keyboard.press('Tab'); await page.waitForTimeout(60);
          const on = await page.evaluate(() => { const el = document.activeElement; if (!el || !el.classList.contains('tsel') || el.getAttribute('aria-pressed') === 'true') return null; const cs = getComputedStyle(el); return (parseFloat(cs.outlineWidth) > 0 && cs.outlineStyle !== 'none') || (cs.boxShadow && cs.boxShadow !== 'none'); }).catch(() => null);
          if (on !== null) { theme.focusRing = !!on; break; }
        }
        const before = await page.evaluate(() => document.documentElement.getAttribute('data-theme') || '');
        await page.click('#themesel .tsel[aria-pressed="false"]').catch(() => {});
        await page.waitForTimeout(500);
        const after = await page.evaluate(() => document.documentElement.getAttribute('data-theme') || '');
        theme.switched = !!after && after !== before;
        theme.framesAfterSwitch = await page.evaluate(async () => { window.__rafReset(); await new Promise(r => setTimeout(r, 1000)); return window.__pageRaf(); }).catch(() => 99);
        try { await page.reload({ waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { /* measured anyway */ }
        theme.repeated = await page.evaluate(() => document.getElementById('themesel').getAttribute('data-pulse') === '1').catch(() => true);
      }
      rec.theme = theme;
      await ctx.close();
    }
    /* The header mark: the letters at rest, the construction under a pointer
       or a keyboard focus, and the page still at rest the frame after it
       settles. Opacity only, so the brand's box may not move by a pixel. */
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      const page = await ctx.newPage();
      try { await page.goto(base + '/' + name, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { /* measured anyway */ }
      const ins = { layers: 0, rest: -1, hover: -1, focus: -1, ms: -1, moved: -1, framesAfter: -1, reducedMs: -1 };
      const has = await page.evaluate(() => !!document.querySelector('.brand .mk-ins'));
      if (has) {
        const read = () => page.evaluate(() => {
          const el = document.querySelector('.brand .mk-ins');
          const b = document.querySelector('.brand').getBoundingClientRect();
          return { o: parseFloat(getComputedStyle(el).opacity),
                   ms: (parseFloat(getComputedStyle(el).transitionDuration) || 0) * 1000,
                   box: [Math.round(b.width), Math.round(b.height)] };
        });
        ins.layers = await page.evaluate(() => document.querySelectorAll('.brand .mk-nom, .brand .mk-ins').length);
        const a = await read();
        ins.rest = a.o; ins.ms = Math.round(a.ms);
        await page.hover('.brand'); await page.waitForTimeout(600);
        const b = await read();
        ins.hover = b.o;
        ins.moved = (a.box[0] === b.box[0] && a.box[1] === b.box[1]) ? 0 : 1;
        ins.framesAfter = await page.evaluate(async () => { window.__rafReset(); await new Promise(r => setTimeout(r, 1000)); return window.__pageRaf(); }).catch(() => 99);
        await page.mouse.move(0, 0); await page.waitForTimeout(400);
        for (let i = 0; i < 6; i++) {
          await page.keyboard.press('Tab'); await page.waitForTimeout(80);
          const on = await page.evaluate(() => document.activeElement && document.activeElement.classList.contains('brand'));
          if (on) { await page.waitForTimeout(500); ins.focus = (await read()).o; break; }
        }
      }
      await ctx.close();
      const rc = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
      const rp = await rc.newPage();
      try { await rp.goto(base + '/' + name, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { /* measured anyway */ }
      ins.reducedMs = await rp.evaluate(() => {
        const el = document.querySelector('.brand .mk-ins');
        return el ? Math.round((parseFloat(getComputedStyle(el).transitionDuration) || 0) * 1000) : -1;
      }).catch(() => -1);
      await rc.close();
      rec.inspect = ins;
    }
    // reduced motion: nothing animating after load
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
      const page = await ctx.newPage();
      try { await page.goto(base + '/' + name, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { /* measured anyway */ }
      await page.waitForTimeout(1000);
      const animations = await page.evaluate(() => document.getAnimations().filter(a => a.playState === 'running').length).catch(() => -1);
      rec.motion = { animations };
      await ctx.close();
    }
  }
  return rec;
}

/* A publish, simulated: save the full copy from this tree, then serve a copy
   of the tree in which one page changed and the worker and manifest were
   regenerated, on the same origin, and see what the saved copy holds. */
function copyTree(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const f of fs.readdirSync(src)) {
    if (f === '.git' || f === 'node_modules' || f === 'cards' || f === '__pycache__') continue;
    fs.cpSync(path.join(src, f), path.join(dst, f), { recursive: true });
  }
}

/* The published copy: one page changes, and the worker and the manifest
   follow it. A falsification may edit the copy first. */
function publish(copy, mutate) {
  const idx = path.join(copy, 'index.html');
  fs.writeFileSync(idx, fs.readFileSync(idx, 'utf8').replace('</body>', '<!-- audit: a publish changed this page --></body>'));
  // the editor changes too: it must be the published one on the next visit
  const adm = path.join(copy, EDITOR);
  if (fs.existsSync(adm)) fs.writeFileSync(adm, fs.readFileSync(adm, 'utf8').replace('</body>', '<!-- audit: a publish changed the editor --></body>'));
  if (mutate) mutate(copy);
  execFileSync('python3', [path.join(copy, 'build', 'build_site.py'), '--offline-only'], { encoding: 'utf8' });
}

async function measureOffline(port, mutate) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'audit-'));
  const profile = path.join(tmp, 'profile');
  const copy = path.join(tmp, 'site');
  copyTree(ROOT, copy);
  publish(copy, mutate);

  const base = 'http://127.0.0.1:' + port;
  const ctx = await chromium.launchPersistentContext(profile, Object.assign({ serviceWorkers: 'allow', viewport: { width: 1280, height: 800 } }, LAUNCH));
  const page = ctx.pages()[0] || await ctx.newPage();
  const held = () => page.evaluate(async () => {
    const ks = await caches.keys(); const k = ks.find(x => x.indexOf('site-pages-') === 0);
    if (!k) return { files: 0, marker: false };
    const c = await caches.open(k); const man = await c.match('offline-manifest.json');
    const files = man ? (await man.json()).files : [];
    let n = 0; for (const f of files) if (await c.match(f)) n++;
    const r = await c.match('index.html'); const t = r ? await r.text() : '';
    return { files: n, of: files.length, marker: t.indexOf('audit: a publish changed this page') >= 0 };
  });
  // the editor under the worker: reached over the network on every visit and
  // held in no cache, before the publish and after it
  const editor = { stored: null, fresh: null };
  const stored = () => page.evaluate(async () => { for (const k of await caches.keys()) { const c = await caches.open(k); if (await c.match('admin.html')) return true; } return false; }).catch(() => null);
  let before = null, after = null;
  const server1 = serve(ROOT);
  await listen(server1, port);
  try {
    await page.goto(base + '/colophon.html', { waitUntil: 'networkidle' });
    await page.evaluate(() => navigator.serviceWorker.ready);
    await page.click('#offline-save');
    await page.waitForFunction(() => /is on this device|failed|Could not/.test(document.getElementById('offline-status').textContent), null, { timeout: 180000 });
    await page.waitForTimeout(1500);
    before = await held();
    await page.goto(base + '/' + EDITOR, { waitUntil: 'networkidle' }); await page.waitForTimeout(500);
    editor.stored = await stored();
    await page.goto(base + '/colophon.html', { waitUntil: 'networkidle' });
  } finally {
    await new Promise(r => server1.close(r));
  }
  const server2 = serve(copy);
  await listen(server2, port);
  try {
    await page.reload({ waitUntil: 'networkidle' }); await page.waitForTimeout(3000);
    await page.reload({ waitUntil: 'networkidle' }); await page.waitForTimeout(4000);
    after = await held();
    await page.goto(base + '/' + EDITOR, { waitUntil: 'networkidle' }); await page.waitForTimeout(500);
    editor.fresh = await page.evaluate(() => document.documentElement.outerHTML.indexOf('audit: a publish changed the editor') >= 0).catch(() => false);
    editor.stored = (await stored()) || editor.stored;
  } finally {
    await new Promise(r => server2.close(r));
  }
  await ctx.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  return { before: before.files, of: before.of, after: after.files, refreshed: after.marker, editor };
}

/* The runtime falsifications: a page made false at its source, on a copy of
   the tree served on its own port, measured exactly as the real page is. */
const FALSIFICATIONS = [
  { key: 'ext', page: 'about.html', what: 'the page loads an image from another origin',
    apply: h => h.replace('</body>', '<img src="https://not-this-origin.invalid/x.png" alt=""></body>') },
  { key: 'idle', page: 'about.html', what: 'a script requests a new frame on every frame after load',
    apply: h => h.replace('</body>', '<script>(function f(){requestAnimationFrame(f)})()</script></body>') },
  { key: 'keyboard', page: 'about.html', what: 'a stylesheet removes the focus ring from every element',
    apply: h => h.replace('</head>', '<style>*:focus,*:focus-visible{outline:none!important;box-shadow:none!important;border-bottom-width:0!important}</style></head>') },
  { key: 'print', page: 'index.html', what: 'under print media the figures may break across pages and the header stays pinned',
    apply: h => h.replace('</head>', '<style>@media print{figure,.spec,.plot{break-inside:auto!important;page-break-inside:auto!important}header.top{position:sticky!important;top:0;display:block!important}}</style></head>') },
  { key: 'motion', page: 'about.html', what: 'the brand mark spins under reduced motion',
    apply: h => h.replace('</head>', '<style>@keyframes neg-spin{to{transform:rotate(1turn)}}.brand .mk{animation:neg-spin 2s linear infinite!important}</style></head>') },
  { key: 'fit', page: 'about.html', what: 'a 900px block that no declaration allows',
    apply: h => h.replace('</body>', '<div style="width:900px;height:2px"></div></body>') },
  { key: 'chrome', page: 'positive-vs-normative.html', what: 'a block the build owns carries words the count would include',
    apply: h => h.replace('</body>', '<p id="__meta-negative">words the count must leave out</p></body>') },
  { key: 'descent', page: 'index.html', what: 'a script keeps requesting frames after the scroll has stopped',
    apply: h => h.replace('</body>', '<script>addEventListener("scroll",function(){(function f(){requestAnimationFrame(f)})()},{passive:true})</script></body>') },
  { key: 'theme', page: 'index.html', what: 'the first-visit pulse repeats on every visit',
    apply: h => h.replace('<script src="site.js', '<script>try{localStorage.removeItem("theme.seen")}catch(e){}</script><script src="site.js') },
  { key: 'theme', page: 'index.html', what: 'a switch of theme starts a loop that keeps requesting frames',
    apply: h => h.replace('</body>', '<script>document.addEventListener("click",function(e){if(e.target.closest&&e.target.closest(".tsel"))(function f(){requestAnimationFrame(f)})()})</script></body>') },
  { key: 'corona', page: 'index.html', what: "the sphere's payload records the wrong origin for two featured documents, so the corona names an origin the row does not have",
    apply: h => h.replace('<script src="site.js', '<script>(function(){var s=document.getElementById("atlasmini-docs");if(!s)return;var d=JSON.parse(s.textContent);d.docs.forEach(function(x){if(x.u==="flagged-in-hindsight.html"||x.u==="brittle-network.html")x.o="course";});s.textContent=JSON.stringify(d);})()</script><script src="site.js') },
  { key: 'descent', page: 'index.html', what: "the sphere's document payload names the wrong document for the first two featured rows",
    apply: h => h.replace('"u":"flagged-in-hindsight.html"', '"u":"__swap__"').replace('"u":"crucible-cockpit.html"', '"u":"flagged-in-hindsight.html"').replace('"u":"__swap__"', '"u":"crucible-cockpit.html"') },
  { key: 'inspect', page: 'about.html', what: 'the construction layer is drawn at rest, so the mark has one state and not two',
    apply: h => h.replace('</head>', '<style>.mk-ins{opacity:1!important}</style></head>') },
  { key: 'inspect', page: 'about.html', what: 'the transition runs past the 260ms cap and keeps running for a reader who asked for no motion',
    apply: h => h.replace('</head>', '<style>.mk-ins{transition:opacity 900ms linear!important}@media (prefers-reduced-motion:reduce){.mk-ins{transition:opacity 900ms linear!important}}</style></head>') },
  { key: 'admin', page: 'admin.html', what: "a syntax error in the editor's script",
    apply: h => h.replace('"use strict";', '"use strict"; this is not javascript;') },
  { key: 'admin', page: 'admin.html', what: 'the editor links a stylesheet that does not exist',
    apply: h => h.replace('href="site.css"', 'href="site-editor.css"') },
  { key: 'admin', page: 'admin.html', what: "the editor writes the token to long-term storage beside the repository",
    apply: h => h.replace('{ owner: cfg.owner, repo: cfg.repo, branch: cfg.branch }', '{ owner: cfg.owner, repo: cfg.repo, branch: cfg.branch, token: cfg.token }') },
];
const SW_FALSIFICATIONS = [
  { what: 'the new worker neither carries the saved copy across nor syncs it, so a publish empties it',
    mutate: copy => {
      const bp = path.join(copy, 'build', 'build_site.py');
      let src = fs.readFileSync(bp, 'utf8');
      const a = '    await migrate();\n', b = '    if (await c.match(MANIFEST)) await sync(broadcast, false);\n';
      if (!src.includes(a) || !src.includes(b)) throw new Error('the worker template has moved; the offline falsification cannot be applied');
      fs.writeFileSync(bp, src.replace(a, '').replace(b, ''));
    } },
  { what: 'the worker stores the editor like any other page, so a visit leaves it in the cache',
    mutate: copy => {
      const bp = path.join(copy, 'build', 'build_site.py');
      const src = fs.readFileSync(bp, 'utf8');
      const a = 'const NEVER_STORED = ["admin.html"];';
      if (!src.includes(a)) throw new Error('the worker template has moved; the editor falsification cannot be applied');
      fs.writeFileSync(bp, src.replace(a, 'const NEVER_STORED = [];'));
    } },
];

async function falsify(dig) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'falsify-'));
  const copy = path.join(tmp, 'site');
  copyTree(ROOT, copy);
  const cases = [];
  const server = serve(copy);
  const port = await listen(server, 0);
  const base = 'http://127.0.0.1:' + port;
  const browser = await chromium.launch(LAUNCH);
  for (const c of FALSIFICATIONS) {
    // one falsification at a time on its page, restored afterwards, so two
    // falsifications of the same page do not measure each other
    const fp = path.join(copy, c.page);
    const orig = fs.readFileSync(fp, 'utf8');
    const mutated = c.apply(orig);
    if (mutated === orig) throw new Error('falsification ' + c.key + ' changed nothing on ' + c.page);
    fs.writeFileSync(fp, mutated);
    const rec = await measurePage(browser, base, c.page, dig.shell.includes(c.page));
    fs.writeFileSync(fp, orig);
    cases.push({ key: c.key, page: c.page, what: c.what, rec: { [c.key]: rec[c.key] } });
    process.stdout.write(`falsified ${c.key} on ${c.page}: ${JSON.stringify(rec[c.key])}\n`);
  }
  await browser.close();
  await new Promise(r => server.close(r));
  fs.rmSync(tmp, { recursive: true, force: true });
  if (!NO_OFFLINE) {
    for (const sw of SW_FALSIFICATIONS) {
      const r = await measureOffline(port, sw.mutate);
      cases.push({ key: 'offline', page: 'sw.js', what: sw.what, rec: r });
      process.stdout.write(`falsified offline: ${r.before} held before, ${r.after} after, the editor ${r.editor && r.editor.stored ? 'stored' : 'not stored'}, ${r.editor && r.editor.fresh ? 'fresh' : 'stale'}\n`);
    }
  }
  const neg = readJSON(NEG_PATH, {});
  neg.runtime = {
    meta: { tool: 'build/audit.js --falsify', date: new Date().toISOString().slice(0, 10),
            commit: git(['rev-parse', '--short', 'HEAD']) || 'unknown', code: dig.runtime_code },
    cases,
  };
  if (!neg.note) neg.note = 'Written by build/negatives.py and build/audit.js --falsify: for each check and each runtime claim, a falsification and what caught it.';
  fs.writeFileSync(NEG_PATH, JSON.stringify(neg, null, 1) + '\n');
  console.log(`falsified ${cases.length} runtime claims; the register grades them by the rule it grades the pages by`);
}

(async () => {
  const dig = digests();
  if (FALSIFY) { await falsify(dig); return; }
  const audit = readJSON(OUT_PATH, {});
  const pages = audit.pages || {};
  const names = Object.keys(dig.pages);
  const stale = names.filter(nm => ALL || (ONLY && ONLY.includes(nm)) || !pages[nm] || pages[nm].inputs !== dig.pages[nm]);
  const server = serve(ROOT);
  const port = await listen(server, 0);
  const base = 'http://127.0.0.1:' + port;
  const browser = await chromium.launch(LAUNCH);
  const version = browser.version();
  let done = 0;
  for (const nm of stale) {
    const rec = await measurePage(browser, base, nm, dig.shell.includes(nm));
    rec.inputs = dig.pages[nm];
    rec.measured = new Date().toISOString().slice(0, 10);
    pages[nm] = rec;
    done++;
    process.stdout.write(`measured ${nm}: ${rec.ext.requests} requests, ${rec.ext.external} external, ${rec.idle.frames} idle frames, fit ${rec.fit.overflow ? 'no' : 'yes'}` +
      (rec.keyboard ? `, ${rec.keyboard.stops} stops, ${rec.keyboard.noRing} without a ring` : '') + '\n');
  }
  // records for pages that no longer exist leave
  for (const nm of Object.keys(pages)) if (!names.includes(nm)) delete pages[nm];
  await browser.close();
  await new Promise(r => server.close(r));

  let offline = audit.offline || null;
  const offlineStale = !offline || offline.inputs !== dig.sw;
  if (!NO_OFFLINE && !ONLY && (ALL || offlineStale)) {
    const r = await measureOffline(port);
    offline = Object.assign(r, { inputs: dig.sw, measured: new Date().toISOString().slice(0, 10) });
    process.stdout.write(`offline: ${r.before} files held before a publish, ${r.after} after, the changed page ${r.refreshed ? 'refreshed' : 'not refreshed'}; the editor ${r.editor && r.editor.stored === false ? 'held in no cache' : 'stored'}, ${r.editor && r.editor.fresh ? 'fresh after the publish' : 'stale'}\n`);
  }

  const out = {
    note: 'Written by build/audit.js: what a headless browser measured on each page, with the fingerprint of the inputs it measured. The register on the controls page prints these results; a page whose inputs moved since is not yet measured for that build. meta.runs is appended by build/claims.py --record-run on every publish.',
    meta: Object.assign({}, audit.meta || {}, { tool: 'build/audit.js', browser: 'Chromium ' + version, date: new Date().toISOString().slice(0, 10), commit: git(['rev-parse', '--short', 'HEAD']) || 'unknown' }),
    pages: Object.fromEntries(Object.keys(pages).sort().map(k => [k, pages[k]])),
    offline,
  };
  fs.writeFileSync(OUT_PATH, JSON.stringify(out, null, 1) + '\n');
  const total = names.length;
  const ext = Object.values(pages).reduce((a, r) => a + (r.ext ? r.ext.external : 0), 0);
  const idle = Object.values(pages).reduce((a, r) => a + (r.idle ? r.idle.frames : 0), 0);
  const overflow = Object.entries(pages).filter(([, r]) => r.fit && r.fit.overflow).map(([k]) => k);
  console.log(`audited ${done} of ${total} pages (${total - done} kept from the record); ${ext} external requests, ${idle} idle frames over all; ` +
              `${overflow.length} page(s) wider than 320px${overflow.length ? ': ' + overflow.join(', ') : ''}`);
})().catch(e => { console.error(e); process.exit(1); });
