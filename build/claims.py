# -*- coding: utf-8 -*-
"""The register of the site's claims about itself, and the instrument that
draws it.

Every sentence the generated pages say about the site is listed here beside
the check that tests it. A claim with a check prints the check's last
result with its denominator: so many links of so many, on so many pages.
A claim with no check prints the word "asserted" where a result would be.
A claim measured in a browser prints "not yet measured for this build" when
the record in content/audit.json is older than the pages it describes.

A check that has never been observed to fail is not evidence that it
operates, so a claim prints "held" only while a current, caught
falsification stands behind every check it cites (content/negatives.json,
written by build/negatives.py and build/audit.js --falsify); with no
falsification on record, or one the check missed, or one recorded against
other code, it prints "untested". The build refuses to publish when a
checked claim fails; the workflow deploys only what the build passed.

The controls page draws the same records as glyphs: one line per page, one
column per check that looks at pages, one glyph per (page, check) the check
covered; and one line per check with a glyph per falsification. Every glyph
is a record, and check 29 reads the rendered page back against the records.
"""
import datetime, hashlib, json, os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_PATH = os.path.join(ROOT, "content", "audit.json")
NEG_PATH = os.path.join(ROOT, "content", "negatives.json")
DECL_PATH = os.path.join(ROOT, "content", "declared.json")
# The pages the build generates. build/build_site.py takes SHELL_PAGES from
# this list rather than keeping its own: the two drifted apart the moment a
# page was added to one of them, and a page missing from this copy is a page
# the audit never opens and the register never grades.
SHELL = ["index.html", "research.html", "coursework.html", "tools.html",
         "selected.html", "library.html", "atlas.html", "about.html",
         "colophon.html", "controls.html", "404.html"]
# the pages the register measures that are neither generated nor pieces: the
# editor, hand-maintained, measured on its own terms under the editor row
AUX = ["admin.html"]
# the code a runtime falsification exercises: the audit, this module's
# aggregators, what the pages run, and the editor's page (its falsifications
# edit it); the worker is read with its per-build constants removed
RUNTIME_CODE = ["build/audit.js", "build/claims.py", "site.js", "site.css", "atlas.js", "admin.html"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def n(x):
    return format(x, ",") if isinstance(x, int) else str(x)


def _load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def load_audit():
    return _load(AUDIT_PATH, {})


def load_negatives():
    return _load(NEG_PATH, {})


def declared():
    return _load(DECL_PATH, {})


def git_short():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


# ----------------------------------------------------------- the audit --
# What a browser measured, per page, with the fingerprint of the inputs it
# measured. A page whose inputs moved since is unmeasured for this build.

def page_input_digest(out_dir, name, shell):
    """The inputs a runtime measurement of a page depends on. A piece is
    self-contained, so its own file as rendered, the build's blocks included.
    A generated page is a function of its sources, so the text of the page
    with what prints the records removed (the register, the instrument and
    the lines under them print the audit, and a measurement must not go
    stale because its own result was printed), plus the stylesheet and the
    scripts it loads."""
    path = os.path.join(out_dir, name)
    if not os.path.exists(path):
        return None
    raw = open(path, encoding="utf-8", errors="ignore").read()
    h = hashlib.sha1()
    if shell:
        raw = re.sub(r'<section[^>]*id="claims".*?</section>', "", raw, flags=re.S)
        raw = re.sub(r'<section[^>]*id="register".*?</section>', "", raw, flags=re.S)
        raw = re.sub(r'<section[^>]*id="instrument".*?</section>', "", raw, flags=re.S)
        raw = re.sub(r'<p class="audit-line">.*?</p>', "", raw, flags=re.S)
        raw = re.sub(r'<p class="register-line">.*?</p>', "", raw, flags=re.S)
        raw = re.sub(r'\?v=[0-9a-f]{8}', "", raw)
        h.update(raw.encode("utf-8"))
        for dep in ("site.css", "site.js", "atlas.js", "figures.css"):
            dp = os.path.join(out_dir, dep)
            if os.path.exists(dp):
                h.update(open(dp, "rb").read())
    elif name in AUX:
        # the editor loads the site's stylesheet and nothing else of the site's
        h.update(raw.encode("utf-8"))
        dp = os.path.join(out_dir, "site.css")
        if os.path.exists(dp):
            h.update(open(dp, "rb").read())
    else:
        raw = re.sub(r"\?v=[0-9a-f]{8}", "", raw)
        h.update(raw.encode("utf-8"))
    return h.hexdigest()[:12]


def sw_input_digest(out_dir):
    """The worker's behaviour, with its per-build constants removed."""
    path = os.path.join(out_dir, "sw.js")
    if not os.path.exists(path):
        return None
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r'const (VERSION|PAGES)\s*=\s*"[^"]*";', r'const \1 = "";', raw)
    raw = re.sub(r"const FILES\s*=\s*\[.*?\];", "const FILES = [];", raw, flags=re.S)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def runtime_code_digest(out_dir=ROOT):
    h = hashlib.sha1()
    for f in RUNTIME_CODE:
        p = os.path.join(out_dir, f)
        if os.path.exists(p):
            h.update(f.encode()); h.update(open(p, "rb").read())
    h.update((sw_input_digest(out_dir) or "").encode())
    return h.hexdigest()[:12]


def audit_state(out_dir, shell_pages, all_pages):
    """Per measurement, which pages the record covers for this build."""
    audit = load_audit()
    pages = audit.get("pages") or {}
    fresh, stale = {}, {}
    for name in all_pages:
        want = page_input_digest(out_dir, name, name in shell_pages)
        rec = pages.get(name)
        if rec and want and rec.get("inputs") == want:
            fresh[name] = rec
        else:
            stale[name] = rec
    off = audit.get("offline") or {}
    off_fresh = bool(off) and off.get("inputs") == sw_input_digest(out_dir)
    return {"audit": audit, "fresh": fresh, "stale": stale,
            "offline": off if off_fresh else None, "offline_stale": off if (off and not off_fresh) else None}


# ------------------------------------------------- the runtime aggregators --
# One place for the rule each runtime row applies to a page's record, so the
# row, the instrument's glyph and the falsification are graded the same way.

def page_ok(key, rec, declared_overflow=()):
    """Whether one page's record holds the claim for this key, or None when
    the record has no measurement for it."""
    r = rec.get(key) if rec else None
    if r is None:
        return None
    if key == "ext":
        return r.get("external", 0) == 0
    if key == "idle":
        return r.get("frames", 0) == 0
    if key == "keyboard":
        return r.get("noRing", 0) == 0
    if key == "print":
        return r.get("stickyLeft", 0) == 0 and r.get("hidden", 0) == 0 and r.get("figuresBreakable", 0) == 0
    if key == "motion":
        return r.get("animations", 0) == 0
    if key == "fit":
        return not r.get("overflow")
    if key == "chrome":
        return r.get("a") == r.get("b")
    if key == "descent":
        shapes = [r.get("wide") or {}, r.get("phone") or {}]
        return all(sh.get("rows", 0) > 0 and sh.get("faced", -1) == sh.get("rows") and sh.get("framesAfter", 1) == 0
                   and sh.get("framesAtTop", 1) == 0 for sh in shapes)
    if key == "corona":
        shapes = [r.get("wide") or {}, r.get("phone") or {}]
        return all(sh.get("rows", 0) > 0 and sh.get("matched", -1) == sh.get("rows") and sh.get("atTop") == "none" for sh in shapes)
    if key == "theme":
        return (r.get("options") == 2 and r.get("pressed") == 1 and bool(r.get("pulsed")) and bool(r.get("pulseEnded"))
                and not r.get("repeated", True) and bool(r.get("switched")) and r.get("framesAfterSwitch", 1) == 0 and bool(r.get("focusRing")))
    if key == "inspect":
        # two layers; nothing showing at rest; full under a pointer and under a
        # keyboard focus; a transition inside the 260 ms cap and none at all for
        # a reader who asked for no motion; the box unmoved; nothing scheduled
        # after it settles
        return (r.get("layers") == 2 and r.get("rest") == 0 and r.get("hover") == 1
                and r.get("focus") == 1 and 0 < r.get("ms", 0) <= 260
                and r.get("reducedMs", -1) == 0 and r.get("moved", 1) == 0
                and r.get("framesAfter", 1) == 0)
    if key == "admin":
        return (r.get("errors", 1) == 0 and r.get("failed", 1) == 0 and r.get("external", 1) == 0 and r.get("idleFrames", 1) == 0
                and r.get("tabs", 0) > 0 and r.get("switched", -1) == r.get("tabs") and r.get("threwUnconnected", 1) == 0
                and bool(r.get("themeSwitched")) and bool(r.get("themeStored"))
                and bool(r.get("cfgSaved")) and bool(r.get("tokenInSession")) and not r.get("tokenInLocal", True)
                and r.get("pieces", 0) > 0 and r.get("rows", -1) == r.get("pieces") and r.get("searched", -1) == r.get("searchExpected", -2)
                and bool(r.get("editorOpened")) and bool(r.get("editEnabledPublish")) and bool(r.get("promptShown"))
                and bool(r.get("forgotten")) and bool(r.get("guardHeld"))
                and r.get("files", 0) > 0 and r.get("files", -1) == r.get("filesExpected", -2) and r.get("siteFields", 0) > 0
                and r.get("writes", 1) == 0 and not r.get("overflow", True))
    return None


def runtime_pages(key, shell, allp, aux=()):
    """The pages one runtime claim is made about: said once, here, and read
    by the register's rows, the wall and check 29."""
    shell = list(shell)
    if key in ("keyboard", "print", "motion", "theme", "inspect"):
        return shell
    if key == "chrome":
        return [p for p in allp if p not in shell]
    if key in ("descent", "corona"):
        return ["index.html"]
    if key == "admin":
        return list(aux)
    return list(allp)


def _runtime(state, key, pages):
    recs = [(p, state["fresh"][p]) for p in pages if p in state["fresh"] and state["fresh"][p].get(key) is not None]
    missing = [p for p in pages if p not in {r[0] for r in recs}]
    return recs, missing


def agg(key, recs, names, declared_overflow=()):
    """(text, ok) for a set of page records under one runtime claim."""
    rs = [r.get(key) or {} for r in recs]
    if key == "ext":
        req = sum(r.get("requests", 0) for r in rs); ext = sum(r.get("external", 0) for r in rs)
        return (f"{n(req)} requests on {len(rs)} pages, {ext} to another origin", ext == 0)
    if key == "idle":
        fr = sum(r.get("frames", 0) for r in rs)
        return (f"{fr} frames requested in the second after load, over {len(rs)} pages", fr == 0)
    if key == "keyboard":
        st = sum(r.get("stops", 0) for r in rs); bad = sum(r.get("noRing", 0) for r in rs)
        return (f"{n(st)} Tab stops on {len(rs)} pages, {bad} without a visible ring", bad == 0)
    if key == "print":
        sticky = sum(r.get("stickyLeft", 0) for r in rs); hidden = sum(r.get("hidden", 0) for r in rs)
        figs = sum(r.get("figures", 0) for r in rs); nobreak = sum(r.get("figuresBreakable", 0) for r in rs)
        return (f"{len(rs)} pages under print media: {sticky} sticky elements left pinned, {hidden} blocks left hidden, "
                f"{nobreak} of {figs} figures allowed to break", sticky == 0 and hidden == 0 and nobreak == 0)
    if key == "motion":
        an = sum(r.get("animations", 0) for r in rs)
        return (f"{an} animations running under reduced motion, over {len(rs)} pages", an == 0)
    if key == "fit":
        over = {nm for nm, r in zip(names, rs) if r.get("overflow")}
        decl = set(declared_overflow)
        undeclared = sorted(over - decl); stale = sorted((decl & set(names)) - over)
        text = f"{len(rs) - len(over)} of {len(rs)} pages fit a 320px viewport; {len(decl)} declared exceptions"
        if undeclared:
            text += "; wider and not declared: " + ", ".join(undeclared)
        if stale:
            text += "; declared but fitting now: " + ", ".join(stale)
        return (text, not undeclared and not stale)
    if key == "chrome":
        bad = [nm for nm, r in zip(names, rs) if r and r.get("a") != r.get("b")]
        return (f"{len(rs) - len(bad)} of {len(rs)} pages count the same words with and without the build's own blocks removed"
                + ("; " + ", ".join(bad) if bad else ""), not bad)
    if key == "descent":
        r = rs[0] if rs else {}
        w, ph = r.get("wide") or {}, r.get("phone") or {}
        ok = page_ok("descent", {"descent": r})
        return (f"{w.get('faced', 0)} of {w.get('rows', 0)} featured rows faced at 1440 and {ph.get('faced', 0)} of {ph.get('rows', 0)} at 390; "
                f"{w.get('framesSettle', 0) + ph.get('framesSettle', 0)} frames while the spring settled (within 700ms of each stop), "
                f"{w.get('framesAfter', 0) + ph.get('framesAfter', 0)} in the second after that, "
                f"{w.get('framesAtTop', 0) + ph.get('framesAtTop', 0)} at the top", bool(ok))
    if key == "corona":
        r = rs[0] if rs else {}
        w, ph = r.get("wide") or {}, r.get("phone") or {}
        ok = page_ok("corona", {"corona": r})
        return (f"{w.get('matched', 0)} of {w.get('rows', 0)} stops at 1440 and {ph.get('matched', 0)} of {ph.get('rows', 0)} at 390 show the faced row's recorded origin; "
                f"at the top the corona names {w.get('atTop')!s} and {ph.get('atTop')!s}", bool(ok))
    if key == "theme":
        two = sum(1 for r in rs if r.get("options") == 2 and r.get("pressed") == 1)
        pulsed = sum(1 for r in rs if r.get("pulsed") and r.get("pulseEnded"))
        rep = sum(1 for r in rs if r.get("repeated"))
        sw = sum(1 for r in rs if r.get("switched"))
        fr = sum(max(0, r.get("framesAfterSwitch", 0)) for r in rs)
        ring = sum(1 for r in rs if r.get("focusRing"))
        return (f"{two} of {len(rs)} pages show two named states with one pressed; the first visit pulsed once and the pulse ended on {pulsed}, "
                f"and repeated on a second visit on {rep}; the switch changed the theme on {sw}, with {fr} frames requested in the second after settling; "
                f"a focus ring on the offer from the keyboard on {ring}",
                two == len(rs) and pulsed == len(rs) and rep == 0 and sw == len(rs) and fr == 0 and ring == len(rs))
    if key == "inspect":
        two = sum(1 for r in rs if r.get("layers") == 2)
        rest = sum(1 for r in rs if r.get("rest") == 0)
        hov = sum(1 for r in rs if r.get("hover") == 1)
        foc = sum(1 for r in rs if r.get("focus") == 1)
        cap = sum(1 for r in rs if 0 < r.get("ms", 0) <= 260)
        red = sum(1 for r in rs if r.get("reducedMs", -1) == 0)
        mv = sum(1 for r in rs if r.get("moved", 1) != 0)
        fr = sum(max(0, r.get("framesAfter", 0)) for r in rs)
        ms = sorted({r.get("ms", -1) for r in rs})
        return (f"on {len(rs)} pages the header mark carries two layers on {two}, draws nothing of the construction at rest on {rest}, "
                f"draws all of it under a pointer on {hov} and under a keyboard focus on {foc}; the transition measures "
                + ", ".join("%d ms" % m for m in ms) + f" and is inside the 260 ms cap on {cap}, and is removed entirely under reduced motion on {red}; "
                f"the brand's box moved on {mv}, and {fr} frames were requested in the second after it settled",
                two == len(rs) and rest == len(rs) and hov == len(rs) and foc == len(rs)
                and cap == len(rs) and red == len(rs) and mv == 0 and fr == 0)
    if key == "admin":
        r = rs[0] if rs else {}
        ok = page_ok("admin", {"admin": r})
        kept = bool(r.get("cfgSaved")) and bool(r.get("tokenInSession")) and not r.get("tokenInLocal", True)
        return (f"served from this tree with no connection saved: {r.get('errors', 0)} console errors or uncaught exceptions, "
                f"{r.get('failed', 0)} failed requests, {r.get('external', 0)} requests to another origin, {r.get('idleFrames', 0)} idle frames; "
                f"{r.get('switched', 0)} of {r.get('tabs', 0)} tabs switched and the search answered before a connection, {r.get('threwUnconnected', 0)} exceptions; "
                f"the theme button {'switched the theme and it was remembered' if r.get('themeSwitched') and r.get('themeStored') else 'did not switch the theme'}; "
                f"the connection form kept the repository in this browser and the token in this tab only: {'yes' if kept else 'no'}; "
                f"connected through a stub of GitHub: {r.get('rows', 0)} of {r.get('pieces', 0)} recorded pieces listed, "
                f"a search matched {r.get('searched', 0)} of {r.get('searchExpected', 0)}, "
                f"the editor {'opened on the first piece' if r.get('editorOpened') else 'did not open'}, "
                f"an edit {'marked it and enabled Publish' if r.get('editEnabledPublish') else 'did not enable Publish'}, "
                f"Publish {'asked for a note' if r.get('promptShown') else 'asked for nothing'}, "
                f"forgetting the token {'disabled Publish' if r.get('forgotten') else 'did not disable Publish'}, "
                f"and without a token Publish {'stopped at the Connection tab' if r.get('guardHeld') else 'did not stop'}; "
                f"{r.get('files', 0)} of {r.get('filesExpected', 0)} files listed, {r.get('siteFields', 0)} site text fields; "
                f"{r.get('writes', 0)} writes attempted; {r.get('scrollWidth', 0)}px wide at 320px", bool(ok))
    return ("", False)


def offline_ok(off):
    ed = (off or {}).get("editor") or {}
    return (bool(off) and off.get("before", 0) > 0 and off.get("after", 0) >= off.get("before", 0) and off.get("refreshed") is True
            and ed.get("stored") is False and ed.get("fresh") is True)


# ----------------------------------------------------------- negatives --

def negatives_state(out_dir=ROOT):
    """The falsifications on record, by check id and by runtime key, each
    marked current or recorded against other code."""
    neg = load_negatives()
    out = {"build": {}, "runtime": {}, "build_meta": {}, "runtime_meta": {}}
    b = neg.get("build") or {}
    out["build_meta"] = b.get("meta") or {}
    bcode = _build_code_digest(out_dir)
    bcur = out["build_meta"].get("code") == bcode
    for c in b.get("cases") or []:
        out["build"].setdefault(c["check"], []).append(dict(c, current=bcur))
    r = neg.get("runtime") or {}
    out["runtime_meta"] = r.get("meta") or {}
    rcur = out["runtime_meta"].get("code") == runtime_code_digest(out_dir)
    for c in r.get("cases") or []:
        rec = c.get("rec") or {}
        if c["key"] == "offline":
            caught = not offline_ok(rec)
        else:
            ok = page_ok(c["key"], rec, declared().get("overflow") or [])
            caught = ok is False
        out["runtime"].setdefault(c["key"], []).append(dict(c, caught=caught, current=rcur))
    return out


def _build_code_digest(out_dir):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("negatives", os.path.join(out_dir, "build", "negatives.py"))
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod.code_digest()
    except Exception:
        return None


def _when_false(cases):
    """The negatives column for a row: (text, status_gate) where the gate is
    None when the row may be held, or the reason it is untested."""
    if not cases:
        return ("no falsification on record", "no falsification on record")
    stale = [c for c in cases if not c.get("current")]
    caught = [c for c in cases if c.get("caught")]
    missed = [c for c in cases if not c.get("caught")]
    text = f"caught {len(caught)} of {len(cases)}: " + "; ".join(c["what"] for c in cases)
    if stale:
        return (text + " (recorded against other code)", "falsified against other code")
    if missed:
        return (text, f"{len(missed)} of {len(cases)} falsifications missed")
    return (text, None)


# --------------------------------------------------------- the register --

def _row(claim, by, checks, result, status, where=None, note=None, when=None, key=None):
    return {"claim": claim, "by": by, "checks": checks, "result": result, "status": status,
            "where": where or [], "note": note, "when": when, "key": key}


def build(ctx):
    """ctx: tally, records, shell_pages, all_pages, audit (state), negatives
    (state), fired (check ids whose problems exist), problems (appended
    to). Returns the rows and a summary."""
    T = ctx["tally"]
    state = ctx["audit"]
    neg = ctx["negatives"]
    fired = set(ctx.get("fired") or ())
    shell = ctx["shell_pages"]
    allp = ctx["all_pages"]
    aux = ctx.get("aux_pages") or []
    decl = declared()
    rows = []

    def checked(claim, checks, result, where=None, note=None):
        by = ("check " if len(checks) == 1 else "checks ") + ", ".join(checks)
        cases = [c for cid in checks for c in neg["build"].get(cid, [])]
        when, gate = _when_false(cases)
        if any(c in fired for c in checks):
            status = "failed"
        elif gate:
            status, note = "untested", (note + " " if note else "") + gate.capitalize() + "."
        else:
            status = "held"
        rows.append(_row(claim, by, checks, result, status, where, note, when))

    def asserted(claim, where=None, note=None):
        rows.append(_row(claim, "nothing yet", [], "asserted", "asserted", where, note, None))

    # --- checked by the build, on every publish ---
    t = T.get("numerals", {})
    checked("Every number on the generated pages is one the build computed or a piece states in its own text; "
            "the numbers on this page are held to the checks' own tallies.",
            ["13"], f"{n(t.get('n', 0))} numerals on {t.get('pages', 0)} pages, 0 typed. Not scanned: the Atlas index and the last pass's notes, which are quoted records",
            ["controls.html", "index.html"])
    t1, t3, t4, t9 = T.get("canonicals", {}), T.get("links", {}), T.get("icons", {}), T.get("listed", {})
    checked("Every link, canonical address, manifest icon and listed file resolves to a file that exists.",
            ["1", "3", "4", "9"],
            f"{n(t3.get('n', 0))} links on {t3.get('pages', 0)} pages, {n(t1.get('n', 0))} canonicals, {t4.get('n', 0)} icons, {t9.get('n', 0)} listed files, 0 unresolved",
            ["colophon.html"])
    t = T.get("hosts", {})
    checked("No page names an address other than this site's.", ["2"], f"{t.get('pages', 0)} pages, 0 other hosts", ["colophon.html"],
            note="A piece that names a stale address is corrected by the build before this check runs, so the check can fail only on a generated page.")
    t = T.get("external", {})
    checked("Nothing on any page is loaded from another origin, except the typefaces the exceptions name.", ["22"],
            f"{n(t.get('refs', 0))} references on {t.get('pages', 0)} pages, {t.get('allowed', 0)} to the named typefaces, 0 others; {t.get('cookie', 0)} uses of the cookie API",
            ["colophon.html", "index.html"])
    t = T.get("invariance", {})
    checked("Nothing a piece claims has moved since its record was written: not a numeral, a reference, a label, an anchor or a result sentence.",
            ["15"], f"{t.get('held', 0)} of {t.get('checked', 0)} records hold ({t.get('listed', 0)} listed pieces and {t.get('transcripts', 0)} transcripts); {t.get('declared', 0)} carry declared changes",
            ["colophon.html"])
    t = T.get("origins", {})
    checked("The three origins add to the corpus line in pieces, words, figures and tables.", ["12"], f"{t.get('keys', 0)} totals, 0 that disagree", ["index.html", "colophon.html"])
    t8, ta = T.get("atlas_marks", {}), T.get("placement", {})
    checked("Every mark on the Atlas opens a passage that exists, and the marks drawn are the marks the placement produced.", ["8", "11a"],
            f"{n(t8.get('n', 0))} marks into {t8.get('files', 0)} documents, 0 dead; {n(ta.get('marks', 0))} on the Atlas and {n(ta.get('teaser', 0))} on the home sphere read back against the placement, 0 stray",
            ["atlas.html", "index.html"])
    t = T.get("weights", {})
    checked("The marks' apportioned word weights add back to the corpus line.", ["11a2"], f"{n(t.get('marks', 0))} weights sum to {n(t.get('sum', 0))}", ["atlas.html"])
    t = T.get("position", {})
    checked("Where a document sits on the sphere is a rule: each origin's zone of latitude has the area of its share of the sections, each document is a disc of two thirds of its share's area, settled clear of every other inside its zone, and its own sections lie on an equal-area spiral inside the disc, the first at the centre.", ["28"],
            f"{t.get('documents', 0)} documents in {t.get('zones', 0)} zones; {t.get('read_back', 0)} centres and radii read back from {t.get('pages', 0)} pages against the rule, 0 out of place; {t.get('overlap', 0)} of {n(t.get('pairs', 0))} disc pairs overlap; {n(t.get('marks', 0))} marks held at their spiral positions and inside their discs, {t.get('off', 0)} off, {t.get('outside', 0)} outside; {t.get('shared', 0)} shared marks placed between their owners",
            ["atlas.html", "index.html"])
    t = T.get("author", {})
    checked("The author is an entry in the section register, placed by the rule every document follows: one mark in an origin of his own, in a zone of latitude with the area of its share, linking to the passage that names him; his card is the recorded standing, the recorded co-op term counted from the build's date, and the featured pieces' subtotal, and the pages carry the build's own arithmetic. The Now block on the about page is held to the same two values.", ["32"],
            f"{t.get('marks', 0)} mark of {n(t.get('total', 0))}, zone {t.get('zone') or 'none'} of {t.get('share', 0.0):.3%} of the sphere, linked to {t.get('link') or 'nothing'}; the card read back from {t.get('cards', 0)} pages, {t.get('off', 0)} off: {t.get('card') or ''}",
            ["atlas.html", "index.html", "about.html"])
    t = T.get("channels", {})
    checked("Every visual channel either sphere draws is named in the Atlas key, and every entry in the key is drawn.", ["27"],
            f"{t.get('declared', 0)} channels declared by {t.get('scripts', 0)} scripts, {t.get('key', 0)} key entries, {t.get('unnamed', 0)} unnamed, {t.get('stray', 0)} stray",
            ["atlas.html", "index.html"])
    t10, t18 = T.get("subset", {}), T.get("fonts", {})
    checked("Every character the pages show that Inter can render is in the self-hosted subset, and every other self-hosted face carries its piece's characters.",
            ["10", "18"], f"{n(t10.get('chars', 0))} distinct characters on {t10.get('pages', 0)} pages against the subset; {t18.get('files', 0)} other subsets held to their manifest and digest",
            ["colophon.html"])
    t = T.get("chrome", {})
    checked("The chrome the build writes into a piece uses only colours the stylesheet knows.", ["11"], f"{t.get('n', 0)} colours, 0 unknown", ["colophon.html"])
    t = T.get("ledger", {})
    checked("The ledger's class for every piece (untouched, styling, copy, new) is what the files show.", ["16"], f"{t.get('n', 0)} pieces recomputed, 0 stale", ["colophon.html"])
    t = T.get("built_from", {})
    checked("Every listed piece states what it was built from, in the owner's own words.", ["17"], f"{t.get('n', 0)} of {t.get('n', 0)} pieces", ["research.html", "coursework.html"])
    t6, t7 = T.get("onehead", {}), T.get("heads", {})
    checked("Every converted document carries one top-level heading, and every page's head holds to its end.", ["6", "7"],
            f"{t6.get('docs', 0)} document bodies, {t7.get('pages', 0)} heads, 0 broken", ["colophon.html"])
    t = T.get("headings", {})
    checked("Headings on the generated pages run in order, never skipping a level.", ["19"], f"{n(t.get('headings', 0))} headings on {t.get('pages', 0)} pages, 0 skips", ["colophon.html"])
    t = T.get("skip", {})
    checked("Every generated page opens with a skip link to its content.", ["20"], f"{t.get('pages', 0)} pages", ["colophon.html"])
    t = T.get("fignames", {})
    checked("Every figure on the generated pages carries an accessible name.", ["21"], f"{t.get('figures', 0)} figures on {t.get('pages', 0)} pages, 0 unnamed", ["colophon.html"])
    t = T.get("emdash", {})
    checked("No em dash stands in the prose of any page, except the six declared records, which are kept as written.", ["23"],
            f"{t.get('pages', 0)} pages, 0 in prose; {n(t.get('alone', 0))} standing alone as a cell or a chip and {n(t.get('code', 0))} inside code and data, counted and not held; "
            f"the {t.get('records', 0)} declared records carry {n(t.get('in_records', 0))}",
            ["colophon.html"])
    t = T.get("spelling", {})
    checked("The build's own words are spelled the Canadian way.", ["25"],
            f"{n(t.get('words', 0))} words on {t.get('pages', 0)} pages, with what the build quotes removed, against {t.get('list', 0)} American spellings; 0 found",
            ["colophon.html"])
    t = T.get("defined", {})
    checked("Every counted number names a definition the colophon prints and carries the value the record holds for it.", ["26"],
            f"{n(t.get('numbers', 0))} counted numbers on {t.get('pages', 0)} pages, 0 undefined, 0 that disagree with the record",
            ["colophon.html", "index.html"])
    t = T.get("superlatives", {})
    checked("A superlative in the owner's own fields is true of the data.", ["14"], f"{t.get('fields', 0)} fields scanned, 0 false", ["research.html"])
    t = T.get("workflow", {})
    checked("The site is deployed only after the build, its checks, the tests of controls, the browser audit and the idempotence proof have passed; a false claim is not published.",
            ["24"], f"the workflow carries the {t.get('steps', 0)} gate steps in order and a deploy job that needs the build job" if t.get("gate")
            else "the workflow lacks " + ", ".join(t.get("missing") or ["the gate"]),
            ["controls.html", "colophon.html"],
            note="Whether the gate operated on a given publish is visible on the repository's Actions page, not here: a run that fails leaves no page to print it on.")

    # --- measured in a browser, per page, with a fingerprint of what was measured ---
    def rt(claim, key, pages, where, note=None):
        recs, missing = _runtime(state, key, pages)
        cases = neg["runtime"].get(key, [])
        when, gate = _when_false(cases)
        if not recs:
            rows.append(_row(claim, "build/audit.js", [], f"for this build: {len(pages)} pages to measure", "open", where, note, when, key))
            return
        text, ok = agg(key, [r for _, r in recs], [p for p, _ in recs], decl.get("overflow") or [])
        if missing:
            text += f"; {len(missing)} of {len(pages)} pages not measured for this build"
        if not ok:
            status = "failed"
            ctx["problems"].append("register: a measured claim fails: %s (%s)" % (claim, text))
        elif gate:
            status, note = "untested", (note + " " if note else "") + gate.capitalize() + "."
        else:
            status = "held"
        rows.append(_row(claim, "build/audit.js", [], text, status, where, note, when, key))

    rt("At runtime the pages request nothing from another origin.", "ext", runtime_pages("ext", shell, allp, aux), ["index.html", "colophon.html"])
    rt("Nothing on a page moves while the reader is idle: no frame is requested once a page has loaded.", "idle", runtime_pages("idle", shell, allp, aux), ["atlas.html", "index.html"])
    rt("Focus is visible at every keyboard stop on the generated pages.", "keyboard", runtime_pages("keyboard", shell, allp, aux), ["colophon.html"])
    rt("The generated pages print: sticky elements release, nothing stays hidden, figures do not break across pages.", "print", runtime_pages("print", shell, allp, aux), ["colophon.html"])
    rt("Reduced motion is respected: nothing animates for a reader who asked for none.", "motion", runtime_pages("motion", shell, allp, aux), ["colophon.html"])
    rt("Every page fits a 320px viewport, except the pages declared in content/declared.json, each of which must still need the exception.", "fit", runtime_pages("fit", shell, allp, aux), ["colophon.html"])
    rt("The word count leaves out the site's own chrome around a piece.", "chrome", runtime_pages("chrome", shell, allp, aux), ["colophon.html"])
    rt("The home sphere turns to face the document whose featured row is at the reading line, at desktop and phone widths, carried by a critically damped spring that settles within 700ms of the last scroll, after which no frame is requested.",
       "descent", runtime_pages("descent", shell, allp, aux), ["index.html"])
    rt("The light behind the home sphere takes the hue of the faced document's recorded origin, the field the statement sorts by, and names no origin when nothing is faced.",
       "corona", runtime_pages("corona", shell, allp, aux), ["index.html"])
    rt("The theme selector is an offer, not an icon: two named states, Obsidian and Archival light, one pressed; a single soft pulse on the first visit from a browser and none after; a switch that settles with no frame requested; a focus ring on the offer from the keyboard.",
       "theme", runtime_pages("theme", shell, allp, aux), ["index.html"])
    rt("The header mark holds two states: the letters at rest, and the construction they were measured from under a pointer or a keyboard focus. "
       "The change is opacity alone, inside a 260ms cap, removed entirely for a reader who asked for no motion, and it moves the brand's box by no pixel "
       "and requests no frame once it has settled.",
       "inspect", runtime_pages("inspect", shell, allp, aux), ["colophon.html"])
    rt("The editor, admin.html, loads with no console error, no uncaught exception and no failed request, asks nothing of another origin until it is connected, "
       "requests no frame while idle, and its controls respond: the tabs and the search before a connection exists, the theme button, the connection form "
       "keeping the repository in this browser and the token in this tab only, and, connected through a stub of GitHub that refuses every write, "
       "the list of every recorded piece, the search, the editor, an edit that enables Publish, the guard that holds Publish without a token, "
       "the files and the site text; nothing is written.",
       "admin", runtime_pages("admin", shell, allp, aux), ["controls.html"],
       note="Measured on this tree's copy, served locally, with GitHub stubbed. On the live site the editor talks to GitHub, and a refusal there "
            "(a rate limit, an expired token) logs one resource error in the console that the page reports in its own words.")

    off = state.get("offline")
    cases = neg["runtime"].get("offline", [])
    when, gate = _when_false(cases)
    claim = "A saved offline copy survives a publish, the file that changed is refreshed in it, and the editor is never served from it."
    if off:
        ok = offline_ok(off)
        ed = off.get("editor") or {}
        edt = ("not measured" if not ed else "served from the network on both visits and held in no cache"
               if (ed.get("stored") is False and ed.get("fresh") is True) else "held in the cache" if ed.get("stored") else "served stale after the publish")
        text = (f"{off.get('before', 0)} files held before a simulated publish, {off.get('after', 0)} after, "
                f"the changed page {'refreshed' if off.get('refreshed') else 'not refreshed'}; the editor {edt}")
        status = "failed" if not ok else ("untested" if gate else "held")
        if not ok:
            ctx["problems"].append("register: the offline claim fails: %s" % json.dumps(off))
        rows.append(_row(claim, "build/audit.js", [], text, status, ["colophon.html"], (gate.capitalize() + ".") if (ok and gate) else None, when, "offline"))
    else:
        rows.append(_row(claim, "build/audit.js", [], "for this build", "open", ["colophon.html"], None, when, "offline"))

    t = T.get("colour", {})
    checked("On the figures the site lifts out of its pieces, no meaning is carried by colour alone: every colour a figure's marks use is declared with a meaning in words and named in a key under the figure.",
            ["30"], f"{t.get('colours', 0)} meaning colours across {t.get('figures', 0)} lifted figures on {t.get('pages', 0)} pages, {t.get('unnamed', 0)} unnamed, {t.get('stray', 0)} declared and unused",
            ["research.html", "index.html", "colophon.html"],
            note="The figures a piece draws inside itself are the piece's own and are not held to this; the sphere and the corpus figure carry their keys on their pages.")
    t = T.get("restated", {})
    checked("Every number a figure on the generated pages draws is restated in the page's text outside the drawing.", ["31"],
            f"{n(t.get('numerals', 0))} numerals drawn by {t.get('figures', 0)} figures on {t.get('pages', 0)} pages, {t.get('missing', 0)} not restated",
            ["research.html", "index.html", "colophon.html"])

    t = T.get("marks", {})
    checked("The three marks the pages draw are the geometry in content/marks and nothing else: every element, "
            "coordinate and stroke width is the file's, no surface draws an element its file does not carry, "
            "the thinnest stroke on every surface clears one device pixel at the size it is drawn, and the "
            "stylesheet does not resize any of them.", ["34"],
            f"{t.get('files', 0)} files of {t.get('elements', 0)} elements on a {t.get('grid', 0)} unit grid, drawn on {t.get('pages', 0)} pages: "
            + "; ".join("%s draws %d of %d at %g times, %.2f device pixels at %gpx"
                        % (d["key"], d["drawn"], d["of"], d["scale"], d["thin"], d["px"])
                        for d in (t.get("detail") or []))
            + f"; {t.get('mismatched', 0)} marks that are not their file's geometry, {t.get('unknown', 0)} elements "
              f"drawn that no file carries, {t.get('thin', 0)} strokes under a device pixel; of the "
              f"{t.get('invariants', 0)} values the marks' own sheet states, {t.get('carried', 0)} are readings the files bear out",
            ["colophon.html", "controls.html"],
            note="The sheet that came with the marks is not a source here: where a stated value and the drawn path "
                 "disagree, the path is what the site draws and what this check reads.")

    t = T.get("instruments", {})
    checked("The six verification glyphs, the seal and the figure on every statement row are the geometry their "
            "files and their measurements produce and nothing else: each glyph is its file's elements, the seal is "
            "its file with the one stroke no size can hold dropped and the rest lifted by one factor, every figure "
            "is what its own document's words, figures, tables and recorded links draw, every dimension the callout "
            "ledger prints is what a second walk of the same path data reads, and the stylesheet resizes none of them.", ["35"],
            f"{t.get('glyphs', 0)} glyphs of {t.get('glyph_elements', 0)} elements and {t.get('seal', 0)} seal, "
            f"{t.get('drawn', 0)} drawn across {t.get('pages', 0)} pages; "
            f"{t.get('figures', 0)} figures for {t.get('of', 0)} pieces, each rebuilt here from the four measured values; "
            f"{t.get('callouts', 0)} dimension callouts walked a second time from the same two files; "
            f"{t.get('mismatched', 0)} that are not the geometry they claim, {t.get('thin', 0)} strokes under a device pixel",
            ["colophon.html", "library.html", "about.html"],
            note="This check keeps its own reader and its own arithmetic, so an emitter that invents an element or "
                 "draws one document's figure on another document's row is caught by something that never asked it.")

    t = T.get("contrast", {})
    checked("Every colour the site sets text in clears the 4.5:1 a reader needs, on every surface a page stands it "
            "on, in both themes, and the two lights behind the hero do not take it under: each light is composited "
            "over the paper at full strength and the whole palette is measured again. The dark ground is declared "
            "twice, once for a browser that asks for it and once for the button, and the two say the same thing. "
            "The border of a control clears 3:1.",
            ["36"],
            f"{t.get('tokens', 0)} text colours across {t.get('themes', 0)} themes, {t.get('pairs', 0)} colour and "
            f"ground pairs measured, {t.get('under', 0)} under the floor; the narrowest is "
            f"{t.get('worst_at', 'nothing measured')} at {t.get('worst', 0)}:1 against a floor of {t.get('floor', 0)}:1; "
            f"{t.get('mirrored', 0)} tokens of the dark ground declared in both places and agreeing in both",
            ["colophon.html", "controls.html"],
            note="Computed from the tokens in site.css on this build, not from a comment beside them: a palette edit "
                 "that lowers a ratio fails the build rather than the audit.")

    t = T.get("scope", {})
    checked("Every table header the build writes says which cells it heads.", ["37"],
            f"{t.get('th', 0)} header cells on {t.get('pages', 0)} generated pages, {t.get('bare', 0)} with no scope, "
            f"{t.get('wrong', 0)} with a scope that is not one",
            ["colophon.html"],
            note="The generated pages only. The tables inside the 65 pieces are the pieces' own markup and are not "
                 "rewritten here, so this claim does not reach them.")

    t = T.get("cases", {})
    checked("Every slot the selected-work page fills points at something already on the site: a heading the piece "
            "itself carries, quoted as the invariance record holds it; another listed piece the corpus records a "
            "link to; or a value this build computed. A slot nothing answers is printed as not carried and counted.",
            ["38"],
            f"{t.get('slots', 0)} slots over {t.get('pieces', 0)} pieces: {t.get('sec', 0)} a section, "
            f"{t.get('doc', 0)} a linked document, {t.get('rec', 0)} a record, {t.get('gap', 0)} not carried; "
            f"{t.get('quoted', 0)} headings quoted, {t.get('misquoted', 0)} that the record does not hold, "
            f"{t.get('broken', 0)} placements that resolve to nothing",
            ["selected.html", "colophon.html"],
            note="Which heading answers which slot is a reading of the piece and is declared in content/cases.json. "
                 "The check holds that every placement resolves and that every quotation is exact. It does not hold "
                 "that the reading is the right one, and nothing here claims it does.")

    t = T.get("capabilities", {})
    checked("Every capability the about page claims names the work that evidences it, every piece it names is one "
            "the site lists and links, and every total printed beside a claim is the sum of that claim's own "
            "pieces, recomputed on the build rather than typed.",
            ["39"],
            f"{t.get('caps', 0)} capabilities, {t.get('named', 0)} pieces named, {t.get('unknown', 0)} not listed, "
            f"{t.get('empty', 0)} with nothing behind them, {t.get('unlinked', 0)} named but not linked, "
            f"{t.get('wrong', 0)} totals that do not match their pieces",
            ["about.html", "colophon.html"],
            note="Which pieces evidence which capability is a reading and is declared in content/capabilities.json. "
                 "The sets overlap, so their subtotals do not add to the corpus. The check holds the arithmetic and "
                 "the membership's existence, not the judgment.")

    t = T.get("editor", {})
    checked("The editor, admin.html, exists and the build never writes it: every stylesheet, script and local asset it references resolves to a file, "
            "every custom property its styles read is defined by the stylesheet it loads, every element id its script names is in its markup, "
            "its script parses, the worker never stores it, the offline copy never lists it, and no index is invited to it.", ["33"],
            f"{t.get('files', 0)} file of {n(t.get('bytes', 0))} bytes, {t.get('rewritten', 0)} rewritten by the build; {t.get('refs', 0)} references, {t.get('broken', 0)} broken; "
            f"{t.get('tokens', 0)} custom properties read, {t.get('undefined', 0)} undefined; {t.get('ids', 0)} element ids named, {t.get('missing', 0)} missing; "
            f"{t.get('scripts', 0)} scripts, {t.get('unparsed', 0)} that do not parse"
            + (" (parsed by node)" if t.get("parsed_by") == "node" else " (node was not on the path, so parsing was not checked)"),
            ["controls.html"],
            note="Hand-maintained, so the em dash rule and the head rewrite leave it alone; what it does when opened is the editor row below, measured in a browser.")

    # --- asserted: no check exists ---
    # (none this build: the two claims that stood here are checks 30 and 31)

    summary = {"rows": len(rows)}
    for st in ("held", "untested", "open", "asserted", "failed"):
        summary[st] = sum(1 for r in rows if r["status"] == st)
    return rows, summary


STATUS_WORD = {"held": "held", "untested": "untested", "open": "not yet measured", "asserted": "asserted", "failed": "failed"}


def _audit_age(audit):
    """How many recorded publishes since the browser audit last ran."""
    runs = ((audit.get("meta") or {}).get("runs")) or []
    age = 0
    for r in reversed(runs):
        if r.get("audit") == "ran":
            break
        age += 1
    return age, len(runs)


def render(rows, summary, audit_meta, neg_state=None):
    """The register as one table, with the lines that say when its records
    were taken."""
    groups = [("Checked by the build on every publish", lambda r: r["by"].startswith("check")),
              ("Measured in a browser, per page", lambda r: r["by"] == "build/audit.js"),
              ("Asserted, with no check yet", lambda r: r["status"] == "asserted")]
    out = []
    for title, want in groups:
        rs = [r for r in rows if want(r)]
        if not rs:
            continue
        out.append(f'<tr class="grp"><th scope="rowgroup" colspan="4">{esc(title)}</th></tr>')
        for r in rs:
            note = f'<span class="rg-note">{esc(r["note"])}</span>' if r.get("note") else ""
            when = esc(r["when"]) if r.get("when") else ("" if r["status"] == "asserted" else "")
            out.append(
                f'<tr class="rg-{r["status"]}"><td class="rg-claim">{esc(r["claim"])}{note}</td>'
                f'<td class="rg-by">{esc(r["by"])}</td>'
                f'<td class="rg-res"><span class="rg-st">{esc(STATUS_WORD[r["status"]])}</span> '
                f'{esc(r["result"]) if r["status"] != "asserted" else ""}</td>'
                f'<td class="rg-when">{when}</td></tr>')
    lines = []
    if audit_meta:
        audit = load_audit()
        age, nruns = _audit_age(audit)
        since = ("this publish measured" if age == 0 and nruns else
                 f"{age} publish{'es' if age != 1 else ''} since kept its records because no input moved")
        lines.append(f'<p class="audit-line">The browser measurements were recorded by <code>build/audit.js</code> '
                     f'on {esc(audit_meta.get("date", "an unknown date"))} at commit <code>{esc(audit_meta.get("commit", "unknown"))}</code> '
                     f'in {esc(audit_meta.get("browser", "a headless browser"))}; the record is '
                     f'<a href="content/audit.json">content/audit.json</a>, a page whose inputs moved since is marked not yet measured, '
                     f'and {since}.</p>')
    if neg_state:
        bm, rm = neg_state.get("build_meta") or {}, neg_state.get("runtime_meta") or {}
        nb = sum(len(v) for v in neg_state["build"].values()); nr = sum(len(v) for v in neg_state["runtime"].values())
        cb = sum(1 for v in neg_state["build"].values() for c in v if c.get("caught"))
        cr = sum(1 for v in neg_state["runtime"].values() for c in v if c.get("caught"))
        lines.append(f'<p class="register-line">The falsifications were recorded by <code>build/negatives.py</code> '
                     f'on {esc(bm.get("date", "no date"))} at commit <code>{esc(bm.get("commit", "unknown"))}</code> against code <code>{esc(bm.get("code", "unknown"))}</code>: '
                     f'{cb} of {nb} caught; the runtime falsifications by <code>build/audit.js --falsify</code> '
                     f'on {esc(rm.get("date", "no date"))}: {cr} of {nr} caught. The record is '
                     f'<a href="content/negatives.json">content/negatives.json</a>; a record taken against other code prints untested.</p>')
    table = ('<div class="tw"><table class="ctab register" id="register-table">'
             '<caption>Every claim the generated pages make about this site, the check that tests it, the last result with its denominator, '
             'and what happened when the claim was deliberately made false. '
             f'{summary["held"]} held, {summary["untested"]} untested, {summary["open"]} not yet measured for this build, '
             f'{summary["asserted"]} asserted with no check, {summary["failed"]} failed. A claim is held only while a current falsification '
             'stands behind every check it cites; a failed claim is never deployed, because the build refuses it.</caption>'
             '<thead><tr><th scope="col">The claim</th><th scope="col">Checked by</th><th scope="col">Last result</th><th scope="col">When made false</th></tr></thead>'
             '<tbody>' + "".join(out) + '</tbody></table></div>')
    return "".join(lines) + table


# --------------------------------------------------------- the instrument --
GLYPH = {"held": "#", "failed": "x", "stale": "?", "declared": "~", "none": ""}
GLYPH_CLASS = {"held": "g-h", "failed": "g-x", "stale": "g-q", "declared": "g-d", "none": "g-n"}
RUNTIME_COLS = [("ext", "E"), ("idle", "I"), ("keyboard", "K"), ("print", "P"), ("motion", "M"), ("fit", "F"), ("chrome", "C"), ("descent", "D"), ("theme", "T"), ("corona", "H"), ("inspect", "V"), ("admin", "A")]


def _sort_key(cid):
    m = re.match(r"(\d+)(.*)", cid)
    return (int(m.group(1)), m.group(2)) if m else (999, cid)


def matrix(ctx):
    """The page wall: for every page, the state of every check that looks at
    pages. Returns (columns, rows) where columns are (id, label, kind) and
    rows are (page, {col_id: state})."""
    R = ctx["records"]
    state = ctx["audit"]
    shell = ctx["shell_pages"]
    allp = ctx["all_pages"]
    aux = ctx.get("aux_pages") or []
    decl = set((declared().get("overflow")) or [])
    listed = set(allp) | set(aux)
    cols = [(cid, cid, "build") for cid in sorted(R, key=_sort_key) if any(p in listed for p in R[cid])]
    cols += [(k, lab, "runtime") for k, lab in RUNTIME_COLS]
    rows = []
    for page in list(allp) + [p for p in aux if p not in allp]:
        cells = {}
        for cid, _lab, kind in cols:
            if kind == "build":
                v = R[cid].get(page)
                # a check does not grade its own glyph: the cell for check 29 on
                # the controls page itself is blank, or the page could never settle
                if cid == "29" and page == "controls.html":
                    v = None
                cells[cid] = "none" if v is None else ("held" if v else "failed")
            else:
                applies = page in runtime_pages(cid, shell, allp, aux)
                if not applies:
                    cells[cid] = "none"
                elif page in state["fresh"] and state["fresh"][page].get(cid) is not None:
                    ok = page_ok(cid, state["fresh"][page])
                    if cid == "fit" and not ok and page in decl:
                        cells[cid] = "declared"
                    else:
                        cells[cid] = "held" if ok else "failed"
                else:
                    cells[cid] = "stale"
        rows.append((page, cells))
    return cols, rows


def ledger(ctx):
    """The falsification wall: one line per check or runtime key, one glyph
    per falsification on record."""
    neg = ctx["negatives"]
    R = ctx["records"]
    lines = []
    ids = sorted(set(R) | set(neg["build"]), key=_sort_key)
    for cid in ids:
        cases = neg["build"].get(cid, [])
        lines.append(("check " + cid, cid, [("stale" if not c.get("current") else ("held" if c.get("caught") else "failed"), c["what"]) for c in cases]))
    for key, lab in RUNTIME_COLS + [("offline", "O")]:
        cases = neg["runtime"].get(key, [])
        lines.append((key, lab, [("stale" if not c.get("current") else ("held" if c.get("caught") else "failed"), c["what"]) for c in cases]))
    return lines


def render_instrument(ctx, page_titles=None):
    cols, rows = matrix(ctx)
    lines = ledger(ctx)
    titles = page_titles or {}
    # column sums: covered and held, the denominators as glyph counts
    covered = {c[0]: sum(1 for _, cells in rows if cells[c[0]] != "none") for c in cols}
    held = {c[0]: sum(1 for _, cells in rows if cells[c[0]] in ("held", "declared")) for c in cols}
    stale = {c[0]: sum(1 for _, cells in rows if cells[c[0]] == "stale") for c in cols}
    failed = {c[0]: sum(1 for _, cells in rows if cells[c[0]] == "failed") for c in cols}
    head = "".join(f'<th scope="col" class="ic ic-{kind}"><span>{esc(lab)}</span></th>' for _cid, lab, kind in cols)
    body = []
    for page, cells in rows:
        kind = ("shell" if page in ctx["shell_pages"] else "editor" if page in (ctx.get("aux_pages") or [])
                else "record" if page in (declared().get("records") or []) else "piece")
        tds = "".join(f'<td class="g {GLYPH_CLASS[cells[cid]]}">{GLYPH[cells[cid]]}</td>' for cid, _l, _k in cols)
        body.append(f'<tr class="ir ir-{kind}"><th scope="row" class="ip"><a href="{esc(page)}">{esc(page)}</a></th>{tds}</tr>')
    foot_cov = "".join(f'<td class="is">{covered[c[0]]}</td>' for c in cols)
    foot_held = "".join(f'<td class="is">{held[c[0]]}</td>' for c in cols)
    total_cells = sum(covered.values())
    total_held = sum(held.values()); total_stale = sum(stale.values()); total_failed = sum(failed.values())
    wall = ('<div class="tw inst-wrap"><table class="inst" id="page-wall">'
            f'<caption>One line per page, one column per check that looks at pages: {len(rows)} pages, {len(cols)} columns, '
            f'{n(total_cells)} glyphs, of which {n(total_held)} held, {total_failed} failed, {total_stale} not measured for this build. '
            'A blank is a check that does not look at that page.</caption>'
            f'<thead><tr><th scope="col" class="ip">page</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody>'
            f'<tfoot><tr class="isum"><th scope="row" class="ip">pages the check looked at</th>{foot_cov}</tr>'
            f'<tr class="isum"><th scope="row" class="ip">of them held</th>{foot_held}</tr></tfoot></table></div>')
    lb = []
    nc = sum(len(cs) for _, _, cs in lines); ncaught = sum(1 for _, _, cs in lines for st, _ in cs if st == "held")
    for name, lab, cases in lines:
        glyphs = "".join(f'<span class="g {GLYPH_CLASS[st]}" title="{esc(what)}">{GLYPH[st]}</span>' for st, what in cases) or '<span class="g g-n"></span>'
        whats = "; ".join(what for _, what in cases)
        count = f'{sum(1 for st, _ in cases if st == "held")} of {len(cases)}' if cases else "none on record"
        lb.append(f'<tr><th scope="row" class="ip">{esc(name)}</th><td class="ig">{glyphs}</td><td class="is">{esc(count)}</td><td class="iw">{esc(whats)}</td></tr>')
    ledg = ('<div class="tw inst-wrap"><table class="inst inst-ledger" id="falsifications">'
            f'<caption>One line per check, one glyph per falsification on record: {nc} falsifications, {ncaught} caught.</caption>'
            '<thead><tr><th scope="col" class="ip">check</th><th scope="col">when made false</th><th scope="col">caught</th><th scope="col">the falsification</th></tr></thead>'
            f'<tbody>{"".join(lb)}</tbody></table></div>')
    key = ('<p class="inst-key"><code>#</code> held on that page for this build &middot; <code>x</code> failed &middot; '
           '<code>?</code> not measured for this build &middot; <code>~</code> held by a declared exception &middot; '
           'blank: the check does not look at that page. Columns: the build\'s checks by number; E requests from another origin, '
           'I idle frames, K keyboard focus, P print media, M reduced motion, F fit at 320px, C the chrome exclusion, D the descent on the home page, T the theme selector, H the corona\'s hue, A the editor, O the offline copy.</p>')
    return key + wall + ledg, {"pages": len(rows), "columns": len(cols), "glyphs": total_cells, "held": total_held,
                              "failed": total_failed, "stale": total_stale, "falsifications": nc, "caught": ncaught}


def known_numbers(ctx):
    """Every numeral the register and the instrument print that the build
    computed: read from the computed strings (results, the when-false
    column, the summary, the instrument's counts and the record lines),
    never from the claim sentences, so a typed numeral in a claim is still
    caught by check 13."""
    rows, summary = build(dict(ctx, problems=[]))
    vals = set()
    def take(s):
        for m in re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", str(s)):
            try:
                vals.add(round(float(m.replace(",", "")), 6))
            except ValueError:
                pass
    for r in rows:
        take(r["result"]); take(r.get("when") or ""); take(r.get("note") or "")
    take(json.dumps(summary))
    _html, counts = render_instrument(ctx)
    take(json.dumps(counts))
    neg = ctx["negatives"]
    take(json.dumps(neg.get("build_meta") or {})); take(json.dumps(neg.get("runtime_meta") or {}))
    for v in list(neg["build"].values()) + list(neg["runtime"].values()):
        take(len(v)); take(sum(1 for c in v if c.get("caught")))
    audit = ctx["audit"]["audit"] or {}
    take(json.dumps(audit.get("meta") or {}))
    take(json.dumps(_audit_age(audit)))
    cols, mrows = matrix(ctx)
    for c in cols:
        take(sum(1 for _, cells in mrows if cells[c[0]] != "none")); take(sum(1 for _, cells in mrows if cells[c[0]] in ("held", "declared")))
    return vals


# ------------------------------------------------------------------ CLI --

def _cli(argv):
    """--digests: every page the register covers with its input fingerprint,
    the generated pages named, and the worker's, as JSON for build/audit.js.
    --stale: how many of those records content/audit.json lacks or holds
    for other inputs, for the workflow's plan step.
    --record-run <1|0>: append this publish to the audit's run record."""
    content = json.load(open(os.path.join(ROOT, "content", "pieces.json"), encoding="utf-8"))
    metrics = json.load(open(os.path.join(ROOT, "content", "metrics.json"), encoding="utf-8"))
    listed = [p.get("url") or (p["slug"] + ".html") for p in content["pieces"]]
    slugs = {p["slug"] for p in content["pieces"]}
    transcripts = sorted(k + ".html" for k in metrics if k not in slugs and os.path.exists(os.path.join(ROOT, k + ".html")))
    pages = [f for f in SHELL + AUX + listed + transcripts if os.path.exists(os.path.join(ROOT, f))]
    dig = {"shell": SHELL, "pages": {f: page_input_digest(ROOT, f, f in SHELL) for f in pages},
           "sw": sw_input_digest(ROOT), "runtime_code": runtime_code_digest(ROOT)}
    if "--digests" in argv:
        print(json.dumps(dig, indent=1))
        return 0
    if "--stale" in argv:
        audit = load_audit()
        recs = audit.get("pages") or {}
        stale = [f for f, d in dig["pages"].items() if not recs.get(f) or recs[f].get("inputs") != d]
        off = audit.get("offline") or {}
        off_stale = (not off) or off.get("inputs") != dig["sw"]
        neg = load_negatives()
        rt = (neg.get("runtime") or {}).get("meta") or {}
        print(json.dumps({"pages": len(stale), "offline": off_stale, "total": len(dig["pages"]),
                          "falsify": rt.get("code") != dig["runtime_code"]}))
        return 0
    if "--record-run" in argv:
        flag = argv[argv.index("--record-run") + 1] if len(argv) > argv.index("--record-run") + 1 else "0"
        audit = load_audit()
        meta = audit.setdefault("meta", {})
        runs = meta.setdefault("runs", [])
        runs.append({"commit": git_short(), "date": datetime.date.today().isoformat(),
                     "audit": "ran" if flag == "1" else "kept"})
        meta["runs"] = runs[-40:]
        json.dump(audit, open(AUDIT_PATH, "w", encoding="utf-8"), indent=1)
        open(AUDIT_PATH, "a", encoding="utf-8").write("\n")
        print("recorded: audit %s, %d runs on record" % (runs[-1]["audit"], len(meta["runs"])))
        return 0
    print("usage: claims.py --digests | --stale | --record-run <1|0>")
    return 2


if __name__ == "__main__":
    import sys
    sys.exit(_cli(sys.argv[1:]))
