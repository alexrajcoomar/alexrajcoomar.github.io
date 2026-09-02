#!/usr/bin/env python3
"""The reader edition: the whole portfolio as one self-contained file for a
phone's Files app, where links between separate local files do not work.
Everything readable is embedded; navigation is same-document anchors, which
need no JavaScript; search is an enhancement on top. Interactive tools
cannot run inside another document, so they appear as honest stubs pointing
at the installed app and the full copy."""
import json, re, os, base64, html, io, datetime

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = json.load(open('content/pieces.json'))['pieces']
M = json.load(open('content/metrics.json'))

_INJ = re.compile(
    r"<!--__rb-->.*?<!--/__rb-->|<!--__rbp-->.*?<!--/__rbp-->|<!--__meta-->.*?<!--/__meta-->"
    r'|<style id="__rb-style">.*?</style>|<div id="__rb">.*?</div>|<a id="__rb-pill"[^>]*>.*?</a>'
    r'|<style id="__mobile_fit">.*?</style>', re.S)

by_url = {p['url']: p for p in P}
embedded = {p['url'] for p in P if p['k'] != 'Tool'}

def img_data(src):
    """Inline a local image, downscaled for a phone archive."""
    if not os.path.exists(src): return None
    try:
        from PIL import Image
        im = Image.open(src)
        if im.width > 1100:
            im = im.resize((1100, int(im.height * 1100 / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.convert('RGB').save(buf, 'JPEG', quality=82) if src.endswith(('.jpg','.jpeg')) else \
            im.save(buf, 'PNG', optimize=True)
        raw = buf.getvalue()
        mime = 'image/jpeg' if src.endswith(('.jpg','.jpeg')) else 'image/png'
    except Exception:
        raw = open(src, 'rb').read()
        mime = 'image/png'
    return 'data:%s;base64,%s' % (mime, base64.b64encode(raw).decode())

IMG_CACHE = {}
def piece_body(p):
    t = open(p['url'], encoding='utf-8', errors='ignore').read()
    t = _INJ.sub('', t)
    t = re.sub(r'<(script|style|noscript)\b[^>]*>.*?</\1>', '', t, flags=re.S|re.I)
    m = re.search(r'<body[^>]*>(.*)</body>', t, re.S|re.I)
    body = m.group(1) if m else t
    slug = p['slug']
    # collision-proof ids and local fragment links
    body = re.sub(r'\bid="([^"]+)"', lambda m2: 'id="%s--%s"' % (slug, m2.group(1)), body)
    body = re.sub(r'href="#([^"]+)"', lambda m2: 'href="#%s--%s"' % (slug, m2.group(1)), body)
    # cross-piece links: to in-document anchors when embedded, live URL otherwise
    def xlink(m2):
        target, frag = m2.group(1), m2.group(2) or ''
        if target in embedded:
            ts = by_url[target]['slug']
            return 'href="#%s"' % (('%s--%s' % (ts, frag[1:])) if frag else ('p--' + ts))
        return 'href="https://alexrajcoomar.github.io/%s%s"' % (target, frag)
    body = re.sub(r'href="\.?/?([a-z0-9-]+\.html)(#[^"]*)?"', xlink, body)
    # non-html local assets -> live URLs
    body = re.sub(r'href="((?:[a-z0-9-]+)\.(?:pdf|md|csv|py|json|xml))"',
                  r'href="https://alexrajcoomar.github.io/\1"', body)
    # images inline
    def img(m2):
        src = m2.group(1)
        if src.startswith('data:'): return m2.group(0)
        if src not in IMG_CACHE: IMG_CACHE[src] = img_data(src)
        return m2.group(0).replace('src="%s"' % src, 'src="%s"' % IMG_CACHE[src]) if IMG_CACHE[src] else m2.group(0)
    body = re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', img, body)
    return body

def esc(s): return html.escape(str(s), quote=False)

GROUPS = [
    ("Research and writing", lambda p: p['surface'] == 'independent' and p['k'] != 'Tool'),
    ("Personal investigations", lambda p: p['surface'] == 'personal' and p['k'] != 'Tool'),
    ("Interactive tools", lambda p: p['k'] == 'Tool'),
    ("Coursework", lambda p: p['surface'] == 'course' and p['k'] != 'Tool'),
]

font64 = base64.b64encode(open('InterVariable-sub.woff2','rb').read()).decode()
total_words = sum(M.get(p['slug'],{}).get('words',0) for p in P)
today = "23 August 2026"


TRACKS = [
 ("For the term ahead", "AFM 291 is on your fall schedule; this is the shelf that course built, in study order.",
  [("afm291", "The vault: every chapter document from one place"),
   ("afm291-study-plan", "The plan the vault is meant to be worked through on"),
   ("afm291-ch1-theory-and-analytics", "Chapters in sequence: theory first"),
   ("afm291-ch4-revenue-recognition", "The revenue chapter, the term's centre of gravity"),
   ("afm291-ch10-fair-value", "Fair value, the hardest sustained argument in the set"),
   ("afm291-key-takeaways", "The compression of all of it; read last, reread often"),
   ("afm291-field-manual", "Midterm week: this and the journal-entry reference"),
   ("revenue-recognition", "IFRS 15 in full, the standard behind Chapter 4")]),
 ("For the profession", "The CPA-path material: standards read closely, applied to real Canadian cases.",
  [("ifrs15-judgment-trainer", "62 revenue scenarios; runs in the installed app"),
   ("ifrs15-verification-memo", "How the trainer's answer key was verified against the Handbook"),
   ("five-shall-paragraphs", "The auditing standards' load-bearing requirements, read one by one"),
   ("flagged-in-hindsight", "Five Canadian frauds through the forensic screen; the CAS 240 section pairs with your assurance course"),
   ("business-law-primer", "The legal frame accountants actually operate in"),
   ("us-canada-legal-architecture", "Why the two systems file, enforce, and archive differently")]),
 ("The method", "The discipline the whole site argues for: falsifiable claims, labelled evidence, adversarial testing.",
  [("crucible-cockpit", "What the claim-audit system is; read before any run"),
   ("crucible-run-0", "The leak test: evidence locked in 2023, verdict UNDETERMINED"),
   ("crucible-run-b", "A live thesis refuted by its own retrievable record"),
   ("predictive-history", "An audit instrument run against its own falsification test"),
   ("not-significant", "What a p-value cannot carry"),
   ("the-delayed-test", "Why testing later beats rereading now; the learning science under this whole file"),
   ("the-calibrated-mind", "Keeping score on your own predictions"),
   ("brittle-network", "A pre-registered protocol: how to commit to a test before the data")]),
]
track_html = ['<section class="tracks" id="start"><h2>Start here: three reading tracks</h2>'
  '<p class="tr-note">Picked for the months ahead of you: a 2B AFM term with AFM 291 on the '
  'schedule, an assurance course beside it, and the CPA path both are pointed at. '
  'Everything else is in the full contents below.</p>']
for tname, twhy, entries in TRACKS:
    track_html.append('<div class="track"><h3>%s</h3><p class="tr-why">%s</p><ol>' % (tname, twhy))
    for slug, why in entries:
        pc = next((x for x in P if x['slug'] == slug), None)
        if not pc: continue
        track_html.append('<li><a href="#p--%s">%s</a><span class="tr-r">%s</span></li>'
                          % (slug, esc(pc['t']), esc(why)))
    track_html.append('</ol></div>')
track_html.append('</section>')
track_block = '\n'.join(track_html)

# ---- topic index from the pieces' own tags ----
import collections
tagmap = collections.OrderedDict()
for p in P:
    for tg in p.get('tags', []):
        tagmap.setdefault(tg, []).append(p)
top = sorted(tagmap.items(), key=lambda kv: -len(kv[1]))[:12]
topic_html = ['<section class="topics"><h2>By topic</h2><dl>']
for tg, ps in top:
    links = ' &middot; '.join('<a href="#p--%s">%s</a>' % (x['slug'], esc(x['t'])) for x in ps[:8])
    topic_html.append('<dt>%s</dt><dd>%s</dd>' % (esc(tg), links))
topic_html.append('</dl></section>')
topic_block = '\n'.join(topic_html)

toc_html, body_html = [], []
for gname, want in GROUPS:
    items = [p for p in P if want(p)]
    if not items: continue
    toc_html.append('<h2 class="toc-g">%s <span>%d</span></h2><ol class="toc-l">' % (gname, len(items)))
    for p in items:
        w = M.get(p['slug'],{}).get('words')
        meta = ' · '.join(x for x in (p['k'], p.get('d',''), format(w,',')+' words' if w else '') if x)
        if p['k'] == 'Tool':
            toc_html.append('<li data-t="%s"><a href="#p--%s">%s</a><span class="toc-s">%s · interactive, see note</span></li>'
                            % (esc(p['t'].lower()), p['slug'], esc(p['t']), esc(meta)))
        else:
            toc_html.append('<li data-t="%s"><a href="#p--%s">%s</a>%s<span class="toc-s">%s</span></li>'
                            % (esc((p['t']+' '+p.get('s','')).lower()), p['slug'], esc(p['t']),
                               ' <span class="sel">&#9733; selected</span>' if p.get('featured') else '',
                               esc(meta)))
    toc_html.append('</ol>')

for gname, want in GROUPS:
    for p in [p for p in P if want(p)]:
        w = M.get(p['slug'],{}).get('words')
        meta = ' · '.join(x for x in (gname, p['k'], p.get('d',''), format(w,',')+' words' if w else '') if x)
        body_html.append('<article class="piece" id="p--%s"><div class="phead">'
                         '<a class="up" href="#top">&#8593; Contents</a>'
                         '<p class="pkick">%s</p><h1 class="pt">%s</h1>%s</div>'
                         % (p['slug'], esc(meta), esc(p['t']),
                            (('<p class="ps">%s</p>' % esc(p['s'])) if p.get('s') else '') +
                            (('<p class="pwhy">%s</p>' % esc(p.get('blurb',''))) if p.get('blurb') else '')))
        if p['k'] == 'Tool':
            body_html.append(
                '<div class="stub"><p><b>This is an interactive tool.</b> Its question banks and scoring '
                'run as a program, which cannot execute inside this single-file archive. It works in full '
                'in the installed site app on this phone and in the complete site copy.</p>'
                '<p class="stub-s">%s</p></div>' % esc(p.get('blurb','')))
        else:
            body_html.append('<div class="pbody">%s</div>' % piece_body(p))
        nxt = None
        flat = [x for g2, w2 in GROUPS for x in P if w2(x)]
        i = flat.index(p)
        prv = flat[i-1] if i > 0 else None
        nxt = flat[i+1] if i+1 < len(flat) else None
        navbits = ['<a href="#top">&#8593; Contents</a>']
        if prv: navbits.insert(0, '<a href="#p--%s">&#8592; %s</a>' % (prv['slug'], esc(prv['t'][:34])))
        if nxt: navbits.append('<a href="#p--%s">%s &#8594;</a>' % (nxt['slug'], esc(nxt['t'][:34])))
        body_html.append('<div class="pnav">%s</div>' % ' '.join(navbits))
        body_html.append('</article>')

page = '''<!doctype html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Alex Rajcoomar: the portfolio, offline reader edition</title>
<style>
@font-face{font-family:"InterVar";font-style:normal;font-weight:100 900;font-display:swap;
  src:url(data:font/woff2;base64,''' + font64 + ''') format("woff2")}
:root{--paper:#faf9f6;--panel:#f2f0e9;--ink:#16150f;--ink-2:#55524a;--ink-3:#6f6c63;
  --rule:#ddd9cf;--rule-strong:#bfb9aa;--accent:#14509b;--edge:#8a847c}
@media (prefers-color-scheme:dark){:root{--paper:#131310;--panel:#1b1a16;--ink:#f7f5ef;
  --ink-2:#c0bcb1;--ink-3:#948f85;--rule:#2c2b24;--rule-strong:#454239;--accent:#85adea;--edge:#6e6960}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:"InterVar",ui-sans-serif,system-ui,-apple-system,sans-serif;
  font-size:17px;line-height:1.6;-webkit-text-size-adjust:100%}
.wrap{max-width:46rem;margin:0 auto;padding:0 18px 80px}
header.mast{padding:44px 0 20px;border-bottom:2px solid var(--ink)}
.mast .k{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-3);margin:0 0 14px}
.mast h1{font-size:2rem;line-height:1.1;letter-spacing:-.02em;margin:0}
.mast p{color:var(--ink-2);margin:14px 0 0;font-size:.98rem}
#q{display:none;width:100%;margin:18px 0 0;padding:10px 12px;font:inherit;font-size:.95rem;
  border:1px solid var(--edge);background:var(--paper);color:var(--ink);border-radius:2px}
.js #q{display:block}
.tracks{border:1px solid var(--rule-strong);border-left:4px solid var(--accent);
  background:var(--panel);padding:6px 18px 14px;margin:26px 0}
.tracks h2{font-size:1.2rem;margin:14px 0 4px}
.tr-note{color:var(--ink-2);font-size:.93rem;margin:0 0 6px}
.track h3{font-size:1rem;margin:18px 0 2px}
.tr-why{color:var(--ink-3);font-size:.88rem;margin:0 0 6px}
.track ol{margin:0;padding-left:1.3em}
.track li{padding:3px 0}
.track a{color:var(--accent);font-weight:600;text-decoration:none}
.tr-r{display:block;font-size:.84rem;color:var(--ink-3)}
.topics h2{font-size:1.05rem;margin:26px 0 4px}
.topics dl{margin:0;font-size:.88rem}
.topics dt{font-weight:650;margin-top:8px}
.topics dd{margin:2px 0 0;color:var(--ink-2)}
.topics a{color:var(--accent);text-decoration:none}
.sel{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3)}
.pwhy{color:var(--ink-2);font-size:.95rem;border-left:3px solid var(--rule-strong);
  padding-left:12px;margin:12px 0 0}
.pnav{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;
  border-top:1px solid var(--rule);margin-top:30px;padding:12px 0;font-size:.88rem}
.pnav a{color:var(--accent);text-decoration:none}
.toc-g{font-size:1.05rem;margin:30px 0 6px;display:flex;gap:10px;align-items:baseline}
.toc-g span{font-size:.8rem;color:var(--ink-3);font-variant-numeric:tabular-nums}
.toc-l{list-style:none;margin:0;padding:0}
.toc-l li{border-bottom:1px solid var(--rule);padding:9px 0}
.toc-l a{color:var(--accent);text-decoration:none;font-weight:600}
.toc-s{display:block;font-size:.82rem;color:var(--ink-3);margin-top:2px}
.piece{border-top:3px solid var(--ink);margin-top:56px}
.phead{padding:20px 0 6px;position:relative}
.up{float:right;font-size:.8rem;color:var(--ink-3);text-decoration:none;border:1px solid var(--edge);
  padding:3px 10px;border-radius:2px}
.pkick{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);margin:0 0 10px}
.pt{font-size:1.7rem;line-height:1.12;letter-spacing:-.015em;margin:0}
.ps{color:var(--ink-2);margin:8px 0 0}
.pbody{overflow-wrap:break-word}
.pbody h1{font-size:1.45rem;line-height:1.15}
.pbody h2{font-size:1.25rem;line-height:1.2;margin:1.6em 0 .5em}
.pbody h3{font-size:1.05rem;margin:1.4em 0 .4em}
.pbody img,.pbody svg{max-width:100%;height:auto}
.pbody table{border-collapse:collapse;font-size:.88rem;display:block;max-width:100%;overflow-x:auto}
.pbody th,.pbody td{border-bottom:1px solid var(--rule);padding:6px 10px 6px 0;text-align:left;vertical-align:top}
.pbody th{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-3)}
.pbody pre{background:var(--panel);border:1px solid var(--rule);padding:10px 12px;overflow-x:auto;font-size:.82rem}
.pbody code{font-family:ui-monospace,Menlo,monospace;font-size:.9em;white-space:pre-wrap;overflow-wrap:anywhere}
.pbody canvas{max-width:100%;height:auto}
.pbody a{color:var(--accent)}
.pbody blockquote{margin:1em 0;padding:2px 0 2px 14px;border-left:3px solid var(--rule-strong);color:var(--ink-2)}
.pbody .tbl-wrap,.pbody .cm-tblwrap{overflow-x:auto}
.pbody button,.pbody input[type=range],.pbody input[type=search]{display:none}
.stub{border:1px solid var(--rule-strong);border-left:4px solid var(--accent);background:var(--panel);
  padding:14px 18px;margin:16px 0}
.stub p{margin:0 0 8px}.stub-s{color:var(--ink-2);font-size:.92rem}
</style>
</head>
<body id="top">
<div class="wrap">
<header class="mast">
  <p class="k">Alex Rajcoomar &middot; Portfolio &middot; Offline reader edition &middot; archived ''' + today + '''</p>
  <h1>The whole shelf, in one file.</h1>
  <p>''' + str(len(P)) + ''' pieces, ''' + format(total_words, ',') + ''' measured words, embedded in a single
  document so every article opens instantly from this phone with no connection and no server.
  Interactive tools are programs, so they are listed here but run in the installed site app.
  The live site is <a href="https://alexrajcoomar.github.io">alexrajcoomar.github.io</a>.</p>
  <input id="q" type="search" placeholder="Filter the contents by title or topic" aria-label="Filter the contents">
</header>
''' + track_block + '''
''' + topic_block + '''
<nav aria-label="Contents">
''' + '\n'.join(toc_html) + '''
</nav>
''' + '\n'.join(body_html) + '''
</div>
<script>
document.body.className+=' js';
(function(){
  var q=document.getElementById('q');if(!q)return;
  var rows=[].slice.call(document.querySelectorAll('.toc-l li'));
  q.addEventListener('input',function(){
    var v=q.value.trim().toLowerCase();
    rows.forEach(function(r){r.hidden=v&&r.getAttribute('data-t').indexOf(v)===-1;});
  });
})();
</script>
</body>
</html>'''
# the reader edition lives beside the pieces it embeds; the script chdir'd to the repository root above
out = 'reader.html'
open(out, 'w', encoding='utf-8').write(page)
print("written:", out, "%.1f MB" % (len(page)/1048576))
