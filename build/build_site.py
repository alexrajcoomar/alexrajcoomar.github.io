# -*- coding: utf-8 -*-
"""Rebuild the index pages from content/pieces.json.

Content lives in content/pieces.json. Design lives here and in site.css.
This script never touches a piece's own HTML except to give it a way back
into the site, and it never touches the stylesheet. Run by the GitHub
Action on every push, so the site relists itself.
"""
import datetime, hashlib, html, json, math, os, re, shutil, struct, subprocess, sys, tempfile

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = json.load(open(os.path.join(ROOT, "content", "pieces.json"), encoding="utf-8"))
METRICS = json.load(open(os.path.join(ROOT, "content", "metrics.json"), encoding="utf-8"))
# the case map: for each featured piece, where in the record each of the eight
# slots is answered. A reading of the pieces, kept out of this file so that
# disagreeing with a placement is an edit to content rather than to the build.
CASES   = json.load(open(os.path.join(ROOT, "content", "cases.json"), encoding="utf-8"))
# the capability map: which pieces evidence each of the four things the about
# page says the portfolio demonstrates. Membership is a reading; every number
# printed beside it is recomputed from the measurements on each build.
CAPS    = json.load(open(os.path.join(ROOT, "content", "capabilities.json"), encoding="utf-8"))
# the parts of a resume nothing here can measure: education, employment and
# named skills. Everything else on resume.html is generated from the same
# measurements the rest of the site uses, and a section with no entries is
# not rendered at all.
RESUME_D = json.load(open(os.path.join(ROOT, "content", "resume.json"), encoding="utf-8"))
# the change ledger of the last content pass; written by build/ledger.py,
# read here for one computed sentence on the colophon and for check 16
try:
    LEDGER = json.load(open(os.path.join(ROOT, "content", "ledger.json"), encoding="utf-8"))
except Exception:
    LEDGER = {}
HERE    = os.path.dirname(os.path.abspath(__file__))
STRIP   = json.load(open(os.path.join(HERE, "figures.json"), encoding="utf-8"))
OUT     = ROOT

S        = CONTENT["site"]
NAME     = S["name"]
SHORT    = S["short"]
EMAIL    = S["email"]
SITE_URL = S["url"]
BORN     = tuple(int(x) for x in S["born"].split("-"))
# Recruiter fields. All optional: an empty value renders nothing, so the
# owner fills them in pieces.json (or the editor) when he has them, and no
# placeholder can ever look production-ready.
RESUME    = (S.get("resume") or "").strip()
LINKEDIN  = (S.get("linkedin") or "").strip()
GITHUB    = (S.get("github") or "").strip()
COOP_TERM = (S.get("coop_term") or "").strip()
GRAD_YEAR = (S.get("grad_year") or "").strip()
# Term standing, e.g. 2B: the fact a co-op recruiter screens on. Owner input,
# like the name; an empty value renders nothing.
STANDING  = (S.get("standing") or "").strip()
WPM      = 230
DOC_MIN  = 1200
TODAY    = datetime.date.today()
# The address is written once, in content/pieces.json, and everything that shows
# it derives from that. A label typed by hand is a label that survives a move:
# the footer of every page used to print the old address while linking to the
# new one, which is the single contradiction this site cannot afford.
HOST     = SITE_URL.split("//", 1)[-1].rstrip("/")

# The colophon describes the font subset in numbers, so those numbers are
# measured from the shipped file and the cmap the subset was cut to, the same
# way every other figure on the site is measured rather than typed.
FONT_BYTES = os.path.getsize(os.path.join(ROOT, "InterVariable-sub.woff2"))
FONT_CODEPOINTS = len([c for c in open(
    os.path.join(HERE, "font-subset-cmap.txt"), encoding="utf-8"
).read().strip().split(",") if c != ""])

# The definitions behind the counted numbers, stated once. The colophon
# prints them as a list, and every counted number on a generated page carries
# the id of the definition it was counted under, so a reader can open the
# definition from the number rather than hunt for it.
DEFS = [
    ("pieces", "Pieces",
     "An entry in content/pieces.json with a file behind it. The three run transcripts are measured "
     "and held to the same record but are not entries, so they are not pieces and not in the corpus line."),
    ("words", "Words",
     "The text of the rendered document after its own scripts have run, with script, style and "
     "noscript removed and collapsed answers included, whether or not a reader has opened them. "
     "The site's own chrome around a piece is not counted: the header, the return bar, the footer, "
     "the contents rail, the search dialog and the line that says what the piece was built from. "
     "A word is a whitespace-separated token containing at least one letter or digit. Question banks "
     "inside the interactive tools are held in code, so they are not counted anywhere."),
    ("mins", "Reading time",
     f"Derived, not counted: words divided by {WPM} words per minute, rounded, minimum one minute. "
     f"A page that renders under {DOC_MIN:,} words is treated as an instrument rather than a document "
     "and carries no reading time."),
    ("figures", "Figures",
     "A top-level svg element in the rendered page, not nested inside another one, covering at least "
     "6,000 square units, which excludes inline glyphs and icons. Counted after render, so it includes "
     "charts a script draws on load; charts built purely from HTML and CSS are not counted, so the "
     "number is a floor rather than a ceiling."),
    ("tables", "Tables",
     "A table element in the rendered document after its scripts have run, wherever it stands."),
    ("checkpoints", "Checkpoint questions",
     "A details element in the rendered document: a question or a worked answer folded away for the "
     "reader to try first."),
]
DEF_BY_ID = {d[0]: d for d in DEFS}

def md(value, kind, of=None, text=None):
    """A counted number as a data element: the raw value, the id of the
    definition it was counted under, and the piece it belongs to when it
    belongs to one. With scripts on, the number opens its definition and its
    measurement; with scripts off it stands as text, and the definition is on
    the colophon."""
    of_attr = f' data-of="{esc(of)}"' if of else ""
    return f'<data class="m" value="{value}" data-m="{kind}"{of_attr}>{text if text is not None else n(value)}</data>'

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
import atlas as atlas_mod
import invariance
import claims
import marks as marks_mod
import fingerprint
# the last content pass's own account of what it got wrong and left undone,
# written by hand during the pass; printed on the colophon, not filed away
try:
    LEDGER_NOTES = json.load(open(os.path.join(HERE, "ledger-notes.json"), encoding="utf-8"))
except Exception:
    LEDGER_NOTES = {}

# The exceptions the site declares by name, so the claims they qualify can
# fail: the records the em dash rule leaves as written, and the pages the
# fit row allows past 320px. A page not named here that breaks the rule
# fails the build; a page named here that no longer needs it does too.
try:
    DECLARED = json.load(open(os.path.join(ROOT, "content", "declared.json"), encoding="utf-8"))
except (OSError, ValueError):
    DECLARED = {}
import emdash

# American spellings the build's own words must not use. Whole words, any
# case; -ize forms are Canadian and are not listed, and "dialog" is the HTML
# element's name as well as a word, so it is not listed either.
US_SPELLINGS = {
    "color", "colors", "colored", "coloring", "colorful", "center", "centers", "centered", "centering",
    "meter", "meters", "liter", "liters", "fiber", "fibers", "theater", "theaters", "gray", "grays",
    "favor", "favors", "favored", "favorite", "favorites", "flavor", "flavors", "flavored", "honor",
    "honors", "honored", "humor", "labor", "labors", "neighbor", "neighbors", "neighboring", "harbor",
    "rumor", "rumors", "vigor", "behavior", "behaviors", "defense", "defenses", "offense", "pretense",
    "catalog", "catalogs", "traveled", "traveling", "traveler", "modeled", "modeling", "canceled",
    "canceling", "labeled", "labeling", "signaled", "totaling", "totaled", "jewelry", "fulfill",
    "fulfills", "fulfilled", "enrollment", "installment", "skillful", "mold", "molds", "plow", "sulfur",
    "maneuver", "counselor", "marvelous", "armor", "clamor", "endeavor", "odor", "parlor", "savior",
    "splendor", "valor", "somber", "specter", "caliber", "saber", "chili", "draft-", "pajamas", "ax",
    "esthetic", "leukemia", "anemia", "paralyzed-", "dependent-", "checkered", "encyclopedia-",
}

# Five entries. The four shelves are one statement filtered four ways and are
# reached from the statement's own subtotal rows and from Work, which is the
# whole of it; Notes is the colophon, where every column is defined.
NAV = [("index.html","Home"),("library.html","Work"),("atlas.html","Atlas"),
       ("about.html","About"),("colophon.html","Notes")]

# Research, Coursework and Tools are one sequence and each said so on its
# own -- "Section 01", "Section 02", "Section 03" -- without ever showing
# the other two. The Atlas had the same problem with its six wall labels
# and answered it with a guide that is progress, contents and skip control
# at once. The same guide is reused here rather than restated.
SECTIONS = [("research.html",   "Research and writing"),
            ("coursework.html", "Coursework"),
            ("tools.html",      "Interactive tools")]

def section_guide(page):
    """The Atlas sequence guide, carried to the three section pages.

    aria-current is "page" rather than "step": the Atlas marks a position
    in a tour, this marks a position in a site, and a screen reader should
    hear the difference."""
    items = "\n".join(
        '        <li><a href="%s"%s><b>%02d</b> %s</a></li>'
        % (u, ' aria-current="page"' if u == page else '', i, esc(t))
        for i, (u, t) in enumerate(SECTIONS, 1))
    return (f'  <nav class="guide sections" aria-label="The three sections">\n'
            f'    <p class="guide-h">The sections '
            f'<span class="guide-c">{len(SECTIONS)} in the sequence</span></p>\n'
            f'    <ol>\n{items}\n    </ol>\n'
            f'  </nav>')

def section_eyebrow(page):
    """The eyebrow keeps its class, which the Atlas page also uses, and
    gains the total the plate index carries: 01 / 03 rather than 01."""
    n = [u for u, _ in SECTIONS].index(page) + 1
    return (f'<p class="eyebrow accent">Section '
            f'<span class="tnum">{n:02d} / {len(SECTIONS):02d}</span></p>')


# --------------------------------------------------------------- assets ----
# A stylesheet and a script are cached by URL, and a reader who has been here
# before keeps the copy they already have until it expires. That is fine while
# the two agree, and it is not fine the moment one of them changes: the live
# page ran yesterday's globe against today's markup for a good ten minutes
# after a deploy. Each asset therefore carries a short digest of its own
# contents in the query string, so a changed file is a different URL and can
# never be served from a copy of the old one.
ASSET_V = {}

def asset(name):
    v = ASSET_V.get(name)
    return name + ("?v=" + v if v else "")

def _digest(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]

def stamp_assets(generated):
    """generated: name -> the text this build is about to write. Anything not
    generated is read from disk, because it is hand-written and already there."""
    for name in ("site.css", "figures.css", "site.js", "atlas.js", "long.css", "long.js"):
        if name in generated:
            ASSET_V[name] = _digest(generated[name])
            continue
        path = os.path.join(OUT, name)
        if os.path.exists(path):
            ASSET_V[name] = _digest(open(path, encoding="utf-8",
                                         errors="ignore").read())

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
<meta property="og:site_name" content="{esc(SHORT)} · portfolio">
<meta property="og:url" content="{SITE_URL}/{'' if page=='index.html' else page}">
<meta property="og:image" content="{SITE_URL}/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(SHORT)} · portfolio">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE_URL}/og-card.png">
<link rel="canonical" href="{SITE_URL}/{'' if page=='index.html' else page}">
<link rel="manifest" href="site.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="preload" href="InterVariable-sub.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{asset("site.css")}">
<link rel="stylesheet" href="{asset("figures.css")}">
<link rel="icon" href="{FAVICON}">
<script>
/* Theme before first paint, so there is no flash. Obsidian is the site's
   default: a browser that holds no choice lands dark, and only the stored
   word "light" lands light. Wrapped because some embedded contexts throw
   on storage access, and a browser that throws still lands dark. */
(function(){{var t=null;try{{t=localStorage.getItem('theme');}}catch(e){{}}
document.documentElement.setAttribute('data-theme',t==='light'?'light':'dark');
document.documentElement.className+=' js';}})();
</script>
<!-- A control that can do nothing is worse than no control: with scripts
     off, the script-driven surfaces hide rather than sit dead. Everything
     they reach remains reachable as plain links and server-rendered lists. -->
<noscript><style>.hbtns,#keysbtn,.tools-bar,#corpusread,#atlasmini,.jsonly,.offline-controls{{display:none !important}}</style></noscript>{extra}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="bar">
    <a class="brand" href="index.html">{marks_mod.svg("brand")}{esc(SHORT)} <span class="sub">portfolio</span></a>
    <nav class="main" aria-label="Sections">
      {nav}
    </nav>
    <div class="hbtns">
      <button class="iconbtn searchbtn" type="button" id="searchbtn" aria-label="Search all work">
        <span aria-hidden="true">&#9906;</span><span class="lbl">Search</span> <kbd>/</kbd>
      </button>
      <div class="themesel" id="themesel" role="group" aria-label="Theme">
        <button type="button" class="tsel" data-pick="dark" aria-pressed="false"><i aria-hidden="true"></i>Obsidian</button>
        <button type="button" class="tsel" data-pick="light" aria-pressed="false"><i aria-hidden="true"></i>Archival light</button>
      </div>
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

def _defs_json():
    """What a counted number can show: the definitions, the record's identity
    and each listed piece's measured figures. The record is named by the
    digest of content/metrics.json, so the dialog can say exactly which
    record a number came from without a date that would go stale."""
    mpath = os.path.join(ROOT, "content", "metrics.json")
    digest = hashlib.sha1(open(mpath, "rb").read()).hexdigest()[:12] if os.path.exists(mpath) else ""
    return json.dumps({
        "defs": {d[0]: {"t": d[1], "d": d[2]} for d in DEFS},
        "meas": {"tool": "build/measure.js", "record": "content/metrics.json", "digest": digest,
                 "pieces": len(P), "transcripts": len([k for k in METRICS if k not in {p["slug"] for p in P}])},
        "pieces": {p["slug"]: {"u": p["url"], "t": p["t"], "w": p["words"], "f": p["figures"], "b": p["tables"]} for p in P},
    }, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")

def foot():
    return f"""</main>
<footer class="site">
  <div class="cols">
    <div>
      <h2>{esc(SHORT)}</h2>
      <p class="small fnote">Accounting and Financial Management, Analytics stream, University of Waterloo. {len(P)} published pieces: research, interactive tools and references, all of them running rather than described.</p>
      <p class="small"><a class="inlink" href="mailto:{EMAIL}">{EMAIL}</a></p>
    </div>
    <nav aria-label="Sections, from the footer">
      <h2>Sections</h2>
      <a href="research.html">Research and writing</a>
      <a href="coursework.html">Coursework</a>
      <a href="tools.html">Interactive tools</a>
      <a href="library.html">Full library</a>
    </nav>
    <nav aria-label="About this site">
      <h2>This site</h2>
      <a href="about.html">About and contact</a>
      <a href="colophon.html">Colophon and method</a>
      <a href="controls.html">Controls: what is tested</a>
      <a href="{SITE_URL}">{HOST}</a>
    </nav>
  </div>
  <div class="fine">
    <span>&copy; {TODAY.year} {esc(NAME)}</span>
    <span><b>{md(len(P), "pieces")}</b> pieces &middot; <b>{md(TOTAL_WORDS, "words")}</b> words &middot; <b>{md(TOTAL_FIGS, "figures")}</b> figures &middot; no framework, nothing external at runtime, one build you can read &middot; <button id="keysbtn" type="button" class="linkbtn">keyboard</button></span>
  </div>
</footer>

<!-- Search across every piece. Progressive: every link on the site works
     without it, and the button is the same route as the keyboard. -->
<dialog class="cmdk" id="cmdk" aria-label="Search all work">
  <div class="cmdk-panel">
    <input id="cmdk-input" type="text" placeholder="Search {len(P)} pieces by title, course or topic" autocomplete="off" spellcheck="false" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="cmdk-list">
    <ul class="cmdk-list" id="cmdk-list" role="listbox" aria-label="Results"></ul>
    <div class="cmdk-foot">
      <span><kbd>&#8593;</kbd><kbd>&#8595;</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span>
    </div>
  </div>
</dialog>

<!-- The keyboard routes, written down. A shortcut nobody can find is the
     same as one that does not exist. Opened with ? or from the footer. -->
<dialog class="keys" id="keysheet" aria-labelledby="keystitle">
  <form method="dialog" class="keys-panel">
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
    <p class="keys-pref"><label><input type="checkbox" id="keysingles" checked>
      Single-key shortcuts. Turn these off if a key press where you did not
      mean one keeps opening things; search stays on <kbd>&#8984;</kbd><kbd>K</kbd>.</label></p>
    <button class="close">Close</button>
  </form>
</dialog>
<!-- A counted number opens here: its definition, the file it was measured
     from, the script and the record. The data is the build's, the text is the
     colophon's, and the dialog is the browser's. -->
<dialog class="prov" id="prov" aria-labelledby="prov-h">
  <form method="dialog" class="prov-panel">
    <p class="prov-k" id="prov-k"></p>
    <h2 id="prov-h"></h2>
    <p class="prov-def" id="prov-def"></p>
    <p class="prov-src" id="prov-src"></p>
    <p class="prov-links" id="prov-links"></p>
    <button class="close">Close</button>
  </form>
</dialog>
<script type="application/json" id="defs">{_defs_json()}</script>
<script>
window.WORK = {WORKJSON};
</script>
<script src="{asset("site.js")}" defer></script>
</body>
</html>
"""

# ------------------------------------------------------ components ----
# The statement: one grammar for the home page, the four shelves and the
# chrome inside a piece. A row is a title and three measured figures; a
# subtotal is an origin; the total is the corpus line. Every number is
# metrics.json or a sum of it, and checks 12 and 13 hold them.

def n(x):
    return f"{x:,}"

def stmt_cells(w, f, t, mins=None, of=None):
    # Minutes sit under the word count rather than in a column of their own:
    # a fifth column does not fit a 390px phone, and the two belong together
    # anyway, one counted and one derived from it. A page under DOC_MIN words
    # carries none, which is the colophon's rule, not a missing value.
    mm = f'<span class="mins">{md(mins, "mins", of, str(mins))} min</span>' if mins else ""
    return (f'<td class="n">{md(w, "words", of)}{mm}</td><td class="n fig">{md(f, "figures", of, str(f))}<span class="tb"> &middot; {md(t, "tables", of, str(t))}</span></td>'
            f'<td class="n tab">{md(t, "tables", of, str(t))}</td>')

def flagged_lift(p):
    """The one graft from the Specimen thesis: the result line of Flagged in
    Hindsight, read from the piece's own result element at build time and
    registered with the caption check. If the element is not there, there is
    no line; nothing is typed in its place."""
    try:
        raw = open(os.path.join(OUT, p["url"]), encoding="utf-8", errors="ignore").read()
    except OSError:
        return None
    m = re.search(r'<div class="big-stat">(.*?)</div>', raw, re.S)
    if not m:
        return None
    inner = re.sub(r"<br\s*/?>", " ", m.group(1))
    num = re.sub(r"<small>.*", "", inner, flags=re.S).strip()
    sm = re.search(r"<small>(.*?)</small>", inner, re.S)
    txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", sm.group(1)))).strip() if sm else ""
    if not num:
        return None
    CAPTIONS.append((num + " " + txt, p["url"]))
    return num, txt

def stmt_row(p, lift=None):
    sub = f'<span class="s">{esc(p["s"])}</span>' if p.get("s") else ""
    out = (f'<tr class="item{" haslift" if lift else ""}" data-o="{p["surface"]}"><th scope="row"><a href="{p["url"]}">{esc(p["t"])}</a>{sub}</th>'
           + stmt_cells(p["words"], p["figures"], p["tables"], piece_mins(p), of=p["slug"]) + "</tr>")
    if lift:
        out += (f'\n<tr class="liftrow"><td colspan="4"><span class="lift"><b>{esc(lift[0])}</b> {esc(lift[1])}</span></td></tr>')
    return out

def stmt_subrow(label, d, href, note=None, cls="sub", sub2=""):
    nr = f'<a class="nref" href="#n{note}" aria-label="Note {note}">{note}</a>' if note else ""
    s2 = f'<span class="sub2">{esc(sub2)}</span>' if sub2 else ""
    return (f'<tr class="{cls}"><th scope="row"><a href="{href}">{esc(label)}</a>{nr}{s2}</th>'
            + stmt_cells(d["words"], d["figures"], d["tables"]) + "</tr>")

def stmt_head_cells():
    return ('<thead><tr><th scope="col">Piece</th>'
            '<th scope="col" class="n"><a href="colophon.html#def-words">Words<span class="nref">1</span></a></th>'
            '<th scope="col" class="n fig"><a href="colophon.html#def-figures">Figures<span class="tb tbh"><span class="dot">&middot; </span>tables</span><span class="nref">1</span></a></th>'
            '<th scope="col" class="n tab"><a href="colophon.html#def-tables">Tables<span class="nref">1</span></a></th></tr></thead>')

def link_degree(slug):
    """How many documents this one is joined to by a link its prose makes, or
    that another document's prose makes to it. The same edges the sphere draws
    as chords, counted per document."""
    n = 0
    for a, b in ATLAS.get("edges") or ():
        if a == slug or b == slug:
            n += 1
    return n


def fingerprint_coverage():
    """How much of the figure the statement actually draws. Each layer is only
    there when its value is, and one of them is rarely there: a chord joins two
    of the ring's nodes, so a document with fewer than two figures has nowhere
    to put one however many links it records."""
    out = {"pieces": len(P), "links": 0, "chords": 0, "rays": 0, "nodes": 0, "elements": 0}
    for q in P:
        d = fingerprint.derive(q["words"], q["figures"], q["tables"], link_degree(q["slug"]))
        out["links"] += 1 if d["C"] else 0
        out["chords"] += 1 if (d["C"] and d["F"] >= 2) else 0
        out["rays"] += 1 if d["T"] else 0
        out["nodes"] += 1 if d["F"] else 0
        # boundary, the ray path, the ring, the chord path, a node each, and
        # the observer and the author's datum
        out["elements"] += (1 + (1 if d["T"] else 0) + (1 if d["F"] else 0)
                            + (1 if (d["C"] and d["F"] >= 2) else 0) + d["F"] + 2)
    return out


def piece_fingerprint(p):
    """The row's own four measured values as one figure. Nothing here is
    chosen: the radius is the word count, the rays are the tables, the nodes
    are the figures and the chords are the recorded links."""
    return fingerprint.svg(p["words"], p["figures"], p["tables"], link_degree(p["slug"]))


# ------------------------------------------------------- selected work ----
# Eight slots, in the order a reader needs them. The vocabulary is fixed here;
# what fills a slot never is. A slot is answered by a heading the piece already
# carries, by another document the corpus records a link to, or by a value this
# build holds. A slot nothing answers prints as not carried, because a shape
# with a hole in it tells a reader more than a hole that has been filled in.
CASE_SLOTS = [
    ("question",   "Question",   "What the piece set out to settle."),
    ("context",    "Context",    "What was already on the table when it started."),
    ("approach",   "Approach",   "The method, fixed before the result."),
    ("evidence",   "Evidence",   "What the argument rests on, and how it is labelled."),
    ("build",      "Build",      "What was made in order to answer it."),
    ("finding",    "Finding",    "The result, in its narrow form."),
    ("limitation", "Limitation", "What the piece will not carry."),
    ("artifact",   "Artifact",   "The thing you can open."),
]
CASE_BY_SLUG = {p["slug"]: p for p in P}
_CASE_H = re.compile(r"<(h[1-6])\b([^>]*)>(.*?)</\1>", re.S | re.I)


def case_headings(url):
    """Every heading in a piece that carries an id, as id to text. Read from
    the file on every build rather than stored here, so a heading cannot go on
    being quoted after the piece stopped saying it. Tags inside a heading
    become a space, which is how build/invariance.py records the same text."""
    path = os.path.join(OUT, url)
    if not os.path.exists(path):
        return {}
    raw = re.sub(r"<(script|style|svg)\b[^>]*>.*?</\1>", " ",
                 open(path, encoding="utf-8", errors="ignore").read(), flags=re.S | re.I)
    out = {}
    for m in _CASE_H.finditer(raw):
        i = re.search(r'\bid="([^"]+)"', m.group(2))
        if not i:
            continue
        txt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(3)))).strip()
        if txt and i.group(1) not in out:
            out[i.group(1)] = txt
    return out


def case_rows(slug):
    """The eight slots for one featured piece, each resolved to where it is
    answered. Nothing is invented for a slot the map leaves empty."""
    p = CASE_BY_SLUG[slug]
    spec = (CASES.get("cases") or {}).get(slug) or {}
    heads = case_headings(p["url"])
    rows = []
    for key, label, meaning in CASE_SLOTS:
        s = spec.get(key) or {}
        r = {"key": key, "label": label, "meaning": meaning, "kind": None}
        if "sec" in s and s["sec"] in heads:
            r.update(kind="sec", id=s["sec"], text=heads[s["sec"]],
                     href="%s#%s" % (p["url"], s["sec"]))
        elif "doc" in s:
            docs = [CASE_BY_SLUG[d] for d in s["doc"] if d in CASE_BY_SLUG]
            if docs:
                r.update(kind="doc", docs=docs)
        elif s.get("rec") == "built_from" and p.get("built_from", "").strip() not in ("", NOT_DECLARED):
            r.update(kind="rec", text=p["built_from"].strip(), label_as="built_from")
        elif s.get("rec") == "piece":
            r.update(kind="rec", text=p["demo"] or p["s"], href=p["url"])
        rows.append(r)
    return rows


def case_coverage():
    """How much of the shape the six pieces actually carry, by where each slot
    is answered. The gap is the point of the number, so it is counted."""
    out = {"pieces": 0, "slots": 0, "sec": 0, "doc": 0, "rec": 0, "gap": 0}
    for slug in (CASES.get("cases") or {}):
        if slug not in CASE_BY_SLUG:
            continue
        out["pieces"] += 1
        for r in case_rows(slug):
            out["slots"] += 1
            out[r["kind"] or "gap"] += 1
    return out


def case_cell(r):
    """One slot, rendered. A section quotes the piece's own heading and opens
    it; a document names the documents the corpus records; a record prints the
    value the build holds; a slot with nothing behind it says so."""
    if r["kind"] == "sec":
        return ('<a class="cslot" href="%s">%s</a>' % (esc(r["href"]), esc(r["text"]))
                + ' <span class="cwhere">section</span>')
    if r["kind"] == "doc":
        links = ", ".join('<a class="cslot" href="%s">%s</a>' % (esc(d["url"]), esc(d["t"]))
                          for d in r["docs"])
        return links + ' <span class="cwhere">%s</span>' % (
            "linked document" if len(r["docs"]) == 1 else "linked documents")
    if r["kind"] == "rec":
        if r.get("href"):
            return ('<a class="cslot" href="%s">Open it</a> <span class="cnote">%s</span>'
                    % (esc(r["href"]), esc(r["text"])))
        # the same label the piece's own line carries, so the sentence a reader
        # meets here is the sentence they meet on the document
        if r.get("label_as") == "built_from":
            # Two of the recorded lines open with a "Built on" clause of their
            # own, and the label would double it. The label is dropped there
            # rather than the sentence rewritten, because the sentence is the
            # owner's and lives in content/pieces.json.
            v = r["text"]
            if v[:6].lower() == "built ":
                return '<span class="cnote">%s</span>' % esc(v)
            return '<span class="cnote"><b>Built from</b> %s</span>' % esc(v)
        return '<span class="cnote">%s</span>' % esc(r["text"])
    return '<span class="cgap">Not carried</span>'


def case_entry(k, p):
    """One case: the measured line, the piece's own blurb, and the eight
    slots as a table whose row headers are the slot names."""
    rows = case_rows(p["slug"])
    held = sum(1 for r in rows if r["kind"])
    trs = "\n".join(
        '        <tr%s><th scope="row"><span class="cslotname">%s</span>'
        '<span class="cmeaning">%s</span></th><td>%s</td></tr>'
        % ("" if r["kind"] else ' class="cempty"', esc(r["label"]), esc(r["meaning"]), case_cell(r))
        for r in rows)
    mins = f'{p["mins"]} min' if p["mins"] else "instrument"
    return f"""  <article class="case" id="case-{esc(p["slug"])}">
    <div class="casehead">
      <p class="ceyebrow"><span class="num tnum">{k:02d}</span> {kind_chip(p)} <span class="csurf">{esc(SURF_LABEL[p["surface"]])}</span> <span class="cdate">{esc(p["d"])}</span></p>
      <h2 class="ctitle"><a href="{esc(p["url"])}">{esc(p["t"])}</a></h2>
      <p class="csub">{esc(p["s"])}</p>
      <div class="cfig" aria-hidden="true">{piece_fingerprint(p)}</div>
    </div>
    <p class="cmeasure"><span>{p["words"]:,} words</span><span>{p["figures"]} figures</span><span>{p["tables"]} tables</span><span>{link_degree(p["slug"])} recorded links</span><span>{esc(mins)}</span></p>
    <p class="cblurb">{esc(p["blurb"])}</p>
    <table class="ctable">
      <caption class="csr">The eight slots for {esc(p["t"])}, {held} of {len(CASE_SLOTS)} carried</caption>
      <tbody>
{trs}
      </tbody>
    </table>
    <p class="cread"><a class="cgo" href="{esc(p["url"])}">Read {esc(p["t"])} <span class="arrow" aria-hidden="true">&#8594;</span></a> <span class="cheld">{held} of {len(CASE_SLOTS)} slots carried</span></p>
  </article>"""


def capability_evidence(cap_id):
    """The pieces declared as evidence for one capability, and their totals.
    Which pieces evidence what is a reading and is declared in
    content/capabilities.json; every number here is recomputed from the
    measurements on this build. A piece may evidence more than one capability,
    so these sets are not a partition and their subtotals do not add to the
    corpus."""
    spec = (CAPS.get("capabilities") or {}).get(cap_id) or {}
    items = [CASE_BY_SLUG[x] for x in (spec.get("pieces") or []) if x in CASE_BY_SLUG]
    return {"id": cap_id, "items": items, "n": len(items),
            "gap": (spec.get("gap") or "").strip(),
            "words": sum(q["words"] for q in items),
            "figures": sum(q["figures"] for q in items),
            "tables": sum(q["tables"] for q in items),
            "tools": sum(1 for q in items if q["k"] == "Tool")}


def cap_block(i, cap_id, title, prose):
    """One capability: the owner's own paragraph, then what evidences it. The
    list is folded away, so the page a reader meets is the page that was here
    before and the evidence is one disclosure below it."""
    e = capability_evidence(cap_id)
    cells = "".join(["<span>%d pieces</span>" % e["n"],
                     "<span>%s words</span>" % format(e["words"], ","),
                     "<span>%d figures</span>" % e["figures"],
                     "<span>%d tables</span>" % e["tables"]]
                    + (["<span>%d %s</span>" % (e["tools"], "tool" if e["tools"] == 1 else "tools")]
                       if e["tools"] else []))
    lst = ", ".join('<a href="%s">%s</a>' % (esc(q["url"]), esc(q["t"])) for q in e["items"])
    gap = '<p class="capgap">%s</p>' % esc(e["gap"]) if e["gap"] else ""
    return ('    <div><p class="plate-n"><b>%02d</b> <span>/ %02d</span></p><h3>%s</h3>%s\n'
            '      <p class="capev">%s</p>\n'
            '      <details class="tv capdet"><summary>What evidences it</summary>\n'
            '      <p class="caplist">%s</p>%s</details></div>'
            % (i, len(CAP_BLOCKS), esc(title), prose, cells, lst, gap))


def _res_dates(e):
    f, t = (e.get("from") or "").strip(), (e.get("to") or "").strip()
    if f and t:
        return "%s to %s" % (f, t)
    if f:
        return "%s to present" % f
    return t


def resume_gaps():
    """Which declared sections carry nothing. Printed by the build on every
    run, so an unfilled resume is visible in the log rather than on the page."""
    return [k for k in ("education", "experience", "skills") if not (RESUME_D.get(k) or [])]


def resume_evidence():
    """The four capabilities, largest first by the words behind them, with the
    same totals the about page prints. Nothing new is measured here."""
    rows = []
    for cid, title, _pr in CAP_BLOCKS:
        e = capability_evidence(cid)
        if e["n"]:
            rows.append((title, e))
    rows.sort(key=lambda r: -r[1]["words"])
    return rows


def page_resume(summary=None):
    """A resume native to this site: the identity and the availability it
    already records, the education and employment declared in
    content/resume.json, and then the part no other resume can carry, which is
    the corpus itself, measured. Everything countable on this page is counted
    by the build that writes it. It prints to one document, and that is the
    PDF: nothing here is a second file that could disagree with the page."""
    aff = S.get("affiliation") or []
    # the register's own tallies, which exist only after the checks have run;
    # this page is written inside the same fixpoint the colophon is, so the
    # numbers it prints are the numbers that page prints
    reg = summary or {}
    ed = "".join(
        '<div class="rrow"><p class="rwhen">%s</p><div class="rwhat"><h3>%s</h3>'
        '<p class="rwhere">%s</p>%s</div></div>'
        % (esc(_res_dates(e)), esc(e.get("credential") or ""), esc(e.get("institution") or ""),
           ('<p class="rnote">%s</p>' % esc(e["note"])) if (e.get("note") or "").strip() else "")
        for e in (RESUME_D.get("education") or []))
    ex = "".join(
        '<div class="rrow"><p class="rwhen">%s</p><div class="rwhat"><h3>%s</h3>'
        '<p class="rwhere">%s</p>%s</div></div>'
        % (esc(_res_dates(e)), esc(e.get("title") or ""),
           ", ".join(x for x in (esc(e.get("employer") or ""), esc(e.get("place") or "")) if x),
           ("<ul class=\"rlines\">%s</ul>" % "".join("<li>%s</li>" % esc(l) for l in (e.get("lines") or [])))
           if (e.get("lines") or []) else "")
        for e in (RESUME_D.get("experience") or []))
    sk = "".join(
        '<div class="rrow"><p class="rwhen">%s</p><div class="rwhat"><p class="rlist">%s</p></div></div>'
        % (esc(g.get("group") or ""), esc(", ".join(g.get("items") or [])))
        for g in (RESUME_D.get("skills") or []) if (g.get("items") or []))
    evid = "".join(
        '<div class="rrow"><p class="rwhen">%s</p><div class="rwhat"><p class="rmeasure">'
        '<span>%d pieces</span><span>%s words</span><span>%d figures</span><span>%d tables</span>%s</p>'
        '<p class="rlist">%s</p></div></div>'
        % (esc(title), e["n"], format(e["words"], ","), e["figures"], e["tables"],
           ("<span>%d %s</span>" % (e["tools"], "tool" if e["tools"] == 1 else "tools")) if e["tools"] else "",
           ", ".join('<a href="%s">%s</a>' % (esc(q["url"]), esc(q["t"]))
                     for q in sorted(e["items"], key=lambda x: -x["words"])[:4])
           + (", and %d more on <a href=\"about.html\">about</a>" % (e["n"] - 4) if e["n"] > 4 else ""))
        for title, e in resume_evidence())
    feats = [p for p in P if p["featured"]][:6]
    sel = "".join(
        '<div class="rrow"><p class="rwhen">%s</p><div class="rwhat"><h3><a href="%s">%s</a></h3>'
        '<p class="rwhere">%s</p><p class="rmeasure"><span>%s words</span><span>%d figures</span>'
        '<span>%d tables</span></p></div></div>'
        % (esc(p["d"]), esc(p["url"]), esc(p["t"]), esc(p["s"]),
           format(p["words"], ","), p["figures"], p["tables"])
        for p in feats)
    w = coop_window()
    avail = esc(COOP_TERM) + ((", %s days from this build" % format(w["days"], ",")) if w and w["days"] > 0 else "")

    def sect(title, body, count=""):
        return ('<section class="band shell rsec">\n'
                '  <div class="sechead"><h2>%s</h2>%s</div>\n%s\n</section>'
                % (esc(title), ('<span class="count">%s</span>' % esc(count)) if count else "", body))

    blocks = []
    if ed:
        blocks.append(sect("Education", ed))
    if ex:
        blocks.append(sect("Experience", ex))
    blocks.append(sect("Capability, and what evidences it", evid,
                       "%d %s" % (len(resume_evidence()),
                                  "claim" if len(resume_evidence()) == 1 else "claims")))
    blocks.append(sect("Selected work", sel, "%d of %d" % (len(feats), len(P))))
    if sk:
        blocks.append(sect("Tools and methods", sk))
    blocks.append(sect("The site itself, measured", (
        '<div class="rrow"><p class="rwhen">The corpus</p><div class="rwhat"><p class="rlist">'
        '%d pieces, %s words, %d figures, %d tables and %s checkpoint questions, every one counted from the '
        'published files by the build rather than typed. %d of them were chosen, scoped and finished without a '
        'course asking for them.</p></div></div>'
        '<div class="rrow"><p class="rwhen">The instrument</p><div class="rwhat">'
        '<p class="rlist register-line">'
        'The site states %d things about itself and checks every one of them on every build; the register on '
        '<a href="controls.html">controls</a> prints %d held, %d untested and %d failed. Each check is itself tested by a '
        'falsification: a change made to a copy of the whole tree that the check must refuse. Every page is opened '
        'in a browser and measured for external requests and for frames requested while idle.</p></div></div>'
        % (len(P), format(TOTAL_WORDS, ","), TOTAL_FIGS, TOTAL_TBLS, format(CHECKPOINTS, ","), N_INDEP,
           reg.get("rows", 0), reg.get("held", 0), reg.get("untested", 0), reg.get("failed", 0)))))

    body = f"""<div class="hero tight shell">
  <p class="eyebrow accent">Resume</p>
  <h1 class="h1">{esc(NAME)}</h1>
  <p class="lede">{esc(", ".join(x for x in ("Accounting and Financial Management, Analytics stream", aff[0] if aff else "") if x))}.
  Standing {esc(STANDING)}. Available for co-op {avail}.</p>
  <p class="rcontact"><a href="mailto:{esc(EMAIL)}">{esc(EMAIL)}</a> <a href="{SITE_URL}">{esc(HOST)}</a>
  {" ".join(profile_links(resume=False))}</p>
  <p class="rprint">Every number below is counted by the build that wrote this page. For a PDF, print this page:
  it is laid out for paper and carries no navigation there.</p>
</div>
{chr(10).join(blocks)}
"""
    return head(f"Resume · {SHORT}",
                f"Resume of {NAME}: Accounting and Financial Management, Analytics stream at Waterloo, with the "
                f"portfolio evidence counted by the build rather than claimed.",
                "resume.html") + body + foot()


def page_selected():
    """The six pieces recorded as featured, each read against the same eight
    slots. Every slot that is filled points at something that already exists:
    a heading the piece carries, a document the corpus records a link to, or a
    value this build computed. Nothing here is a new sentence about the work."""
    feats = [p for p in P if p["featured"]][:6]
    cov = case_coverage()
    entries = "\n".join(case_entry(i, p) for i, p in enumerate(feats, 1))
    w = sum(p["words"] for p in feats)
    f = sum(p["figures"] for p in feats)
    t = sum(p["tables"] for p in feats)
    body = f"""<div class="hero tight shell">
  <p class="eyebrow accent">Selected work</p>
  <h1 class="h1">The strongest pieces, put through one shape.</h1>
  <p class="lede">The {len(feats)} pieces recorded as featured, {w:,} words, {f} figures and {t} tables between them,
  each put through one shape: question, context, approach, evidence, build, finding, limitation, artifact.
  A slot is filled only by something already on the site, and {cov["gap"]} of {cov["slots"]} are not filled at all.
  The whole corpus is on <a href="library.html">Work</a>.</p>
</div>
<section class="shell stack-end">
  <p class="caselead">{cov["slots"]} slots over {cov["pieces"]} pieces: {cov["sec"]} answered by a section,
  {cov["doc"]} by a linked document, {cov["rec"]} by a record, {cov["gap"]} not carried.
  <a href="#casenotes">How a slot is filled &#8595;</a></p>
{entries}
  <div class="casenote" id="casenotes">
    <h2>Notes on the reading</h2>
    <p><b>How to read a row.</b> A slot marked <i>section</i> quotes a heading the piece itself carries and opens
    the piece at it. A slot marked <i>linked document</i> names another piece the corpus records a link to.
    The rest print a value this build already holds: the line the piece declares it was built from, or
    the artifact itself. A slot nothing answers says <i>not carried</i>, and is counted.</p>
    <p><b>What is measured and what is not.</b> The counts, the links and the figure on each entry are measured.
    Which heading answers which slot is a reading, declared in <code>content/cases.json</code>. The build checks
    that every anchor exists, that every heading is quoted as the invariance record holds it, and that every
    named document is a recorded link; it does not check that the reading is the right one. Disagree with a
    placement and the file is the place to say so.</p>
  </div>
</section>
"""
    return head(f"Selected work · {SHORT}",
                f"Six featured pieces by Alex Rajcoomar read against one shape: question, context, approach, "
                f"evidence, build, finding, limitation, artifact, every slot pointing at the piece's own record.",
                "selected.html") + body + foot()


def shelf_row(k, p, extra="", fp=False):
    """A full statement row for a shelf or the library: the title, the
    owner's one-line subtitle, the declared rule from the demo field verbatim
    or the computed absence, the three figures, and whatever the shelf lifts
    beside the piece. The data attributes are the library's filter and sort
    contract in site.js."""
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"])
    hay = " ".join([p["t"], p["s"], p["blurb"], " ".join(p["tags"]), p["k"], p["c"],
                    SURF_LABEL[p["surface"]]]).lower()
    rule = (f'<p class="rule">{esc(p["demo"])}</p>' if p.get("demo")
            else '<p class="rule none">No declared rule on file.</p>')
    mins = f'<span class="s-min">{piece_mins(p)} min</span>' if piece_mins(p) else ""
    fig = f'<div class="sr-f" data-fp="{p["slug"]}">{piece_fingerprint(p)}</div>' if fp else ""
    return f"""      <li data-kind="{p['k'].lower()}" data-course="{esc(p['c'])}" data-surface="{p['surface']}" data-search="{esc(hay)}" data-words="{p['words']}" data-figs="{p['figures']}" data-title="{esc(p['t'].lower())}">
        <div class="srow">
          <div class="sr-t">
            <span class="num tnum">{k:02d}</span>
            <h3><a href="{p['url']}">{esc(p['t'])}</a></h3>
            <p class="s">{esc(p['s'])}</p>
            {rule}
            <p class="meta">{kind_chip(p)}{surf(p)}{mins}<span class="metadate">{esc(p['d'])}</span>{tags}</p>
            {extra}
          </div>
          <div class="sr-n"><span class="tnum">{md(p['words'], 'words', p['slug'])}</span><span class="tnum">{md(p['figures'], 'figures', p['slug'], str(p['figures']))}</span><span class="tnum">{md(p['tables'], 'tables', p['slug'], str(p['tables']))}</span></div>
          {fig}
        </div>
      </li>"""

# The four columns of the statement and the glyph that says what each one is.
# The piece is the source, the words are the observation, the figures are the
# transformations the argument declares, and the tables are where it was put
# under load. The glyphs are the package's own, drawn at the size their
# authored stroke still holds an edge.
STMT_COLS = (("Piece", "source"), ("Words", "evidence"),
             ("Figures", "method"), ("Tables", "tested"))


def _col(label, glyph):
    return ('<span class="stcol">%s<span class="stlab">%s</span></span>'
            % (marks_mod.glyph_svg(glyph, "head"), label))


def shelf_list_head(fp=False):
    cells = "".join(f"<span>{_col(l, g)}</span>" for l, g in STMT_COLS[1:])
    tail = ('<div class="sr-f">%s</div>' % _col("Figure", "linked")) if fp else ""
    return ('      <li class="sr-head" aria-hidden="true"><div class="srow"><div class="sr-t">'
            + _col(*STMT_COLS[0]) + '</div>'
            f'<div class="sr-n">{cells}</div>{tail}</div></li>')

def shelf_subtotal(label, items, href=None, fp=False):
    w = sum(p["words"] for p in items); f = sum(p["figures"] for p in items); t = sum(p["tables"] for p in items)
    lab = f'<a href="{href}">{esc(label)}</a>' if href else esc(label)
    # the verified glyph on the subtotal: two scales at different pitch, and
    # the reading is where they coincide. These three figures have to coincide
    # with the corpus line, and check 12 fails the build when they do not.
    tail = (f'<div class="sr-f">{marks_mod.glyph_svg("verified", "head")}</div>') if fp else ""
    return (f'      <li class="sr-sub"><div class="srow"><div class="sr-t">{lab}</div>'
            f'<div class="sr-n"><span class="tnum">{n(w)}</span><span class="tnum">{f}</span>'
            f'<span class="tnum">{t}</span></div>{tail}</div></li>')

# figures lifted out of pieces, shown beside the piece they belong to
# Which of the six verification glyphs each lifted figure carries. The
# boundary drawing states a rule and applies it, so it is a method; the
# vintage drawing carries two measured valuations side by side without
# reconciling them, so it is evidence.
LIFT_GLYPH = {"whose-losses-count": "method", "the-trillion-dollar-vintage": "evidence"}
LIFTS = {
    "whose-losses-count": ("fs-wlc", "Blue is inside the number, red is outside",
        "Seven literatures making the same boundary decision, drawn on one vertical rule. Whatever falls to the right of it is real and appears on no ledger. Open outlines are results not distinguishable from zero, drawn at full size rather than shrunk away."),
    "not-significant": ("fs-ns1", "Solid reaches a ledger, open does not",
        "Deceive an investor and the market takes 7.53 times what the law does. Injure a stranger who does not trade with you and the share price moves 0.24 per cent, which is not significant. The essay is built on that gap."),
    "the-trillion-dollar-vintage": ("fs-tv1", "The fork is never closed",
        "Two ways of pricing the same vintage, 2.3 times apart, carried side by side to the end rather than averaged. The refused marker between them is the point: no instrument measured that value, so nothing is drawn there."),
    "predictive-history": ("fs-ph1", "An interval that overlaps is not a difference",
        "The obvious reading is that writing a verdict rubric lifted agreement from 53 per cent to 96. It did not. Only the second and third rows hold the record constant, and between those two the rubric is worth four points with the intervals overlapping. The other forty-three points are the record and the number of raters, which is a different claim entirely."),
}

def identity_block():
    aff = S.get("affiliation") or []
    uni = esc(aff[0]) if aff else ""
    school = esc(aff[1]) if len(aff) > 1 else ""
    st = f'<b>{esc(STANDING)}</b>, ' if STANDING else ""
    standing = (f'<p class="standing">{st}<span class="ph">Accounting and Financial Management (Analytics)'
                + (f', {uni}' if uni else '') + '</span><span class="dt">Accounting and Financial Management, Analytics stream'
                + (f'<br>{school}, {uni}' if (school or uni) else '') + '</span></p>')
    facts = []
    if COOP_TERM:
        facts.append(f'<p class="term">Co-op term: {esc(COOP_TERM)}</p>')
    if GRAD_YEAR:
        facts.append(f'<p class="term">Graduating {esc(GRAD_YEAR)}</p>')
    links = profile_links("") + [f'<a href="mailto:{esc(EMAIL)}">{esc(EMAIL)}</a>']
    return (f'<h1 class="name">{esc(SHORT)}</h1>\n    {standing}\n    '
            + "\n    ".join(facts) + (chr(10) + "    " if facts else "")
            + f'<p class="links">{"".join(links)}</p>\n'
            f'    <p class="thesis">{S["headline"]}</p>\n'
            f'    <p class="method">Every figure below is counted from the published files by the build, never typed. '
            f'The notes define each column and state every exception.</p>\n'
            # The same four totals the statement's last row carries, printed
            # where a reader on a phone reaches them: the table's own total
            # is a screen and a half down once every row keeps its
            # description, and this is the one line a thirty-second reader
            # gets. Same variables as the total row, so the two cannot drift.
            f'    <p class="tot"><b>{len(P)} pieces</b> &middot; {n(TOTAL_WORDS)} words '
            f'&middot; {TOTAL_FIGS} figures &middot; {TOTAL_TBLS} tables</p>')

def google_font_families():
    """Which family each of the pieces that load Google Fonts asks for, read
    from the link in the piece itself."""
    fams = {}
    for p in P:
        try:
            t = open(os.path.join(OUT, p["url"]), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        if "fonts.googleapis" not in t:
            continue
        found = []
        for href in re.findall(r'href="([^"]*fonts\.googleapis[^"]*)"', t):
            for fam in re.findall(r"family=([^&:\"]+)", html.unescape(href)):
                found.append(fam.replace("+", " ").strip())
        fams[p["slug"]] = sorted(set(found)) or ["a family the link does not name"]
    return fams

SURF_LABEL = {"independent":"Independent","course":"Coursework","personal":"Personal"}

def surf(p):
    return f'<span class="surf surf-{p["surface"]}">{SURF_LABEL[p["surface"]]}</span>'

def piece_mins(p):
    """The derived reading time, or None. A Tool carries none whatever its
    length: sig() has always printed "Interactive ... runs in the browser"
    for one, because a drill has no length, only a session. The word
    threshold is the colophon's."""
    return None if p["k"] == "Tool" else p["mins"]

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
    # The Atlas joins a metadata line with a middot and the .tag list on
    # this page already did too. The slash was the only third separator
    # on the site, so it goes.
    line = '<i aria-hidden="true">&middot;</i>'.join(f'<span>{b}</span>' for b in bits)
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

def feature(p, delay=0, h=3):
    # The whole card stays clickable through the stretched title link, but the
    # link itself is the title, so a screen reader's link list announces a
    # name rather than the card's entire text: the old whole-card anchor made
    # the ~90-word blurb part of every link's accessible name.
    # The heading level is a parameter because the same card sits under an h2
    # band head on most pages and under an h3 course head on coursework.html,
    # where an h3 card would read as the course's sibling rather than its
    # member.
    return f"""      <article class="feature" style="transition-delay:{delay}ms">
        <span class="kindrow">{kind_chip(p)}{surf(p)}</span>
        <h{h}><a class="cardlink" href="{p['url']}">{esc(p['t'])}</a></h{h}>
        <p>{esc(p['blurb'])}</p>
        {sig(p, with_surface=False)}
        <span class="go">Open <span class="arrow" aria-hidden="true">&#8594;</span></span>
      </article>"""


def feature_compact(p, delay=0):
    # The home page is the skim surface, so its cards carry the standfirst
    # rather than the full blurb; the blurbs stay on the section pages and in
    # the library, one click away, where the reader has chosen depth.
    return f"""      <article class="feature feature-c" style="transition-delay:{delay}ms">
        <span class="kindrow">{kind_chip(p)}{surf(p)}</span>
        <h3><a class="cardlink" href="{p['url']}">{esc(p['t'])}</a></h3>
        <p>{esc(p['s'])}</p>
        {sig(p, with_surface=False)}
        <span class="go">Open <span class="arrow" aria-hidden="true">&#8594;</span></span>
      </article>"""


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
    # The source page wires its .hit groups to a tooltip script that the
    # shell does not carry, so the lifted copy must not promise interaction
    # it cannot deliver: no tab stop, no nested img role inside the figure's
    # own img role, and no aria-label either, which is prohibited on a plain
    # group. The figure's own label and caption carry the description.
    svg = re.sub(r'<g class="hit" tabindex="0" role="img" aria-label="[^"]*"',
                 '<g class="hit"', svg)
    return svg

FIG_NEUTRAL = re.compile(r"^--(gridline|baseline|rule(-\w+)?|text-\w+|surface-\d|ink(-\d)?|sans|paper|axis)$")


def figure_colour_vars(fid):
    """The colour variables a lifted figure's marks use, less the neutral ones
    (grid, rules, text, surfaces): the colours that carry a meaning."""
    d = STRIP[fid]
    used = set(re.findall(r"var\((--[\w-]+)\)", (d.get("css") or "") + d.get("svg", "")))
    return {v for v in used if not FIG_NEUTRAL.match(v)}


def figure_numbers(svg):
    """Every line of visible text in a figure that carries a numeral: the
    text elements, with styles, titles and descriptions left out."""
    body = re.sub(r"<(style|title|desc|script)\b[^>]*>.*?</\1>", " ", svg, flags=re.S | re.I)
    out = []
    for t in re.findall(r"<text\b[^>]*>(.*?)</text>", body, re.S):
        line = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))).strip()
        if line and re.search(r"\d", line) and line not in out:
            out.append(line)
    return out


def figure_key(fid):
    """The colours that carry a meaning, each named in words beside a swatch,
    from the meanings figures.json declares; check 30 holds the declaration
    to the variables the marks use and this key to the declaration."""
    means = STRIP[fid].get("meanings") or {}
    if not means:
        return ""
    items = "".join(f'<span class="fk-item" data-var="{esc(v)}"><i class="sw" style="background:var({esc(v)})" aria-hidden="true"></i>{esc(w)}</span>'
                    for v, w in means.items())
    return f'<p class="fkey">{items}</p>'


def restated_block(svg, href):
    """The numbers a drawing carries, restated as text under it so that no
    number is carried by the drawing alone; check 31 holds every numeral in
    the figure's text to the page's text outside it, and check 13 holds the
    restatement to the piece the figure was lifted from."""
    lines = figure_numbers(svg)
    if not lines:
        return ""
    for line in lines:
        CAPTIONS.append((line, href))
    return ('<details class="fignums"><summary>The numbers this figure draws</summary><p>'
            + " &middot; ".join(esc(x) for x in lines) + "</p></details>")


def figure_restated(fid, href):
    return restated_block(STRIP[fid].get("svg", ""), href)


def lifted(fid, rule, title, note, href, glyph=None):
    CAPTIONS.append((rule + " " + note, href))
    """A figure lifted out of its own document together with the CSS rules its
    classes depend on, shown at the size it was drawn for. The glyph on the
    rule line says what kind of claim the drawing is making, which is the one
    thing the drawing itself cannot say."""
    d = STRIP[fid]
    gl = (f'<span class="glrule">{marks_mod.glyph_svg(glyph)}'
          f'<span class="gllab">{esc(marks_mod.GLYPHS[glyph][1])}</span></span>') if glyph else ""
    return f"""    <figure class="spec" id="{fid}">
      <div class="frame">{strip_svg(fid)}</div>
      <figcaption>
        <div class="who">
          {gl}
          <p class="rule">{esc(rule)}</p>
          <h3>{esc(title)}</h3>
        </div>
        <div class="what">
          <p>{esc(note)}</p>
          {figure_key(fid)}
          {figure_restated(fid, href)}
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

    # role="group", not "img": an img role marks its descendants
    # presentational, and every row in this drawing is a real link. A group
    # keeps the label and leaves the links to be what they are.
    out = [f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="100%" role="group" '
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

def tools_drawn():
    """Which interactive tools reach the drawing floor. Three render a full
    document on load and are drawn like one; the caption used to say none
    were, which the drawing itself contradicted."""
    drawn = [p for p in P if p["k"] == "Tool" and p["is_doc"]]
    undrawn = [p for p in P if p["k"] == "Tool" and not p["is_doc"]]
    return drawn, undrawn

def corpus_table():
    docs = [p for p in P if p["is_doc"]]
    t_drawn, t_undrawn = tools_drawn()
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
                        f'<td class="tnum">{md(p["words"], "words", p["slug"])}</td></tr>')
    return (f'<table class="ctab"><caption>Every document at or above {DOC_MIN:,} rendered words, with the word count each square is drawn from. '
            f'{len(t_drawn)} of the {N_TOOLS} interactive tools reach that floor and are drawn; the other {len(t_undrawn)} hold their content in code rather than prose and are not.</caption>'
            '<thead><tr><th scope="col">Piece</th><th scope="col">Kind</th>'
            '<th scope="col" class="tnum">Words</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table>')

def group_totals():
    """Words per origin over the documents the corpus figure draws, which is
    every piece at or above DOC_MIN words. This is the drawing's own total and
    it excludes the undrawn pieces by construction; the statement's subtotals
    come from surface_totals() below, which excludes nothing."""
    docs = [p for p in P if p["is_doc"]]
    return {k: sum(p["words"] for p in docs if p["surface"] == k) for k, _, _ in GROUPS}


def surface_totals():
    """Pieces, words, figures and tables per origin over all listed pieces. The
    three rows add to the corpus line exactly, and a check refuses the build
    if they ever stop doing so; this is what every page that names an origin
    total prints, so the same quantity cannot carry two values."""
    out = {}
    for k, _, _ in GROUPS:
        xs = [p for p in P if p["surface"] == k]
        out[k] = {"n": len(xs), "words": sum(p["words"] for p in xs),
                  "figures": sum(p["figures"] for p in xs),
                  "tables": sum(p["tables"] for p in xs)}
    return out


class _FigsShim:
    UNIT = UNIT
    corpus_svg = staticmethod(corpus_svg)
    corpus_table = staticmethod(corpus_table)
    group_totals = staticmethod(group_totals)
    surface_totals = staticmethod(surface_totals)
figs = _FigsShim()
ST = surface_totals()

TRANSCRIPT_WORDS = sum(METRICS[k].get("words", 0) for k in METRICS if k not in {p["slug"] for p in P})

def exceptions():
    """Every way the site's own rules are not the whole story, counted from
    the files rather than remembered: pieces that load a typeface from Google
    Fonts, pieces under the drawing floor, transcripts measured but not
    listed, and the tools that stand on two shelves."""
    fonts, kinds = [], {"md": 0, "doc": 0}
    for p in P:
        path = os.path.join(OUT, p["url"])
        try:
            t = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        if "fonts.googleapis" in t:
            fonts.append(p)
        m = re.search(r"<!--__docend (md|doc)-->", t)
        if m:
            kinds[m.group(1)] += 1
        elif "Converted from my own Word document" in t:
            kinds["doc"] += 1
        elif "Converted from my own markdown note" in t:
            kinds["md"] += 1
    undrawn = [p for p in P if not p["is_doc"]]
    listed = {p["slug"] for p in P}
    transcripts = sorted(k for k in METRICS if k not in listed)
    return {"fonts": fonts, "undrawn": undrawn,
            "undrawn_words": sum(p["words"] for p in undrawn),
            "transcripts": transcripts, "kinds": kinds,
            "tools": [p for p in P if p["k"] == "Tool"]}

# Every caption the shell lifts out of a piece is registered here with the
# piece it cites, so the numeral check can hold the caption to the piece's
# own text rather than trusting the template.
CAPTIONS = []

# ------------------------------------------------------------ pages ----
def eyebrow_chip():
    """The standing and the owner's own eyebrow line, as one chip."""
    st = f'<b>{esc(STANDING)}</b> ' if STANDING else ""
    return f'<p class="eyeb">{st}{esc(S["eyebrow"])}</p>'

def hero_identity():
    """Who this is, in four lines: the same fields identity_block() prints,
    laid out for the stage. Every optional line renders nothing when its
    value is empty, so no placeholder can look production-ready."""
    aff = S.get("affiliation") or []
    uni = esc(aff[0]) if aff else ""
    school = esc(aff[1]) if len(aff) > 1 else ""
    where = ", ".join(x for x in (school, uni) if x)
    facts = []
    if COOP_TERM:
        facts.append(f'<p class="term">Co-op term: {esc(COOP_TERM)}</p>')
    if GRAD_YEAR:
        facts.append(f'<p class="term">Graduating {esc(GRAD_YEAR)}</p>')
    links = profile_links("") + [f'<a href="mailto:{esc(EMAIL)}">{esc(EMAIL)}</a>']
    return (f'<div class="ident">\n'
            f'      <h1 class="name">{esc(SHORT)}</h1>\n'
            f'      <p class="standing"><span class="ph">Accounting and Financial Management (Analytics)'
            + (f', {uni}' if uni else '') + '</span><span class="dt">Accounting and Financial Management, Analytics stream'
            + (f'<br>{where}' if where else "") + '</span></p>\n      '
            + "\n      ".join(facts) + ("\n      " if facts else "")
            + f'<p class="links">{"".join(links)}</p>\n    </div>')

# Three doorways, for the three reasons a stranger opens this site. Each one
# points at a surface that already exists and says what is behind it in the
# fewest words that are still true. Kept to one row: a reader who wants the
# site as it was scrolls past a single line.
DOORS = [
    ("selected.html", "Hiring me"),
    ("library.html",  "Reading the research"),
    ("colophon.html", "How this is built"),
]


def start_here():
    """One line under the corpus figures. The labels carry the whole of it:
    a description under each one wrapped the row onto three broken lines at
    every width the hero column actually takes, and each destination opens
    with a lede that says the same thing better."""
    items = "\n        ".join(
        '<a href="%s">%s <span aria-hidden="true">&#8594;</span></a>' % (esc(u), esc(t))
        for u, t in DOORS)
    return ('<nav class="startrow" aria-label="Start here">\n'
            '      <p class="startlab">Start here</p>\n'
            '      <p class="startlinks">\n        %s\n      </p>\n    </nav>' % items)


def now_line():
    """Where the author is, from values the site already records: the standing
    in content/pieces.json, the co-op term counted from this build's date, and
    the day the corpus was last measured. The optional sentence renders only
    when it has been written, so nothing here can read as a placeholder."""
    bits = []
    if STANDING:
        bits.append("<div><b>Term</b><span>%s, %s</span></div>"
                    % (esc(STANDING), esc(TODAY.strftime("%B %Y"))))
    w = coop_window()
    if w:
        bits.append("<div><b>Next co-op</b><span>%s, %s day%s from this build</span></div>"
                    % (esc(COOP_TERM), format(w["days"], ","), "" if w["days"] == 1 else "s"))
    elif COOP_TERM:
        bits.append("<div><b>Next co-op</b><span>%s</span></div>" % esc(COOP_TERM))
    bits.append('<div><b>Last measured</b><span>%s, %s pieces and %s words, by the build that '
                'wrote this page</span></div>'
                % (esc(TODAY.isoformat()), len(P), format(TOTAL_WORDS, ",")))
    nw = (S.get("now") or "").strip()
    if nw:
        bits.append("<div><b>Building</b><span>%s</span></div>" % esc(nw))
    return '<div class="facts measure wide pane nowpane">%s</div>' % "".join(bits)


def corpus_line():
    """The corpus in four figures, each the same variable the statement's
    total row prints, so the two cannot drift. A definition list, because
    each cell is a label and its value."""
    cells = (("Pieces", md(len(P), "pieces")), ("Words", md(TOTAL_WORDS, "words")),
             ("Figures", md(TOTAL_FIGS, "figures")), ("Tables", md(TOTAL_TBLS, "tables")))
    return ('<dl class="corpusline">' + "".join(
        f'<div><dt>{a}</dt><dd class="tnum">{b}</dd></div>' for a, b in cells) + '</dl>')

def sect_head(num, title, note="", count="", hid=None):
    """A section head in the home grammar: the index of the section in the
    sequence, the title, an optional note, and an optional count at the
    right. The index is a position, not a quantity, and is cut out before
    the numeral scan like the statement's row numbers."""
    idattr = f' id="{hid}"' if hid else ""
    return (f'<div class="sechead hm">\n'
            f'    <span class="num tnum">{num:02d}</span>\n'
            f'    <h2{idattr}>{title}</h2>\n'
            + (f'    <p class="note">{note}</p>\n' if note else "")
            + (f'    <span class="count">{count}</span>\n' if count else "")
            + '  </div>')

def page_index():
    feats  = [p for p in P if p["featured"]][:6]
    gt = figs.group_totals()
    ex = exceptions()
    fams = google_font_families()
    ATLAS_N, ATLAS_PTS, ATLAS_SHARED = atlas_teaser_bits()
    # the two parallels that bound the zones, as y, for the sphere to draw
    ATLAS_ZONES = ",".join("%.3f" % ATLAS["zones"][z][1] for z in ("independent", "course") if z in ATLAS["zones"])
    F = atlas_facts()
    N_EDGES = len(ATLAS.get("edges", []))
    n_undrawn = len(ex["undrawn"])

    rows = []
    for p in feats:
        lift = flagged_lift(p) if p["slug"] == "flagged-in-hindsight" else None
        rows.append(stmt_row(p, lift))
    n_feat_ind = sum(1 for p in feats if p["surface"] == "independent")
    ind = ST["independent"]
    more = ind["n"] - n_feat_ind
    subs = [
        stmt_subrow(f"Independent, {ind['n']}", ind, "research.html", 2),
        stmt_subrow(f"Coursework, {ST['course']['n']}", ST["course"], "coursework.html", 2),
        stmt_subrow(f"Personal, {ST['personal']['n']}", ST["personal"], "library.html#personal", 3),
        stmt_subrow(f"All work, {len(P)} pieces",
                    {"words": TOTAL_WORDS, "figures": TOTAL_FIGS, "tables": TOTAL_TBLS},
                    "library.html", None, cls="total"),
    ]
    # families by count, most pieces first, ties by name
    famcount = {}
    for fs in fams.values():
        for f in fs:
            famcount[f] = famcount.get(f, 0) + 1
    fam_line = ", ".join(f"{esc(f)} on {c}" for f, c in sorted(famcount.items(), key=lambda x: (-x[1], x[0])))
    # the sentence exists only while the count it states is above zero: when
    # every typeface is self-hosted the exception is gone, not reworded
    fonts_sentence = (f"{len(ex['fonts'])} pieces load a typeface from Google Fonts, {fam_line}; "
                      f"everything else on the site makes no external request."
                      if ex["fonts"] else
                      "No piece loads a typeface from another origin; nothing on the site makes an external request.")

    # two figures lifted from their pieces, each with the rule the shelf gives it
    figs_html = "\n".join(
        lifted(LIFTS[slug][0], LIFTS[slug][1], _by_slug_all[slug]["t"], LIFTS[slug][2],
               _by_slug_all[slug]["url"], LIFT_GLYPH.get(slug))
        for slug in ("the-trillion-dollar-vintage", "whose-losses-count") if slug in LIFTS and slug in _by_slug_all)
    tools = [p for p in P if p["k"] == "Tool"]
    # One row per tool, the way the statement lists a piece: a thirty-second
    # reader on a phone gets the whole shelf in a screen, and the seven
    # tiles this replaced cost 1,500px that reader never reached.
    tiles = "\n".join(
        f'      <li><span class="num tnum">{i:02d}</span>'
        f'<div class="tl-t"><h3><a href="{p["url"]}">{esc(p["t"])}</a></h3><p class="s">{esc(p["s"])}</p></div>'
        f'<p class="tl-m">{surf(p)}<span class="tl-run">{"Installs to a phone" if p["pwa"] else "Runs in the browser"}</span></p></li>'
        for i, p in enumerate(tools, 1))
    lifts_count = (f'{len(LIFTS)} lifted on the <a class="inlink" href="research.html">research shelf</a>')

    body = f"""<div class="shell descent">
  <section class="stage" aria-label="Who this is">
    {eyebrow_chip()}
    {hero_identity()}
    <p class="display">{S["headline"]}</p>
    <p class="method">Every figure below is counted from the published files by the build, never typed. The notes define each column and state every exception.</p>
    {corpus_line()}
    {start_here()}
  </section>
  <div class="descent-globe">
    <div class="stage-globe">
      <div class="tease-globe hero-globe" id="atlasmini" data-pts="{ATLAS_PTS}" data-zones="{ATLAS_ZONES}" data-fill="0.44" aria-hidden="true"></div>
      <script type="application/json" id="atlasmini-docs">{atlas_home_links()}</script>
      <div class="globe-card" id="atlasmini-card" hidden><a class="gc-t" href="atlas.html"></a><span class="gc-d"></span></div>
      <p class="globe-cap"><a class="inlink" href="atlas.html">{ATLAS_N} sections, every one a link <span aria-hidden="true">&#8594;</span></a>
        <span class="globe-hint">Point at a mark: chords join its document to the documents its prose links, or that link it. <span class="gc-l">{N_EDGES}</span> such links are recorded.</span>
        <span class="globe-hint-touch">Tap a mark: chords join its document to the documents its prose links, or that link it, and its name opens it. <span class="gc-l">{N_EDGES}</span> such links are recorded.</span></p>
      <p class="facing" aria-live="off"></p>
      <p class="globe-key">Where a mark sits is a rule the build checks: each origin's zone of latitude has the area of its share of the sections, each document is a disc of two thirds of its share's area, settled clear of every other inside its zone, and its sections lie on a spiral inside the disc, the first at the centre and the last at the rim. As a featured row reaches the reading line the sphere turns to face that document.</p>
      <noscript><p class="note">The sphere needs a browser that runs scripts.
      The <a class="inlink" href="atlas.html">full index</a> does not.</p></noscript>
    </div>
  </div>
  <section class="band statement" id="statement" aria-labelledby="stmt-h">
    {sect_head(1, "Statement of work", "Six featured pieces, then every origin, then the whole. As a row reaches the reading line the sphere turns to face that document.", f'<a class="inlink" href="#notes">Notes 1 to 6 &#8595;</a>', "stmt-h")}
    <div class="pane">
      <table class="st">
        {stmt_head_cells()}
        <tbody>
{chr(10).join(rows)}
{chr(10).join(subs)}
        </tbody>
      </table>
    </div>
    <p class="stmore"><a class="inlink" href="selected.html">The featured pieces, each read against the same eight questions <span aria-hidden="true">&#8594;</span></a></p>
  </section>
</div>

<section class="band ground" id="figures" aria-labelledby="fig-h">
  <div class="shell">
  {sect_head(2, "Two figures, lifted from their pieces", "", lifts_count, "fig-h")}
  <div class="figband">
{figs_html}
  </div>
  </div>
</section>

<section class="band shell" id="corpus" aria-labelledby="corpus-h">
  {sect_head(3, 'The statement, drawn to scale <a class="nref" href="#n6">6</a>', "Every document on this site, measured from the files themselves rather than estimated.", f"{TOTAL_WORDS:,} words", "corpus-h")}
  <div class="corpus">
    <a class="skip" href="#corpus-table">Skip the drawing to the table of its numbers</a>
    <div class="plot">
      {figs.corpus_svg()}
    </div>
    <aside class="rail-app" aria-label="How to read the figure">
      <h3>How to read it</h3>
      <p class="scaleread">{marks_mod.glyph_svg("tested")}<span><b>One square is {figs.UNIT} words.</b>
      The square never rescales, so a long piece is long on the page. The unit is a choice, declared once:
      the drawing is held to it rather than fitted to whatever would make the shelf look even.</span></p>
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
        <span><i class="open" aria-hidden="true"></i>Open outline: coursework</span>
        <span><i class="half" aria-hidden="true"></i>Solid, lighter: personal interest</span>
      </div>
      <p>Of the words drawn here, {gt['course']:,} were written for a course, most of it one course
      rebuilt end to end, and {gt['independent']:,} because I wanted the answer and nobody asked for
      them. The {n_undrawn} pieces under the floor are counted in the statement above and not drawn.</p>
      <p><a class="openlink" href="colophon.html">How every number here is measured &#8594;</a></p>
    </aside>
  </div>
  <details class="tv spaced" id="corpus-table">
    <summary>The numbers behind the figure</summary>
    {figs.corpus_table()}
  </details>
</section>

<section class="band ground" id="tools" aria-labelledby="tools-h">
  <div class="shell">
  {sect_head(4, "Interactive tools", f"Things you use rather than read. Each opens and runs in the browser; {N_PWA} install to a phone home screen.", f"{N_TOOLS} tools", "tools-h")}
  <ol class="toolledger">
{tiles}
  </ol>
  </div>
</section>

<section class="notes shell" id="notes" aria-labelledby="notes-h">
  {sect_head(5, "Notes to the statement", "", "", "notes-h")}
  <ol>
    <li id="n1"><b>Basis of measurement.</b> Words are the text of the rendered page after its own scripts have run, with script, style and noscript blocks removed and collapsed answers included. A figure is a top-level drawing covering at least 6,000 square units. A table is a table. All three are counted in a headless browser after the page's own scripts have run. Minutes are the one figure on this page that is derived rather than counted: words divided by {WPM} words per minute, rounded. A page under {DOC_MIN:,} rendered words carries none, and neither does an interactive tool. <a href="colophon.html#definitions">The definitions in full.</a></li>
    <li id="n2"><b>Origin.</b> Independent means I chose the question and finished it without a course asking for it: {ind['n']} pieces, the {n_feat_ind} above and {more} more on the <a href="research.html">research shelf</a>. Coursework means built while taking one of {len(COURSES)} courses, for the assessment that was coming: {ST['course']['n']} pieces, built from my course materials with AI assistance and then verified. Anything built alongside a course is filed as coursework even where the question was my own.</li>
    <li id="n3"><b>Personal.</b> {ST['personal']['n']} pieces read and written for their own sake, with no claim on either shelf. They are counted above and listed in the <a href="library.html#personal">library</a>, not here.</li>
    <li id="n4"><b>Exceptions.</b> {fonts_sentence} {n_undrawn} pieces render under {DOC_MIN:,} words and are counted above but not drawn in the figure; together they hold {ex['undrawn_words']:,} words. {len(ex['transcripts'])} run transcripts are measured but not listed. The {N_TOOLS} interactive tools sit on the shelf of the course or research that produced them and are counted once. <a href="colophon.html#exceptions">The exceptions, by name.</a></li>
    <li id="n5"><b>The index.</b> {F["headN"]:,} section headings and {F["toolN"]} whole tools from the {len(P)} documents, and the author's own anchor: {F["total"]:,} marks placed on one sphere, every mark a link. <a href="atlas.html">The Atlas.</a></li>
    <li id="n6"><b>The drawing.</b> The statement drawn to scale above, one square {figs.UNIT} words, solid for independent work, an open outline for coursework, lighter for personal. The square never rescales, so a long piece is long on the page.</li>
  </ol>
  <div class="prose measure material">
    <h3>A note on the material</h3>
    <p>These are my own artefacts, written by me for my own use. They are not course materials,
    not official solutions, and not a substitute for the standards themselves. Where a figure or a
    rule matters, check the primary source: the CPA Canada Handbook, the Income Tax Act, or the CRA.</p>
  </div>
</section>
"""
    return head(f"{SHORT} · portfolio",
                f"Research, study tools and references by Alex Rajcoomar, Accounting "
                f"and Financial Management at Waterloo. {len(P)} pieces, "
                f"{TOTAL_WORDS:,} words, all of them running.",
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
    iw = sum(p["words"] for p in items)
    n_essay = sum(1 for p in items if p["k"] == "Essay")
    n_ref   = sum(1 for p in items if p["k"] == "Reference")
    n_tool  = sum(1 for p in items if p["k"] == "Tool")
    rows = [shelf_list_head()]
    for k, p in enumerate(items, 1):
        extra = ""
        if p["slug"] in LIFTS:
            fid, rule, note = LIFTS[p["slug"]]
            extra = lifted(fid, rule, p["t"], note, p["url"])
        spec = SPECIMEN_OF.get(p["slug"])
        if spec:
            CAPTIONS.append((spec[1], p["url"]))
            extra += (f'<div class="specimen" id="{spec[0]}"><div class="fig">{fit(spec[0])}</div>'
                      f'<p class="figcap">{esc(spec[1])}</p>{restated_block(SPECS[spec[0]]["svg"], p["url"])}</div>')
        rows.append(shelf_row(k, p, extra))
    rows.append(shelf_subtotal(f"Independent, {len(items)} pieces", items))
    body = f"""<div class="hero tight shell">
  {section_eyebrow("research.html")}
  <h1 class="h1">Research and writing</h1>
  <p class="lede">{len(items)} pieces where the argument is the point. Every one of them started because
  I did not believe a claim, or could not find two jurisdictions held apart properly, and the fastest
  way to find out was to build the thing. {iw:,} words, none of them assigned. The order is mine; the
  figures are the build's.</p>
{section_guide("research.html")}
</div>
<section class="band shell">
  <div class="sechead">
    <h2>The independent shelf</h2>
    <p class="note">The statement, filtered to the work nobody assigned. Each row carries the piece's own
    declared rule, verbatim from the record, and the figures lifted from four of them.</p>
    <span class="count">{len(items)} of {len(P)}</span>
  </div>
  <ol class="index stmt-list">
{chr(10).join(rows)}
  </ol>
</section>
"""
    return head(f"Research and writing \u00b7 {SHORT}",
                f"{len(items)} independent research pieces by Alex Rajcoomar: {n_essay} essays, "
                f"{n_ref} references and {n_tool} tool{'s' if n_tool != 1 else ''}, "
                f"{iw:,} words, every figure carrying its source.",
                "research.html") + body + foot()

def page_tools():
    items = [p for p in P if p["k"] == "Tool"]
    n_drill = sum(1 for p in items if not p["is_doc"])
    n_full  = len(items) - n_drill
    rows = [shelf_list_head()] + [shelf_row(k, p) for k, p in enumerate(items, 1)]
    rows.append(shelf_subtotal(f"Tools, {len(items)} pieces, counted once on their own shelves", items))
    body = f"""<div class="hero tight shell">
  {section_eyebrow("tools.html")}
  <h1 class="h1">Interactive tools</h1>
  <p class="lede">{len(items)} things you use rather than read. {N_PWA} of them install to a phone home
  screen. {n_drill} are drill engines that hold their question banks in code, so they carry no reading
  time: a drill has no length, only a session. The other {n_full} render{'s' if n_full == 1 else ''} a full document on load and
  {'is' if n_full == 1 else 'are'} measured like one.</p>
{section_guide("tools.html")}
</div>
<section class="band shell">
  <div class="sechead"><h2>The tools</h2><p class="note">Each opens and runs in the browser. Every tool also stands on the shelf of the course or research that produced it, and every total counts it once.</p><span class="count">{len(items)} tools</span></div>
  <ol class="index stmt-list">
{chr(10).join(rows)}
  </ol>
</section>
<section class="band ground">
  <div class="shell">
  <div class="sechead"><h2>Installing one</h2><span class="count">How to</span></div>
  <div class="prose measure">
    <p>On a phone, open the tool and choose <em>Add to Home Screen</em> from the share menu. It gets an
    icon and opens without browser chrome. Progress is stored in that browser only: nothing is
    uploaded, and clearing site data clears the progress with it.</p>
  </div>
  </div>
</section>
"""
    return head(f"Interactive tools \u00b7 {SHORT}",
                f"{len(items)} interactive study tools built by Alex Rajcoomar, {N_PWA} of them installable to a phone home screen.",
                "tools.html") + body + foot()

# The sentinel admin.html tells the owner to write when a piece has no
# recorded provenance. It is already a whole sentence, so the label would
# read "Built from Not declared on file."; it stands alone instead. This is
# the one branch, not a general strip: everywhere else the field is the
# complement of the label and check 17 holds it to that.
NOT_DECLARED = "Not declared on file."

def built_from_counts(items):
    """From the built_from lines: how many name AI assistance, how many
    declare no source on file. Counted from the field, never typed."""
    n_ai = sum(1 for p in items if "AI assistance" in (p.get("built_from") or ""))
    n_nd = sum(1 for p in items if (p.get("built_from") or "").strip() == NOT_DECLARED)
    return n_ai, n_nd

def page_coursework():
    items = [p for p in P if p["surface"] == "course"]
    n_ai, n_nd = built_from_counts(items)
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
    k = 0
    for c in COURSES:
        cs = [p for p in items if p["c"] == c]
        rows = [shelf_list_head()]
        for p in cs:
            k += 1
            rows.append(shelf_row(k, p))
        rows.append(shelf_subtotal(f"{c}, {len(cs)} piece{'s' if len(cs) != 1 else ''}", cs))
        groups.append(f"""  <details class="cgroup" open>
    <summary class="grouphead"><h3>{esc(c)}</h3>
    <p class="gnote">{len(cs)} piece{'s' if len(cs)!=1 else ''}, {sum(p['words'] for p in cs):,} words.</p>
    <span class="gcount">{len(cs)}</span></summary>
  <ol class="index stmt-list">
{chr(10).join(rows)}
  </ol>
  </details>""")
    body = f"""<div class="hero tight shell">
  {section_eyebrow("coursework.html")}
  <h1 class="h1">Coursework</h1>
  <p class="lede">{len(items)} pieces across {len(COURSES)} courses, each one built while taking the course
  rather than afterwards. Built from my course materials, {n_ai} of the {len(items)} with AI assistance,
  then verified against the course materials; each piece states on its own bar what it was built from,
  and {n_nd} of them declare no source on file. References are organised for retrieval under time pressure,
  not for reading front to back, which is why several of them are deliberately compressed to what fits on a page.</p>
{section_guide("coursework.html")}
</div>
<section class="band ground">
  <div class="shell">
  <div class="sechead"><h2>Coverage</h2><p class="note">What exists per course, counted from the files themselves.</p><span class="count">{len(items)} of {len(P)}</span></div>
  <p class="note measure prose">Word counts exclude the question banks inside the interactive
  tools, because those live in code rather than prose, so the tool-heavy courses read lower than they are.
  The remaining {len(P)-len(items)} pieces are not tied to one course: {N_INDEP} under
  <a href="research.html">research</a> and the {N_PERSONAL} read for
  their own sake in the <a href="library.html#personal">library</a>.</p>
  <div class="pane"><div class="tw"><table class="ctab">
    <thead><tr><th scope="col">Course</th><th scope="col" class="tnum">Interactive</th>
    <th scope="col" class="tnum">References</th><th scope="col" class="tnum">Total</th>
    <th scope="col" class="tnum">Words</th></tr></thead>
    <tbody>{''.join(rows_c)}</tbody>
  </table></div></div>
  </div>
</section>
<section class="band shell">
  <div class="sechead"><h2>By course</h2><p class="note">The statement, filtered to each course, in the order the pieces were published.</p><span class="count">{len(COURSES)} courses</span></div>
{chr(10).join(groups)}
</section>
"""
    return head(f"Coursework \u00b7 {SHORT}",
                f"{len(items)} references and trainers across {len(COURSES)} courses, with a coverage table counted from the files.",
                "coursework.html") + body + foot()

def page_library():
    order = ["independent", "course", "personal"]
    notes = {
      "independent": "Chosen, scoped and finished without a course asking for it.",
      "course": "Built while taking the course, for the assessment that was coming.",
      "personal": "Read and written for its own sake. Reachable here, and only here.",
    }
    k = 0; blocks = []
    for key in order:
        items = [p for p in P if p["surface"] == key]
        if not items: continue
        w = sum(p["words"] for p in items)
        rows = [shelf_list_head(fp=True)]
        for p in items:
            k += 1
            rows.append(shelf_row(k, p, fp=True))
        rows.append(shelf_subtotal(f"{SURF_LABEL[key]}, {len(items)} pieces", items, fp=True))
        blocks.append(f"""  <section class="lgroup" data-group="{key}" id="{key}">
    <div class="grouphead"><h2>{SURF_LABEL[key]}</h2>
      <p class="gnote">{esc(notes[key])}</p>
      <span class="gcount">{len(items)} pieces &middot; {w:,} words</span></div>
    <ol class="index stmt-list stmt-fig">
{chr(10).join(rows)}
    </ol>
  </section>""")

    body = f"""<div class="hero tight shell">
  <p class="eyebrow accent">Work</p>
  <h1 class="h1">The whole statement.</h1>
  <p class="lede">All {len(P)} pieces, split by what asked for them, every row carrying the piece's
  measured words, figures and tables and its own declared rule. The three origins add to the corpus
  line, {TOTAL_WORDS:,} words, and the <a href="colophon.html">notes</a> define each column.
  For fewer of them in more depth, the featured pieces are read one shape at a time on
  <a href="selected.html">selected work</a>.</p>
</div>
<section class="shell stack-end">
  <div class="tools-bar">
    <label class="sr" for="q">Search the library</label>
    <input id="q" type="search" placeholder="Search {len(P)} pieces" autocomplete="off" spellcheck="false">
    <div class="chipset" id="chips" role="group" aria-label="Filter by kind">
      <button class="chip" type="button" data-f="all" aria-pressed="true">All</button>
      <button class="chip" type="button" data-f="essay" aria-pressed="false">Essays</button>
      <button class="chip" type="button" data-f="tool" aria-pressed="false">Tools</button>
      <button class="chip" type="button" data-f="reference" aria-pressed="false">References</button>
    </div>
    <div class="chipset" id="chips-surface" role="group" aria-label="Filter by what asked for the work">
      <button class="chip" type="button" data-f="all" aria-pressed="true">Any origin</button>
      <button class="chip" type="button" data-f="independent" aria-pressed="false">Independent</button>
      <button class="chip" type="button" data-f="course" aria-pressed="false">Coursework</button>
      <button class="chip" type="button" data-f="personal" aria-pressed="false">Personal</button>
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
    return head(f"Work \u00b7 {SHORT}",
                f"All {len(P)} pieces by Alex Rajcoomar as one statement of work: measured words, figures and tables on every row, split by origin.",
                "library.html") + body + foot()

def profile_links(css="inlink", resume=True):
    """The optional recruiter links, each rendered only where a value
    exists in pieces.json's site block."""
    out = []
    if LINKEDIN:
        out.append(f'<a class="{css}" href="{esc(LINKEDIN)}">LinkedIn</a>')
    if GITHUB:
        out.append(f'<a class="{css}" href="{esc(GITHUB)}">GitHub</a>')
    # an external resume when one is recorded, and otherwise the page this
    # build writes, which is always current because it is generated. The
    # resume's own contact line asks for it off: a link to the page you are
    # reading is furniture, not a link.
    if resume:
        out.append(f'<a class="{css}" href="{esc(RESUME) if RESUME else "resume.html"}">Resume</a>')
    return out


# The four things the portfolio demonstrates. The paragraphs are the owner's,
# moved here unchanged so the blocks can be generated with their evidence
# attached; content/capabilities.json says which pieces evidence which.
CAP_BLOCKS = [
    ("evidence", "Evidence discipline",
     "<p>Every figure carries the provenance tag it was published under. "
     "Derived numbers are labelled as derived. Two sources that disagree are reported separately instead of "
     "averaged. One essay reaches a negative result and reports it as one, and the largest piece corrects its "
     "own arithmetic in public where a later attribution changed the base.</p>"),
    ("reporting", "Financial reporting",
     "<p>Intermediate financial accounting under IFRS, worked to the entry "
     "rather than the summary: revenue recognition through the five-step model, a journal entry reference "
     "built for retrieval under time pressure, and a coverage audit that records what is still missing.</p>"),
    ("canadian", "Canadian tax and law, kept Canadian",
     "<p>Co-op work preparing Canadian corporate and personal "
     "returns, and a primer that holds the Canadian and American legal positions apart at every point they "
     "diverge instead of blending them.</p>"),
    ("building", "Building the thing", None),
]


def page_about():
    # the fourth paragraph counts this build's own pages, tools and figures, so
    # it is written here rather than in the constant beside the other three
    built = ("<p>Hand-written HTML, CSS and JavaScript across %d pages and %d interactive tools, "
             "%d of them installable. %d figures, all built by hand as static SVG so they render with "
             "JavaScript off. No framework, no build step on the reader's side, accessible in light and "
             "dark, and it prints.</p>" % (len(P), N_TOOLS, N_PWA, TOTAL_FIGS))
    caps_html = "\n".join(
        cap_block(i, cid, title, prose if prose is not None else built)
        for i, (cid, title, prose) in enumerate(CAP_BLOCKS, 1))
    gt = figs.group_totals()
    afm = [p for p in P if p["c"] == "AFM 291"]
    # Optional recruiter rows: absent values render nothing at all, so the
    # section carries no empty shelves while the owner has not filled them.
    seek_bits = []
    if COOP_TERM:
        seek_bits.append(f'<div><b>Seeking</b><span>{esc(COOP_TERM)}</span></div>')
    if GRAD_YEAR:
        seek_bits.append(f'<div><b>Graduation</b><span class="tnum">{esc(GRAD_YEAR)}</span></div>')
    if profile_links():
        seek_bits.append('<div><b>Profiles</b><span>'
                         + ' &middot; '.join(profile_links()) + '</span></div>')
    recruit_rows = ("\n    " + "\n    ".join(seek_bits)) if seek_bits else ""
    body = f"""<div class="hero tight shell">
  <p class="eyebrow accent">About</p>
  <div class="namerow">
    <h1 class="h1" id="author">{marks_mod.svg("author")}{esc(NAME)}</h1>
    <div class="affil">
      <img class="affil-logo" src="uw-logo.png" alt="University of Waterloo"
        width="280" height="67" decoding="async">
      <span class="affil-school">School of Accounting and Finance</span>
    </div>
  </div>
  <p class="lede">Alex, {(esc(STANDING) + ", ") if STANDING else ""}an Accounting and Financial Management
  student in the Analytics stream at the University of Waterloo. I build the thing I need, then leave it
  running here.</p>
</div>

<section class="band ground">
  <div class="shell">
  <div class="sechead"><h2>The short version</h2><span class="count">Facts</span></div>
  <div class="sealrow">
    <figure class="sealbox">
      {marks_mod.seal_svg()}
      <figcaption>Alex Rajcoomar &middot; Waterloo AFM Analytics. A calibration band of
      {marks_mod.seal_facts()["stations"]} stations {marks_mod.seal_facts()["step"]:g} degrees apart,
      the north one left to the observer. Nothing on it was awarded: it is a datum, not a credential,
      and every fact beside it is checkable from this site.</figcaption>
    </figure>
  <div class="facts measure wide pane">
    <div><b>Programme</b><span>Accounting and Financial Management, Analytics stream, University of Waterloo.</span></div>
    <div><b>Co-op</b><span>Preparing Canadian corporate and personal tax returns.</span></div>
    <div><b>Focus</b><span>Financial reporting under IFRS and ASPE, Canadian tax, and the analytics side of accounting.</span></div>
    <div><b>Standing interests</b><span>The science of learning, judgment under uncertainty, and capital cycles. Outside coursework, AI in medicine and commercial spaceflight.</span></div>
    <div><b>Contact</b><span><a class="inlink" href="mailto:{EMAIL}">{EMAIL}</a></span></div>
    <div><b>This site</b><span><a class="inlink" href="{SITE_URL}">{HOST}</a></span></div>{recruit_rows}
  </div>
  </div>
  <div class="sechead nowhead"><h3 id="now">Now</h3><span class="count">This build</span></div>
  {now_line()}
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
{caps_html}
  </div>
  <p class="capnote">The paragraphs are the claim. Under each one is the work that evidences it, named
  and counted: the pieces are declared in <code>content/capabilities.json</code> and the words, figures
  and tables are recomputed from the measurements on every build. A piece can evidence more than one,
  so the four sets overlap and their subtotals do not add to the {TOTAL_WORDS:,} on the corpus line.
  There are no levels here and no self-ratings, because neither could be checked.</p>
</section>

<section class="band ground">
  <div class="shell">
  <div class="sechead"><h2>Why the site exists</h2><span class="count">Rationale</span></div>
  <div class="prose measure">
    <p>Most of what I build starts as a problem I have: a course that will not stay in my head, a claim
    I do not believe, a process I keep repeating by hand. The output is usually an interactive
    document, because a diagram you can interrogate beats a paragraph you can skim. Rather than let
    those sit in a downloads folder, they live here, running, where anyone can use them.</p>

    <p>Two things are worth separating. One course, AFM 291, has been rebuilt here end to end:
    {len(afm)} pieces, {sum(x['words'] for x in afm):,} words, every chapter running the same structure so a topic
    can be found the same way twice. Alongside it sits {ST['independent']['words']:,} words of research
    nobody assigned. The corpus figure on the <a href="index.html#corpus">home page</a> draws that
    split rather than claiming it.</p>

    <h3>How the work is organised</h3>
    <ul>
      <li><strong>Research and writing</strong> holds the pieces where the argument is the point, plus
      the method work on how the rest gets built and audited.</li>
      <li><strong>Coursework</strong> groups every reference and trainer by the course it was built
      for, with a coverage table showing what exists and what does not.</li>
      <li><strong>Interactive tools</strong> are the things you use rather than read. {N_PWA} install to a
      phone home screen.</li>
    </ul>

    <h3>A note on the material</h3>
    <p>These are my own artefacts, written by me for my own use. They are not course materials,
    not official solutions, and not a substitute for the standards themselves. Where a figure or a
    rule matters, check the primary source: the CPA Canada Handbook, the Income Tax Act, or the CRA.</p>

    <p class="plate-nav"><a class="pbtn pbtn-go" href="colophon.html">How this site is built, and how it counts <span aria-hidden="true">&#8594;</span></a>
    <a class="pbtn" href="library.html">The full library <span aria-hidden="true">&#8594;</span></a></p>
  </div>
  </div>
</section>
"""
    return head(f"About · {SHORT}",
                "Alex Rajcoomar, Accounting and Financial Management student in the Analytics stream at the University of Waterloo.",
                "about.html", extra="\n" + jsonld_person()) + body + foot()

# One selection rule for the full-offline copy, stated once: the colophon's
# "about N MB" and the manifest the service worker reads were two copies of
# this logic evaluated at different points in the build, which is how they
# could drift. The skip set also keeps repo documentation out of a reader's
# phone: the handoff notes and the README serve the repository, not an
# offline reader (mscore.py stays: a piece ships it on purpose).
OFFLINE_EXT  = (".html", ".css", ".js", ".woff2", ".webmanifest",
                ".pdf", ".md", ".csv", ".py", ".png")
OFFLINE_SKIP = {"og-card.png", "sw.js", "admin.html", "404.html", "reader.html",
                "HANDOFF.md", "README.md"}

# The editor is hand-maintained and the build never writes it: not a
# generated page, not a piece, not a file any pass rewrites. Every pass that
# walks the tree skips the names here; check 33 holds each file
# byte-identical to the bytes the build started from, and main() puts those
# bytes back should anything still have written it. The snapshot is taken
# at import, before any pass runs.
PROTECTED = ("admin.html",)
_PROTECTED_BYTES = {}
for _f in PROTECTED:
    _pp = os.path.join(OUT, _f)
    _PROTECTED_BYTES[_f] = open(_pp, "rb").read() if os.path.exists(_pp) else None

def offline_files():
    root = [f for f in os.listdir(OUT)
            if f.endswith(OFFLINE_EXT) and f not in OFFLINE_SKIP
            and os.path.isfile(os.path.join(OUT, f))]
    # the self-hosted typefaces the pieces load, so an offline copy renders them
    fdir = os.path.join(OUT, "fonts")
    fonts = ["fonts/" + f for f in os.listdir(fdir)] if os.path.isdir(fdir) else []
    return sorted(root + [f for f in fonts if f.endswith((".woff2", ".json", ".txt"))])

def pass_sentence():
    """One sentence about the last content pass, from content/ledger.json:
    how many pieces a machine-assisted pass edited for copy, how many for
    styling only, how many it left alone. The classes are recomputed from the
    files on every build (check 16), so this cannot be typed or go stale."""
    sm = (LEDGER.get("summary") or {})
    ps = (LEDGER.get("pass") or {})
    if not sm or not ps.get("started"):
        return ""
    try:
        d = datetime.date.fromisoformat(ps["started"])
        started = f"{d.day} {d.strftime('%B')} {d.year}"
    except ValueError:
        started = ps["started"]
    return (f'<p id="pass">The content pass that began on {esc(started)} was carried out by an AI '
            f'assistant under a check that holds every numeral, citation, provenance label, anchor and '
            f'result sentence of every piece to a record. Of the {sm["pieces"]} pieces it could touch, '
            f'{sm["copy"]} received copy edits, {sm["styling"]} received styling only, {sm["untouched"]} '
            f'were left untouched, and {sm["new"]} were added in the pass. The ledger of every change '
            f'is <code>content/ledger.json</code>.</p>')

def _register_sentence(summary):
    if not summary:
        return "This build's register is not yet settled."
    return (f"This build: {summary['rows']} claims, {summary['held']} held, {summary['untested']} untested, "
            f"{summary['open']} not yet measured, {summary['asserted']} asserted with no check, {summary['failed']} failed.")


def limits_block():
    """What the last pass got wrong and what it did not do, in the words it
    wrote at the time. Absent when there are no notes."""
    flaws = [x for x in (LEDGER_NOTES.get("flaws") or []) if isinstance(x, str)]
    undone = [x for x in (LEDGER_NOTES.get("not_done") or []) if isinstance(x, str)]
    if not flaws and not undone:
        return ""
    ps = LEDGER_NOTES.get("pass") or {}
    when = ps.get("started", "")
    li = lambda xs: "".join(f"<li>{esc(x)}</li>" for x in xs)
    return f"""<section class="band colo ground limits" id="limits">
  <div class="shell">
  <div class="sechead"><h2>What the last pass got wrong, and what it left undone</h2><span class="count">{len(flaws) + len(undone)} notes</span></div>
  <div class="prose measure">
    <p>The content pass that began on {esc(when)} kept its own account of its mistakes and its
    omissions in <code>build/ledger-notes.json</code>. A site that scores its own claims should also
    print what it knows is wrong with itself, so the notes are here, as written, rather than in a
    file a reader would have to know to open. The numbers in them are the pass's own, as it wrote
    them; this build reproduces the notes and does not recompute them.</p>
    <h3>Got wrong</h3>
    <ol>{li(flaws)}</ol>
    <h3>Left undone</h3>
    <ol>{li(undone)}</ol>
  </div>
  </div>
</section>
"""

DENSITY_DD = '      <dt>Density</dt>\n      <dd>Figures plus tables per thousand words. Under 1.0 is <b>Prose</b>, 1.0 to 3.0 is\n      <b>Mixed</b>, 3.0 and above is <b>Dense</b>. Documents under 400 words carry no label, because the\n      ratio is unstable at that length. It is a rough signal of what the page will feel like, not a\n      quality measure: a dense page is not a better page.</dd>'

def defs_html():
    """The definitions list, from DEFS, each term carrying the id a counted
    number refers to."""
    out = []
    for did, term, text in DEFS:
        out.append(f'      <dt id="def-{did}">{esc(term)}</dt>\n      <dd>{esc(text)}</dd>')
    out.append(DENSITY_DD)
    return "\n".join(out)

def marks_block():
    """The colophon's account of the marks: the three brand marks and what each
    stands for, the six verification glyphs and what each one asserts, the seal,
    the rule that decides what a surface may draw, the dimensions the drawings
    are read at, and what the sheet that came with them claims against what the
    files carry. Every number here is read from content/marks on this build."""
    F = marks_mod.facts()
    A = marks_mod.audit()
    G = marks_mod.glyph_facts()
    SL = marks_mod.seal_facts()
    FP = fingerprint.facts()
    FC = fingerprint_coverage()
    CO = marks_mod.callouts()
    V = F["variants"]
    # a mark whose file is missing has no reading; check 34 refuses the build
    # over that, and this page says so rather than falling over first
    thin = min([v["thinnest_px"] for v in V.values() if v["thinnest_px"]] or [0])
    ins = V["brand"].get("inspect") or {}

    def srow(lbl, mark, cell, scale, px, tpx):
        return ('<tr><th scope="row">{}</th><td>{}</td><td class="tnum">{}</td>'
                '<td class="tnum">{:g}</td><td class="tnum">{:g}</td>'
                '<td class="tnum">{}</td></tr>').format(
                    esc(lbl), esc(mark), esc(cell), scale, px,
                    ("%.2f" % tpx) if tpx else "not drawn")

    def share(drawn, of):
        return "%d of %d" % (drawn, of)

    rows = "".join(
        srow(lbl, V[k]["mark"], share(V[k]["drawn"], V[k]["of"]), V[k]["scale"], V[k]["px"],
             V[k]["thinnest_px"])
        for k, lbl in (("brand", "The header, at rest"),
                       ("bar", "The bar at the top of every piece"),
                       ("favicon", "The tab icon"),
                       ("controls", "The tests of controls"),
                       ("atlas", "The Atlas"),
                       ("author", "Beside the author's name")))
    if ins:
        rows += srow("The header, under a pointer", V["brand"]["mark"],
                     share(ins["drawn"], V["brand"]["of"]), ins["scale"], V["brand"]["px"],
                     ins["thinnest_px"])
    if not SL.get("missing"):
        rows += srow("The seal, above the facts", "seal", share(SL["drawn"], SL["elements"]),
                     SL["scale"], SL["px"], SL["thinnest_px"])
    # the figure is generated rather than reduced from a file, so its cell
    # counts what the statement's figures draw between them
    rows += srow("The figure on every statement row", "fingerprint",
                 "%s across %d figures" % (format(FC["elements"], ","), FC["pieces"]),
                 FP["places"]["row"]["scale"], FP["places"]["row"]["px"],
                 FP["places"]["row"]["thinnest_px"])

    grows = "".join(
        '<tr><th scope="row"><span class="glcell">{}{}</span></th><td>{}</td>'
        '<td class="tnum">{}</td><td class="tnum">{:g}</td><td class="tnum">{}</td></tr>'.format(
            marks_mod.glyph_svg(k, "head"), esc(g["label"]), esc(g["means"]),
            g["elements"], g["stroke"],
            " and ".join("%.2f" % v for v in sorted(G["rendered"].values())))
        for k, g in G["glyphs"].items())

    crows = "".join(
        '<tr><th scope="row" class="tnum">{}</th><td>{}</td><td class="tnum">{}</td>'
        '<td>{}</td><td>{}</td></tr>'.format(
            esc(c["label"]), esc(c["mark"]), esc(c["coords"]), esc(c["from"]), esc(c["check"]))
        for c in CO)

    frows = "".join('<tr><th scope="row">{}</th><td>{}</td></tr>'.format(esc(a), esc(b))
                    for a, b in fingerprint.RULES)
    seal_p = ("" if SL.get("missing") else
              f"""<p>The seal is the same discipline closed into a medallion: the monogram at its centre, a type
    band on a real arc, and a calibration band of {SL['stations']} stations exactly {SL['step']:g} degrees apart,
    {SL['ticks']} of them fine ticks, {SL['cardinals']} cardinal rules, and the north station left to the observer
    rather than drawn as a tick. The sheet intends divisions every {SL['step']:g} degrees for the polar datum and that
    file carries them every 45; this one carries them every {SL['step']:g}. Of its {SL['elements']} elements the site draws {SL['drawn']}: the innermost ring is
    {marks_mod.SEAL_DROP:g} units and could not hold an edge at any size this
    site uses, so it is dropped rather than drawn as a smear.</p>""")

    return f"""
<section class="band colo ground" id="marks">
  <div class="shell">
  <div class="sechead"><h2>The marks, the glyphs and the seal</h2>
    <span class="count">{F['elements'] + G['elements'] + SL.get('elements', 0)} elements in {len(F['marks']) + G['n'] + (0 if SL.get('missing') else 1)} files</span></div>
  <div class="prose measure">
    <p>The identity is drawn rather than typed: a monogram whose A and R stand on one vertical datum, in the
    header of every generated page, on the bar at the top of every standalone piece, and in the tab icon.
    In the header it holds two layers. At rest it draws the {V['brand']['drawn']} strokes of the letters;
    point at it or reach it with a keyboard and it draws the {ins.get('drawn', 0)} construction elements those
    letters were measured from, which are the circle the A sits in, the datum both letters stand on, and the
    ticks at the apex and the two feet. The other two marks stand where they mean something. The delta heads the
    tests of controls because its own sequence is that page's: evidence, a change, a verified datum, a ledger
    record. The polar datum heads the Atlas and stands beside the author's name because it is this site's own
    sphere abstracted, and the filled node at its north pole is the author's mark among the
    {format(len(ATLAS['points']), ',')} on that sphere.</p>
    <p>A stroke renders at its width times the size it is drawn, over the {F['grid']} unit grid the marks are
    authored on, so a line thinner than one device pixel cannot hold an edge. Each surface therefore draws
    only what it can hold and multiplies every stroke it keeps by one factor. The thinnest line any surface
    draws measures {thin:.2f} device pixels. Nothing is resized by the stylesheet, because a mark scaled after
    the fact would be a mark whose arithmetic was done for another size.</p>
    {seal_p}
  </div>
  <div class="tw"><table class="ctab">
    <caption>What each surface draws, from which mark, how much of it, and how thin its finest line ends up.
    The figure on a row has no file to draw a share of, so its count is what the whole statement's figures draw between them.</caption>
    <thead><tr><th scope="col">Surface</th><th scope="col">Mark</th><th scope="col">Elements</th>
    <th scope="col">Stroke factor</th><th scope="col">Drawn at</th><th scope="col">Thinnest line</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <div class="prose measure">
    <p>Six further glyphs carry the state of a claim rather than the identity of the site. They are authored on
    a {G['grid']} unit grid at stroke {G['stroke']:g}, which renders at
    {" and ".join("%.2f" % v for v in sorted(G['rendered'].values()))} device pixels at the two sizes this site
    draws them, so unlike the brand marks they need no factor at all. They head the columns of the whole
    statement, and they say what a column is before a reader has read a single number in it.</p>
  </div>
  <div class="tw"><table class="ctab">
    <caption>The six verification glyphs, what each one asserts, and what its authored stroke renders as.</caption>
    <thead><tr><th scope="col">Glyph</th><th scope="col">What it asserts</th><th scope="col">Elements</th>
    <th scope="col">Stroke</th><th scope="col">Renders at</th></tr></thead>
    <tbody>{grows}</tbody>
  </table></div>
  <div class="prose measure">
    <p>Every row of the whole statement also carries a figure of its own document, built from four values this
    build measured: the outer radius from the word count, one calibration ray per table, one node per figure,
    and one chord per recorded link between that document and another on this site. There is no random source
    anywhere in it, so the same document draws the same figure on every build, and a figure that changes means
    one of those four values changed.</p>
    <p>A layer is drawn only where its value is, and one of them is thin on the ground: of the {FC['pieces']} figures,
    {FC['rays']} carry rays and {FC['nodes']} carry nodes, {FC['links']} belong to a document with a recorded link, and
    {FC['chords']} draw a chord. A chord joins two of the ring\'s nodes, so a document with fewer than two figures has
    nowhere to put one however many links it records. That is the arithmetic the figure was specified with, kept as
    specified rather than widened to make the layer show up more often.</p>
  </div>
  <div class="tw"><table class="ctab">
    <caption>How a document becomes a figure. W is its words, F its figures, T its tables and C its recorded links.</caption>
    <thead><tr><th scope="col">Feature</th><th scope="col">Rule</th></tr></thead>
    <tbody>{frows}</tbody>
  </table></div>
  <div class="prose measure">
    <p>The marks arrived with a sheet of stated geometry. {A['n']} of its values are readings this build takes
    from the files themselves, and {A['carried']} of those readings bear the sheet out. The rest do not, so the site
    draws the files: the sheet gives the monogram's bowl a radius the path does not describe, sets the delta's
    two ledger rules closer together than they sit, and asks the polar datum for finer angular divisions than
    it carries. Below, {len(CO)} dimensions of the monogram and the polar datum, each one read off a vertex or
    an arc boundary of the shipped path data rather than copied from the sheet. Check 34 recomputes what the pages
    draw on every build without asking the module that drew it, and check 35 walks these {len(CO)} readings a second
    time, with its own reader, and refuses the build if the two walks disagree.</p>
  </div>
  <div class="tw"><table class="ctab">
    <caption>Fifteen dimensions, the coordinates each is read from, and what kind of feature carries it.</caption>
    <thead><tr><th scope="col">Callout</th><th scope="col">Mark</th><th scope="col">Coordinates</th>
    <th scope="col">Read from</th><th scope="col">Check</th></tr></thead>
    <tbody>{crows}</tbody>
  </table></div>
  </div>
</section>
"""


def page_colophon(summary=None):
    gt = figs.group_totals()
    ex = exceptions()
    fams = google_font_families()
    font_list = ", ".join('<a href="%s">%s</a> (%s)' % (p["url"], esc(p["t"]), esc(", ".join(fams.get(p["slug"], []))))
                          for p in ex["fonts"])
    tr_list = ", ".join('<a href="%s.html">%s</a>' % (k, esc(k)) for k in ex["transcripts"])
    # counted from the files: the item is absent, not reworded, when the count is zero
    x1 = (f'<li id="x1">{len(ex["fonts"])} pieces load a typeface from Google Fonts, the family in brackets: {font_list}.\n'
          f'      Everything else on the site makes no external request.</li>' if ex["fonts"] else
          '<li id="x1">No piece loads a typeface from another origin: every face the site uses is self-hosted, '
          'subset to the characters each piece shows, and the build fails on any character a subset lacks.</li>')
    OFF_MB = round(sum(
        os.path.getsize(os.path.join(OUT, f)) for f in offline_files()) / 1048576)
    body = f"""<div class="hero tight shell">
  <p class="eyebrow accent">Colophon</p>
  <h1 class="h1">How this site is built, and how it counts.</h1>
  <p class="lede">Every number on this site is measured from the published files rather than estimated.
  This page states each definition, so a reader can disagree with one.</p>
</div>

<section class="band shell colo">
  <div class="sechead"><h2>The measurements</h2><span class="count">Definitions</span></div>
  <div class="prose measure">
    <dl id="definitions">
{defs_html()}
      <dt>Where the counts stop</dt>
      <dd>The interactive tools read as {min(p['words'] for p in P if p['k']=='Tool')} to {max(p['words'] for p in P if p['k']=='Tool')}
      words and are genuinely much larger than that: their question banks are held in code. The
      {WPM} words per minute behind the reading time is a middle estimate for careful reading of
      technical prose; a skim is faster and a first pass through a figure-heavy section is slower. The
      instrument threshold is applied to what a page renders, not to what I would like it to be, and it
      is why the {N_TOOLS} interactive tools carry no reading time at any length.</dd>

      <dt>Independent, coursework, personal</dt>
      <dd><b>Independent</b> means I chose the question, scoped it and finished it without a course
      asking for it. <b>Coursework</b> means it was built while taking the course, for the assessment
      that was coming. <b>Personal</b> means read and written for its own sake, with no claim on either.
      The split is mine and I have made it conservatively: anything built alongside a course is filed
      as coursework even where the question was my own.</dd>
    </dl>
  </div>
</section>

<section class="band colo ground">
  <div class="shell">
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
      <dd>Inter Variable, subset to the {FONT_CODEPOINTS} characters the corpus actually uses and
      self-hosted at {FONT_BYTES:,} bytes, with a metric-matched fallback face so the page does not
      reflow when the font lands. If the file fails to load, the site keeps working on the system
      stack. The build fails on any page character the subset lacks, so the number above is checked
      rather than believed.</dd>

      <dt>A number you can open</dt>
      <dd>A counted number on these pages is set with a dotted underline. Pointing at it or pressing it
      shows the definition it was counted under, the file it was measured from, the script that measured
      it and the record that holds it. The totals sit in the Tab order; a number inside a row opens
      with a pointer only, so a keyboard reader is not made to stop at every figure of every row, and
      what its dialog would say is the row's own link and the definition above. With scripts off the
      number stands as text and the definitions are the list above; nothing about the number itself
      depends on the script.</dd>

      <dt>Surfaces</dt>
      <dd>Warm paper in light, a near-black ground in dark, hairline rules, no rounded corners. The
      shell pages paint no drop shadow; the search panel sits on the browser's own backdrop. On a
      piece a shadow sits only under what floats over its text: the contents drawer on a phone, the
      reading-position pill, the section menu and the tips; a piece's own sheet keeps whatever it
      declared. One accent, blue, for the independent work on the sphere and for links. A second
      accent, violet, means one thing: a link one document's prose makes to another. It is the colour
      of the chords on both spheres, of the key entry that names them, of the link counts in the
      sphere's card and of the one count of recorded links under the home sphere, and it appears
      nowhere else; it is violet because no figure on this site has spent that hue. A panel sits one step above the ground behind a one-pixel edge. The one gradient
      on the site is the light around the sphere, which encodes nothing and is drawn outside the disc
      so it darkens no mark. Dark mode is a selected set of tokens rather than an inversion, and the
      manual toggle wins over the system setting in both directions.</dd>
    </dl>
  </div>
  </div>
</section>

<section class="band shell colo">
  <div class="sechead"><h2>How it is built</h2><span class="count">Technical</span></div>
  <div class="prose measure">
    <p>No framework, no runtime dependency, and nothing loaded from another origin except where
    the exceptions below say so. No tracking, no cookies, no analytics. {len(P)} pieces served as
    static files by GitHub Pages.
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
    reveal-on-scroll, and the count of passages this browser has opened on the Atlas.</p>
    <p>Accessibility: skip link, visible focus, headings in order, every figure labelled, colour never
    load-bearing on its own, and reduced motion respected. The generated pages print: sticky elements
    release, nothing stays hidden, and figures avoid breaking across pages. Each of those sentences is a
    row in the <a href="controls.html#register">register</a>, with the check that tests it and the last result,
    or the word asserted where nothing tests it yet.</p>
    <p>{ex['kinds']['doc']} of these pages began as Word documents and {ex['kinds']['md']} as markdown
    notes. Each was converted once, by a script that lives outside this repository, and the HTML it
    produced is the record: it is what the build counts, what the Atlas harvests and what a reader
    saves. Nothing is converted at build time. The build does own the sentence at the foot of each
    converted piece that says so, and the footer under it, and it proves on every run that the text
    outside those two blocks is byte for byte what it was.</p>
    {pass_sentence()}
    <p>The corpus as of this build: {md(len(P), "pieces")} pieces, {md(TOTAL_WORDS, "words")} words, {md(TOTAL_FIGS, "figures")} figures,
    {md(TOTAL_TBLS, "tables")} tables and {md(CHECKPOINTS, "checkpoints")} checkpoint questions. {md(ST['independent']['words'], "words")} of those words
    were not assigned by anyone.</p>
  </div>
</section>

<section class="band shell colo" id="claims">
  <div class="sechead"><h2>What this site claims about itself, and what checks it</h2><span class="count">The register</span></div>
  <div class="prose measure">
    <p>Every sentence the generated pages say about this site is a row in a register, beside the check
    that tests it, the last result with its denominator, and what happened when the claim was
    deliberately made false. {_register_sentence(summary)} The register, and the same records drawn one
    glyph each, are on the <a href="controls.html#register">controls page</a>.</p>
  </div>
</section>

{limits_block()}

<section class="band colo ground" id="exceptions">
  <div class="shell">
  <div class="sechead"><h2>The exceptions</h2><span class="count">Counted, not remembered</span></div>
  <div class="prose measure">
    <ol class="excs">
      {x1}
      <li>{len(ex['undrawn'])} pieces render under {DOC_MIN:,} words. They are counted in every total and
      not drawn in the corpus figure; together they hold {ex['undrawn_words']:,} words.</li>
      <li>{len(ex['transcripts'])} run transcripts are measured, held to the same record as every piece, and kept
      in the offline copy, but not listed and not counted in the corpus line: {tr_list}. Together they
      hold {TRANSCRIPT_WORDS:,} words, so the site as a whole carries {TOTAL_WORDS + TRANSCRIPT_WORDS:,} measured
      words over {len(P) + len(ex['transcripts'])} documents; the corpus line counts the {len(P)} pieces.</li>
      <li>The {len(ex['tools'])} interactive tools stand on the shelf of the course or research that
      produced them and on the tools shelf. Every total counts each of them once.</li>
    </ol>
  </div>
  </div>
</section>

{marks_block()}

<section class="band shell colo" id="offline">
  <div class="sechead"><h2>On your phone</h2><span class="count">Offline</span></div>
  <div class="prose measure">
    <p>This site installs. In Safari on a phone, open the share sheet and choose
    <b>Add to Home Screen</b>: the site becomes an app icon, and every page you
    have visited already works with no connection. To hold all of it, every
    piece, the atlas, the tools and the data files, press the button below
    once while online. A saved copy survives a publish: the new worker carries
    every saved file across, then fetches only the files whose digest changed.
    The line under the buttons is read from the cache each time this page
    opens, not remembered.</p>
    <p class="offline-controls">
      <button type="button" id="offline-save" class="linkbtn">Keep the whole site on this phone</button>
      <button type="button" id="offline-drop" class="linkbtn">Remove the offline copy</button>
      <span id="offline-status" role="status" aria-live="polite"></span>
    </p>
    <p>The full copy is about {OFF_MB} MB. One honest caveat: a phone can
    reclaim the space if the icon goes unused for many weeks; opening it once
    while online brings everything back.</p>
  </div>
</section>
"""
    return head(f"Colophon · {SHORT}",
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
#__rb .__rb-home i{font-style:normal;font-weight:400;color:#66635a}
#__rb .__rb-right{margin-left:auto;display:flex;gap:1.1rem;flex-wrap:wrap}
/* the piece's own row of the statement: origin, words, figures, tables, the
   same figures the home page prints for it, from the same measurement */
#__rb .__rb-row{color:#66635a;font-variant-numeric:tabular-nums;white-space:nowrap}
#__rb .__rb-row b{font-weight:600;color:#55524a}
@media (max-width:44rem){#__rb .__rb-row{flex-basis:100%;order:3;white-space:normal}}
/* what the piece was built from, in the owner's words, from pieces.json */
#__rb .__rb-from{flex-basis:100%;order:5;font-weight:400;color:#66635a;line-height:1.4;max-width:70ch}
#__rb .__rb-from b{font-weight:600;color:#55524a}
#__rb .__mark{
  flex:none;align-self:center;color:inherit;
  /* pinned: six pieces give every svg a width of 100 per cent, and this
     mark's stroke factor was computed for the size named here. Check 34
     holds the two to each other. */
  width:__MARKPX__px;height:__MARKPX__px;
}
/* Dark has to answer to two things: the reader's system setting, and the
   theme button on the page, which sets data-theme on <html>. Keyed to the
   media query alone, the bar stayed paper-white across the top of an essay
   the reader had just switched to dark, and read as a rendering fault. The
   media query is scoped so an explicit light choice wins, and the attribute
   selector is repeated so an explicit dark choice wins on a light system. */
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) #__rb{background:#0d0e11;border-bottom-color:#26282d;color:#b9bbc1}
  :root:not([data-theme="light"]) #__rb .__rb-home{color:#f3f3f0}
  :root:not([data-theme="light"]) #__rb .__rb-home i{color:#8f929a}
  :root:not([data-theme="light"]) #__rb .__rb-row{color:#8f929a}
  :root:not([data-theme="light"]) #__rb .__rb-row b{color:#b9bbc1}
  :root:not([data-theme="light"]) #__rb .__rb-from{color:#8f929a}
  :root:not([data-theme="light"]) #__rb .__rb-from b{color:#b9bbc1}
  :root:not([data-theme="light"]) #__rb a{color:#8fb6ee}
  :root:not([data-theme="light"]) #__rb .__mark{background:#f3f3f0;color:#0d0e11}
}
:root[data-theme="dark"] #__rb{background:#0d0e11;border-bottom-color:#26282d;color:#b9bbc1}
:root[data-theme="dark"] #__rb .__rb-home{color:#f3f3f0}
:root[data-theme="dark"] #__rb .__rb-home i{color:#8f929a}
:root[data-theme="dark"] #__rb .__rb-row{color:#8f929a}
:root[data-theme="dark"] #__rb .__rb-row b{color:#b9bbc1}
:root[data-theme="dark"] #__rb .__rb-from{color:#8f929a}
:root[data-theme="dark"] #__rb .__rb-from b{color:#b9bbc1}
:root[data-theme="dark"] #__rb a{color:#8fb6ee}
:root[data-theme="dark"] #__rb .__mark{background:#f3f3f0;color:#0d0e11}
@media print{#__rb{display:none !important}}
</style>
<nav id="__rb" aria-label="Portfolio">
  <a class="__rb-home" href="index.html">__MARK__Alex Rajcoomar <i>portfolio</i></a>
  <span class="__rb-row">__ROW__</span>
  <span class="__rb-right"><a href="__UP__">__UPNAME__</a><a href="atlas.html">Atlas</a><a href="library.html">All work</a></span>
  __FROM__
</nav>
<script>
/* the trail: which passages this browser has opened. The atlas reads it and
   rings them; the record lives in localStorage and never leaves the machine. */
(function(){
  if(window.__trailed) return; window.__trailed=1;
  if('serviceWorker' in navigator && location.protocol.indexOf('http')===0){
    addEventListener('load',function(){setTimeout(function(){
      navigator.serviceWorker.register('sw.js').catch(function(){});},6000);});
  }
  try{
    var k='atlas.trail';
    var u=location.pathname.split('/').pop()||'index.html';
    var t2=JSON.parse(localStorage.getItem(k)||'{}');
    function put(key){
      if(t2[key]||Object.keys(t2).length<500){
        t2[key]=(t2[key]||0)+1;
        try{localStorage.setItem(k,JSON.stringify(t2));}catch(e){}
      }
    }
    put(u+location.hash);
    addEventListener('hashchange',function(){ put(u+location.hash); });
  }catch(e){}
})();
</script>
<!--/__rb-->
"""

RETURN_PILL = """
<!--__rbp-->
<!-- The pill styles itself: this block used to live only with the top bar,
     so the seven tool pages, which carry the pill alone, rendered it as an
     unstyled link at the very end of the document. Whatever carries the
     pill now carries its style. -->
<style id="__rbp-style">
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
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) #__rb-pill{background:rgba(243,243,240,.95);color:#0d0e11;border-color:rgba(0,0,0,.2)}
  :root:not([data-theme="light"]) #__rb-pill:hover{background:#fff;color:#000}
}
:root[data-theme="dark"] #__rb-pill{background:rgba(243,243,240,.95);color:#0d0e11;border-color:rgba(0,0,0,.2)}
:root[data-theme="dark"] #__rb-pill:hover{background:#fff;color:#000}
@media (prefers-reduced-motion:reduce){#__rb-pill{transition:none}}
@media print{#__rb-pill{display:none !important}}
/* a tool carries no bar, so what it was built from stands at the foot of the document */
#__rb-from{margin:1.25rem 1rem;font:400 13px/1.45 InterVar,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;color:#66635a;max-width:70ch}
#__rb-from b{font-weight:600;color:#55524a}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) #__rb-from{color:#8f929a}
  :root:not([data-theme="light"]) #__rb-from b{color:#b9bbc1}
}
:root[data-theme="dark"] #__rb-from{color:#8f929a}
:root[data-theme="dark"] #__rb-from b{color:#b9bbc1}
</style>
<!-- With scripts off nothing ever adds the __on class, and the only way
     back from a tool page vanished. The pill needs its script for the
     scroll threshold, not for existing. -->
<noscript><style>#__rb-pill{opacity:1 !important;transform:none !important;pointer-events:auto !important}</style></noscript>
<a id="__rb-pill" href="__UP__">&#8592; __UPNAME__</a>
__FROM__
<script>
(function(){
  var p=document.getElementById('__rb-pill'); if(!p) return;
  /* On a page with the top bar the pill waits until the bar has scrolled
     out of reach. On a page without one (the tools carry no bar, because a
     bar inside a full-screen application sits in the wrong place) the pill
     is the only way back, so it is there from the first paint: a tool
     screen shorter than the threshold used to strand the reader entirely. */
  var TH=document.getElementById('__rb')?160:-1;
  var t=false;
  function run(){ t=false;
    p.classList.toggle('__on',(window.scrollY||document.documentElement.scrollTop)>TH); }
  function q(){ if(!t){ t=true; requestAnimationFrame(run); } }
  addEventListener('scroll',q,{passive:true}); run();
})();
/* the trail, for the pages that carry only the pill (the tools) */
(function(){
  if(window.__trailed) return; window.__trailed=1;
  if('serviceWorker' in navigator && location.protocol.indexOf('http')===0){
    addEventListener('load',function(){setTimeout(function(){
      navigator.serviceWorker.register('sw.js').catch(function(){});},6000);});
  }
  try{
    var k='atlas.trail';
    var u=location.pathname.split('/').pop()||'index.html';
    var t2=JSON.parse(localStorage.getItem(k)||'{}');
    function put(key){
      if(t2[key]||Object.keys(t2).length<500){
        t2[key]=(t2[key]||0)+1;
        try{localStorage.setItem(k,JSON.stringify(t2));}catch(e){}
      }
    }
    put(u+location.hash);
    addEventListener('hashchange',function(){ put(u+location.hash); });
  }catch(e){}
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
    r'<nav id="__rb".*?</nav>',
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


def piece_row(p):
    if not p:
        return ""
    return (f'{SURF_LABEL[p["surface"]]} &middot; <b>{p["words"]:,}</b> words &middot; '
            f'<b>{p["figures"]}</b> figures &middot; <b>{p["tables"]}</b> tables')

def from_line(p):
    """The built_from line's own markup: label plus complement, or the
    sentinel on its own."""
    bf = p["built_from"].strip()
    if bf == NOT_DECLARED:
        return esc(bf)
    return f'<b>Built from</b> {esc(bf)}'

def piece_from(p):
    """The built_from line, one per piece, in the owner's words. Rendered by
    the build so it can never drift from content/pieces.json; check 17 refuses
    a piece without one, or one with an em dash."""
    if not p or not (p.get("built_from") or "").strip():
        return ""
    return f'<span class="__rb-from">{from_line(p)}</span>'

_FROM_BLOCK = re.compile(r"\s*<!--__from-->.*?<!--/__from-->", re.S)

def own_from(path, p):
    """A converted note carries the site's own header and no bar, so its
    built_from line stands in the masthead, in a block the build owns. The
    block is refilled on every run and written only when it changes."""
    if not p or not (p.get("built_from") or "").strip():
        return False
    text = open(path, encoding="utf-8", errors="ignore").read()
    block = '<!--__from--><p class="docfrom">%s</p><!--/__from-->' % from_line(p)
    new = _FROM_BLOCK.sub("", text)
    m = re.search(r'(<div class="docmeta">.*?</div>)(\s*</header>)', new, re.S)
    if not m:
        m = re.search(r'(<p class="dek">.*?</p>)(\s*</header>)', new, re.S)
    if not m:
        return False
    new = new[:m.end(1)] + "\n        " + block + new[m.end(1):]
    if new != text:
        os.chmod(path, 0o644)
        open(path, "w", encoding="utf-8").write(new)
    return True


LONG_WORDS = 5000
_LONG_BLOCK = re.compile(r"\s*<!--__long-->.*?<!--/__long-->", re.S)

def own_long(path, p):
    """The reading kit for a piece over LONG_WORDS measured words: a section
    index built from the same anchors the Atlas harvests, a reading position
    kept in localStorage, a 66ch measure for running text, tabular figures in
    tables only, and print rules that keep figures whole. One owned block
    before </body>, refilled on every run; removed if the piece falls under
    the threshold."""
    text = open(path, encoding="utf-8", errors="ignore").read()
    long_ = bool(p) and int(p.get("words") or 0) > LONG_WORDS
    block = ('<!--__long--><link rel="stylesheet" href="%s"><script src="%s" defer></script><!--/__long-->'
             % (asset("long.css"), asset("long.js"))) if long_ else ""
    new = _LONG_BLOCK.sub("", text)
    if block:
        i = new.lower().rfind("</body>")
        new = (new[:i] + "\n" + block + "\n" + new[i:]) if i != -1 else new + block
    if new != text:
        os.chmod(path, 0o644)
        open(path, "w", encoding="utf-8").write(new)
    return long_


def add_return(path, up="index.html", upname="Home", bar=True, p=None):
    """Give a standalone piece a way back into the site. Any earlier injection
    is stripped first, so a page never ends up carrying two."""
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return
    before = text
    text = strip_injected(text)

    pill = RETURN_PILL.replace("__UP__", up).replace("__UPNAME__", upname)
    # the bar carries the built_from line where there is a bar; a tool, which
    # carries the pill alone, carries the line at the foot of its document
    pill = pill.replace("__FROM__", "" if bar else piece_from(p).replace('class="__rb-from"', 'id="__rb-from"').replace("<span", "<p").replace("</span>", "</p>"))
    if bar:
        top = (RETURN_BAR.replace("__MARKPX__", str(marks_mod.VARIANTS["bar"]["px"]))
               .replace("__MARK__", marks_mod.svg("bar", cls="__mark mk-bar"))
               .replace("__UP__", up).replace("__UPNAME__", upname)
               .replace("__ROW__", piece_row(p)).replace("__FROM__", piece_from(p)))
        m = _body_tag(text)
        text = (text[:m.end()] + top + text[m.end():]) if m else (top + text)
    i = text.lower().rfind("</body>")
    text = (text[:i] + pill + text[i:]) if i != -1 else (text + pill)
    if text != before:
        open(path, "w", encoding="utf-8").write(text)


# ------------------------------------------- converted pieces' own chrome ----
# Twenty-two pieces were converted from notes and carried a copy of the site
# footer made on the day of conversion, so each one told a reader the site
# held 48 pieces long after it held 61, and each said it was converted at
# build time, which no build step does. The sentence and the footer are chrome
# and the build owns them now, inside two marked blocks. Nothing outside the
# blocks is touched, and the pass proves it: the readable text of the piece
# with the blocks cut out is compared before and after, byte for byte.
DOCEND = {
    "md": ("Converted once from my own markdown note by a script outside this "
           "repository. The HTML is the record, and this page is the published "
           "form of it. <a href=\"colophon.html\">How the site counts it</a>."),
    "doc": ("Converted once from my own Word document by a script outside this "
            "repository. The HTML is the record, and this page is the published "
            "form of it. <a href=\"colophon.html\">How the site counts it</a>."),
}
TAIL_PROBLEMS = []
TAIL_KINDS = {}

def _piece_footer():
    """The generated pages' footer, with the three heading ids the hand-copied
    footers carried, so an anchor that resolved yesterday resolves today."""
    m = re.search(r'<footer class="site">.*?</footer>', foot(), re.S)
    f = m.group(0)
    # No keyboard button and, below, no keyboard sheet: the measurement counts
    # hidden text, so a sheet of shortcut prose in 22 pieces would add some
    # forty invisible "words" to each of them. A piece keeps the dialog and
    # the manifest it always carried and nothing that is not read.
    f = re.sub(r'\s*&middot;\s*<button id="keysbtn"[^>]*>keyboard</button>', "", f)
    f = f.replace('<h2>%s</h2>' % esc(SHORT), '<h2 id="alex-rajcoomar">%s</h2>' % esc(SHORT), 1)
    f = f.replace('<h2>Sections</h2>', '<h2 id="sections">Sections</h2>', 1)
    f = f.replace('<h2>This site</h2>', '<h2 id="this-site">This site</h2>', 1)
    return f

_DOCEND_OLD = re.compile(r'<p class="docend">.*?</p>', re.S)
_DOCEND_NEW = re.compile(r'<!--__docend (md|doc)-->.*?<!--/__docend-->', re.S)
_FOOT_OLD = re.compile(r'<footer class="site">.*?</footer>', re.S)
_FOOT_NEW = re.compile(r'<!--__foot-->.*?<!--/__foot-->', re.S)
# the search dialog and its manifest, hand-copied on the day of conversion:
# the manifest listed 48 pieces and the box said so in its placeholder
_TAIL_OLD = re.compile(r'<!-- Search across every piece\..*?<script>\s*window\.WORK\s*=.*?</script>', re.S)
_TAIL_NEW = re.compile(r'<!--__tail-->.*?<!--/__tail-->', re.S)

def _piece_tail():
    """The generated pages' search dialog, keyboard sheet and manifest, which
    is everything foot() emits between the footer and the script tag."""
    m = re.search(r'</footer>\s*(.*?)\s*<script src="site\.js', foot(), re.S)
    tail = m.group(1)
    tail = re.sub(r'<!-- The keyboard routes.*?<dialog class="keys" id="keysheet".*?</dialog>\s*', "", tail, flags=re.S)
    # the provenance dialog and its data serve the generated pages' counted
    # numbers; a piece carries neither the script that opens it nor numbers
    # that open, and its one word would be counted as the piece's
    tail = re.sub(r'<!-- A counted number opens here.*?<dialog class="prov" id="prov".*?</dialog>\s*', "", tail, flags=re.S)
    tail = re.sub(r'<script type="application/json" id="defs">.*?</script>\s*', "", tail, flags=re.S)
    return tail

def _outside_tail(text):
    """The file with the two owned regions cut out: raw bytes, and the readable
    text of what remains."""
    t = _DOCEND_NEW.sub("", text)
    t = _DOCEND_OLD.sub("", t)
    t = _FOOT_NEW.sub("", t)
    t = _FOOT_OLD.sub("", t)
    t = _TAIL_NEW.sub("", t)
    t = _TAIL_OLD.sub("", t)
    r = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", t, flags=re.S | re.I)
    r = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", r))).strip()
    return t, r

def own_tail(path):
    """Rewrite the conversion sentence and the footer of a converted piece.
    Returns True if the file carries the blocks. Idempotent: the markers are
    found and refilled, so a second run writes nothing."""
    text = open(path, encoding="utf-8", errors="ignore").read()
    m = _DOCEND_NEW.search(text)
    if m:
        kind = m.group(1)
    else:
        m = _DOCEND_OLD.search(text)
        if not m:
            return False
        kind = "doc" if "Word document" in m.group(0) else "md"
    mf = _FOOT_NEW.search(text) or _FOOT_OLD.search(text)
    if not mf:
        return False
    raw_before, read_before = _outside_tail(text)
    new_docend = '<!--__docend %s--><p class="docend">%s</p><!--/__docend-->' % (kind, DOCEND[kind])
    text = text[:m.start()] + new_docend + text[m.end():]
    mf = _FOOT_NEW.search(text) or _FOOT_OLD.search(text)
    text = text[:mf.start()] + "<!--__foot-->" + _piece_footer() + "<!--/__foot-->" + text[mf.end():]
    mt = _TAIL_NEW.search(text) or _TAIL_OLD.search(text)
    if mt:
        text = text[:mt.start()] + "<!--__tail-->" + _piece_tail() + "<!--/__tail-->" + text[mt.end():]
    raw_after, read_after = _outside_tail(text)
    f = os.path.basename(path)
    if raw_before != raw_after:
        TAIL_PROBLEMS.append("%s: bytes outside the owned blocks changed" % f)
    if read_before != read_after:
        TAIL_PROBLEMS.append("%s: readable text outside the owned blocks changed" % f)
    TAIL_KINDS[f] = kind
    old = open(path, encoding="utf-8", errors="ignore").read()
    if text != old:
        os.chmod(path, 0o644)
        open(path, "w", encoding="utf-8").write(text)
    return True


# ------------------------------------------------------- piece titles ----
# The <title> of a piece was hand-written on the day the piece was made and
# carried its own separator and suffix. The build owns it now the way it
# owns the meta block, but only where the tag read as the piece's title plus
# a separator plus a suffix; a tag that says something else is content and
# is listed for the owner instead.
#
# The suffix is the piece's own subtitle, not the site's name. A search
# result already prints the site on its own line and the name is in the
# host, so spending the tag on it bought nothing and cost the descriptor
# the tag used to carry: "Not Significant - An essay on the accounting of
# harm" had become "Not Significant - Alex Rajcoomar". The subtitle is the
# same string the statement and every shelf row print under the title, so
# editing it in admin.html corrects the tab, the search result and the link
# preview at once.
_TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)

def piece_title(p):
    """The tag, the tab and the link preview all say the same thing: the
    piece, then what it is."""
    s = (p.get("s") or "").strip()
    return "%s \u00b7 %s" % (p["t"], s) if s else p["t"]

TITLE_SKIPPED = []
TITLE_ALONE = []
TITLE_PROBLEMS = []

def own_title(path, p):
    text = open(path, encoding="utf-8", errors="ignore").read()
    m = _TITLE.search(text)
    if not m:
        return False
    cur = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()
    want = piece_title(p)
    if cur == want:
        return True
    t = p["t"].strip()
    if cur == t:
        # the title alone, no separator and no suffix: nothing to own
        TITLE_ALONE.append(p["slug"])
        return False
    rest = cur[len(t):] if cur.startswith(t) else None
    if rest is None or not re.match(r"^\s*[\u2014\u2013\u00b7|:-]\s+.+$", rest):
        TITLE_SKIPPED.append((p["slug"], cur))
        return False
    new = text[:m.start()] + "<title>%s</title>" % esc(want) + text[m.end():]
    if text[:m.start()] + text[m.end():] != new[:m.start()] + new[m.start() + len("<title>%s</title>" % esc(want)):]:
        TITLE_PROBLEMS.append("%s: bytes outside <title> changed" % os.path.basename(path))
    os.chmod(path, 0o644)
    open(path, "w", encoding="utf-8").write(new)
    return True


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
# The tab icon is the monogram reduced to what a 16px square can hold: the
# A and the R's leg, at 3.3 times the authored stroke, which puts the thinnest
# line over one device pixel. The bowl is dropped because its counter falls to
# about a pixel and a quarter at that size and fills in.
FAVICON = marks_mod.favicon_uri("#16150f", "#faf9f6")

def head_block(p):
    url  = SITE_URL + "/" + p["url"]
    desc = (p.get("blurb") or p.get("s") or "").strip()
    # 160, not 300: a search result shows about that much and the rest is cut
    # mid-word by the engine rather than mid-sentence by us.
    if len(desc) > 160:
        desc = desc[:157].rsplit(" ", 1)[0].rstrip(",;:") + "\u2026"
    title = piece_title(p)
    return f"""{_HEAD_START}
<meta name="color-scheme" content="{p.get('_scheme', 'light dark')}">
<meta name="description" content="{esc(desc)}">
<link rel="icon" href="{FAVICON}">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
{'' if p.get("pwa") else '<link rel="manifest" href="site.webmanifest">'}
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{esc(SHORT)} \u00b7 portfolio">
<meta property="og:image" content="{SITE_URL}/{_card_for(p)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(p["t"])} \u00b7 {esc(SHORT)}">
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
    r'|\s*<link rel="icon"' + _ATTRS + r'>'
    r'|\s*<meta name="color-scheme"' + _ATTRS + r'>'
    r'|\s*<meta name="description"' + _ATTRS + r'>')

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
    # Declare what the document can actually do rather than what the site
    # wishes it did. Six pieces carry a fixed light palette and no dark rules:
    # a reader in dark mode was landing on a white page from a dark one, with
    # the browser's own scrollbars and form controls painted for the wrong
    # side. Saying "light" makes the browser agree with the page.
    # Test the document's own CSS, not the blocks this build injects into it:
    # the return bar carries its own dark rules, and the theme script mentions
    # data-theme, so both would make every piece look dark-capable.
    own = re.sub(r"<!--__rb-->.*?<!--/__rb-->", "", text, flags=re.S)
    own = re.sub(r"<!--__meta-->.*?<!--/__meta-->", "", own, flags=re.S)
    # A piece is dark-capable if it links the site stylesheet, which carries
    # the dark palette, or if its own CSS answers the media query. Six do
    # neither, and those are the ones that were flashing white at a reader who
    # had asked the whole site for dark.
    p["_scheme"] = ("light dark"
                    if re.search(r'href="site\.css', own)
                    or re.search(r"prefers-color-scheme\s*:\s*dark", own)
                    else "light")
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


# The shared assets carry a content digest in their URL on every generated
# page, so a deploy can never serve yesterday's stylesheet against today's
# markup. The pieces that link those same assets referenced them bare, which
# is exactly that failure, made one visit longer by the service worker's
# cache-first strategy. Rewritten to the current digest on every build;
# idempotent because the digest is a function of the asset's content.
_ASSET_LINK = re.compile(
    r'\b(href|src)="(site\.css|figures\.css|site\.js|atlas\.js)(\?v=[0-9a-f]{8})?"')

def version_assets(path):
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return False
    fixed = _ASSET_LINK.sub(lambda m: f'{m.group(1)}="{asset(m.group(2))}"', text)
    if fixed != text:
        os.chmod(path, 0o644)
        open(path, "w", encoding="utf-8").write(fixed)
        return True
    return False


# The converted notes carry two h1s: the site masthead's, copied in when the
# note was converted, and the document's own inside .docbody. Two h1s make
# the document read as two documents to heading navigation. The masthead is
# site furniture, so its h1 is demoted to a styled paragraph; the document's
# own h1, which is content, stays the page's one h1.
_DOCMAST_H1 = re.compile(
    r'(<header class="docmast">.*?)<h1>(.*?)</h1>', re.S)

def demote_docmast_h1(path):
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return False
    fixed = _DOCMAST_H1.sub(r'\1<p class="docmast-h1">\2</p>', text, count=1)
    if fixed != text:
        os.chmod(path, 0o644)
        open(path, "w", encoding="utf-8").write(fixed)
        return True
    return False


# An image with no declared size claims no space until it loads, and the
# prose below it jumps down when it does. The size is measured from the
# file's own PNG header rather than typed, the same way every other number
# here is, and the declared height stays honest because site.css keeps
# img{height:auto}. Idempotent: a tag that already carries a width is left
# exactly as it is.
_IMG_TAG = re.compile(r"<img\b[^>]*>")

def _png_size(fp):
    try:
        with open(fp, "rb") as fh:
            head = fh.read(24)
    except OSError:
        return None
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return (w, h) if w and h else None

def size_images(path):
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return 0
    count = [0]
    def fix(m):
        tag = m.group(0)
        if "width=" in tag or "height=" in tag:
            return tag
        src = re.search(r'src="([^"/]+\.png)"', tag)
        if not src:
            return tag
        wh = _png_size(os.path.join(OUT, src.group(1)))
        if not wh:
            return tag
        count[0] += 1
        end = "/>" if tag.endswith("/>") else ">"
        return tag[:-len(end)].rstrip() + f' width="{wh[0]}" height="{wh[1]}"' + end
    fixed = _IMG_TAG.sub(fix, text)
    if count[0] and fixed != text:
        os.chmod(path, 0o644)
        open(path, "w", encoding="utf-8").write(fixed)
    return count[0]



# The nav on a converted piece was copied by hand when the piece was written,
# so it is frozen at whatever the site looked like that day. Thirty-one of them
# still list six sections and cannot reach the Atlas at all, which means the
# longest documents on the site have no route to the page built to index them.
# Rewritten from NAV on every build, the same way the head metadata is.
_NAV_BLOCK = re.compile(r'<nav class="main"[^>]*>.*?</nav>', re.S | re.I)

def normalise_nav(path):
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return False
    want = ('<nav class="main" aria-label="Sections">\n      '
            + "\n      ".join(f'<a href="{u}">{t}</a>' for u, t in NAV)
            + "\n    </nav>")
    fixed = _NAV_BLOCK.sub(lambda m: want, text)
    if fixed != text:
        os.chmod(path, 0o644)
        open(path, "w", encoding="utf-8").write(fixed)
        return True
    return False



# A diagram a screen reader cannot see is a diagram that is not there. Twenty
# three figures across six documents carried no role and no label, so they were
# announced as nothing at all. The name comes from the heading the figure sits
# under, which is the only description the document actually contains, and it
# is numbered when a heading governs more than one figure so the reader can
# tell which of them they have reached.
_SVG_OPEN = re.compile(r"<svg\b([^>]*)>", re.I)
_HEADING = re.compile(r"<h[1-6]\b[^>]*>(.*?)</h[1-6]>", re.S | re.I)

def label_figures(path):
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return 0
    # the favicon is an SVG inside an attribute, not an element on the page
    # Blanked, not removed: every offset below indexes into `text`, so the
    # masked copy has to stay the same length or the insertions land in the
    # wrong place. Losing that is how the first version rewrote the same
    # twenty-three figures on every run without ever inserting anything.
    scan = re.sub(r'href="data:image/svg\+xml,[^"]*"',
                  lambda m: " " * len(m.group(0)), text)
    scan = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", lambda m: " " * len(m.group(0)),
                  scan, flags=re.S | re.I)

    hits = [m for m in _SVG_OPEN.finditer(scan)
            if "role=" not in m.group(1) and "aria-hidden" not in m.group(1)]
    if not hits:
        return 0

    names = []
    for m in hits:
        heads = _HEADING.findall(scan[:m.start()])
        raw = heads[-1] if heads else ""
        # a space per tag boundary, or a numeral in a span glues to the word
        # after it and the label reads "1The seven graphs"
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()
        # a section number lives in its own span, so it arrives glued to the
        # front of the name: "1 The seven graphs" is the numeral, not the title
        txt = re.sub(r"^[0-9]{1,2}[.\u00b7)]?\s+(?=[A-Za-z])", "", txt)
        names.append(txt or "Figure")

    counts = {}
    for n in names:
        counts[n] = counts.get(n, 0) + 1
    seen, out, n_done = {}, [], 0
    for m, base in zip(hits, names):
        if counts[base] > 1:
            seen[base] = seen.get(base, 0) + 1
            label = f"{base}, figure {seen[base]} of {counts[base]}"
        else:
            label = base
        out.append((m, label))

    for m, label in reversed(out):
        ins = ' role="img" aria-label="%s"' % esc(label)
        text = text[:m.start() + 4] + ins + text[m.start() + 4:]
        n_done += 1
    if n_done:
        os.chmod(path, 0o644)
        open(path, "w", encoding="utf-8").write(text)
    return n_done


def add_returns_everywhere():
    """Two things per standalone piece: the head metadata the build owns, and a
    way back into the site. The bar is skipped where a page already carries full
    navigation, and the tools get the floating pill only, because a bar inside a
    full-screen application sits in the wrong place. The head is normalised on
    every piece regardless, including the converted notes."""
    # the generated pages carry full navigation; the reader edition and the
    # editor are the two other pages that are not pieces
    shell = set(SHELL_PAGES) | {"reader.html"} | set(PROTECTED)
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
    n = heads = navs = figs_named = tails = titles = longs = 0
    # The nav runs over every hand-maintained page but the protected editor,
    # reader.html included though it carries its own navigation and is skipped
    # below. A page the reader can land on and cannot leave for the Atlas is
    # the defect being fixed, and reader.html is exactly such a page.
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".html") and f not in SHELL_PAGES and f not in PROTECTED:
            if normalise_nav(os.path.join(OUT, f)):
                navs += 1
            if own_tail(os.path.join(OUT, f)):
                tails += 1
            if f in by_url and own_title(os.path.join(OUT, f), by_url[f]):
                titles += 1
            # The typeface is self-hosted: any page still preloading it from
            # the CDN is rewritten to the local subset, so no request leaves
            # the origin. Runs on every hand-maintained page, reader.html
            # included, because the CDN preload was hand-copied the same way
            # the nav was.
            fp = os.path.join(OUT, f)
            try:
                _t = open(fp, encoding="utf-8", errors="ignore").read()
            except Exception:
                _t = ""
            _t2 = re.sub(
                r"https://cdnjs\.cloudflare\.com/ajax/libs/inter-ui/[0-9.]+/"
                r"variable/InterVariable\.woff2",
                "InterVariable-sub.woff2", _t)
            if _t2 != _t:
                os.chmod(fp, 0o644)
                open(fp, "w", encoding="utf-8").write(_t2)

    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".html") or f in shell:
            continue
        path = os.path.join(OUT, f)
        if f in by_url and normalise_head(path, by_url[f]):
            heads += 1
        fix_stale_host(path)
        version_assets(path)
        figs_named += label_figures(path)
        size_images(path)
        demote_docmast_h1(path)
        longs += own_long(path, by_url.get(f))
        if 'class="docbar"' in open(path, encoding="utf-8", errors="ignore").read():
            own_from(path, by_url.get(f))
            continue                      # converted notes already carry full navigation
        up, upname = where.get(f, ("index.html", "Home"))
        add_return(path, up, upname, bar=f not in tools, p=by_url.get(f))
        n += 1
    add_returns_everywhere.longs = longs
    return n, heads, navs, figs_named, tails, titles


# --------------------------------------------------------------- write ----
ATLAS_BODY = r"""<section class="band atlas-band" id="atlas">
  <div class="shell atlas-grid">
    <div class="atlas-side">
      <div class="atlas-mark">{mark_atlas}</div>
      <p class="eyebrow accent">Atlas</p>
      <h1 class="atlas-h1">Every section of everything, on one sphere.</h1>
      <p class="atlas-lede">{lede}</p>

      <script type="application/json" id="afacts">{facts}</script>

      <noscript><style>#aplates article[hidden]{{display:block !important}}#astage{{display:none}}</style></noscript>
      <div class="plates" id="aplates">
{plates}
      </div>

      <nav class="guide" id="aguide" aria-label="The six labels">
        <p class="guide-h">The sequence <span class="guide-c">6 labels</span></p>
        <ol>
{guide}
        </ol>
      </nav>

      <p class="plate-nav" id="anav">
        <a class="pbtn" id="pprev" href="#label-1">&#8592; Back</a>
        <a class="pbtn pbtn-go" id="pnext" href="#label-2">Next label &#8594;</a>
        <a class="pskip" id="pskip" href="#atlaslist">Skip to the index</a>
      </p>

      <div class="freebar" id="afree" hidden>
        <div class="atlas-controls">
          <label class="sr" for="aq">Search {nsec} sections</label>
          <input id="aq" type="search" placeholder="Search {nsec} sections" autocomplete="off" spellcheck="false">
          <div class="atlas-modes" id="amodes">
            <button type="button" id="aglobe" class="chip" aria-pressed="true">Globe</button>
            <button type="button" id="alist" class="chip" aria-pressed="false">List</button>
          </div>
        </div>
        <p class="atlas-count" id="acount" role="status">Showing all {nsec} sections.</p>
        <p class="atoday" id="atoday" hidden></p>
        <div class="atlas-results" id="ares" hidden></div>
        <div class="atlas-key">
          <ul class="akey-list">
            <li><i class="ak ak-ind"></i>Independent work</li>
            <li><i class="ak ak-per"></i>Personal interest</li>
            <li><i class="ak ak-cou"></i>Coursework, drawn as an outline</li>
            <li><i class="ak ak-too"></i>Tools, one mark each, standing off the sphere: not headings</li>
            <li class="akey-wide"><i class="ak ak-shr"></i>Headings carried by more than one document, standing off the surface by how many carry them; point at one and the fan to its documents is drawn</li>
            <li class="akey-wide"><i class="ak ak-vis"></i><span id="aseen">Passages</span> this browser has opened, ringed. The record stays in this browser</li>
            <li class="akey-wide"><i class="ak ak-lnk"></i>Point at any mark and chords join its document to the documents its text links, or that link it; each chord's tick sits nearer the linked one</li>
            <li class="akey-wide"><i class="ak ak-dsc"></i>A document's disc, a hairline: two thirds of its share of the sphere, settled clear of every other disc; the document under the pointer, or faced by the home sphere, has its disc drawn in the chord colour</li>
            <li class="akey-wide"><i class="ak ak-zon"></i>The two parallels that bound the origins' zones: independent work north of the first, coursework between them, personal interest south of the second</li>
            <li class="akey-wide"><i class="ak ak-aut"></i>The author, one anchor at the north pole, above his own independent work: an origin of his own, its zone, disc and position by the rule every document follows; its card is the recorded standing, the recorded co-op term counted from this build's date, and the featured pieces' subtotal</li>
            <li class="akey-wide"><i class="ak ak-cor"></i>The light behind the home sphere takes the hue of the faced document's recorded origin: indigo over slate for independent work, cobalt for coursework, bronze over slate for personal interest; parchment, ivory and bone on paper</li>
          </ul>
          <p class="akey-note">A mark's area is apportioned from its document's measured word count by
          the share of the document's static text under that heading; it is not a per-section
          measurement. Heading level is no longer drawn on the sphere and is kept in the index
          beside it. A heading several documents carry is placed once, between them. Where a
          document sits is a rule: each origin owns a zone of latitude whose area is its share
          of the sections (independent work in the north, coursework across the middle, personal
          interest in the south); within its zone each document starts at the height its
          cumulative section count gives it, largest first, on a longitude that steps by the
          golden angle from one document to the next, and is drawn as a disc of two thirds of its
          share of the sphere; the discs are settled apart, a fixed number of steps with no
          randomness, until no two touch, each held inside its zone. A document's own sections lie
          on an equal-area spiral inside its disc, the first at the centre, each next one a golden
          angle round and a ring further out, so a document reads as one cluster and its reading
          order runs from the centre to the rim. A wide disc is a document of many sections, and
          the third of the sphere that no disc holds is the space between documents. The build
          recomputes every centre, every radius and every mark from the section counts on every
          run and refuses a sphere that disagrees (check 28).</p>
        </div>
        <p class="replay"><button type="button" id="preplay" class="linkbtn">Replay the six labels</button></p>
      </div>

      <div class="atlas-doc" id="adoc" hidden></div>
    </div>

    <div class="atlas-stagewrap" id="astagewrap">
    <div class="atlas-stage" id="astage">
      <canvas id="acanvas" aria-hidden="true"></canvas>
      <div class="atlas-labels" id="alabels" aria-hidden="true"></div>
      <div class="atlas-card" id="acard" hidden aria-hidden="true"><p class="ac-t"></p><p class="ac-d"></p></div>
      <div class="atlas-crumb" id="acrumb" hidden>
        <button type="button" id="acrumbout" class="crumb-out">&#8592; All {ndoc} documents</button>
        <span class="crumb-now" id="acrumbnow"></span>
      </div>
    </div>
    <!-- The hint, the caption and the stage key sit under the sphere, not
         in its box: on a phone the box is the sphere's whole height, and
         anything placed inside it lands on the marks. At desktop widths they
         are positioned against the wrap, which is the stage's own box. -->
    <div class="atlas-under" id="aunder">
      <p class="atlas-hint" id="ahint">Drag to turn it, or press <kbd>&#8594;</kbd> for the next label.</p>
      <p class="atlas-cap" id="acap"></p>
      <button type="button" class="arestore" id="arestore" hidden>Restore the framing</button>
      <div class="stagekey" id="astagekey" hidden></div>
    </div>
    </div>
  </div>

  <div class="shell">
    <div class="atlas-list" id="atlaslist" data-zones="{ATLAS_ZONES_A}">
{blocks}
    </div>
  </div>
</section>
"""

# ------------------------------------------------------------------ atlas --
# The globe is a view of this page, not a second copy of it. Every section is
# written out as a real link inside a real list with its coordinates on the
# element; the script reads those elements and draws them. Turn the script off
# and the page is still the complete table of contents for the whole corpus,
# which is also what a screen reader and a crawler get.
ATLAS = {"points": [], "regions": [], "zones": {}}

SURF_NAME = {"independent": "Independent", "course": "Coursework",
             "personal": "Personal interest", "author": "The author"}


def coop_window():
    """The recorded co-op term ("January to April 2027") as dates, and the
    days from this build's date to its first day. None when the term is not
    recorded in that form, and then nothing about it is printed."""
    m = re.match(r"^\s*([A-Z][a-z]+)\s+to\s+([A-Z][a-z]+)\s+(\d{4})\s*$", COOP_TERM or "")
    if not m:
        return None
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    if m.group(1) not in months or m.group(2) not in months:
        return None
    y = int(m.group(3)); a = months.index(m.group(1)) + 1; b = months.index(m.group(2)) + 1
    start = datetime.date(y, a, 1)
    end = (datetime.date(y + (b // 12), (b % 12) + 1, 1) - datetime.timedelta(days=1))
    return {"start": start, "end": end, "days": (start - TODAY).days}


def featured_subtotal():
    """Words, figures and tables over the pieces recorded as featured."""
    fp = [p for p in P if p.get("featured")]
    return {"n": len(fp), "words": sum(p["words"] for p in fp),
            "figures": sum(p["figures"] for p in fp), "tables": sum(p["tables"] for p in fp)}


def author_card():
    """The author's card, one line, from the recorded standing, the recorded
    co-op term counted from this build's date, and the featured subtotal.
    check 32 recomputes each figure on its own and holds both pages to it."""
    bits = []
    if STANDING:
        bits.append(f"{STANDING}, Accounting and Financial Management, Analytics stream")
    else:
        bits.append("Accounting and Financial Management, Analytics stream")
    w = coop_window()
    if w:
        if w["days"] > 0:
            bits.append(f"co-op term {COOP_TERM}, {w['days']:,} days from this build ({TODAY.isoformat()})")
        elif w["end"] >= TODAY:
            bits.append(f"co-op term {COOP_TERM}, under way at this build ({TODAY.isoformat()})")
        else:
            bits.append(f"co-op term {COOP_TERM}, past at this build ({TODAY.isoformat()})")
    f = featured_subtotal()
    bits.append(f"{f['n']} featured pieces: {f['words']:,} words, {f['figures']} figures, {f['tables']} tables")
    return " \u00b7 ".join(bits)

def p3(v):
    """A unit-sphere position at three decimals, trailing zeros dropped, the
    same function the check uses to read it back."""
    return ",".join(("%.3f" % x).rstrip("0").rstrip(".") or "0" for x in v)


_by_slug_all = {p["slug"]: p for p in P}

def atlas_facts():
    """The Atlas's facts, computed once from the placement and cached: the
    home page prints from the same dict the six wall labels are written
    from, so the two cannot disagree about what a mark is."""
    if not ATLAS.get("facts"):
        ATLAS["facts"] = atlas_mod.facts(ATLAS["points"], ATLAS["regions"])
    return ATLAS["facts"]

def page_atlas():
    pts, regs = ATLAS["points"], ATLAS["regions"]
    F = atlas_facts()
    LABELS = atlas_mod.labels(F)

    by = {}
    for q in pts:
        by.setdefault(q["s"], []).append(q)

    # Independent work first, then personal, then coursework, and by size
    # inside each. The old order was section count alone, which opened the
    # index on a course document and buried the writing the page exists for.
    RANK = {"independent": 0, "personal": 1, "course": 2, "author": 3}
    ordered = sorted((r for r in regs if by.get(r["s"])),
                     key=lambda r: (RANK.get(r["surface"], 3),
                                    -len(by[r["s"]]), r["t"]))

    blocks = []
    for r in ordered:
        items = by[r["s"]]
        # The list implies the class, a missing level means the ordinary
        # third level, and three decimals place a mark within a fifth of a
        # pixel at the largest radius the page draws. Nothing about the data
        # changes; check 11a reads every mark back against the placement.
        lis = "\n".join(
            '<li data-p="%s" data-w="%d"%s%s%s><a href="%s">%s</a></li>'
            % (p3(q["p"]), q.get("w", 0),
               (' data-l="%d"' % q["l"]) if q["l"] != 3 else "",
               (' data-n="%d"' % q["n"]) if q["n"] > 1 else "",
               (' data-o="%s"' % ",".join(q["o"])) if q.get("o") else "",
               q["u"], esc(q["t"]))
            for q in items)
        word = "section" if len(items) == 1 else "sections"
        pc = _by_slug_all.get(r["s"])
        row = ("%s words &#183; %d figures &#183; %d tables"
               % (format(pc["words"], ","), pc["figures"], pc["tables"])) if pc else ""
        meta = " &#183; ".join(x for x in (
            esc(r["k"]), esc(r["c"] or SURF_NAME[r["surface"]]), esc(r["d"]), row) if x)
        # the author's entry carries his card as a native disclosure, reachable
        # from the keyboard like everything else in the list
        extra = ("        <details class=\"acard\"><summary>The author's card</summary>\n"
                 "          <p class=\"acard-p\" id=\"author-card\">%s</p>\n"
                 "        </details>\n" % esc(author_card()).replace("&#183;", "&#183;")) if r["s"] == "author" else ""
        blocks.append(
            '      <section class="areg" data-s="%s" data-k="%s" data-surface="%s"\n'
            '        data-c="%s,%s,%s" data-r="%s" data-t="%s" data-u="%s">\n'
            '        <h2 class="areg-h"><a href="%s">%s</a>\n'
            '          <span class="areg-n">%d %s</span></h2>\n'
            '        <p class="areg-m">%s</p>\n'
            '        <ol class="areg-l">\n%s\n        </ol>\n%s'
            '      </section>'
            % (r["s"], r["k"], r["surface"], r["p"][0], r["p"][1], r["p"][2], r["r"],
               esc(r["t"]), r["u"], r["u"], esc(r["t"]), len(items), word,
               meta, lis, extra))

    plates, guide = [], []
    for i, L in enumerate(LABELS, 1):
        paras = "\n          ".join("<p>%s</p>" % b for b in L["body"])
        plates.append(
            '        <article class="plate" id="label-%d" data-stage="%s"%s>\n'
            '          <p class="plate-n"><b>%02d</b> <span>/ %02d</span></p>\n'
            '          <h2 class="plate-h">%s</h2>\n'
            '          %s\n'
            '        </article>' % (i, L["stage"], "" if i == 1 else " hidden",
                                    i, len(LABELS), L["title"], paras))
        guide.append(
            '          <li><a href="#label-%d" data-step="%d">'
            '<b>%02d</b> %s</a></li>' % (i, i, i, L["title"].rstrip(".")))

    # Every chord endpoint must be a placed document, or the sphere would be
    # asked to draw a relationship to nowhere. A miss here is a build defect,
    # not a datum to drop quietly.
    regslugs = {r["s"] for r in ordered}
    for a, b in ATLAS.get("edges", []):
        if a not in regslugs or b not in regslugs:
            raise SystemExit("atlas edge names an unplaced document: %s -> %s"
                             % (a, b))
    F["js"]["lk"] = [list(e) for e in ATLAS.get("edges", [])]

    nsec, ndoc = len(pts), len(ordered)
    zones_a = ",".join("%.3f" % ATLAS["zones"][z][1] for z in ("independent", "course") if z in ATLAS["zones"])
    body = ATLAS_BODY.format(nsec=format(nsec, ","), ndoc=ndoc, ATLAS_ZONES_A=zones_a,
                             mark_atlas=marks_mod.svg("atlas"),
                             plates="\n".join(plates), guide="\n".join(guide),
                             facts=json.dumps(F["js"], separators=(",", ":")).replace("</", "<\\/"),
                             lede=("{} marks from {} documents and the author: {} "
                                   "independent works, {} personal "
                                   "investigations, {} course references, and "
                                   "one anchor for the author. "
                                   "Every mark is a link into a passage."
                                   .format(format(F["total"], ","), F["docs"],
                                           F["indD"], F["perD"], F["couD"])),
                             blocks="\n".join(blocks))
    return head("Atlas · " + SHORT,
                "All %s sections of all %d documents on this site, and the author, placed on a "
                "sphere by the document they belong to and linked to the passage "
                "itself." % (format(nsec, ","), ndoc - 1),
                "atlas.html",
                extra='<script src="' + asset("atlas.js") + '" defer></script>') + body + foot()


# The teaser's size band: the Atlas draws radius 0.55 + 0.028 * sqrt(words),
# and at teaser scale that rule is quantised to ten bands on sqrt(words) so
# a missing digit, the smallest band, is the common case and costs nothing.
def teaser_band(w):
    import math
    return min(9, int(math.sqrt(max(0, w)) / 13))

def atlas_teaser_bits():
    """The home page draws the same sphere small, so the payload is the same
    positions and nothing else: no headings, no links, no second copy of the
    data. Two decimals is a hundredth of the radius, which at teaser size is
    well under a pixel, and it keeps the whole thing near six kilobytes over
    the wire.

    The fourth field carries the kind letter and, when the mark's apportioned
    word weight puts it above the smallest size band, a band digit straight
    after it: "i" is a mark in independent work in the smallest band, "i2"
    the same kind two bands up. The bands are the Atlas's own size rule
    quantised, so the home page and the atlas make the same claim about the
    same points; check 11a holds the positions to the placement pass."""
    code = {"independent": "i", "personal": "p", "course": "c", "author": "a"}
    surf = {r["s"]: ("t" if r["k"] == "Tool" else code[r["surface"]])
            for r in ATLAS["regions"]}
    out = []
    for q in ATLAS["points"]:
        band = teaser_band(q.get("w", 0))
        mark = surf[q["s"]] + ("" if band == 0 else str(band))
        out.append("%.2f,%.2f,%.2f,%s" % (q["p"][0], q["p"][1], q["p"][2], mark))
    return (format(len(ATLAS["points"]), ","), ";".join(out),
            format(len([q for q in ATLAS["points"] if q["n"] > 1]), ","))


def atlas_home_links():
    """The connective layer for the home sphere. The positions stay in
    data-pts, where check 11a reads them back against the placement; this
    carries only what a chord needs: the documents (centre, disc radius, title,
    address, kind, in placement order), which document each mark belongs to, run-length
    over the payload order, and the links edges() harvested from prose, as
    index pairs with their direction. No headings and no second copy of the
    marks, so the home page still draws from one placement and one harvest."""
    regs = ATLAS["regions"]
    idx = {r["s"]: i for i, r in enumerate(regs)}
    docs = [dict({"t": r["t"], "u": r["u"], "k": r["k"], "o": r["surface"],
                  "p": [round(x, 4) for x in r["p"]], "r": round(r["r"], 4)},
                 **({"card": author_card()} if r["surface"] == "author" else {})) for r in regs]
    own, run, last = [], 0, None
    for q in ATLAS["points"]:
        i = idx[q["s"]]
        if i == last:
            run += 1
        else:
            if last is not None:
                own.append(f"{last}*{run}" if run > 1 else str(last))
            last, run = i, 1
    if last is not None:
        own.append(f"{last}*{run}" if run > 1 else str(last))
    lk = [[idx[a], idx[b]] for a, b in ATLAS.get("edges", []) if a in idx and b in idx]
    return json.dumps({"docs": docs, "own": ",".join(own), "lk": lk},
                      separators=(",", ":")).replace("</", "<\\/")


def page_controls(register, instrument, counts, summary):
    """The tests of controls: the register, the page wall and the
    falsification ledger. Every glyph and every number on it is a record;
    check 29 reads the page back against the records on every build."""
    body = f"""
<section class="band shell colo" id="controls-top">
  <div class="sechead"><div class="markhead">{marks_mod.svg("controls")}<h1>What this site claims, what tests it, and what happened when each claim was made false</h1></div><span class="count">Tests of controls</span></div>
  <div class="prose measure">
    <p>A register that prints <b>held</b> beside every claim proves only that the checks agree with
    themselves. In the language of audit that is inquiry: a control described, not observed. A test
    of controls is different. The control is watched operating, and a control that has never been
    seen to fail is not evidence that it can. So every check on this site has a falsification on
    record: an edit to a copy of the site that makes the claim false at its source (a piece, the
    content, a font, the workflow, or the build's own code), after which the whole build is run in
    that copy and must refuse, naming the check. A claim prints <b>held</b> only while a current,
    caught falsification stands behind every check it cites; otherwise it prints <b>untested</b>.
    A claim nothing tests prints <b>asserted</b>; a claim measured in a browser prints <b>not yet
    measured</b> when its record is older than the page.</p>
    <p>Nothing on this page is typed. Every number is a check's own tally or a record's count, every
    glyph in the two walls below is one record, and check 29 reads this page back against the
    records on every build. The <a href="colophon.html">colophon</a> says how the site is built and
    defines every number it counts; this page says which of its claims are tested, which are
    asserted, which are stale, and what happened when each was false.</p>
  </div>
</section>

<section class="band shell colo" id="register">
  <div class="sechead"><h2>The register</h2><span class="count">{summary["rows"]} claims</span></div>
  {register}
</section>

<section class="band shell colo ground" id="instrument">
  <div class="sechead"><h2>The same records, one glyph each</h2><span class="count">{counts["glyphs"]:,} glyphs</span></div>
  <div class="prose measure">
    <p>One line per page and one column per check that looks at pages. A glyph is a record: the
    check's outcome on that page for this build, or the browser's current measurement of it. A blank
    is a check that does not look at that page, so the columns that reach only the generated pages
    show their reach as absence. Under it, one line per check and one glyph per falsification.</p>
  </div>
  {instrument}
</section>

<section class="band shell colo" id="not-shown">
  <div class="sechead"><h2>What this page cannot show</h2><span class="count">Limits</span></div>
  <div class="prose measure">
    <p>Its own glyph. The cell for check 29 on this page is blank: a check that graded its own
    outcome could never settle, so the page is held to the records by a check the page does not
    grade in turn.</p>
    <p>Whether the deploy gate operated on a given publish. The workflow deploys only what the build
    passed, and a run that fails leaves no page to print its failure on; the record of that is the
    repository's Actions page. The falsifications were written by the same hand as the checks and
    break what the checks look for; each is described in one sentence so a reader can judge whether
    it is the failure that matters. A wall of held glyphs is the honest read-out of a site that
    refuses to publish a failure; its blanks are the argument.</p>
  </div>
</section>
"""
    return head(f"Controls · {SHORT}",
                "Every claim this site makes about itself, the check that tests it, and what happened when the claim was deliberately made false.",
                "controls.html") + body + foot()


def page_404():
    """Generated like every other shell page, so its piece count and contact
    address cannot fall behind. It used to be the one page the build touched
    but never rewrote, and it sat at 21 pieces and a stale email for months."""
    body = f"""<div class="hero lost shell">
  <p class="eyebrow accent">404</p>
  <h1 class="display lost-h">That page is not here.</h1>
  <p class="lede">The address may have a typo, or the piece may have been renamed. The library holds
  all {len(P)} pieces<span class="jsonly">, and pressing <kbd>/</kbd> searches them from anywhere</span>.</p>
  <p class="plate-nav">
    <a class="pbtn pbtn-go" href="library.html">Open the library <span aria-hidden="true">&#8594;</span></a>
    <a class="pbtn" href="index.html">&#8592; Home</a>
    <a class="pskip" href="atlas.html">Or every section, on one sphere</a>
  </p>
</div>
"""
    out = head("Page not found \u00b7 " + SHORT,
               f"That address is not on this site. The library holds all {len(P)} pieces.",
               "404.html") + body + foot()
    # GitHub Pages serves this file's content at ANY missing path, including
    # nested ones, where relative URLs stop resolving: /foo/bar rendered the
    # page unstyled with every link broken. Every static relative reference
    # is therefore made root-relative here. Fragment, absolute, data: and
    # mailto: URLs pass through untouched.
    return re.sub(r'\b(href|src)="(?!https?:|/|#|data:|mailto:)', r'\1="/', out)


# ------------------------------------------------------- service worker ----
SW_TEMPLATE = r"""/* Offline machinery for the whole site. Generated by
   build/build_site.py; do not edit by hand, the next build overwrites it.
   Two caches with different lifetimes: CORE precaches the installable tools,
   and its versioned name retires it whenever a cached file changes. PAGES
   holds everything a reader has visited, plus the full offline copy if they
   asked for one. Its name is a digest of the contents of every file the
   offline copy lists, so a publish changes it; on activate the new worker
   carries every entry of the previous generation across before deleting
   it, so nothing a reader saved is lost. A saved full copy then refreshes
   itself: the manifest carries a digest per file, and only the files whose
   digest moved are fetched again. Caches named term-* belong to the /term/
   instrument's own worker, which manages its own versions; they are not
   this worker's to delete. */
const VERSION  = "__VERSION__";
const CORE     = "site-" + VERSION;
const PAGES    = "site-pages-__PAGES__";
const MANIFEST = "offline-manifest.json";
const FILES    = __FILES__;
// The editor is never served from this cache: an administrative page read
// from a stale copy would show yesterday's list and publish over today's.
// It goes to the network every time, is stored by nothing here, and is
// dropped from any earlier generation that held it.
const NEVER_STORED = ["admin.html"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CORE)
      // addAll is all-or-nothing, so one missing file would leave the tools
      // with no cache at all. Each file is added on its own and a failure is
      // survivable: the rest still work offline.
      .then(c => Promise.all(FILES.map(f => c.add(f).catch(() => null))))
      .then(() => self.skipWaiting())
  );
});

/* Carry the previous generation across. Every entry the reader held is
   copied into the new cache before the old one is deleted; a page copied
   this way is one publish old until it is visited (the fetch handler
   refreshes it then) or until the full copy syncs itself below. */
async function migrate() {
  const keys = await caches.keys();
  const old = keys.filter(k => k.indexOf("site-pages-") === 0 && k !== PAGES);
  if (!old.length) return false;
  const nc = await caches.open(PAGES);
  for (const k of old) {
    const oc = await caches.open(k);
    for (const req of await oc.keys()) {
      if (await nc.match(req)) continue;
      const res = await oc.match(req);
      if (res) await nc.put(req, res);
    }
    await caches.delete(k);
  }
  return true;
}

self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    await migrate();
    const keys = await caches.keys();
    await Promise.all(keys
      .filter(k => k !== CORE && k !== PAGES && k.indexOf("term-") !== 0)
      .map(k => caches.delete(k)));
    await self.clients.claim();
    // a saved full copy refreshes itself against the new manifest
    const c = await caches.open(PAGES);
    for (const f of NEVER_STORED) await c.delete(f);
    if (await c.match(MANIFEST)) await sync(broadcast, false);
  })());
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (NEVER_STORED.indexOf(url.pathname.replace(/^\//, "")) >= 0) {
    e.respondWith(fetch(req).catch(() =>
      new Response("The editor is never served from the cache; it needs the network.",
        { status: 503, headers: { "content-type": "text/plain; charset=utf-8" } })));
    return;
  }

  // Cache first, refresh behind: a click on a saved page opens from disk
  // with no network wait at all, while the fetch that follows replaces the
  // stored copy so the next click is current. A page seen after a publish
  // is therefore at most one visit old, and never slow.
  e.respondWith(
    caches.match(req).then(hit => {
      const refresh = fetch(req)
        .then(res => {
          if (res && res.ok && res.type === "basic") {
            const copy = res.clone();
            caches.open(PAGES).then(c => c.put(req, copy)).catch(() => {});
          }
          return res;
        });
      if (hit) { refresh.catch(() => {}); return hit; }
      return refresh.catch(() =>
        caches.match(url.pathname.replace(/^\//, "") || "index.html")
          .then(h2 => h2 || caches.match("index.html")));
    })
  );
});

async function broadcast(m) {
  const cs = await self.clients.matchAll({ includeUncontrolled: true });
  cs.forEach(c => c.postMessage(m));
}

/* The full offline copy, saved or refreshed by the same routine: read the
   live manifest, compare each file's digest with the manifest last synced,
   fetch what is new or changed, drop what the site no longer lists, then
   store the manifest itself as the record of what is held. "force" fetches
   everything, which is what the colophon's button asks for. */
async function sync(tell, force) {
  let man;
  try {
    man = await (await fetch(MANIFEST, { cache: "no-cache" })).json();
  } catch (err) { tell({ type: "cache-all-done", ok: 0, failed: -1 }); return; }
  const c = await caches.open(PAGES);
  const heldRes = await c.match(MANIFEST);
  let held = null;
  try { held = heldRes ? await heldRes.json() : null; } catch (err) { held = null; }
  const was = (held && held.digests) || {};
  const now = man.digests || {};
  const files = man.files || [];
  const todo = [];
  for (const f of files) {
    if (force || !was[f] || was[f] !== now[f] || !(await c.match(f))) todo.push(f);
  }
  // files the site no longer lists leave the copy
  for (const req of await c.keys()) {
    const name = new URL(req.url).pathname.replace(/^\//, "");
    if (name && name !== MANIFEST && was[name] && !now[name]) await c.delete(req);
  }
  let ok = 0, failed = 0, i = 0;
  const pool = 6;
  async function worker() {
    while (i < todo.length) {
      const f = todo[i++];
      try {
        const res = await fetch(f, { cache: "no-cache" });
        if (res && res.ok) { await c.put(f, res); ok++; }
        else failed++;
      } catch (err) { failed++; }
      if ((ok + failed) % 5 === 0 || ok + failed === todo.length)
        tell({ type: "cache-all-progress", done: ok + failed, total: todo.length });
    }
  }
  await Promise.all(Array.from({ length: pool }, worker));
  if (!failed) {
    await c.put(MANIFEST, new Response(JSON.stringify(man),
      { headers: { "content-type": "application/json" } }));
  }
  tell({ type: "cache-all-done", ok, failed, total: todo.length, held: await count(c, files), of: files.length, version: man.version });
}

async function count(c, files) {
  let n = 0;
  for (const f of files) if (await c.match(f)) n++;
  return n;
}

/* What this phone holds, read from the cache rather than remembered: how
   many of the listed files are present, which manifest version they were
   synced against, and whether that is the live version when the network
   can say. */
async function status(tell) {
  const c = await caches.open(PAGES);
  const heldRes = await c.match(MANIFEST);
  let held = null;
  try { held = heldRes ? await heldRes.json() : null; } catch (err) { held = null; }
  let live = null;
  try { live = await (await fetch(MANIFEST, { cache: "no-cache" })).json(); } catch (err) { live = null; }
  const files = (held || live || {}).files || [];
  tell({ type: "status", held: await count(c, files), of: files.length,
         saved: !!held, version: held ? held.version : null,
         live: live ? live.version : null });
}

self.addEventListener("message", e => {
  const msg = e.data || {};
  const tell = m => { if (e.source) e.source.postMessage(m); };
  if (msg.type === "cache-all") {
    e.waitUntil(sync(tell, true));
  } else if (msg.type === "status") {
    e.waitUntil(status(tell));
  } else if (msg.type === "drop-all") {
    e.waitUntil(caches.delete(PAGES).then(() => tell({ type: "drop-all-done" })));
  }
});
"""

def page_sw(pages_version="v1"):
    """A real offline cache, generated so the file list and the version cannot
    fall behind. Three tools register this and three manifests promise the
    reader they work offline; the placeholder that shipped before cached
    nothing, so a reload with no connection failed and the promise was false.

    Precached: the installable tools and the icons their manifests name. They
    are single self-contained files that request nothing else, which is what
    makes a precache honest here rather than a partial one. The cache name
    carries a digest of those files, so publishing a new version of a tool
    retires the old cache instead of serving a stale page forever.

    The page cache is named by a digest of the offline copy's contents, and
    the worker carries the previous generation across on activate: a publish
    used to delete a reader's saved copy outright (measured: 182 files to 7
    after a one-character change to one page), which contradicted the
    colophon's promise that the copy refreshes itself."""
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
    return (SW_TEMPLATE.replace("__VERSION__", version)
            .replace("__PAGES__", pages_version)
            .replace("__FILES__", files))


# ----------------------------------------------------- sitemap, robots ----
_MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}

def piece_month(d):
    """A piece's own date, "August 2026", as the sitemap's YYYY-MM, or None
    when the field does not carry a month. The build date is never used: a
    sitemap stamped with the day of the last build claims every page changed
    that day, and it rewrote itself on the first run of every new day."""
    m = re.match(r"([A-Z][a-z]+)\s+(\d{4})$", (d or "").strip())
    if not m or m.group(1) not in _MONTHS:
        return None
    return "%s-%02d" % (m.group(2), _MONTHS[m.group(1)])

def page_sitemap():
    """Every address on the site, in one file, so a search engine does not have
    to guess which of fifty-eight files matter. Generated from the same list
    that builds the pages, so a piece cannot be listed here and missing there.
    lastmod is each piece's own month; the generated pages carry the latest
    piece month, because that is when their content last changed."""
    months = {x["url"]: piece_month(x.get("d")) for x in P}
    have = [m for m in months.values() if m]
    latest = max(have) if have else None
    urls = [("", "1.0", latest)] + [(p, "0.8", latest) for p in SHELL_PAGES if p != "index.html"]
    urls += [(x["url"], "0.7" if x["featured"] else "0.6", months[x["url"]]) for x in P]
    seen, rows = set(), []
    for loc, pri, stamp in urls:
        if loc in seen or loc == "404.html":
            continue
        seen.add(loc)
        rows.append(f"  <url>\n    <loc>{SITE_URL}/{loc}</loc>\n"
                    + (f"    <lastmod>{stamp}</lastmod>\n" if stamp else "")
                    + f"    <priority>{pri}</priority>\n  </url>")
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
        "name": f"{SHORT} · portfolio",
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
    same_as = [u for u in (LINKEDIN, GITHUB) if u]
    if same_as:
        data["sameAs"] = same_as
    return ('<script type="application/ld+json">'
            + json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
            + "</script>")


# One list, in build/claims.py, because the register, the falsification wall
# and build/audit.js all read it from there. Kept as a literal here it drifted:
# a page added to this tuple and not to that list is generated, checked and
# never measured in a browser, and nothing said so.
SHELL_PAGES = tuple(claims.SHELL)

# ------------------------------------------------------------- checks ----
# The build guarantees what it generates. Everything it merely touches was
# still hand-maintained, and drifted: twenty-two pages claimed a canonical URL
# of /none, the footer printed the old address while linking to the new one,
# and two tools asked for an icon that was never there. None of that was
# visible in a diff, because nothing was looking. These three assertions look.
# They run on every build and fail it, which is the same move as the colophon
# applied to the build: state the rule, then let something disagree with you.

def _claims_ctx(problems=()):
    """What the register and the instrument are built from: the tallies and
    per-page records of the checks that have run, the audit's state, the
    falsifications on record, and the checks whose problems exist so far."""
    all_pages = list(SHELL_PAGES) + [p["url"] for p in P] + [k + ".html" for k in exceptions()["transcripts"]]
    fired = {m.group(1) for m in (re.match(r"check (\S+):", x) for x in problems) if m}
    return {"tally": getattr(check_site, "tally", {}), "records": getattr(check_site, "records", {}),
            "shell_pages": list(SHELL_PAGES), "all_pages": all_pages, "aux_pages": list(claims.AUX),
            "audit": claims.audit_state(OUT, set(SHELL_PAGES), all_pages + list(claims.AUX)),
            "negatives": claims.negatives_state(ROOT), "fired": fired, "problems": []}


def _look(cid, page):
    """A check looked at a page: recorded as held until a problem names it."""
    check_site.records.setdefault(cid, {}).setdefault(page, True)


_PAGE_IN_PROBLEM = re.compile(r"^([A-Za-z0-9_.\-]+\.(?:html|webmanifest|json|css|js)): ")


def _p(cid, msg):
    """A problem line, named by the check that found it. When the line opens
    with a file name that check looked at, the record for that page turns
    false; otherwise the check's site-level record does."""
    m = _PAGE_IN_PROBLEM.match(msg)
    rec = check_site.records.setdefault(cid, {})
    page = "site"
    if m and m.group(1) in rec:
        page = m.group(1)
    else:
        m2 = re.match(r"^([\w.\-]+): ", msg)
        if m2 and (m2.group(1) + ".html") in rec:
            page = m2.group(1) + ".html"
    rec[page] = False
    return "check %s: %s" % (cid, msg)


def check_site():
    problems, files = [], set(os.listdir(OUT))
    # every check tallies what it looked at, so the register on the colophon
    # can print a denominator beside each claim rather than a bare pass
    T = check_site.tally = {}
    # and which pages each check looked at, with the outcome per page, so the
    # instrument on the controls page can draw one glyph per (page, check)
    R = check_site.records = {}
    look = _look
    # check 13's coverage is known up front (the scan runs in main's fixpoint,
    # after the pages are written), so the controls page can be read back
    # against it by check 29
    for f in SHELL_PAGES:
        look("13", f)
    T["numerals"] = {"n": getattr(_typed_numerals, "checked", 0), "pages": len(SHELL_PAGES)}
    html_files = sorted(f for f in files if f.endswith(".html"))
    for sub in ("cards", "fonts", "content", "build"):
        if os.path.isdir(os.path.join(OUT, sub)):
            files |= {sub + "/" + f for f in os.listdir(os.path.join(OUT, sub))}

    def local(u):
        if not u or re.match(r"^(https?:|mailto:|tel:|#|data:|//|javascript:)", u):
            return None
        # The site is served at the domain root, so a root-relative URL names
        # the same file its bare form does. 404.html uses them on purpose:
        # GitHub Pages serves that page at any missing path, at any depth.
        return u.lstrip("/").split("#")[0].split("?")[0] or None

    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".html"):
            continue
        text = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore").read()
        look("1", f); look("2", f); look("3", f)

        # 1. every canonical resolves to a file that exists
        T.setdefault("hosts", {"pages": 0})["pages"] += 1
        for m in re.finditer(r'<link rel="canonical" href="([^"]+)"', text):
            href = m.group(1)
            T.setdefault("canonicals", {"n": 0})["n"] += 1
            if not href.startswith(SITE_URL):
                problems.append(_p("1", f"{f}: canonical points off-site, {href}"))
                continue
            rest = href[len(SITE_URL):].lstrip("/") or "index.html"
            if rest not in files:
                problems.append(_p("1", f"{f}: canonical is {href}, which is not a file here"))

        # 2. no page names a host other than this one
        # bare, not just inside a URL: the stale address that survived the
        # move was sitting in link text, where a URL pattern never saw it
        for host in set(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9-]*\.github\.io\b", text)):
            if host != HOST:
                problems.append(_p("2", f"{f}: mentions {host}, which is not this site"))

        # 3. every local href and src resolves. Script and style blocks are cut
        # first: a page that builds its own markup client-side has href= inside
        # a template literal, and `${esc(s.url)}` is live code, not a dead link.
        prose = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", text, flags=re.S | re.I)
        tl = T.setdefault("links", {"n": 0, "pages": 0})
        tl["pages"] += 1
        for m in re.finditer(r'(?:href|src)="([^"]+)"', prose):
            u = local(m.group(1))
            # reader.html builds a couple of URLs in script; those are not links
            if u and "' +" not in u:
                tl["n"] += 1
                if u not in files:
                    problems.append(_p("3", f"{f}: links to {u}, which does not exist"))

    # 4. every manifest icon resolves
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".webmanifest"):
            continue
        look("4", f)
        try:
            data = json.load(open(os.path.join(OUT, f), encoding="utf-8"))
        except Exception as e:
            problems.append(_p("4", f"{f}: is not readable as JSON ({e})"))
            continue
        for icon in data.get("icons", []):
            T.setdefault("icons", {"n": 0})["n"] += 1
            if icon.get("src") not in files:
                problems.append(_p("4", f"{f}: names icon {icon.get('src')}, which does not exist"))

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
        look("5", f)
        for fid in set(re.findall(r'id="(fs-[a-z0-9]+)"', text)):
            T.setdefault("figscope", {"n": 0})["n"] += 1
            if ("#" + fid) not in sheet:
                problems.append(_p("5", f"{f}: shows figure {fid}, which has no colour "
                                f"scope in figures.css"))

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
        look("6", f)
        # per document body: the reader edition embeds every converted note,
        # each with its own body and its own single heading
        bodies = re.findall(r'<article class="docbody"[^>]*>(.*?)</article>', text, re.S)
        counts = [len(re.findall(r"<h1[\s>]", b)) for b in bodies] if bodies else [len(re.findall(r"<h1[\s>]", text[i:]))]
        T.setdefault("onehead", {"docs": 0})["docs"] += len(counts)
        for n in counts:
            if n > 1:
                problems.append(_p("6", f"{f}: {n} top-level headings in a document body; "
                                f"all but the first are hidden by the stylesheet"))
                break

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
        T.setdefault("heads", {"pages": 0})["pages"] += 1
        look("7", f)
        if j == -1:
            problems.append(_p("7", f"{f}: has no </head>"))
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
                problems.append(_p("7", f"{f}: <{tag}> inside <head> ends the head early; "
                                f"everything after it is parsed into the body"))

    # 8. every mark on the atlas lands somewhere real. The globe is only worth
    # having if a click opens the passage it names, and the passage is named by
    # an anchor inside another document, which nothing else on the site checks.
    # A heading renamed in a piece changes its generated id, and this is what
    # notices before the mark starts pointing at nothing.
    apath = os.path.join(OUT, "atlas.html")
    if os.path.exists(apath):
        atext = open(apath, encoding="utf-8", errors="ignore").read()
        marks = re.findall(r'<li data-p="[^"]*"[^>]*>\s*<a href="([^"]+)"', atext)
        want = {}
        for href in marks:
            f, _, frag = href.partition("#")
            want.setdefault(f, set()).add(frag)
        T["atlas_marks"] = {"n": len(marks), "files": len(want)}
        look("8", "atlas.html")
        for f, frags in sorted(want.items()):
            fp = os.path.join(OUT, f)
            if not os.path.exists(fp):
                problems.append(_p("8", f"atlas.html: {len(frags)} marks point into {f}, "
                                f"which does not exist"))
                continue
            have = set(re.findall(r'\bid="([^"]+)"',
                                  open(fp, encoding="utf-8", errors="ignore").read()))
            missing = sorted(x for x in frags if x and x not in have)
            if missing:
                problems.append(_p("8", f"atlas.html: {len(missing)} mark(s) point at "
                                f"anchors {f} does not carry, first is "
                                f"#{missing[0]}"))
        if marks and not want:
            problems.append(_p("8", "atlas.html: carries no marks"))

    # 9. every listed piece has a file behind it
    T["listed"] = {"n": len(P)}
    for x in P:
        look("9", x["url"])
        if x["url"] not in files:
            problems.append(_p("9", f"content/pieces.json: {x['slug']} points at {x['url']}, which does not exist"))

    # 10. every character the pages show that Inter could render is in the
    # self-hosted subset. A glyph outside the subset silently falls to the
    # metric-matched fallback, which is exactly the mixed typography the
    # self-hosting exists to prevent. When this fires, re-subset:
    #   pyftsubset node_modules/inter-ui/variable/InterVariable.woff2
    #     --unicodes-file=<updated set> --flavor=woff2 ...
    try:
        _sub = {int(x) for x in open(
            os.path.join(HERE, "font-subset-cmap.txt")).read().split(",")}
        _full = {int(x) for x in open(
            os.path.join(HERE, "font-full-cmap.txt")).read().split(",")}
        _missing = {}
        _seen_chars = set()
        _ts = T.setdefault("subset", {"chars": 0, "pages": 0})
        for f in sorted(os.listdir(OUT)):
            if not f.endswith(".html"):
                continue
            raw = open(os.path.join(OUT, f), encoding="utf-8",
                       errors="ignore").read()
            body = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", raw,
                          flags=re.S | re.I)
            body = re.sub(r"<[^>]+>", "", body)
            _ts["pages"] += 1
            look("10", f)
            for ch in set(body):
                cp = ord(ch)
                if cp > 32:
                    _seen_chars.add(cp)
                if cp > 32 and cp in _full and cp not in _sub:
                    _missing.setdefault(ch, f)
        _ts["chars"] = len(_seen_chars)
        for ch, f in sorted(_missing.items()):
            problems.append(_p("10", 
                "font subset: U+%04X (%r) in %s renders in the fallback, "
                "not Inter; re-subset InterVariable-sub.woff2" % (ord(ch), ch, f)))
    except FileNotFoundError:
        problems.append(_p("10", "font subset: build/font-*-cmap.txt missing"))

    # 11. the injected chrome carries the palette as literals, because the
    # standalone pieces do not load site.css. Nothing kept the two in
    # agreement: a palette change in the stylesheet would ship every piece
    # with last year's chrome. Every colour the chrome states must therefore
    # exist somewhere in site.css's own vocabulary (white and black are
    # allowed: the pill states them on purpose, on surfaces that never
    # change with the palette).
    def _hexes(text):
        out = set()
        for h in re.findall(r'#([0-9a-fA-F]{6})\b', text):
            out.add(h.lower())
        for h in re.findall(r'#([0-9a-fA-F]{3})\b(?![0-9a-fA-F])', text):
            out.add("".join(c * 2 for c in h.lower()))
        for r, g, b in re.findall(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', text):
            out.add("%02x%02x%02x" % (int(r), int(g), int(b)))
        return out
    try:
        _vocab = _hexes(open(os.path.join(OUT, "site.css"), encoding="utf-8").read())
        _chrome = _hexes(RETURN_BAR) | _hexes(RETURN_PILL)
        T["chrome"] = {"n": len(_chrome)}
        look("11", "site")
        _stray = _chrome - _vocab - {"ffffff", "000000"}
        for h in sorted(_stray):
            problems.append(_p("11", "injected chrome: #%s is not a colour site.css knows; "
                            "the chrome palette in build_site.py has drifted from "
                            "the stylesheet" % h))
    except FileNotFoundError:
        problems.append(_p("11", "injected chrome: site.css missing, palette unverifiable"))
    # 11a. one placement, two renderers, one picture. The Atlas page's marks
    # and the home page's teaser payload are both read back from the built
    # files and held to the points place() produced: the same count, and the
    # same positions at the precision each carries. A heading harvested from
    # the build's own chrome once put a 1,553rd mark on the sphere and passed
    # every other check, because its anchor resolved.
    pts = ATLAS.get("points") or []
    apath = os.path.join(OUT, "atlas.html")
    if pts and os.path.exists(apath):
        atext = open(apath, encoding="utf-8", errors="ignore").read()
        look("11a", "atlas.html")
        marks = re.findall(r'<li data-p="([^"]+)"', atext)
        links = re.findall(r'<li data-p="[^"]*"[^>]*>\s*<a href="[^"]+"', atext)
        if len(marks) != len(pts) or len(links) != len(pts):
            problems.append(_p("11a", "atlas.html: %d marks and %d links read back, %d points placed"
                            % (len(marks), len(links), len(pts))))
        want = {p3(q["p"]) for q in pts}
        T.setdefault("placement", {})["marks"] = len(marks)
        stray = [m for m in marks if m not in want]
        if stray:
            problems.append(_p("11a", "atlas.html: %d mark(s) at positions the placement did not produce, first %s"
                            % (len(stray), stray[0])))
    ipath = os.path.join(OUT, "index.html")
    if pts and os.path.exists(ipath):
        itext = open(ipath, encoding="utf-8", errors="ignore").read()
        look("11a", "index.html")
        m = re.search(r'data-pts="([^"]*)"', itext)
        tease = [x for x in (m.group(1).split(";") if m else []) if x]
        T.setdefault("placement", {})["teaser"] = len(tease)
        if len(tease) != len(pts):
            problems.append(_p("11a", "index.html: teaser carries %d marks, %d points placed" % (len(tease), len(pts))))
        want2 = {"%.2f,%.2f,%.2f" % (q["p"][0], q["p"][1], q["p"][2]) for q in pts}
        stray2 = [x for x in tease if ",".join(x.split(",")[:3]) not in want2]
        if stray2:
            problems.append(_p("11a", "index.html: %d teaser mark(s) at positions the placement did not produce, first %s"
                            % (len(stray2), stray2[0])))

    # 11a2. the weights add back. Every mark's apportioned word weight is read
    # from the built page and summed; the sum must equal the corpus line, because
    # each document's weights add to its measured count and a shared heading
    # carries the sum of its owners' shares.
    if pts and os.path.exists(apath):
        ws = [int(x) for x in re.findall(r'<li data-p="[^"]*" data-w="(\d+)"', atext)]
        T["weights"] = {"marks": len(ws), "sum": sum(ws)}
        look("11a2", "atlas.html")
        if len(ws) != len(pts):
            problems.append(_p("11a2", "atlas.html: %d marks carry a weight, %d points placed" % (len(ws), len(pts))))
        elif sum(ws) != TOTAL_WORDS:
            problems.append(_p("11a2", "atlas.html: mark weights add to %s, the corpus line says %s"
                            % (format(sum(ws), ","), format(TOTAL_WORDS, ","))))

    # 28. where a document sits is a rule, and the pages hold to it. The rule
    # gives each origin a zone of latitude with the area of its share of the
    # sections, draws each document as a disc of two thirds of its share's
    # area, settles the discs apart inside their zones until no two touch, and
    # lays a document's own sections on an equal-area spiral inside its disc,
    # the first at the centre. Every centre and radius the Atlas index and the
    # home sphere carry is recomputed from the section counts and compared;
    # every disc is held inside its zone and clear of every other; every own
    # mark is held at its spiral position; a shared heading is counted, not
    # held, because it sits between its owners.
    regs = ATLAS.get("regions") or []
    placed_slugs = {r["s"] for r in regs}
    counts28 = {}
    for pt28 in ATLAS.get("points") or []:
        for o28 in (pt28.get("o") or [pt28["s"]]):
            counts28[o28] = counts28.get(o28, 0) + 1
    # the author is a document of the rule too, with the origin the placement gave him
    pieces28 = [p for p in P if p["slug"] in placed_slugs]
    if "author" in placed_slugs:
        pieces28.append({"slug": "author", "surface": "author"})
    rule28, zones28 = atlas_mod.layout(pieces28, counts28)
    want_c = {slug: atlas_mod.centroid_of(e) for slug, e in rule28.items()}
    want_r = {slug: e["r"] for slug, e in rule28.items()}
    T["position"] = {"documents": len(want_c), "pages": 0, "zones": len(zones28), "read_back": 0,
                     "pairs": 0, "overlap": 0, "marks": 0, "shared": 0, "off": 0, "outside": 0}
    def _ang28(a, b):
        d = sum(x * y for x, y in zip(a, b)) / max(1e-9, math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b)))
        return math.acos(max(-1.0, min(1.0, d)))
    def _hold_positions(f, got, radii):
        """got: slug -> (x, y, z) and radii: slug -> disc radius, as the page carries them."""
        look("28", f)
        T["position"]["pages"] += 1
        T["position"]["read_back"] += len(got)
        if set(got) != set(want_c):
            problems.append(_p("28", "%s: carries %d document positions, the rule places %d" % (f, len(got), len(want_c))))
        for slug, xyz in got.items():
            w = want_c.get(slug)
            if w and max(abs(a - b) for a, b in zip(xyz, w)) > 2e-3:
                problems.append(_p("28", "%s: %s sits at %s; its zone, its start and the settling put it at %s"
                                   % (f, slug, ",".join("%.3f" % v for v in xyz), ",".join("%.3f" % v for v in w))))
                break
        for slug, r in radii.items():
            if slug in want_r and abs(r - want_r[slug]) > 2e-3:
                problems.append(_p("28", "%s: %s is drawn as a disc of %.3f rad; two thirds of its share is %.3f"
                                   % (f, slug, r, want_r[slug])))
                break
        for surf, (ytop, ybot) in zones28.items():
            lo = math.acos(max(-1.0, min(1.0, ytop))); hi = math.acos(max(-1.0, min(1.0, ybot)))
            for s2 in sorted(got):
                if rule28.get(s2, {}).get("zone") != surf:
                    continue
                th = math.acos(max(-1.0, min(1.0, got[s2][1])))
                r = radii.get(s2, want_r.get(s2, 0.0))
                if (lo > 1e-9 and th < lo + r - 2e-3) or (hi < math.pi - 1e-9 and th > hi - r + 2e-3):
                    problems.append(_p("28", "%s: %s is %s work and its disc crosses out of its zone" % (f, s2, surf)))
                    break
        slugs = sorted(got)
        shown = 0
        for i28, a in enumerate(slugs):
            for b in slugs[i28 + 1:]:
                T["position"]["pairs"] += 1
                if _ang28(got[a], got[b]) < radii.get(a, want_r.get(a, 0.0)) + radii.get(b, want_r.get(b, 0.0)) - 2e-3:
                    T["position"]["overlap"] += 1
                    if shown < 2:
                        shown += 1
                        problems.append(_p("28", "%s: the discs of %s and %s overlap" % (f, a, b)))
    if regs and os.path.exists(apath):
        got, radii = {}, {}
        for m in re.finditer(r'<section class="areg" data-s="([^"]+)"[^>]*?data-c="([^"]+)" data-r="([^"]+)"', atext, re.S):
            got[m.group(1)] = tuple(float(v) for v in m.group(2).split(","))
            radii[m.group(1)] = float(m.group(3))
        _hold_positions("atlas.html", got, radii)
        # every own mark at its point on the spiral, and inside its disc. The
        # spiral is recomputed by the placement's own formula, so a change to
        # that formula would agree with itself; the disc is the invariant the
        # formula does not share, and it is what caught the first
        # falsification that doubled every ring. A heading several documents
        # carry is placed between them and is counted, not held.
        shown28 = 0
        for m in re.finditer(r'<section class="areg" data-s="([^"]+)".*?</section>', atext, re.S):
            slug = m.group(1); e = rule28.get(slug)
            if not e:
                continue
            lis = list(re.finditer(r'<li data-p="([^"]+)"([^>]*)>', m.group(0)))
            own = [mm for mm in lis if ' data-o="' not in mm.group(2)]
            T["position"]["shared"] += len(lis) - len(own)
            for i28, mm in enumerate(own):
                T["position"]["marks"] += 1
                pt = tuple(float(v) for v in mm.group(1).split(","))
                want = atlas_mod.mark_at(e, i28, len(own))
                if max(abs(a - b) for a, b in zip(pt, want)) > 2e-3:
                    T["position"]["off"] += 1
                    if shown28 < 3:
                        shown28 += 1
                        problems.append(_p("28", "atlas.html: section %d of %d of %s sits at %s; its spiral puts it at %s"
                                           % (i28 + 1, len(own), slug, ",".join("%.3f" % v for v in pt), ",".join("%.3f" % v for v in want))))
                if _ang28(pt, want_c[slug]) > e["r"] + 0.01:
                    T["position"]["outside"] += 1
                    if shown28 < 3:
                        shown28 += 1
                        problems.append(_p("28", "atlas.html: a mark of %s lies %.2f rad from its centre, outside its disc of %.2f"
                                           % (slug, _ang28(pt, want_c[slug]), e["r"])))
    if regs and os.path.exists(ipath):
        m = re.search(r'<script type="application/json" id="atlasmini-docs">(.*?)</script>', itext, re.S)
        if m:
            try:
                docs = json.loads(m.group(1).replace("<\\/", "</"))["docs"]
                url_slug = {p["url"]: p["slug"] for p in P}
                def _slug28(d):
                    return "author" if d.get("o") == "author" else url_slug.get(d["u"])
                got = {_slug28(d): tuple(d["p"]) for d in docs if _slug28(d)}
                radii = {_slug28(d): float(d.get("r", 0)) for d in docs if _slug28(d)}
                _hold_positions("index.html", got, radii)
            except (ValueError, KeyError) as e:
                problems.append(_p("28", "index.html: the sphere's document payload is unreadable (%s)" % e))
        mz = re.search(r'id="atlasmini"[^>]*data-zones="([^"]*)"', itext)
        want_z = ",".join("%.3f" % zones28[z][1] for z in ("independent", "course") if z in zones28)
        if mz and mz.group(1) != want_z:
            problems.append(_p("28", "index.html: the sphere draws its zone parallels at %s; the shares put them at %s" % (mz.group(1), want_z)))

    # 11b. the converted pieces' owned blocks changed nothing outside themselves
    for p in P:
        if os.path.exists(os.path.join(OUT, p["url"])) and \
           "<!--__docend" in open(os.path.join(OUT, p["url"]), encoding="utf-8", errors="ignore").read():
            look("11b", p["url"])
    for line in TAIL_PROBLEMS:
        problems.append(_p("11b", "converted piece: " + line))
    for line in TITLE_PROBLEMS:
        problems.append(_p("11b", "piece title: " + line))

    # 12. the statement's subtotals add to the corpus line. Three origins, one
    # total, and the arithmetic is the reader's to check on the page, so the
    # build checks it first.
    st = surface_totals()
    T["origins"] = {"keys": 4}
    look("12", "site")
    for key, tot in (("n", len(P)), ("words", TOTAL_WORDS),
                     ("figures", TOTAL_FIGS), ("tables", TOTAL_TBLS)):
        got = sum(st[k][key] for k in st)
        if got != tot:
            problems.append(_p("12", "origin totals: %s add to %s, the corpus line says %s"
                            % (key, got, tot)))

    # 14. a superlative in the owner's fields is held to the data. "The largest
    # essay" and "X is the largest piece on the site" are claims a build can
    # test, so it does: the piece carrying "largest essay" must be the essay
    # with the most words, and a piece named as the largest on the site must
    # have the most words of all. A field that stops being true fails the
    # build rather than staying published.
    essays = [x for x in P if x["k"] == "Essay"]
    top_essay = max(essays, key=lambda x: x["words"]) if essays else None
    top_piece = max(P, key=lambda x: x["words"])
    T["superlatives"] = {"fields": 3 * len(P)}
    for x in P:
        look("14", x["url"])
        text = " ".join(str(x.get(k) or "") for k in ("s", "blurb", "demo"))
        if re.search(r"\blargest essay\b", text, re.I) and top_essay and x is not top_essay:
            problems.append(_p("14", "content/pieces.json: %s calls itself the largest essay; %s is, at %s words"
                            % (x["slug"], top_essay["slug"], format(top_essay["words"], ","))))
        for m in re.finditer(r"([A-Z][^.()]*?) is the largest piece on the site", text):
            named = m.group(1).strip().lower()
            # a piece may be named by its title, or by its title before the colon
            full = top_piece["t"].lower()
            if named not in (full, full.split(":")[0].strip()):
                problems.append(_p("14", "content/pieces.json: %s says %s is the largest piece; %s is, at %s words"
                                % (x["slug"], named, top_piece["t"], format(top_piece["words"], ","))))

    # 15. nothing a piece claims has moved. Every numeral, reference,
    # provenance label, chip, anchor id, URL, heading and result sentence in
    # every piece is held to the record in content/invariants.json; a strike
    # or a stale-count fix must be declared in content/ledger.json for the
    # piece, and the record is renewed only by hand (build/invariance.py).
    inv_problems, inv_summary = invariance.check(OUT, P, extra=exceptions()["transcripts"])
    for p in P:
        look("15", p["url"])
    for k in exceptions()["transcripts"]:
        look("15", k + ".html")
    problems.extend((_p("15", _x) for _x in inv_problems))
    check_site.invariance = inv_summary
    T["invariance"] = dict(inv_summary, listed=len(P), transcripts=len(exceptions()["transcripts"]))

    # 18. every self-hosted typeface carries every character its piece shows.
    # fonts/manifest.json records each subset's codepoints and the size of
    # the source's full cmap; a character the piece shows that the source
    # could render and the subset cannot would fall to the fallback face.
    # The manifest is written by the subsetting script, never by hand.
    mpath = os.path.join(OUT, "fonts", "manifest.json")
    if os.path.exists(mpath):
        try:
            man = json.load(open(mpath, encoding="utf-8"))
        except Exception:
            man = None
            problems.append(_p("18", "fonts/manifest.json: unreadable"))
        if man:
            T["fonts"] = {"files": len(man.get("files") or {})}
            by_piece = {}
            for fname, rec in (man.get("files") or {}).items():
                if not os.path.exists(os.path.join(OUT, fname)):
                    problems.append(_p("18", "fonts/manifest.json: %s is listed but missing" % fname))
                    continue
                by_piece.setdefault(rec["piece"], []).append((fname, rec))
            for p in P:
                recs = by_piece.get(p["slug"])
                if not recs:
                    continue
                look("18", p["url"])
                raw = open(os.path.join(OUT, p["url"]), encoding="utf-8", errors="ignore").read()
                if "fonts.googleapis" in raw:
                    problems.append(_p("18", "%s: still loads Google Fonts although fonts/ carries its faces" % p["url"]))
                shown = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.S | re.I)
                shown = html.unescape(re.sub(r"<[^>]+>", " ", shown))
                cps = {ord(c) for c in set(shown) if ord(c) > 32}
                for fname, rec in recs:
                    have = set(rec.get("codepoints") or [])
                    # only characters the face could render matter: a character
                    # outside the family's own repertoire falls back under any
                    # hosting, so the manifest carries each source's cmap
                    fam_cmap = set(((man.get("families") or {}).get(rec.get("family_dir")) or {}).get("cmap") or [])
                    lacking = sorted(c for c in cps if c not in have and c in fam_cmap)
                    for c in lacking[:3]:
                        problems.append(_p("18", "font subset: U+%04X (%r) in %s is not in %s; re-subset" % (c, chr(c), p["url"], fname)))
            for fname in sorted(os.listdir(os.path.join(OUT, "fonts"))):
                if fname.endswith(".woff2") and ("fonts/" + fname) not in (man.get("files") or {}):
                    problems.append(_p("18", "fonts/%s: not in the manifest" % fname))

            # the subsets are distributed under non-reserved internal names
            # (a subset is a Modified Version under the OFL); the rename
            # script records each file's alias and sha256, and a file re-cut
            # without the rename would carry the source's reserved name, so
            # every file is held to the recorded digest
            for fname, rec in (man.get("files") or {}).items():
                fp = os.path.join(OUT, fname)
                if not os.path.exists(fp):
                    continue
                if not rec.get("internal_name"):
                    problems.append(_p("18", "fonts/manifest.json: %s has no internal_name; run the rename" % fname))
                digest = hashlib.sha256(open(fp, "rb").read()).hexdigest()
                if digest != rec.get("sha256"):
                    problems.append(_p("18", "fonts/manifest.json: %s does not match its recorded sha256; run the rename" % fname))
            inter = man.get("inter") or {}
            if inter.get("file"):
                ip = os.path.join(OUT, inter["file"])
                if not os.path.exists(ip) or hashlib.sha256(open(ip, "rb").read()).hexdigest() != inter.get("sha256"):
                    problems.append(_p("18", "%s: does not match the sha256 in fonts/manifest.json; run the rename" % inter["file"]))

    # 17. every listed piece states what it was built from, in the owner's
    # voice: the field is present, never carries an em dash, and never
    # restates the label the template already prints. The field is the
    # complement of "Built from", which is how admin.html asks for it ("one
    # plain line in your own words"), so a value opening with those two
    # words renders as "Built from Built from ..." on the page. Forty-two
    # of them did.
    T["built_from"] = {"n": len(P)}
    for p in P:
        look("17", p["url"])
        bf = (p.get("built_from") or "").strip()
        if not bf:
            problems.append(_p("17", "content/pieces.json: %s has no built_from line" % p["slug"]))
        elif "\u2014" in bf:
            problems.append(_p("17", "content/pieces.json: %s built_from carries an em dash" % p["slug"]))
        elif " ".join(bf.split()[:2]).lower().strip(",;:") == "built from":
            problems.append(_p("17", "content/pieces.json: %s built_from restates the label; "
                            "the field is the complement of \"Built from\"" % p["slug"]))

    # 16. the ledger's class for every piece is what the files show. The
    # colophon prints the ledger's summary, so a stale ledger would print a
    # count the tree does not support; build/ledger.py rewrites it.
    if LEDGER:
        live = invariance.classes(OUT, P)
        T["ledger"] = {"n": len(live)}
        for slug, cls in live.items():
            look("16", slug + ".html")
            said = ((LEDGER.get("pieces") or {}).get(slug) or {}).get("class")
            if said != cls:
                problems.append(_p("16", "content/ledger.json: %s is %s, the files say %s; run build/ledger.py"
                                % (slug, said or "missing", cls)))
    # 19. headings on the generated pages run in order. A level skipped is a
    # section a screen reader's outline cannot place; the colophon claims the
    # order, so the build holds it.
    th = T["headings"] = {"pages": 0, "headings": 0}
    for f in SHELL_PAGES:
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        body = re.sub(r"<(script|style|svg)\b[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
        levels = [int(x) for x in re.findall(r"<h([1-6])[\s>]", body)]
        th["pages"] += 1
        look("19", f)
        th["headings"] += len(levels)
        last = 0
        for lv in levels:
            if lv > last + 1 and last:
                problems.append(_p("19", f"{f}: a heading skips from h{last} to h{lv}"))
                break
            last = lv

    # 20. every generated page opens with a skip link to its main content
    ts = T["skip"] = {"pages": 0}
    for f in SHELL_PAGES:
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        ts["pages"] += 1
        look("20", f)
        if not re.search(r'<a class="skip" href="#main"', text) or 'id="main"' not in text:
            problems.append(_p("20", f"{f}: has no skip link to #main"))

    # 21. every figure on the generated pages carries an accessible name: a
    # top-level svg on a real artboard has role="img" with a label, or a
    # <title> a reader's assistive technology can read, or is marked
    # decorative outright.
    tf = T["fignames"] = {"pages": 0, "figures": 0}
    for f in SHELL_PAGES:
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        tf["pages"] += 1
        look("21", f)
        depth = 0
        for m in re.finditer(r"<(/?)svg\b([^>]*)>", text):
            if m.group(1):
                depth -= 1
                continue
            depth += 1
            if depth != 1:
                continue
            attrs = m.group(2)
            vb = re.search(r'viewBox="([^"]+)"', attrs)
            area = 0
            if vb:
                q = [float(x) for x in re.split(r"[\s,]+", vb.group(1).strip()) if x]
                area = (q[2] * q[3]) if len(q) == 4 else 0
            if area < 6000:
                continue
            tf["figures"] += 1
            inner = text[m.end():m.end() + 600]
            named = (re.search(r'aria-label="[^"]+"|aria-labelledby="[^"]+"', attrs)
                     or re.search(r'aria-hidden="true"', attrs)
                     or re.search(r"<title[\s>]", inner))
            if not named:
                problems.append(_p("21", f"{f}: a figure carries no accessible name"))

    # 22. nothing on any page is loaded from another origin: no script,
    # stylesheet, image, frame, font or media with a src or href on another
    # host, except the Google Fonts typefaces the exceptions name in the
    # pieces that still load them; and no page or script touches the
    # cookie API. Check 2 holds hostnames; this holds what is fetched.
    te = T["external"] = {"pages": 0, "refs": 0, "allowed": 0, "cookie": 0}
    allowed_pages = {p["url"] for p in exceptions()["fonts"]}
    for f in html_files:
        text = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore").read()
        te["pages"] += 1
        look("22", f)
        te["cookie"] += len(re.findall(r"document\.cookie", text))
        for m in re.finditer(r'<(?:script|link|img|iframe|source|video|audio|embed|object)\b[^>]*\b(?:src|href)="(https?://[^"]+)"', text):
            te["refs"] += 1
            host = re.sub(r"^https?://", "", m.group(1)).split("/")[0]
            if f in allowed_pages and host in ("fonts.googleapis.com", "fonts.gstatic.com"):
                te["allowed"] += 1
            elif host == HOST:
                te["allowed"] += 1
            else:
                problems.append(_p("22", f"{f}: loads {m.group(1)} from another origin"))
        for m in re.finditer(r"url\((?:'|\")?(https?://[^)'\"]+)", text):
            te["refs"] += 1
            host = re.sub(r"^https?://", "", m.group(1)).split("/")[0]
            if f in allowed_pages and host in ("fonts.googleapis.com", "fonts.gstatic.com"):
                te["allowed"] += 1
            elif host == HOST:
                te["allowed"] += 1
            else:
                problems.append(_p("22", f"{f}: loads {m.group(1)} from another origin"))
    for jsname in ("site.js", "atlas.js"):
        jp = os.path.join(OUT, jsname)
        if os.path.exists(jp):
            te["cookie"] += len(re.findall(r"document\.cookie", open(jp, encoding="utf-8").read()))
    if te["cookie"]:
        problems.append(_p("22", "the cookie API is used %d time(s); the colophon says no cookies" % te["cookie"]))

    # 24. the deploy gate: the site is deployed by the workflow only after the
    # build, its checks, the tests of controls, the browser audit and the
    # idempotence proof have passed. The workflow file is held to that shape:
    # a build job that runs those steps in that order, none allowed to fail
    # quietly, and a deploy job that needs the build job and deploys with
    # actions/deploy-pages. A workflow without the gate fails the build, so
    # the claim cannot outlive the file that makes it true.
    wf = os.path.join(ROOT, ".github", "workflows", "build.yml")
    look("24", "site")
    T["workflow"] = {"idempotence": False, "gate": False, "steps": 0, "missing": []}
    if not os.path.exists(wf):
        problems.append(_p("24", ".github/workflows/build.yml: missing; nothing gates the deploy"))
    else:
        wtext = open(wf, encoding="utf-8").read()
        wants = [("build_site.py", "python3 build/build_site.py"),
                 ("negatives.py", "python3 build/negatives.py"),
                 ("audit.js", "node build/audit.js"),
                 ("audit.js --falsify", "node build/audit.js --falsify"),
                 ("record-run", "claims.py --record-run"),
                 ("idempotence", 'grep -q "rewrote: nothing"'),
                 ("upload", "actions/upload-pages-artifact"),
                 ("deploy", "actions/deploy-pages")]
        pos, missing = -1, []
        for name, needle in wants:
            i = wtext.find(needle, pos + 1)
            if i == -1:
                missing.append(name)
            else:
                pos = i
        T["workflow"]["steps"] = len(wants) - len(missing)
        T["workflow"]["missing"] = missing
        T["workflow"]["idempotence"] = "idempotence" not in missing
        gated = bool(re.search(r"^\s*needs:\s*(\[\s*build\s*\]|build)\s*$", wtext, re.M)) and "branches: [main]" in wtext
        quiet = "continue-on-error: true" in wtext
        T["workflow"]["gate"] = gated and not missing and not quiet
        if missing:
            problems.append(_p("24", ".github/workflows/build.yml: the gate lacks, in order, %s" % ", ".join(missing)))
        if not gated:
            problems.append(_p("24", ".github/workflows/build.yml: no deploy job needs the build job"))
        if quiet:
            problems.append(_p("24", ".github/workflows/build.yml: a step may fail quietly (continue-on-error)"))

    # 23. no em dash in the prose of any page, except the records declared in
    # content/declared.json (transcripts and run reports kept as written). A
    # dash standing alone as a cell or a chip is a symbol, not prose, and
    # dashes inside script, style, code and data are counted and reported,
    # not held. A declared record that no longer carries one is stale.
    td = T["emdash"] = {"pages": 0, "prose": 0, "alone": 0, "code": 0, "records": 0, "in_records": 0,
                        "generated_pages": 0}
    records = set(DECLARED.get("records") or [])
    for f in html_files:
        if f in ("reader.html", "admin.html"):
            continue
        text = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore").read()
        pr, al, co = emdash.prose_dashes(text)
        if f in records:
            td["records"] += 1
            td["in_records"] += pr
            if not pr:
                problems.append(_p("23", f"{f}: is declared a record exempt from the em dash rule but carries none; content/declared.json is stale"))
            continue
        look("23", f)
        td["pages"] += 1
        if f in SHELL_PAGES:
            td["generated_pages"] += 1
        td["alone"] += al
        td["code"] += co
        if pr:
            td["prose"] += pr
            problems.append(_p("23", f"{f}: carries {pr} em dash(es) in its prose"))
    for f in records:
        if f not in html_files:
            problems.append(_p("23", f"content/declared.json: {f} is declared a record but is not a page here"))

    # 25. the build's own words are spelled the Canadian way. The generated
    # pages are scanned with the text the build quotes removed (the owner's
    # fields, the lifted captions, the Atlas index of the pieces' headings,
    # the last pass's notes, and the two run-transcript names), and held
    # against a list of American spellings, whole words, any case.
    quoted_text = []
    for p in P:
        for k in ("t", "s", "blurb", "demo", "built_from"):
            v = p.get(k)
            if v:
                quoted_text.append(str(v))
        for tg in p.get("tags") or []:
            quoted_text.append(str(tg))
    for text_c, _href in CAPTIONS:
        quoted_text.append(text_c)
    ts25 = T["spelling"] = {"pages": 0, "words": 0, "hits": 0, "list": len(US_SPELLINGS)}
    for f in SHELL_PAGES:
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            continue
        look("25", f)
        raw = open(path, encoding="utf-8", errors="ignore").read()
        raw = re.sub(r'<section class="areg".*?</section>', " ", raw, flags=re.S)
        raw = re.sub(r'<section[^>]*id="limits".*?</section>', " ", raw, flags=re.S)
        raw = re.sub(r"<(script|style|svg)\b[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
        text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        for q in quoted_text:
            if q:
                text = text.replace(html.unescape(q), " ")
        ts25["pages"] += 1
        words25 = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
        ts25["words"] += len(words25)
        found = sorted({w for w in words25 if w.lower() in US_SPELLINGS})
        if found:
            ts25["hits"] += len(found)
            problems.append(_p("25", f"{f}: spells {', '.join(found[:5])} the American way"))

    # 26. every counted number on the generated pages names a definition the
    # colophon prints, and carries the value the record holds for it: a
    # number with data-of must equal that piece's metric, and a total must be
    # one of the aggregates the build computes over the pieces for that
    # definition (the corpus, an origin, a course, a kind, or the transcripts).
    def _aggregates():
        agg = {k: set() for k in ("pieces", "words", "figures", "tables", "checkpoints", "mins")}
        groups = [P] + [[p for p in P if p["surface"] == sf] for sf in ("independent", "course", "personal")]
        groups += [[p for p in P if p["c"] == c] for c in COURSES]
        groups += [[p for p in P if p["k"] == kd] for kd in ("Essay", "Reference", "Tool")]
        groups += [[p for p in P if p["surface"] == sf and p["k"] == kd] for sf in ("independent", "course", "personal") for kd in ("Essay", "Reference", "Tool")]
        groups += [[p for p in P if p["slug"] in ("crucible-run-0", "crucible-run-b", "crucible-run-c")]]
        groups += [[p for p in P if not p["is_doc"]]]
        for g in groups:
            agg["pieces"].add(len(g)); agg["words"].add(sum(p["words"] for p in g))
            agg["figures"].add(sum(p["figures"] for p in g)); agg["tables"].add(sum(p["tables"] for p in g))
        agg["checkpoints"].add(CHECKPOINTS)
        agg["words"].add(TRANSCRIPT_WORDS); agg["words"].add(TOTAL_WORDS + TRANSCRIPT_WORDS)
        agg["pieces"].add(len(P) + len(exceptions()["transcripts"]))
        return agg
    agg26 = _aggregates()
    by_slug26 = {p["slug"]: p for p in P}
    t26 = T["defined"] = {"numbers": 0, "pages": 0, "undefined": 0, "disagree": 0}
    for f in SHELL_PAGES:
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            continue
        look("26", f)
        t26["pages"] += 1
        raw = open(path, encoding="utf-8", errors="ignore").read()
        for m in re.finditer(r'<data class="m" value="([^"]*)" data-m="([^"]*)"(?: data-of="([^"]*)")?>', raw):
            t26["numbers"] += 1
            val, kind, of = m.group(1), m.group(2), m.group(3)
            if kind not in DEF_BY_ID:
                t26["undefined"] += 1
                problems.append(_p("26", f"{f}: a counted number names the definition {kind!r}, which the colophon does not print"))
                continue
            try:
                v = float(val)
            except ValueError:
                t26["disagree"] += 1
                problems.append(_p("26", f"{f}: a counted number carries the value {val!r}, which is not a number"))
                continue
            if of:
                pc = by_slug26.get(of)
                want = None if not pc else {"words": pc["words"], "figures": pc["figures"], "tables": pc["tables"],
                                            "mins": pc.get("mins"), "pieces": 1}.get(kind)
                if want is None or float(want) != v:
                    t26["disagree"] += 1
                    problems.append(_p("26", f"{f}: {kind} for {of} prints {val}; the record holds {want}"))
            elif v not in {float(x) for x in agg26.get(kind, set())}:
                t26["disagree"] += 1
                problems.append(_p("26", f"{f}: {kind} prints {val}, which is no aggregate the build computes for that definition"))

    # 32. the author is an entry in the register, by the rule, and his card is
    # the build's own arithmetic. One region of origin author with one mark,
    # linking to the heading on the about page that names him; the card on
    # the Atlas and in the home sphere's payload equal to a second computation
    # of the standing, the co-op window and the featured subtotal, made here
    # without the writer's function, so a writer that drifts is caught.
    look("32", "atlas.html"); look("32", "index.html"); look("32", "about.html")
    T["author"] = {"marks": 0, "total": len(ATLAS.get("points") or []), "zone": "", "share": 0.0, "link": "", "cards": 0, "off": 0, "card": ""}
    aregs32 = [r for r in regs if r["surface"] == "author"]
    apts32 = [q for q in (ATLAS.get("points") or []) if q["s"] == "author"]
    T["author"]["marks"] = len(apts32)
    if len(aregs32) != 1 or len(apts32) != 1:
        problems.append(_p("32", "atlas.html: the author is not one entry of the register (%d regions, %d marks)" % (len(aregs32), len(apts32))))
    else:
        q32 = apts32[0]
        T["author"]["link"] = q32["u"]
        if q32["u"] != "about.html#author":
            problems.append(_p("32", "atlas.html: the author's anchor links to %s, not to the heading that names him" % q32["u"]))
        about32 = os.path.join(OUT, "about.html")
        if not (os.path.exists(about32) and 'id="author"' in open(about32, encoding="utf-8", errors="ignore").read()):
            problems.append(_p("32", "about.html: carries no heading with the id the author's anchor links to"))
        e32 = rule28.get("author") or {}
        T["author"]["zone"] = e32.get("zone", "")
        T["author"]["share"] = e32.get("share", 0.0)
        if e32.get("zone") != "author":
            problems.append(_p("32", "atlas.html: the author's mark is not in a zone of his own"))
        # the card, a second time, without author_card()
        f32 = [p for p in P if p.get("featured")]
        bits32 = [(STANDING + ", " if STANDING else "") + "Accounting and Financial Management, Analytics stream"]
        m32 = re.match(r"^\s*([A-Z][a-z]+)\s+to\s+([A-Z][a-z]+)\s+(\d{4})\s*$", COOP_TERM or "")
        months32 = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        if m32 and m32.group(1) in months32 and m32.group(2) in months32:
            y32, a32, b32 = int(m32.group(3)), months32.index(m32.group(1)) + 1, months32.index(m32.group(2)) + 1
            start32 = datetime.date(y32, a32, 1)
            end32 = datetime.date(y32 + (b32 // 12), (b32 % 12) + 1, 1) - datetime.timedelta(days=1)
            days32 = (start32 - TODAY).days
            if days32 > 0:
                bits32.append("co-op term %s, %s days from this build (%s)" % (COOP_TERM, format(days32, ","), TODAY.isoformat()))
            elif end32 >= TODAY:
                bits32.append("co-op term %s, under way at this build (%s)" % (COOP_TERM, TODAY.isoformat()))
            else:
                bits32.append("co-op term %s, past at this build (%s)" % (COOP_TERM, TODAY.isoformat()))
        bits32.append("%d featured pieces: %s words, %d figures, %d tables" % (len(f32), format(sum(p["words"] for p in f32), ","),
                                                                              sum(p["figures"] for p in f32), sum(p["tables"] for p in f32)))
        want32 = " \u00b7 ".join(bits32)
        T["author"]["card"] = want32
        def _norm32(s32):
            return re.sub(r"\s+", " ", html.unescape(s32 or "")).strip()
        m = re.search(r'id="author-card">([^<]*)<', atext)
        if m:
            T["author"]["cards"] += 1
            if _norm32(m.group(1)) != want32:
                T["author"]["off"] += 1
                problems.append(_p("32", "atlas.html: the author's card reads %r; the build's own arithmetic says %r" % (_norm32(m.group(1)), want32)))
        else:
            problems.append(_p("32", "atlas.html: carries no card for the author"))
        m = re.search(r'<script type="application/json" id="atlasmini-docs">(.*?)</script>', itext, re.S)
        card32 = None
        if m:
            try:
                for d32 in json.loads(m.group(1).replace("<\\/", "</"))["docs"]:
                    if d32.get("o") == "author":
                        card32 = d32.get("card")
            except (ValueError, KeyError):
                card32 = None
        if card32 is None:
            problems.append(_p("32", "index.html: the sphere's payload carries no card for the author"))
        else:
            T["author"]["cards"] += 1
            if _norm32(card32) != want32:
                T["author"]["off"] += 1
                problems.append(_p("32", "index.html: the author's card reads %r; the build's own arithmetic says %r" % (_norm32(card32), want32)))

        # the same two recorded values on the about page's Now block, which is
        # the only part of that page that goes stale on its own. The day count
        # is held to the arithmetic just done, not to the writer that printed
        # it, and the measurement date is held to this build's date.
        atx32 = os.path.join(OUT, "about.html")
        if os.path.exists(atx32):
            nraw32 = open(atx32, encoding="utf-8", errors="ignore").read()
            nm32 = re.search(r'<div class="facts[^"]*nowpane">(.*?)</div>\s*</div>\s*</section>', nraw32, re.S)
            nblk32 = _norm32(re.sub(r"<[^>]+>", " ", nm32.group(1))) if nm32 else None
            if nblk32 is None:
                problems.append(_p("32", "about.html: carries no Now block, and the page claims one"))
            else:
                T["author"]["cards"] += 1
                if m32 and days32 > 0:
                    want_days32 = "%s, %s days from this build" % (COOP_TERM, format(days32, ","))
                    if want_days32 not in nblk32:
                        T["author"]["off"] += 1
                        problems.append(_p("32", "about.html: the Now block does not read %r, which is the "
                                                 "co-op window this build computes" % want_days32))
                if TODAY.isoformat() not in nblk32:
                    T["author"]["off"] += 1
                    problems.append(_p("32", "about.html: the Now block does not carry this build's date, %s"
                                             % TODAY.isoformat()))

    # 27. every visual channel the two sphere scripts declare is named in the
    # Atlas key, and every key entry is a channel one of them draws; the home
    # sphere's key is the Atlas key, one link from its caption.
    declared = {}
    for jsname in ("site.js", "atlas.js"):
        jp = os.path.join(OUT, jsname)
        if os.path.exists(jp):
            mm = re.search(r"CHANNELS\s*=\s*\[([^\]]*)\]", open(jp, encoding="utf-8").read())
            declared[jsname] = set(re.findall(r'"([a-z]+)"', mm.group(1))) if mm else set()
    key_items = set()
    if os.path.exists(apath):
        key_items = set(re.findall(r'<li[^>]*><i class="ak ak-([a-z]+)"', atext))
    t27 = T["channels"] = {"scripts": len(declared), "declared": len(set().union(*declared.values()) if declared else set()),
                           "key": len(key_items), "unnamed": 0, "stray": 0}
    look("27", "atlas.html"); look("27", "index.html")
    for jsname, chs in declared.items():
        if not chs:
            problems.append(_p("27", f"{jsname}: declares no channels; the sphere cannot be held to its key"))
        for ch in sorted(chs - key_items):
            t27["unnamed"] += 1
            problems.append(_p("27", f"{'index.html' if jsname == 'site.js' else 'atlas.html'}: {jsname} draws the channel {ch!r}, which the Atlas key does not name"))
    drawn27 = set().union(*declared.values()) if declared else set()
    for ch in sorted(key_items - drawn27):
        t27["stray"] += 1
        problems.append(_p("27", f"atlas.html: the key names {ch!r}, which neither sphere draws"))

    # 30. on the lifted figures, no meaning is carried by colour alone: every
    # colour variable a figure's marks use is declared with a meaning in
    # words, the declaration names no colour the marks do not use, and the
    # rendered key under the figure names each one.
    t30 = T["colour"] = {"figures": 0, "pages": 0, "colours": 0, "unnamed": 0, "stray": 0}
    for f in SHELL_PAGES:
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        fids = re.findall(r'<figure class="spec" id="(fs-[a-z0-9]+)">', text)
        if not fids:
            continue
        look("30", f)
        t30["pages"] += 1
        for fid in fids:
            if fid not in STRIP:
                continue
            t30["figures"] += 1
            used = figure_colour_vars(fid)
            means = STRIP[fid].get("meanings") or {}
            block = re.search(r'<figure class="spec" id="%s">.*?</figure>' % fid, text, re.S)
            shown = set(re.findall(r'<span class="fk-item" data-var="([^"]+)">', block.group(0))) if block else set()
            t30["colours"] += len(used)
            for v in sorted(used - set(means)):
                t30["unnamed"] += 1
                problems.append(_p("30", f"{f}: {fid} draws with {v}, which carries no declared meaning"))
            for v in sorted(set(means) - used):
                t30["stray"] += 1
                problems.append(_p("30", f"{f}: {fid} declares a meaning for {v}, which its marks do not use"))
            for v in sorted(used - shown):
                t30["unnamed"] += 1
                problems.append(_p("30", f"{f}: {fid}'s key does not name {v}"))

    # 31. every number a figure on the generated pages draws is restated in
    # the page's text outside the drawing: the numerals in the figure's
    # visible text, each found in the page with its figures removed.
    t31 = T["restated"] = {"figures": 0, "pages": 0, "numerals": 0, "missing": 0}
    for f in SHELL_PAGES:
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8", errors="ignore").read()
        svgs = []
        depth = 0; start = None
        for m in re.finditer(r"<(/?)svg\b([^>]*)>", text):
            if m.group(1):
                depth -= 1
                if depth == 0 and start is not None:
                    svgs.append(text[start:m.end()])
                continue
            if depth == 0:
                start = m.start()
            depth += 1
        big = []
        for sv in svgs:
            vb = re.search(r'viewBox="([^"]+)"', sv[:400])
            q = [float(x) for x in re.split(r"[\s,]+", vb.group(1).strip()) if x] if vb else []
            if len(q) == 4 and q[2] * q[3] >= 6000:
                big.append(sv)
        if not big:
            continue
        look("31", f)
        t31["pages"] += 1
        outside = re.sub(r"<svg\b.*?</svg>", " ", text, flags=re.S)
        outside = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", outside, flags=re.S | re.I)
        outside = html.unescape(re.sub(r"<[^>]+>", " ", outside))
        outside = re.sub(r"\s+", " ", outside)
        for sv in big:
            t31["figures"] += 1
            nums = set()
            for line in figure_numbers(sv):
                nums |= set(re.findall(r"\d[\d,]*(?:\.\d+)?", line))
            t31["numerals"] += len(nums)
            lost = sorted(x for x in nums if x not in outside)
            if lost:
                t31["missing"] += len(lost)
                problems.append(_p("31", f"{f}: a figure draws {', '.join(lost[:5])}, which the page's text does not restate"))
    # 34. the marks. Three files in content/marks are the geometry; every mark
    # a page draws is read back and recomputed here from those files, by this
    # check's own reader rather than by the module that wrote them, so an
    # emitter that invents an element or forgets to scale one is caught. Two
    # rules are held besides: a surface may only draw elements its source
    # carries, and the thinnest stroke it draws must clear one device pixel at
    # the size it is drawn (a stroke renders at its width times that size over
    # the 64 unit grid the marks are authored on), which is the whole reason a
    # reduction exists. The stylesheet may not resize a mark, or that
    # arithmetic would be about a size nothing draws.
    t34 = T["marks"] = {"files": 0, "elements": 0, "surfaces": 0, "drawn": 0,
                        "pages": 0, "mismatched": 0, "unknown": 0, "thin": 0,
                        "invariants": 0, "carried": 0, "detail": []}

    def _read_mark(path):
        """The elements of a mark file, in order, id'd by the comment above
        them: this check's own reading of the source."""
        raw = open(path, encoding="utf-8").read()
        label, seen, els = "", {}, []
        for m in re.finditer(r"<!--(.*?)-->|<(circle|path)\b([^>]*?)/>", raw, re.S):
            if m.group(1) is not None:
                label = re.sub(r"\s+", " ", m.group(1)).strip()
                continue
            a = dict(re.findall(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"', m.group(3)))
            if "d" in a:
                a["d"] = re.sub(r"\s+", " ", a["d"]).strip()
            seen[label] = seen.get(label, 0) + 1
            els.append(("%s#%d" % (label, seen[label]), m.group(2), a))
        return els

    want34 = {}
    for key, spec in marks_mod.VARIANTS.items():
        src = os.path.join(OUT, "content", "marks", marks_mod.FILES[spec["mark"]])
        if not os.path.exists(src):
            problems.append(_p("34", "content/marks/%s: missing, so the %s mark cannot be drawn"
                                     % (marks_mod.FILES[spec["mark"]], key))); continue
        els = _read_mark(src)
        t34["surfaces"] += 1
        ids = {e[0] for e in els}
        for want in (spec["keep"] or ()):
            if want not in ids:
                t34["unknown"] += 1
                problems.append(_p("34", "the %s mark draws %s, which %s does not carry"
                                         % (key, want, marks_mod.FILES[spec["mark"]])))
        def _layer(keep, scale, label):
            """One layer of a surface: the elements it keeps, every stroke on
            them multiplied by its factor, and the check that the finest of
            them still holds an edge at the size the surface draws."""
            parts, widths = [], []
            for eid, tag, a in els:
                if keep is not None and eid not in keep:
                    continue
                a = dict(a)
                if "stroke-width" in a:
                    w = float(a["stroke-width"]) * scale
                    widths.append(w)
                    a["stroke-width"] = ("%.4f" % w).rstrip("0").rstrip(".")
                parts.append("<%s %s/>" % (tag, " ".join('%s="%s"' % (k, a[k]) for k in
                             ("cx", "cy", "r", "d", "stroke-width", "opacity", "fill", "stroke") if k in a)))
            t34["drawn"] += len(parts)
            if widths:
                thin = min(widths) * spec["px"] / 64.0
                t34["detail"].append({"key": label, "drawn": len(parts), "of": len(els),
                                      "scale": scale, "px": spec["px"], "thin": round(thin, 2)})
                if thin < 1.0:
                    t34["thin"] += 1
                    problems.append(_p("34", "the %s mark's thinnest stroke draws %.3f device pixels at %dpx, "
                                             "under the one pixel an edge needs" % (label, thin, spec["px"])))
            return "".join(parts)

        body34 = _layer(spec["keep"], spec["scale"], key)
        ins34 = spec.get("inspect")
        if ins34:
            # a surface may carry a second layer, which a reader reveals; it is
            # held to the same two rules, drawn from the same file
            for want in ins34["keep"]:
                if want not in ids:
                    t34["unknown"] += 1
                    problems.append(_p("34", "the %s mark's inspection layer draws %s, which %s does not carry"
                                             % (key, want, marks_mod.FILES[spec["mark"]])))
            body34 = ('<g class="mk-nom">%s</g><g class="mk-ins">%s</g>'
                      % (body34, _layer(ins34["keep"], ins34["scale"], key + " inspected")))
            t34["surfaces"] += 1
        want34[key] = body34
    for name in sorted(marks_mod.FILES.values()):
        sp = os.path.join(OUT, "content", "marks", name)
        if os.path.exists(sp):
            t34["files"] += 1
            t34["elements"] += len(_read_mark(sp))
    # every mark on every page is the geometry above, and nothing else
    for f in html_files:
        text34 = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore").read()
        found = re.findall(r'<svg class="[^"]*\bmk-([a-z]+)\b[^"]*"[^>]*>(.*?)</svg>', text34, re.S)
        if not found:
            continue
        look("34", f)
        t34["pages"] += 1
        for key, drawn in found:
            if key not in want34:
                t34["mismatched"] += 1
                problems.append(_p("34", "%s: draws a mark named %s, which the build defines no geometry for" % (f, key)))
            elif drawn != want34[key]:
                t34["mismatched"] += 1
                problems.append(_p("34", "%s: the %s mark drawn is not the geometry content/marks holds" % (f, key)))
    # the stylesheet may not resize a mark out from under that arithmetic
    css34 = open(os.path.join(OUT, "site.css"), encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"\.mk(-[a-z]+)?\s*\{([^}]*)\}", css34):
        key34, decl = (m.group(1) or "")[1:], m.group(2)
        for prop, val in re.findall(r"\b(width|height)\s*:\s*([^;}]+)", decl):
            want = marks_mod.VARIANTS.get(key34, {}).get("px")
            if want is None or val.strip() != "%dpx" % want:
                problems.append(_p("34", "site.css: a rule on the marks sets %s to %s; a mark may only be pinned to "
                                         "the size its stroke rule was computed for" % (prop, val.strip())))
    # the bar injected into a piece meets that piece's stylesheet, so its box is
    # pinned there; the pin must name the size the bar's mark is drawn at
    barpx = marks_mod.VARIANTS["bar"]["px"]
    barcss = re.search(r"#__rb \.__mark\{([^}]*)\}", RETURN_BAR.replace("__MARKPX__", str(barpx)), re.S)
    if not barcss or not re.search(r"width:%dpx;height:%dpx" % (barpx, barpx), re.sub(r"\s+", "", barcss.group(1))):
        problems.append(_p("34", "the bar injected into every piece does not pin its mark to %dpx, so a piece's own "
                                 "stylesheet can draw it at a size its stroke rule was not computed for" % barpx))
    aud34 = marks_mod.audit(os.path.join(OUT, "content", "marks"))
    t34["invariants"], t34["carried"] = aud34["n"], aud34["carried"]
    t34["grid"] = marks_mod.grid(os.path.join(OUT, "content", "marks"))


    # 35. the glyphs, the seal and the figure on every statement row. Three
    # further families of drawn geometry, each recomputed here from the files
    # and the measurements rather than from the modules that emitted them.
    # The rules are the ones check 34 holds the brand marks to, plus one more
    # for the figures: a figure has to be the geometry its own document's four
    # measured values produce, so a row cannot carry a picture of some other
    # document, or a picture of nothing.
    t35 = T["instruments"] = {"glyphs": 0, "glyph_elements": 0, "drawn": 0, "seal": 0,
                              "figures": 0, "of": 0, "mismatched": 0, "thin": 0,
                              "pages": 0, "callouts": 0, "detail": []}
    MD = os.path.join(OUT, "content", "marks")

    def _els35(path, tags):
        """This check's own reader: every drawn element of one file, in order,
        with its attributes, keyed by tag."""
        if not os.path.exists(path):
            return None
        raw = open(path, encoding="utf-8").read()
        seen, out = {}, []
        for m in re.finditer(r"<(%s)\b([^>]*?)/>" % "|".join(tags), raw, re.S):
            a = dict(re.findall(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"', m.group(2)))
            if "d" in a:
                a["d"] = re.sub(r"\s+", " ", a["d"]).strip()
            seen[m.group(1)] = seen.get(m.group(1), 0) + 1
            out.append((m.group(1), a))
        return out

    ORDER35 = ("cx", "cy", "r", "x", "y", "width", "height", "d", "stroke-width", "fill", "stroke")
    want35 = {}
    for gk, (gfile, glabel, _means) in marks_mod.GLYPHS.items():
        gp = os.path.join(MD, marks_mod.GLYPH_DIR, gfile)
        els = _els35(gp, ("circle", "path", "rect"))
        if els is None:
            problems.append(_p("35", "content/marks/%s/%s: missing, so the %s glyph cannot be drawn"
                                     % (marks_mod.GLYPH_DIR, gfile, gk))); continue
        raw = open(gp, encoding="utf-8").read()
        vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', raw)
        sw = re.search(r'stroke-width="([\d.]+)"', raw)
        if not vb or int(vb.group(1)) != marks_mod.glyph_grid(gk, MD):
            problems.append(_p("35", "content/marks/%s: does not declare the grid the build draws it on" % gfile))
            continue
        t35["glyphs"] += 1
        t35["glyph_elements"] += len(els)
        want35["gl-" + gk] = "".join(
            "<%s %s/>" % (tag, " ".join('%s="%s"' % (k, a[k]) for k in ORDER35 if k in a))
            for tag, a in els)
        for size, px in marks_mod.GLYPH_SIZES.items():
            thin = float(sw.group(1)) * px / int(vb.group(1))
            t35["detail"].append({"key": "%s at %s" % (gk, size), "px": px, "thin": round(thin, 2)})
            if thin < 1.0:
                t35["thin"] += 1
                problems.append(_p("35", "the %s glyph draws %.3f device pixels at %dpx, under the one "
                                         "pixel an edge needs" % (gk, thin, px)))

    # the seal: the file, with exactly three changes and no others
    sealp = os.path.join(MD, marks_mod.SEAL_FILE)
    if not os.path.exists(sealp):
        problems.append(_p("35", "content/marks/%s: missing, so the seal cannot be drawn" % marks_mod.SEAL_FILE))
    else:
        raw = open(sealp, encoding="utf-8").read()
        inner = raw[raw.index(">", raw.index("<svg")) + 1: raw.rindex("</svg>")]
        inner = re.sub(r"<!--.*?-->", "", inner, flags=re.S)
        dropped = len(re.findall(r'<[a-z]+\b[^>]*stroke-width="%s"[^>]*/>' % re.escape(str(marks_mod.SEAL_DROP)), inner))
        inner = re.sub(r'<[a-z]+\b[^>]*stroke-width="%s"[^>]*/>' % re.escape(str(marks_mod.SEAL_DROP)), "", inner)
        widths = [float(w) * marks_mod.SEAL_SCALE for w in re.findall(r'stroke-width="([\d.]+)"', inner)]
        inner = re.sub(r'stroke-width="([\d.]+)"',
                       lambda m: 'stroke-width="%s"' % ("%.4f" % (float(m.group(1)) * marks_mod.SEAL_SCALE)
                                                        ).rstrip("0").rstrip("."), inner)
        inner = inner.replace("seal-arc-seal", marks_mod.SEAL_ARC_ID)
        want35["sl-seal"] = re.sub(r">\s+<", "><", re.sub(r"\s+", " ", inner)).strip()
        t35["seal"] = 1
        if dropped != 1:
            problems.append(_p("35", "the seal drops %d element(s) at stroke %s; the rule drops exactly the one "
                                     "its finest stroke cannot hold" % (dropped, marks_mod.SEAL_DROP)))
        grid35 = int(re.search(r'viewBox="0 0 (\d+)', raw).group(1))
        thin = min(widths) * marks_mod.SEAL_PX / grid35 if widths else 0
        t35["detail"].append({"key": "seal", "px": marks_mod.SEAL_PX, "thin": round(thin, 2)})
        if thin < 1.0:
            t35["thin"] += 1
            problems.append(_p("35", "the seal's thinnest stroke draws %.3f device pixels at %dpx, under the "
                                     "one pixel an edge needs" % (thin, marks_mod.SEAL_PX)))

    # the fifteen dimensions, walked a second time. The ledger states a reading
    # off a vertex or an arc boundary; this walks the same two files with its
    # own reader and its own path walker, and the two have to agree.
    def _walk35(d):
        """The points a path passes through. A cubic names two control points
        before its endpoint, and a control point is not a place on a drawing."""
        toks = re.findall(r"[MmLlHhVvCcZz]|-?\d+(?:\.\d+)?", d)
        pts, i, x, y, cmd = [], 0, 0.0, 0.0, None
        while i < len(toks):
            t = toks[i]
            if re.match(r"[A-Za-z]", t):
                cmd = t; i += 1
                if cmd in "Zz":
                    continue
            if cmd in "MmLl":
                nx, ny = float(toks[i]), float(toks[i + 1])
                x, y = (nx, ny) if cmd in "ML" else (x + nx, y + ny); i += 2
            elif cmd in "HhVv":
                v = float(toks[i]); i += 1
                if cmd == "H": x = v
                elif cmd == "h": x += v
                elif cmd == "V": y = v
                else: y += v
            elif cmd in "Cc":
                vs = [float(toks[i + k]) for k in range(6)]
                x, y = (vs[4], vs[5]) if cmd == "C" else (x + vs[4], y + vs[5]); i += 6
            else:
                i += 1; continue
            pts.append((x, y))
        return pts

    dims35 = {}
    for mk35, fn35 in (("monogram", "01_vernier_monogram_AR.svg"), ("datum", "03_polar_datum.svg")):
        els35 = _els35(os.path.join(MD, fn35), ("circle", "path"))
        if els35 is None:
            problems.append(_p("35", "content/marks/%s: missing, so the callout ledger answers to nothing" % fn35))
            continue
        paths = [a for tag, a in els35 if tag == "path"]
        circs = [a for tag, a in els35 if tag == "circle"]
        if mk35 == "monogram":
            datum = _walk35(paths[0]["d"])
            A = _walk35(paths[1]["d"]); bar = _walk35(paths[2]["d"])
            bowl = _walk35(paths[3]["d"]); tick = _walk35(paths[6]["d"])
            feet = sorted(p for p in A if p[1] == max(q[1] for q in A))
            top35, bot35 = min(p[1] for p in bowl), max(p[1] for p in bowl)
            dims35["monogram"] = sorted([
                round(datum[1][1] - datum[0][1], 3), round(float(circs[0]["r"]), 3),
                round(min(p[1] for p in A), 3), round(feet[0][1], 3),
                round(feet[-1][0] - feet[0][0], 3), round(bar[-1][0] - bar[0][0], 3),
                round(bot35 - top35, 3), round(tick[-1][0] - tick[0][0], 3)])
        else:
            axis = _walk35(paths[0]["d"])
            rings = [float(c["r"]) for c in circs[:4]]
            pole, author = circs[4], circs[5]
            dims35["datum"] = sorted([
                round(2 * rings[0], 3), round(2 * rings[1], 3), round(2 * rings[2], 3),
                round(float(circs[0]["cy"]) - float(pole["cy"]), 3),
                round(axis[-1][1] - axis[0][1], 3),
                round(2 * float(pole["r"]), 3), round(2 * float(author["r"]), 3)])
    said35 = {}
    for c35 in marks_mod.callouts(MD):
        said35.setdefault(c35["mark"], []).append(round(float(c35["value"]), 3))
    t35["callouts"] = sum(len(v) for v in said35.values())
    for mk35 in sorted(set(dims35) | set(said35)):
        if sorted(said35.get(mk35, [])) != dims35.get(mk35, []):
            t35["mismatched"] += 1
            problems.append(_p("35", "the %s callouts read %s on a second walk of the same file; the ledger prints %s"
                                     % (mk35, dims35.get(mk35), sorted(said35.get(mk35, [])))))

    # the figure on a row: this check's own arithmetic, from the four values
    def _fp35(w, f, t, c):
        """The generator's rules, restated here. A radius from the words, a ray
        per table, a ring at 0.62 of the radius, a chord per recorded link and
        a node per figure, with the observer on the boundary and the author's
        datum at the centre."""
        W = max(1, min(200000, int(round(w)) or 1))
        F = max(0, min(80, int(round(f)))); T2 = max(0, min(80, int(round(t))))
        C = max(0, min(60, int(round(c))))
        hi = math.log10(50000)
        tt = min(1.0, max(0.0, (math.log10(W) - 3.0) / (hi - 3.0)))
        r3 = lambda n: round(n * 1000) / 1000
        R = r3(12.0 + 16.0 * tt); ring = r3(R * 0.62)
        stride = 0
        if F >= 2:
            k = max(1, int(round(F * 0.382)))
            stride = k + 1 if 2 * k == F else k
        sc = fingerprint.PLACES["row"]["scale"]
        wd = lambda x: ("%.4f" % (x * sc)).rstrip("0").rstrip(".")
        pt = lambda rr, deg: (r3(32 + rr * math.sin(math.radians(deg))),
                              r3(32 - rr * math.cos(math.radians(deg))))
        out = ['<circle cx="32" cy="32" r="%g" stroke-width="%s"/>' % (R, wd(1.0))]
        if T2:
            seg = "".join("M%g %gL%g %g" % (pt(R - 4, i * 360.0 / T2) + pt(R, i * 360.0 / T2))
                          for i in range(T2))
            out.append('<path d="%s" stroke-width="%s"/>' % (seg, wd(0.75)))
        if F:
            out.append('<circle cx="32" cy="32" r="%g" stroke-width="%s"/>' % (ring, wd(0.4)))
        if C and F >= 2:
            seg = ""
            for i in range(C):
                a = int(round(i * F / C)) % F
                b = (a + stride) % F
                seg += "M%g %gL%g %g" % (pt(ring, a * 360.0 / F) + pt(ring, b * 360.0 / F))
            out.append('<path d="%s" stroke-width="%s"/>' % (seg, wd(0.5)))
        if F:
            out.append('<g fill="currentColor" stroke="none">%s</g>' % "".join(
                '<circle cx="%g" cy="%g" r="1.1"/>' % pt(ring, i * 360.0 / F) for i in range(F)))
        out.append('<circle cx="32" cy="%g" r="1.6" fill="currentColor" stroke="none"/>' % r3(32 - R))
        out.append('<circle cx="32" cy="32" r="1" fill="currentColor" stroke="none"/>')
        return "".join(out), min(0.4, 0.5, 0.75, 1.0) * sc * fingerprint.PLACES["row"]["px"] / 64.0

    deg35 = {}
    for a35, b35 in ATLAS.get("edges") or ():
        deg35[a35] = deg35.get(a35, 0) + 1
        deg35[b35] = deg35.get(b35, 0) + 1
    by35 = {p["slug"]: p for p in P}

    # every glyph, seal and figure on every page is that geometry, and nothing else
    for f in html_files:
        text35 = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore").read()
        found = re.findall(r'<svg class="(?:gl gl-([a-z]+)|sl (sl-seal))"[^>]*>(.*?)</svg>', text35, re.S)
        figs35 = re.findall(r'<div class="sr-f" data-fp="([^"]+)">(<svg class="fp".*?</svg>)</div>', text35, re.S)
        if not found and not figs35:
            continue
        look("35", f)
        t35["pages"] += 1
        for gk, sk, drawn in found:
            key = ("gl-" + gk) if gk else sk
            t35["drawn"] += 1
            if key not in want35:
                t35["mismatched"] += 1
                problems.append(_p("35", "%s: draws an instrument named %s, which the build defines no geometry for"
                                         % (f, key)))
            elif drawn != want35[key]:
                t35["mismatched"] += 1
                problems.append(_p("35", "%s: the %s drawn is not the geometry content/marks holds" % (f, key)))
        for slug35, svg35 in figs35:
            t35["figures"] += 1
            pc = by35.get(slug35)
            if pc is None:
                t35["mismatched"] += 1
                problems.append(_p("35", "%s: carries a figure for %s, which is not a listed piece" % (f, slug35)))
                continue
            body35, thin35 = _fp35(pc["words"], pc["figures"], pc["tables"], deg35.get(slug35, 0))
            inner35 = re.sub(r"^<svg[^>]*>|</svg>$", "", svg35)
            if inner35 != body35:
                t35["mismatched"] += 1
                problems.append(_p("35", "%s: the figure on %s is not the geometry its %s words, %d figures, "
                                         "%d tables and %d recorded links produce"
                                         % (f, slug35, format(pc["words"], ","), pc["figures"], pc["tables"],
                                            deg35.get(slug35, 0))))
            if thin35 < 1.0:
                t35["thin"] += 1
                problems.append(_p("35", "a figure's thinnest stroke draws %.3f device pixels at %dpx, under the "
                                         "one pixel an edge needs" % (thin35, fingerprint.PLACES["row"]["px"])))
    t35["of"] = len(P)
    if t35["figures"] and t35["figures"] != len(P):
        problems.append(_p("35", "the whole statement carries %d figures for %d pieces"
                                 % (t35["figures"], len(P))))
    # the stylesheet may not resize an instrument either
    for m in re.finditer(r"\.(gl|sl|fp)(-[a-z]+)?\s*\{([^}]*)\}", css34):
        for prop, val in re.findall(r"\b(width|height)\s*:\s*([^;}]+)", m.group(3)):
            problems.append(_p("35", "site.css: a rule on the instruments sets %s to %s; each one is drawn at "
                                     "the size its stroke rule was computed for and is never resized"
                                     % (prop, val.strip())))

    # 36. contrast, from the tokens themselves. Every colour the site puts text
    # in has to clear 4.5:1 on every surface a page can stand it on, in both
    # themes, and the two lights may not take it under that: each is composited
    # over the paper at its full strength and the whole set is measured again.
    # The floor for a control's border is 3:1 (WCAG 2.2 SC 1.4.11), because on
    # a control the border is the only thing telling a reader it is there.
    t36 = T["contrast"] = {"tokens": 0, "pairs": 0, "themes": 0, "floor": 4.5,
                           "worst": None, "worst_at": "", "under": 0, "mirrored": 0}
    TEXT36 = ("ink", "ink-2", "ink-3", "accent", "accent-2", "link", "tool", "ref")
    SURF36 = ("paper", "panel", "panel-2")
    EDGE36 = 3.0

    def _tok36(block):
        return dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", block))

    def _lamp36(block):
        return dict(re.findall(r"--(lamp-[a-z]+):\s*rgba\(([^)]*)\)", block))

    def _rgb36(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    def _lum36(c):
        f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        r, g, b = (f(v) for v in c)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _cr36(a, b):
        la, lb = _lum36(a), _lum36(b)
        hi, lo = max(la, lb), min(la, lb)
        return (hi + 0.05) / (lo + 0.05)

    mlight = re.search(r":root\{(.*?)\n\}", css34, re.S)
    mdark = re.search(r':root\[data-theme="dark"\]\{(.*?)\n\}', css34, re.S)
    # the dark ground is declared twice on purpose: once for a browser that
    # asks for it and once for a reader who pressed the button. Only the second
    # is measured below, so the two have to say the same thing, or a reader
    # whose system is dark gets a palette nothing checked.
    mmedia = re.search(r"@media \(prefers-color-scheme: dark\)\{\s*"
                       r':root:where\(:not\(\[data-theme="light"\]\)\)\{(.*?)\n  \}', css34, re.S)
    if not mmedia:
        problems.append(_p("36", "site.css: the dark palette for a browser that asks for it is not readable "
                                 "as a token block, so it cannot be held to the one the button sets"))
    elif mdark:
        a36, b36 = _tok36(mmedia.group(1)), _tok36(mdark.group(1))
        a36.update(_lamp36(mmedia.group(1))); b36.update(_lamp36(mdark.group(1)))
        t36["mirrored"] = len(b36)
        for k36 in sorted(set(a36) | set(b36)):
            if a36.get(k36) != b36.get(k36):
                t36["under"] += 1
                problems.append(_p("36", "site.css: the two dark palettes disagree on %s, %s where the browser "
                                         "asks for dark and %s where the button sets it"
                                         % (k36, a36.get(k36, "not defined"), b36.get(k36, "not defined"))))
    if not (mlight and mdark):
        problems.append(_p("36", "site.css: the light and dark palettes are not both readable as token blocks"))
    else:
        for tname, blk in (("Archival light", mlight.group(1)), ("Obsidian", mdark.group(1))):
            toks, lamps = _tok36(blk), _lamp36(blk)
            t36["themes"] += 1
            missing = [k for k in TEXT36 + SURF36 + ("edge",) if k not in toks]
            if missing:
                problems.append(_p("36", "site.css: the %s palette defines no %s" % (tname, ", ".join(missing))))
                continue
            grounds = [(sname, _rgb36(toks[sname])) for sname in SURF36]
            for lname, spec in sorted(lamps.items()):
                parts = [x.strip() for x in spec.split(",")]
                lr, lg, lb, la = [float(x) for x in parts[:3]] + [float(parts[3])]
                paper = _rgb36(toks["paper"])
                grounds.append(("paper under the %s" % lname.replace("lamp-", "").replace("cool", "cool light").replace("warm", "warm light"),
                                tuple((lr / 255.0, lg / 255.0, lb / 255.0)[i] * la + paper[i] * (1 - la)
                                      for i in range(3))))
            for tk in TEXT36:
                t36["tokens"] += 1
                for sname, ground in grounds:
                    c = _cr36(_rgb36(toks[tk]), ground)
                    t36["pairs"] += 1
                    if t36["worst"] is None or c < t36["worst"]:
                        t36["worst"] = round(c, 2)
                        t36["worst_at"] = "%s on %s in %s" % (tk, sname, tname)
                    if c < 4.5:
                        t36["under"] += 1
                        problems.append(_p("36", "site.css: %s on %s in %s is %.2f:1, under the 4.5:1 a "
                                                 "reader needs to read it" % (tk, sname, tname, c)))
            for sname in ("paper", "panel"):
                c = _cr36(_rgb36(toks["edge"]), _rgb36(toks[sname]))
                t36["pairs"] += 1
                if c < EDGE36:
                    t36["under"] += 1
                    problems.append(_p("36", "site.css: the border of a control is %.2f:1 on the %s in %s, "
                                             "under the 3:1 that tells a reader the control is there"
                                             % (c, sname, tname)))

    # 37. a table header says which cells it heads. Every th the build writes
    # carries a scope, because a header cell with none leaves a screen reader
    # to guess from the shape of the table.
    t37 = T["scope"] = {"th": 0, "pages": 0, "bare": 0, "wrong": 0}
    for f in list(SHELL_PAGES):
        fp37 = os.path.join(OUT, f)
        if not os.path.exists(fp37):
            continue
        look("37", f)
        t37["pages"] += 1
        for tag in re.findall(r"<th\b[^>]*>", open(fp37, encoding="utf-8", errors="ignore").read()):
            t37["th"] += 1
            m37 = re.search(r'\bscope="([^"]*)"', tag)
            if not m37:
                t37["bare"] += 1
                problems.append(_p("37", "%s: a table header carries no scope, so nothing says which cells "
                                         "it heads" % f))
            elif m37.group(1) not in ("col", "row", "colgroup", "rowgroup"):
                t37["wrong"] += 1
                problems.append(_p("37", "%s: a table header declares scope=%s, which is not a scope"
                                         % (f, m37.group(1))))

    # 38. the case map. content/cases.json says where each of the eight slots
    # is answered for each featured piece, and every placement in it is a
    # reading rather than a measurement. What can be held is held here: the
    # piece is one the site lists and records as featured, the slot key is one
    # of the eight, a named section exists both in the file and in the piece's
    # invariance record, the heading printed beside it is the heading that
    # record holds, a named document is a listed piece the corpus records a
    # link to, and a named record is one this build actually carries. The
    # coverage the page prints is recomputed here from the files rather than
    # read back from the page, so a slot cannot be counted as carried by a
    # page that does not carry it.
    t38 = T["cases"] = {"pieces": 0, "slots": 0, "sec": 0, "doc": 0, "rec": 0,
                        "gap": 0, "broken": 0, "quoted": 0, "misquoted": 0}
    try:
        _inv38 = json.load(open(invariance.BASE_PATH, encoding="utf-8")).get("pieces") or {}
    except Exception:
        _inv38 = {}
    _slug38 = {q["slug"]: q for q in P}
    _feat38 = {q["slug"] for q in P if q.get("featured")}
    _keys38 = {k for k, _l, _m in CASE_SLOTS}
    _edge38 = set()
    for _a38, _b38 in (ATLAS.get("edges") or ()):
        _edge38.add((_a38, _b38)); _edge38.add((_b38, _a38))
    look("38", "selected.html")
    for slug38, spec38 in sorted((CASES.get("cases") or {}).items()):
        if slug38 not in _slug38:
            t38["broken"] += 1
            problems.append(_p("38", "content/cases.json: %s is not a listed piece" % slug38))
            continue
        if slug38 not in _feat38:
            t38["broken"] += 1
            problems.append(_p("38", "content/cases.json: %s carries a case but is not recorded as "
                                     "featured, so nothing on the site shows it" % slug38))
        t38["pieces"] += 1
        p38 = _slug38[slug38]
        heads38 = case_headings(p38["url"])
        rec38 = (_inv38.get(slug38) or {}).get("sets") or {}
        ids38 = set(rec38.get("ids") or ())
        for k38 in spec38:
            if k38 not in _keys38:
                t38["broken"] += 1
                problems.append(_p("38", "content/cases.json: %s names the slot %s, which is not one "
                                         "of the eight" % (slug38, k38)))
        for key38, _l38, _m38 in CASE_SLOTS:
            t38["slots"] += 1
            s38 = spec38.get(key38) or {}
            if not s38:
                t38["gap"] += 1
                continue
            if "sec" in s38:
                a38 = s38["sec"]
                if a38 not in heads38:
                    t38["broken"] += 1
                    problems.append(_p("38", "content/cases.json: %s names #%s for %s, and %s carries no "
                                             "heading with that id" % (slug38, a38, key38, p38["url"])))
                    continue
                if ids38 and a38 not in ids38:
                    t38["broken"] += 1
                    problems.append(_p("38", "content/cases.json: #%s is not an anchor the invariance "
                                             "record holds for %s" % (a38, slug38)))
                    continue
                t38["sec"] += 1
            elif "doc" in s38:
                ok38 = True
                for d38 in s38["doc"]:
                    if d38 not in _slug38:
                        ok38 = False
                        problems.append(_p("38", "content/cases.json: %s names %s for %s, which is not a "
                                                 "listed piece" % (slug38, d38, key38)))
                    elif (slug38, d38) not in _edge38:
                        ok38 = False
                        problems.append(_p("38", "content/cases.json: %s names %s for %s, and the corpus "
                                                 "records no link between them" % (slug38, d38, key38)))
                if ok38:
                    t38["doc"] += 1
                else:
                    t38["broken"] += 1
            elif "rec" in s38:
                v38 = s38["rec"]
                if v38 == "built_from" and p38.get("built_from"):
                    t38["rec"] += 1
                elif v38 == "piece":
                    t38["rec"] += 1
                else:
                    t38["broken"] += 1
                    problems.append(_p("38", "content/cases.json: %s asks %s for the record %r, which "
                                             "this build does not hold" % (slug38, key38, v38)))
            else:
                t38["broken"] += 1
                problems.append(_p("38", "content/cases.json: %s gives %s no source at all"
                                         % (slug38, key38)))
    # what the page actually printed, read back from the file rather than from
    # the generator that wrote it. An anchor that resolves is not the same
    # claim as a heading quoted correctly, and only the page can answer the
    # second one: a build that quotes a piece loosely still passes every test
    # that reads the piece instead of the page.
    _sel38 = os.path.join(OUT, "selected.html")
    if os.path.exists(_sel38):
        _raw38 = open(_sel38, encoding="utf-8", errors="ignore").read()
        _url38 = {q["url"]: q["slug"] for q in P}
        for _h38, _i38, _t38 in re.findall(
                r'<a class="cslot" href="([^"#]+)#([^"]+)">([^<]*)</a>', _raw38):
            t38["quoted"] += 1
            _sl38 = _url38.get(_h38)
            _rc38 = ((_inv38.get(_sl38) or {}).get("sets") or {}) if _sl38 else {}
            _hs38 = {invariance.norm_sentence(x) for x in (_rc38.get("headings") or ())}
            _said = invariance.norm_sentence(html.unescape(_t38))
            if _sl38 is None or _i38 not in set(_rc38.get("ids") or ()):
                t38["misquoted"] += 1
                problems.append(_p("38", "selected.html: quotes #%s of %s, which no invariance record "
                                         "holds" % (_i38, _h38)))
            elif _hs38 and _said not in _hs38:
                t38["misquoted"] += 1
                problems.append(_p("38", "selected.html: prints %r at #%s of %s, and the invariance record "
                                         "holds no such heading there" % (_said[:60], _i38, _h38)))
        if t38["quoted"] != t38["sec"]:
            problems.append(_p("38", "selected.html: prints %d quoted headings where the case map "
                                     "resolves %d" % (t38["quoted"], t38["sec"])))

    _said38 = case_coverage()
    for k38 in ("pieces", "slots", "sec", "doc", "rec", "gap"):
        if _said38.get(k38) != t38[k38]:
            problems.append(_p("38", "selected.html: the page counts %d %s and the files hold %d"
                                     % (_said38.get(k38, 0), k38, t38[k38])))

    # 39. the capability map. content/capabilities.json says which pieces
    # evidence each of the four things the about page claims, and that
    # membership is a reading. What is held: every named piece is one the site
    # lists, no capability is left with nothing behind it, every capability the
    # page draws has a map entry and every entry has a block, every piece named
    # is linked on the page, and every total printed beside a block is the sum
    # of that block's own pieces, recomputed here from content/metrics.json
    # rather than read back off the page.
    t39 = T["capabilities"] = {"caps": 0, "named": 0, "unknown": 0, "empty": 0,
                               "unlinked": 0, "wrong": 0}
    _map39 = (CAPS.get("capabilities") or {})
    _slug39 = {q["slug"]: q for q in P}
    _about39 = os.path.join(OUT, "about.html")
    _raw39 = open(_about39, encoding="utf-8", errors="ignore").read() if os.path.exists(_about39) else ""
    look("39", "about.html")
    for cid39, title39, _pr39 in CAP_BLOCKS:
        t39["caps"] += 1
        spec39 = _map39.get(cid39)
        if spec39 is None:
            t39["empty"] += 1
            problems.append(_p("39", "content/capabilities.json: nothing evidences %s, which the about "
                                     "page claims" % cid39))
            continue
        names39 = spec39.get("pieces") or []
        if not names39:
            t39["empty"] += 1
            problems.append(_p("39", "content/capabilities.json: %s names no piece at all" % cid39))
        w39 = f39 = b39 = 0
        for sl39 in names39:
            t39["named"] += 1
            q39 = _slug39.get(sl39)
            if q39 is None:
                t39["unknown"] += 1
                problems.append(_p("39", "content/capabilities.json: %s names %s, which is not a listed "
                                         "piece" % (cid39, sl39)))
                continue
            w39 += q39["words"]; f39 += q39["figures"]; b39 += q39["tables"]
            if _raw39 and ('href="%s"' % q39["url"]) not in _raw39:
                t39["unlinked"] += 1
                problems.append(_p("39", "about.html: %s is named as evidence for %s and the page links "
                                         "no such piece" % (sl39, cid39)))
        said39 = capability_evidence(cid39)
        for key39, want39 in (("words", w39), ("figures", f39), ("tables", b39)):
            if said39[key39] != want39:
                t39["wrong"] += 1
                problems.append(_p("39", "about.html: %s prints %d %s and its own pieces measure %d"
                                         % (cid39, said39[key39], key39, want39)))
    # the resume prints the same four subtotals; held here so the two pages
    # cannot disagree about what evidences a claim
    _res39 = os.path.join(OUT, "resume.html")
    if os.path.exists(_res39):
        _rraw39 = open(_res39, encoding="utf-8", errors="ignore").read()
        look("39", "resume.html")
        for cid39, title39, _pr39 in CAP_BLOCKS:
            e39 = capability_evidence(cid39)
            if not e39["n"]:
                continue
            want39 = "<span>%s words</span>" % format(e39["words"], ",")
            if want39 not in _rraw39:
                t39["wrong"] += 1
                problems.append(_p("39", "resume.html: does not print %s words for %s, which is what the "
                                         "about page prints and what its pieces measure"
                                         % (format(e39["words"], ","), cid39)))

    for cid39 in sorted(_map39):
        if cid39 not in {c for c, _t, _p2 in CAP_BLOCKS}:
            t39["wrong"] += 1
            problems.append(_p("39", "content/capabilities.json: %s evidences nothing the about page "
                                     "claims" % cid39))

    # 33. the editor. admin.html is hand-maintained and the build never
    # writes it. Held here: the file is byte-identical to the bytes this run
    # started from; it is a whole document (the doctype at one end, </html> at
    # the other, every script and style block closed); every stylesheet,
    # script and local asset it references resolves to a file here; every
    # custom property its own styles read is defined by a stylesheet it loads
    # or by the page; every element id its script names as a literal is in
    # its markup; each inline script parses (node --check, when node is on
    # the path; the tally says whether it was, and without node the
    # falsification for it is missed and the row prints untested); it invites
    # no index (noindex on the page, Disallow in robots.txt); the worker the
    # build writes never stores it and the offline copy never lists it. What
    # the page does when opened (console errors, exceptions, failed requests,
    # its controls) is the audit's to measure, under the register's editor
    # row.
    t33 = T["editor"] = {"files": 0, "bytes": 0, "rewritten": 0, "refs": 0, "broken": 0, "tokens": 0,
                         "undefined": 0, "ids": 0, "missing": 0, "scripts": 0, "unparsed": 0,
                         "parsed_by": "node" if shutil.which("node") else "none"}

    def _scripts_parse(text):
        # Only the blocks a browser runs as script: one carrying a type that is
        # not JavaScript is data (a JSON payload is the case on the generated
        # pages) and is not parsed as a program.
        node = shutil.which("node")
        bad = []
        for i, m in enumerate(re.finditer(r"<script\b([^>]*)>(.*?)</script>", text, re.S | re.I)):
            attrs, src = m.group(1), m.group(2)
            mt = re.search(r'\btype\s*=\s*"([^"]*)"', attrs, re.I)
            if mt and mt.group(1).strip().lower() not in ("", "text/javascript", "application/javascript", "module"):
                continue
            if not src.strip():
                continue
            t33["scripts"] += 1
            if not node:
                continue
            fd, tmp = tempfile.mkstemp(suffix=".js")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(src)
            try:
                r = subprocess.run([node, "--check", tmp], capture_output=True, text=True, timeout=60)
            finally:
                os.unlink(tmp)
            if r.returncode != 0:
                lines = [ln.strip() for ln in (r.stderr or "").strip().splitlines() if ln.strip()]
                why = next((ln for ln in lines if "Error" in ln), lines[0] if lines else "did not parse")
                bad.append((i + 1, why[:120]))
        return bad

    for f in PROTECTED:
        look("33", f)
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            problems.append(_p("33", f"{f}: missing"))
            continue
        raw = open(path, "rb").read()
        text = raw.decode("utf-8", errors="ignore")
        t33["files"] += 1
        t33["bytes"] += len(raw)
        was = _PROTECTED_BYTES.get(f)
        if was is None:
            problems.append(_p("33", f"{f}: was not on disk when the build started"))
        elif raw != was:
            t33["rewritten"] += 1
            problems.append(_p("33", f"{f}: the build rewrote it ({len(was):,} bytes became {len(raw):,}); no build step may write the editor"))
        stripped = text.strip()
        if not stripped.lower().startswith("<!doctype html>") or not stripped.lower().endswith("</html>"):
            problems.append(_p("33", f"{f}: is not a whole document; it must open with the doctype and close with </html>"))
        for tag in ("script", "style"):
            opened = len(re.findall(r"<%s\b" % tag, text, re.I))
            closed = len(re.findall(r"</%s>" % tag, text, re.I))
            if opened != closed:
                problems.append(_p("33", f"{f}: {opened} <{tag}> tags open and {closed} close"))
        prose = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", text, flags=re.S | re.I)
        for m in re.finditer(r'(?:href|src)="([^"]+)"', prose):
            u = local(m.group(1))
            if u:
                t33["refs"] += 1
                if u not in files:
                    t33["broken"] += 1
                    problems.append(_p("33", f"{f}: references {u}, which is not a file here"))
        defined = set(re.findall(r"(--[A-Za-z0-9_-]+)\s*:", text))
        for sheet in re.findall(r'<link rel="stylesheet" href="([^"?]+)', text):
            sp = os.path.join(OUT, sheet)
            if os.path.exists(sp):
                defined |= set(re.findall(r"(--[A-Za-z0-9_-]+)\s*:", open(sp, encoding="utf-8", errors="ignore").read()))
        for tok in sorted(set(re.findall(r"var\((--[A-Za-z0-9_-]+)", text))):
            t33["tokens"] += 1
            if tok not in defined:
                t33["undefined"] += 1
                problems.append(_p("33", f"{f}: reads {tok}, which no stylesheet it loads defines"))
        ids = set(re.findall(r'\bid="([^"]+)"', prose))
        for name in sorted(set(re.findall(r"(?:\$|getElementById)\(\s*'([A-Za-z][\w-]*)'\s*\)", text))):
            t33["ids"] += 1
            if name not in ids:
                t33["missing"] += 1
                problems.append(_p("33", f"{f}: its script asks for #{name}, which its markup does not carry"))
        for which, why in _scripts_parse(text):
            t33["unparsed"] += 1
            problems.append(_p("33", f"{f}: script block {which} does not parse: {why}"))
        if not re.search(r'<meta name="robots" content="[^"]*noindex', text):
            problems.append(_p("33", f"{f}: carries no noindex"))
    robots33 = page_robots()
    m33 = re.search(r"const NEVER_STORED\s*=\s*\[(.*?)\]", SW_TEMPLATE, re.S)
    never33 = set(re.findall(r'"([^"]+)"', m33.group(1))) if m33 else set()
    off33 = set(offline_files())
    for f in PROTECTED:
        if f"Disallow: /{f}" not in robots33:
            problems.append(_p("33", f"robots.txt: does not disallow /{f}"))
        if f not in never33:
            problems.append(_p("33", f"sw.js: the worker the build writes does not name {f} among the files it never stores"))
        if f in off33:
            problems.append(_p("33", f"offline-manifest.json: the offline copy lists {f}"))

    # 29. every glyph on the controls page is a record. The page wall and the
    # falsification ledger are parsed back from the rendered page and each
    # glyph is compared with the record it stands for: the check's per-page
    # outcome, the audit's current measurement, or the falsification's
    # result, with the glyph vocabulary stated here a second time on purpose,
    # so the page is held to the records and not to the code that drew it.
    cpath = os.path.join(OUT, "controls.html")
    look("29", "controls.html")
    t29 = T["instrument"] = {"glyphs": 0, "pages": 0, "columns": 0, "disagree": 0, "falsifications": 0, "ledger_disagree": 0}
    if not os.path.exists(cpath):
        problems.append(_p("29", "controls.html: missing"))
    else:
        ctext = open(cpath, encoding="utf-8", errors="ignore").read()
        cctx = _claims_ctx(problems)
        st29, R29 = cctx["audit"], check_site.records
        decl29 = set(DECLARED.get("overflow") or [])
        rt_keys = {lab: key for key, lab in claims.RUNTIME_COLS}
        wall = re.search(r'<table class="inst" id="page-wall">(.*?)</table>', ctext, re.S)
        if not wall:
            problems.append(_p("29", "controls.html: carries no page wall"))
        else:
            cols = re.findall(r'<th scope="col" class="ic ic-(build|runtime)"><span>([^<]+)</span></th>', wall.group(1))
            t29["columns"] = len(cols)
            seen_pages, shown = set(), 0
            colsum = {lab: 0 for _k, lab in cols}
            for m in re.finditer(r'<tr class="ir ir-\w+"><th scope="row" class="ip"><a href="([^"]+)">[^<]*</a></th>(.*?)</tr>', wall.group(1), re.S):
                page = m.group(1)
                cells = re.findall(r'<td class="g (g-[hxqdn])">([^<]*)</td>', m.group(2))
                t29["pages"] += 1
                seen_pages.add(page)
                if len(cells) != len(cols):
                    problems.append(_p("29", f"controls.html: {page} shows {len(cells)} glyph cells under {len(cols)} columns"))
                    continue
                for (kind, lab), (cls, glyph) in zip(cols, cells):
                    if glyph:
                        t29["glyphs"] += 1
                        colsum[lab] += 1
                    if kind == "build":
                        v = R29.get(lab, {}).get(page)
                        if lab == "29" and page == "controls.html":
                            v = None   # a check does not grade its own glyph
                        exp = "" if v is None else ("#" if v else "x")
                    else:
                        key = rt_keys.get(lab)
                        # which pages a runtime key applies to is said once, in claims.py
                        applies = key is not None and page in claims.runtime_pages(key, SHELL_PAGES, cctx["all_pages"], cctx["aux_pages"])
                        if not applies:
                            exp = ""
                        elif page in st29["fresh"] and st29["fresh"][page].get(key) is not None:
                            ok = claims.page_ok(key, st29["fresh"][page])
                            exp = "~" if (key == "fit" and not ok and page in decl29) else ("#" if ok else "x")
                        else:
                            exp = "?"
                    if glyph != exp:
                        t29["disagree"] += 1
                        if shown < 5:
                            shown += 1
                            problems.append(_p("29", f"controls.html: {page} under {lab} shows {glyph!r}, the record says {exp!r}"))
            all29 = set(cctx["all_pages"]) | set(cctx["aux_pages"])
            if seen_pages != all29:
                problems.append(_p("29", "controls.html: the wall lists %d pages, the site has %d" % (len(seen_pages), len(all29))))
            foot = re.search(r'<tr class="isum"><th scope="row" class="ip">pages the check looked at</th>(.*?)</tr>', wall.group(1), re.S)
            sums = [int(x) for x in re.findall(r'<td class="is">(\d+)</td>', foot.group(1))] if foot else []
            if sums != [colsum[lab] for _k, lab in cols]:
                problems.append(_p("29", "controls.html: the wall's column totals are not the count of its glyphs"))
        ledg = re.search(r'<table class="inst inst-ledger" id="falsifications">(.*?)</table>', ctext, re.S)
        if not ledg:
            problems.append(_p("29", "controls.html: carries no falsification ledger"))
        else:
            neg29 = cctx["negatives"]
            rt_names = {lab: key for key, lab in claims.RUNTIME_COLS} | {"O": "offline"}
            for m in re.finditer(r'<tr><th scope="row" class="ip">([^<]+)</th><td class="ig">(.*?)</td><td class="is">([^<]*)</td>', ledg.group(1), re.S):
                name, glyphs, count = m.group(1), re.findall(r'class="g (g-[hxqdn])"', m.group(2)), m.group(3)
                if name.startswith("check "):
                    cases = neg29["build"].get(name[6:], [])
                else:
                    cases = neg29["runtime"].get(name, [])
                exp = ["g-q" if not c.get("current") else ("g-h" if c.get("caught") else "g-x") for c in cases] or ["g-n"]
                t29["falsifications"] += len(cases)
                if glyphs != exp:
                    t29["ledger_disagree"] += 1
                    problems.append(_p("29", f"controls.html: the ledger line for {name} shows {len(glyphs)} glyph(s) that are not the record's"))

    # 13. no numeral in shell copy is typed. Every numeral of two or more
    # digits, or carrying a decimal or a thousands separator, on a generated
    # page must be a value the build computed, or a figure a piece states in
    # its own text where the shell quotes that piece. One-digit numerals are
    # left alone: note references and the small counts of a sentence.
    # The scan itself runs in main's fixpoint, on the pages as written from
    # this round's records, so the register's and the instrument's numbers
    # are known to it from the very records that produced them (read from the
    # computed strings, never from a claim sentence). Here the check records
    # its coverage and the previous scan's count for the register's row.

    return sorted(set(problems))


_NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d{3,})(?![\w])")
# two-digit numerals, held to the same registry wherever they stand in shell
# prose; one-digit numerals stay free (note references, "the 6 above")
_SMALL = re.compile(r"(?<![\w.,])(\d{2})(?![\w.,%])")


def _readable_text(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    raw = re.sub(r"<(script|style|svg)\b[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", raw))


def _num(s):
    return round(float(s.replace(",", "")), 6)


def _piece_numbers(url):
    """Every numeral a piece states in its own readable text, as values, so a
    shell caption that says 0.20 matches a piece that says 0.2. The text a
    piece draws inside its figures counts as stated: a lifted figure's
    restated numbers are held to it."""
    path = os.path.join(OUT, url)
    if not os.path.exists(path):
        return set()
    text = _readable_text(path)
    raw = open(path, encoding="utf-8", errors="ignore").read()
    for sv in re.findall(r"<svg\b.*?</svg>", raw, flags=re.S | re.I):
        text += " " + " ".join(figure_numbers(sv))
    return {_num(x) for x in _NUM.findall(text)} | \
        {_num(x) for x in re.findall(r"(?<![\w.])(\d{1,2}(?:\.\d+)?)(?![\w])", text)}


def _known_numbers():
    vals = set()
    def add(x):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            vals.add(round(float(x), 6)); vals.add(float(round(x)))
        elif isinstance(x, dict):
            for v in x.values(): add(v)
        elif isinstance(x, (list, tuple, set)):
            for v in x: add(v)
        elif isinstance(x, str):
            for m in _NUM.findall(x): vals.add(_num(m))
            for m in _SMALL.findall(x): vals.add(_num(m))
    add(case_coverage()); add(len(CASE_SLOTS))
    for _cid, _t, _pr in CAP_BLOCKS:
        add(capability_evidence(_cid))
    add([len(P), TOTAL_WORDS, TOTAL_FIGS, TOTAL_TBLS, CHECKPOINTS, DOC_MIN, WPM,
         FONT_BYTES, FONT_CODEPOINTS, N_TOOLS, N_PWA, N_INDEP, N_COURSE, N_PERSONAL,
         len(COURSES), UNIT, len(SHELL_PAGES), 404])
    # the colophon's definitions: figure area floor, density bands and floor
    add([6000, 1.0, 3.0, 400])
    add(figs.group_totals()); add(surface_totals())
    for p in P:
        add([p["words"], p["figures"], p["tables"], p["apparatus"],
             p.get("mins"), reading_minutes(p["words"])])
    for c in COURSES:
        cs = [p for p in P if p["c"] == c]
        add([len(cs), sum(p["words"] for p in cs), sum(p["figures"] for p in cs),
             sum(p["tables"] for p in cs),
             sum(1 for p in cs if p["k"] == "Tool"), sum(1 for p in cs if p["k"] != "Tool")])
        add(re.findall(r"\d+", c))
    # the shelves' own subtotals: per kind, and per kind within an origin
    for kind in ("Essay", "Reference", "Tool"):
        ks = [p for p in P if p["k"] == kind]
        add([len(ks), sum(p["words"] for p in ks), sum(p["figures"] for p in ks), sum(p["tables"] for p in ks)])
    cru = [p for p in P if p["slug"] in ("crucible-run-0", "crucible-run-b", "crucible-run-c")]
    add(sum(p["words"] for p in cru))
    add(len(ATLAS.get("points") or [])); add(ATLAS.get("facts") or {})
    add(len(ATLAS.get("edges") or []))
    for r in ATLAS.get("regions") or []:
        add(r.get("n"))
    off = offline_files()
    add([len(off), round(sum(os.path.getsize(os.path.join(OUT, f)) for f in off) / 1048576)])
    ex = exceptions()
    add([len(ex["fonts"]), len(ex["undrawn"]), ex["undrawn_words"], len(ex["transcripts"]),
         len(ex["tools"]), ex["kinds"]["md"], ex["kinds"]["doc"],
         TRANSCRIPT_WORDS, TOTAL_WORDS + TRANSCRIPT_WORDS, len(P) + len(ex["transcripts"])])
    # the marks: every value the colophon's four ledgers print is read from
    # content/marks or computed by the generator on this build
    add(marks_mod.facts()); add(marks_mod.glyph_facts()); add(marks_mod.seal_facts())
    add(marks_mod.callout_numbers()); add(fingerprint.facts()); add(fingerprint_coverage())
    _gf, _sf = marks_mod.glyph_facts(), marks_mod.seal_facts()
    add([len(marks_mod.callouts()), len(marks_mod.GLYPHS), marks_mod.SEAL_DROP,
         # the count line adds the three families together
         marks_mod.facts()["elements"] + _gf["elements"] + _sf.get("elements", 0),
         len(marks_mod.FILES) + _gf["n"] + (0 if _sf.get("missing") else 1)])
    for r in marks_mod.audit()["rows"]:
        add([r["claimed"], r["read"]])
    # the lifted figures, and the tools the drawing reaches
    add([len(STRIP), len(LIFTS)])
    add([len(x) for x in tools_drawn()])
    add(LEDGER.get("summary") or {})
    add(built_from_counts([p for p in P if p["surface"] == "course"]))
    # the register's numbers: every tally the checks kept on this run, what
    # the browser audit recorded for the pages whose record is current, the
    # sums the register prints over them, and the negatives' counts. Check
    # 13 runs after every other check, so the tallies are complete; the
    # register on the page was printed from the previous round of the
    # fixpoint, and the round that settles is the one whose numbers agree.
    add(getattr(check_site, "tally", {}))
    return vals


def _typed_numerals(extra_known=None):
    out = []
    known = _known_numbers() | set(extra_known or ())
    years = {float(y) for y in range(1900, 2031)}
    # what the shell quotes from pieces: the owner's own fields, and lifted captions
    quoted = set()
    for p in P:
        stated = _piece_numbers(p["url"])
        for k in ("t", "s", "blurb", "demo", "tags"):
            field = " ".join(p.get(k) or []) if k == "tags" else str(p.get(k) or "")
            for m in _NUM.findall(field) + _SMALL.findall(field):
                if _num(m) in stated:
                    quoted.add(_num(m))
                else:
                    out.append("content/pieces.json: %s.%s quotes %s, which %s does not state"
                               % (p["slug"], k, m, p["url"]))
    for text, href in CAPTIONS:
        stated = _piece_numbers(href)
        for m in _NUM.findall(text) + _SMALL.findall(text):
            if _num(m) in stated:
                quoted.add(_num(m))
            else:
                out.append("lifted caption for %s quotes %s, which the piece does not state"
                           % (href, m))
    # the case map quotes each piece's own headings, so a numeral inside one is
    # the piece's, not this build's; the quote is held to the piece all the same
    for slug in (CASES.get("cases") or {}):
        if slug not in CASE_BY_SLUG:
            continue
        href = CASE_BY_SLUG[slug]["url"]
        stated = _piece_numbers(href)
        for r in case_rows(slug):
            if r["kind"] != "sec":
                continue
            for m in _NUM.findall(r["text"]) + _SMALL.findall(r["text"]):
                if _num(m) in stated:
                    quoted.add(_num(m))
                else:
                    out.append("the case map quotes %s from a heading of %s, which the piece "
                               "does not state" % (m, href))
    checked = 0
    for f in SHELL_PAGES:
        path = os.path.join(OUT, f)
        if not os.path.exists(path):
            continue
        raw = open(path, encoding="utf-8", errors="ignore").read()
        # the atlas index is the pieces' own headings, which are content
        raw = re.sub(r'<section class="areg".*?</section>', " ", raw, flags=re.S)
        # the last pass's notes on the colophon are a record reproduced as
        # written; their numerals are the pass's own, not this build's
        raw = re.sub(r'<section[^>]*id="limits".*?</section>', " ", raw, flags=re.S)
        raw = re.sub(r"<(script|style|svg)\b[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
        # the statement rows are numbered by position, which is a count of
        # the list, not a quantity; the number is cut out before the scan
        raw = re.sub(r'<span class="num tnum">\d+</span>', " ", raw)
        text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        for m in _NUM.findall(text) + _SMALL.findall(text):
            checked += 1
            v = _num(m)
            if v in known or v in years or v in quoted:
                continue
            out.append("%s: prints %s, which the build did not compute and no piece states" % (f, m))
    _typed_numerals.checked = checked
    return out


def write_offline(changed):
    """The full-offline manifest and the worker, from the files as they stand.
    Called after the register settled, because both digest every file the
    offline copy holds, the colophon among them; and on its own by
    --offline-only, which build/audit.js uses to turn a copy of the tree with
    one changed page into the next generation a publish would produce."""
    # The full-offline manifest: every file a reader needs to hold the whole
    # site on a phone, from the one selection rule offline_files() states.
    off_files = offline_files()
    _oh = hashlib.sha1()
    digests = {}
    for f in off_files:
        _oh.update((f + str(os.path.getsize(os.path.join(OUT, f)))).encode())
        with open(os.path.join(OUT, f), "rb") as fh:
            digests[f] = hashlib.sha1(fh.read()).hexdigest()[:12]
    off_bytes = sum(os.path.getsize(os.path.join(OUT, f)) for f in off_files)
    # a digest per file, so a saved copy can refresh only what changed
    off = json.dumps({"version": _oh.hexdigest()[:12],
                      "bytes": off_bytes,
                      "files": off_files,
                      "digests": digests}, indent=1)
    offpath = os.path.join(OUT, "offline-manifest.json")
    if (not os.path.exists(offpath)) or open(offpath, encoding="utf-8").read() != off:
        open(offpath, "w", encoding="utf-8").write(off)
        changed.append("offline-manifest.json")

    # The page cache is named by a digest of the CONTENTS of every file the
    # offline copy holds, computed here, after the piece pass, for the same
    # reason the CORE digest is. It used to be the constant "site-pages-v1",
    # which the activate filter exempted, so every page a reader had ever
    # loaded persisted across every build and was served cache-first: two
    # generations of the site in one session. A size digest would not do:
    # 483,735 and 483,784 are the same number of characters.
    _ph = hashlib.sha1()
    for f in off_files:
        with open(os.path.join(OUT, f), "rb") as fh:
            _ph.update(f.encode("utf-8") + fh.read())
    sw = page_sw(_ph.hexdigest()[:12])
    swpath = os.path.join(OUT, "sw.js")
    if (not os.path.exists(swpath)) or open(swpath, encoding="utf-8").read() != sw:
        open(swpath, "w", encoding="utf-8").write(sw)
        changed.append("sw.js")



def main():
    # First, because it writes anchor ids into the pieces themselves and every
    # later pass reads those files. Giving a section a name is a content edit,
    # so it happens once and then never again: an id already present is kept.
    atlas_mod.AUTHOR = {"t": NAME, "url": "about.html", "id": "author"}
    ATLAS["points"], ATLAS["regions"], ATLAS["zones"] = (lambda d: (d["points"], d["regions"], d["zones"]))(
        atlas_mod.build(OUT, P)[0])
    ATLAS["edges"] = atlas_mod.edges(OUT, P)

    # The digests have to be known before any page is written, because every
    # page prints them. figures.css is generated by this build, so it is
    # stamped from the text about to be written rather than from the copy on
    # disk, which is still the previous build's.
    figures_css = ("/* Generated from build/figures.json. Do not edit: the next build\n"
                   "   overwrites it. Each lifted figure keeps the colour variables and\n"
                   "   class rules it was drawn against, scoped to its own id so nothing\n"
                   "   leaks into the page around it. */\n" + strip_css() + "\n")
    stamp_assets({"figures.css": figures_css})

    pages = {"index.html": page_index(), "research.html": page_research(),
             "atlas.html": page_atlas(),
             "coursework.html": page_coursework(), "tools.html": page_tools(),
             "selected.html": page_selected(),
             "library.html": page_library(), "about.html": page_about(),
             "404.html": page_404(),
             "sitemap.xml": page_sitemap(), "robots.txt": page_robots(),
             "figures.css": figures_css}
    changed = []
    for name, text in pages.items():
        path = os.path.join(OUT, name)
        old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if old != text:
            open(path, "w", encoding="utf-8").write(text)
            changed.append(name)

    for f, css in OVERFLOWING.items():
        path = os.path.join(OUT, f)
        if os.path.exists(path) and f not in PROTECTED:
            fit_mobile(path, css)

    n, heads, navs, figs_named, tails, titles = add_returns_everywhere()

    # The register on the colophon prints what the checks found, and the
    # checks read the colophon, so the two are run to a fixpoint: check,
    # print the register, rewrite the colophon if it moved, check again. The
    # register's shape does not depend on its numbers, so the second pass
    # settles it; a cap guards the loop all the same, and only the check
    # that ran on the colophon as finally written decides the build.
    all_pages = list(SHELL_PAGES) + [p["url"] for p in P] + [k + ".html" for k in exceptions()["transcripts"]]
    colpath = os.path.join(OUT, "colophon.html")
    ctlpath = os.path.join(OUT, "controls.html")
    respath = os.path.join(OUT, "resume.html")
    started_with = {pth: (open(pth, encoding="utf-8").read() if os.path.exists(pth) else None) for pth in (colpath, ctlpath, respath)}
    # the two pages are written only here, from the records: written first
    # without them and again with them, every build rewrote the pages
    if not os.path.exists(colpath):
        open(colpath, "w", encoding="utf-8").write(page_colophon())
        changed.append("colophon.html")
    if not os.path.exists(ctlpath):
        open(ctlpath, "w", encoding="utf-8").write("<!DOCTYPE html><html><head><title>Controls</title></head><body><a class=\"skip\" href=\"#main\">Skip to content</a><main id=\"main\"></main></body></html>")
        changed.append("controls.html")
    # the resume prints the register's tallies, so it is written here for the
    # same reason the colophon is: written before the checks it would say zero
    if not os.path.exists(respath):
        open(respath, "w", encoding="utf-8").write(page_resume())
        changed.append("resume.html")
    settled = False
    for _round in range(5):
        problems = check_site()
        ctx = _claims_ctx(problems)
        rows, summary = claims.build(ctx)
        problems = sorted(set(problems + ctx["problems"]))
        meta = (ctx["audit"]["audit"] or {}).get("meta") or {}
        register_html = claims.render(rows, summary, meta, ctx["negatives"])
        instrument_html, counts = claims.render_instrument(ctx)
        new_ctl = page_controls(register_html, instrument_html, counts, summary)
        new_col = page_colophon(summary=summary)
        new_res = page_resume(summary=summary)
        moved = False
        for path, text, name in ((ctlpath, new_ctl, "controls.html"), (colpath, new_col, "colophon.html"),
                                 (respath, new_res, "resume.html")):
            on_disk = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if text != on_disk:
                open(path, "w", encoding="utf-8").write(text)
                moved = True
        # check 13, on the pages just written, knowing every number this
        # round's records put on them
        for line in _typed_numerals(claims.known_numbers(ctx)):
            problems.append(_p("13", line))
        problems = sorted(set(problems))
        if not moved:
            settled = True
            break
    if not settled:
        problems.append("controls.html: the register did not settle in five rounds")
    # the first round prints the previous scan's count and is rewritten by the
    # second, so a page counts as rewritten only if it ends up different
    for pth, name in ((ctlpath, "controls.html"), (colpath, "colophon.html"), (respath, "resume.html")):
        if open(pth, encoding="utf-8").read() != started_with[pth] and name not in changed:
            changed.append(name)
    check_site.register = summary

    # the editor is never the build's to write: should any pass have changed
    # a protected file, the bytes the build started from go back, and check
    # 33 has already refused the build that did it
    for _f, _was in _PROTECTED_BYTES.items():
        _pth = os.path.join(OUT, _f)
        _now = open(_pth, "rb").read() if os.path.exists(_pth) else None
        if _was is not None and _now != _was:
            open(_pth, "wb").write(_was)
            problems.append(_p("33", f"{_f}: restored from the bytes the build started with"))
            problems = sorted(set(problems))

    write_offline(changed)

    print(f"{len(P)} pieces · {TOTAL_WORDS:,} words · {TOTAL_FIGS} figures · {TOTAL_TBLS} tables")
    print("rewrote: " + (", ".join(changed) if changed else "nothing, pages already current"))
    _gaps = resume_gaps()
    if _gaps:
        print("resume: %s declared and unsupplied in content/resume.json; "
              "the page renders neither" % ", ".join(_gaps))
    if figs_named:
        print(f"accessible names written on {figs_named} figures")
    if navs:
        print(f"section nav rewritten on {navs} "
              f"{'piece' if navs == 1 else 'pieces'}")
    print(f"return navigation checked on {n} standalone pieces, "
          f"head metadata written on {heads}")
    if titles or TITLE_SKIPPED:
        print(f"page title owned on {titles} pieces; the title alone on {len(TITLE_ALONE)}; "
              f"left as written on {len(TITLE_SKIPPED)}" + (":" if TITLE_SKIPPED else ""))
        for slug, cur in TITLE_SKIPPED:
            print(f"  {slug}: {cur}")
    if getattr(add_returns_everywhere, "longs", 0):
        print(f"reading kit (section index, reading position, 66ch measure, print rules) on "
              f"{add_returns_everywhere.longs} pieces over {LONG_WORDS:,} words")
    if tails:
        ok = tails - len({x.split(":")[0] for x in TAIL_PROBLEMS})
        print(f"conversion sentence, footer and search block owned on {tails} converted pieces; "
              f"text outside the blocks byte-identical on {ok} of {tails}")
    inv = getattr(check_site, "invariance", None)
    if inv:
        n_tr = len(exceptions()["transcripts"])
        print(f"invariance: {inv['held']} of {inv['checked']} records hold every numeral, reference, "
              f"label, anchor and result sentence ({len(P)} listed pieces and {n_tr} transcripts); "
              f"{inv['declared']} carry declared strikes")
    if problems:
        # the checks that fired, by id, on one line: what build/negatives.py
        # reads to decide whether a falsification was caught by the check
        # the claim names, rather than by the build failing for any reason
        fired = sorted({m.group(1) for m in (re.match(r"check (\S+):", x) for x in problems) if m},
                       key=lambda k: (int(re.match(r"\d+", k).group(0)), k))
        print(f"\n{len(problems)} problem(s) found. The site was written, but this is broken:")
        if fired:
            print("checks that failed: " + ", ".join(fired))
        for line in problems[:40]:
            print("  " + line)
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        sys.exit(1)
    print("checks passed: every link, canonical, icon and listed file resolves")

if __name__ == "__main__":
    if "--offline-only" in sys.argv:
        _ch = []
        write_offline(_ch)
        print("offline: " + (", ".join(_ch) if _ch else "nothing, already current"))
        sys.exit(0)
    main()
