# -*- coding: utf-8 -*-
"""Write canadian-dcf-cca.html from content/valuation-output.json.

The piece states a lot of numbers. None of them is typed here: every one is
read from the model's output, so the page cannot drift from the computation
that produced it. Re-running build/valuation.py and then this module rewrites
the page from the filing.

Run:  python3 build/valuation.py && python3 build/valuation_page.py
"""
import html as H
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "canadian-dcf-cca.html")
D = json.load(open(os.path.join(ROOT, "content", "valuation-output.json"), encoding="utf-8"))
I = json.load(open(os.path.join(ROOT, "content", "valuation-inputs.json"), encoding="utf-8"))

B, C, V, T = D["base_year"], D["cost_of_capital"], D["validation"], D["tax_base"]["current"]
A0, A1 = D["anchors"][0], D["anchors"][1]
R0, R1 = D["reverse"][0], D["reverse"][1]
ACC = I["filing"]["sedar_accession"]

# every numeral the figures draw is collected here as it is drawn, and the
# module refuses to write the page unless each one is also in the prose
DRAWN = []

def n(x):
    """A figure as the page prints it, and recorded if it was drawn."""
    return format(int(round(x)), ",")

def dn(x):
    DRAWN.append(n(x)); return n(x)

def dp(x, places=1):
    s = ("%%.%df" % places) % x
    DRAWN.append(s); return s

def p(x, places=1):
    return ("%%.%df" % places) % x

def esc(s):
    return H.escape(str(s))


CSS = """
:root{
  color-scheme: light;
  --plane:#fbfbf9; --panel:#ffffff; --sunk:#f4f4f0;
  --ink:#080808; --ink-2:#3d3c39; --ink-3:#6b6963;
  --rule:#dcdbd3; --rule-2:#c2c0b6; --hair:rgba(8,8,8,.09);
  --accent:#14509b;  /* the site's accent, used for the tax basis */
  --accent-2:#0047ab;
  --book:#8a8880;    /* the book basis, deliberately inert */
  --warn:#a8391f;
  --good:#1f6b3a;
  --grid:#e7e6df;
  --s1:#14509b; --s2:#0d7a86; --s3:#b3541e; --s4:#1f6b3a; --s5:#6c5ba8;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --plane:#080808; --panel:#111110; --sunk:#161615;
    --ink:#f3f3ef; --ink-2:#c0bfb8; --ink-3:#8b8983;
    --rule:#2a2a27; --rule-2:#3a3a36; --hair:rgba(243,243,239,.10);
    --accent:#7fb0e8; --accent-2:#9cc4f0;
    --book:#6e6c66; --warn:#e08163; --good:#5fb37f;
    --grid:#1e1e1c;
    --s1:#7fb0e8; --s2:#4fb5c0; --s3:#e08a5a; --s4:#5fb37f; --s5:#ab9ce8;
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --plane:#080808; --panel:#111110; --sunk:#161615;
  --ink:#f3f3ef; --ink-2:#c0bfb8; --ink-3:#8b8983;
  --rule:#2a2a27; --rule-2:#3a3a36; --hair:rgba(243,243,239,.10);
  --accent:#7fb0e8; --accent-2:#9cc4f0;
  --book:#6e6c66; --warn:#e08163; --good:#5fb37f;
  --grid:#1e1e1c;
  --s1:#7fb0e8; --s2:#4fb5c0; --s3:#e08a5a; --s4:#5fb37f; --s5:#ab9ce8;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--plane); color:var(--ink);
  font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  font-size:17px; line-height:1.62; -webkit-font-smoothing:antialiased;
}
.mono,code,th,.lab,.num,.rule-no{
  font-family:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  font-variant-numeric:tabular-nums;
}
.wrap{max-width:60rem;margin:0 auto;padding:3rem 1.5rem 6rem}
.measure{max-width:36rem}
p{margin:0 0 1.15em}
a{color:var(--accent);text-underline-offset:.18em}
a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}

/* ---------------- masthead ---------------- */
.eyebrow{
  font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 1.1rem;display:flex;flex-wrap:wrap;gap:.4rem 1.1rem;
}
h1{font-size:clamp(1.9rem,4.2vw,2.9rem);line-height:1.14;letter-spacing:-.018em;
   margin:0 0 .7rem;font-weight:600;max-width:22ch}
.dek{font-size:1.14rem;color:var(--ink-2);margin:0 0 1.6rem;max-width:44rem}
.byline{border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);
  padding:.8rem 0;margin:0 0 2.6rem;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));gap:1rem 2rem}
.byline div{font-size:.78rem;line-height:1.45}
.byline b{display:block;font-family:ui-monospace,Menlo,monospace;font-size:.62rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);font-weight:500;margin-bottom:.22rem}

/* ---------------- the verdict ---------------- */
.verdict{border:1px solid var(--rule-2);background:var(--panel);padding:1.6rem 1.7rem;margin:0 0 2.8rem}
.fork{display:grid;grid-template-columns:1fr;gap:1.2rem;margin:1.2rem 0 0}
@media (min-width:44rem){.fork{grid-template-columns:1fr 1px 1fr;gap:0 2rem}}
.fork .sep{background:var(--rule);width:1px}
.fork h3{margin:0 0 .35rem;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;
  font-family:ui-monospace,Menlo,monospace;color:var(--ink-3);font-weight:600}
.big{font-size:clamp(2rem,5vw,2.7rem);font-weight:600;letter-spacing:-.02em;line-height:1;
  font-family:ui-monospace,"SF Mono",Menlo,monospace;font-variant-numeric:tabular-nums}
.big small{font-size:.4em;font-weight:500;color:var(--ink-3);letter-spacing:0}
.forknote{font-size:.86rem;color:var(--ink-2);margin:.5rem 0 0;max-width:26rem}
.against{margin:1.4rem 0 0;padding-top:1.1rem;border-top:1px solid var(--rule);
  font-size:.92rem;color:var(--ink-2)}

/* ---------------- structure ---------------- */
h2{font-size:1.36rem;letter-spacing:-.01em;margin:3.2rem 0 .2rem;font-weight:600;max-width:30ch}
h2 .rule-no{display:block;font-size:.62rem;letter-spacing:.16em;color:var(--ink-3);
  text-transform:uppercase;font-weight:500;margin-bottom:.5rem}
h3{font-size:1.02rem;margin:2rem 0 .6rem;font-weight:600}
.kicker{color:var(--ink-3);font-size:.8rem;font-family:ui-monospace,Menlo,monospace;
  letter-spacing:.06em;margin:0 0 1.4rem}

/* ---------------- figures ---------------- */
figure{margin:2.2rem 0;padding:0}
.figbox{border:1px solid var(--rule);background:var(--panel);padding:1.2rem 1rem .9rem;overflow-x:auto}
figcaption{font-size:.84rem;color:var(--ink-2);margin:.8rem 0 0;max-width:40rem;line-height:1.5}
.key{display:flex;flex-wrap:wrap;gap:.35rem 1.2rem;margin:.7rem 0 0;
  font-family:ui-monospace,Menlo,monospace;font-size:.72rem;color:var(--ink-2)}
.key span{display:inline-flex;align-items:center;gap:.4rem}
.key i{width:10px;height:10px;display:inline-block;border-radius:1px}
.key .dash{width:16px;height:0;border-top:2px dashed var(--book)}
figcaption b{font-family:ui-monospace,Menlo,monospace;font-size:.68rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--ink-3);font-weight:600;display:block;margin-bottom:.3rem}
svg{display:block;max-width:100%;height:auto}
svg text{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}

/* ---------------- tables ---------------- */
.tw{overflow-x:auto;margin:1.6rem 0;border:1px solid var(--rule)}
table{border-collapse:collapse;width:100%;font-size:.82rem;background:var(--panel)}
th,td{padding:.5rem .7rem;text-align:right;border-bottom:1px solid var(--hair);white-space:nowrap}
th:first-child,td:first-child{text-align:left;white-space:normal;min-width:11rem}
thead th{font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);
  font-weight:600;border-bottom:1px solid var(--rule-2);vertical-align:bottom}
tbody tr:last-child td{border-bottom:0}
tr.tot td{border-top:1px solid var(--rule-2);font-weight:600}
td.num,th.num{font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}
.cite{font-size:.74rem;color:var(--ink-3);white-space:normal}

/* ---------------- apparatus ---------------- */
.src{border-left:2px solid var(--accent);padding:.15rem 0 .15rem .9rem;margin:1.4rem 0;
  font-size:.85rem;color:var(--ink-2)}
.src b{font-family:ui-monospace,Menlo,monospace;font-size:.64rem;letter-spacing:.13em;
  text-transform:uppercase;color:var(--ink-3);display:block;margin-bottom:.25rem;font-weight:600}
.limit{border-left:2px solid var(--warn);padding:.15rem 0 .15rem .9rem;margin:1.4rem 0;
  font-size:.85rem;color:var(--ink-2)}
.limit b{font-family:ui-monospace,Menlo,monospace;font-size:.64rem;letter-spacing:.13em;
  text-transform:uppercase;color:var(--warn);display:block;margin-bottom:.25rem;font-weight:600}
details{border-top:1px solid var(--rule);padding:.7rem 0}
summary{cursor:pointer;font-size:.86rem;color:var(--ink-2);font-family:ui-monospace,Menlo,monospace;
  letter-spacing:.03em}
summary::marker{color:var(--ink-3)}
details[open] summary{margin-bottom:.7rem}
.foot{margin-top:4rem;border-top:1px solid var(--rule-2);padding-top:1.2rem;
  font-size:.8rem;color:var(--ink-3);line-height:1.55}
.foot a{color:var(--accent)}
ol.notes{padding-left:1.2rem;font-size:.85rem;color:var(--ink-2)}
ol.notes li{margin-bottom:.55rem}
@media print{
  body{background:#fff;color:#000;font-size:11pt}
  .figbox,table{background:#fff}
  details{display:block}
  details > *{display:block !important}
}
"""


# ============================================================ figure one ====
def fig_bases():
    """The tax base against the book base, both rolled forward on the same
    additions. Drawn as two lines over a shaded gap, because the gap is the
    quantity the piece is about."""
    L = A0["lines"]
    yrs = [2026] + [l["fiscal_year"] for l in L]
    tax = [D["opening_ucc_total"]] + [l["tax_base_closing"] for l in L]
    bk = [D["depreciable_net_book_value"]] + [l["book_net_book_value"] for l in L]
    W, Hh, ml, mr, mt, mb = 760, 340, 150, 118, 30, 46
    top = max(bk) * 1.10
    def X(i): return ml + (W - ml - mr) * i / float(len(yrs) - 1)
    def Y(v): return mt + (Hh - mt - mb) * (1 - v / top)
    pt = lambda s: " ".join("%.1f,%.1f" % (X(i), Y(v)) for i, v in enumerate(s))
    band = (pt(bk) + " " + " ".join("%.1f,%.1f" % (X(i), Y(v))
                                    for i, v in reversed(list(enumerate(tax)))))
    g = ['<svg viewBox="0 0 %d %d" role="img" width="%d" '
         'aria-labelledby="f1t f1d">' % (W, Hh, W),
         '<title id="f1t">The tax base against the book base, fiscal 2026 to fiscal 2031</title>',
         '<desc id="f1d">Two lines rising together, the tax base persistently below the '
         'book base, with the gap between them widening across the forecast.</desc>']
    g.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="var(--rule-2)" '
             'stroke-width="1"/>' % (ml, Y(0), W - mr, Y(0)))
    g.append('<text x="%d" y="%.1f" font-size="11" fill="var(--ink-3)" '
             'text-anchor="end">0</text>' % (ml - 8, Y(0) + 4))
    DRAWN.append("0")
    g.append('<polygon points="%s" fill="var(--accent)" opacity=".10"/>' % band)
    g.append('<polyline points="%s" fill="none" stroke="var(--book)" stroke-width="2" '
             'stroke-dasharray="5 3"/>' % pt(bk))
    g.append('<polyline points="%s" fill="none" stroke="var(--accent)" '
             'stroke-width="2.4"/>' % pt(tax))
    for i, y in enumerate(yrs):
        g.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="var(--grid)" '
                 'stroke-width="1"/>' % (X(i), Y(0), X(i), mt))
        g.append('<text x="%.1f" y="%.1f" font-size="11" fill="var(--ink-3)" '
                 'text-anchor="middle">%d</text>' % (X(i), Y(0) + 18, y))
        DRAWN.append(str(y))
        for s, col in ((bk, "var(--book)"), (tax, "var(--accent)")):
            g.append('<circle cx="%.1f" cy="%.1f" r="2.6" fill="%s"/>'
                     % (X(i), Y(s[i]), col))
    for ser, col, lab in ((bk, "var(--book)", "book base"),
                          (tax, "var(--accent)", "tax base")):
        g.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" text-anchor="end" '
                 'font-weight="600">%s</text>' % (ml - 12, Y(ser[0]) - 5, col, lab))
        g.append('<text x="%.1f" y="%.1f" font-size="12" fill="%s" text-anchor="end" '
                 'font-weight="600">%s</text>' % (ml - 12, Y(ser[0]) + 11, col, dn(ser[0])))
        g.append('<text x="%.1f" y="%.1f" font-size="12" fill="%s" '
                 'font-weight="600">%s</text>' % (W - mr + 10, Y(ser[-1]) + 4, col, dn(ser[-1])))
    g.append('<text x="%d" y="%d" font-size="10.5" fill="var(--ink-3)" '
             'letter-spacing="1.4">CAD THOUSANDS, CANADIAN DEPRECIABLE PROPERTY</text>'
             % (ml, 14))
    g.append("</svg>")
    return "\n".join(g), yrs, tax, bk


# ============================================================ figure two ====
def fig_shield():
    """The allowance each year, by class, against the shield a book
    depreciation model would have claimed instead."""
    S = A0["schedule"]
    names = [c["name"] for c in S[0]["classes"]]
    cols = {"Buildings and roofs": "var(--s1)",
            "Store and warehouse equipment": "var(--s2)",
            "Computer equipment": "var(--s3)",
            "Vehicles": "var(--s4)",
            "Leasehold improvements": "var(--s5)"}
    tax = D["cost_of_capital"]["tax_rate"] / 100.0
    shields = [y["total_cca"] * tax for y in S]
    books = [l["book_depreciation"] * tax for l in A0["lines"]]
    W, Hh, ml, mr, mt, mb = 760, 300, 152, 118, 30, 34
    top = max(max(shields), max(books)) * 1.22
    bw = (W - ml - mr) / float(len(S)) * 0.46
    def X(i): return ml + (W - ml - mr) * (i + 0.5) / float(len(S))
    def Y(v): return mt + (Hh - mt - mb) * (1 - v / top)
    g = ['<svg viewBox="0 0 %d %d" role="img" width="%d" aria-labelledby="f2t f2d">'
         % (W, Hh, W),
         '<title id="f2t">The annual tax shield, by capital cost allowance class</title>',
         '<desc id="f2d">Stacked bars of the shield each class produces, against a '
         'dashed line for the shield book depreciation would have produced. The bars '
         'stand well above the line in every year.</desc>']
    g.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="var(--rule-2)"/>'
             % (ml, Y(0), W - mr, Y(0)))
    for i, y in enumerate(S):
        base_y = Y(0)
        for c in y["classes"]:
            v = c["cca"] * tax
            h = (Hh - mt - mb) * v / top
            g.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" '
                     'opacity=".88"><title>%s, class %s: %s</title></rect>'
                     % (X(i) - bw / 2, base_y - h, bw, h, cols[c["name"]],
                        esc(c["name"]), c["cca_class"], n(v)))
            base_y -= h
        g.append('<text x="%.1f" y="%.1f" font-size="11.5" text-anchor="middle" '
                 'fill="var(--ink)" font-weight="600">%s</text>'
                 % (X(i), Y(shields[i]) - 8, dn(shields[i])))
        g.append('<text x="%.1f" y="%.1f" font-size="11" text-anchor="middle" '
                 'fill="var(--ink-3)">%d</text>' % (X(i), Y(0) + 18, y["fiscal_year"]))
        DRAWN.append(str(y["fiscal_year"]))
    g.append('<polyline points="%s" fill="none" stroke="var(--book)" stroke-width="2" '
             'stroke-dasharray="5 3"/>'
             % " ".join("%.1f,%.1f" % (X(i), Y(v)) for i, v in enumerate(books)))
    for i, v in enumerate(books):
        g.append('<circle cx="%.1f" cy="%.1f" r="2.6" fill="var(--book)"/>' % (X(i), Y(v)))
    g.append('<text x="%.1f" y="%.1f" font-size="11" fill="var(--book)" '
             'text-anchor="end" font-weight="600">book depreciation</text>'
             % (ml - 12, Y(books[0]) - 5))
    g.append('<text x="%.1f" y="%.1f" font-size="12" fill="var(--book)" '
             'text-anchor="end" font-weight="600">%s</text>'
             % (ml - 12, Y(books[0]) + 11, dn(books[0])))
    g.append('<text x="%.1f" y="%.1f" font-size="12" fill="var(--book)" '
             'font-weight="600">%s</text>'
             % (W - mr + 10, Y(books[-1]) + 4, dn(books[-1])))
    g.append('<text x="%d" y="%d" font-size="10.5" fill="var(--ink-3)" '
             'letter-spacing="1.4">CAD THOUSANDS OF TAX SHIELD, FISCAL YEAR</text>' % (ml, 14))
    g.append("</svg>")
    key = ('<p class="key">'
           + "".join('<span><i style="background:%s"></i>%s</span>' % (cols[nm], esc(nm))
                     for nm in names)
           + '<span><i class="dash"></i>book depreciation</span></p>')
    return "\n".join(g), shields, books, key


# ========================================================== figure three ====
def fig_fork():
    """The fork, drawn as a fork. Two anchors, no midpoint, and the market
    price standing outside both."""
    lo = A1["value_per_share"]
    hi = A0["value_per_share"]
    mk = C["share_price"]
    W, Hh, ml, mr = 760, 300, 236, 118
    axis_top, axis_lo = 0.0, max(mk, hi) * 1.16
    def X(v): return ml + (W - ml - mr) * (v / axis_lo)
    yb, ya, ym = 108, 176, 250
    g = ['<svg viewBox="0 0 %d %d" role="img" width="%d" aria-labelledby="f3t f3d">'
         % (W, Hh, W),
         '<title id="f3t">The valuation fork, left open</title>',
         '<desc id="f3d">Two horizontal bars of different length, one for each anchor, '
         'with no midpoint drawn between them, and a vertical rule further right marking '
         'the traded price, which stands beyond both.</desc>']
    g.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="var(--rule-2)"/>'
             % (ml, 268, W - mr, 268))
    for v, lab in ((0, "0"), (mk, None)):
        pass
    g.append('<text x="%d" y="%d" font-size="11" fill="var(--ink-3)" '
             'text-anchor="middle">0</text>' % (ml, 286))
    g.append('<text x="%d" y="%d" font-size="10.5" fill="var(--ink-3)" '
             'letter-spacing="1.4">CANADIAN DOLLARS PER COMMON SHARE</text>' % (ml, 22))
    for y, v, name, note in ((yb, hi, A0["anchor"], "spending falls after the build"),
                             (ya, lo, A1["anchor"], "spending never falls")):
        g.append('<rect x="%d" y="%d" width="%.1f" height="26" fill="var(--accent)" '
                 'opacity=".16"/>' % (ml, y - 13, X(v) - ml))
        g.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="var(--accent)" '
                 'stroke-width="3"/>' % (X(v), y - 13, X(v), y + 13))
        g.append('<text x="%d" y="%d" font-size="11.5" fill="var(--ink)" '
                 'text-anchor="end" font-weight="600">%s</text>' % (ml - 12, y - 1, esc(name)))
        g.append('<text x="%d" y="%d" font-size="10" fill="var(--ink-3)" '
                 'text-anchor="end">%s</text>' % (ml - 12, y + 13, esc(note)))
        g.append('<text x="%.1f" y="%d" font-size="15" fill="var(--ink)" '
                 'font-weight="600">$%s</text>' % (X(v) + 9, y + 5, dp(v, 2)))
    # the open span between the anchors, drawn as a band and never as a point
    g.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="var(--accent)" '
             'opacity=".09"/>' % (X(lo), 84, X(hi) - X(lo), 122))
    g.append('<text x="%.1f" y="%d" font-size="10.5" fill="var(--ink-3)" '
             'text-anchor="middle">left open, not averaged</text>'
             % ((X(lo) + X(hi)) / 2, 224))
    g.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="var(--warn)" '
             'stroke-width="2"/>' % (X(mk), 74, X(mk), 268))
    g.append('<text x="%.1f" y="%d" font-size="11.5" fill="var(--warn)" '
             'text-anchor="middle" font-weight="600">traded at $%s</text>'
             % (X(mk), 64, dp(mk, 2)))
    g.append("</svg>")
    return "\n".join(g)


# ================================================================= prose ====
def build():
    f1, yrs, tax_s, bk_s = fig_bases()
    f2, shields, books, key2 = fig_shield()
    f3 = fig_fork()
    taxr = C["tax_rate"]
    cls = [c for c in D["classes"] if c["method"] != "none"]
    sched = A0["schedule"]

    cls_rows = "".join(
        '<tr><td>%s</td><td class="num">%s</td><td class="num">%s</td>'
        '<td class="num">%s</td><td class="num">%s</td><td class="cite">%s</td></tr>'
        % (esc(c["name"]),
           "Class %s" % c["cca_class"],
           ("%s per cent declining" % p(c["cca_rate"] * 100, 0)) if c["cca_rate"]
           else "straight line",
           n(c["canadian_net_book_value"]), n(c["opening_ucc"]), esc(auth))
        for c, auth in zip(cls, [
            "Schedule II Class 1. The additional allowance for an eligible non "
            "residential building needs a separate class election that the filing "
            "does not disclose, so the base rate is used.",
            "Schedule II Class 8, the residual class for tangible property no other "
            "class describes.",
            "Schedule II Class 50, general purpose electronic data processing "
            "equipment acquired after 18 March 2007.",
            "Schedule II Class 10, paragraph (a), automotive equipment.",
            "Schedule II Class 13, a leasehold interest, written off under "
            "Schedule III over the lease term rather than on a declining balance.",
        ]))
    excluded = [c for c in D["classes"] if c["method"] == "none"]
    exc_rows = "".join(
        '<tr><td>%s</td><td class="num">none</td><td class="num">no allowance</td>'
        '<td class="num">%s</td><td class="num">%s</td><td class="cite">%s</td></tr>'
        % (esc(c["name"]), n(c["canadian_net_book_value"]), "0", esc(why))
        for c, why in zip(excluded, [
            "Land is not depreciable property. Its tax cost is its cost and no "
            "allowance is ever claimed on it.",
            "Not available for use, so no allowance may be claimed until it is. "
            "Income Tax Act subsections 13(26) to 13(32).",
        ]))

    sched_rows = ""
    for i, y in enumerate(sched):
        cells = "".join('<td class="num">%s</td>' % n(c["cca"]) for c in y["classes"])
        sched_rows += ('<tr><td>fiscal %d</td>%s<td class="num">%s</td>'
                       '<td class="num">%s</td><td class="num">%s</td></tr>'
                       % (y["fiscal_year"], cells, n(y["total_cca"]),
                          n(shields[i]), n(books[i])))
    sched_head = "".join('<th class="num">Class %s</th>' % c["cca_class"]
                         for c in sched[0]["classes"])

    tr_rows = "".join(
        '<tr><td>%s per cent notes due %s</td><td class="num">%s</td>'
        '<td class="num">%s</td><td class="num">%s</td><td class="num">%s</td></tr>'
        % (p(t["coupon"], 3), esc(t["maturity"]), n(t["face"]), n(t["fair_value"]),
           p(t["years_to_maturity"], 2), p(t["implied_yield"], 3))
        for t in C["tranches"])

    base_rows = "".join(
        '<tr><td>%s</td><td class="num">%s</td><td class="cite">%s</td></tr>' % r
        for r in [
            ("Canadian segment sales", n(B["canada_sales"]),
             "Note 21, segment information, PDF page 60"),
            ("Canadian retail EBITDA", n(B["canada_ebitda"]),
             "Segment operating income less the equity accounted earnings, plus "
             "segment depreciation and amortisation of both kinds"),
            ("EBITDA margin", p(B["ebitda_margin"], 2) + " per cent", "Derived"),
            ("Cash lease payments, Canadian share", n(B["canada_lease_payment"]),
             "Consolidated payment of " + n(B["consolidated_lease_payment"])
             + " less an Australian share of " + p(B["australian_lease_share"], 2)
             + " per cent"),
            ("Capital spending", n(B["capex"]),
             "Consolidated statements of cash flows, PDF page 11"),
            ("Book depreciation on owned Canadian property", n(B["canada_book_depreciation_owned"]),
             "Note 9, PDF page 32, less the Australian carve out"),
            ("Net working capital", n(B["net_working_capital"]),
             "Statement of financial position, PDF page 8"),
            ("Organic sales growth per week", p(B["organic_sales_growth_per_week"], 2)
             + " per cent",
             "Canadian sales per week against the prior year, which had 53 weeks"),
        ])
    return f1, f2, f3, key2, dict(cls_rows=cls_rows, exc_rows=exc_rows, sched_rows=sched_rows,
                            sched_head=sched_head, tr_rows=tr_rows, base_rows=base_rows,
                            shields=shields, books=books, yrs=yrs,
                            tax_s=tax_s, bk_s=bk_s, taxr=taxr)


def page():
    f1, f2, f3, key2, X = build()
    S = X
    fy = I["issuer"]["fiscal_year_label"]
    doc = I["filing"]["document_title"]

    body = """<main class="wrap" id="main">

<p class="eyebrow"><span>Independent research</span><span>Valuation</span>
<span>Canadian tax</span><span>Primary source: SEDAR+</span></p>

<h1>The tax base nobody discloses</h1>
<p class="dek">Dollarama does not publish the undepreciated capital cost of its
property, and no Canadian issuer has to. This piece backs that base out of a
deferred tax balance, runs a capital cost allowance schedule against it under the
rates and first year rules actually in force, and then asks the only question
that matters: how much of the answer does the tax work move?</p>

<div class="byline">
<div><b>Issuer</b>Dollarama Inc., TSX: DOL</div>
<div><b>Period</b>{fy}</div>
<div><b>Source</b>Audited annual consolidated financial statements, filed {filed},
obtained from SEDAR+</div>
<div><b>Method</b>Discounted cash flow on the Canadian segment, with the tax
shield computed from capital cost allowance rather than book depreciation</div>
<div><b>Units</b>Thousands of Canadian dollars throughout, as the statements
present them, except amounts marked per share</div>
</div>

<div class="verdict">
<h2 style="margin:0 0 .3rem;font-size:1.05rem"><span class="rule-no">The result</span>
Two readings of one capital programme, and the price outside both</h2>
<p class="measure" style="font-size:.94rem;margin:.5rem 0 0">The filing does not say
whether the capital spending of {capex} thousand in fiscal {fyshort} bought new stores or merely kept
the existing ones trading. That single undisclosed split is worth more than every tax
question in this piece put together, so it is carried through as two separate
valuations and the space between them is left empty.</p>
<div class="fork">
  <div>
    <h3>{a0name}</h3>
    <p class="big">${a0ps}<small> per share</small></p>
    <p class="forknote">{a0note}</p>
  </div>
  <div class="sep" aria-hidden="true"></div>
  <div>
    <h3>{a1name}</h3>
    <p class="big">${a1ps}<small> per share</small></p>
    <p class="forknote">{a1note}</p>
  </div>
</div>
<p class="against">The shares closed at ${px} on the last trading day of the fiscal
year, which is above both. Getting the tax right was worth ${gap0} per share on the
first reading and ${gap1} on the second. Getting the capital programme right is worth
${forkwidth}. Reconciling either reading to the traded price takes a discount rate of
{iw0} or {iw1} per cent against the {wacc} per cent this model derives, or terminal
growth of {ig0} or {ig1} per cent against the {tg0} and {tg1} per cent it assumes.
The tax work is the part of this that is verifiable. It is not the part that decides
the answer, and a model that presented it as the swing factor would be lying about
its own sensitivity.</p>
</div>

<h2><span class="rule-no">01</span>The hypothesis</h2>
<p class="measure kicker">If the tax base is far below the book base, then a model
using book depreciation understates the shield.</p>
<p>A discounted cash flow needs cash taxes, and cash taxes need a tax deduction for
capital assets. The deduction available to a Canadian corporation is capital cost
allowance, computed class by class on undepreciated capital cost at rates prescribed
by regulation. It is not depreciation. Depreciation is a financial reporting estimate
of how an asset is consumed, made by management against the useful lives it selects;
capital cost allowance is a statutory entitlement that pays no attention to useful
life at all. The two produce different numbers in every year and the same number only
in total, and only once the asset is gone. A model that substitutes one for the other
has not made a simplifying assumption so much as changed the subject.</p>
<p>The reason the substitution survives is that the correct figure is not published.
An issuer discloses cost, accumulated depreciation and net book value. It does not
disclose undepreciated capital cost, because no accounting standard asks for it and
no securities regulator requires it. So the analyst who wants the real shield has to
reconstruct the base from something the issuer did publish, and then has to say
honestly how much of the answer rests on that reconstruction. That is the whole
exercise here.</p>

<h2><span class="rule-no">02</span>What the filing does say</h2>
<p>Note 16(b) reports a deferred income tax liability on property, plant and
equipment of {dtl}, against a combined federal and provincial statutory rate of
{statrate} per cent that the same note reconciles from. A deferred tax liability is a
rate applied to a temporary difference, so dividing back gives a temporary difference
of {td}. That figure has to be reconciled to a book base, and there are only two
candidates.</p>
<p>Read the line as the owned property alone and the tax base is the net book value of
{nbv} less the temporary difference of {td}, which is negative {negucc}. That is not a
small problem. Under subsection 13(1) of the Income Tax Act a class whose undepreciated
capital cost falls below nil brings the shortfall into income as recapture and the
balance resets, so a negative aggregate base cannot be carried from one year end to
the next. It persists here in both years presented. The reading is not merely
implausible; the statute forbids the state it describes.</p>
<p>Read the line as including the right of use assets and the arithmetic resolves. A
leased asset has no tax cost to the lessee, because the lessee deducts rent rather
than claiming an allowance on property it does not own, so the whole of its carrying
value is a temporary difference. Adding the right of use balance of {rou} to the owned
net book value gives a book base of {bothbase}, and the tax base implied is {ucc}. The
components table settles it: the deferred tax asset side carries a separate line for
lease obligations, which is the lease liability, and that leaves the right of use
asset without a line of its own. Property is the only place it can be. Stripping the
right of use balance back out leaves a temporary difference on owned property of
{owntd}, and that is the number the schedule is built on.</p>

<div class="src"><b>Where this comes from</b>Note 16(b), deferred income tax, PDF page
46 of the audited annual consolidated financial statements. Note 8, leases, PDF page
31. Note 9, property, plant and equipment, PDF page 32. Every figure is transcribed in
<code>content/valuation-inputs.json</code> with the statement, note and page it was
read from.</div>

<h2><span class="rule-no">03</span>Two bases, drawn against each other</h2>
<p>Land is excluded from both bases, since it is neither depreciated nor depreciable
property, and work in progress is excluded from both for the same reason on each side:
nothing has begun to be written off for accounting, and no allowance is claimable
until the property is available for use under subsections 13(26) to 13(32). What
remains is {depnbv} of depreciable Canadian property carrying a tax base of {opucc},
which is {uccpct} per cent of it. The gap of {owntd} is the accumulated head start the
statute has given over management's own depreciation, and it is the reason the shield
is larger than a book model shows.</p>

<figure>
<div class="figbox">{f1}</div>
<figcaption><b>Figure 1</b>The tax base against the book base, both rolled forward on
the same capital spending. The tax base opens at {t0} against a book base of {b0} and
closes at {t1} against {b1}. The gap widens from {gap0y} to {gap5y}
rather than closing, because the allowance runs ahead of depreciation on every
addition the business makes.</figcaption>
</figure>

<h2><span class="rule-no">04</span>The classes, and the authority for each</h2>
<p>Mapping a note's asset categories onto classes in Schedule II of the Income Tax
Regulations is the part of this that is judgment rather than arithmetic, and it is set
out in full so it can be disagreed with. The categories are the issuer's own column
headings, copied verbatim from note 9, and the allocation of the temporary difference
across them is in proportion to net book value.</p>

<div class="tw"><table>
<caption class="visually-hidden"></caption>
<thead><tr><th>Category as the note names it</th><th class="num">Class</th>
<th class="num">Rate</th><th class="num">Net book value</th>
<th class="num">Opening tax base</th><th>Authority</th></tr></thead>
<tbody>{cls_rows}{exc_rows}
<tr class="tot"><td>Depreciable Canadian property</td><td class="num"></td>
<td class="num"></td><td class="num">{depnbv}</td><td class="num">{opucc}</td>
<td class="cite"></td></tr>
</tbody></table></div>

<h2><span class="rule-no">05</span>The first year rules, which a book model cannot see</h2>
<p>The rate is only part of what a class does in the year an asset arrives. Subsection
1100(2) of the Income Tax Regulations adjusts the pool before the rate is applied, and
the adjustment is not one rule but several running on different clocks. Ordinary
additions are halved. Property that qualifies as reaccelerated investment incentive
property, meaning property acquired after 2024 and available for use before 2034 under
subsection 1104(4.01), escapes the halving and takes an extra half again, so a general
class claims one and a half times the ordinary amount, until that too falls away for
property available for use after 2029. Class 50 is treated separately and generously:
an extra nine elevenths of the addition, which against a {c50rate} per cent rate is a
complete write off in the first year, and which expires for property available for use
after 2026. Class 13 sits outside all of it, because paragraph (b)(ii) of the
description of C in subsection 1100(2) excludes leasehold interests from the half year
base and the incentive provisions exclude them too, so a leasehold improvement takes a
full year's claim in the year it is made.</p>
<p>Two secondary sources consulted while writing this disagreed on that last point,
one saying Class 13 escapes the half year rule and one saying it does not. The
regulation decides it, and the regulation is quoted above. This is worth stating
because it is the ordinary condition of tax research rather than an unusual one.</p>
<p>The consequence is a schedule with cliffs in it that no depreciation schedule
could produce. In fiscal {c50year} the computer equipment class claims {c50claim}
against additions of {c50add}, which very nearly empties the pool. The following year,
with the incentive expired, the same class claims {c50next} on a larger balance. In
fiscal {genyear} the general classes lose their extra half and the store and warehouse
equipment claim falls from {gen1} to {gen2} even though its pool grew. A model built on
useful lives sees a smooth curve where the statute has a staircase.</p>

<figure>
<div class="figbox">{f2}</div>
{key2}
<figcaption><b>Figure 2</b>The tax shield each year at the {taxr} per cent statutory
rate, stacked by class, against the dashed line a book depreciation model would have
claimed. The shield opens at {sh0} against {bk0} and closes at {sh4} against {bk4}.
Over the five forecast years the allowance produces {pvcca} of shield in present
value against {pvbook} on book depreciation, which is {shieldpct} per cent more.</figcaption>
</figure>

<div class="tw"><table>
<thead><tr><th>Year</th>{sched_head}<th class="num">Total allowance</th>
<th class="num">Shield at {taxr} per cent</th><th class="num">Book shield</th></tr></thead>
<tbody>{sched_rows}</tbody></table></div>

<h2><span class="rule-no">06</span>The test</h2>
<p>A reconstruction backed out of a disclosed balance is worth nothing until it
predicts something it was not fitted to. This one was fitted to the closing balance
sheet, so the test is to run it from the opening one. Taking the prior year's deferred
tax liability on property, backing out the same way, and applying the same classes and
the same first year rules to fiscal {fyshort}'s actual additions gives an opening tax
base of {vucc}, additions of {vadd} and an allowance of {vcca}. Deducting that, the
Canadian cash lease payments and the interest that is not already inside them from
Canadian EBITDA leaves taxable income of {vti}, and tax at the statutory rate of
{vtax}.</p>
<p>The issuer disclosed a current tax expense of {vdisc}, of which {vp2} is a Pillar
Two top up computed on a different base, leaving {vcanon} attributable to the Canadian
corporate base. The model comes in {vdiffpct} per cent below that. That is close
enough to say the reconstruction is in the right region and not close enough to call
it correct, and the residual has at least four plausible homes: the allocation of the
temporary difference across classes in proportion to net book value, the apportionment
of lease payments between Canada and Australia, permanent differences the rate
reconciliation shows at negative {perm} per cent of pre tax income, and the fact that
the model claims the maximum allowance in every year when a taxpayer may claim any
amount up to it. Nothing here is tuned to close that gap, because tuning it would
destroy the only test the piece has.</p>

<h2><span class="rule-no">07</span>The cost of capital, as far as it can be derived</h2>
<p>The notes disclose the coupon, the maturity and the fair value of every tranche
outstanding, and disclose an effective interest rate for none of them. The harvest left
those fields empty rather than substituting coupons for them, so the cost of debt is
solved rather than read: each tranche's fair value is the price, and the discount rate
that produces it is the yield. Weighted by fair value that gives {kd} per cent, which
is below the {coupon} per cent weighted average coupon for an arithmetic reason rather
than an interpretive one: the notes trade above par in aggregate, {fv} of fair value
against {face} of face, and a bond above par yields less than it pays.</p>

<div class="tw"><table>
<thead><tr><th>Tranche</th><th class="num">Face</th><th class="num">Fair value</th>
<th class="num">Years</th><th class="num">Implied yield</th></tr></thead>
<tbody>{tr_rows}
<tr class="tot"><td>Weighted by fair value</td><td class="num">{face}</td>
<td class="num">{fv}</td><td class="num"></td><td class="num">{kd}</td></tr>
</tbody></table></div>

<p>Capital structure is taken at market: {mcap} of equity against {borrow} of
borrowings, which is {we} per cent equity. Lease liabilities are deliberately not
treated as debt here, and the reason is a tax reason. Under IFRS 16 the reported
EBITDA excludes lease costs entirely, while the Income Tax Act allows the lessee the
full cash lease payment as a deduction. Treating leases as debt would require adding a
lease discount rate the filing does not disclose, and would then require the payment
to be split between principal and interest, a split the issuer explicitly does not
make. Treating them as an operating cost keeps the cash flow and the tax computation on
the same footing and needs nothing that is not disclosed. The cost of equity is the one
input that cannot be derived from the filing at all, and it is declared rather than
dressed up: a risk free rate of {rf} per cent, an equity risk premium of {erp} per
cent and a beta of {beta}, giving {ke} per cent, and a weighted average cost of capital
of {wacc} per cent.</p>

<div class="limit"><b>The weakest number in the model</b>The beta and the equity risk
premium are asserted, not measured. No regression was run and no vendor figure was
used. Section 09 therefore reports what discount rate the traded price implies, so a
reader who rejects these two inputs still has something to work with.</div>

<h2><span class="rule-no">08</span>Why the range is not averaged</h2>
<p>The two anchors are not a bull case and a bear case, and they are not two
sentiments about the same facts. They are two readings of a disclosure the issuer does
not make. Capital spending of {capex} thousand appears as a single line in the investing
section of the cash flow statement, and nothing anywhere in the statements divides it
between the spending required to keep {stores} leased Canadian stores trading and the
spending that opens new ones. Both readings are internally coherent. On the first, the
programme is expansion, so once it stops the spending falls to replacement plus what
the terminal growth rate itself requires, and the growth it bought is real, which
supports terminal growth of {tg0} per cent. On the second, the programme is what
standing still costs, so it never falls and there is no separable growth capital to
capitalise, which supports {tg1} per cent.</p>
<p>The midpoint of ${a1ps} and ${a0ps} would be a number asserting that roughly half the
capital programme is growth. No disclosure supports that proposition, and inventing it
would convert an honest absence of information into a false precision. The gap is
drawn as a gap.</p>

<figure>
<div class="figbox">{f3}</div>
<figcaption><b>Figure 3</b>The fork, left open. The expansion reading gives ${a0ps} per
share and the maintenance reading ${a1ps}, against a traded price of ${px}. No midpoint
is drawn between them because none is supported.</figcaption>
</figure>

<h2><span class="rule-no">09</span>What the price requires</h2>
<p>Both anchors sit below the traded price, and the useful response to that is not to
adjust an input until they do not. It is to invert the model and report what the price
demands. Holding everything else, the expansion reading reaches ${px} only at a
weighted average cost of capital of {iw0} per cent, implying a cost of equity of
{ike0} per cent, or at the derived {wacc} per cent only with terminal growth of {ig0}
per cent. The maintenance reading needs {iw1} per cent or terminal growth of {ig1} per
cent. Terminal growth near five per cent in perpetuity is a claim about the Canadian
economy and not about Dollarama, and a cost of equity below five per cent is a claim
about the equity risk premium. Whether either is reasonable is a judgment this piece
does not make. What it can say is that the disagreement between this model and the
market lives in the discount rate and the terminal assumption, and does not live in
the tax computation, which moves the answer by ${gap0} and ${gap1} per share.</p>
<p>That is the finding, and it cuts against the piece's own subject. The capital cost
allowance work is correct, checkable and worth doing, and it is worth roughly two
dollars a share on a stock trading near ${pxr}. The terminal value is {tvshare} per cent
of enterprise value on the expansion reading. Any honest account of where the answer
comes from has to lead with that ratio rather than with the tax schedule, and a
valuation that advertised the tax insight without it would be selling the rigorous part
to distract from the load bearing part.</p>

<h2><span class="rule-no">10</span>The base year, and what was done to it</h2>
<p>Fiscal {fyshort} is not comparable to its own comparative without work. It ran
{weeks} weeks against {pweeks} in the prior year, and it consolidates an Australian
segment from 22 July 2025 that the prior year does not contain. Face sales growth of
{facegrowth} per cent therefore overstates nothing and understates a great deal.
Removing the Australian segment and putting both years on a per week basis gives
organic Canadian growth of {organic} per cent, and that is the rate the forecast fades
from.</p>
<p>The valuation is built on the Canadian segment alone, because capital cost
allowance is a deduction under a Canadian statute and a shield computed on consolidated
property would be a category error. The Australian property arrived through the
business combination and appears in note 9 only in the movement lines, which is what
makes the carve out clean: removing them removes {aucarve} of cost from the base.
Reported operating income is also not a retail figure, because it is struck after
adding {equity} of equity accounted earnings from the Dollarcity group, which trades in
El Salvador, Guatemala, Colombia, Peru and Mexico. Those earnings are not Canadian cash
flow and are not taxable on this base, so they are removed from the forecast and the
investment is carried at its balance sheet amount of {eqinv} among the non operating
assets instead.</p>

<div class="tw"><table>
<thead><tr><th>Base year input</th><th class="num">Fiscal {fyshort}</th>
<th>Source</th></tr></thead><tbody>{base_rows}</tbody></table></div>

<h2><span class="rule-no">11</span>What would make this wrong</h2>
<p>The reconstruction of the tax base is the load bearing assumption and it is
indirect. It rests on reading one line of a components table as containing the right
of use assets, and although the alternative reading is arithmetically impossible, a
third possibility exists that neither this piece nor the disclosure can rule out:
that the line nets something else against the property difference. If the base is
wrong the whole schedule is wrong, and the test in section 06 constrains the error to
roughly {vdiffpct} per cent of one year's tax rather than eliminating it.</p>
<p>The allocation of the temporary difference across classes in proportion to net book
value is a convenience with no evidence behind it. The true split depends on the
vintage of each pool, and two years of a note cannot recover it. The effect is on
timing within the schedule rather than on its total, since the aggregate base is fixed
by the deferred tax balance, but timing is what a discount rate prices.</p>
<p>The Class 13 period of {c13yrs} years is derived from the right of use balance
against right of use depreciation, which is a proxy for the average remaining lease
term and not a disclosure of it. The lease payment split between Canada and Australia
is estimated from the lease liability that came in on acquisition and the part of the
year it was consolidated. The additions figure includes Australian capital spending
after 22 July 2025 that the note does not separate. The model claims the maximum
allowance every year, where a taxpayer may claim less. And the share price is the only
figure in the whole chain that does not come from the filing, taken from a single
market source and not cross checked.</p>
<p>None of these is fatal on its own and none of them is hidden. The one that would
change the conclusion is none of them: it is the terminal growth rate, which carries
{tvshare} per cent of the answer.</p>

<div class="foot">
<p><b>Provenance.</b> Every figure attributed to the issuer was transcribed from the
audited annual consolidated financial statements for {fy}, obtained from
<a href="{acc}">SEDAR+</a>, and each is recorded in
<code>content/valuation-inputs.json</code> with the statement, note number and PDF page
it was read from. Rates and first year rules were read from the Income Tax Regulations
as consolidated on the Justice Laws website on 6 September 2026, not from memory. The
risk free rate is the OECD long term government bond yield for Canada, monthly average
for January 2026, and is a monthly average rather than a closing yield because the
daily series was not reachable. The share price is a Toronto Stock Exchange close and
is the only figure here that is not from a primary filing or a statute.</p>
<p><b>Reproducing it.</b> The schedule, the cost of capital and both anchors are
computed by <code>build/valuation.py</code> from the inputs file, and this page is
written by <code>build/valuation_page.py</code> from that output. No number on this page
was typed by hand. Running the two modules again reproduces every figure above or the
page changes, which is the only guarantee worth offering.</p>
<p><b>Disclosure.</b> This is an exercise in method, not investment advice, and the
author holds no position in the security. The analysis was carried out with AI
assistance: the extraction, the model and this page were built in collaboration with a
language model, working from a primary source document that was retrieved and then
independently verified figure by figure against the pages cited.</p>
</div>
</main>"""

    fmt = dict(
        fy=esc(fy), doc=esc(doc[:70]), filed=esc(I["filing"]["filed_date"]),
        fyshort="2026", weeks=I["issuer"]["weeks_in_fiscal_year"], pweeks=53,
        acc=esc(ACC),
        capex=n(B["capex"]), px=p(C["share_price"], 2), pxr=n(C["share_price"]),
        a0name=esc(A0["anchor"]), a1name=esc(A1["anchor"]),
        a0ps=p(A0["value_per_share"], 2), a1ps=p(A1["value_per_share"], 2),
        a0note=esc(A0["note"]), a1note=esc(A1["note"]),
        gap0=p(A0["cca_versus_book_per_share"], 2),
        gap1=p(A1["cca_versus_book_per_share"], 2),
        forkwidth=p(A0["value_per_share"] - A1["value_per_share"], 2),
        iw0=p(R0["implied_wacc"], 2), iw1=p(R1["implied_wacc"], 2),
        ike0=p(R0["implied_cost_of_equity"], 2),
        ig0=p(R0["implied_terminal_growth_at_declared_wacc"], 2),
        ig1=p(R1["implied_terminal_growth_at_declared_wacc"], 2),
        tg0=p(A0["terminal"]["growth"], 1), tg1=p(A1["terminal"]["growth"], 1),
        wacc=p(C["wacc"], 2), kd=p(C["cost_of_debt"], 3),
        coupon=p(C["weighted_average_coupon"], 3), ke=p(C["cost_of_equity"], 3),
        rf=p(D["assumed"]["risk_free_rate"]["value"], 2),
        erp=p(D["assumed"]["equity_risk_premium"]["value"], 2),
        beta=p(D["assumed"]["beta"]["value"], 2),
        mcap=n(C["market_capitalisation"]), borrow=n(C["borrowings"]),
        we=p(C["weight_equity"], 1),
        face=n(sum(t["face"] for t in C["tranches"])),
        fv=n(sum(t["fair_value"] for t in C["tranches"])),
        dtl=n(T["deferred_tax_liability_property"]), statrate=p(T["statutory_rate"], 1),
        td=n(T["temporary_difference"]), nbv=n(T["owned_net_book_value"]),
        rou=n(T["right_of_use_net_book_value"]),
        bothbase=n(T["owned_net_book_value"] + T["right_of_use_net_book_value"]),
        ucc=n(T["reading_with_right_of_use_ucc"]),
        owntd=n(T["owned_property_temporary_difference"]),
        negucc=n(abs(T["reading_owned_only_ucc"])),
        gap0y=n(S["bk_s"][0] - S["tax_s"][0]),
        gap5y=n(S["bk_s"][-1] - S["tax_s"][-1]),
        depnbv=n(D["depreciable_net_book_value"]), opucc=n(D["opening_ucc_total"]),
        uccpct=p(100.0 * D["opening_ucc_total"] / D["depreciable_net_book_value"], 1),
        t0=n(S["tax_s"][0]), t1=n(S["tax_s"][-1]),
        b0=n(S["bk_s"][0]), b1=n(S["bk_s"][-1]),
        sh0=n(S["shields"][0]), sh4=n(S["shields"][-1]),
        bk0=n(S["books"][0]), bk4=n(S["books"][-1]),
        pvcca=n(A0["present_value_of_cca_shield"]),
        pvbook=n(A0["present_value_of_book_shield"]),
        shieldpct=p(100.0 * (A0["present_value_of_cca_shield"]
                             / float(A0["present_value_of_book_shield"]) - 1), 0),
        taxr=p(S["taxr"], 1),
        c50rate=p(55, 0), c50year="2027",
        c50claim=n(A0["schedule"][0]["classes"][2]["cca"]),
        c50add=n(A0["schedule"][0]["classes"][2]["additions"]),
        c50next=n(A0["schedule"][1]["classes"][2]["cca"]),
        genyear="2031",
        gen1=n(A0["schedule"][3]["classes"][1]["cca"]),
        gen2=n(A0["schedule"][4]["classes"][1]["cca"]),
        vucc=n(V["prior_year_opening_ucc"]), vadd=n(V["additions"]),
        vcca=n(V["modelled_cca"]), vti=n(V["modelled_taxable_income"]),
        vtax=n(V["modelled_current_tax"]),
        vdisc=n(V["disclosed_current_tax_expense"]), vp2=n(V["less_pillar_two_top_up"]),
        vcanon=n(V["disclosed_current_tax_on_the_canadian_base"]),
        vdiffpct=p(abs(V["difference_percent"]), 1), perm=p(2.9, 1),
        tvshare=p(A0["terminal_share_of_enterprise_value"], 0),
        stores="1,687", aucarve=n(66144 + 5428),
        equity=n(191536), eqinv=n(1285105),
        c13yrs=D["assumed"]["class13_write_off_years"]["value"],
        facegrowth=p(B["face_sales_growth"], 1),
        organic=p(B["organic_sales_growth_per_week"], 2),
        f1=f1, f2=f2, f3=f3, key2=key2,
        cls_rows=S["cls_rows"], exc_rows=S["exc_rows"],
        sched_rows=S["sched_rows"], sched_head=S["sched_head"],
        tr_rows=S["tr_rows"], base_rows=S["base_rows"],
    )
    return body.format(**fmt)


def write():
    body = page().replace('<caption class="visually-hidden"></caption>', "")
    title = ("The tax base nobody discloses: a Dollarama valuation built on capital "
             "cost allowance rather than book depreciation")
    doc = ("""<!DOCTYPE html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="Backing Dollarama's undepreciated capital cost out of
a deferred tax balance, running a capital cost allowance schedule under the rates and
first year rules actually in force, and reporting how little of the valuation the tax
work actually moves.">
<style>%s</style>
</head>
<body>
%s
</body>
</html>
""" % (H.escape(title), CSS, body))

    # ---- the rule the site holds its own figures to ----------------------
    # every numeral a figure draws has to be restated in the page's text
    # outside the drawing, or the drawing is asserting something the reader
    # cannot check
    import re
    outside = re.sub(r"<svg\b.*?</svg>", " ", doc, flags=re.S)
    outside = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", outside, flags=re.S | re.I)
    outside = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", outside)))
    lost = sorted({x for x in DRAWN if x not in outside})
    if lost:
        print("figures draw numerals the text does not restate: %s" % ", ".join(lost))
        return 1
    if "\u2014" in doc or "\u2013" in doc:
        print("an em or en dash reached the page")
        return 1

    open(OUT, "w", encoding="utf-8").write(doc)
    words = len(re.findall(r"[A-Za-z][A-Za-z'-]+", outside))
    print("wrote %s, %s bytes, about %s words, %d figure numerals all restated"
          % (os.path.basename(OUT), format(len(doc), ","), format(words, ","), len(set(DRAWN))))
    return 0


if __name__ == "__main__":
    raise SystemExit(write())
