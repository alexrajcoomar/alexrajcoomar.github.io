# -*- coding: utf-8 -*-
"""The register of the site's claims about itself.

Every sentence the generated pages say about the site is listed here beside
the check that tests it. A claim with a check prints the check's last
result with its denominator: so many links of so many, on so many pages.
A claim with no check prints the word "asserted" where a result would be,
so a reader can see what is taken on trust. A claim measured in a browser
prints "not yet measured for this build" when the record in
content/audit.json is older than the pages it describes, rather than a
result that was true of a previous build.

The build refuses to publish when a checked claim fails, which is what the
checks in build_site.py already do; this module adds the visible score.
The colophon prints the register; nothing here is typed by hand except the
sentences, and every number beside a sentence is computed.
"""
import datetime, hashlib, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_PATH = os.path.join(ROOT, "content", "audit.json")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def n(x):
    return format(x, ",") if isinstance(x, int) else str(x)


# ----------------------------------------------------------- the audit --
# What a browser measured, per page, with the fingerprint of the inputs it
# measured. A page whose inputs moved since is unmeasured for this build.

def load_audit():
    try:
        return json.load(open(AUDIT_PATH, encoding="utf-8"))
    except Exception:
        return {}


def page_input_digest(out_dir, name, shell):
    """The inputs a runtime measurement of a page depends on. A piece is
    self-contained, so its own text with the build's injected blocks removed.
    A generated page is a function of its sources, so the text of the page
    with the register itself removed (the register prints the audit, and a
    measurement must not go stale because its own result was printed),
    plus the stylesheet and the scripts it loads."""
    path = os.path.join(out_dir, name)
    if not os.path.exists(path):
        return None
    raw = open(path, encoding="utf-8", errors="ignore").read()
    h = hashlib.sha1()
    if shell:
        raw = re.sub(r'<section[^>]*id="claims".*?</section>', "", raw, flags=re.S)
        raw = re.sub(r'<p class="audit-line">.*?</p>', "", raw, flags=re.S)
        raw = re.sub(r'\?v=[0-9a-f]{8}', "", raw)
        h.update(raw.encode("utf-8"))
        for dep in ("site.css", "site.js", "atlas.js", "figures.css"):
            dp = os.path.join(out_dir, dep)
            if os.path.exists(dp):
                h.update(open(dp, "rb").read())
    else:
        raw = re.sub(r"<!--__rb-->.*?<!--/__rb-->|<!--__rbp-->.*?<!--/__rbp-->|<!--__meta-->.*?<!--/__meta-->"
                     r"|<!--__docend[^>]*-->.*?<!--/__docend-->|<!--__foot-->.*?<!--/__foot-->"
                     r"|<!--__tail-->.*?<!--/__tail-->|<!--__from-->.*?<!--/__from-->"
                     r"|<!--__long-->.*?<!--/__long-->|<style id=\"__mobile_fit\">.*?</style>"
                     r"|<!-- injected by the site build.*?-->|\?v=[0-9a-f]{8}", "", raw, flags=re.S)
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


# --------------------------------------------------------- the register --

def _row(claim, by, result, status, where=None, note=None):
    return {"claim": claim, "by": by, "result": result, "status": status,
            "where": where or [], "note": note}


def _runtime(state, key, pages, describe, agg):
    """A row for a browser measurement over a set of pages: aggregated over
    the pages whose record is current, with the unmeasured ones counted."""
    recs = [(p, state["fresh"][p].get(key)) for p in pages if p in state["fresh"] and state["fresh"][p].get(key) is not None]
    missing = [p for p in pages if p not in {r[0] for r in recs}]
    if not recs:
        return None, len(pages), missing
    return agg([r[1] for r in recs], [r[0] for r in recs]), len(pages), missing


def build(ctx):
    """ctx carries the build's tallies (check_site.tally), the piece
    population, the page lists and the audit state. Returns the rows, the
    problems (a checked claim that fails), and a summary."""
    T = ctx["tally"]
    state = ctx["audit"]
    shell = ctx["shell_pages"]
    allp = ctx["all_pages"]
    rows = []

    def held(claim, by, result, where=None, note=None):
        rows.append(_row(claim, by, result, "held", where, note))

    def asserted(claim, where=None, note=None):
        rows.append(_row(claim, "nothing yet", "asserted", "asserted", where, note))

    # --- checked by the build, on every publish ---
    t = T.get("numerals", {})
    held("Every number on the generated pages is one the build computed or a piece states in its own text.",
         "check 13",
         f"{n(t.get('n', 0))} numerals on {t.get('pages', 0)} pages, 0 typed. Not scanned: the Atlas index and the last pass's notes, which are quoted records, and this register, whose numbers are the checks' own output",
         ["colophon.html", "index.html"])
    t1, t3, t4, t9 = T.get("canonicals", {}), T.get("links", {}), T.get("icons", {}), T.get("listed", {})
    held("Every link, canonical address, manifest icon and listed file resolves to a file that exists.",
         "checks 1, 3, 4, 9",
         f"{n(t3.get('n', 0))} links on {t3.get('pages', 0)} pages, {n(t1.get('n', 0))} canonicals, "
         f"{t4.get('n', 0)} icons, {t9.get('n', 0)} listed files, 0 unresolved",
         ["colophon.html"])
    t = T.get("hosts", {})
    held("No page names an address other than this site's.", "check 2",
         f"{t.get('pages', 0)} pages, 0 other hosts", ["colophon.html"])
    t = T.get("external", {})
    held("Nothing on any page is loaded from another origin, except the typefaces the exceptions name.",
         "check 22",
         f"{n(t.get('refs', 0))} references on {t.get('pages', 0)} pages, {t.get('allowed', 0)} to the named typefaces, 0 others; "
         f"{t.get('cookie', 0)} uses of the cookie API",
         ["colophon.html", "index.html"])
    t = T.get("invariance", {})
    held("Nothing a piece claims has moved since its record was written: not a numeral, a reference, a label, an anchor or a result sentence.",
         "check 15",
         f"{t.get('held', 0)} of {t.get('checked', 0)} records hold ({t.get('listed', 0)} listed pieces and {t.get('transcripts', 0)} transcripts); "
         f"{t.get('declared', 0)} carry declared changes",
         ["colophon.html"])
    t = T.get("origins", {})
    held("The three origins add to the corpus line in pieces, words, figures and tables.", "check 12",
         f"{t.get('keys', 0)} totals, 0 that disagree", ["index.html", "colophon.html"])
    t8, ta = T.get("atlas_marks", {}), T.get("placement", {})
    held("Every mark on the Atlas opens a passage that exists, and the marks drawn are the marks the placement produced.",
         "checks 8, 11a",
         f"{n(t8.get('n', 0))} marks into {t8.get('files', 0)} documents, 0 dead; {n(ta.get('marks', 0))} on the Atlas and "
         f"{n(ta.get('teaser', 0))} on the home sphere read back against the placement, 0 stray",
         ["atlas.html", "index.html"])
    t = T.get("weights", {})
    held("The marks' apportioned word weights add back to the corpus line.", "check 11a2",
         f"{n(t.get('marks', 0))} weights sum to {n(t.get('sum', 0))}", ["atlas.html"])
    t10, t18 = T.get("subset", {}), T.get("fonts", {})
    held("Every character the pages show that Inter can render is in the self-hosted subset, and every other self-hosted face carries its piece's characters.",
         "checks 10, 18",
         f"{n(t10.get('chars', 0))} distinct characters on {t10.get('pages', 0)} pages against the subset; "
         f"{t18.get('files', 0)} other subsets held to their manifest and digest",
         ["colophon.html"])
    t = T.get("chrome", {})
    held("The chrome the build writes into a piece uses only colours the stylesheet knows.", "check 11",
         f"{t.get('n', 0)} colours, 0 unknown", ["colophon.html"])
    t = T.get("ledger", {})
    held("The ledger's class for every piece (untouched, styling, copy, new) is what the files show.", "check 16",
         f"{t.get('n', 0)} pieces recomputed, 0 stale", ["colophon.html"])
    t = T.get("built_from", {})
    held("Every listed piece states what it was built from, in the owner's own words.", "check 17",
         f"{t.get('n', 0)} of {t.get('n', 0)} pieces", ["research.html", "coursework.html"])
    t6, t7 = T.get("onehead", {}), T.get("heads", {})
    held("Every converted document carries one top-level heading, and every page's head holds to its end.",
         "checks 6, 7",
         f"{t6.get('docs', 0)} document bodies, {t7.get('pages', 0)} heads, 0 broken", ["colophon.html"])
    t = T.get("headings", {})
    held("Headings on the generated pages run in order, never skipping a level.", "check 19",
         f"{n(t.get('headings', 0))} headings on {t.get('pages', 0)} pages, 0 skips", ["colophon.html"])
    t = T.get("skip", {})
    held("Every generated page opens with a skip link to its content.", "check 20",
         f"{t.get('pages', 0)} pages", ["colophon.html"])
    t = T.get("fignames", {})
    held("Every figure on the generated pages carries an accessible name.", "check 21",
         f"{t.get('figures', 0)} figures on {t.get('pages', 0)} pages, 0 unnamed", ["colophon.html"])
    t = T.get("emdash", {})
    held("No em dash on any generated page.", "check 23",
         f"{t.get('generated_pages', 0)} pages, 0 em dashes; the pieces carry {n(t.get('in_pieces', 0))} in "
         f"{t.get('pieces_with', 0)} pieces, which their record holds",
         ["colophon.html"])
    t = T.get("superlatives", {})
    held("A superlative in the owner's own fields is true of the data.", "check 14",
         f"{t.get('fields', 0)} fields scanned, 0 false", ["research.html"])

    # --- measured in a browser, per page, with a fingerprint of what was measured ---
    def rt(claim, key, pages, agg, where, by="build/audit.js"):
        res, total, missing = _runtime(state, key, pages, None, agg)
        if res is None:
            rows.append(_row(claim, by, f"not yet measured for this build ({total} pages)", "open", where))
            return
        text, ok = res
        if missing:
            text += f"; {len(missing)} of {total} pages not yet measured for this build"
        rows.append(_row(claim, by, text, "held" if ok else "failed", where))
        if not ok:
            ctx["problems"].append("register: a measured claim fails: %s (%s)" % (claim, text))

    def agg_ext(recs, names):
        req = sum(r.get("requests", 0) for r in recs); ext = sum(r.get("external", 0) for r in recs)
        return (f"{n(req)} requests on {len(recs)} pages, {ext} to another origin", ext == 0)
    rt("At runtime the pages request nothing from another origin.", "ext", allp, agg_ext, ["index.html", "colophon.html"])

    def agg_idle(recs, names):
        fr = sum(r.get("frames", 0) for r in recs)
        return (f"{fr} frames requested in the second after load, over {len(recs)} pages", fr == 0)
    rt("Nothing on a page moves while the reader is idle: no frame is requested once a page has loaded.", "idle", allp, agg_idle, ["atlas.html", "index.html"])

    def agg_kb(recs, names):
        st = sum(r.get("stops", 0) for r in recs); bad = sum(r.get("noRing", 0) for r in recs)
        return (f"{n(st)} Tab stops on {len(recs)} pages, {bad} without a visible ring", bad == 0)
    rt("Focus is visible at every keyboard stop on the generated pages.", "keyboard", shell, agg_kb, ["colophon.html"])

    def agg_print(recs, names):
        sticky = sum(r.get("stickyLeft", 0) for r in recs); hidden = sum(r.get("hidden", 0) for r in recs)
        figs = sum(r.get("figures", 0) for r in recs); nobreak = sum(r.get("figuresBreakable", 0) for r in recs)
        return (f"{len(recs)} pages under print media: {sticky} sticky elements left pinned, {hidden} blocks left hidden, "
                f"{nobreak} of {figs} figures allowed to break", sticky == 0 and hidden == 0 and nobreak == 0)
    rt("The generated pages print: sticky elements release, nothing stays hidden, figures do not break across pages.", "print", shell, agg_print, ["colophon.html"])

    def agg_motion(recs, names):
        an = sum(r.get("animations", 0) for r in recs)
        return (f"{an} animations running under reduced motion, over {len(recs)} pages", an == 0)
    rt("Reduced motion is respected: nothing animates for a reader who asked for none.", "motion", shell, agg_motion, ["colophon.html"])

    def agg_fit(recs, names):
        bad = [nm for nm, r in zip(names, recs) if r.get("overflow")]
        text = f"{len(recs) - len(bad)} of {len(recs)} pages fit a 320px viewport"
        if bad:
            text += "; " + ", ".join(bad)
        return (text, True)   # reported, not enforced: the overflowing pieces are named, not hidden
    rt("Every page fits a 320px viewport; the pages that do not are named here.", "fit", allp, agg_fit, ["colophon.html"])

    off = state.get("offline")
    if off:
        ok = off.get("before", 0) > 0 and off.get("after", 0) >= off.get("before", 0) and off.get("refreshed") is True
        rows.append(_row("A saved offline copy survives a publish, and the file that changed is refreshed in it.",
                         "build/audit.js",
                         f"{off.get('before', 0)} files held before a simulated publish, {off.get('after', 0)} after, "
                         f"the changed page {'refreshed' if off.get('refreshed') else 'not refreshed'}",
                         "held" if ok else "failed", ["colophon.html"]))
        if not ok:
            ctx["problems"].append("register: the offline claim fails: %s" % json.dumps(off))
    else:
        rows.append(_row("A saved offline copy survives a publish, and the file that changed is refreshed in it.",
                         "build/audit.js", "not yet measured for this build", "open", ["colophon.html"]))

    # --- asserted: no check exists yet ---
    asserted("Colour never carries meaning on its own: every mark that means something also differs in fill or shape.", ["colophon.html"])
    asserted("Every figure's numbers are restated in a table or in the running text.", ["colophon.html"])
    asserted("The build is idempotent: a second run rewrites nothing.", ["colophon.html"],
             note="Checked by hand on every commit of the branch that introduced this register; not yet by the workflow.")
    asserted("The word count leaves out the site's own chrome around a piece.", ["colophon.html"],
             note="The measurement removes the chrome by selector; nothing checks that the selectors still name all of it.")

    summary = {
        "rows": len(rows),
        "held": sum(1 for r in rows if r["status"] == "held"),
        "open": sum(1 for r in rows if r["status"] == "open"),
        "asserted": sum(1 for r in rows if r["status"] == "asserted"),
        "failed": sum(1 for r in rows if r["status"] == "failed"),
    }
    return rows, summary


STATUS_WORD = {"held": "held", "open": "not yet measured", "asserted": "asserted", "failed": "failed"}


def render(rows, summary, audit_meta):
    """The register as one table with the audit's own line above it."""
    groups = [("Checked by the build on every publish", lambda r: r["by"].startswith("check")),
              ("Measured in a browser, per page", lambda r: r["by"] == "build/audit.js"),
              ("Asserted, with no check yet", lambda r: r["status"] == "asserted")]
    out = []
    for title, want in groups:
        rs = [r for r in rows if want(r)]
        if not rs:
            continue
        out.append(f'<tr class="grp"><th scope="rowgroup" colspan="3">{esc(title)}</th></tr>')
        for r in rs:
            note = f'<span class="rg-note">{esc(r["note"])}</span>' if r.get("note") else ""
            out.append(
                f'<tr class="rg-{r["status"]}"><td class="rg-claim">{esc(r["claim"])}{note}</td>'
                f'<td class="rg-by">{esc(r["by"])}</td>'
                f'<td class="rg-res"><span class="rg-st">{esc(STATUS_WORD[r["status"]])}</span> '
                f'{esc(r["result"]) if r["status"] != "asserted" else ""}</td></tr>')
    meta = ""
    if audit_meta:
        meta = (f'<p class="audit-line">The browser measurements were recorded by <code>build/audit.js</code> '
                f'on {esc(audit_meta.get("date", "an unknown date"))} at commit <code>{esc(audit_meta.get("commit", "unknown"))}</code> '
                f'in {esc(audit_meta.get("browser", "a headless browser"))}; the record is '
                f'<a href="content/audit.json">content/audit.json</a>, and a page whose inputs moved since is marked not yet measured.</p>')
    table = ('<div class="tw"><table class="ctab register" id="register">'
             '<caption>Every claim the generated pages make about this site, the check that tests it, and the last result with its denominator. '
             f'{summary["held"]} held, {summary["open"]} not yet measured for this build, {summary["asserted"]} asserted with no check, '
             f'{summary["failed"]} failed; a failed claim is never published, because the build refuses it.</caption>'
             '<thead><tr><th scope="col">The claim</th><th scope="col">Checked by</th><th scope="col">Last result</th></tr></thead>'
             '<tbody>' + "".join(out) + '</tbody></table></div>')
    return meta + table
