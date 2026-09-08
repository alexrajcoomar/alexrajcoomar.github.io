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

# The cover letter is one source with four interchangeable second paragraphs,
# compiled into four complete letters rather than one file carrying all four.
# A template a person has to delete two paragraphs out of before sending is a
# template that eventually goes out with two paragraphs still in it.
LETTER_SRC = "cover_letter_template.md"
LETTERS = [
    ("a", "Cover_Letter_Template"),
    ("b", "Cover_Letter_Option_B_Assurance"),
    ("c", "Cover_Letter_Option_C_FPA"),
    ("d", "Cover_Letter_Option_D_FinOps"),
]
LETTER_WORD_CAP = 250

# One accent, used for nothing but links. Black is the document's information;
# the accent means "this goes somewhere". #1F4E79 is Word's own Blue Accent 1
# Darker 50%, so the DOCX looks native rather than arbitrarily coloured.
#
# The rule under a link is not decoration and is not optional. Measured on this
# palette: the accent reads 8.7:1 against white, which is comfortably legible at
# 10pt, but only 2.42:1 against the black beside it, under the 3:1 that makes
# one colour distinguishable from another. A greyscale printer renders the
# accent at 7% luminance against black's 0%, a difference no laser print shows.
# So on the page a recruiter prints, and for the roughly one man in twelve with
# a colour vision deficiency, the colour carries no signal and the hairline is
# the only thing left saying a link is there. It is set at 0.4pt and dropped
# clear of the baseline, which is what separates it from the default browser
# underline that makes a document look like a web page.
ACCENT = "1F4E79"
RULE_PT = 0.4
RULE_OFFSET_PT = 1.8

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


# The three destinations a reader is meant to reach. Written once, matched
# wherever the display text appears, so a link cannot exist in the header and
# be missing from the body, and the shown text cannot drift from where it goes.
# The tokens are matched with a right-hand boundary that excludes the
# punctuation a sentence puts after them, so "alexrajcoomar.github.io," links
# the address and not the comma.
LINKS = [
    (re.compile(r"a2rajcoo@uwaterloo\.ca"),               "mailto:a2rajcoo@uwaterloo.ca"),
    (re.compile(r"linkedin\.com/in/leesharam-rajcoomar"), "https://www.linkedin.com/in/leesharam-rajcoomar/"),
    (re.compile(r"alexrajcoomar\.github\.io"),            "https://alexrajcoomar.github.io"),
]


def linked(text):
    """Split a plain string into (text, href or None) segments. The earliest
    match wins and the remainder is rescanned, so overlapping patterns cannot
    produce a link inside a link."""
    out, pos = [], 0
    while pos < len(text):
        best = None
        for rx, url in LINKS:
            m = rx.search(text, pos)
            if m and (best is None or m.start() < best[0].start()):
                best = (m, url)
        if best is None:
            out.append((text[pos:], None)); break
        m, url = best
        if m.start() > pos:
            out.append((text[pos:m.start()], None))
        out.append((m.group(0), url))
        pos = m.end()
    return [seg for seg in out if seg[0]]


def runs_linked(text):
    """(text, bold, italic, href) for a string, markdown emphasis and links
    resolved together. Emphasis is split first because a link never spans an
    emphasis boundary in these documents, and a run that did would have to be
    two runs in Word anyway."""
    out = []
    for t, b, i_ in runs(text):
        for seg, href in linked(t):
            out.append((seg, b, i_, href))
    return out


def header_lines(doc):
    """The three-line header. The markdown carries the contact block over two
    lines because that is what reads well in a text editor; a printed resume
    wants it on one, so they are joined here rather than duplicated there."""
    contact = [l for l in doc["header"] if not (l.startswith("*") and l.endswith("*"))]
    subtitle = [l.strip("*") for l in doc["header"] if l.startswith("*") and l.endswith("*")]
    return doc["name"], " | ".join(contact), (subtitle[0] if subtitle else "")



def parse_letter(md, option):
    """Assemble one letter from the block file.

    The blocks are named rather than positional, so an option can be added or
    reworded without the compiler needing to know where it sits in the file,
    and a missing block is an error with a name in it rather than a letter
    that quietly went out a paragraph short.
    """
    doc = parse(md)
    blocks = dict(re.findall(r"^## BLOCK: (\S+)[^\n]*\n(.*?)(?=^## |\Z)",
                             md, re.S | re.M))
    want = ["opening", "p1", "p2-" + option, "p3", "p4", "sign"]
    missing = [k for k in want if k not in blocks]
    if missing:
        raise KeyError("cover letter is missing block(s): " + ", ".join(missing))

    def lines(key):
        return [l.strip() for l in blocks[key].strip().split("\n\n")]

    body = []
    for l in blocks["opening"].strip().split("\n"):
        body.append({"kind": "addr", "text": l.strip()})
    # The salutation ends the opening block, and stripping the block takes its
    # trailing blank line with it. Put the line back: a letter whose first
    # paragraph sits directly on "Dear" reads as a mistake.
    body.append({"kind": "addr", "text": ""})
    for key in ("p1", "p2-" + option, "p3", "p4"):
        body.append({"kind": "para",
                     "text": " ".join(blocks[key].split())})
    for l in blocks["sign"].strip().split("\n"):
        body.append({"kind": "addr", "text": l.strip()})

    words = sum(len(b["text"].split()) for b in body if b["kind"] == "para")
    return {"name": doc["name"], "header": doc["header"], "body": body,
            "words": words}


LETTER_CSS = """
@page { size: %(pw).2fin %(ph).2fin; margin: %(m).2fin; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: 'Times New Roman', 'Liberation Serif', 'Tinos', Times, serif;
  font-size: %(bodypt).2fpt;
  line-height: %(lead).2fpt;
  color: #000; background: #fff;
  width: %(pwin).3fin;
}
.name {
  font-size: %(headpt).1fpt; font-weight: 700; letter-spacing: .035em;
  text-align: center; line-height: %(headlead).1fpt; margin: 0 0 2.5pt;
}
.contact, .avail { text-align: center; }
.contact { font-size: %(contactpt).1fpt; line-height: %(contactlead).1fpt;
           margin: 0 0 1pt; }
.avail { font-size: %(availpt).1fpt; line-height: %(availlead).1fpt;
         font-style: italic; margin: 0 0 0; }
hr { border: 0; border-top: .9pt solid #000; margin: 5pt 0 11pt; }
p.addr { margin: 0; }
p.gap { margin: 0 0 %(gap).1fpt; }
p.para { margin: 0 0 %(gap).1fpt; text-align: left; }
/* A link that shouts is a link a reader distrusts, and a link that hides is
   one nobody clicks. Both signals are carried: the accent for the reader
   looking at a screen, the hairline for the one holding a greyscale print. */
a { color: #%(accent)s; text-decoration: underline;
    text-decoration-color: #%(accent)s;
    text-decoration-thickness: %(rule).1fpt;
    text-underline-offset: %(offset).1fpt; }
"""


def letter_html(letter, body_pt, line_h, gap):
    css = LETTER_CSS % {"pw": PAGE_W_IN, "ph": PAGE_H_IN, "m": MARGIN_IN,
                        "bodypt": body_pt, "lead": leading(body_pt, line_h),
                        "headpt": HEAD_PT, "headlead": HEAD_LEAD,
                        "contactpt": CONTACT_PT, "contactlead": CONTACT_LEAD,
                        "availpt": AVAIL_PT, "availlead": AVAIL_LEAD,
                        "gap": gap, "pwin": PAGE_W_IN - 2 * MARGIN_IN,
                        "accent": ACCENT, "rule": RULE_PT, "offset": RULE_OFFSET_PT}
    name, contact, avail = header_lines(letter)
    p = ['<!doctype html><html><head><meta charset="utf-8">',
         "<title>%s</title><style>%s</style></head><body>" % (H.escape(name), css),
         '<div class="name">%s</div>' % H.escape(name),
         '<div class="contact">%s</div>' % esc(contact),
         '<div class="avail">%s</div><hr>' % H.escape(avail)]
    prev = None
    for b in letter["body"]:
        if b["kind"] == "para":
            p.append('<p class="para">%s</p>' % esc(b["text"]))
        elif not b["text"]:
            p.append('<p class="gap">&nbsp;</p>' if prev == "addr" else "")
        else:
            p.append('<p class="addr">%s</p>' % esc(b["text"]))
        prev = b["kind"] if b["text"] else prev
    p.append("</body></html>")
    return "\n".join(p)



def docx_runs(document, paragraph, text, bold=None, italic=None, size=None):
    """Write one string into a Word paragraph, emphasis and hyperlinks both.

    python-docx has no hyperlink API, so a linked run is built by hand: the
    document part is asked for an external relationship to the target, and a
    w:hyperlink element carrying that relationship id wraps the run. Word and
    LibreOffice both read that, and so does every PDF exporter that has to
    turn the file back into a document.

    The link is styled here rather than by Word's Hyperlink style, so the
    accent and the hairline are the document's own choices and survive a theme
    change, a copy into another file, or a reviewer with a different Normal
    style.
    """
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    def style(run, b, i_):
        run.bold = b if bold is None else bold
        run.italic = i_ if italic is None else italic
        if size:
            run.font.size = Pt(size)

    for t, b, i_, href in runs_linked(text):
        if not href:
            style(paragraph.add_run(t), b, i_)
            continue
        rid = document.part.relate_to(href, RT.HYPERLINK, is_external=True)
        link = OxmlElement("w:hyperlink")
        link.set(qn("r:id"), rid)
        # Build the run through python-docx so its own run properties apply,
        # then move the finished element under the hyperlink.
        run = paragraph.add_run(t)
        style(run, b, i_)
        rPr = run._r.get_or_add_rPr()
        col = OxmlElement("w:color"); col.set(qn("w:val"), ACCENT)
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single"); u.set(qn("w:color"), ACCENT)
        rPr.append(col); rPr.append(u)
        paragraph._p.remove(run._r)
        link.append(run._r)
        paragraph._p.append(link)


def letter_docx(letter, path, body_pt, line_h, gap):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, Inches, RGBColor

    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(body_pt)
    st.font.color.rgb = RGBColor(0, 0, 0)
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), "Times New Roman")
    lead = Pt(leading(body_pt, line_h))
    pf = st.paragraph_format
    pf.line_spacing = lead
    pf.space_before = Pt(0); pf.space_after = Pt(0); pf.widow_control = False

    s = d.sections[0]
    s.page_width, s.page_height = Inches(PAGE_W_IN), Inches(PAGE_H_IN)
    for side in ("top", "bottom", "left", "right"):
        setattr(s, side + "_margin", Inches(MARGIN_IN))

    def para(after=0, line=None, align=None):
        p = d.add_paragraph()
        f = p.paragraph_format
        f.space_before = Pt(0); f.space_after = Pt(after)
        f.line_spacing = lead if line is None else line
        f.widow_control = False
        if align is not None:
            p.alignment = align
        return p

    def put(p, text):
        docx_runs(d, p, text)
        return p

    name, contact, avail = header_lines(letter)
    p = para(1.2, Pt(HEAD_LEAD), WD_ALIGN_PARAGRAPH.CENTER)
    r = p.add_run(name); r.bold = True; r.font.size = Pt(HEAD_PT)
    p = para(0.5, Pt(CONTACT_LEAD), WD_ALIGN_PARAGRAPH.CENTER)
    docx_runs(d, p, contact, bold=False, italic=False, size=CONTACT_PT)
    p = para(5.0, Pt(AVAIL_LEAD), WD_ALIGN_PARAGRAPH.CENTER)
    r = p.add_run(avail); r.italic = True; r.font.size = Pt(AVAIL_PT)
    # The rule under the letterhead is the same paragraph border the resumes
    # use for a section, so the two documents carry one mark and not two.
    pPr = p._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr"); bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single"); bot.set(qn("w:sz"), "7")
    bot.set(qn("w:space"), "6"); bot.set(qn("w:color"), "000000")
    bd.append(bot); pPr.append(bd)

    prev = None
    for b in letter["body"]:
        if b["kind"] == "para":
            put(para(gap), b["text"])
        elif not b["text"]:
            if prev == "addr":
                para(gap)
        else:
            put(para(0), b["text"])
        prev = b["kind"] if b["text"] else prev
    d.save(path)


def fit_letter(letter, pdf_path, docx_path):
    """Same walk as the resumes, with one more dimension: the space between
    paragraphs. A letter that is short of the page reads badly when it is
    crammed, so the ladder is walked from the most open setting down and the
    first that fits is taken."""
    tried = []
    for gap in (14.0, 12.0, 10.0, 8.5, 7.0, 5.5):
        for body_pt, line_h in LADDER:
            m = render_pdf(letter_html(letter, body_pt, line_h, gap), pdf_path)
            pages, declared = pdf_pages(pdf_path)
            if pages != 1 or (declared not in (1, None)) or \
                    PRINTABLE_H - m["contentPx"] < SLACK_PX:
                tried.append((body_pt, line_h, "pdf", pages, m["contentPx"]))
                continue
            letter_docx(letter, docx_path, body_pt, line_h, gap)
            dpages, _err = docx_pages(docx_path)
            if dpages == 1:
                return body_pt, line_h, gap, m["contentPx"], dpages, tried
            tried.append((body_pt, line_h, "docx", dpages or "?", m["contentPx"]))
    return None, None, None, None, None, tried


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
/* A second entry inside a section, the UW CISA row under the Pet Valu
   bullets, otherwise butts straight against the bullet above it and reads as
   part of the same block. The rule under a section heading separates
   sections; this separates entries. */
ul + .entry { margin-top: 2.8pt; }
ul { margin: .8pt 0 2pt; padding-left: 11.5pt; }
li { margin: 0 0 1.15pt; padding-left: 1.5pt; }
li::marker { font-size: .85em; }
/* A link that shouts is a link a reader distrusts, and a link that hides is
   one nobody clicks. Both signals are carried: the accent for the reader
   looking at a screen, the hairline for the one holding a greyscale print. */
a { color: #%(accent)s; text-decoration: underline;
    text-decoration-color: #%(accent)s;
    text-decoration-thickness: %(rule).1fpt;
    text-underline-offset: %(offset).1fpt; }
b, strong { font-weight: 700; }
i, em { font-style: italic; }
"""



def esc(text):
    out = []
    for t, b, i_, href in runs_linked(text):
        piece = H.escape(t)
        if b and i_:
            piece = "<b><i>%s</i></b>" % piece
        elif b:
            piece = "<b>%s</b>" % piece
        elif i_:
            piece = "<i>%s</i>" % piece
        if href:
            piece = '<a href="%s">%s</a>' % (H.escape(href, quote=True), piece)
        out.append(piece)
    return "".join(out)


def to_html(doc, body_pt, line_h):
    name, contact, avail = header_lines(doc)
    css = CSS % {"pw": PAGE_W_IN, "ph": PAGE_H_IN, "m": MARGIN_IN,
                 "bodypt": body_pt, "lead": leading(body_pt, line_h),
                 "seclead": body_pt * SECTION_LEAD,
                 "headpt": HEAD_PT, "headlead": HEAD_LEAD,
                 "contactpt": CONTACT_PT, "contactlead": CONTACT_LEAD,
                 "availpt": AVAIL_PT, "availlead": AVAIL_LEAD,
                 "pwin": PAGE_W_IN - 2 * MARGIN_IN,
                 "accent": ACCENT, "rule": RULE_PT, "offset": RULE_OFFSET_PT}
    p = ['<!doctype html><html><head><meta charset="utf-8">',
         "<title>%s</title><style>%s</style></head><body>" % (H.escape(name), css),
         '<div class="name">%s</div>' % H.escape(name),
         '<div class="contact">%s</div>' % esc(contact),
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
  // Not scrollHeight. documentElement.scrollHeight never falls below the
  // viewport, so a document shorter than the viewport measures as the
  // viewport and the number stops meaning anything: every cover letter
  // measured exactly 720px, the default viewport height, whatever its
  // spacing. Measure the content instead, as the lowest edge any top-level
  // element reaches once its own bottom margin is counted. The body has no
  // margin of its own, so that edge is the height of the document.
  const h = await pg.evaluate(() => {
    const kids = [...document.body.children];
    if (!kids.length) return 0;
    return Math.ceil(Math.max(...kids.map(e => {
      const r = e.getBoundingClientRect();
      const mb = parseFloat(getComputedStyle(e).marginBottom) || 0;
      return r.bottom + window.scrollY + mb;
    })));
  });
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
        docx_runs(d, p, text, bold, italic, size)
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
    docx_runs(d, p, contact, bold=False, italic=False, size=CONTACT_PT)
    p = para(0, 2.0, Pt(AVAIL_LEAD)); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(avail); r.italic = True; r.font.size = Pt(AVAIL_PT)

    first = True
    for sec in doc["sections"]:
        p = para(3.0 if first else 5.2, 2.0, Pt(body_pt * SECTION_LEAD))
        first = False
        r = p.add_run(sec["title"]); r.bold = True; r.font.size = Pt(body_pt)
        rule(p)
        after_bullets = False
        for blk in sec["blocks"]:
            if blk["kind"] == "bullet":
                after_bullets = True
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
                ep = para(2.8 if (key == "main" and after_bullets) else 0, 0.6)
                ep.paragraph_format.tab_stops.add_tab_stop(
                    right_tab, WD_TAB_ALIGNMENT.RIGHT)
                put(ep, blk[key])
                if blk.get(rkey):
                    ep.add_run("\t" + blk[rkey])
                after_bullets = False
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



def expected_links(texts):
    """How many link segments the source says a document should carry, and to
    where. Counted from the same function the renderers use, so the count
    cannot drift from what was written."""
    out = []
    for t in texts:
        out += [href for _seg, href in linked(t) if href]
    return out


def doc_texts(doc):
    _n, contact, _a = header_lines(doc)
    out = [contact]
    for sec in doc["sections"]:
        for blk in sec["blocks"]:
            for k in ("text", "main", "sub"):
                if blk.get(k):
                    out.append(blk[k])
    return out


def letter_texts(letter):
    _n, contact, _a = header_lines(letter)
    return [contact] + [b["text"] for b in letter["body"] if b["text"]]


def pdf_links(path):
    """The URI actions the PDF actually carries. A link that is only styled to
    look like one is the failure this catches: the text is underlined, the
    reader clicks, and nothing happens."""
    raw = open(path, "rb").read()
    return [u.decode("latin-1") for u in re.findall(rb"/URI\s*\((.*?)\)", raw)]


def docx_links(path):
    """The hyperlink elements in the Word file, resolved through the document
    part's relationships. Counting relationships alone would undercount, since
    Word reuses one relationship for repeated targets."""
    import zipfile
    z = zipfile.ZipFile(path)
    rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    body = z.read("word/document.xml").decode("utf-8")
    z.close()
    by_id = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"[^>]*TargetMode="External"',
                            rels))
    return [by_id.get(rid, "?") for rid in
            re.findall(r'<w:hyperlink [^>]*r:id="([^"]+)"', body)]


def same_target(a, b):
    """Chromium writes a bare origin back with its trailing slash. That is the
    same destination, not a different one."""
    return a.rstrip("/") == b.rstrip("/")


def check_links(stem, want, pdf_path, docx_path):
    """Every link the source declares must exist in both files, pointing where
    it was told to point."""
    problems = []
    for label, got in (("PDF", pdf_links(pdf_path)), ("DOCX", docx_links(docx_path))):
        if len(got) != len(want):
            problems.append("%s: the %s carries %d links, the source declares %d"
                            % (stem, label, len(got), len(want)))
            continue
        for w, g in zip(sorted(want), sorted(got)):
            if not same_target(w, g):
                problems.append("%s: the %s links to %s where the source says %s"
                                % (stem, label, g, w))
    return problems


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
            rows.append((stem, "-", "-", "-", tried[-1][4], 0.0, 0))
            continue
        want = expected_links(doc_texts(doc))
        bad += check_links(stem, want, pdf_path, docx_path)
        rows.append((stem, "%.1fpt / %.2f" % (body_pt, line_h), 1, dpages, px,
                     100.0 * px / PRINTABLE_H, len(want)))

    if not only or only == "letter":
        md = open(os.path.join(HERE, LETTER_SRC), encoding="utf-8").read()
        for stray in ("\u2014", "\u2013"):
            if stray in md:
                bad.append("%s: an em or en dash reached the source" % LETTER_SRC)
        for option, stem in LETTERS:
            letter = parse_letter(md, option)
            if letter["words"] > LETTER_WORD_CAP:
                bad.append("%s: %d words in the four paragraphs, over the %d "
                           "the brief sets. A letter nobody finishes reading "
                           "is not a shorter letter."
                           % (stem, letter["words"], LETTER_WORD_CAP))
            pdf_path = os.path.join(OUT, stem + ".pdf")
            docx_path = os.path.join(OUT, stem + ".docx")
            body_pt, line_h, gap, px, dpages, tried = fit_letter(
                letter, pdf_path, docx_path)
            if body_pt is None:
                last = tried[-1]
                bad.append("%s: does not fit one page. At the tightest setting "
                           "the %s renderer laid it out on %s pages."
                           % (stem, last[2], last[3]))
                rows.append((stem, "-", "-", "-", last[4], 0.0, 0))
                continue
            want = expected_links(letter_texts(letter))
            bad += check_links(stem, want, pdf_path, docx_path)
            rows.append((stem, "%.1fpt / %.2f / %.1fpt" % (body_pt, line_h, gap),
                         1, dpages, px, 100.0 * px / PRINTABLE_H, len(want)))

    w = max(len(r[0]) for r in rows) if rows else 10
    print("%-*s  %-22s %-4s %-5s %-6s %-9s  %s"
          % (w, "document", "setting (body / line / gap)", "PDF", "DOCX",
             "links", "content", "page fill"))
    for stem, setting, pages, dpages, px, fill, nlinks in rows:
        print("%-*s  %-22s %-4s %-5s %-6s %6.1fpx  %5.1f%% of %.0fpx"
              % (w, stem, setting, pages, dpages, nlinks, px, fill, PRINTABLE_H))
    if bad:
        print()
        for b in bad:
            print("FAIL " + b)
        return 1
    print("\nAll %d compiled to exactly one page, measured in both Chromium "
          "and LibreOffice, with %d live links resolved in both formats."
          % (len(rows), sum(r[6] for r in rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
