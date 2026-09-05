# -*- coding: utf-8 -*-
"""Tests of controls: for every check, a recorded case where the claim is
deliberately made false and the check is shown to catch it.

A register that prints "held" beside every claim proves only that the
checks agree with themselves. A control that has never been observed to
fail is not evidence that it operates. So each check here has at least one
falsification: an edit to a copy of the tree that makes the claim false at
its source (a piece, the content, the fonts, the workflow, or the build's
own code), after which the whole build is run in that copy and must refuse,
naming the check. The result is recorded in content/negatives.json with a
digest of the code it was recorded against; the register prints a checked
claim as held only while a current, caught falsification stands behind
every check it cites, and prints "untested" otherwise.

The falsifications are edits to sources, never to the checks: a falsifier
that reached into a check would prove nothing. Each one is described in
one sentence beside its row, so a reader can judge whether it is the
failure that matters.

usage: python3 build/negatives.py            run the cases the record lacks
                                             or holds for other code
       python3 build/negatives.py --all      run every case again
       python3 build/negatives.py --only 3,15
       python3 build/negatives.py --stale    print whether the record is
                                             current for this code
       python3 build/negatives.py --list
Options: --jobs N (default 3), --keep (leave the last copy on disk).
"""
import concurrent.futures, datetime, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "content", "negatives.json")
BS = "build/build_site.py"
# the code a build-level falsification exercises: the checks, the modules
# they call, this file, and the workflow the deploy gate reads
BUILD_CODE = ["build/build_site.py", "build/claims.py", "build/atlas.py", "build/invariance.py",
              "build/ledger.py", "build/marks.py", "build/fingerprint.py", "build/negatives.py",
              ".github/workflows/build.yml"]
PIECE_SMALL = "positive-vs-normative.html"          # a short listed piece, not a record
PIECE_CONVERTED = "afm291-ch1-theory-and-analytics.html"   # a converted document with a body


class Falsifier(Exception):
    pass


def code_digest(files=BUILD_CODE):
    h = hashlib.sha1()
    for f in files:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            h.update(f.encode()); h.update(open(p, "rb").read())
    return h.hexdigest()[:12]


# ------------------------------------------------------------ editing --
def _edit(tree, rel, old, new, count=1):
    p = os.path.join(tree, rel)
    s = open(p, encoding="utf-8").read()
    if s.count(old) != count:
        raise Falsifier("anchor %r found %d time(s) in %s, expected %d" % (old[:50], s.count(old), rel, count))
    open(p, "w", encoding="utf-8").write(s.replace(old, new))


def _regex(tree, rel, pattern, repl, count=1, flags=0):
    p = os.path.join(tree, rel)
    s = open(p, encoding="utf-8").read()
    new, n = re.subn(pattern, repl, s, count=count, flags=flags)
    if n != count:
        raise Falsifier("pattern %r matched %d time(s) in %s" % (pattern[:50], n, rel))
    open(p, "w", encoding="utf-8").write(new)


def _json(tree, rel, fn):
    p = os.path.join(tree, rel)
    d = json.load(open(p, encoding="utf-8"))
    fn(d)
    json.dump(d, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def _before_body_end(tree, rel, html):
    _edit(tree, rel, "</body>", html + "\n</body>")


def _in_block(tree, rel, start, end, pattern, repl):
    """A regex replacement confined to the text between two anchors."""
    p = os.path.join(tree, rel)
    s = open(p, encoding="utf-8").read()
    i = s.index(start); j = s.index(end, i + len(start))
    block, n = re.subn(pattern, repl, s[i:j], count=1)
    if n != 1:
        raise Falsifier("pattern %r not found between %r and %r in %s" % (pattern, start, end, rel))
    open(p, "w", encoding="utf-8").write(s[:i] + block + s[j:])


def _set_piece(field, value, slug=None, index=None):
    def fn(d):
        ps = d["pieces"]
        p = next(x for x in ps if x["slug"] == slug) if slug else ps[index]
        p[field] = value
    return fn


# -------------------------------------------------------------- cases --
def C(check, name, what, mutate):
    return {"id": "%s-%s" % (check, name), "check": check, "what": what, "mutate": mutate}


def _strip_figure_name(d):
    svg = d["fs-tv1"]["svg"]
    svg = re.sub(r'\s+aria-labelledby="[^"]*"', "", svg)
    svg = re.sub(r'\s+aria-label="[^"]*"', "", svg)
    svg = svg.replace("<title", "<desc").replace("</title>", "</desc>")
    d["fs-tv1"]["svg"] = svg


def _ledger_class_flip(d):
    slug, entry = next(iter(d["pieces"].items()))
    entry["class"] = "styling" if entry["class"] != "styling" else "copy"


def _font_sha_flip(d):
    fname, rec = next(iter(d["files"].items()))
    rec["sha256"] = "0" * 64


CASES = [
    C("1", "canonical-offsite", "the build writes every canonical address on another site",
      lambda t: _edit(t, BS, '<link rel="canonical" href="{SITE_URL}/', '<link rel="canonical" href="https://elsewhere.invalid/')),
    # a piece cannot carry this falsification: the build rewrites any stale
    # GitHub Pages host in a piece to this site's before the check runs, so
    # the check can only ever fail on a page the build writes from a template
    C("2", "other-host-named", "the footer of every generated page names another GitHub Pages host",
      lambda t: _edit(t, BS, "no framework, nothing external at runtime", "formerly at someone-else.github.io, nothing external at runtime")),
    C("3", "dead-link", "a piece links to a file that does not exist",
      lambda t: _before_body_end(t, PIECE_SMALL, '<p><a href="no-such-page.html">a page that is not there</a></p>')),
    C("4", "icon-missing", "the site manifest names an icon file that does not exist",
      lambda t: _edit(t, "site.webmanifest", '"src": "site-192.png"', '"src": "site-192-gone.png"')),
    C("5", "figure-scope-missing", "a lifted figure loses its colour scope in figures.css",
      lambda t: _json(t, "build/figures.json", lambda d: d["fs-tv1"].update({"css": "", "light": {}, "dark": {}}))),
    C("6", "second-h1", "a converted document gains a second top-level heading in its body",
      lambda t: _regex(t, PIECE_CONVERTED, r"(<h1\b[^>]*>.*?</h1>)", r"\1<h1>Another top-level heading</h1>", flags=re.S)),
    C("7", "head-ended-early", "the build puts a div inside head, which ends the head before the canonical",
      lambda t: _edit(t, BS, "<noscript><style>.hbtns", "<div></div><noscript><style>.hbtns")),
    C("8", "atlas-anchor-dead", "the placement points every mark at an anchor no document carries",
      lambda t: _edit(t, "build/atlas.py", '"u": s["url"] + ("#" + s["id"] if s["id"] else ""),',
                      '"u": s["url"] + ("#" + s["id"] + "-gone" if s["id"] else ""),')),
    C("9", "listed-file-missing", "content/pieces.json lists a file that does not exist",
      lambda t: _json(t, "content/pieces.json", _set_piece("url", "not-there.html", index=-1))),
    C("10", "glyph-outside-subset", "the build prints a character Inter could render that the self-hosted subset lacks",
      lambda t: _edit(t, BS, "<span>&copy; {TODAY.year} {esc(NAME)}</span>", "<span>&copy; {TODAY.year} {esc(NAME)} Ω</span>")),
    C("11", "chrome-colour-unknown", "the chrome the build writes into pieces states a colour the stylesheet does not know",
      lambda t: _in_block(t, BS, 'RETURN_BAR = """', '"""\n', r"#[0-9a-fA-F]{6}\b", "#123456")),
    C("11a", "stray-mark", "the Atlas page carries a mark at a position the placement did not produce",
      lambda t: _edit(t, BS, '        word = "section" if len(items) == 1 else "sections"\n',
                      '        lis += \'\\n<li data-p="0.100,0.200,0.300" data-w="0"><a href="atlas.html">stray</a></li>\'\n'
                      '        word = "section" if len(items) == 1 else "sections"\n')),
    C("11a2", "weight-inflated", "one mark on the Atlas carries a word weight the apportionment did not give it",
      lambda t: _edit(t, BS, '% (p3(q["p"]), q.get("w", 0),', '% (p3(q["p"]), q.get("w", 0) + (1 if q is items[0] else 0),')),
    C("12", "corpus-line-off", "the corpus line's word total is one more than the three origins add to",
      lambda t: _edit(t, BS, 'TOTAL_WORDS = sum(p["words"] for p in P)\n', 'TOTAL_WORDS = sum(p["words"] for p in P) + 1\n')),
    C("13", "typed-numeral", "the build types a numeral into the footer that nothing computed",
      lambda t: _edit(t, BS, "<span>&copy; {TODAY.year} {esc(NAME)}</span>", "<span>&copy; {TODAY.year} {esc(NAME)}, 1,234 lines</span>")),
    C("14", "false-superlative", "a short essay's blurb calls it the largest essay on the site",
      lambda t: _json(t, "content/pieces.json", lambda d: _set_piece("blurb", next(x for x in d["pieces"] if x["slug"] == "heartbeat-budget")["blurb"] + " This is the largest essay on the site.", slug="heartbeat-budget")(d))),
    C("15", "result-sentence-added", "a piece gains a result sentence with a numeral that its record does not hold",
      lambda t: _before_body_end(t, PIECE_SMALL, "<p>The result is therefore 12,345, not 12,344.</p>")),
    C("16", "ledger-class-stale", "the ledger's class for a piece is not what the files show",
      lambda t: _json(t, "content/ledger.json", _ledger_class_flip)),
    C("17", "built-from-empty", "a listed piece has no built_from line",
      lambda t: _json(t, "content/pieces.json", _set_piece("built_from", "", index=0))),
    C("18", "font-digest-wrong", "a self-hosted font file no longer matches the digest its manifest records",
      lambda t: _json(t, "fonts/manifest.json", _font_sha_flip)),
    C("19", "heading-skips", "the footer's headings skip from h2 to h4",
      lambda t: _edit(t, BS, "<h2>Sections</h2>", "<h4>Sections</h4>", count=2)),
    C("20", "skip-link-gone", "the generated pages open without a skip link",
      lambda t: _edit(t, BS, '<a class="skip" href="#main">Skip to content</a>\n', "")),
    C("21", "figure-unnamed", "a lifted figure on the home and research pages loses its accessible name",
      lambda t: _json(t, "build/figures.json", _strip_figure_name)),
    C("22", "script-from-elsewhere", "every generated page loads a script from another origin",
      lambda t: _edit(t, BS, "</footer>\n", '<script src="https://cdn.elsewhere.invalid/x.js"></script>\n</footer>\n')),
    C("23", "dash-on-generated-page", "the footer of every generated page carries an em dash",
      lambda t: _edit(t, BS, "no framework, nothing external at runtime", "no framework — nothing external at runtime")),
    C("23", "dash-in-piece-prose", "a listed piece that is not a declared record carries an em dash in its prose",
      lambda t: _before_body_end(t, PIECE_SMALL, "<p>A dash — in the prose.</p>")),
    C("24", "idempotence-step-gone", "the workflow no longer fails the run when a further build rewrites something",
      lambda t: _edit(t, ".github/workflows/build.yml", '          grep -q "rewrote: nothing" /tmp/build-again.log\n', "")),
    C("24", "deploy-ungated", "the deploy job no longer waits for the build job",
      lambda t: _edit(t, ".github/workflows/build.yml", "    needs: build\n", "")),
    C("25", "american-spelling", "the footer of every generated page spells colour the American way",
      lambda t: _edit(t, BS, "no framework, nothing external at runtime", "no framework, no color scheme, nothing external at runtime")),
    C("26", "number-without-record", "the footer carries a counted number whose value no record holds",
      lambda t: _edit(t, BS, "<b>{md(TOTAL_FIGS, \"figures\")}</b> figures", "<b>{md(TOTAL_FIGS + 7, \"figures\")}</b> figures")),
    C("27", "channel-unnamed", "the home sphere declares a channel the Atlas key does not name",
      lambda t: _edit(t, "site.js", 'var CHANNELS = ["ind", "cou", "per", "too", "shr", "vis", "lnk", "dsc", "zon", "aut", "cor"];', 'var CHANNELS = ["ind", "cou", "per", "too", "shr", "vis", "lnk", "dsc", "zon", "aut", "cor", "halo"];')),
    C("28", "placed-by-lattice", "documents are spread over the sphere by the old even lattice instead of settled by their sections",
      lambda t: _edit(t, "build/atlas.py", '    cents = {p["slug"]: centroid_of(rule[p["slug"]]) for p in order}\n',
                      '    cents = dict(zip([p["slug"] for p in order], _fib_sphere(len(order))))\n')),
    C("28", "marks-off-the-spiral", "a document's sections leave the spiral: every ring is drawn twice as far out",
      lambda t: _edit(t, "build/atlas.py", '    rho = math.acos(max(-1.0, min(1.0, 1.0 - (1.0 - math.cos(radius)) * frac)))\n',
                      '    rho = 2.0 * math.acos(max(-1.0, min(1.0, 1.0 - (1.0 - math.cos(radius)) * frac)))\n')),
    C("28", "discs-left-overlapping", "the discs are never settled apart, so documents overlap where their starting heights put them",
      lambda t: _edit(t, "build/atlas.py", "SETTLE_STEPS = 800\n", "SETTLE_STEPS = 0\n")),
    C("28", "discs-drawn-too-large", "every disc is drawn at the whole of its share rather than two thirds of it",
      lambda t: _edit(t, "build/atlas.py", "DISC_AREA = 2.0 / 3.0\n", "DISC_AREA = 1.0\n")),
    # one page's record is made stale first, so the case bites whatever the
    # last audit left: run against a record that was current on every page,
    # the glyph change alone had nothing to draw wrongly and was missed
    C("29", "stale-drawn-as-held", "the instrument draws a page whose record is stale as held",
      lambda t: (_json(t, "content/audit.json", lambda d: d["pages"]["404.html"].update({"inputs": "000000stale0"})),
                 _edit(t, "build/claims.py", 'GLYPH = {"held": "#", "failed": "x", "stale": "?", "declared": "~", "none": ""}',
                       'GLYPH = {"held": "#", "failed": "x", "stale": "#", "declared": "~", "none": ""}'))),
    C("30", "colour-unnamed", "a lifted figure's colour loses its declared meaning",
      lambda t: _json(t, "build/figures.json", lambda d: d["fs-wlc"]["meanings"].pop("--outside"))),
    C("31", "numbers-not-restated", "the lifted figures no longer restate the numbers they draw",
      lambda t: _edit(t, BS, "          {figure_restated(fid, href)}\n", "")),
    C("32", "author-unplaced", "the author is left off the sphere: no entry, no zone, no anchor",
      lambda t: _edit(t, "build/atlas.py", "    if AUTHOR:\n", "    if AUTHOR and False:\n")),
    C("32", "author-card-inflated", "the author's card claims seven words more than the featured pieces hold",
      lambda t: _edit(t, BS, "{f['words']:,} words, {f['figures']} figures", "{f['words'] + 7:,} words, {f['figures']} figures")),
    # the editor: hand-maintained, never the build's to write, held whole
    C("33", "asset-missing", "the editor links a stylesheet that does not exist",
      lambda t: _edit(t, "admin.html", 'href="site.css"', 'href="site-editor.css"')),
    C("33", "editor-overwritten", "the build writes the editor as if it were a generated page",
      lambda t: _edit(t, BS, '             "404.html": page_404(),\n', '             "404.html": page_404(), "admin.html": page_404(),\n')),
    C("33", "token-undefined", "the editor reads a custom property no stylesheet it loads defines",
      lambda t: _regex(t, "admin.html", r"var\(--edge\)", "var(--edge-2)")),
    C("33", "id-missing", "the editor's script asks for an element its markup no longer carries",
      lambda t: _edit(t, "admin.html", 'id="save-setup"', 'id="save-setup-2"')),
    C("33", "script-broken", "a syntax error in the editor's script",
      lambda t: _edit(t, "admin.html", '"use strict";\n', '"use strict";\nthis is not javascript;\n')),
    C("33", "worker-stores-the-editor", "the worker the build writes stores the editor like any other page",
      lambda t: _edit(t, BS, 'const NEVER_STORED = ["admin.html"];', 'const NEVER_STORED = [];')),
    C("33", "truncated", "the editor's file ends before its markup does",
      lambda t: _edit(t, "admin.html", "</script>\n</body>\n</html>\n", "</script>\n")),
    # the marks: geometry the files do not carry, a stroke too thin to hold an
    # edge at the size it is drawn, and a source file that is not there
    C("34", "mark-element-invented", "the pages draw a line the mark's file does not carry",
      lambda t: _edit(t, "build/marks.py", '    return "".join(parts)\n\nMONO_PRIMARY',
                      '    return "".join(parts) + \'<path d="M2 2 L62 62" stroke-width="1"/>\'\n\nMONO_PRIMARY')),
    C("34", "mark-stroke-unscaled", "the tab icon is drawn at the authored stroke, which cannot hold an edge at that size",
      lambda t: _edit(t, "build/marks.py", '"keep": ("A#1", "A#2", "R leg#1"), "scale": 3.3, "px": 16',
                      '"keep": ("A#1", "A#2", "R leg#1"), "scale": 1.0, "px": 16')),
    C("34", "mark-source-missing", "a mark's source file is gone, so what the pages draw answers to nothing",
      lambda t: os.remove(os.path.join(t, "content", "marks", "02_forensic_audit_delta.svg"))),
    C("34", "inspection-unscaled", "the header's construction layer is drawn at the letters' factor, which cannot hold an edge at 24px",
      lambda t: _edit(t, "build/marks.py", '"inspect": {"keep": MONO_CONSTRUCTION, "scale": 3.6}',
                      '"inspect": {"keep": MONO_CONSTRUCTION, "scale": 2.2}')),

    C("35", "glyph-element-invented", "a glyph is drawn with a line its file does not carry",
      lambda t: _edit(t, "build/marks.py", '    return "".join(parts)\n\n\ndef glyph_svg',
                      '    return "".join(parts) + \'<path d="M1 1 L23 23"/>\'\n\n\ndef glyph_svg')),
    C("35", "glyph-drawn-too-small", "a glyph is drawn at a size its authored stroke cannot hold",
      lambda t: _edit(t, "build/marks.py", 'GLYPH_SIZES = {"head": 20, "band": 24}',
                      'GLYPH_SIZES = {"head": 18, "band": 24}')),
    C("35", "glyph-source-missing", "a glyph's source file is gone, so the column head answers to nothing",
      lambda t: os.remove(os.path.join(t, "content", "marks", "glyphs", "04_tested.svg"))),
    C("35", "seal-keeps-the-ring-it-cannot-hold", "the seal draws the ring whose stroke is under a device pixel at every size",
      lambda t: _edit(t, "build/marks.py", "SEAL_DROP = 0.5", "SEAL_DROP = 0.0")),
    C("35", "figure-of-another-document", "every statement row draws the first piece's figure instead of its own",
      lambda t: _edit(t, "build/build_site.py",
                      'return fingerprint.svg(p["words"], p["figures"], p["tables"], link_degree(p["slug"]))',
                      'return fingerprint.svg(P[0]["words"], P[0]["figures"], P[0]["tables"], link_degree(P[0]["slug"]))')),
    C("35", "figure-resized-by-the-stylesheet", "the stylesheet draws the figure at a size its stroke rule was not computed for",
      lambda t: _edit(t, "site.css", ".fp{flex:none;display:block;", ".fp{width:40px;flex:none;display:block;")),

    C("36", "ink-under-the-floor", "the faintest ink in Obsidian is set to a value that measures under 4.5:1 on the paper it stands on",
      lambda t: _edit(t, "site.css", "--ink-3:       #8f929a;", "--ink-3:       #7a7a74;", 2)),
    C("36", "light-strong-enough-to-matter", "the reading light behind the hero is turned up until it takes the text under the floor",
      lambda t: _edit(t, "site.css", "--lamp-warm:   rgba(219,171,93,.05);", "--lamp-warm:   rgba(219,171,93,.5);", 2)),

    C("36", "dark-palettes-disagree", "the dark ground the browser asks for and the dark ground the button sets stop agreeing",
      lambda t: _edit(t, "site.css", "    --panel-2:     #1c1d22;", "    --panel-2:     #2a2b33;")),

    C("37", "header-without-scope", "a generated table header no longer says which cells it heads",
      lambda t: _edit(t, "build/build_site.py", '''<thead><tr><th scope="col">Piece</th>''' + "'",
                      '''<thead><tr><th>Piece</th>''' + "'")),
]


# ------------------------------------------------------------- running --
def _copy_tree(dst):
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", ".pytest_cache"))


def run_case(case, keep=False):
    tmp = tempfile.mkdtemp(prefix="neg-")
    tree = os.path.join(tmp, "site")
    t0 = time.time()
    rec = {"id": case["id"], "check": case["check"], "what": case["what"]}
    try:
        _copy_tree(tree)
        case["mutate"](tree)
        r = subprocess.run([sys.executable, os.path.join(tree, "build", "build_site.py")], cwd=tree,
                           capture_output=True, text=True, timeout=900)
        out = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"^checks that failed: (.*)$", out, re.M)
        fired = [x.strip() for x in m.group(1).split(",")] if m else []
        line = next((ln.strip() for ln in out.splitlines() if ln.strip().startswith("check %s:" % case["check"])), "")
        rec.update({"exit": r.returncode, "fired": fired, "caught": r.returncode != 0 and case["check"] in fired,
                    "line": line[:240]})
        if r.returncode != 0 and not fired:
            # the build fell over before its checks ran: a refusal, not a catch
            tail = [ln for ln in out.strip().splitlines() if ln.strip()][-1:]
            rec["line"] = ("the build stopped before its checks: " + " ".join(tail))[:240]
    except Falsifier as e:
        rec.update({"exit": None, "fired": [], "caught": False, "line": "the falsification could not be applied: %s" % e})
    except subprocess.TimeoutExpired:
        rec.update({"exit": None, "fired": [], "caught": False, "line": "the build did not finish in 900 s"})
    finally:
        rec["seconds"] = round(time.time() - t0, 1)
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            rec["kept"] = tree
    return rec


def load():
    try:
        return json.load(open(OUT_PATH, encoding="utf-8"))
    except Exception:
        return {}


def git_short():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def main(argv):
    if "--list" in argv:
        for c in CASES:
            print("%-6s %-28s %s" % (c["check"], c["id"], c["what"]))
        return 0
    digest = code_digest()
    rec = load()
    build = rec.get("build") or {}
    have = {c["id"]: c for c in (build.get("cases") or [])}
    current = (build.get("meta") or {}).get("code") == digest
    if "--stale" in argv:
        missing = [c["id"] for c in CASES if c["id"] not in have]
        print(json.dumps({"stale": (not current) or bool(missing), "code": digest,
                          "recorded": (build.get("meta") or {}).get("code"), "missing": missing}))
        return 0
    only = None
    if "--only" in argv:
        only = set(argv[argv.index("--only") + 1].split(","))
    jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else 3
    keep = "--keep" in argv
    todo = [c for c in CASES if (only and (c["check"] in only or c["id"] in only))
            or (not only and ("--all" in argv or not current or c["id"] not in have))]
    if not todo:
        print("negatives: the record is current for this code (%s); %d cases" % (digest, len(have)))
        return 0
    print("negatives: running %d of %d cases with %d jobs (code %s)" % (len(todo), len(CASES), jobs, digest))
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = {ex.submit(run_case, c, keep): c for c in todo}
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            results[r["id"]] = r
            print("  %-6s %-28s %s  %5.1fs  %s" % (r["check"], r["id"], "caught" if r["caught"] else "MISSED",
                                                  r["seconds"], r["line"][:110]))
    if not current or "--all" in argv:
        have = {}   # a record for other code is not carried forward
    have.update(results)
    cases = [have[c["id"]] for c in CASES if c["id"] in have]
    out = {
        "note": ("Written by build/negatives.py: for each check, a falsification applied to a copy of "
                 "the tree and the build's answer. A claim is held only while a current, caught "
                 "falsification stands behind every check it cites."),
        "build": {"meta": {"tool": "build/negatives.py", "date": datetime.date.today().isoformat(),
                           "commit": git_short(), "code": digest, "code_files": BUILD_CODE},
                  "cases": cases},
        "runtime": rec.get("runtime") or None,
    }
    json.dump(out, open(OUT_PATH, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(OUT_PATH, "a", encoding="utf-8").write("\n")
    caught = sum(1 for c in cases if c["caught"])
    print("negatives: %d of %d falsifications caught; record written to content/negatives.json" % (caught, len(cases)))
    return 0 if caught == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
