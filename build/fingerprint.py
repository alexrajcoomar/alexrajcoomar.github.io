# -*- coding: utf-8 -*-
"""One document, four measured values, one figure.

The generator reads only what the build already counted for that document:
its words, its figures, its tables, and the links its prose makes to other
documents on this site or that other documents make to it. Nothing is chosen
by hand and there is no random source, so the same document draws the same
figure on every build, and a figure that changes means a document changed.

The fourth input is a recorded link, not a citation. This site measures links
between its own documents, so that is what the chords count and that is what
the colophon calls them."""
import math

GRID = 64            # the square every mark on this site is authored on
LO, HI = 3.0, math.log10(50000)
W_MAX, N_MAX, C_MAX = 200000, 80, 60
R_MIN, R_SPAN = 12.0, 16.0
RING = 0.62          # the node ring, as a share of the outer radius
STRIDE = 0.382       # a chord's reach around the ring
NODE_R, OBS_R, DATUM_R = 1.1, 1.6, 1.0
# Authored stroke widths, thinnest first. A surface that draws the figure
# multiplies all four by one factor, exactly as a brand mark does.
STROKES = {"boundary": 1.0, "ray": 0.75, "chord": 0.5, "ring": 0.4}
# Where the figure is drawn, and the factor that lifts its finest line over one
# device pixel at that size (rendered weight is stroke x size / 64).
PLACES = {"row": {"px": 56, "scale": 2.9}}


def r3(n):
    return round(n * 1000) / 1000


def derive(words, figures, tables, links):
    """The four inputs, clamped, and everything the drawing needs from them."""
    W = max(1, min(W_MAX, int(round(words)) or 1))
    F = max(0, min(N_MAX, int(round(figures))))
    T = max(0, min(N_MAX, int(round(tables))))
    C = max(0, min(C_MAX, int(round(links))))
    t = min(1.0, max(0.0, (math.log10(W) - LO) / (HI - LO)))
    R = r3(R_MIN + R_SPAN * t)
    if F < 2:
        stride = 0
    else:
        k = max(1, int(round(F * STRIDE)))
        # every chord a diameter would draw the second half of the ring twice
        stride = k + 1 if 2 * k == F else k
    return {"W": W, "F": F, "T": T, "C": C, "t": r3(t), "R": R,
            "ring": r3(R * RING), "stride": stride,
            "rayStep": r3(360.0 / T) if T else 0,
            "nodeStep": r3(360.0 / F) if F else 0}


def _pt(r, deg):
    k = math.radians(deg)
    return r3(GRID / 2 + r * math.sin(k)), r3(GRID / 2 - r * math.cos(k))


def _w(name, scale):
    return ("%.4f" % (STROKES[name] * scale)).rstrip("0").rstrip(".")


def body(d, scale=1.0):
    """The figure as SVG, the layers in the order they are read: the boundary
    the words set, one ray per table, the ring the nodes stand on, one chord
    per recorded link, one node per figure, the observer on the boundary and
    the author's datum at the centre."""
    out = ['<circle cx="32" cy="32" r="%g" stroke-width="%s"/>' % (d["R"], _w("boundary", scale))]
    if d["T"]:
        seg = []
        for i in range(d["T"]):
            a = i * 360.0 / d["T"]
            p, q = _pt(d["R"] - 4, a), _pt(d["R"], a)
            seg.append("M%g %gL%g %g" % (p[0], p[1], q[0], q[1]))
        out.append('<path d="%s" stroke-width="%s"/>' % ("".join(seg), _w("ray", scale)))
    if d["F"]:
        out.append('<circle cx="32" cy="32" r="%g" stroke-width="%s"/>' % (d["ring"], _w("ring", scale)))
    if d["C"] and d["F"] >= 2:
        seg = []
        for i in range(d["C"]):
            a = int(round(i * d["F"] / d["C"])) % d["F"]
            b = (a + d["stride"]) % d["F"]
            p, q = _pt(d["ring"], a * 360.0 / d["F"]), _pt(d["ring"], b * 360.0 / d["F"])
            seg.append("M%g %gL%g %g" % (p[0], p[1], q[0], q[1]))
        out.append('<path d="%s" stroke-width="%s"/>' % ("".join(seg), _w("chord", scale)))
    if d["F"]:
        # r stays on every node: as a presentation attribute on the group it
        # would depend on SVG 2 geometry properties, which not every browser
        # that renders the rest of this figure correctly supports
        nodes = "".join('<circle cx="%g" cy="%g" r="%g"/>' % (_pt(d["ring"], i * 360.0 / d["F"]) + (NODE_R,))
                        for i in range(d["F"]))
        out.append('<g fill="currentColor" stroke="none">%s</g>' % nodes)
    out.append('<circle cx="32" cy="%g" r="%g" fill="currentColor" stroke="none"/>'
               % (r3(32 - d["R"]), OBS_R))
    out.append('<circle cx="32" cy="32" r="%g" fill="currentColor" stroke="none"/>' % DATUM_R)
    return "".join(out)


def svg(words, figures, tables, links, place="row", cls="fp"):
    p = PLACES[place]
    d = derive(words, figures, tables, links)
    return ('<svg class="%s" viewBox="0 0 %d %d" width="%d" height="%d" fill="none" '
            'stroke="currentColor" aria-hidden="true" focusable="false">%s</svg>'
            % (cls, GRID, GRID, p["px"], p["px"], body(d, p["scale"])))


def signature(d):
    """The four inputs and the three values they set, as one line."""
    return "W%d F%d T%d C%d %s R%.3f %s RING%.3f %s STRIDE%d" % (
        d["W"], d["F"], d["T"], d["C"], "·", d["R"], "·", d["ring"], "·", d["stride"])


def facts():
    """What a page may say about the figure: the rules, the sizes it is drawn
    at, and what the finest line of each renders as in device pixels."""
    out = {"grid": GRID, "strokes": dict(STROKES), "ring": RING, "stride": STRIDE,
           "r_min": R_MIN, "r_span": R_SPAN, "w_max": W_MAX, "places": {},
           # the two constants the rules quote: a full turn, and the word count
           # the radius saturates at
           "turn": 360, "w_hi": 50000}
    thin = min(STROKES.values())
    for k, p in PLACES.items():
        out["places"][k] = {"px": p["px"], "scale": p["scale"],
                            "thinnest_px": round(thin * p["scale"] * p["px"] / GRID, 3)}
    return out


RULES = (
    ("Outer radius", "R = 12 + 16t, t = (log10 W minus 3) / (log10 50000 minus 3)"),
    ("Calibration rays", "one per table, at 360 / T"),
    ("Node ring", "0.62 R"),
    ("Figure nodes", "one per figure, at 360 / F"),
    ("Chord stride", "round(0.382 F), plus one if that would be a diameter"),
    ("Link chords", "origin round(i F / C), target origin plus stride"),
)
