# -*- coding: utf-8 -*-
"""Contrast of every category the Atlas key names, at the alpha atlas.js paints
it on the near face of the sphere, composited over the paper of each theme.
Run after any change to the palette or to draw(): the floor for a keyed
category is 3:1 (WCAG 1.4.11, a graphical object required to understand the
content). Prints a table; exits non-zero if any keyed category is under."""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
css = open(os.path.join(HERE, "..", "site.css"), encoding="utf-8").read()

def tokens(block):
    return dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", block))

light = tokens(re.search(r":root\{(.*?)\n\}", css, re.S).group(1))
dark = tokens(re.search(r':root\[data-theme="dark"\]\{(.*?)\}', css, re.S).group(1))

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def over(fg, a, bg):
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))

def lum(c):
    def ch(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def q48(a):
    """tone2() quantises alpha to 1/48ths before it paints."""
    return int(a * 48 + 0.5) / 48

# near-face alpha in draw(): a = (0.10 + 0.80 * t) * boost, t = 1 on the near face
A = 0.90
CATS = [
    ("Independent work", "accent", q48(A), True),
    ("Personal interest", "accent", q48(A * 0.85), True),
    ("Coursework, drawn as an outline", "ink-3", q48(min(1, A * 1.25)), True),
    ("Tools, one mark each", "tool", q48(A), True),
    ("Shared headings, stem and tip", "ref", q48(min(1, 0.30 + 0.55 + 0.15)), True),
    ("Search hits", "accent", q48(A), True),
    ("Passages opened, the ring", "ink", q48(0.55), True),
    ("Chords between linked documents", "ink", q48(0.55), True),
    ("Receded field at stop 01 (boost 1.05)", "edge", q48(min(1, A * 1.05)), True),
    ("Receded field at stop 02 (boost 0.55)", "edge", q48(A * 0.55), False),
    ("Everything else at stop 05 (boost 1.25)", "edge", q48(min(1, A * 1.25)), True),
]

worst = 99.0
rows = []
for name, tok, a, keyed in CATS:
    out = [name]
    for theme in (light, dark):
        paper = rgb(theme["paper"])
        c = contrast(over(rgb(theme[tok]), a, paper), paper)
        out.append("%.2f" % c)
        if keyed:
            worst = min(worst, c)
    out.append("keyed" if keyed else "context")
    rows.append(out)

print("%-42s %-6s %-6s %s" % ("category", "light", "dark", "role"))
for r in rows:
    print("%-42s %-6s %-6s %s" % tuple(r))
print("lowest keyed category: %.2f:1 (floor 3:1)" % worst)
sys.exit(0 if worst >= 3.0 else 1)
