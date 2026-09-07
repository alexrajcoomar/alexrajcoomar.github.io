# -*- coding: utf-8 -*-
"""Compile the markdown resumes into submission-ready PDF and DOCX.

One source, two renderers, one measurement. The markdown files under
applications/ are the only place the words live. This module parses them into
a small document model and hands that model to two independent renderers, an
HTML one that Chromium prints to PDF and a python-docx one that writes Word.
Neither renderer is allowed to invent content, so a claim can only reach a
submitted document by being in the markdown first.

The page budget is not a hope. After rendering, the PDF is measured: the page
objects are counted, and the browser is asked for the rendered content height
against the printable height of a Letter page at the declared margins. A file
that spills to a second page fails the build and says by how much, because a
two-page co-op resume that was meant to be one page is a defect the sender
cannot see in the file they attach.

The typeface is Times New Roman with Liberation Serif behind it. Liberation
Serif is metric-compatible with Times New Roman, so a machine that lacks the
Microsoft face sets the same text on the same metrics instead of substituting
something wider. Without that, the page-fit measurement taken here would be a
measurement of whatever font happened to be installed, and would not predict
what Word does on the machine the file is actually sent from.

Usage:  python3 applications/build_resumes.py [--only v1]
"""
import html as H
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "compiled")

# The three sources and the name each compiled file carries when it is
# attached to an application. The stem is what a recruiter sees in a download
# folder, so it names the person before it names the variant.
DOCS = [
    ("v1", "resume_v1_accounting_tax.md",        "Alex_Rajcoomar_Resume_V1_Tax"),
    ("v2", "resume_v2_assurance_forensics.md",   "Alex_Rajcoomar_Resume_V2_Assurance"),
    ("v3", "resume_v3_fpa_fintech_analytics.md", "Alex_Rajcoomar_Resume_V3_FPA"),
]

# Letter, in CSS pixels at 96 dpi, which is the unit Chromium lays out in.
PAGE_W_IN, PAGE_H_IN = 8.5, 11.0
MARGIN_IN = 0.55
PX = 96.0
PRINTABLE_H = (PAGE_H_IN - 2 * MARGIN_IN) * PX   # 950.4
PRINTABLE_W = (PAGE_W_IN - 2 * MARGIN_IN) * PX   # 748.8

# The brief fixes the typographic box: a classic serif, body at 10pt or
# 10.5pt, line spacing between 1.10 and 1.15. That box still has room in it,
# so rather than guessing one setting and hoping, the compiler walks the box
# from the most generous rung down and takes the first that measures onto one
# page in both renderers. The setting each document landed on is reported, so
# a document sitting on the last rung is visibly a document that needs cutting
# rather than one that quietly got away with it.
LADDER = [(10.5, 1.15), (10.5, 1.13), (10.5, 1.11), (10.5, 1.10),
          (10.0, 1.15), (10.0, 1.13), (10.0, 1.11), (10.0, 1.10)]
# Chromium and Word do not lay out identically, so a document that measures at
# exactly the page height in one will spill in the other. A rung is only
# accepted with this much room left.
SLACK_PX = 8.0

# Line spacing is the one setting where the two renderers mean different
# things by the same number. CSS line-height is a multiple of the font size.
# Word's "Multiple" is a multiple of the font's own natural line height, which
# for a Times-metric serif is about 1.15em, so Word's 1.10 is CSS 1.27 and a
# document set to the same figure in both comes out eleven per cent taller in
# Word. Measured here: 55 single lines of 10pt text at Word multiple 1.10 fill
# a page that arithmetic says holds 65. So neither renderer is given a
# multiple. Both are given the line height in points, computed once, and the
# ratio the brief asks for is then a true ratio of the body size.
HEAD_PT, HEAD_LEAD = 17.0, 18.5      # the name
CONTACT_PT, CONTACT_LEAD = 9.5, 11.0  # the one-line contact block
AVAIL_PT, AVAIL_LEAD = 9.5, 11.2      # the availability line
SECTION_LEAD = 1.15                   # section headings, as a ratio of body


def leading(body_pt, line_h):
    """The body line height in points, rounded to the twentieth of a point
    Word actually stores, so the two renderers are given the same number and
    not two roundings of it."""
    return round(body_pt * line_h * 20) / 20.0


# ---------------------------------------------------------------- parsing

def parse(md):
    """Markdown to a document model.

    The grammar is only as large as the resumes use: a title, a run of header
    lines, sections, and inside a section either an entry (one or two lines,
    each optionally carrying a right-hand field after a pipe) or a bullet.
    Anything the grammar does not recognise raises rather than being dropped,
    so a formatting mistake in the source is loud instead of invisible.
    """
    doc = {"name": "", "header": [], "sections": []}
    lines = md.replace("\r\n", "\n").split("\n")
    i, n = 0, len(lines)
    sec = None

    while i < n:
        raw = lines[i]
        line = raw.strip()
        i += 1
        if not line or line == "---":
            continue

        if line.startswith("# "):
            doc["name"] = line[2:].strip()
            continue

        if line.startswith("## "):
            sec = {"title": line[3:].strip(), "blocks": []}
            doc["sections"].append(sec)
            continue

        if sec is None:
            doc["header"].append(line)
            continue

        if line.startswith("- "):
            sec["blocks"].append({"kind": "bullet", "text": line[2:].strip()})
            continue

        # An entry line. Split on the last pipe so a pipe inside the left-hand
        # text (there is none today, but there could be) does not steal the
        # right-hand field.
        left, right = line, ""
        if " | " in line:
            left, right = line.rsplit(" | ", 1)
        blocks = sec["blocks"]
        if blocks and blocks[-1]["kind"] == "entry" and not blocks[-1].get("sub"):
            blocks[-1]["sub"] = left.strip()
            blocks[-1]["subright"] = right.strip()
        else:
            blocks.append({"kind": "entry", "main": left.strip(),
                           "mainright": right.strip()})
    return doc


_TOKEN = re.compile(r"\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*")


def runs(text):
    """Inline markdown to (text, bold, italic) runs. No nesting beyond the
    three forms the resumes use, which is checked by the regex rather than
    assumed: anything else stays literal."""
    out, pos = [], 0
    for m in _TOKEN.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], False, False))
        bi, b, i_ = m.group(1), m.group(2), m.group(3)
        if bi is not None:
            out.append((bi, True, True))
        elif b is not None:
            out.append((b, True, False))
        else:
            out.append((i_, False, True))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], False, False))
    return [r for r in out if r[0]]


def header_lines(doc):
    """The three-line header. The markdown carries the contact block over two
    lines because that is what reads well in a text editor; a printed resume
    wants it on one, so they are joined here rather than duplicated there."""
    contact = [l for l in doc["header"] if not (l.startswith("*") and l.endswith("*"))]
    subtitle = [l.strip("*") for l in doc["header"] if l.startswith("*") and l.endswith("*")]
    return doc["name"], " | ".join(contact), (subtitle[0] if subtitle else "")


# ---------------------------------------------------------------- HTML, PDF

CSS = """
@page { size: %(pw).2fin %(ph).2fin; margin: %(m).2fin; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: 'Times New Roman', 'Liberation Serif', 'Tinos', Times, serif;
  font-size: %(bodypt).2fpt;
  line-height: %(lead).2fpt;
  color: #000; background: #fff;
  width: %(pwin).3fin;
  -webkit-font-smoothing: antialiased;
}
.name {
  font-size: %(headpt).1fpt; font-weight: 700; letter-spacing: .035em;
  text-align: center; line-height: %(headlead).1fpt; margin: 0 0 2.5pt;
}
.contact, .avail { text-align: center; }
.contact { font-size: %(contactpt).1fpt; line-height: %(contactlead).1fpt;
           margin: 0 0 1pt; }
.avail { font-size: %(availpt).1fpt; line-height: %(availlead).1fpt;
         font-style: italic; margin: 0 0 3pt; }
h2 {
  font-size: %(bodypt).2fpt; font-weight: 700; letter-spacing: .09em;
  text-transform: uppercase; line-height: %(seclead).2fpt;
  margin: 5.2pt 0 2pt; padding: 0 0 1pt;
  border-bottom: .9pt solid #000;
}
h2:first-of-type { margin-top: 3pt; }
.entry { display: flex; justify-content: space-between; gap: 10pt; }
.entry .l { flex: 1 1 auto; }
.entry .r { flex: 0 0 auto; white-space: nowrap; }
.entry.sub { margin-bottom: .6pt; }
ul { margin: .8pt 0 2pt; padding-left: 11.5pt; }
li { margin: 0 0 1.15pt; padding-left: 1.5pt; }
li::marker { font-size: .85em; }
b, strong { font-weight: 700; }
i, em { font-style: italic; }
"""



def esc(text):
    return "".join(
        ("<b><i>%s</i></b>" if (b and i_) else "<b>%s</b>" if b else "<i>%s</i>" if i_ else "%s")
        % H.escape(t) for t, b, i_ in runs(text))


def to_html(doc, body_pt, line_h):
    name, contact, avail = header_lines(doc)
    css = CSS % {"pw": PAGE_W_IN, "ph": PAGE_H_IN, "m": MARGIN_IN,
                 "bodypt": body_pt, "lead": leading(body_pt, line_h),
                 "seclead": body_pt * SECTION_LEAD,
                 "headpt": HEAD_PT, "headlead": HEAD_LEAD,
                 "contactpt": CONTACT_PT, "contactlead": CONTACT_LEAD,
                 "availpt": AVAIL_PT, "availlead": AVAIL_LEAD,
                 "pwin": PAGE_W_IN - 2 * MARGIN_IN}
    p = ['<!doctype html><html><head><meta charset="utf-8">',
         "<title>%s</title><style>%s</style></head><body>" % (H.escape(name), css),
         '<div class="name">%s</div>' % H.escape(name),
         '<div class="contact">%s</div>' % H.escape(contact),
         '<div class="avail">%s</div>' % H.escape(avail)]
    for sec in doc["sections"]:
        p.append("<h2>%s</h2>" % H.escape(sec["title"]))
        openul = False
        for blk in sec["blocks"]:
            if blk["kind"] == "bullet":
                if not openul:
                    p.append("<ul>"); openul = True
                p.append("<li>%s</li>" % esc(blk["text"]))
                continue
            if openul:
                p.append("</ul>"); openul = False
            p.append('<div class="entry"><span class="l">%s</span>'
                     '<span class="r">%s</span></div>'
                     % (esc(blk["main"]), H.escape(blk.get("mainright", ""))))
            if blk.get("sub"):
                p.append('<div class="entry sub"><span class="l">%s</span>'
                         '<span class="r">%s</span></div>'
                         % (esc(blk["sub"]), H.escape(blk.get("subright", ""))))
        if openul:
            p.append("</ul>")
    p.append("</body></html>")
    return "\n".join(p)


NODE_PRINT = r"""
const { chromium } = require('playwright');
(async () => {
  const [htmlPath, pdfPath, printableH] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage();
  await pg.goto('file://' + htmlPath, { waitUntil: 'load' });
  await pg.emulateMedia({ media: 'print' });
  const h = await pg.evaluate(() => Math.max(
      document.body.scrollHeight, document.documentElement.scrollHeight));
  await pg.pdf({ path: pdfPath, printBackground: true,
                 preferCSSPageSize: true });
  await b.close();
  console.log(JSON.stringify({ contentPx: h, printablePx: Number(printableH) }));
})();
"""


def pdf_pages(path):
    """Page count, asked of poppler where it exists and read out of the file
    where it does not. The fallback is not a guess: Chromium and LibreOffice
    both write an uncompressed page tree, so /Type /Page objects can be
    counted directly, with the page tree's own /Count read as a second opinion.
    Keeping the fallback means this module still measures on a machine with no
    poppler installed, which is the machine most likely to run it."""
    try:
        r = subprocess.run(["pdfinfo", path], capture_output=True, text=True,
                           timeout=60)
        if r.returncode == 0:
            m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
            if m:
                n = int(m.group(1))
                return n, n
    except (OSError, subprocess.SubprocessError):
        pass
    raw = open(path, "rb").read()
    objs = len(re.findall(rb"/Type\s*/Page[^s]", raw))
    counts = [int(m.group(1)) for m in re.finditer(rb"/Type\s*/Pages.*?/Count\s+(\d+)", raw, re.S)]
    return objs, (max(counts) if counts else None)


def render_pdf(html, pdf_path):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as f:
        f.write(html); html_path = f.name
    # Node resolves modules from the script's own directory, and playwright
    # is installed at the repository root, so the printer is written there and
    # removed again rather than left in the tree.
    script = os.path.join(ROOT, ".resume_print.js")
    open(script, "w").write(NODE_PRINT)
    env = dict(os.environ)
    env.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    r = subprocess.run(["node", script, html_path, pdf_path, str(PRINTABLE_H)],
                       capture_output=True, text=True, cwd=ROOT, env=env)
    os.unlink(html_path)
    if os.path.exists(script):
        os.unlink(script)
    if r.returncode != 0:
        raise RuntimeError("chromium print failed:\n" + (r.stderr or r.stdout))
    return json.loads(r.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------- DOCX

def render_docx(doc, path, body_pt, line_h):
    from docx import Document
    from docx.enum.text import WD_TAB_ALIGNMENT, WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, Inches, RGBColor

    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(body_pt)
    st.font.color.rgb = RGBColor(0, 0, 0)
    # Word resolves East Asian and complex-script fonts separately; without
    # this the serif face silently reverts on some machines.
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), "Times New Roman")
    lead = Pt(leading(body_pt, line_h))
    pf = st.paragraph_format
    # A Length here writes w:lineRule="exact", which is the only rule that
    # means the same thing as a CSS line-height in points.
    pf.line_spacing = lead
    pf.space_before = Pt(0); pf.space_after = Pt(0)
    pf.widow_control = False

    s = d.sections[0]
    s.page_width, s.page_height = Inches(PAGE_W_IN), Inches(PAGE_H_IN)
    for side in ("top", "bottom", "left", "right"):
        setattr(s, side + "_margin", Inches(MARGIN_IN))
    right_tab = Inches(PAGE_W_IN - 2 * MARGIN_IN)

    def para(space_before=0, space_after=0, line=None):
        p = d.add_paragraph()
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = lead if line is None else line
        p.paragraph_format.widow_control = False
        return p

    def put(p, text, bold=None, italic=None, size=None):
        for t, b, i_ in runs(text):
            r = p.add_run(t)
            r.bold = b if bold is None else bold
            r.italic = i_ if italic is None else italic
            if size:
                r.font.size = Pt(size)
        return p

    def rule(p):
        """A section rule drawn as a paragraph bottom border, which is what
        Word itself uses, so the line survives editing rather than being a
        drawn object a reviewer can drag."""
        pPr = p._p.get_or_add_pPr()
        b = OxmlElement("w:pBdr"); bot = OxmlElement("w:bottom")
        bot.set(qn("w:val"), "single"); bot.set(qn("w:sz"), "7")
        bot.set(qn("w:space"), "1"); bot.set(qn("w:color"), "000000")
        b.append(bot); pPr.append(b)

    name, contact, avail = header_lines(doc)
    p = para(0, 1.2, Pt(HEAD_LEAD)); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(name); r.bold = True; r.font.size = Pt(HEAD_PT)
    p = para(0, 0.5, Pt(CONTACT_LEAD)); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(contact); r.font.size = Pt(CONTACT_PT)
    p = para(0, 2.0, Pt(AVAIL_LEAD)); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(avail); r.italic = True; r.font.size = Pt(AVAIL_PT)

    first = True
    for sec in doc["sections"]:
        p = para(3.0 if first else 5.2, 2.0, Pt(body_pt * SECTION_LEAD))
        first = False
        r = p.add_run(sec["title"]); r.bold = True; r.font.size = Pt(body_pt)
        rule(p)
        for blk in sec["blocks"]:
            if blk["kind"] == "bullet":
                # Word's built-in List Bullet style carries its own numbering
                # definition, indents and spacing, which no amount of
                # per-paragraph override fully cancels. A literal bullet on a
                # hanging indent is what the HTML renderer does, so it is what
                # this does, and the two then measure the same.
                bp = para(0, 1.15)
                fmt = bp.paragraph_format
                fmt.left_indent = Inches(0.16)
                fmt.first_line_indent = Inches(-0.16)
                bp.add_run("\u2022\t")
                fmt.tab_stops.add_tab_stop(Inches(0.16))
                put(bp, blk["text"])
                continue
            for key, rkey in (("main", "mainright"), ("sub", "subright")):
                if not blk.get(key):
                    continue
                ep = para(0, 0.6)
                ep.paragraph_format.tab_stops.add_tab_stop(
                    right_tab, WD_TAB_ALIGNMENT.RIGHT)
                put(ep, blk[key])
                if blk.get(rkey):
                    ep.add_run("\t" + blk[rkey])
    d.save(path)


def docx_pages(path):
    """Ask LibreOffice, which is the only thing here that lays out a .docx the
    way Word would. Counting paragraphs would not answer the question asked."""
    with tempfile.TemporaryDirectory() as td:
        prof = os.path.join(td, "loprofile")
        r = subprocess.run(
            ["soffice", "--headless", "--norestore", "--nolockcheck",
             "-env:UserInstallation=file://" + prof,
             "--convert-to", "pdf", "--outdir", td, path],
            capture_output=True, text=True, timeout=300)
        out = os.path.join(td, os.path.splitext(os.path.basename(path))[0] + ".pdf")
        if not os.path.exists(out):
            return None, (r.stderr or r.stdout)[-300:]
        return pdf_pages(out)[0], None


# ---------------------------------------------------------------- main

def fit(doc, pdf_path, docx_path):
    """Walk the permitted typographic box until the document measures onto one
    page in both renderers, and return the rung it landed on. Both are
    measured, because Chromium's layout is not Word's and only one of them is
    the file a recruiter opens."""
    tried = []
    for body_pt, line_h in LADDER:
        m = render_pdf(to_html(doc, body_pt, line_h), pdf_path)
        pages, declared = pdf_pages(pdf_path)
        room = PRINTABLE_H - m["contentPx"]
        if pages != 1 or (declared not in (1, None)) or room < SLACK_PX:
            tried.append((body_pt, line_h, "pdf", pages, m["contentPx"]))
            continue
        render_docx(doc, docx_path, body_pt, line_h)
        dpages, err = docx_pages(docx_path)
        if dpages == 1:
            return body_pt, line_h, m["contentPx"], dpages, tried
        tried.append((body_pt, line_h, "docx", dpages if dpages else "?",
                      m["contentPx"]))
    return None, None, None, None, tried


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    os.makedirs(OUT, exist_ok=True)
    rows, bad = [], []
    for key, src, stem in DOCS:
        if only and key != only:
            continue
        md = open(os.path.join(HERE, src), encoding="utf-8").read()
        doc = parse(md)
        for stray in ("\u2014", "\u2013"):
            if stray in md:
                bad.append("%s: an em or en dash reached the source" % src)

        pdf_path = os.path.join(OUT, stem + ".pdf")
        docx_path = os.path.join(OUT, stem + ".docx")
        body_pt, line_h, px, dpages, tried = fit(doc, pdf_path, docx_path)
        if body_pt is None:
            last = tried[-1]
            line_px = last[0] * last[1] * 96 / 72
            over = last[4] - (PRINTABLE_H - SLACK_PX)
            bad.append("%s: does not fit one page anywhere in the permitted "
                       "box. At the tightest rung (%.1fpt / %.2f) the %s "
                       "renderer laid it out on %s pages: %.0fpx of content "
                       "against %.0fpx of page less %.0fpx of slack. Cut "
                       "roughly %.1f lines."
                       % (stem, last[0], last[1], last[2], last[3], last[4],
                          PRINTABLE_H, SLACK_PX, max(0.0, over) / line_px))
            rows.append((stem, "-", "-", "-", tried[-1][4], 0.0))
            continue
        rows.append((stem, "%.1fpt / %.2f" % (body_pt, line_h), 1, dpages, px,
                     100.0 * px / PRINTABLE_H))

    w = max(len(r[0]) for r in rows) if rows else 10
    print("%-*s  %-14s %-4s %-5s  %-9s  %s"
          % (w, "document", "setting", "PDF", "DOCX", "content", "page fill"))
    for stem, setting, pages, dpages, px, fill in rows:
        print("%-*s  %-14s %-4s %-5s  %6.1fpx  %5.1f%% of %.0fpx"
              % (w, stem, setting, pages, dpages, px, fill, PRINTABLE_H))
    if bad:
        print()
        for b in bad:
            print("FAIL " + b)
        return 1
    print("\nAll %d compiled to exactly one page, measured in both Chromium "
          "and LibreOffice." % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
