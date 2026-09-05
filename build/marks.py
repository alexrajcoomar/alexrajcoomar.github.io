# -*- coding: utf-8 -*-
"""The shipped brand marks, parsed, and the reductions the pages draw.

A mark drawn small is the same geometry as the mark drawn large: elements are
removed and every remaining stroke is multiplied by one stated factor. Nothing
is redrawn by hand, so a reduction cannot drift from its source."""
import html as _html, math, os, re


def html_unescape(t):
    return _html.unescape(t)

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "marks")
FILES = {"monogram": "01_vernier_monogram_AR.svg",
         "delta": "02_forensic_audit_delta.svg",
         "datum": "03_polar_datum.svg"}
_AT = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')


def read(path, tags=("circle", "path"), by_tag=False):
    """Every drawn element of one file, in document order. A group of elements
    is keyed by the comment above it plus its ordinal in that group; a file
    that carries no comments is keyed by tag instead, which is what the glyphs
    need and what the three brand marks never hit."""
    if not os.path.exists(path):
        return []          # check 34 names the missing file; the build refuses there
    raw = open(path, encoding="utf-8").read()
    label, seen, out = "", {}, []
    pat = r"<!--(.*?)-->|<(%s)\b([^>]*?)/>" % "|".join(tags)
    for m in re.finditer(pat, raw, re.S):
        if m.group(1) is not None:
            label = re.sub(r"\s+", " ", m.group(1)).strip()
            continue
        a = dict(_AT.findall(m.group(3)))
        if "d" in a:
            a["d"] = re.sub(r"\s+", " ", a["d"]).strip()
        key = m.group(2) if by_tag else label
        seen[key] = seen.get(key, 0) + 1
        out.append({"id": "%s#%d" % (key, seen[key]), "tag": m.group(2), "attrs": a})
    return out


def parse(name, src_dir=None):
    """Every drawn element of one brand mark, in document order, keyed by the
    comment that labels its group plus its ordinal in that group."""
    return read(os.path.join(src_dir or SRC, FILES[name]))

def body(name, keep=None, scale=1.0, src_dir=None):
    """The elements of one mark as SVG, with every stroke multiplied by scale."""
    parts = []
    for e in parse(name, src_dir):
        if keep is not None and e["id"] not in keep:
            continue
        a = dict(e["attrs"])
        if "stroke-width" in a:
            w = float(a["stroke-width"]) * scale
            a["stroke-width"] = ("%.4f" % w).rstrip("0").rstrip(".")
        order = ("cx", "cy", "r", "d", "stroke-width", "opacity", "fill", "stroke")
        parts.append("<%s %s/>" % (e["tag"], " ".join('%s="%s"' % (k, a[k]) for k in order if k in a)))
    return "".join(parts)

MONO_PRIMARY = ("A#1", "A#2", "R bowl#1", "R leg#1")
# What the reduction leaves out: the circle the A is constructed inside, the
# datum both letters stand on, and the ticks at the apex and the two feet.
# These are the three dimensions the sheet calls R28, APEX y6 and BASE y56,
# and the header draws them when a reader points at the mark.
MONO_CONSTRUCTION = ("Construction circle#1", "Central datum#1",
                     "Verification ticks#1", "Verification ticks#2", "Verification ticks#3")
# What each surface draws, and the factor that lifts its thinnest stroke over
# one device pixel at the size it is drawn (rendered weight is stroke x size / 64).
VARIANTS = {
    # the header mark carries a second layer: at rest it draws the letters, and
    # under a pointer or a keyboard focus it draws the construction they were
    # measured from. The layer needs a factor of its own, because 0.75 units at
    # the letters' factor would be 0.62 of a device pixel and hold no edge.
    "brand":    {"mark": "monogram", "keep": MONO_PRIMARY, "scale": 2.2, "px": 24,
                 "inspect": {"keep": MONO_CONSTRUCTION, "scale": 3.6}},
    # the bar injected at the top of a standalone piece is narrower than the
    # header's: it replaced a 1.2rem tile, and four pieces sat at exactly the
    # 320px a phone gives them, so a wider mark took them over it
    "bar":      {"mark": "monogram", "keep": MONO_PRIMARY, "scale": 2.4, "px": 19},
    "favicon":  {"mark": "monogram", "keep": ("A#1", "A#2", "R leg#1"), "scale": 3.3, "px": 16},
    "controls": {"mark": "delta", "keep": None, "scale": 1.5, "px": 44},
    "atlas":    {"mark": "datum", "keep": None, "scale": 1.8, "px": 48},
    "author":   {"mark": "datum",
                 "keep": ("Polar rings#1", "Cardinal datum ticks#1", "North Pole observer#1", "Author datum#1"),
                 "scale": 3.0, "px": 26},
}

def variant_body(key, src_dir=None):
    v = VARIANTS[key]
    return body(v["mark"], v["keep"], v["scale"], src_dir)

if __name__ == "__main__":
    import json
    for n in FILES:
        print(n, [e["id"] for e in parse(n)])
    out = [{"name": k, "mark": v["mark"], "px": v["px"], "scale": v["scale"],
            "body": variant_body(k)} for k, v in VARIANTS.items()]
    json.dump(out, open("/tmp/claude-0/-home-user/fbb4bce0-ef46-5bf7-bbda-3c26fad9e8dd/scratchpad/phase8/final.json", "w"), indent=1)
    print("\nwritten: final.json")


def svg(key, cls=None, src_dir=None):
    """One mark as an inline SVG element: no request, no colour of its own.
    Decorative in every placement, because in each one the words beside it
    already say what it says."""
    v = VARIANTS[key]
    inner = variant_body(key, src_dir)
    ins = v.get("inspect")
    if ins:
        inner = ('<g class="mk-nom">%s</g><g class="mk-ins">%s</g>'
                 % (inner, body(v["mark"], ins["keep"], ins["scale"], src_dir)))
    return ('<svg class="%s" viewBox="0 0 64 64" width="%d" height="%d" fill="none" '
            'stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true" focusable="false">%s</svg>'
            % (cls or ("mk mk-" + key), v["px"], v["px"], inner))


def favicon_uri(ink, paper, src_dir=None):
    """The tab icon. A favicon has no document to inherit from, so currentColor
    has no meaning there and the ink is baked, which is the one place on this
    site where a mark carries a colour of its own."""
    v = VARIANTS["favicon"]
    inner = variant_body("favicon", src_dir).replace('"', "'")
    return ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
            "<rect width='64' height='64' fill='%s'/>"
            "<g fill='none' stroke='%s' stroke-linecap='round' stroke-linejoin='round'>%s</g></svg>"
            % (ink.replace("#", "%23"), paper.replace("#", "%23"), inner))


def grid(src_dir=None):
    """The square the marks are authored on, read from their viewBox rather
    than assumed: every stroke rule on the site divides by it."""
    sizes = set()
    for name in FILES:
        path = os.path.join(src_dir or SRC, FILES[name])
        if not os.path.exists(path):
            continue
        m = re.search(r'viewBox="0 0 (\d+) (\d+)"', open(path, encoding="utf-8").read())
        if m:
            sizes.add((int(m.group(1)), int(m.group(2))))
    return sizes.pop()[0] if len(sizes) == 1 else 0


def facts(src_dir=None):
    """What the pages may say about the marks, computed from the files they are
    drawn from: the element count of each mark, and for each surface the
    elements it draws, the factor on every stroke, and the width in device
    pixels of its thinnest stroke at the size it is drawn."""
    out = {"marks": {}, "variants": {}, "elements": 0, "grid": grid(src_dir)}
    for name in FILES:
        els = parse(name, src_dir)
        out["marks"][name] = {"elements": len(els),
                              "ids": [e["id"] for e in els],
                              "strokes": sorted({float(e["attrs"]["stroke-width"])
                                                 for e in els if "stroke-width" in e["attrs"]})}
        out["elements"] += len(els)
    for key, v in VARIANTS.items():
        els = parse(v["mark"], src_dir)
        kept = [e for e in els if v["keep"] is None or e["id"] in v["keep"]]
        ws = [float(e["attrs"]["stroke-width"]) * v["scale"] for e in kept if "stroke-width" in e["attrs"]]
        out["variants"][key] = {
            "mark": v["mark"], "px": v["px"], "scale": v["scale"],
            "drawn": len(kept), "of": len(els),
            "unknown": [i for i in (v["keep"] or ()) if i not in {e["id"] for e in els}],
            # the specimen's rule: rendered weight is stroke x size / 64
            "thinnest_px": round(min(ws) * v["px"] / 64.0, 3) if ws else None,
        }
        ins = v.get("inspect")
        if ins:
            ik = [e for e in els if e["id"] in ins["keep"]]
            iw = [float(e["attrs"]["stroke-width"]) * ins["scale"]
                  for e in ik if "stroke-width" in e["attrs"]]
            out["variants"][key]["inspect"] = {
                "drawn": len(ik), "scale": ins["scale"],
                "unknown": [i for i in ins["keep"] if i not in {e["id"] for e in els}],
                "thinnest_px": round(min(iw) * v["px"] / 64.0, 3) if iw else None,
            }
    return out


# ---------------------------------------------------------------------------
# The package's own specification sheet, and what the shipped paths carry.
# The sheet is a claim about the files; these are the readings that test it,
# each computed from the geometry rather than copied from the sheet. Where a
# reading and the sheet disagree, the site draws the file.
def _num(v):
    return float(v)

def _points(d):
    """Every point a path names, walked command by command, so a path written
    with H, V or C is read as the geometry it draws rather than as a flat list
    of numbers."""
    toks = re.findall(r"[MmLlHhVvCcZz]|-?\d+(?:\.\d+)?", d)
    pts, i, x, y, cmd = [], 0, 0.0, 0.0, None
    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t; i += 1
            if cmd in "Zz":
                continue
        n = lambda k: float(toks[i + k])
        if cmd in "ML":
            x, y = n(0), n(1); i += 2
        elif cmd in "ml":
            x, y = x + n(0), y + n(1); i += 2
        elif cmd == "H":
            x = n(0); i += 1
        elif cmd == "h":
            x = x + n(0); i += 1
        elif cmd == "V":
            y = n(0); i += 1
        elif cmd == "v":
            y = y + n(0); i += 1
        elif cmd in "Cc":
            rel = cmd == "c"
            for k in (0, 2, 4):
                px, py = (x + n(k), y + n(k + 1)) if rel else (n(k), n(k + 1))
                pts.append((px, py))
            x, y = pts[-1]; i += 6
            continue
        else:
            i += 1
            continue
        pts.append((x, y))
    return pts

def _xs(d):
    return [p[0] for p in _points(d)]

def _ys(d):
    return [p[1] for p in _points(d)]

def _by(els, eid):
    return next(e for e in els if e["id"] == eid)

def _readings(src_dir=None):
    m = parse("monogram", src_dir); d = parse("delta", src_dir); t = parse("datum", src_dir)
    if not (m and d and t):
        return []          # nothing to read against when a source file is gone
    A = _by(m, "A#1")["attrs"]["d"]
    bowl = _by(m, "R bowl#1")["attrs"]["d"]
    rules = [_by(d, "Ledger baseline#1"), _by(d, "Ledger baseline#2")]
    return [
        ("monogram", "primary stroke", 1.5, _num(_by(m, "A#1")["attrs"]["stroke-width"])),
        ("monogram", "secondary stroke", 0.75, _num(_by(m, "Central datum#1")["attrs"]["stroke-width"])),
        ("monogram", "A base", 40, max(_xs(A)) - min(_xs(A))),
        ("monogram", "central datum x", 32, min(_xs(_by(m, "Central datum#1")["attrs"]["d"]))),
        ("monogram", "construction circle radius", 28, _num(_by(m, "Construction circle#1")["attrs"]["r"])),
        # the sheet says 15; the bowl spans 18 units of height, so half of it is 9
        ("monogram", "R bowl radius", 15, round((max(_ys(bowl)) - min(_ys(bowl))) / 2.0, 3)),
        ("delta", "apex x", 32, _xs(_by(d, "Delta / verification frame#1")["attrs"]["d"])[0]),
        ("delta", "apex y", 6, _ys(_by(d, "Delta / verification frame#1")["attrs"]["d"])[0]),
        ("delta", "main node radius", 4, _num(_by(d, "Precision node#1")["attrs"]["r"])),
        ("delta", "endpoint node radius", 2, _num(_by(d, "Endpoint verification nodes#1")["attrs"]["r"])),
        # the sheet says 2; the two rules sit at y 52 and y 56
        ("delta", "ledger rule spacing", 2, abs(_ys(rules[1]["attrs"]["d"])[0] - _ys(rules[0]["attrs"]["d"])[0])),
        ("datum", "outer radius", 28, _num(_by(t, "Polar rings#1")["attrs"]["r"])),
        ("datum", "inner radii", "22, 16, 8",
         ", ".join(("%g" % _num(_by(t, "Polar rings#%d" % i)["attrs"]["r"])) for i in (2, 3, 4))),
        ("datum", "north pole y", 4, _num(_by(t, "North Pole observer#1")["attrs"]["cy"])),
        ("datum", "pole marker radius", 2.5, _num(_by(t, "North Pole observer#1")["attrs"]["r"])),
        # the sheet intends divisions every 15 degrees; four axes draw them every 45
        ("datum", "angular divisions", 15, 360.0 / (2 * sum(1 for e in t if e["id"].startswith("Longitude axes")))),
    ]


def audit(src_dir=None):
    """The sheet against the files: how many of its stated values the paths
    carry, and which they do not."""
    rows = []
    for mark, label, claimed, read in _readings(src_dir):
        same = (("%g" % claimed) if isinstance(claimed, (int, float)) else str(claimed)) == \
               (("%g" % read) if isinstance(read, (int, float)) else str(read))
        rows.append({"mark": mark, "label": label, "claimed": claimed, "read": read, "carried": same})
    return {"rows": rows, "n": len(rows),
            "carried": sum(1 for r in rows if r["carried"]),
            "diverged": [r for r in rows if not r["carried"]]}


# ------------------------------------------------------------------ glyphs --
# Six forensic marks on one 24 unit grid at stroke 1.25, drawn whole rather
# than reduced: at every size the site uses them the authored stroke already
# clears a device pixel, so there is nothing to take away.
GLYPH_DIR = "glyphs"
GLYPH_TAGS = ("circle", "path", "rect")
GLYPHS = {
    "source":   ("01_source.svg", "Source",
                 "Three intake streams converge on one node. Nothing enters the record unlabelled."),
    "evidence": ("02_evidence.svg", "Evidence",
                 "A plotted observation carrying its own interval. The point is never shown without it."),
    "method":   ("03_method.svg", "Method",
                 "Input, a declared transfer, output. The diagonal is the stated rule, not a decoration."),
    "tested":   ("04_tested.svg", "Tested",
                 "A specimen loaded between two platens until a failure plane opens. The claim was attacked, not asserted."),
    "linked":   ("05_linked.svg", "Linked",
                 "One passage cites another. The chord carries direction, so a reader can walk the claim back to its source."),
    "verified": ("06_verified.svg", "Verified",
                 "Two scales at different pitch, five against four. Exactly one pair of graduations coincides, and that coincidence is the reading."),
}
# The two sizes the site draws them at. A glyph in the statement's column head
# stands beside four numbers on a 390px phone and takes the smaller one; every
# other placement has the room for the size the sheet proves.
GLYPH_SIZES = {"head": 20, "band": 24}


def glyph_path(key, src_dir=None):
    return os.path.join(src_dir or SRC, GLYPH_DIR, GLYPHS[key][0])


def glyph_parse(key, src_dir=None):
    return read(glyph_path(key, src_dir), GLYPH_TAGS, by_tag=True)


def glyph_grid(key, src_dir=None):
    path = glyph_path(key, src_dir)
    if not os.path.exists(path):
        return 0
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', open(path, encoding="utf-8").read())
    return int(m.group(1)) if m else 0


def glyph_body(key, src_dir=None):
    """The glyph's elements verbatim: no factor, because none is needed."""
    parts = []
    for e in glyph_parse(key, src_dir):
        a = e["attrs"]
        order = ("cx", "cy", "r", "x", "y", "width", "height", "d", "stroke-width", "fill", "stroke")
        parts.append("<%s %s/>" % (e["tag"], " ".join('%s="%s"' % (k, a[k]) for k in order if k in a)))
    return "".join(parts)


def glyph_svg(key, size="band", cls=None, src_dir=None):
    px = GLYPH_SIZES[size]
    g = glyph_grid(key, src_dir) or 24
    return ('<svg class="%s" viewBox="0 0 %d %d" width="%d" height="%d" fill="none" '
            'stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true" focusable="false">%s</svg>'
            % (cls or ("gl gl-" + key), g, g, px, px, glyph_body(key, src_dir)))


def glyph_facts(src_dir=None):
    """Per glyph: the grid it is authored on, its elements, its authored stroke,
    and what that stroke renders as at each size the site draws it."""
    out = {"n": len(GLYPHS), "sizes": dict(GLYPH_SIZES), "glyphs": {}, "elements": 0,
           "grid": 0, "stroke": 0.0, "missing": []}
    grids, strokes = set(), set()
    for key in GLYPHS:
        if not os.path.exists(glyph_path(key, src_dir)):
            out["missing"].append(GLYPHS[key][0])
            continue
        els = glyph_parse(key, src_dir)
        g = glyph_grid(key, src_dir)
        # the stroke lives on the root element of each glyph, not on its paths
        raw = open(glyph_path(key, src_dir), encoding="utf-8").read()
        sw = float(re.search(r'stroke-width="([\d.]+)"', raw).group(1))
        grids.add(g); strokes.add(sw)
        out["glyphs"][key] = {"file": GLYPHS[key][0], "label": GLYPHS[key][1],
                              "means": GLYPHS[key][2], "elements": len(els),
                              "ids": [e["id"] for e in els], "grid": g, "stroke": sw}
        out["elements"] += len(els)
    out["grid"] = grids.pop() if len(grids) == 1 else 0
    out["stroke"] = strokes.pop() if len(strokes) == 1 else 0.0
    if out["grid"] and out["stroke"]:
        out["rendered"] = {k: round(out["stroke"] * px / out["grid"], 3)
                           for k, px in GLYPH_SIZES.items()}
        out["printed"] = {k: round(v, 2) for k, v in out["rendered"].items()}
    else:
        out["rendered"] = {}
        out["printed"] = {}
    return out


# -------------------------------------------------------------------- seal --
# The institutional seal: the polar datum's discipline applied to a medallion,
# with the monogram at its centre and the type band on a real arc. Drawn at its
# own grid so every stated coordinate is one device pixel, which leaves its
# finest ring under an edge; that ring is dropped and the rest lifted by one
# factor, the same rule every other surface follows.
SEAL_FILE = "04_institutional_audit_seal.svg"
SEAL_PX = 128
SEAL_SCALE = 1.5
SEAL_DROP = 0.5          # the stroke width no size on this site can hold
SEAL_ARC_ID = "mk-seal-arc"


def seal_path(src_dir=None):
    return os.path.join(src_dir or SRC, SEAL_FILE)


def _fmt(w):
    return ("%.4f" % w).rstrip("0").rstrip(".")


def seal_inner(src_dir=None):
    """The seal's own markup, with three stated changes and no others: the
    element whose stroke no size can hold is removed, every remaining stroke is
    multiplied by one factor, and the one internal id is namespaced so the mark
    can stand on a page that has ids of its own."""
    path = seal_path(src_dir)
    if not os.path.exists(path):
        return ""
    raw = open(path, encoding="utf-8").read()
    inner = raw[raw.index(">", raw.index("<svg")) + 1: raw.rindex("</svg>")]
    inner = re.sub(r"<!--.*?-->", "", inner, flags=re.S)
    inner = re.sub(r'<[a-z]+\b[^>]*stroke-width="%s"[^>]*/>' % re.escape(str(SEAL_DROP)), "", inner)
    inner = re.sub(r'stroke-width="([\d.]+)"',
                   lambda m: 'stroke-width="%s"' % _fmt(float(m.group(1)) * SEAL_SCALE), inner)
    inner = inner.replace("seal-arc-seal", SEAL_ARC_ID)
    return re.sub(r">\s+<", "><", re.sub(r"\s+", " ", inner)).strip()


def seal_svg(cls="sl sl-seal", src_dir=None):
    return ('<svg class="%s" viewBox="0 0 %d %d" width="%d" height="%d" fill="none" '
            'stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true" focusable="false">%s</svg>'
            % (cls, SEAL_PX, SEAL_PX, SEAL_PX, SEAL_PX, seal_inner(src_dir)))


def seal_facts(src_dir=None):
    """The seal read off its own file: the grid, the rings it draws, how many
    stations sit around the calibration band and how far apart, the words the
    type band carries, and what its finest line renders as."""
    path = seal_path(src_dir)
    if not os.path.exists(path):
        return {"missing": SEAL_FILE}
    raw = open(path, encoding="utf-8").read()
    grid = int(re.search(r'viewBox="0 0 (\d+)', raw).group(1))
    els = read(path, ("circle", "path"), by_tag=True)
    c = grid / 2.0

    def sw(e):
        return float(e["attrs"].get("stroke-width", 0))

    def polar(e):
        x, y = _points(e["attrs"]["d"])[0]
        return math.hypot(x - c, y - c), round(math.degrees(math.atan2(x - c, c - y)) % 360, 3)

    drawn = [e for e in els if sw(e) != SEAL_DROP]
    rings = sorted({float(e["attrs"]["r"]) for e in drawn
                    if e["tag"] == "circle" and e["attrs"].get("stroke") != "none"}, reverse=True)
    # a station on the calibration band is either a fine tick or a cardinal
    # rule; the north station is the observer, which is a filled node instead
    band = sorted(polar(e)[1] for e in drawn
                  if e["tag"] == "path" and sw(e) == 0.7 and polar(e)[0] > rings[0] - 10)
    cardinal = sorted(polar(e)[1] for e in drawn
                      if e["tag"] == "path" and sw(e) == 1.4 and polar(e)[0] > rings[0] - 10)
    obs = [e for e in drawn if e["tag"] == "circle" and e["attrs"].get("fill") == "currentColor"
           and float(e["attrs"]["cy"]) < c - rings[0] + 10]
    stations = sorted(band + cardinal + [0.0] * len(obs))
    steps = sorted({round(b - a, 3) for a, b in zip(stations, stations[1:])})
    kept = [sw(e) for e in drawn if "stroke-width" in e["attrs"]]
    m = re.search(r"<textPath[^>]*>(.*?)</textPath>", raw, re.S)
    band_text = html_unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else ""
    return {
        "grid": grid, "px": SEAL_PX, "scale": SEAL_SCALE,
        "elements": len(els), "drawn": len(drawn), "dropped": len(els) - len(drawn),
        "rings": rings, "ticks": len(band), "cardinals": len(cardinal),
        "observers": len(obs), "stations": len(stations),
        "step": steps[0] if len(steps) == 1 else 0,
        "type": band_text,
        "authored_thinnest": min(kept) if kept else 0,
        "thinnest_px": round(min(kept) * SEAL_SCALE * SEAL_PX / grid, 3) if kept else 0,
    }


# ---------------------------------------------------------------- callouts --
# Fifteen dimensions, each read off a vertex or an arc boundary of the shipped
# path data rather than copied from the sheet. The colophon prints the reading
# and the coordinates it came from, so a reader can check the drawing against
# the file without trusting either.
def _anchors(d):
    """The points a path actually passes through. A cubic names two control
    points before its endpoint, and a control point is not a place on the
    drawing, so a dimension read off one would be a dimension of nothing."""
    toks = re.findall(r"[MmLlHhVvCcZz]|-?\d+(?:\.\d+)?", d)
    out, keep, i, cmd = _points(d), [], 0, None
    idx = 0
    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t; i += 1
            if cmd in "Zz":
                continue
        if cmd in "MmLl":
            keep.append(out[idx]); idx += 1; i += 2
        elif cmd in "HhVv":
            keep.append(out[idx]); idx += 1; i += 1
        elif cmd in "Cc":
            keep.append(out[idx + 2]); idx += 3; i += 6
        else:
            i += 1
    return keep


def _P(els, eid):
    return _anchors(_by(els, eid)["attrs"]["d"])


def _c2(p):
    return "%g, %g" % (round(p[0], 3), round(p[1], 3))


def callouts(src_dir=None):
    m = parse("monogram", src_dir)
    t = parse("datum", src_dir)
    if not (m and t):
        return []
    out = []

    def row(mark, label, value, coords, read_from, kind):
        out.append({"mark": mark, "label": label, "value": value, "coords": coords,
                    "from": read_from, "check": kind})

    # --- the monogram, eight readings
    dat = _P(m, "Central datum#1")
    row("monogram", "%g" % (dat[1][1] - dat[0][1]), dat[1][1] - dat[0][1],
        "%s and %s" % (_c2(dat[0]), _c2(dat[1])),
        "central datum, %s" % _by(m, "Central datum#1")["attrs"]["d"], "path vertex")
    cc = _by(m, "Construction circle#1")["attrs"]
    cr, cx, cy = float(cc["r"]), float(cc["cx"]), float(cc["cy"])
    row("monogram", "R%g" % cr, cr, "%s and %s" % (_c2((cx, cy)), _c2((cx + cr, cy))),
        "construction circle centre to its rightmost boundary", "circle centre")
    A = _P(m, "A#1")
    apex = min(A, key=lambda p: p[1])
    feet = sorted([p for p in A if p[1] == max(q[1] for q in A)])
    row("monogram", "APEX y%g" % apex[1], apex[1], _c2(apex),
        "A apex, %s" % _by(m, "A#1")["attrs"]["d"], "path vertex")
    row("monogram", "BASE y%g" % feet[0][1], feet[0][1], _c2(feet[0]),
        "A left foot, %s" % _by(m, "A#1")["attrs"]["d"], "path vertex")
    row("monogram", "%g" % (feet[-1][0] - feet[0][0]), feet[-1][0] - feet[0][0],
        "%s and %s" % (_c2(feet[0]), _c2(feet[-1])), "A left foot to A right foot", "path vertex")
    bar = _P(m, "A#2")
    row("monogram", "%g" % (bar[-1][0] - bar[0][0]), bar[-1][0] - bar[0][0],
        "%s and %s" % (_c2(bar[0]), _c2(bar[-1])),
        "crossbar, %s" % _by(m, "A#2")["attrs"]["d"], "path vertex")
    bowl = _P(m, "R bowl#1")
    top, bot = min(p[1] for p in bowl), max(p[1] for p in bowl)
    right = max(p[0] for p in bowl if p[1] in (top, bot))
    row("monogram", "%g" % (bot - top), bot - top,
        "%s and %s" % (_c2((right, top)), _c2((right, bot))),
        "R bowl entry and exit, %s" % _by(m, "R bowl#1")["attrs"]["d"], "path vertex")
    tick = _P(m, "Verification ticks#2")
    row("monogram", "%g" % (tick[-1][0] - tick[0][0]), tick[-1][0] - tick[0][0],
        "%s and %s" % (_c2(tick[0]), _c2(tick[-1])),
        "left verification tick, %s" % _by(m, "Verification ticks#2")["attrs"]["d"], "path vertex")

    # --- the polar datum, seven readings
    for i, name in ((1, "outer ring"), (2, "second ring"), (3, "third ring")):
        a = _by(t, "Polar rings#%d" % i)["attrs"]
        r, x, y = float(a["r"]), float(a["cx"]), float(a["cy"])
        row("datum", "dia %g" % (2 * r), 2 * r,
            "%s and %s" % (_c2((x - r, y)), _c2((x + r, y))),
            "%s, r %g about %s" % (name, r, _c2((x, y))), "arc r%g" % r)
    pole = _by(t, "North Pole observer#1")["attrs"]
    px_, py_, pr = float(pole["cx"]), float(pole["cy"]), float(pole["r"])
    ring = float(_by(t, "Polar rings#1")["attrs"]["r"])
    cy2 = float(_by(t, "Polar rings#1")["attrs"]["cy"])
    row("datum", "%g" % (cy2 - py_), cy2 - py_, "%s and %s" % (_c2((px_, py_)), _c2((px_, cy2))),
        "north pole centre to field centre", "arc r%g" % ring)
    ax = _P(t, "Longitude axes#1")
    row("datum", "%g" % (ax[-1][1] - ax[0][1]), ax[-1][1] - ax[0][1],
        "%s and %s" % (_c2(ax[0]), _c2(ax[-1])),
        "vertical longitude axis, %s" % _by(t, "Longitude axes#1")["attrs"]["d"], "path vertex")
    row("datum", "dia %g" % (2 * pr), 2 * pr, _c2((px_ + pr, py_)),
        "north pole observer, r %g about %s" % (pr, _c2((px_, py_))), "arc r%g" % pr)
    au = _by(t, "Author datum#1")["attrs"]
    ar, ax_, ay_ = float(au["r"]), float(au["cx"]), float(au["cy"])
    row("datum", "dia %g" % (2 * ar), 2 * ar, _c2((ax_ + ar, ay_)),
        "author datum, r %g about %s" % (ar, _c2((ax_, ay_))), "arc r%g" % ar)
    return out


def callout_numbers(src_dir=None):
    """Every numeral the callout ledger prints, as values, so the numeral scan
    knows each one was computed here."""
    vals = []
    for c in callouts(src_dir):
        vals.append(c["value"])
        for part in (c["label"], c["coords"], c["from"], c["check"]):
            vals += [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", part)]
    return vals
