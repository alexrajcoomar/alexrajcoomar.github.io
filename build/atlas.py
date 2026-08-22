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
    # The site footer is part of each converted document's own markup, not an
    # injected block, so it survived every other filter and put three of its
    # column headings — the owner's name, "Sections", "This site" — on the
    # sphere as if they were passages. They were the most-shared "headings" in
    # the corpus, carried by nineteen documents, and they sat at a mean
    # position that means nothing. A footer is furniture wherever it lives.
    t = re.sub(r"<footer\b[^>]*>.*?</footer>", "", t, flags=re.S | re.I)
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
        # which documents actually carry a shared heading. The merged point
        # keeps only one slug, so without this the relationship the placement
        # encodes is not recoverable from the placement.
        if len(shared[key]) > 1:
            placed[-1]["o"] = sorted(shared[key])

    regions = [{"s": p["slug"], "t": p["t"], "u": p["url"], "k": p["k"],
                "c": p.get("c") or "", "surface": p["surface"],
                "d": p.get("d", ""),
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


def edges(out_dir, pieces):
    """Real links between documents: every <a> in a document's own text whose
    target is another document on this site. The chrome is stripped first with
    the same filter the harvest uses, and the injected pill besides, so
    navigation the build wrote can never masquerade as a reference. What
    remains is a link a reader could click in the prose itself. Directed,
    deduped, and computed here at build time, so the sphere can only draw a
    chord the corpus actually records."""
    by_file = {p["url"]: p["slug"] for p in pieces
               if p["url"].endswith(".html") and "/" not in p["url"]}
    out = set()
    for p in pieces:
        if p["url"] not in by_file:
            continue
        path = os.path.join(out_dir, p["url"])
        if not os.path.exists(path):
            continue
        t = _readable(open(path, encoding="utf-8", errors="ignore").read())
        t = re.sub(r"<!--__rbp-->.*?<!--/__rbp-->", "", t, flags=re.S)
        for href in re.findall(r'<a\b[^>]*\bhref="([^"#?]+\.html)', t):
            h = href.lstrip("./")
            if h in by_file and by_file[h] != p["slug"]:
                out.add((p["slug"], by_file[h]))
    return sorted(out)


# ------------------------------------------------------------------ facts --
# The six wall labels are written at build time, from the same placement pass
# that draws the sphere, so a label cannot quote a number the picture does not
# show. Deriving them here rather than in the browser also means a reader with
# no JavaScript gets the whole argument as prose, and the page costs nothing at
# runtime to say it.

def _ang(a, b):
    d = max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))
    return math.degrees(math.acos(d))


def _esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def facts(points, regions):
    F = {}
    by = {r["s"]: r for r in regions}
    cnt = {}
    for p in points:
        cnt[p["s"]] = cnt.get(p["s"], 0) + 1

    F["total"] = len(points)
    F["docs"] = len(regions)
    # the six tool marks are catalogue titles placed whole, not harvested
    # headings, and their links carry no fragment. Label 01 has to say so or
    # it is false twice: once about what a mark is, once about where a click
    # lands. Both counts come from the data, not from a constant.
    F["toolN"] = sum(1 for p in points if "#" not in p["u"])
    F["headN"] = len(points) - F["toolN"]
    F["shared"] = sum(1 for p in points if p["n"] > 1)
    lv = {}
    for p in points:
        lv[p["l"]] = lv.get(p["l"], 0) + 1
    F["levels"] = lv

    # 1 — one mark, named. It has to read as a sentence somebody wrote, not as
    # a filing label, or the claim "one mark is one section" lands as a shrug.
    surf0 = {r["s"]: r["surface"] for r in regions}
    def _readable_score(p):
        t = p["t"]
        return (surf0.get(p["s"]) == "independent",
                24 <= len(t) <= 68,
                t.count(" ") >= 4,
                not t[0].isdigit(),
                p["l"] == 2,
                -abs(len(t) - 46))
    F["one"] = max((p for p in points if p["n"] == 1), key=_readable_score)
    F["oneDoc"] = by[F["one"]["s"]]["t"]

    # 1b — the flagship: the largest independent document, and one readable
    # mark inside it. The spotlight is the pass's own count, not taste.
    indregs = [r for r in regions if r["surface"] == "independent"]
    flag = max(indregs, key=lambda r: cnt.get(r["s"], 0))
    flagpts = [p for p in points if p["s"] == flag["s"]]
    F["flag"] = flag
    F["flagN"] = len(flagpts)
    F["flagCap"] = max(_ang(p["p"], flag["p"]) for p in flagpts)
    F["flagOne"] = max((p for p in flagpts if p["n"] == 1), key=_readable_score)

    # 1c — the corpus in one sentence: documents by surface, course marks
    sd = {}
    for r in regions:
        sd[r["surface"]] = sd.get(r["surface"], 0) + 1
    F["indD"] = sd.get("independent", 0)
    F["perD"] = sd.get("personal", 0)
    F["couD"] = sd.get("course", 0)
    F["couMarks"] = sum(1 for p in points if surf0.get(p["s"]) == "course")

    # 1d — where the camera looks first: the weighted centre of the
    # independent work, so the sphere's first face is the strongest one
    iv = [0.0, 0.0, 0.0]
    for p in points:
        if surf0.get(p["s"]) == "independent":
            for i in range(3):
                iv[i] += p["p"][i]
    F["homeC"] = [round(x, 4) for x in _norm(tuple(iv))]

    # 2 — the largest document, its cap, and what else falls inside it.
    # The count and the drawn circle have to be the same circle. Rounding the
    # radius for the prose and then counting against the unrounded one put
    # three marks in the annulus between what the label said and what the
    # reader could see, which is exactly the drift this page exists to refuse.
    big = max(regions, key=lambda r: cnt.get(r["s"], 0))
    bigpts = [p for p in points if p["s"] == big["s"]]
    cap = max(_ang(p["p"], big["p"]) for p in bigpts)
    inside = [p for p in points if p["s"] != big["s"] and _ang(p["p"], big["p"]) <= cap]
    F["big"] = big
    F["bigN"] = len(bigpts)
    F["capDeg"] = round(cap)
    F["capExact"] = round(cap, 3)
    F["overlapN"] = len(inside)
    F["overlapD"] = len({p["s"] for p in inside})

    # 3 — two documents that genuinely share headings.
    #
    # The first version of this picked its pair by geometry: any mark with a
    # share count above one that happened to fall between two centroids. That
    # is not the same question. It selected AFM 291 Property, Plant and
    # Equipment against AFM 291 Case Guide: AceSpin Inc. and said nineteen
    # headings appeared in both, when the true number was zero: all nineteen
    # were chapter-template headings belonging to seven other documents, which
    # merely landed nearby. The label and the picture agreed with each other
    # and both were wrong about the data.
    #
    # Co-occurrence is recorded, so it is read rather than inferred. Only
    # headings carried by exactly these two documents are counted, because
    # only those are placed at the midpoint of exactly these two centroids; a
    # heading in three documents sits at the mean of three and is not evidence
    # about any pair.
    co = {}
    for p in points:
        o = p.get("o")
        if not o:
            continue
        for i, a in enumerate(o):
            for b in o[i + 1:]:
                co.setdefault((a, b), []).append(p)

    best = None
    for (sa, sb), ps in co.items():
        a, b = by.get(sa), by.get(sb)
        if not a or not b:
            continue
        only = [p for p in ps if len(p.get("o") or []) == 2]
        if len(only) < 2:
            continue
        sep = _ang(a["p"], b["p"])
        # Closer than this and the two centroids are one blob, so "between
        # them" is not a place a reader can point at; further and an
        # orthographic camera cannot hold both on the near face at once.
        if sep < 25 or sep > 95:
            continue
        score = len(only) * (1.0 - abs(sep - 45) / 120.0)
        if best is None or score > best[0]:
            best = (score, a, b, sep, only, ps)
    if best:
        _, a, b, sep, only, allshared = best
        mid = _norm(tuple(a["p"][i] + b["p"][i] for i in range(3)))
        F["pairA"], F["pairB"] = a, b
        F["pairSep"] = round(sep)
        F["pairMids"] = only[:6]
        F["pairMidN"] = len(only)
        F["pairAllN"] = len(allshared)
        # the caps as measured, not as guessed: the renderer draws these
        F["pairCapA"] = round(max(_ang(p["p"], a["p"])
                                  for p in points if p["s"] == a["s"]), 3)
        F["pairCapB"] = round(max(_ang(p["p"], b["p"])
                                  for p in points if p["s"] == b["s"]), 3)
        F["pairMid"] = [round(x, 4) for x in mid]
        # how far the shared marks stray from the exact halfway point, which
        # is the number the drawn arc lets a reader check
        F["pairOff"] = round(max(_ang(p["p"], mid) for p in only))
        # The label wants to say "more than any other pair". That is only true
        # of the exclusive count, and only if it is a strict maximum, so it is
        # checked here rather than asserted. A corpus change that produced a
        # tie would drop the clause instead of publishing a falsehood.
        tops = sorted((len([q for q in v if len(q.get("o") or []) == 2])
                       for v in co.values()), reverse=True)
        F["pairTop"] = bool(len(tops) > 1 and tops[0] > tops[1]
                            and tops[0] == len(only))
    # 4 — where the encoding strains: the headings shared by the most documents
    maxn = max(p["n"] for p in points)
    knot = [p for p in points if p["n"] == maxn]
    if knot:
        k = [sum(p["p"][i] for p in knot) / len(knot) for i in range(3)]
        kc = _norm(tuple(k))
        # A merged point keeps one slug, so looking the owners up by slug found
        # exactly one document and the label then quoted a single distance as
        # though it held for all seven. The documents that carry a shared
        # heading are recorded on the point; read them.
        kslugs = sorted({o for p in knot for o in (p.get("o") or [p["s"]])})
        owners = [by[s2] for s2 in kslugs if s2 in by]
        ds = [_ang(r["p"], kc) for r in owners] or [0]
        F["knotN"] = len(knot)
        F["knotShare"] = maxn
        F["knotMin"], F["knotMax"] = round(min(ds)), round(max(ds))
        F["knotOwnerN"] = len(owners)
        F["knotNames"] = [p["t"] for p in knot[:3]]

    # 5 — the parallel that best separates independent work from everything else
    surf = {r["s"]: r["surface"] for r in regions}
    ind = [p for p in points if surf.get(p["s"]) == "independent"]
    bestf, besty = -1.0, 0.0
    y = -0.98
    while y <= 0.98:
        above = [p for p in points if p["p"][1] >= y]
        if above:
            hit = sum(1 for p in above if surf.get(p["s"]) == "independent")
            pr = hit / len(above)
            rc = hit / max(1, len(ind))
            f = (2 * pr * rc / (pr + rc)) if (pr + rc) else 0.0
            if f > bestf:
                bestf, besty = f, y
        y += 0.01
    above = [p for p in points if p["p"][1] >= besty]
    exc = [p for p in above if surf.get(p["s"]) != "independent"]
    ec = {}
    for p in exc:
        ec[p["s"]] = ec.get(p["s"], 0) + 1
    F["parY"] = round(besty, 2)
    F["parDeg"] = round(math.degrees(math.asin(besty)))
    F["indTotal"] = len(ind)
    F["nAbove"] = len(above)
    F["nIndAbove"] = len(above) - len(exc)
    F["nExc"] = len(exc)
    F["excDocs"] = len(ec)
    # The line has two kinds of error and the label used to report only one.
    # A boundary that names its false positives and hides its false negatives
    # is arguing rather than describing.
    F["indBelow"] = len(ind) - (len(above) - len(exc))
    F["excUrls"] = [p["u"] for p in exc]
    if ec:
        top = max(ec, key=lambda k2: ec[k2])
        F["excTop"] = by[top]["t"]
        F["excTopS"] = top
        F["excTopN"] = ec[top]

    # The small blob the renderer needs to stage each label. Points are keyed
    # by their href, which is unique, so the script never has to recompute any
    # of this and the prose and the picture cannot disagree.
    owners = sorted({o for p in knot for o in p.get("o", [p["s"]])}) if knot else []
    F["js"] = {
        # the exact cap, so the circle the reader counts against is the circle
        # the count was taken from
        "big": big["s"], "cap": F["capExact"],
        "pairA": (pa := F.get("pairA")) and pa["s"],
        "pairB": (pb := F.get("pairB")) and pb["s"],
        "pairCapA": F.get("pairCapA"), "pairCapB": F.get("pairCapB"),
        "pairMid": F.get("pairMid"),
        # only the headings carried by exactly these two documents: the ones
        # whose position really is a record of this pair
        "mids": [m["u"] for m in F.get("pairMids", [])],
        "knot": [p["u"] for p in knot],
        "knotOwners": owners,
        "knotC": [round(x, 4) for x in kc] if knot else [0, 0, 1],
        "parY": F["parY"],
        "flag": F["flag"]["s"],
        "flagCap": round(F["flagCap"], 2),
        "flagOne": F["flagOne"]["u"],
        "homeC": F["homeC"],
        # the marks above the line that are not independent work: the label
        # counts them, so the picture has to be able to point at them
        "exc": F.get("excUrls", []),
    }
    return F


# ------------------------------------------------------------------ labels --
# Six wall labels. Every number in them comes from facts(), which comes from
# the same placement pass that draws the sphere, so a label cannot quote a
# figure the picture does not show. Written out at build time so that a reader
# with no JavaScript still gets the whole argument as prose.

def _n(x):
    return "{:,}".format(x)


def labels(F):
    one = F["one"]
    big, pa, pb = F["big"], F["pairA"], F["pairB"]
    lv = F["levels"]
    return [
        {
            "id": "flagship",
            "title": "Start with the largest independent work.",
            "stage": "flag",
            "body": [
                "<b class=\"lw\" data-reg=\"{}\" tabindex=\"0\">{}</b> "
                "holds {} sections, the most of any independent "
                "work here, inside the drawn circle {}&deg; wide. Every "
                "section is a mark and every mark opens its passage, not the "
                "front of the piece: try <b>{}</b>, lit beside its name."
                .format(F["flag"]["s"], _esc(F["flag"]["t"]), _n(F["flagN"]),
                        round(F["flagCap"]), _esc(F["flagOne"]["t"])),
                "{} of the {} marks are headings somebody typed into a "
                "document; the other {} are whole tools, placed as one mark "
                "each, and a tool opens the tool. Size follows heading "
                "level, and nothing is sampled and nothing is capped."
                .format(_n(F["headN"]), _n(F["total"]), F["toolN"]),
            ],
        },
        {
            "id": "between",
            "title": "Two essays share a vocabulary.",
            "stage": "pair",
            "body": [
                "<i class=\"lw\" data-reg=\"{}\" tabindex=\"0\">{}</i> and "
                "<i class=\"lw\" data-reg=\"{}\" tabindex=\"0\">{}</i> are "
                "the closest pair on this sphere "
                "in the only sense it records: {} headings appear in these "
                "two documents and nowhere else{}. Their centroids sit "
                "{}&deg; apart, and the arc between them is drawn."
                .format(pa["s"], _esc(pa["t"]), pb["s"], _esc(pb["t"]),
                        _n(F["pairMidN"]),
                        ", more than any other pair here" if F.get("pairTop")
                        else "", F["pairSep"]),
                "Rather than being drawn twice, each of those {} headings is "
                "placed once, at the midpoint of the two: none sits more than "
                "{}&deg; off the halfway mark, the rest of the scatter being "
                "the same jitter every mark gets. Position is the only record "
                "of the overlap. There are no lines in this data, only places, "
                "and the arc here is a ruler rather than a link."
                .format(_n(F["pairMidN"]), F["pairOff"]),
            ],
        },
        {
            "id": "an-area",
            "title": "The coursework is the continent.",
            "stage": "big",
            "body": [
                "<span class=\"lw\" data-reg=\"{}\" tabindex=\"0\">{}</span> "
                "holds {} sections, more than any other document here, "
                "and its circle is drawn at the radius it was measured at: "
                "{}&deg;. Around it runs the course shelf, {} marks from {} "
                "documents, the reading that underwrites the rest."
                .format(big["s"], _esc(big["t"]), _n(F["bigN"]), F["capDeg"],
                        _n(F["couMarks"]), F["couD"]),
                "A document's area grows with what it holds, so the same "
                "circle around a short piece would be small. It also means "
                "areas run into each other: {} marks from {} other documents "
                "sit inside this one's circle. The sphere has two dimensions "
                "and the corpus does not, so overlap is the price, and it is "
                "shown rather than hidden."
                .format(_n(F["overlapN"]), F["overlapD"]),
            ],
        },
        {
            "id": "strain",
            "title": "Where the encoding strains.",
            "stage": "knot",
            "body": [
                "{} headings are carried by {} documents at once, the AFM 291 "
                "chapter template: {}, and the rest of the scaffolding every "
                "chapter is built on."
                .format(_n(F["knotN"]), F["knotShare"],
                        ", ".join("<i>%s</i>" % _esc(x) for x in F["knotNames"])),
                "Averaging {} positions strands them between {}&deg; and "
                "{}&deg; from the chapters that use them, which is to say "
                "nowhere near any of them. The dotted lines run to those {} "
                "chapters and are the only lines on this sphere: they measure "
                "a distance rather than assert a link. This is the honest "
                "failure of the method, and it is left visible."
                .format(F["knotShare"], F["knotMin"], F["knotMax"],
                        F["knotOwnerN"]),
            ],
        },
        {
            "id": "north",
            "title": "North is the independent work.",
            "stage": "north",
            "body": [
                "The hairline is the parallel at {}&deg;N. Above it sit {} "
                "marks, and {} of them are independent work: writing chosen, "
                "scoped and finished without a course asking for it."
                .format(F["parDeg"], _n(F["nAbove"]), _n(F["nIndAbove"])),
                "The line misses in both directions, and both are drawn. {} "
                "marks above it are ringed, because they come from {} "
                "documents that are not independent, {} of them from {}. "
                "Another {} independent marks sit below it. The arrangement is "
                "also inherited rather than designed: documents are laid out "
                "in the order the library lists them, so the sphere took a "
                "shelf order and the pattern followed."
                .format(F["nExc"], F["excDocs"], F["excTopN"],
                        "<span class=\"lw\" data-reg=\"%s\" tabindex=\"0\">%s</span>"
                        % (F["excTopS"], _esc(F["excTop"])), F["indBelow"]),
            ],
        },
        {
            "id": "yours",
            "title": "The rest is yours.",
            "stage": "free",
            "body": [
                "Drag the sphere to turn it. Point at any mark to read the "
                "section it names, and click to open that passage. Choose a "
                "document and the camera flies in; its sections are named on "
                "the sphere where they fit, and listed in full beside it "
                "either way.",
                "Everything is also a list: {} sections under {} documents, "
                "the same data, the same links, reachable from the keyboard, "
                "and the only version a page with no JavaScript can show."
                .format(_n(F["total"]), F["docs"]),
            ],
        },
    ]
