# -*- coding: utf-8 -*-
"""Rebuild the index pages from content/pieces.json.

Content lives in content/pieces.json. Design lives here and in site.css.
This script never touches a piece's own HTML except to give it a way back
into the site, and it never touches the stylesheet. Run by the GitHub
Action on every push, so the site relists itself.
"""
import datetime, hashlib, html, json, os, re, sys

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = json.load(open(os.path.join(ROOT, "content", "pieces.json"), encoding="utf-8"))
METRICS = json.load(open(os.path.join(ROOT, "content", "metrics.json"), encoding="utf-8"))
HERE    = os.path.dirname(os.path.abspath(__file__))
STRIP   = json.load(open(os.path.join(HERE, "figures.json"), encoding="utf-8"))
OUT     = ROOT

S        = CONTENT["site"]
NAME     = S["name"]
SHORT    = S["short"]
EMAIL    = S["email"]
SITE_URL = S["url"]
BORN     = tuple(int(x) for x in S["born"].split("-"))
WPM      = 230
DOC_MIN  = 1200
TODAY    = datetime.date.today()
# The address is written once, in content/pieces.json, and everything that shows
# it derives from that. A label typed by hand is a label that survives a move:
# the footer of every page used to print the old address while linking to the
# new one, which is the single contradiction this site cannot afford.
HOST     = SITE_URL.split("//", 1)[-1].rstrip("/")

def reading_minutes(w): return max(1, round(w / WPM))

def density_label(words, apparatus):
    if words < 400: return None
    per = apparatus / words * 1000
    if per < 1.0: return "Prose"
    if per < 3.0: return "Mixed"
    return "Dense"

P = []
for i, row in enumerate(CONTENT["pieces"]):
    p = dict(row)
    m = METRICS.get(p["slug"], {"words": 0, "figures": 0, "tables": 0})
    p["words"], p["figures"], p["tables"] = m["words"], m["figures"], m["tables"]
    p["apparatus"] = m["figures"] + m["tables"]
    p["order"] = i
    p["url"] = p.get("url") or (p["slug"] + ".html")
    p["tags"] = p.get("tags") or []
    p["demo"] = p.get("demo") or ""
    for flag in ("featured", "pwa"):
        p[flag] = bool(p.get(flag))
    if p["words"] < DOC_MIN:
        p["mins"] = None; p["density"] = None
    else:
        p["mins"] = reading_minutes(p["words"])
        p["density"] = density_label(p["words"], p["apparatus"])
    p["is_doc"] = p["words"] >= DOC_MIN
    P.append(p)

TOTAL_WORDS = sum(p["words"] for p in P)
TOTAL_FIGS  = sum(p["figures"] for p in P)
TOTAL_TBLS  = sum(p["tables"] for p in P)
CHECKPOINTS = sum(METRICS.get(p["slug"], {}).get("details", 0) for p in P)
COURSES     = sorted({p["c"] for p in P if p["c"]})
N_TOOLS     = sum(1 for p in P if p["k"] == "Tool")
N_PWA       = sum(1 for p in P if p["pwa"])
N_INDEP     = sum(1 for p in P if p["surface"] == "independent")
N_COURSE    = sum(1 for p in P if p["surface"] == "course")
N_PERSONAL  = sum(1 for p in P if p["surface"] == "personal")

def esc(s): return html.escape(str(s), quote=True)

def age_on(d):
    y = d.year - BORN[0] - ((d.month, d.day) < (BORN[1], BORN[2]))
    return y
AGE = age_on(TODAY)

def kwords(n):
    return f"{n/1000:.0f}k" if n >= 1000 else str(n)

# ------------------------------------------------------------ shell ----
NAV = [("index.html","Home"),("research.html","Research"),("coursework.html","Coursework"),
       ("tools.html","Tools"),("library.html","Library"),("about.html","About")]

def head(title, desc, page, extra=""):
    CUR = ' aria-current="page"'
    nav = "\n      ".join(
        f'<a href="{u}"{CUR if u==page else ""}>{t}</a>' for u, t in NAV)
    return f"""<!DOCTYPE html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="light dark">
<meta name="author" content="{esc(NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SHORT)} — portfolio">
<meta property="og:url" content="{SITE_URL}/{'' if page=='index.html' else page}">
<meta property="og:image" content="{SITE_URL}/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(SHORT)} — portfolio">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE_URL}/og-card.png">
<link rel="canonical" href="{SITE_URL}/{'' if page=='index.html' else page}">
<link rel="preload" href="https://cdnjs.cloudflare.com/ajax/libs/inter-ui/4.1.1/variable/InterVariable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="site.css">
<link rel="stylesheet" href="figures.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%2316150f'/><text x='50' y='72' font-size='64' font-family='Helvetica,Arial' font-weight='bold' fill='%23faf9f6' text-anchor='middle'>A</text></svg>">
<script>
/* Theme before first paint, so there is no flash. Wrapped because some
   embedded contexts throw on storage access. */
(function(){{try{{var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}
document.documentElement.className+=' js';}})();
</script>{extra}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="bar">
    <a class="brand" href="index.html"><span class="mark" aria-hidden="true">A</span>{esc(SHORT)} <span class="sub">portfolio</span></a>
    <nav class="main" aria-label="Sections">
      {nav}
    </nav>
    <div class="hbtns">
      <button class="iconbtn searchbtn" type="button" id="searchbtn" aria-label="Search all work">
        <span aria-hidden="true">&#9906;</span><span class="lbl">Search</span> <kbd>/</kbd>
      </button>
      <button class="iconbtn" type="button" id="themebtn" aria-label="Switch between light and dark">&#9686;</button>
    </div>
  </div>
</header>
<main id="main">
"""

# The manifest is embedded inside a <script>, and the editor now writes the
# titles, so a title is untrusted text as far as this file is concerned. The
# only sequence that can end a script block early is "</", so it is escaped;
# "\u003c/" is the same string to a JSON parser and inert to an HTML parser.
WORKJSON = json.dumps([{"t":p["t"],"s":p["s"],"u":p["url"],"k":p["k"],"c":p["c"],"d":p["d"]} for p in P],
                      separators=(",",":")).replace("</", "<\\/")

def foot():
    return f"""</main>
<footer class="site">
  <div class="cols">
    <div>
      <h2>{esc(SHORT)}</h2>
      <p class="small" style="max-width:26rem;color:var(--ink-2)">Accounting and Financial Management, Analytics stream, University of Waterloo. {len(P)} published pieces: research, interactive tools and references, all of them running rather than described.</p>
      <p class="small"><a href="mailto:{EMAIL}" style="color:var(--accent)">{EMAIL}</a></p>
    </div>
    <div>
      <h2>Sections</h2>
      <a href="research.html">Research and writing</a>
      <a href="coursework.html">Coursework</a>
      <a href="tools.html">Interactive tools</a>
      <a href="library.html">Full library</a>
    </div>
    <div>
      <h2>This site</h2>
      <a href="about.html">About and contact</a>
      <a href="colophon.html">Colophon and method</a>
      <a href="{SITE_URL}">{HOST}</a>
    </div>
  </div>
  <div class="fine">
    <span>&copy; {TODAY.year} {esc(NAME)}</span>
    <span><b>{len(P)}</b> pieces &middot; <b>{TOTAL_WORDS:,}</b> words &middot; <b>{TOTAL_FIGS}</b> figures &middot; hand-written HTML and CSS, no framework &middot; <button id="keysbtn" type="button" class="linkbtn">keyboard</button></span>
  </div>
</footer>

<!-- Search across every piece. Progressive: every link on the site works
     without it, and the button is the same route as the keyboard. -->
<div class="cmdk" id="cmdk" hidden role="dialog" aria-modal="true" aria-label="Search all work">
  <div class="cmdk-panel">
    <input id="cmdk-input" type="text" placeholder="Search {len(P)} pieces by title, course or topic" autocomplete="off" spellcheck="false" aria-controls="cmdk-list">
    <ul class="cmdk-list" id="cmdk-list" role="listbox" aria-label="Results"></ul>
    <div class="cmdk-foot">
      <span><kbd>&#8593;</kbd><kbd>&#8595;</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span>
    </div>
  </div>
</div>

<!-- The keyboard routes, written down. A shortcut nobody can find is the
     same as one that does not exist. Opened with ? or from the footer. -->
<div class="keys" id="keysheet" hidden role="dialog" aria-modal="true" aria-labelledby="keystitle">
  <div class="keys-panel">
    <h2 id="keystitle">Keyboard</h2>
    <dl>
      <dt><kbd>/</kbd></dt><dd>Search every piece</dd>
      <dt><kbd>&#8984;</kbd><kbd>K</kbd></dt><dd>The same search</dd>
      <dt><kbd>g</kbd> <kbd>h</kbd></dt><dd>Home</dd>
      <dt><kbd>g</kbd> <kbd>r</kbd></dt><dd>Research</dd>
      <dt><kbd>g</kbd> <kbd>c</kbd></dt><dd>Coursework</dd>
      <dt><kbd>g</kbd> <kbd>t</kbd></dt><dd>Tools</dd>
      <dt><kbd>g</kbd> <kbd>l</kbd></dt><dd>Library</dd>
      <dt><kbd>g</kbd> <kbd>a</kbd></dt><dd>About</dd>
      <dt><kbd>?</kbd></dt><dd>This list</dd>
    </dl>
    <button class="close" type="button">Close</button>
  </div>
</div>
<script>
window.WORK = {WORKJSON};
</script>
<script src="site.js" defer></script>
</body>
</html>
"""

# ------------------------------------------------------ components ----
SURF_LABEL = {"independent":"Independent","course":"Coursework","personal":"Personal"}

def surf(p):
    return f'<span class="surf surf-{p["surface"]}">{SURF_LABEL[p["surface"]]}</span>'

def sig(p, with_surface=True):
    """The signature line: length, apparatus, density. Defined in the colophon."""
    bits = []
    if p["k"] == "Tool":
        bits.append('<span class="s-min">Interactive</span>')
        bits.append("installs to a phone" if p["pwa"] else "runs in the browser")
    else:
        # A page under DOC_MIN words carries no reading time: the colophon says
        # so, and printing the missing value was putting "None min" on fourteen
        # cards across the site.
        if p["mins"]:
            bits.append(f'<span class="s-min">{p["mins"]} min</span>')
        ap = []
        if p["figures"]: ap.append(f'{p["figures"]} figure' + ("s" if p["figures"] != 1 else ""))
        if p["tables"]:  ap.append(f'{p["tables"]} table' + ("s" if p["tables"] != 1 else ""))
        bits.append(", ".join(ap) if ap else "no figures")
        if p["density"]:
            bits.append(f'<span class="dens dens-{p["density"]}">{p["density"]}</span>')
    line = '<i aria-hidden="true">/</i>'.join(f'<span>{b}</span>' for b in bits)
    return f'<p class="sig">{line}{surf(p) if with_surface else ""}</p>'

def kind_chip(p):
    return f'<span class="kind kind-{p["k"].lower()}">{p["k"]}</span>'

def row(n, p):
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"])
    hay = " ".join([p["t"], p["s"], p["blurb"], " ".join(p["tags"]), p["k"], p["c"],
                    SURF_LABEL[p["surface"]]]).lower()
    # words, figures and title travel with the row so the library can be
    # reordered client-side without a second copy of the manifest
    return f"""      <li data-kind="{p['k'].lower()}" data-course="{esc(p['c'])}" data-surface="{p['surface']}" data-search="{esc(hay)}" data-words="{p['words']}" data-figs="{p['figures']}" data-title="{esc(p['t'].lower())}">
        <a class="row" href="{p['url']}">
          <span class="num tnum">{n:02d}</span>
          <span>
            <span class="title">{esc(p['t'])} <span class="sub">{esc(p['s'])}</span></span>
            <p class="blurb">{esc(p['blurb'])}</p>
            <span class="meta">{kind_chip(p)}{tags}</span>
            {sig(p)}
          </span>
          <span class="side"><span>{esc(p['d'])}</span><span class="arrow" aria-hidden="true">&#8594;</span></span>
        </a>
      </li>"""

def feature(p, delay=0):
    return f"""      <a class="feature rise" style="transition-delay:{delay}ms" href="{p['url']}">
        <span class="kindrow">{kind_chip(p)}{surf(p)}</span>
        <h3>{esc(p['t'])}</h3>
        <p>{esc(p['blurb'])}</p>
        {sig(p, with_surface=False)}
        <span class="go">Open <span class="arrow" aria-hidden="true">&#8594;</span></span>
      </a>"""


def _smallest_label(d):
    """The smallest type in a figure, in the figure's own coordinates. Read from
    whatever the figure declares; a figure that declares nothing inherits the
    browser default, which is what the specimens do."""
    txt = d.get("svg", "") + d.get("css", "")
    sizes = [float(x) for x in re.findall(r'font-size:\s*([\d.]+)px', txt)]
    sizes += [float(x) for x in re.findall(r'font-size="([\d.]+)"', txt)]
    sizes += [float(x) for x in re.findall(r'font-size:\s*([\d.]+)(?![\d.px])', txt)]
    return min(sizes) if sizes else 16.0


def strip_svg(fid):
    """Keep the artboard the figure was drawn on, widen it a little so any text
    that spills past the edge still lands inside the box, and cap the display
    width at that artboard so the type never inflates."""
    d = STRIP[fid]
    svg = d["svg"]
    x, y, w, h = d["vb"]
    px, py = w * 0.05, h * 0.05
    svg = re.sub(r'viewBox="[^"]*"',
                 f'viewBox="{x - px:.0f} {y - py:.0f} {w + px * 2:.0f} {h + py * 2:.0f}"',
                 svg, count=1)
    svg = re.sub(r'\s(width|height)="[\d.]+"', "", svg, count=2)
    # Floor as well as ceiling. Capped alone, the figure still shrank to fit a
    # phone and its labels went with it: 10.5 units of type at 0.59 scale is
    # 6.2px on screen. The floor is the smallest width at which the smallest
    # label in this particular figure still lands at 10.5px, so the frame
    # scrolls sideways rather than shrinking the type below legibility.
    art  = w * 1.10
    floor = min(art, art * (10.5 / _smallest_label(d)))
    svg = svg.replace("<svg ", f'<svg style="max-width:{art:.0f}px;min-width:{floor:.0f}px" ', 1)
    return svg

def lifted(fid, rule, title, note, href):
    """A figure lifted out of its own document together with the CSS rules its
    classes depend on, shown at the size it was drawn for."""
    d = STRIP[fid]
    return f"""    <figure class="spec rise" id="{fid}">
      <div class="frame">{strip_svg(fid)}</div>
      <figcaption>
        <div class="who">
          <p class="rule">{esc(rule)}</p>
          <h3>{esc(title)}</h3>
        </div>
        <div class="what">
          <p>{esc(note)}</p>
          <a class="open" href="{href}">Open the piece <span aria-hidden="true">&#8594;</span></a>
        </div>
      </figcaption>
    </figure>"""

def strip_css():
    """Each lifted figure carries its own colour variables and the class rules
    its marks depend on. Both are scoped to the figure's id so nothing leaks."""
    out = []
    for fid, d in STRIP.items():
        if d.get("css"):
            out.append(d["css"])
    for fid, d in STRIP.items():
        if d["light"]:
            out.append("#" + fid + "{" + ";".join(f"{k}:{v}" for k, v in d["light"].items()) + "}")
    for fid, d in STRIP.items():
        if d["dark"]:
            body = ";".join(f"{k}:{v}" for k, v in d["dark"].items())
            out.append("@media (prefers-color-scheme:dark){:root:where(:not([data-theme=\"light\"])) #"
                       + fid + "{" + body + "}}")
            out.append(":root[data-theme=\"dark\"] #" + fid + "{" + body + "}")
    return "\n".join(out)
REFIT = json.load(open(os.path.join(HERE, "refit.json"), encoding="utf-8"))
SPECS = json.load(open(os.path.join(HERE, "specimens.json"), encoding="utf-8"))

def fit(sid):
    """The source pages let figure text spill past its artboard, and a
    substituted font spills further than the measured box. The viewBox is
    refitted to the measured ink with slack on both sides, and the figure is
    capped at its own natural size so it is never blown up past the type size
    it was drawn for."""
    svg = SPECS[sid]["svg"]
    r = REFIT[sid]
    w0, h0 = r["x1"] - r["x0"], r["y1"] - r["y0"]
    x0 = r["x0"] - w0 * 0.08
    y0 = r["y0"] - h0 * 0.03
    w  = w0 * 1.20
    h  = h0 * 1.08
    svg = re.sub(r'viewBox="[^"]*"', f'viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}"', svg, count=1)
    svg = re.sub(r'\s(width|height)="[\d.]+"', "", svg, count=2)
    floor = min(w, w * (10.5 / _smallest_label(SPECS[sid])))
    svg = svg.replace("<svg ",
                      f'<svg style="max-width:{w:.0f}px;min-width:{floor:.0f}px" ', 1)
    return svg


"""The corpus figure. Static SVG, generated at build time, so it renders
with JavaScript disabled and prints. Geometry is computed here rather than
hand-written, which is what keeps labels from colliding."""
import html


UNIT   = 500      # words per square. Declared once, never rescaled.
CELL   = 8.0
PITCH  = 10.0     # 8px cell + 2px surface gap, per the mark spec
ROW    = 17.0
LABW   = 196.0
GAPW   = 8.0
NUMW   = 62.0

GROUPS = [
    ("independent", "Independent", "Chosen, scoped and finished without a course asking for it."),
    ("personal",    "Personal interest", "Read for its own sake."),
    ("course",      "Coursework", "Built while taking the course, for the exam that was coming."),
]



def corpus_svg():
    docs = [p for p in P if p["is_doc"]]
    widest = max(p["words"] for p in docs) / UNIT
    plotw  = widest * PITCH
    x0     = LABW + GAPW
    rows, y = [], 0.0
    for key, title, note in GROUPS:
        items = sorted([p for p in docs if p["surface"] == key],
                       key=lambda p: -p["words"])
        if not items: continue
        rows.append(("head", title, note, y)); y += 24.0
        for p in items:
            rows.append(("row", p, key, y)); y += ROW
        y += 10.0
    h = y + 4.0
    w = x0 + plotw + GAPW + NUMW

    out = [f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="100%" role="img" '
           f'aria-label="Every published document drawn at one square per {UNIT} words. '
           f'Independent work is drawn solid, coursework as open outlines. '
           f'The independent block and the coursework block are close to the same size." '
           f'class="corpusfig">']
    out.append('<style>'
      '.cf-h{font:600 11px/1 InterVar,Helvetica,Arial,sans-serif;letter-spacing:.09em;'
      'text-transform:uppercase;fill:var(--ink-3)}'
      '.cf-n{font:400 11.5px/1 InterVar,Helvetica,Arial,sans-serif;fill:var(--ink-2)}'
      '.cf-t{font:500 11.5px/1 InterVar,Helvetica,Arial,sans-serif;fill:var(--ink)}'
      '.cf-v{font:400 11px/1 InterVar,Helvetica,Arial,sans-serif;fill:var(--ink-3);'
      'font-variant-numeric:tabular-nums}'
      '</style>')

    for kind, a, b, yy in rows:
        if kind == "head":
            out.append(f'<text class="cf-h" x="0" y="{yy+11:.1f}">{esc(a)}</text>')
            out.append(f'<line x1="0" y1="{yy+17:.1f}" x2="{w:.0f}" y2="{yy+17:.1f}" '
                       f'stroke="var(--rule)" stroke-width="1"/>')
            continue
        p, key = a, b
        ty = yy + ROW / 2
        label = p["t"] if len(p["t"]) <= 34 else p["t"][:32].rstrip(" ,:") + "…"
        # Each document is a link with its own name, so the figure is
        # keyboard-navigable and a screen reader reads it as a list of
        # documents rather than as one long alt text.
        out.append(
            f'<a class="cf-row" href="{p["url"]}" '
            f'data-t="{esc(p["t"])}" data-w="{p["words"]}" data-k="{esc(p["k"])}" '
            f'data-c="{esc(p["c"] or SURF_LABEL[p["surface"]])}" data-m="{p["mins"] or 0}" '
            f'data-f="{p["figures"]}" data-b="{p["tables"]}" data-s="{key}">'
            f'<title>{esc(p["t"])} &#183; {p["words"]:,} words</title>'
            f'<rect class="cf-hit" x="0" y="{yy:.1f}" width="{w:.0f}" height="{ROW:.1f}" fill="transparent"/>'
            f'<text class="cf-t" x="0" y="{ty+4:.1f}">{esc(label)}</text>')
        n_full = int(p["words"] // UNIT)
        frac   = (p["words"] % UNIT) / UNIT
        cy     = yy + (ROW - CELL) / 2
        solid  = key != "course"
        fill   = "var(--cf-2)" if key == "personal" else "var(--cf-1)"
        for i in range(n_full):
            cx = x0 + i * PITCH
            if solid:
                out.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{CELL}" height="{CELL}" fill="{fill}"/>')
            else:
                out.append(f'<rect x="{cx+0.5:.1f}" y="{cy+0.5:.1f}" width="{CELL-1}" height="{CELL-1}" '
                           f'fill="none" stroke="var(--cf-1)" stroke-width="1"/>')
        if frac > 0.06:
            cx = x0 + n_full * PITCH
            fw = CELL * frac
            if solid:
                out.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{fw:.1f}" height="{CELL}" fill="{fill}"/>')
            else:
                out.append(f'<rect x="{cx+0.5:.1f}" y="{cy+0.5:.1f}" width="{max(fw-1,1):.1f}" height="{CELL-1}" '
                           f'fill="none" stroke="var(--cf-1)" stroke-width="1"/>')
        out.append(f'<text class="cf-v" x="{w:.0f}" y="{ty+4:.1f}" text-anchor="end">'
                   f'{p["words"]:,}</text>')
        out.append('</a>')
    out.append('</svg>')
    return "\n".join(out)

def corpus_table():
    docs = [p for p in P if p["is_doc"]]
    rows = []
    for key, title, _ in GROUPS:
        items = sorted([p for p in docs if p["surface"] == key], key=lambda p: -p["words"])
        if not items: continue
        sub = sum(p["words"] for p in items)
        rows.append(f'<tr class="grp"><th scope="rowgroup" colspan="2">{esc(title)}</th>'
                    f'<td class="tnum">{sub:,}</td></tr>')
        for p in items:
            rows.append(f'<tr><td><a href="{p["url"]}">{esc(p["t"])}</a></td>'
                        f'<td>{esc(p["k"])}{" &middot; " + esc(p["c"]) if p["c"] else ""}</td>'
                        f'<td class="tnum">{p["words"]:,}</td></tr>')
    return ('<table class="ctab"><caption>Every document, with the word count each square is drawn from. '
            'Interactive tools are not drawn: their content is held in code rather than prose.</caption>'
            '<thead><tr><th scope="col">Piece</th><th scope="col">Kind</th>'
            '<th scope="col" class="tnum">Words</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table>')

def group_totals():
    docs = [p for p in P if p["is_doc"]]
    return {k: sum(p["words"] for p in docs if p["surface"] == k) for k, _, _ in GROUPS}


class _FigsShim:
    UNIT = UNIT
    corpus_svg = staticmethod(corpus_svg)
    corpus_table = staticmethod(corpus_table)
    group_totals = staticmethod(group_totals)
figs = _FigsShim()

# ------------------------------------------------------------ pages ----
def page_index():
    recent = [p for p in P if p["surface"] != "personal"][:4]
    feats  = [p for p in P if p["featured"]][:6]
    gt = figs.group_totals()
    indep_share = round(gt["independent"] / (gt["independent"] + gt["course"] + gt["personal"]) * 100)

    rail = "".join(f"""      <a href="{p['url']}">
        <div class="rt">{esc(p['t'])}</div>
        <div class="rm">{kind_chip(p)}{'<span class="pwa" title="Installs to a phone home screen">Installable</span>' if p['pwa'] else ''}<span>{esc(p['d'])}</span></div>
      </a>""" for p in recent)

    body = f"""<div class="hero shell">
  <div class="hero-grid">
    <div>
      <p class="eyebrow accent rise">Portfolio &middot; Waterloo AFM Analytics</p>
      <h1 class="display rise" style="transition-delay:60ms">I make arguments you can <em>audit</em>.</h1>
      <p class="lede rise" style="transition-delay:120ms">
        I am Alex Rajcoomar, <span data-age="{BORN[0]}-{BORN[1]:02d}-{BORN[2]:02d}">{AGE}</span>, an Accounting
        and Financial Management student in the Analytics stream at the University of Waterloo.
        Everything here is something I built and use. In the research, every figure carries the
        source it came from, derived numbers are labelled as derived, and where two sources
        disagree both are shown rather than averaged. Nothing is a screenshot: every item opens
        and runs.
      </p>
      <div class="stats rise" style="transition-delay:180ms">
        <div><b class="tnum">{len(P)}</b><span>published pieces</span></div>
        <div><b class="tnum">{kwords(TOTAL_WORDS)}</b><span>words, {TOTAL_FIGS} figures</span></div>
        <div><b class="tnum">{TOTAL_TBLS}</b><span>tables, {CHECKPOINTS} checkpoint questions</span></div>
        <div><b class="tnum">{N_TOOLS}</b><span>interactive tools, {N_PWA} installable</span></div>
      </div>
    </div>
    <aside class="rail rise" style="transition-delay:240ms" aria-label="Most recent work">
      <div class="railhead"><span class="dot" aria-hidden="true"></span>Most recent</div>
{rail}
      <a class="allwork" href="library.html">All {len(P)} pieces <span aria-hidden="true">&#8594;</span></a>
    </aside>
  </div>
</div>

<section class="band shell">
  <div class="sechead">
    <h2>Three marks, three rules</h2>
    <p class="note">Each piece declares one rule for what its marks mean, states it once near the top,
    and then holds it for the whole document. These three figures are lifted unchanged out of the
    pieces they belong to, colour rules and all. A fourth rule sits further down this page: the corpus
    figure borrows the fixed unit from <a href="global-spending-and-wealth.html">Global Spending and
    Wealth</a>, where one square is one trillion dollars and never rescales.</p>
    <span class="count">3 of {TOTAL_FIGS}</span>
  </div>
  <div class="specs">
{lifted("fs-wlc", "Blue is inside the number, red is outside",
        "Whose Losses Count",
        "Seven literatures making the same boundary decision, drawn on one vertical rule. Whatever falls to the right of it is real and appears on no ledger. Open outlines are results not distinguishable from zero, drawn at full size rather than shrunk away.",
        "whose-losses-count.html")}
{lifted("fs-ns1", "Solid reaches a ledger, open does not",
        "Not Significant",
        "Deceive an investor and the market takes 7.53 times what the law does. Injure a stranger who does not trade with you and the share price moves 0.24 per cent, which is not significant. The essay is built on that gap.",
        "not-significant.html")}
{lifted("fs-tv1", "The fork is never closed",
        "The Trillion-Dollar Vintage",
        "Two ways of pricing the same vintage, 2.3 times apart, carried side by side to the end rather than averaged. The refused marker between them is the point: no instrument measured that value, so nothing is drawn there.",
        "the-trillion-dollar-vintage.html")}
  </div>
</section>

<section class="band shell">
  <div class="sechead">
    <h2>And one that failed</h2>
    <p class="note">The three above are the grammar. This is what happened when the same method was
    turned on itself: the instrument was run against the falsification test it had specified for
    itself before it knew the answer, and it did not pass. The figure is the reason the headline
    finding is published in its narrow form.</p>
    <span class="count">Method</span>
  </div>
  <div class="specs">
{lifted("fs-ph1", "An interval that overlaps is not a difference",
        "Predictive History",
        "The obvious reading is that writing a verdict rubric lifted agreement from 53 per cent to 96. "
        "It did not. Only the second and third rows hold the record constant, and between those two "
        "the rubric is worth four points with the intervals overlapping. The other forty-three points "
        "are the record and the number of raters, which is a different claim entirely.",
        "predictive-history.html")}
  </div>
</section>

<section class="band shell" id="corpus">
  <div class="sechead">
    <h2>The corpus, drawn to scale</h2>
    <p class="note">Every document on this site, measured from the files themselves rather than estimated.</p>
    <span class="count">{TOTAL_WORDS:,} words</span>
  </div>
  <div class="corpus">
    <div class="plot rise">
      {figs.corpus_svg()}
    </div>
    <aside class="rail-app">
      <h3>How to read it</h3>
      <p><b>One square is {figs.UNIT} words.</b> The square never rescales, so a long piece is
      long on the page.</p>
      <!-- Populated on hover or keyboard focus of a row in the figure. It sits
           in the flow with a resting state, so the rail does not jump when the
           reader's pointer enters the drawing, and it is a live region so the
           readout is announced rather than only seen. -->
      <div class="cf-read" id="corpusread" aria-live="polite">
        <div class="cf-rest">Point at a row, or tab into the drawing, to read the document it belongs to.</div>
        <div class="cf-out" hidden>
          <b class="cf-name"></b>
          <span class="cf-meta"></span>
          <span class="cf-bar" aria-hidden="true"><i></i></span>
          <span class="cf-share"></span>
        </div>
      </div>
      <div class="key">
        <span><i aria-hidden="true"></i>Solid: independent work</span>
        <span><i class="half" aria-hidden="true"></i>Solid, lighter: personal interest</span>
        <span><i class="open" aria-hidden="true"></i>Open outline: coursework</span>
      </div>
      <p>{gt['course']:,} words were written for a course, most of it one course rebuilt end to
      end. {gt['independent']:,} were written because I wanted the answer and nobody asked for
      them. The two blocks are not the same size, and the drawing says so rather than the
      caption.</p>
      <p>Four of the drill engines are not drawn: they render a few hundred words and hold the
      rest in code, so a word count would understate them badly. They are counted on the
      <a href="tools.html" style="color:var(--accent)">tools page</a> instead.</p>
      <p><a href="colophon.html" style="color:var(--accent)">How every number here is measured &#8594;</a></p>
    </aside>
  </div>
  <details class="tv" style="margin-top:1rem">
    <summary>The numbers behind the figure</summary>
    {figs.corpus_table()}
  </details>
</section>

<section class="band shell">
  <div class="sechead">
    <h2>Start here</h2>
    <p class="note">The three sections, and what is in each. If you have ten minutes, open the first piece under research.</p>
    <span class="count">3 sections</span>
  </div>
  <div class="features">
      <a class="feature rise" href="research.html">
        <span class="kindrow"><span class="kind">Research and writing</span></span>
        <h3>Independent research</h3>
        <p>Four data essays and a study edition, each with its own declared rule for what its marks mean, plus the method pieces on how the work gets built and audited.</p>
        <span class="go">{N_INDEP} pieces <span class="arrow" aria-hidden="true">&#8594;</span></span>
      </a>      <a class="feature rise" href="tools.html">
        <span class="kindrow"><span class="kind">Interactive tools</span></span>
        <h3>{N_TOOLS} things you can use</h3>
        <p>Interactive trainers and daily instruments. {N_PWA} of them install to a phone home screen.</p>
        <span class="go">{N_TOOLS} pieces <span class="arrow" aria-hidden="true">&#8594;</span></span>
      </a>      <a class="feature rise" href="coursework.html">
        <span class="kindrow"><span class="kind">Coursework</span></span>
        <h3>Grouped by course</h3>
        <p>Every reference and trainer, sorted into the {len(COURSES)} courses they were built for, with a coverage table.</p>
        <span class="go">{N_COURSE} pieces <span class="arrow" aria-hidden="true">&#8594;</span></span>
      </a>
  </div>
</section>

<section class="band shell">
  <div class="sechead">
    <h2>Selected work</h2>
    <p class="note">Chosen because together they show the widest range: a study edition, an audited final, a negative result, a comparative primer, and the tools people actually use.</p>
    <span class="count">{len(feats)} of {len(P)}</span>
  </div>
  <div class="features">
{chr(10).join(feature(p, n*45) for n, p in enumerate(feats))}
  </div>
</section>

<section class="band shell" id="note">
  <div class="sechead"><h2>A note on the material</h2><span class="count">Please read</span></div>
  <div class="prose measure">
    <p>These are my own artefacts, written by me for my own use. They are not course materials,
    not official solutions, and not a substitute for the standards themselves. Where a figure or a
    rule matters, check the primary source: the CPA Canada Handbook, the Income Tax Act, or the CRA.</p>
  </div>
</section>
"""
    return head(f"{SHORT} — portfolio",
                f"Research, interactive study tools and references built by Alex Rajcoomar, "
                f"Accounting and Financial Management student at the University of Waterloo. "
                f"{len(P)} published pieces, {TOTAL_WORDS:,} words, all of them running.",
                "index.html", extra="\n" + jsonld_site()) + body + foot()

# The specimen figure shown beside the lead belongs to one particular piece,
# so it is registered against that piece rather than against the slot. Adding
# a new piece at the top of the list used to move the slot without moving the
# figure, which left a caption describing a chart from a different document.
SPECIMEN_OF = {"the-trillion-dollar-vintage": (
    "spec-vintage",
    "Figure lifted from the piece. One vintage on two bases: 1,082 billion dollars as "
    "first reported, 990 billion after an attribution correction the page makes in "
    "public. The fork stays open.")}

def page_research():
    items = [p for p in P if p["surface"] == "independent"]
    # the largest, not the first: the note beside this slot says "the largest
    # thing here", and a positional lead makes that sentence false the moment
    # anything is published above it
    lead = max(items, key=lambda x: x["words"])
    rest = [x for x in items if x is not lead]
    gt = figs.group_totals()

    spec = SPECIMEN_OF.get(lead["slug"])
    leadfig = ""
    if spec:
        leadfig = (f'<div id="{spec[0]}">\n'
                   f'      <div class="fig">{fit(spec[0])}</div>\n'
                   f'      <p class="figcap">{esc(spec[1])}</p>\n'
                   f'    </div>')

    blocks = []
    for p in rest:
        demo = (f'<div class="demo"><b>What it demonstrates</b>{esc(p["demo"])}</div>'
                if p["demo"] else "")
        blocks.append(f"""    <article class="lead rise" style="border-top:1px solid var(--rule);padding-top:var(--gap)">
      <div class="lt">
        <span class="kindrow">{kind_chip(p)}<span class="tnum" style="color:var(--ink-3);font-size:.8125rem">{esc(p['d'])}</span></span>
        <h3><a href="{p['url']}">{esc(p['t'])}</a></h3>
        <p class="sub">{esc(p['s'])}</p>
        <p class="blurb">{esc(p['blurb'])}</p>
        {sig(p, with_surface=False)}
      </div>
      <div>{demo}<a class="open" style="font-size:.875rem;font-weight:560;color:var(--accent);text-decoration:none" href="{p['url']}">Open the piece <span aria-hidden="true">&#8594;</span></a></div>
    </article>""")

    body = f"""<div class="hero shell" style="padding-block:clamp(2.5rem,5vw,4rem) 1rem">
  <p class="eyebrow accent">Section 01</p>
  <h1 class="h1">Research and writing</h1>
  <p class="lede">{len(items)} pieces where the argument is the point. Every one of them started because
  I did not believe a claim, or could not find two jurisdictions held apart properly, and the fastest
  way to find out was to build the thing. {gt['independent']:,} words, none of them assigned.</p>
  <div class="stats" style="margin-top:2rem">
    <div><b class="tnum">{len(items)}</b><span>independent pieces</span></div>
    <div><b class="tnum">{gt['independent']:,}</b><span>words</span></div>
    <div><b class="tnum">{sum(p['figures'] for p in items)}</b><span>figures, hand-built</span></div>
    <div><b class="tnum">{sum(p['tables'] for p in items)}</b><span>tables of underlying numbers</span></div>
  </div>
</div>

<section class="band shell">
  <div class="sechead">
    <h2>The lead piece</h2>
    <p class="note">The largest thing here, and the one that shows the method at full size.</p>
    <span class="count">{str(lead['mins']) + ' min' if lead['mins'] else esc(lead['k'])}</span>
  </div>
  <article class="lead">
    <div class="lt">
      <span class="kindrow">{kind_chip(lead)}{surf(lead)}<span style="color:var(--ink-3);font-size:.8125rem">{esc(lead['d'])}</span></span>
      <h3><a href="{lead['url']}">{esc(lead['t'])}</a></h3>
      <p class="sub">{esc(lead['s'])}</p>
      <p class="blurb">{esc(lead['blurb'])}</p>
      <div class="demo"><b>What it demonstrates</b>{esc(lead['demo'])}</div>
      {sig(lead, with_surface=False)}
      <a class="open" style="font-size:.9375rem;font-weight:600;color:var(--accent);text-decoration:none" href="{lead['url']}">Open the study edition <span aria-hidden="true">&#8594;</span></a>
    </div>
    {leadfig}
  </article>
</section>

<section class="band shell">
  <div class="sechead">
    <h2>The rest</h2>
    <p class="note">Newest first. Each opens as a self-contained page.</p>
    <span class="count">{len(rest)} pieces</span>
  </div>
  <div style="display:grid;gap:var(--gap)">
{chr(10).join(blocks)}
  </div>
</section>

<section class="band shell">
  <div class="sechead"><h2>The rules the figures follow</h2><span class="count">Method</span></div>
  <div class="prose measure">
    <p>Each piece declares one rule for what its marks mean, states it once near the top, and then
    holds it for the whole document. The rule is derived from what that particular research is about,
    so no two pieces share one.</p>
    <ul>
      <li><strong>Global Spending and Wealth:</strong> one square is one trillion US dollars, declared once and never rescaled.</li>
      <li><strong>Not Significant:</strong> solid marks are quantities that reach someone's books; open outlines at full size are quantities that are real and appear on no invoice.</li>
      <li><strong>The Trillion-Dollar Vintage:</strong> the fork between the two anchors is never closed, and a mark that arithmetic produced rather than an instrument measured is drawn open.</li>
      <li><strong>Whose Losses Count:</strong> blue is inside the accounting boundary and priced, red is outside it.</li>
    </ul>
    <p>The same discipline runs through this site: the corpus figure on the
    <a href="index.html#corpus">home page</a> declares its own unit, and the
    <a href="colophon.html">colophon</a> states how every number on the site is measured.</p>
  </div>
</section>
"""
    return head(f"Research and writing — {SHORT}",
                f"{len(items)} independent research pieces by Alex Rajcoomar: data essays, a study edition "
                f"and an audited final, {gt['independent']:,} words, every figure carrying its source.",
                "research.html") + body + foot()

def page_tools():
    items = [p for p in P if p["k"] == "Tool"]
    body = f"""<div class="hero shell" style="padding-block:clamp(2.5rem,5vw,4rem) 1rem">
  <p class="eyebrow accent">Section 03</p>
  <h1 class="h1">Interactive tools</h1>
  <p class="lede">{len(items)} things you use rather than read. {N_PWA} of them install to a phone home
  screen. Four are drill engines that hold their question banks in code, so they carry no reading
  time: a drill has no length, only a session. The other two render a full document on load and are
  measured like one.</p>
</div>
<section class="band shell">
  <div class="sechead"><h2>All {len(items)}</h2><p class="note">Each opens and runs in the browser. Nothing to install unless you want the home-screen icon.</p><span class="count">{len(items)} tools</span></div>
  <div class="features">
{chr(10).join(feature(p, n*45) for n, p in enumerate(items))}
  </div>
</section>
<section class="band shell">
  <div class="sechead"><h2>Installing one</h2><span class="count">How to</span></div>
  <div class="prose measure">
    <p>On a phone, open the tool and choose <em>Add to Home Screen</em> from the share menu. It gets an
    icon and opens without browser chrome. Progress is stored in that browser only: nothing is
    uploaded, and clearing site data clears the progress with it.</p>
  </div>
</section>
"""
    return head(f"Interactive tools — {SHORT}",
                f"{len(items)} interactive study tools built by Alex Rajcoomar, {N_PWA} of them installable to a phone home screen.",
                "tools.html") + body + foot()

def page_coursework():
    items = [p for p in P if p["surface"] == "course"]
    rows_c = []
    for c in COURSES:
        cs = [p for p in items if p["c"] == c]
        it = sum(1 for p in cs if p["k"] == "Tool")
        rf = len(cs) - it
        w  = sum(p["words"] for p in cs)
        rows_c.append(f'<tr><th scope="row">{esc(c)}</th><td class="tnum">{it or "&middot;"}</td>'
                      f'<td class="tnum">{rf or "&middot;"}</td><td class="tnum">{len(cs)}</td>'
                      f'<td class="tnum">{w:,}</td></tr>')
    tot_w = sum(p["words"] for p in items)
    tot_i = sum(1 for p in items if p["k"] == "Tool")
    rows_c.append(f'<tr class="grp"><th scope="row">All courses</th><td class="tnum">{tot_i}</td>'
                  f'<td class="tnum">{len(items)-tot_i}</td><td class="tnum">{len(items)}</td>'
                  f'<td class="tnum">{tot_w:,}</td></tr>')

    groups = []
    for c in COURSES:
        cs = sorted([p for p in items if p["c"] == c], key=lambda p: (p["k"] != "Tool", -p["words"]))
        groups.append(f"""  <div class="grouphead"><h3>{esc(c)}</h3>
    <p class="gnote">{len(cs)} piece{'s' if len(cs)!=1 else ''}, {sum(p['words'] for p in cs):,} words.</p>
    <span class="gcount">{len(cs)}</span></div>
  <div class="features">
{chr(10).join(feature(p) for p in cs)}
  </div>""")

    body = f"""<div class="hero shell" style="padding-block:clamp(2.5rem,5vw,4rem) 1rem">
  <p class="eyebrow accent">Section 02</p>
  <h1 class="h1">Coursework</h1>
  <p class="lede">{len(items)} pieces across {len(COURSES)} courses, each one built while taking the course
  rather than afterwards. References are organised for retrieval under time pressure, not for reading
  front to back, which is why several of them are deliberately compressed to what fits on a page.</p>
</div>

<section class="band shell">
  <div class="sechead"><h2>Coverage</h2><p class="note">What exists per course, counted from the files themselves.</p><span class="count">{len(items)} of {len(P)}</span></div>
  <p class="note measure" style="margin-bottom:1rem">Word counts exclude the question banks inside the interactive
  tools, because those live in code rather than prose, so the tool-heavy courses read lower than they are.
  The remaining {len(P)-len(items)} pieces are not tied to one course: {N_INDEP} under
  <a href="research.html" style="color:var(--accent)">research</a> and the {N_PERSONAL} read for
  their own sake in the <a href="library.html" style="color:var(--accent)">library</a>.</p>
  <div class="tw"><table class="ctab">
    <thead><tr><th scope="col">Course</th><th scope="col" class="tnum">Interactive</th>
    <th scope="col" class="tnum">References</th><th scope="col" class="tnum">Total</th>
    <th scope="col" class="tnum">Words</th></tr></thead>
    <tbody>{''.join(rows_c)}</tbody>
  </table></div>
</section>

<section class="band shell">
  <div class="sechead"><h2>By course</h2><p class="note">Tools first, then references, longest first.</p><span class="count">{len(COURSES)} courses</span></div>
{chr(10).join(groups)}
</section>
"""
    return head(f"Coursework — {SHORT}",
                f"{len(items)} references and trainers across {len(COURSES)} courses, with a coverage table counted from the files.",
                "coursework.html") + body + foot()

def page_library():
    order = ["independent", "course", "personal"]
    notes = {
      "independent": "Chosen, scoped and finished without a course asking for it.",
      "course": "Built while taking the course, for the assessment that was coming.",
      "personal": "Read and written for its own sake.",
    }
    n = 0; blocks = []
    for key in order:
        items = [p for p in P if p["surface"] == key]
        if not items: continue
        w = sum(p["words"] for p in items)
        rows = []
        for p in items:
            n += 1
            rows.append(row(n, p))
        blocks.append(f"""  <section class="lgroup" data-group="{key}">
    <div class="grouphead"><h2>{SURF_LABEL[key]}</h2>
      <p class="gnote">{esc(notes[key])}</p>
      <span class="gcount">{len(items)} pieces &middot; {w:,} words</span></div>
    <ol class="index">
{chr(10).join(rows)}
    </ol>
  </section>""")

    body = f"""<div class="hero shell" style="padding-block:clamp(2.5rem,5vw,4rem) 1rem">
  <p class="eyebrow accent">Library</p>
  <h1 class="h1">Everything, in one place.</h1>
  <p class="lede">All {len(P)} pieces, split by what asked for them. Every item carries how long it takes
  to read, how much apparatus it holds, and how dense that makes it. The
  <a href="colophon.html">colophon</a> gives the definitions.</p>
</div>
<section class="shell" style="padding-bottom:4rem">
  <div class="tools-bar">
    <label class="sr" for="q">Search the library</label>
    <input id="q" type="search" placeholder="Search {len(P)} pieces" autocomplete="off" spellcheck="false">
    <div class="chipset" id="chips" role="group" aria-label="Filter by kind">
      <button class="chip" type="button" data-f="all" aria-pressed="true">All</button>
      <button class="chip" type="button" data-f="essay" aria-pressed="false">Essays</button>
      <button class="chip" type="button" data-f="tool" aria-pressed="false">Tools</button>
      <button class="chip" type="button" data-f="reference" aria-pressed="false">References</button>
    </div>
    <div class="sortset">
      <label class="sr" for="sort">Order</label>
      <select id="sort">
        <option value="default">Grouped, as published</option>
        <option value="long">Longest first</option>
        <option value="short">Shortest first</option>
        <option value="figs">Most figures</option>
        <option value="az">A to Z</option>
      </select>
    </div>
  </div>
  <p class="resultnote" id="resultnote" role="status">Showing all {len(P)} pieces.</p>
{chr(10).join(blocks)}
  <p class="resultnote" id="noresults" hidden>Nothing matches that. Try a shorter word, or a course code.</p>
</section>
"""
    return head(f"Library — {SHORT}",
                f"All {len(P)} pieces by Alex Rajcoomar, split into independent work and coursework, with reading time and density on each.",
                "library.html") + body + foot()

def page_about():
    gt = figs.group_totals()
    indep_share = round(gt["independent"] / (gt["independent"] + gt["course"] + gt["personal"]) * 100)
    body = f"""<div class="hero shell" style="padding-block:clamp(2.5rem,5vw,4rem) 1rem">
  <p class="eyebrow accent">About</p>
  <div class="namerow">
    <h1 class="h1">{esc(NAME)}</h1>
    <div class="affil" role="img" aria-label="University of Waterloo, School of Accounting and Finance">
      <span class="affil-bar" aria-hidden="true"></span>
      <span class="affil-txt">
        <b>University of Waterloo</b>
        <span>School of Accounting and Finance</span>
      </span>
    </div>
  </div>
  <p class="lede">Alex, <span data-age="{BORN[0]}-{BORN[1]:02d}-{BORN[2]:02d}">{AGE}</span>, an Accounting
  and Financial Management student in the Analytics stream at the University of Waterloo. I build the
  thing I need, then leave it running here.</p>
</div>

<section class="band shell">
  <div class="sechead"><h2>The short version</h2><span class="count">Facts</span></div>
  <div class="facts measure" style="max-width:46rem">
    <div><b>Programme</b><span>Accounting and Financial Management, Analytics stream, University of Waterloo.</span></div>
    <div><b>Co-op</b><span>Preparing Canadian corporate and personal tax returns.</span></div>
    <div><b>Focus</b><span>Financial reporting under IFRS and ASPE, Canadian tax, and the analytics side of accounting.</span></div>
    <div><b>Standing interests</b><span>The science of learning, judgment under uncertainty, and capital cycles. Outside coursework, AI in medicine and commercial spaceflight.</span></div>
    <div><b>Contact</b><span><a href="mailto:{EMAIL}" style="color:var(--accent)">{EMAIL}</a></span></div>
    <div><b>This site</b><span><a href="{SITE_URL}" style="color:var(--accent)">{HOST}</a></span></div>
  </div>
</section>

<section class="band shell">
  <div class="sechead">
    <h2>What this portfolio demonstrates</h2>
    <p class="note">The work is study material and independent research, so here is the translation:
    what building {len(P)} pieces of it actually required.</p>
    <span class="count">Four things</span>
  </div>
  <div class="caps">
    <div><h3>Evidence discipline</h3><p>Every figure carries the provenance tag it was published under.
    Derived numbers are labelled as derived. Two sources that disagree are reported separately instead of
    averaged. One essay reaches a negative result and reports it as one, and the largest piece corrects its
    own arithmetic in public where a later attribution changed the base.</p></div>
    <div><h3>Financial reporting</h3><p>Intermediate financial accounting under IFRS, worked to the entry
    rather than the summary: revenue recognition through the five-step model, a journal entry reference
    built for retrieval under time pressure, and a coverage audit that records what is still missing.</p></div>
    <div><h3>Canadian tax and law, kept Canadian</h3><p>Co-op work preparing Canadian corporate and personal
    returns, and a primer that holds the Canadian and American legal positions apart at every point they
    diverge instead of blending them.</p></div>
    <div><h3>Building the thing</h3><p>Hand-written HTML, CSS and JavaScript across {len(P)} pages and
    {N_TOOLS} interactive tools, {N_PWA} of them installable. {TOTAL_FIGS} figures, all built by hand as
    static SVG so they render with JavaScript off. No framework, no build step on the reader's side,
    accessible in light and dark, and it prints.</p></div>
  </div>
</section>

<section class="band shell">
  <div class="sechead"><h2>Why the site exists</h2><span class="count">Rationale</span></div>
  <div class="prose measure">
    <p>Most of what I build starts as a problem I have: a course that will not stay in my head, a claim
    I do not believe, a process I keep repeating by hand. The output is usually an interactive
    document, because a diagram you can interrogate beats a paragraph you can skim. Rather than let
    those sit in a downloads folder, they live here, running, where anyone can use them.</p>

    <p>Two things are worth separating. One course, AFM 291, has been rebuilt here end to end:
    eleven documents, {gt['course']:,} words, every chapter running the same structure so a topic
    can be found the same way twice. Alongside it sits {gt['independent']:,} words of research
    nobody assigned. The corpus figure on the <a href="index.html#corpus">home page</a> draws that
    split rather than claiming it.</p>

    <h2>How the work is organised</h2>
    <ul>
      <li><strong>Research and writing</strong> holds the pieces where the argument is the point, plus
      the method work on how the rest gets built and audited.</li>
      <li><strong>Coursework</strong> groups every reference and trainer by the course it was built
      for, with a coverage table showing what exists and what does not.</li>
      <li><strong>Interactive tools</strong> are the things you use rather than read. {N_PWA} install to a
      phone home screen.</li>
    </ul>

    <h2>A note on the material</h2>
    <p>These are my own artefacts, written by me for my own use. They are not course materials,
    not official solutions, and not a substitute for the standards themselves. Where a figure or a
    rule matters, check the primary source: the CPA Canada Handbook, the Income Tax Act, or the CRA.</p>

    <p><a href="colophon.html">How this site is built, and how every number on it is measured &#8594;</a></p>
  </div>
</section>
"""
    return head(f"About — {SHORT}",
                "Alex Rajcoomar, Accounting and Financial Management student in the Analytics stream at the University of Waterloo.",
                "about.html", extra="\n" + jsonld_person()) + body + foot()

def page_colophon():
    gt = figs.group_totals()
    body = f"""<div class="hero shell" style="padding-block:clamp(2.5rem,5vw,4rem) 1rem">
  <p class="eyebrow accent">Colophon</p>
  <h1 class="h1">How this site is built, and how it counts.</h1>
  <p class="lede">Every number on this site is measured from the published files rather than estimated.
  This page states each definition, so a reader can disagree with one.</p>
</div>

<section class="band shell colo">
  <div class="sechead"><h2>The measurements</h2><span class="count">Definitions</span></div>
  <div class="prose measure">
    <dl>
      <dt>Words</dt>
      <dd>The text a reader can select, taken from the rendered document with
      <code>&lt;script&gt;</code>, <code>&lt;style&gt;</code> and <code>&lt;noscript&gt;</code> removed.
      A word is a whitespace-separated token containing at least one letter or digit. Question banks
      inside the interactive tools are held in code, so they are not counted anywhere: the tools read
      as {min(p['words'] for p in P if p['k']=='Tool')} to {max(p['words'] for p in P if p['k']=='Tool')}
      words and are genuinely much larger than that.</dd>

      <dt>Reading time</dt>
      <dd>Words divided by {WPM} words per minute, rounded, minimum one minute. {WPM} is a
      middle estimate for careful reading of technical prose; a skim is faster and a first pass through
      a figure-heavy section is slower. A page that renders under {DOC_MIN:,} words is treated as an
      instrument rather than a document and carries no reading time, because a drill has no length,
      only a session. That threshold is applied to what the page renders, not to what I would like it
      to be.</dd>

      <dt>Figures</dt>
      <dd>A top-level <code>&lt;svg&gt;</code> in the rendered page, not nested inside another one,
      covering at least 6,000 square units, which excludes inline glyphs and icons. Because the count
      runs after render it includes charts a script draws on load. Charts built purely from HTML and
      CSS are still not counted, so the number remains a floor rather than a ceiling.</dd>

      <dt>Density</dt>
      <dd>Figures plus tables per thousand words. Under 1.0 is <b>Prose</b>, 1.0 to 3.0 is
      <b>Mixed</b>, 3.0 and above is <b>Dense</b>. Documents under 400 words carry no label, because the
      ratio is unstable at that length. It is a rough signal of what the page will feel like, not a
      quality measure: a dense page is not a better page.</dd>

      <dt>Independent, coursework, personal</dt>
      <dd><b>Independent</b> means I chose the question, scoped it and finished it without a course
      asking for it. <b>Coursework</b> means it was built while taking the course, for the assessment
      that was coming. <b>Personal</b> means read and written for its own sake, with no claim on either.
      The split is mine and I have made it conservatively: anything built alongside a course is filed
      as coursework even where the question was my own.</dd>
    </dl>
  </div>
</section>

<section class="band shell colo">
  <div class="sechead"><h2>The design rules</h2><span class="count">Conventions</span></div>
  <div class="prose measure">
    <dl>
      <dt>One declared rule per piece</dt>
      <dd>Each research page states once, near the top, what its marks mean, then holds that rule to the
      end. The rule is derived from the subject, so no two pieces share one. The
      <a href="index.html#corpus">corpus figure</a> obeys the same convention: one square is
      {figs.UNIT} words, solid is independent, an open outline is coursework.</dd>

      <dt>Colour</dt>
      <dd>Chart colours come from a validated categorical palette, checked for lightness band, chroma
      floor, colour-vision separation and contrast against both the light and the dark surface before
      use. Colour never carries meaning on its own: every figure's numbers are restated in a table or in
      the running text, and every mark that means something also differs in fill or shape.</dd>

      <dt>Typography</dt>
      <dd>Inter Variable, loaded from a public CDN with a metric-matched fallback so the page does not
      reflow when the webfont lands. If the CDN fails, the site keeps working on the system stack.</dd>

      <dt>Surfaces</dt>
      <dd>Warm paper, near-black ink, hairline rules, one accent, no rounded corners, no drop shadows,
      no gradients. Dark mode is a selected set of tokens rather than an inversion, and the manual
      toggle wins over the system setting in both directions.</dd>
    </dl>
  </div>
</section>

<section class="band shell colo">
  <div class="sechead"><h2>How it is built</h2><span class="count">Technical</span></div>
  <div class="prose measure">
    <p>Hand-written HTML, CSS and JavaScript. No framework, no build step on the reader's side, no
    tracking, no cookies, no analytics. {len(P)} pieces served as static files by GitHub Pages.
    The {len(SHELL_PAGES)} pages the build generates, this one included, share one stylesheet and one
    script; each piece carries its own styling inside itself, so a change to the site's look cannot
    reach into a piece and a broken piece cannot reach the site.</p>
    <p>The listing pages are generated. Content lives in one file, <code>content/pieces.json</code>:
    every piece's title, description, tags, section and position. A script reads it and rewrites the
    listing pages, and a GitHub Action runs that script after every change. Any piece whose file
    changed is opened in a headless browser first and counted, which is where every number on this
    page comes from. Nothing here is typed in by hand, which is the only way the counts stay true.</p>
    <p>Figures are static SVG generated at build time, so every chart renders with JavaScript disabled.
    JavaScript adds only enhancements: the theme toggle, the search palette, the library filters, the
    reveal-on-scroll, and the age in the first sentence of the home page, which is computed from a date
    so the sentence does not go stale.</p>
    <p>Accessibility: skip link, visible focus, headings in order, every figure labelled, colour never
    load-bearing on its own, and reduced-motion respected. Every page prints: sticky elements release,
    revealed content is forced visible, and figures avoid breaking across pages.</p>
    <p>Six of these pages began as Word documents. Those files carry their structure in font size
    rather than in heading styles, so a second converter works out the heading levels per document
    from the sizes it finds, then carries the tables, the inline diagrams and the run-in headings
    across in document order.</p>
    <p>Sixteen more began as markdown notes and are converted to HTML at build time by a
    converter written for this site: it handles the callout syntax the notes use, turns every
    checkpoint question into a collapsed block a reader has to open, resolves internal note links to
    published pages, and carries evidence tags through as visible chips. An earlier draft of this site
    fetched the markdown in the browser instead. Converting at build time is better: the text is in
    the page, so it prints, it can be searched, it survives JavaScript being off, and it can be
    measured like everything else.</p>
    <p>The corpus as of this build: {len(P)} pieces, {TOTAL_WORDS:,} words, {TOTAL_FIGS} figures,
    {TOTAL_TBLS} tables and {CHECKPOINTS} checkpoint questions. {gt['independent']:,} of those words
    were not assigned by anyone.</p>
  </div>
</section>
"""
    return head(f"Colophon — {SHORT}",
                "How this site is built, and the exact definition behind every number on it.",
                "colophon.html") + body + foot()

# ------------------------------------------------------------- run ----

MOBILE_FIT_FULL = """
<style id="__mobile_fit">
/* Injected by the site build. These pages were laid out for letter paper and
   hold their column widths in inches, which is right for the printed sheet and
   wrong for a 390px screen: the page itself overflowed sideways, so the whole
   document rubber-banded and the header slid off. The sheet keeps its width
   and scrolls inside its own frame instead, which leaves the type at the size
   it was set and the page still. */
@media (max-width:48rem){
  html,body{max-width:100%}
  body{overflow-wrap:break-word}
  svg,img{max-width:100%;height:auto}
  /* The sheet keeps the width it was set at and scrolls inside its own frame.
     Clipping it instead would stop the page sliding, at the price of putting
     part of the document out of reach, which is the worse trade on a page
     whose content is the point. */
  body > *,.sheet,.page,.wrap,main,article{
    max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch
  }
  /* the injected return bar is the build's own furniture and already fits */
  body > #__rb,body > #__rb-pill,body > style,body > script{overflow:visible}
  table{display:block;max-width:100%;overflow-x:auto}
  /* a segmented control that clips its own buttons puts two of them out of
     reach on a phone; let the control scroll instead of hiding them */
  .seg{overflow-x:auto;max-width:100%}
}
</style>
"""

MOBILE_FIT_ART = """
<style id="__mobile_fit">
/* Injected by the site build. A long unbreakable token or a wide figure was
   pushing the page sideways on a phone; nothing else about the layout is
   touched. */
@media (max-width:48rem){
  html,body{max-width:100%}
  body{overflow-wrap:break-word}
  svg,img{max-width:100%;height:auto}
  table{display:block;max-width:100%;overflow-x:auto}
}
</style>
"""

OVERFLOWING = {
    "afm274-capital-structure.html": MOBILE_FIT_FULL,
    "afm291-field-manual.html": MOBILE_FIT_FULL,
    "afm291-journal-entries.html": MOBILE_FIT_FULL,
    "afm291-study-system.html": MOBILE_FIT_FULL,
    "econ102-visual-reference.html": MOBILE_FIT_FULL,
    "revenue-recognition.html": MOBILE_FIT_FULL,
    "global-spending-and-wealth.html": MOBILE_FIT_ART,
}

def fit_mobile(path, css):
    """Only touches pages that actually overflow; leaves the rest alone. An
    older block is replaced rather than left in place, so improving these rules
    reaches pages that already carry a previous version of them."""
    text = open(path, encoding="utf-8", errors="ignore").read()
    before = text
    text = re.sub(r'\s*<style id="__mobile_fit">.*?</style>', "", text, flags=re.S)
    i = text.lower().rfind("</head>")
    if i == -1:
        return
    text = text[:i] + css + text[i:]
    if text != before:
        open(path, "w", encoding="utf-8").write(text)


RETURN_BAR = """
<!--__rb-->
<!-- injected by the site build: a way back into the site from a standalone
     piece. A static bar at the top, so it is visible on arrival, and a pill
     that appears once you have scrolled past it, so there is always a way out.
     Self-contained, because these pages do not load the site stylesheet. -->
<style id="__rb-style">
#__rb{
  box-sizing:border-box;display:flex;flex-wrap:wrap;align-items:center;gap:.6rem 1.25rem;
  padding:.6rem clamp(1rem,4vw,2rem);border-bottom:1px solid #ddd9cf;background:#faf9f6;
  font:500 13px/1.35 InterVar,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  color:#55524a;
}
#__rb a{color:#14509b;text-decoration:none;display:inline-flex;align-items:center;gap:.4rem}
#__rb a:hover{text-decoration:underline}
#__rb .__rb-home{font-weight:640;color:#16150f}
#__rb .__rb-home i{font-style:normal;font-weight:400;color:#6f6c63}
#__rb .__rb-right{margin-left:auto;display:flex;gap:1.1rem;flex-wrap:wrap}
#__rb .__mark{
  display:inline-grid;place-items:center;width:1.2rem;height:1.2rem;flex:none;
  background:#16150f;color:#faf9f6;font-size:.72rem;font-weight:700;
}
#__rb-pill{
  position:fixed;left:14px;bottom:14px;z-index:2147483000;
  display:inline-flex;align-items:center;gap:.45rem;padding:.58rem .9rem;
  background:rgba(22,21,15,.93);color:#faf9f6;text-decoration:none;border-radius:99px;
  font:600 12.5px/1 InterVar,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  border:1px solid rgba(255,255,255,.16);box-shadow:0 6px 22px rgba(0,0,0,.28);
  opacity:0;transform:translateY(6px);pointer-events:none;
  transition:opacity .2s ease,transform .2s ease;
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
}
#__rb-pill.__on{opacity:1;transform:none;pointer-events:auto}
#__rb-pill:hover{background:#16150f;color:#fff}
/* Dark has to answer to two things: the reader's system setting, and the
   theme button on the page, which sets data-theme on <html>. Keyed to the
   media query alone, the bar stayed paper-white across the top of an essay
   the reader had just switched to dark, and read as a rendering fault. The
   media query is scoped so an explicit light choice wins, and the attribute
   selector is repeated so an explicit dark choice wins on a light system. */
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) #__rb{background:#131310;border-bottom-color:#2c2b24;color:#c0bcb1}
  :root:not([data-theme="light"]) #__rb .__rb-home{color:#f7f5ef}
  :root:not([data-theme="light"]) #__rb .__rb-home i{color:#948f85}
  :root:not([data-theme="light"]) #__rb a{color:#85adea}
  :root:not([data-theme="light"]) #__rb .__mark{background:#f7f5ef;color:#131310}
  :root:not([data-theme="light"]) #__rb-pill{background:rgba(247,245,239,.95);color:#131310;border-color:rgba(0,0,0,.2)}
  :root:not([data-theme="light"]) #__rb-pill:hover{background:#fff;color:#000}
}
:root[data-theme="dark"] #__rb{background:#131310;border-bottom-color:#2c2b24;color:#c0bcb1}
:root[data-theme="dark"] #__rb .__rb-home{color:#f7f5ef}
:root[data-theme="dark"] #__rb .__rb-home i{color:#948f85}
:root[data-theme="dark"] #__rb a{color:#85adea}
:root[data-theme="dark"] #__rb .__mark{background:#f7f5ef;color:#131310}
:root[data-theme="dark"] #__rb-pill{background:rgba(247,245,239,.95);color:#131310;border-color:rgba(0,0,0,.2)}
:root[data-theme="dark"] #__rb-pill:hover{background:#fff;color:#000}
@media (prefers-reduced-motion:reduce){#__rb-pill{transition:none}}
@media print{#__rb,#__rb-pill{display:none !important}}
</style>
<div id="__rb">
  <a class="__rb-home" href="index.html"><span class="__mark" aria-hidden="true">A</span>Alex Rajcoomar <i>portfolio</i></a>
  <span class="__rb-right"><a href="__UP__">__UPNAME__</a><a href="library.html">All work</a></span>
</div>
<!--/__rb-->
"""

RETURN_PILL = """
<!--__rbp-->
<a id="__rb-pill" href="__UP__">&#8592; __UPNAME__</a>
<script>
(function(){
  var p=document.getElementById('__rb-pill'); if(!p) return;
  var t=false;
  function run(){ t=false;
    p.classList.toggle('__on',(window.scrollY||document.documentElement.scrollTop)>420); }
  function q(){ if(!t){ t=true; requestAnimationFrame(run); } }
  addEventListener('scroll',q,{passive:true}); run();
})();
</script>
<!--/__rbp-->
"""

# Every fragment the build has ever injected into a piece page. A page is
# cleaned against all of them before a fresh bar goes in, so running the
# build twice leaves the page exactly as running it once did. Without this
# the injections stacked: the second run left a stray half-bar behind.
_SENTINEL = [
    r"\n?<!--__rb-->.*?<!--/__rb-->\n?",
    r"\n?<!--__rbp-->.*?<!--/__rbp-->\n?",
]
_INJECTED = [
    r"<!-- injected by the site build.*?-->",
    r'<style id="__rb-style">.*?</style>',
    r'<div id="__rb">.*?</div>',
    r'<span class="__rb-right">.*?</span>\s*</div>',
    r'<a id="__rb-pill"[^>]*>.*?</a>',
    r"<script>\s*\(function\(\)\{\s*var p=document\.getElementById\('__rb-pill'\).*?</script>",
]

def strip_injected(text):
    # The sentinel form is removed exactly as it was inserted, so a page that
    # has been through the build once is a fixed point: build it again and the
    # file does not change. The legacy shapes below clean pages injected by an
    # earlier version of this script, which had no sentinels.
    for pat in _SENTINEL:
        text = re.sub(pat, "", text, flags=re.S)
    for pat in _INJECTED:
        text = re.sub(pat + r"\s*", "", text, flags=re.S)
    return text


_BODY_TAG = re.compile(r"<body\b[^>]*>", re.I)

def _body_tag(text):
    """The opening body tag, ignoring anything a comment has already claimed.
    One piece explains in a head comment that "the one script sits at the end
    of <body>", and a plain search for the tag matched that sentence. The
    return bar was injected into the middle of the comment, which split it in
    two: the head ended at the injected div, the canonical and the Open Graph
    tags fell into the body, and the rest of the comment printed on the page
    as text. Comment spans are skipped, so only a real tag can match."""
    pos = 0
    while True:
        c = text.find("<!--", pos)
        m = _BODY_TAG.search(text, pos, c if c != -1 else len(text))
        if m:
            return m
        if c == -1:
            return None
        end = text.find("-->", c + 4)
        if end == -1:
            return None                      # unterminated: nothing to inject into
        pos = end + 3


def add_return(path, up="index.html", upname="Home", bar=True):
    """Give a standalone piece a way back into the site. Any earlier injection
    is stripped first, so a page never ends up carrying two."""
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return
    before = text
    text = strip_injected(text)

    pill = RETURN_PILL.replace("__UP__", up).replace("__UPNAME__", upname)
    if bar:
        top = RETURN_BAR.replace("__UP__", up).replace("__UPNAME__", upname)
        m = _body_tag(text)
        text = (text[:m.end()] + top + text[m.end():]) if m else (top + text)
    i = text.lower().rfind("</body>")
    text = (text[:i] + pill + text[i:]) if i != -1 else (text + pill)
    if text != before:
        open(path, "w", encoding="utf-8").write(text)


# --------------------------------------------------- piece page heads ----
# Every piece is a standalone file with its own <head>, written at different
# times by different converters. That is how twenty-two of them ended up
# claiming their canonical URL was /none: the converter was handed the string
# "none" to switch off the nav highlight and it reached the canonical too.
# Hand-maintained head tags drift, so the build owns them now. The values come
# from content/pieces.json, which means editing a title in the editor also
# corrects the search-engine and link-preview copy for that piece.

def _card_for(p):
    """The link-preview image. A piece keeps its own card if one has been
    rendered; otherwise it falls back to the site card, which is always
    present, so a page never advertises an image that 404s."""
    own = "cards/" + p["slug"] + ".png"
    return own if os.path.exists(os.path.join(OUT, own)) else "og-card.png"

# Every piece already styles itself off data-theme on <html>; none of them read
# the choice the reader made on the site, so switching to dark on the home page
# and opening an essay put them back in daylight. This applies the stored
# choice before first paint, and mirrors a toggle inside a piece back to the
# same place, so there is one preference rather than fifty-eight.
THEME_JS = """<script>
(function(){
  var d=document.documentElement;
  try{var t=localStorage.getItem('theme'); if(t) d.setAttribute('data-theme',t);}catch(e){}
  new MutationObserver(function(){
    try{
      var v=d.getAttribute('data-theme');
      if(v) localStorage.setItem('theme',v); else localStorage.removeItem('theme');
    }catch(e){}
  }).observe(d,{attributes:true,attributeFilter:['data-theme']});
})();
</script>"""

_HEAD_START, _HEAD_END = "<!--__meta-->", "<!--/__meta-->"

# The pieces were written before the site had a mark, so twenty-six of them
# showed a blank tab icon and asked the server for a favicon.ico that is not
# there. One definition, used by the shell pages and injected into the pieces.
FAVICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           "<rect width='100' height='100' fill='%2316150f'/><text x='50' y='72' font-size='64' "
           "font-family='Helvetica,Arial' font-weight='bold' fill='%23faf9f6' "
           "text-anchor='middle'>A</text></svg>")

def head_block(p):
    url  = SITE_URL + "/" + p["url"]
    desc = (p.get("blurb") or p.get("s") or "").strip()
    if len(desc) > 300:
        desc = desc[:297].rsplit(" ", 1)[0] + "\u2026"
    title = f'{p["t"]} \u2014 {SHORT}'
    return f"""{_HEAD_START}
<link rel="icon" href="{FAVICON}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{esc(SHORT)} \u2014 portfolio">
<meta property="og:image" content="{SITE_URL}/{_card_for(p)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(p["t"])} \u2014 {esc(SHORT)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE_URL}/{_card_for(p)}">
{THEME_JS}
{_HEAD_END}"""

# One tag, matched properly: [^>]* is wrong for any tag whose attribute value
# can itself contain ">". The icon link is exactly that tag, because an SVG data
# URL carries "<svg ...>" inside href, and a pattern that stopped at the first
# ">" cut the tag in half and left the rest of the URL in the document as live
# markup. _ATTRS swallows a quoted value whole, so the match ends at the ">"
# that actually closes the tag.
_ATTRS = r'(?:[^>"\']|"[^"]*"|\'[^\']*\')*'

# the tags the build now owns, wherever an earlier converter left them
_OWNED = re.compile(
    r'\s*<link rel="canonical"' + _ATTRS + r'>'
    r'|\s*<meta property="og:(?:title|description|type|url|site_name|image(?::\w+)?)"' + _ATTRS + r'>'
    r'|\s*<meta name="twitter:(?:card|image)"' + _ATTRS + r'>'
    r'|\s*<link rel="icon"' + _ATTRS + r'>')

# What the old pattern left behind on twenty-two pages, still sitting in their
# <head>: the tail of the icon URL, reading as a real <rect> element. An
# element that cannot appear in <head> ends the head there, so the canonical,
# every Open Graph tag and the theme script landed in <body>, where a scraper
# does not look and a link preview does not resolve. Removed only after _OWNED
# has taken the intact icon links out, so this can never bite a good one: after
# that pass, anything ending in </svg>"> is an orphan by construction.
_ICON_DEBRIS = re.compile(
    r"\s*<rect\b" + _ATTRS + r"/?>\s*<text\b" + _ATTRS + r">[^<]*</text>\s*</svg>\">")

def normalise_head(path, p):
    """Replace whatever head metadata a piece carries with the generated block.
    Idempotent: the block is delimited, so a second run reproduces the file."""
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return False
    before = text
    text = re.sub(re.escape(_HEAD_START) + r".*?" + re.escape(_HEAD_END) + r"\n?",
                  "", text, flags=re.S)
    text = _OWNED.sub("", text)
    i = text.lower().find("</head>")
    if i == -1:
        return False
    # scoped to the head: that is where the orphan does its damage, and it is
    # the only region where "</svg>\">" cannot be something a document meant
    head_txt = _ICON_DEBRIS.sub("", text[:i])
    text = head_txt + head_block(p) + "\n" + text[i:]
    if text != before:
        open(path, "w", encoding="utf-8").write(text)
    return True

_STALE_HOST = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9-]*\.github\.io)\b")

def fix_stale_host(path):
    """Twenty-two pieces carry a footer that was generated before the site
    moved, and it printed the old address as the label on a link that already
    pointed at the new one. The address is not head metadata, so it survived
    the head rewrite; it is corrected here, wherever it appears, including in
    plain text where no URL parser would have found it."""
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return False
    fixed = _STALE_HOST.sub(lambda m: HOST if m.group(1) != HOST else m.group(1), text)
    if fixed != text:
        open(path, "w", encoding="utf-8").write(fixed)
        return True
    return False


def add_returns_everywhere():
    """Two things per standalone piece: the head metadata the build owns, and a
    way back into the site. The bar is skipped where a page already carries full
    navigation, and the tools get the floating pill only, because a bar inside a
    full-screen application sits in the wrong place. The head is normalised on
    every piece regardless, including the converted notes."""
    shell = {"index.html", "library.html", "about.html", "404.html", "research.html",
             "coursework.html", "tools.html", "reader.html", "colophon.html",
             "admin.html"}
    where, by_url = {}, {}
    for p in P:
        by_url[p["url"]] = p
        if p["surface"] == "independent":
            where[p["url"]] = ("research.html", "Research")
        elif p["c"] == "AFM 291":
            where[p["url"]] = ("afm291.html", "The vault")
        elif p["surface"] == "personal":
            where[p["url"]] = ("library.html", "Library")
        else:
            where[p["url"]] = ("coursework.html", "Coursework")
    tools = {p["url"] for p in P if p["k"] == "Tool"}
    n = heads = 0
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".html") or f in shell:
            continue
        path = os.path.join(OUT, f)
        if f in by_url and normalise_head(path, by_url[f]):
            heads += 1
        fix_stale_host(path)
        if 'class="docbar"' in open(path, encoding="utf-8", errors="ignore").read():
            continue                      # converted notes already carry full navigation
        up, upname = where.get(f, ("index.html", "Home"))
        add_return(path, up, upname, bar=f not in tools)
        n += 1
    return n, heads


# --------------------------------------------------------------- write ----
def page_404():
    """Generated like every other shell page, so its piece count and contact
    address cannot fall behind. It used to be the one page the build touched
    but never rewrote, and it sat at 21 pieces and a stale email for months."""
    body = f"""<div class="hero shell" style="padding-block:clamp(3rem,8vw,6rem) 2rem">
  <p class="eyebrow accent">404</p>
  <h1 class="display" style="font-size:clamp(2rem,5vw,3.4rem)">That page is not here.</h1>
  <p class="lede">The address may have a typo, or the piece may have been renamed. The library holds
  all {len(P)} pieces, and pressing <kbd>/</kbd> searches them from anywhere.</p>
  <p style="margin-top:1.5rem"><a href="library.html" style="color:var(--accent);font-weight:620">Open the library <span aria-hidden="true">&#8594;</span></a></p>
</div>
"""
    return head("Page not found \u2014 " + SHORT,
                f"That address is not on this site. The library holds all {len(P)} pieces.",
                "404.html") + body + foot()


# ------------------------------------------------------- service worker ----
def page_sw():
    """A real offline cache, generated so the file list and the version cannot
    fall behind. Three tools register this and three manifests promise the
    reader they work offline; the placeholder that shipped before cached
    nothing, so a reload with no connection failed and the promise was false.

    Precached: the installable tools and the icons their manifests name. They
    are single self-contained files that request nothing else, which is what
    makes a precache honest here rather than a partial one. The cache name
    carries a digest of those files, so publishing a new version of a tool
    retires the old cache instead of serving a stale page forever."""
    want = []
    for p in P:
        if not p["pwa"]:
            continue
        want.append(p["url"])
        base = p["slug"]
        for suffix in ("-192.png", "-512.png"):
            if os.path.exists(os.path.join(OUT, base + suffix)):
                want.append(base + suffix)
        man = base + ".webmanifest"
        if os.path.exists(os.path.join(OUT, man)):
            want.append(man)
    want = sorted(set(want))

    h = hashlib.sha1()
    for f in want:
        path = os.path.join(OUT, f)
        if os.path.exists(path):
            with open(path, "rb") as fh:
                h.update(f.encode("utf-8") + fh.read())
    version = h.hexdigest()[:12]
    files = json.dumps(want, indent=2)

    return f"""/* Offline cache for the installable tools. Generated by build/build_site.py
   from the pieces marked as installing to a phone; do not edit by hand, the
   next build overwrites it. Version changes whenever a cached file changes,
   which is what retires the previous cache. */
const VERSION = "{version}";
const CACHE   = "site-" + VERSION;
const FILES   = {files};

self.addEventListener("install", e => {{
  e.waitUntil(
    caches.open(CACHE)
      // addAll is all-or-nothing, so one missing file would leave the tools
      // with no cache at all. Each file is added on its own and a failure is
      // survivable: the rest still work offline.
      .then(c => Promise.all(FILES.map(f => c.add(f).catch(() => null))))
      .then(() => self.skipWaiting())
  );
}});

self.addEventListener("activate", e => {{
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
}});

self.addEventListener("fetch", e => {{
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  // Network first, so a published change is picked up as soon as there is a
  // connection; the cache is the fallback that makes the offline claim true.
  e.respondWith(
    fetch(req)
      .then(res => {{
        if (res && res.ok && res.type === "basic") {{
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {{}});
        }}
        return res;
      }})
      .catch(() => caches.match(req).then(hit => hit || caches.match("index.html")))
  );
}});
"""


# ----------------------------------------------------- sitemap, robots ----
def page_sitemap():
    """Every address on the site, in one file, so a search engine does not have
    to guess which of fifty-eight files matter. Generated from the same list
    that builds the pages, so a piece cannot be listed here and missing there."""
    urls = [("", "1.0")] + [(p, "0.8") for p in SHELL_PAGES if p != "index.html"]
    urls += [(x["url"], "0.7" if x["featured"] else "0.6") for x in P]
    seen, rows = set(), []
    stamp = TODAY.isoformat()
    for loc, pri in urls:
        if loc in seen or loc == "404.html":
            continue
        seen.add(loc)
        rows.append(f"  <url>\n    <loc>{SITE_URL}/{loc}</loc>\n"
                    f"    <lastmod>{stamp}</lastmod>\n"
                    f"    <priority>{pri}</priority>\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n")


def page_robots():
    """The editor is not for readers and not for indexes."""
    return (f"User-agent: *\nAllow: /\nDisallow: /admin.html\n\n"
            f"Sitemap: {SITE_URL}/sitemap.xml\n")


def jsonld_site():
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": f"{SHORT} — portfolio",
        "url": SITE_URL + "/",
        "inLanguage": "en-CA",
        "author": {"@type": "Person", "name": NAME},
    }
    return ('<script type="application/ld+json">'
            + json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
            + "</script>")


def jsonld_person():
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": NAME,
        "alternateName": SHORT,
        "url": SITE_URL + "/",
        "email": "mailto:" + EMAIL,
        "affiliation": {"@type": "CollegeOrUniversity",
                        "name": S["affiliation"][0],
                        "department": S["affiliation"][1]},
        "knowsAbout": ["Financial reporting under IFRS and ASPE",
                       "Canadian taxation", "Accounting analytics"],
    }
    return ('<script type="application/ld+json">'
            + json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
            + "</script>")


SHELL_PAGES = ("index.html", "research.html", "coursework.html", "tools.html",
               "library.html", "about.html", "colophon.html", "404.html")

# ------------------------------------------------------------- checks ----
# The build guarantees what it generates. Everything it merely touches was
# still hand-maintained, and drifted: twenty-two pages claimed a canonical URL
# of /none, the footer printed the old address while linking to the new one,
# and two tools asked for an icon that was never there. None of that was
# visible in a diff, because nothing was looking. These three assertions look.
# They run on every build and fail it, which is the same move as the colophon
# applied to the build: state the rule, then let something disagree with you.

def check_site():
    problems, files = [], set(os.listdir(OUT))
    for sub in ("cards",):
        if os.path.isdir(os.path.join(OUT, sub)):
            files |= {sub + "/" + f for f in os.listdir(os.path.join(OUT, sub))}

    def local(u):
        if not u or re.match(r"^(https?:|mailto:|tel:|#|data:|//|javascript:)", u):
            return None
        return u.split("#")[0].split("?")[0] or None

    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".html"):
            continue
        text = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore").read()

        # 1. every canonical resolves to a file that exists
        for m in re.finditer(r'<link rel="canonical" href="([^"]+)"', text):
            href = m.group(1)
            if not href.startswith(SITE_URL):
                problems.append(f"{f}: canonical points off-site, {href}")
                continue
            rest = href[len(SITE_URL):].lstrip("/") or "index.html"
            if rest not in files:
                problems.append(f"{f}: canonical is {href}, which is not a file here")

        # 2. no page names a host other than this one
        # bare, not just inside a URL: the stale address that survived the
        # move was sitting in link text, where a URL pattern never saw it
        for host in set(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9-]*\.github\.io\b", text)):
            if host != HOST:
                problems.append(f"{f}: mentions {host}, which is not this site")

        # 3. every local href and src resolves. Script and style blocks are cut
        # first: a page that builds its own markup client-side has href= inside
        # a template literal, and `${esc(s.url)}` is live code, not a dead link.
        prose = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", text, flags=re.S | re.I)
        for m in re.finditer(r'(?:href|src)="([^"]+)"', prose):
            u = local(m.group(1))
            # reader.html builds a couple of URLs in script; those are not links
            if u and "' +" not in u and u not in files:
                problems.append(f"{f}: links to {u}, which does not exist")

    # 4. every manifest icon resolves
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".webmanifest"):
            continue
        try:
            data = json.load(open(os.path.join(OUT, f), encoding="utf-8"))
        except Exception as e:
            problems.append(f"{f}: is not readable as JSON ({e})")
            continue
        for icon in data.get("icons", []):
            if icon.get("src") not in files:
                problems.append(f"{f}: names icon {icon.get('src')}, which does not exist")

    # 5. a figure shown on a page must have its colour scope generated. A
    # lifted figure inherits nothing from the page it lands on: registering it
    # in figures.json and forgetting the variables renders it in default black,
    # which is exactly what happened the first time a fourth one was added.
    sheet = ""
    fpath = os.path.join(OUT, "figures.css")
    if os.path.exists(fpath):
        sheet = open(fpath, encoding="utf-8").read()
    for f in SHELL_PAGES:
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        for fid in set(re.findall(r'id="(fs-[a-z0-9]+)"', text)):
            if ("#" + fid) not in sheet:
                problems.append(f"{f}: shows figure {fid}, which has no colour "
                                f"scope in figures.css")

    # 6. a converted document must carry exactly one top-level heading in its
    # body. More than one means the stylesheet's title-suppressing rule is
    # deleting section headings from the page, which is how eight of them
    # disappeared from one piece without anything failing.
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".html"):
            continue
        text = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore").read()
        i = text.find('class="docbody"')
        if i == -1:
            continue
        n = len(re.findall(r"<h1[\s>]", text[i:]))
        if n > 1:
            problems.append(f"{f}: {n} top-level headings in the document body; "
                            f"all but the first are hidden by the stylesheet")

    # 7. the head has to hold. Every generated tag can be correct and still be
    # useless if the browser has already closed <head> before reaching it: one
    # stray element there ends the head, and the canonical and the Open Graph
    # tags after it are parsed into <body>, where no scraper reads them. The
    # tags are checked by name after quoted attribute values and comments are
    # removed, so a "<" inside a data URL is not mistaken for markup.
    HEAD_OK = {"html", "head", "meta", "link", "title", "/title", "script",
               "/script", "style", "/style", "base", "noscript", "/noscript",
               "!doctype", "/head"}
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".html"):
            continue
        text = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore").read()
        j = text.lower().find("</head>")
        if j == -1:
            problems.append(f"{f}: has no </head>")
            continue
        # Style and script bodies go first. Their contents are not markup, and
        # the quotes inside a stylesheet do not pair with the quotes in the
        # tags around it: leaving them in let a run of CSS quotes swallow the
        # very element this check exists to find.
        head_txt = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", text[:j],
                          flags=re.S | re.I)
        head_txt = re.sub(r"<!--.*?-->", "", head_txt, flags=re.S)
        head_txt = re.sub(r'"[^"]*"', '""', head_txt)
        head_txt = re.sub(r"'[^']*'", "''", head_txt)
        for tag in set(re.findall(r"<(/?[A-Za-z!][A-Za-z0-9]*)", head_txt)):
            if tag.lower() not in HEAD_OK:
                problems.append(f"{f}: <{tag}> inside <head> ends the head early; "
                                f"everything after it is parsed into the body")

    # 8. every listed piece has a file behind it
    for x in P:
        if x["url"] not in files:
            problems.append(f"content/pieces.json: {x['slug']} points at {x['url']}, which does not exist")

    return sorted(set(problems))


def main():
    pages = {"index.html": page_index(), "research.html": page_research(),
             "coursework.html": page_coursework(), "tools.html": page_tools(),
             "library.html": page_library(), "about.html": page_about(),
             "colophon.html": page_colophon(), "404.html": page_404(),
             "sitemap.xml": page_sitemap(), "robots.txt": page_robots(),
             "figures.css": ("/* Generated from build/figures.json. Do not edit: the next build\n"
                             "   overwrites it. Each lifted figure keeps the colour variables and\n"
                             "   class rules it was drawn against, scoped to its own id so nothing\n"
                             "   leaks into the page around it. */\n" + strip_css() + "\n")}
    changed = []
    for name, text in pages.items():
        path = os.path.join(OUT, name)
        old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if old != text:
            open(path, "w", encoding="utf-8").write(text)
            changed.append(name)

    for f, css in OVERFLOWING.items():
        path = os.path.join(OUT, f)
        if os.path.exists(path):
            fit_mobile(path, css)

    n, heads = add_returns_everywhere()

    # After the pieces, not before: the service worker's version is a digest of
    # the files it caches, and the pass above edits three of them. Generated
    # first, the digest described the previous build and the file never settled.
    sw = page_sw()
    swpath = os.path.join(OUT, "sw.js")
    if (not os.path.exists(swpath)) or open(swpath, encoding="utf-8").read() != sw:
        open(swpath, "w", encoding="utf-8").write(sw)
        changed.append("sw.js")

    print(f"{len(P)} pieces · {TOTAL_WORDS:,} words · {TOTAL_FIGS} figures · {TOTAL_TBLS} tables")
    print("rewrote: " + (", ".join(changed) if changed else "nothing, pages already current"))
    print(f"return navigation checked on {n} standalone pieces, "
          f"head metadata written on {heads}")

    problems = check_site()
    if problems:
        print(f"\n{len(problems)} problem(s) found. The site was written, but this is broken:")
        for line in problems[:40]:
            print("  " + line)
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        sys.exit(1)
    print("checks passed: every link, canonical, icon and listed file resolves")

if __name__ == "__main__":
    main()
