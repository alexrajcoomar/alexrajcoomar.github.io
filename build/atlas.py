"""The atlas: every section of every document, placed on a sphere.

Two passes, both mechanical.

harvest() reads each published piece, gives every section heading a stable id
if it does not already have one, and records the heading text, its anchor and
its document. Writing the ids is the part that makes the atlas clickable: a
point that cannot land on the passage it names is decoration, and half the
corpus, including the three largest essays, carried no anchors at all.

place() puts those sections on a unit sphere. Position is not decoration
either. Each document gets a centroid, the centroids are spread evenly by the
Fibonacci lattice so no region is arbitrarily crowded, and a document's
sections scatter around its own centroid inside a cap whose radius grows with
the square root of the section count. A dense patch on the globe is therefore
a dense document, which is the same contract the corpus figure makes when it
draws one square per five hundred words. A heading that appears in more than
one document is placed between their centroids rather than duplicated, so
proximity between two regions means the documents share language.

Nothing here is capped or sampled. Every section in every readable document is
on the globe.
"""

import html
import json
import math
import os
import re

# Headings that are page furniture rather than passages. Anything repeated
# this many times inside one document is furniture by construction, which is a
# rule rather than a list that has to be maintained by hand.
CHROME_REPEATS = 3
CHROME_WORDS = {
    "contents", "table of contents", "on this page", "in this section",
    "navigation", "menu", "search", "index", "jump to", "skip to content",
}

# Tools are applications. Their headings are controls, not passages, so a tool
# is represented by one point for the tool itself instead of a cloud of button
# labels.
ONE_POINT_KINDS = {"Tool"}

_HEAD = re.compile(r"<h([1-4])\b([^>]*)>(.*?)</h\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_ID = re.compile(r'\bid\s*=\s*"([^"]*)"')


def _text(inner):
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", inner))).strip()


def _slug(s, used):
    base = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "section"
    if base[0].isdigit():
        base = "s-" + base
    slug, n = base, 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used.add(slug)
    return slug


def _readable(text):
    """The document with its chrome removed: injected blocks, scripts, styles,
    and any navigation the piece carries of its own."""
    t = re.sub(r"<!--__rb-->.*?<!--/__rb-->", "", text, flags=re.S)
    t = re.sub(r"<!--__meta-->.*?<!--/__meta-->", "", t, flags=re.S)
    t = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", t, flags=re.S | re.I)
    t = re.sub(r"<nav\b[^>]*>.*?</nav>", "", t, flags=re.S | re.I)
    return t


def harvest(out_dir, pieces):
    """Give every section an anchor, and return the list of sections.

    Idempotent: an id already in the file is kept, so links handed out today
    still resolve after the next build. Only headings the build had to name
    itself are written, and a second run writes nothing.
    """
    sections, wrote = [], 0
    for p in pieces:
        path = os.path.join(out_dir, p["url"])
        if not os.path.exists(path):
            continue
        raw = open(path, encoding="utf-8", errors="ignore").read()
        body = _readable(raw)

        found = [(int(m.group(1)), m.group(2), _text(m.group(3)), m.span())
                 for m in _HEAD.finditer(body)]
        counts = {}
        for _, _, txt, _ in found:
            counts[txt.lower()] = counts.get(txt.lower(), 0) + 1

        if p["k"] in ONE_POINT_KINDS:
            sections.append({"t": p["t"], "url": p["url"], "id": "",
                             "slug": p["slug"], "lvl": 1})
            continue

        used = set(_ID.findall(raw))
        edits, seen = [], set()
        for lvl, attrs, txt, span in found:
            low = txt.lower()
            if (not txt or len(txt) < 3 or low in CHROME_WORDS
                    or counts[low] >= CHROME_REPEATS or low in seen):
                continue
            # the document's own title repeats the piece title; the centroid
            # already carries that name
            if lvl == 1 and low == p["t"].lower():
                continue
            seen.add(low)
            m = _ID.search(attrs)
            if m and m.group(1):
                anchor = m.group(1)
            else:
                anchor = _slug(txt, used)
                edits.append((body[span[0]:span[1]], lvl, anchor))
            sections.append({"t": txt, "url": p["url"], "id": anchor,
                             "slug": p["slug"], "lvl": lvl})

        if edits:
            for original, lvl, anchor in edits:
                fixed = re.sub(r"^<h%d\b" % lvl, '<h%d id="%s"' % (lvl, anchor),
                               original, count=1)
                raw = raw.replace(original, fixed, 1)
            os.chmod(path, 0o644)
            open(path, "w", encoding="utf-8").write(raw)
            wrote += 1
    return sections, wrote


# ------------------------------------------------------------------ place --
def _fib_sphere(n):
    """Evenly spread points, so no document lands in a crowd by accident."""
    pts, ga = [], math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        y = 1 - (i / float(max(1, n - 1))) * 2
        r = math.sqrt(max(0.0, 1 - y * y))
        th = ga * i
        pts.append((math.cos(th) * r, y, math.sin(th) * r))
    return pts


def _norm(v):
    m = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


def _rand(seed):
    """A small deterministic generator. The globe has to come out identical on
    every machine, or the build stops being reproducible and every rebuild
    shows a diff."""
    s = seed & 0xFFFFFFFF
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF


def place(sections, pieces):
    """Assign every section a point on the unit sphere."""
    order = [p for p in pieces if any(s["slug"] == p["slug"] for s in sections)]
    cents = dict(zip([p["slug"] for p in order], _fib_sphere(len(order))))

    by_slug = {}
    for s in sections:
        by_slug.setdefault(s["slug"], []).append(s)

    # a heading that occurs in several documents is one point, sitting between
    # the documents that share it
    shared = {}
    for s in sections:
        shared.setdefault(s["t"].lower(), set()).add(s["slug"])

    rnd = _rand(20260819)
    placed, done = [], set()
    for s in sections:
        key = s["t"].lower()
        if key in done and len(shared[key]) > 1:
            continue
        homes = [c for c in (cents.get(x) for x in shared[key]) if c]
        if not homes:
            continue
        cx = sum(h[0] for h in homes) / len(homes)
        cy = sum(h[1] for h in homes) / len(homes)
        cz = sum(h[2] for h in homes) / len(homes)
        centre = _norm((cx, cy, cz))

        # cap radius grows with the square root of the document's size, so the
        # area a document occupies is proportional to how much it holds
        n = len(by_slug.get(s["slug"], []))
        rad = min(0.62, 0.13 + 0.055 * math.sqrt(n))
        if len(shared[key]) > 1:
            rad *= 0.45

        # a random direction in the tangent plane, then a random arc along it
        a, b, c = next(rnd), next(rnd), next(rnd)
        tang = _norm((a - 0.5, b - 0.5, c - 0.5))
        dot = sum(tang[i] * centre[i] for i in range(3))
        tang = _norm(tuple(tang[i] - dot * centre[i] for i in range(3)))
        ang = rad * math.sqrt(next(rnd))
        v = _norm(tuple(centre[i] * math.cos(ang) + tang[i] * math.sin(ang)
                        for i in range(3)))

        done.add(key)
        placed.append({
            "t": s["t"],
            "u": s["url"] + ("#" + s["id"] if s["id"] else ""),
            "s": s["slug"],
            "l": s["lvl"],
            "n": len(shared[key]),
            "p": [round(v[0], 4), round(v[1], 4), round(v[2], 4)],
        })

    regions = [{"s": p["slug"], "t": p["t"], "u": p["url"], "k": p["k"],
                "c": p.get("c") or "", "surface": p["surface"],
                "p": [round(x, 4) for x in cents[p["slug"]]],
                "n": len([q for q in placed if q["s"] == p["slug"]])}
               for p in order]
    return placed, regions


def build(out_dir, pieces):
    """The page carries the data. Each section is rendered as a real link in a
    real list, with its coordinates on the element, and the globe reads that
    list rather than fetching a second copy. One source of truth, the page
    works with no JavaScript, a screen reader gets every section, and there is
    no separate asset that can drift out of step with the documents."""
    sections, wrote = harvest(out_dir, pieces)
    points, regions = place(sections, pieces)
    return {"points": points, "regions": regions}, wrote
