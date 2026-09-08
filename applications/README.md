# applications/

The markdown files are the source. Nothing is written twice: the compiled PDF
and DOCX are generated from them, and the site's own resume page is generated
from `content/resume.json`, so a claim reaches a submitted document by being in
one of those two places first.

## Compiling

    python3 applications/build_resumes.py

Writes six files into `applications/compiled/`. The compiler refuses to finish
unless every one measures onto exactly one page, in Chromium and in Word's
layout both, and it says which renderer rejected what when it refuses.

## What the compiler settled

| Document | Body | Line | Gap | Content | Page fill |
|---|---|---|---|---|---|
| `Alex_Rajcoomar_Resume_V1_Tax` | 10.0pt | 1.15 | | 929px | 97.7% |
| `Alex_Rajcoomar_Resume_V2_Assurance` | 10.0pt | 1.11 | | 935px | 98.4% |
| `Alex_Rajcoomar_Resume_V3_FPA` | 10.0pt | 1.13 | | 934px | 98.3% |
| `Cover_Letter_Template` (option A) | 10.5pt | 1.15 | 14.0pt | 618px | 65.0% |
| `Cover_Letter_Option_B_Assurance` | 10.5pt | 1.15 | 14.0pt | 618px | 65.0% |
| `Cover_Letter_Option_C_FPA` | 10.5pt | 1.15 | 14.0pt | 635px | 66.8% |
| `Cover_Letter_Option_D_FinOps` | 10.5pt | 1.15 | 14.0pt | 618px | 65.0% |

Four live links in each resume, five in each letter, thirty-two in all,
resolved in both the PDF and the Word file.

The letters sit at two thirds of the page on purpose. A cover letter that fills
a page is a cover letter nobody finished, so the compiler caps the four
paragraphs at 250 words and then walks the paragraph spacing from the most open
setting down rather than the tightest up.

Letter, 0.55in margins, single column, Times New Roman. The line height is a
true multiple of the body size in both files, which is not what Word's own
"Multiple 1.10" box means: Word multiplies the font's natural line height,
about 1.15em, so a document set to the same figure in both comes out about
eleven per cent taller in Word. Measured here: 55 single lines of 10pt text at
Word multiple 1.10 filled a page that arithmetic said held 65. Both renderers
are therefore given the line height in points rather than a multiple.

The typeface is Times New Roman with Liberation Serif behind it, which is
metric-compatible with it. Without that fallback a machine lacking the
Microsoft face substitutes something wider and the page-fit measurement stops
predicting what Word does on the machine the file is sent from.

## Links

Three destinations are declared once in `build_resumes.py` and matched wherever
their display text appears, so a link cannot exist in the header and be missing
from the body, and the shown text cannot drift from where it goes.

| Shown | Goes to |
|---|---|
| `a2rajcoo@uwaterloo.ca` | `mailto:a2rajcoo@uwaterloo.ca` |
| `linkedin.com/in/leesharam-rajcoomar` | `https://www.linkedin.com/in/leesharam-rajcoomar/` |
| `alexrajcoomar.github.io` | `https://alexrajcoomar.github.io` |

They are black text with a thin grey rule under them, in both formats. A link
that shouts is a link a reader distrusts, and a link that hides is one nobody
clicks. In Word this is written as an explicit run property rather than by
applying Word's Hyperlink style, which paints blue and underlines in the
default theme.

The compiler counts what the source declares and then reads it back out of both
finished files: the `/URI` actions in the PDF, and the `w:hyperlink` elements in
the Word file resolved through the document part's relationships. A mismatch in
count or in target fails the build. That check was itself falsified two ways: a
Word renderer that draws the underline but writes no relationship, and a link
pointing at the wrong host. Both were refused, by name.

Chromium writes a bare origin back with a trailing slash, so
`https://alexrajcoomar.github.io` reads as `https://alexrajcoomar.github.io/` in
the PDF. Same destination; the check normalises for it rather than pretending
not to notice.

## Bolding

One emphasis span per bullet, and it is the figure or the credential that
bullet exists to deliver. Structural bold is separate and does not count
against it: the employer, the institution, a project title, a label at the head
of a line. Bold italic is reserved for the title of a published piece. The rule
exists because emphasis is a budget, not a decoration: a bullet with three bold
phrases has none.

## Editing

Edit the markdown, re-run the compiler, and read what it says. Every resume
sits above 97% of the page, so one added line will fail the build rather than
quietly produce a two-page resume. That is the point: a resume that spilled is
a defect the sender cannot see in the file they attach.

If a document will not fit, the compiler names how many lines to cut. Cut them
in the markdown. Do not widen the margins or drop below 10pt.
