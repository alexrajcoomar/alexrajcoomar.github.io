# -*- coding: utf-8 -*-
"""The shipped brand marks, parsed, and the reductions the pages draw.

A mark drawn small is the same geometry as the mark drawn large: elements are
removed and every remaining stroke is multiplied by one stated factor. Nothing
is redrawn by hand, so a reduction cannot drift from its source."""
import os, re

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "marks")
FILES = {"monogram": "01_vernier_monogram_AR.svg",
         "delta": "02_forensic_audit_delta.svg",
         "datum": "03_polar_datum.svg"}
_AT = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')

def parse(name, src_dir=None):
    """Every drawn element, in document order, keyed by the comment that labels
    its group plus its ordinal in that group."""
    path = os.path.join(src_dir or SRC, FILES[name])
    if not os.path.exists(path):
        return []          # check 34 names the missing file; the build refuses there
    raw = open(path, encoding="utf-8").read()
    label, seen, out = "", {}, []
    for m in re.finditer(r"<!--(.*?)-->|<(circle|path)\b([^>]*?)/>", raw, re.S):
        if m.group(1) is not None:
            label = re.sub(r"\s+", " ", m.group(1)).strip()
            continue
        a = dict(_AT.findall(m.group(3)))
        if "d" in a:
            a["d"] = re.sub(r"\s+", " ", a["d"]).strip()
        seen[label] = seen.get(label, 0) + 1
        out.append({"id": "%s#%d" % (label, seen[label]), "tag": m.group(2), "attrs": a})
    return out

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
# What each surface draws, and the factor that lifts its thinnest stroke over
# one device pixel at the size it is drawn (rendered weight is stroke x size / 64).
VARIANTS = {
    "brand":    {"mark": "monogram", "keep": MONO_PRIMARY, "scale": 2.2, "px": 24},
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
    return ('<svg class="%s" viewBox="0 0 64 64" width="%d" height="%d" fill="none" '
            'stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true" focusable="false">%s</svg>'
            % (cls or ("mk mk-" + key), v["px"], v["px"], variant_body(key, src_dir)))


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
