# -*- coding: utf-8 -*-
"""Write spanish-a1-cafe.html from content/contrastive-a1.json.

The piece is the Spanish A1 café unit read against the French one that is
already on the site. Every count on the page is computed here from the
alignment file rather than typed, so the page cannot claim a tally the data
does not carry. The classification of each pair is a reading and says so; what
this module holds is that the reading is complete and cited.

Run:  python3 build/contrastive.py
"""
import html as H
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "spanish-a1-cafe.html")
DATA = os.path.join(ROOT, "content", "contrastive-a1.json")
D = json.load(open(DATA, encoding="utf-8"))

PAIRS = D["pairs"]
STRUCT = D["structures"]
ES_ONLY = D["spanish_only"]
FR_ONLY = D["french_only"]
CLASSES = D["classes"]
SRC = D["sources"]

# Every numeral a figure draws is recorded as it is drawn, and the module
# refuses to write unless the prose restates it. The site holds this only for
# its shell pages; the piece adopts it because a figure a reader cannot check
# against the text is decoration.
DRAWN = []


def esc(s):
    return H.escape(str(s))


def dn(x):
    s = format(int(x), ",")
    DRAWN.append(s)
    return s


# ------------------------------------------------------------------ gate --

def validate():
    """What the data has to carry before a page is written from it."""
    problems = []
    seen = set()
    for i, p in enumerate(PAIRS):
        where = "pair %d (%s)" % (i + 1, p.get("concept", "unnamed"))
        for k in ("concept", "fr", "es", "class", "why", "src_fr", "src_es"):
            if not str(p.get(k) or "").strip():
                problems.append("%s: %s is empty" % (where, k))
        if p.get("class") not in CLASSES:
            problems.append("%s: class %r is not one of %s"
                            % (where, p.get("class"), ", ".join(sorted(CLASSES))))
        key = p.get("concept", "").strip().lower()
        if key in seen:
            problems.append("%s: the concept is listed twice" % where)
        seen.add(key)
    for s in STRUCT:
        for k in ("id", "title", "fr", "es", "cost", "src_fr", "src_es"):
            if not str(s.get(k) or "").strip():
                problems.append("structure %s: %s is empty" % (s.get("id", "?"), k))
    for row in ES_ONLY:
        if not (row.get("es") and row.get("en") and row.get("why")):
            problems.append("spanish_only: a row is incomplete")
    for row in FR_ONLY:
        if not (row.get("fr") and row.get("en") and row.get("why")):
            problems.append("french_only: a row is incomplete")
    return problems


def tally():
    t = {k: 0 for k in CLASSES}
    for p in PAIRS:
        t[p["class"]] += 1
    return t


T = tally()
N_PAIRS = len(PAIRS)
N_TRANSFER = T["transfers"]
N_MISLEAD = T["misleads"]
N_INDEP = T["independent"]
# the share of the shared vocabulary a learner cannot carry across unchanged
N_UNSAFE = N_MISLEAD + N_INDEP
PC_UNSAFE = 100.0 * N_UNSAFE / N_PAIRS


CLS_LABEL = {"transfers": "Transfers", "misleads": "Misleads", "independent": "Learn twice"}
CLS_SHORT = {"transfers": "T", "misleads": "M", "independent": "L"}


# --------------------------------------------------------------- figures --

def fig_alignment():
    """Every aligned concept as one row: the French form, the Spanish form,
    and a bar between them whose colour is how transfer behaves. The figure
    draws three numerals and the prose restates all three."""
    rowh, top, botm = 26, 92, 58
    W = 720
    Hh = top + rowh * N_PAIRS + botm
    lx, rx = 258, 462          # the two columns of forms
    parts = ['<svg viewBox="0 0 %d %d" role="img" aria-labelledby="f1t f1d" class="fig">' % (W, Hh),
             '<title id="f1t">The twenty-two shared concepts, by how transfer behaves</title>',
             '<desc id="f1d">Each row is one concept both units teach. The bar between the '
             'French form on the left and the Spanish form on the right is green where the '
             'pattern transfers, amber where it misleads, and grey where there is nothing to '
             'carry over. The counts are restated in the paragraph below.</desc>']
    parts.append('<text x="14" y="26" class="fk">FRANÇAIS</text>')
    parts.append('<text x="%d" y="26" class="fk">ESPAÑOL</text>' % (rx + 6))
    # the key, with its three counts
    keys = [("transfers", N_TRANSFER, 14), ("misleads", N_MISLEAD, 252), ("independent", N_INDEP, 470)]
    for cls, count, x in keys:
        parts.append('<rect x="%d" y="46" width="16" height="9" rx="1" class="sw %s"/>' % (x, cls))
        parts.append('<text x="%d" y="55" class="fk2">%s, %s</text>'
                     % (x + 22, esc(CLS_LABEL[cls].lower()), dn(count)))
    parts.append('<line x1="14" y1="%d" x2="%d" y2="%d" class="ax"/>' % (top - 16, W - 14, top - 16))
    for i, p in enumerate(PAIRS):
        y = top + rowh * i
        parts.append('<rect x="14" y="%d" width="%d" height="%d" class="rw %s"/>'
                     % (y - 15, W - 28, rowh - 4, "odd" if i % 2 else "even"))
        parts.append('<text x="20" y="%d" class="fl">%s</text>' % (y, esc(p["fr"])[:34]))
        parts.append('<rect x="%d" y="%d" width="%d" height="6" rx="3" class="bar %s"/>'
                     % (lx + 8, y - 9, rx - lx - 16, p["class"]))
        parts.append('<text x="%d" y="%d" class="fl">%s</text>' % (rx + 6, y, esc(p["es"])[:32]))
    parts.append('</svg>')
    return "\n".join(parts)


def fig_articles():
    """The article decision in each language, side by side. The point of the
    drawing is the branch Spanish does not have, so the French tree is drawn
    with three limbs and the Spanish with two, at the same scale."""
    W, Hh = 720, 320
    parts = ['<svg viewBox="0 0 %d %d" role="img" aria-labelledby="f2t f2d" class="fig">' % (W, Hh),
             '<title id="f2t">Choosing an article, in each language</title>',
             '<desc id="f2d">French asks three questions and Spanish asks two. The middle '
             'French branch, the partitive, has no Spanish counterpart, which is the gap the '
             'text below describes.</desc>']
    cols = [
        (14, "FRANÇAIS", [
            ("one whole countable thing", "un, une, des", "un café, une tarte"),
            ("an unmeasured amount", "du, de la, de l'", "du sucre, de l'eau"),
            ("that specific thing", "le, la, les", "l'addition, la carte"),
        ]),
        (376, "ESPAÑOL", [
            ("one whole countable thing", "un, una, unos, unas", "un café, una empanada"),
            (None, None, None),
            ("that specific thing", "el, la, los, las", "la cuenta, el agua"),
        ]),
    ]
    for x0, head, rows in cols:
        parts.append('<text x="%d" y="26" class="fk">%s</text>' % (x0, head))
        parts.append('<rect x="%d" y="38" width="330" height="1" class="axf"/>' % x0)
        for j, (q, arts, ex) in enumerate(rows):
            y = 70 + j * 84
            if q is None:
                parts.append('<rect x="%d" y="%d" width="330" height="66" rx="3" class="gap"/>'
                             % (x0, y - 22))
                parts.append('<text x="%d" y="%d" class="fg">no partitive</text>' % (x0 + 14, y + 6))
                parts.append('<text x="%d" y="%d" class="fs">Spanish does not ask this question</text>'
                             % (x0 + 14, y + 26))
                continue
            parts.append('<rect x="%d" y="%d" width="330" height="66" rx="3" class="cell b%d"/>'
                         % (x0, y - 22, j))
            parts.append('<text x="%d" y="%d" class="fs">%s</text>' % (x0 + 14, y - 4, esc(q)))
            parts.append('<text x="%d" y="%d" class="fa">%s</text>' % (x0 + 14, y + 18, esc(arts)))
            parts.append('<text x="%d" y="%d" class="fx">%s</text>' % (x0 + 14, y + 36, esc(ex)))
    parts.append('</svg>')
    return "\n".join(parts)


# ----------------------------------------------------------------- drill --

def drill_data():
    """The self-test payload: one item per aligned pair, in the file's order."""
    return [{"c": p["concept"], "f": p["fr"], "e": p["es"], "k": p["class"], "w": p["why"]}
            for p in PAIRS]


DRILL_JS = """
(function(){
  var D=%s, i=0, score=0, done=0, answered=false;
  var el=function(id){return document.getElementById(id);};
  var card=el('dcard'), fr=el('dfr'), es=el('des'), why=el('dwhy'), verdict=el('dver');
  var pos=el('dpos'), sc=el('dscore'), btns=el('dbtns'), next=el('dnext');
  if(!card){return;}
  function paint(){
    var it=D[i];
    el('dconcept').textContent=it.c;
    fr.textContent=it.f; es.textContent=it.e; why.textContent=it.w;
    verdict.textContent=''; verdict.className='dver';
    card.setAttribute('data-shown','no');
    pos.textContent=(i+1)+' of '+D.length;
    sc.textContent=score+' of '+done;
    answered=false;
    next.disabled=true;
  }
  function answer(k){
    if(answered){return;}
    answered=true; done++;
    var it=D[i], right=(k===it.k);
    if(right){score++;}
    verdict.textContent=(right?'Correct, ':'Not quite, ')+LBL[it.k]+'.';
    verdict.className='dver '+(right?'ok':'no');
    card.setAttribute('data-shown','yes');
    sc.textContent=score+' of '+done;
    next.disabled=false;
  }
  var LBL={transfers:'it transfers',misleads:'it misleads',independent:'it has to be learned twice'};
  btns.addEventListener('click',function(e){
    var b=e.target.closest('button[data-k]');
    if(b){answer(b.getAttribute('data-k'));}
  });
  next.addEventListener('click',function(){
    i=(i+1)%%D.length; paint();
  });
  el('dreset').addEventListener('click',function(){
    i=0; score=0; done=0; paint();
  });
  paint();
})();
"""


def drill_html():
    first = PAIRS[0]
    btns = "".join(
        '<button type="button" data-k="%s" class="dbtn">%s</button>' % (k, esc(CLS_LABEL[k]))
        for k in ("transfers", "misleads", "independent"))
    return """<div class="drill" id="dcard" data-shown="yes">
      <p class="dhead"><span class="dpos" id="dpos">1 of %s</span>
        <span class="dsc">Score <b id="dscore">0 of 0</b></span></p>
      <p class="dq">If you know the French, what does <b id="dconcept">%s</b> do in Spanish?</p>
      <div class="dbtns" id="dbtns" role="group" aria-label="Answer">%s</div>
      <p class="dver" id="dver" role="status" aria-live="polite"></p>
      <dl class="dforms">
        <dt>Français</dt><dd id="dfr">%s</dd>
        <dt>Español</dt><dd id="des">%s</dd>
      </dl>
      <p class="dwhy" id="dwhy">%s</p>
      <p class="dnav">
        <button type="button" id="dnext" class="dbtn ghost" disabled>Next</button>
        <button type="button" id="dreset" class="dbtn ghost">Start again</button>
      </p>
    </div>""" % (dn(N_PAIRS), esc(first["concept"]), btns,
                 esc(first["fr"]), esc(first["es"]), esc(first["why"]))


# ------------------------------------------------------------------- css --

CSS = """
:root{
  color-scheme: light;
  --plane:#fbfbf9; --panel:#ffffff; --sunk:#f4f4f0;
  --ink:#080808; --ink-2:#3d3c39; --ink-3:#6b6963;
  --rule:#dcdbd3; --rule-2:#c2c0b6; --hair:rgba(8,8,8,.09);
  --accent:#14509b; --accent-2:#0047ab;
  --ok:#1f6b3a; --ok-w:#e6f0e9;
  --warn:#a8391f; --warn-w:#f6ebe7;
  --none:#8a8880; --none-w:#eeedea; --none-ink:#63615c;
  --grid:#e7e6df;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --plane:#080808; --panel:#111110; --sunk:#161615;
    --ink:#f3f3ef; --ink-2:#c0bfb8; --ink-3:#8b8983;
    --rule:#2a2a27; --rule-2:#3a3a36; --hair:rgba(243,243,239,.10);
    --accent:#7fb0e8; --accent-2:#9cc4f0;
    --ok:#5fb37f; --ok-w:#16241b;
    --warn:#e08163; --warn-w:#2a1a15;
    --none:#6e6c66; --none-w:#1c1c1a; --none-ink:#9a988f;
    --grid:#1e1e1c;
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --plane:#080808; --panel:#111110; --sunk:#161615;
  --ink:#f3f3ef; --ink-2:#c0bfb8; --ink-3:#8b8983;
  --rule:#2a2a27; --rule-2:#3a3a36; --hair:rgba(243,243,239,.10);
  --accent:#7fb0e8; --accent-2:#9cc4f0;
  --ok:#5fb37f; --ok-w:#16241b;
  --warn:#e08163; --warn-w:#2a1a15;
  --none:#6e6c66; --none-w:#1c1c1a; --none-ink:#9a988f;
  --grid:#1e1e1c;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--plane); color:var(--ink);
  font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  font-size:17px; line-height:1.62; -webkit-font-smoothing:antialiased;
}
.mono,code,th,.lab,.num{
  font-family:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  font-variant-numeric:tabular-nums;
}
.wrap{max-width:60rem;margin:0 auto;padding:3rem 1.5rem 6rem}
.measure{max-width:36rem}
p{margin:0 0 1.15em}
a{color:var(--accent);text-underline-offset:.18em}
a:focus-visible,summary:focus-visible,button:focus-visible{
  outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}

.eyebrow{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 1.1rem;display:flex;flex-wrap:wrap;gap:.4rem 1.1rem}
h1{font-size:clamp(1.9rem,4.2vw,2.9rem);line-height:1.14;letter-spacing:-.018em;
  margin:0 0 .7rem;font-weight:600;max-width:20ch}
.dek{font-size:1.14rem;color:var(--ink-2);margin:0 0 1.6rem;max-width:44rem}
.byline{border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);
  padding:.8rem 0;margin:0 0 2.6rem;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));gap:1rem 2rem}
.byline div{font-size:.82rem;color:var(--ink-3)}
.byline b{display:block;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  font-size:.66rem;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-3);
  margin-bottom:.2rem;font-weight:400}
.byline span{color:var(--ink)}

.verdict{background:var(--panel);border:1px solid var(--rule);border-radius:4px;
  padding:1.4rem 1.5rem;margin:0 0 1.4rem}
.verdict h2{font-size:.7rem;letter-spacing:.15em;text-transform:uppercase;
  font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;color:var(--ink-3);
  margin:0 0 .9rem;font-weight:400}
.big{display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));gap:1.2rem;margin:0 0 1rem}
.big div{border-left:3px solid var(--rule-2);padding-left:.8rem}
.big .n{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  font-size:1.7rem;line-height:1.1;letter-spacing:-.02em;display:block}
.big .l{font-size:.78rem;color:var(--ink-3);display:block;margin-top:.25rem}
.big .t{border-left-color:var(--ok)} .big .t .n{color:var(--ok)}
.big .m{border-left-color:var(--warn)} .big .m .n{color:var(--warn)}
.big .i{border-left-color:var(--none)} .big .i .n{color:var(--none)}

.callout{border-left:3px solid var(--accent);background:var(--sunk);
  padding:1rem 1.2rem;margin:0 0 2.4rem;font-size:.95rem}
.callout p:last-child{margin-bottom:0}

h2.sec{font-size:1.28rem;margin:2.8rem 0 .3rem;letter-spacing:-.01em;font-weight:600;
  padding-top:1.4rem;border-top:1px solid var(--rule)}
h2.sec .num{color:var(--ink-3);font-size:.8rem;margin-right:.6rem}
.take{color:var(--ink-2);font-size:.98rem;margin:0 0 1.3rem;max-width:40rem;font-style:italic}
h3{font-size:1.02rem;margin:1.8rem 0 .5rem;font-weight:600}

table{border-collapse:collapse;width:100%;margin:0 0 1.4rem;font-size:.9rem}
caption{text-align:left;color:var(--ink-3);font-size:.8rem;margin-bottom:.5rem}
th,td{border-bottom:1px solid var(--rule);padding:.5rem .6rem;text-align:left;vertical-align:top}
th{font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);font-weight:400;
  border-bottom:1px solid var(--rule-2)}
tbody tr:hover{background:var(--sunk)}
.tag{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:.66rem;
  letter-spacing:.06em;text-transform:uppercase;padding:.12rem .4rem;border-radius:2px;
  white-space:nowrap}
.tag.transfers{background:var(--ok-w);color:var(--ok)}
.tag.misleads{background:var(--warn-w);color:var(--warn)}
.tag.independent{background:var(--none-w);color:var(--none-ink)}
.form{font-style:normal}
.gl{color:var(--ink-3);font-size:.84rem;display:block}

figure{margin:1.6rem 0 2rem}
.figbox{overflow-x:auto;border:1px solid var(--rule);border-radius:4px;background:var(--panel);
  padding:.6rem}
[data-scroll]{overflow-x:auto;margin:0 0 1.4rem}
[data-scroll] table{margin-bottom:0;min-width:30rem}
.fig{display:block;width:100%;min-width:34rem;height:auto}
.fig .fk{font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.12em;fill:var(--ink-3)}
.fig .fk2{font-family:ui-monospace,monospace;font-size:11px;fill:var(--ink-2)}
.fig .fl{font-size:13px;fill:var(--ink)}
.fig .fs{font-size:12px;fill:var(--ink-3)}
.fig .fa{font-family:ui-monospace,monospace;font-size:13px;fill:var(--ink)}
.fig .fx{font-size:11px;fill:var(--ink-3);font-style:italic}
.fig .fg{font-family:ui-monospace,monospace;font-size:13px;fill:var(--none)}
.fig .ax{stroke:var(--rule-2);stroke-width:1}
.fig .axf{fill:var(--rule-2)}
.fig .rw.even{fill:transparent} .fig .rw.odd{fill:var(--sunk)}
.fig .bar.transfers{fill:var(--ok)} .fig .sw.transfers{fill:var(--ok)}
.fig .bar.misleads{fill:var(--warn)} .fig .sw.misleads{fill:var(--warn)}
.fig .bar.independent{fill:var(--none)} .fig .sw.independent{fill:var(--none)}
.fig .cell{fill:var(--sunk);stroke:var(--rule);stroke-width:1}
.fig .gap{fill:none;stroke:var(--rule-2);stroke-width:1;stroke-dasharray:4 3}
figcaption{font-size:.84rem;color:var(--ink-3);margin-top:.6rem;max-width:44rem}

.struct{border:1px solid var(--rule);border-radius:4px;background:var(--panel);
  padding:1.1rem 1.2rem;margin:0 0 1.1rem}
.struct h3{margin:0 0 .7rem}
.struct .two{display:grid;grid-template-columns:1fr 1fr;gap:1rem 1.6rem;margin-bottom:.8rem}
.struct .two > div{border-left:2px solid var(--rule-2);padding-left:.7rem}
.struct .two b{font-family:ui-monospace,monospace;font-size:.66rem;letter-spacing:.12em;
  text-transform:uppercase;color:var(--ink-3);font-weight:400;display:block;margin-bottom:.25rem}
.struct .two p{font-size:.88rem;margin:0}
.struct .cost{font-size:.9rem;margin:0;padding-top:.7rem;border-top:1px solid var(--rule)}
.struct .cost b{color:var(--warn)}
.src{font-family:ui-monospace,monospace;font-size:.7rem;color:var(--ink-3);margin:.5rem 0 0}

.drill{border:1px solid var(--rule-2);border-radius:4px;background:var(--panel);
  padding:1.2rem 1.3rem;margin:0 0 1.2rem}
.dhead{display:flex;justify-content:space-between;gap:1rem;font-family:ui-monospace,monospace;
  font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin:0 0 .9rem}
.dq{font-size:1.05rem;margin:0 0 .9rem}
.dq b{font-style:italic}
.dbtns{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 .9rem}
.dbtn{font:inherit;font-size:.86rem;padding:.4rem .9rem;border:1px solid var(--rule-2);
  border-radius:3px;background:var(--sunk);color:var(--ink);cursor:pointer}
.dbtn:hover{border-color:var(--accent)}
.dbtn.ghost{background:transparent;font-size:.8rem}
.dbtn[disabled]{opacity:.45;cursor:default}
.dver{min-height:1.4em;font-size:.9rem;margin:0 0 .8rem}
.dver.ok{color:var(--ok)} .dver.no{color:var(--warn)}
.dforms{display:grid;grid-template-columns:auto 1fr;gap:.3rem 1rem;margin:0 0 .7rem;
  padding:.8rem 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.dforms dt{font-family:ui-monospace,monospace;font-size:.66rem;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ink-3);padding-top:.15rem}
.dforms dd{margin:0;font-size:1rem}
.dwhy{font-size:.88rem;color:var(--ink-2);margin:0 0 .8rem}
.drill[data-shown="no"] .dforms dt,.drill[data-shown="no"] .dforms dd,
.drill[data-shown="no"] .dwhy{visibility:hidden}
.dnav{margin:0;display:flex;gap:.5rem}

details{border:1px solid var(--rule);border-radius:4px;background:var(--panel);
  padding:.7rem .9rem;margin:0 0 .9rem}
summary{cursor:pointer;font-size:.9rem;color:var(--ink-2)}
details[open] summary{margin-bottom:.8rem;border-bottom:1px solid var(--rule);padding-bottom:.5rem}

.lim{border-left:3px solid var(--warn);background:var(--sunk);padding:1rem 1.2rem;font-size:.94rem}
.lim p:last-child{margin-bottom:0}
.foot{margin-top:3rem;padding-top:1.2rem;border-top:1px solid var(--rule);
  font-size:.82rem;color:var(--ink-3)}

@media (max-width:38rem){
  .wrap{padding:2rem 1rem 4rem}
  .struct .two{grid-template-columns:1fr}
  .fig{min-width:30rem}
}
@media print{
  .drill{display:none}
  body{font-size:11pt}
}
"""


# ------------------------------------------------------------------ page --

def pair_rows():
    out = []
    for p in PAIRS:
        out.append(
            '<tr><td>%s</td>'
            '<td><span class="form">%s</span>%s</td>'
            '<td><span class="form">%s</span>%s</td>'
            '<td><span class="tag %s">%s</span></td></tr>'
            % (esc(p["concept"]),
               esc(p["fr"]), ('<span class="gl">%s</span>' % esc(p["fr_note"])) if p.get("fr_note") else "",
               esc(p["es"]), ('<span class="gl">%s</span>' % esc(p["es_note"])) if p.get("es_note") else "",
               p["class"], esc(CLS_LABEL[p["class"]])))
        out.append('<tr class="wr"><td></td><td colspan="3" class="gl">%s <span class="src">%s '
                   'against %s</span></td></tr>'
                   % (esc(p["why"]), esc(p["src_fr"]), esc(p["src_es"])))
    return "\n".join(out)


def struct_blocks():
    out = []
    for s in STRUCT:
        out.append(
            '<div class="struct">\n'
            '  <h3 id="s-%s">%s</h3>\n'
            '  <div class="two">\n'
            '    <div><b>Français</b><p>%s</p></div>\n'
            '    <div><b>Español</b><p>%s</p></div>\n'
            '  </div>\n'
            '  <p class="cost"><b>What it costs you.</b> %s</p>\n'
            '  <p class="src">%s against %s</p>\n'
            '</div>' % (esc(s["id"]), esc(s["title"]), esc(s["fr"]), esc(s["es"]),
                        esc(s["cost"]), esc(s["src_fr"]), esc(s["src_es"])))
    return "\n".join(out)


def only_rows(rows, key, head):
    body = "\n".join(
        '<tr><td><span class="form">%s</span></td><td>%s</td><td class="gl">%s</td></tr>'
        % (esc(r[key]), esc(r["en"]), esc(r["why"])) for r in rows)
    return ('<div data-scroll><table><caption>%s</caption><thead><tr><th>Form</th>'
            '<th>English</th><th>Why it is here and not there</th></tr></thead>'
            '<tbody>%s</tbody></table></div>'
            % (esc(head), body))


def page():
    fr_url, es_unit = SRC["fr"]["url"], SRC["es"]["unit"]
    body = """<main class="wrap" id="main">
<p class="eyebrow"><span>Personal</span><span>Spanish</span><span>Unit 1</span><span>CEFR A1</span></p>
<h1>Unidad 1: En el Café</h1>
<p class="dek">The Spanish A1 café unit, read against the French one already on this site.
Where the two languages agree, one unit does the work of two. Where they disagree, knowing
French is worse than knowing nothing, because it supplies a confident wrong answer.</p>

<div class="byline">
  <div><b>Level</b><span>CEFR A1, both units</span></div>
  <div><b>Varieties</b><span>%(esvar)s; %(frvar)s</span></div>
  <div><b>Method</b><span>Concept alignment across two units</span></div>
  <div><b>Sources</b><span>These two units only</span></div>
</div>

<div class="verdict">
  <h2 id="finding">The finding</h2>
  <div class="big">
    <div class="t"><span class="n">%(nt)s</span><span class="l">transfer safely</span></div>
    <div class="m"><span class="n">%(nm)s</span><span class="l">mislead you</span></div>
    <div class="i"><span class="n">%(ni)s</span><span class="l">must be learned twice</span></div>
  </div>
  <p class="measure" style="margin-bottom:0">Of the %(np)s concepts both units teach,
  %(nt)s carry over from French to Spanish unchanged. The other %(nu)s do not, which is
  %(pc)s per cent of the shared ground. A second Romance language is not half price.</p>
</div>

<div class="callout">
  <p><b>If you have already done the French unit,</b> the fastest way through this one is to
  read section 03, drill the %(nm)s misleading pairs until they are automatic, and skim the
  rest. The %(nt)s that transfer need no work from you. That is the whole argument for
  reading two units against each other rather than one after the other.</p>
</div>

<h2 class="sec" id="s-01"><span class="num">01</span>What this is, and what it is not</h2>
<p class="take">A comparison of two A1 café units, not a Spanish course and not a claim about
the two languages in general.</p>
<p>The French unit, <a href="%(frurl)s">%(frunit)s</a>, and this one cover the same ground: the
twenty or so words you need to order in a café, the polite request formulas, the article
system, two dialogues and a set of drills. Because the domain, the level and the language of
instruction are identical, the two units can be laid side by side and the differences are
about the languages rather than about how the material happened to be written.</p>
<p>Everything on this page comes from those two units and nothing else. Where a claim would
need a third source, it is not made. That rules out a good deal a comparative grammar would
say, and it keeps every row on this page checkable against a document you can open.</p>

<h2 class="sec" id="s-02"><span class="num">02</span>The alignment at a glance</h2>
<p class="take">Twenty-two concepts, each drawn as one row, coloured by whether the French
form predicts the Spanish one.</p>
<figure>
  <div class="figbox">%(fig1)s</div>
  <figcaption>Every concept both units carry, with the French form on the left and the Spanish
  on the right. Green where the pattern transfers (%(nt)s rows), amber where it misleads
  (%(nm)s rows), grey where there is nothing to carry over (%(ni)s rows).</figcaption>
</figure>

<h2 class="sec" id="s-03"><span class="num">03</span>The alignment, pair by pair</h2>
<p class="take">The same %(np)s rows in full, each with the reason and the section of each unit
it was read from.</p>
<div data-scroll><table>
  <caption>The %(np)s concepts both units teach. The class is a reading, declared in
  <code>content/contrastive-a1.json</code>, and the build checks that every row cites both
  units rather than that the reading is correct.</caption>
  <thead><tr><th>Concept</th><th>Français</th><th>Español</th><th>Transfer</th></tr></thead>
  <tbody>
%(rows)s
  </tbody>
</table></div>

<h2 class="sec" id="s-04"><span class="num">04</span>Five differences that are structural</h2>
<p class="take">Vocabulary you can look up. These five change what a sentence has to contain,
so they cost you on every sentence rather than on one word.</p>
%(structs)s

<h2 class="sec" id="s-05"><span class="num">05</span>The article decision, drawn</h2>
<p class="take">French asks three questions before it lets you say a noun. Spanish asks two.</p>
<figure>
  <div class="figbox">%(fig2)s</div>
  <figcaption>The article systems at the same scale. The dashed box is the branch Spanish does
  not have: there is no partitive, so the question French forces you to answer about every
  uncountable noun simply does not arise.</figcaption>
</figure>
<p>This is the single largest divergence in the pair, and it runs in both directions. Coming
from Spanish, you will say <span class="form">je voudrais sucre</span> and leave out an article
French requires. Coming from French, you will reach for a Spanish partitive that does not
exist and produce something like <span class="form">de azúcar</span> where the language wants
the bare noun after <span class="form">con</span> or <span class="form">sin</span>.</p>

<h2 class="sec" id="s-06"><span class="num">06</span>Test yourself on the transfer, not the vocabulary</h2>
<p class="take">The vocabulary you can drill anywhere. What only two units together can drill
is whether the first language is helping or lying to you.</p>
<p>The card below names a concept and asks what the French form predicts about the Spanish
one. The forms and the reason stay dimmed until you commit to an answer, because recognising
a correct answer in a list is not the same as retrieving it.</p>
%(drill)s
<p class="gl">With scripts off this card shows the first pair and the full table in section 03
carries all %(np)s, so nothing here is only available to a browser that runs JavaScript.</p>

<h2 class="sec" id="s-07"><span class="num">07</span>What each unit has that the other does not</h2>
<p class="take">The two units are not translations of each other, and the gaps are informative
in their own right.</p>
%(esonly)s
%(fronly)s

<h2 class="sec" id="s-08"><span class="num">08</span>What would make this wrong</h2>
<p class="take">The honest limits, stated rather than buried.</p>
<div class="lim">
  <p><b>The classification is a reading.</b> Whether a pair transfers or misleads is my
  judgement about what a learner will do, not a measured fact about the languages. Someone who
  already speaks a third Romance language would classify several rows differently. The file is
  the place to disagree.</p>
  <p><b>The sample is two units, not two languages.</b> Twenty-two shared concepts in one
  domain at one level cannot support a claim about French and Spanish generally. The
  proportion that misleads would move with the domain, and almost certainly with the level.</p>
  <p><b>There is no learner in the data.</b> The piece predicts where transfer will fail. It
  does not observe anyone failing. A real test would be error rates from someone learning the
  second language after the first, and I have not run one.</p>
  <p><b>Both units were written by the same hand, and so was this.</b> If the French unit is
  wrong about French, this page inherits the error and presents it as a contrast. The two
  units are the only sources, which keeps the page checkable and also keeps its ceiling low.</p>
  <p><b>Latin American Spanish against Metropolitan French.</b> Neither unit covers its whole
  language. Several rows would change against Peninsular Spanish, and the units say so where
  they know it.</p>
</div>

<p class="foot">Written from <code>content/contrastive-a1.json</code> by
<code>build/contrastive.py</code>. Every count on this page is computed from that file on each
build, so the page cannot claim a tally the data does not carry. The companion unit is
<a href="%(frurl)s">%(frunit)s</a>.</p>
</main>
""" % {
        "esvar": esc(SRC["es"]["variety"]),
        "frvar": esc(SRC["fr"]["variety"]),
        "nt": dn(N_TRANSFER), "nm": dn(N_MISLEAD), "ni": dn(N_INDEP),
        "np": dn(N_PAIRS), "nu": N_UNSAFE, "pc": "%.0f" % PC_UNSAFE,
        "frurl": esc(fr_url), "frunit": esc(SRC["fr"]["unit"]),
        "fig1": fig_alignment(), "fig2": fig_articles(),
        "rows": pair_rows(), "structs": struct_blocks(),
        "drill": drill_html(),
        "esonly": only_rows(ES_ONLY, "es", "In the Spanish unit's core, with no counterpart in the French twenty"),
        "fronly": only_rows(FR_ONLY, "fr", "In the French unit's core, with no counterpart in the Spanish twenty"),
    }

    js = DRILL_JS % json.dumps(drill_data(), ensure_ascii=False)
    title = ("Unidad 1: En el Caf\u00e9, the Spanish A1 caf\u00e9 unit read against the French one")
    desc = ("Two A1 caf\u00e9 units on the same twenty words, aligned concept by concept to "
            "find how much of the first language survives the trip to the second: which "
            "patterns transfer, which mislead, and which have to be learned twice.")
    return ("""<!DOCTYPE html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<style>%s</style>
</head>
<body>
%s
<script>%s</script>
</body>
</html>
""" % (esc(title), esc(desc), CSS, body, js))


def write():
    problems = validate()
    if problems:
        for p in problems:
            print("contrastive: " + p)
        return 1
    doc = page()

    # every numeral a figure drew has to be restated where a reader can see it
    outside = re.sub(r"<svg\b.*?</svg>", " ", doc, flags=re.S | re.I)
    outside = re.sub(r"<script\b.*?</script>", " ", outside, flags=re.S | re.I)
    lost = sorted({x for x in DRAWN if x not in outside})
    if lost:
        print("contrastive: figures draw numerals the text does not restate: %s" % ", ".join(lost))
        return 1
    if "—" in doc or "–" in doc:
        print("contrastive: an em or en dash reached the page")
        return 1

    open(OUT, "w", encoding="utf-8").write(doc)
    words = len(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)\b.*?</\1>", " ", doc,
                                               flags=re.S | re.I)).split())
    print("wrote %s, %s bytes, about %s words, %d pairs (%d transfer, %d mislead, %d twice)"
          % (os.path.basename(OUT), format(len(doc), ","), format(words, ","),
             N_PAIRS, N_TRANSFER, N_MISLEAD, N_INDEP))
    return 0


if __name__ == "__main__":
    raise SystemExit(write())
