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

| Document | Body | Line height | Content | Page fill |
|---|---|---|---|---|
| `Alex_Rajcoomar_Resume_V1_Tax` | 10.0pt | 1.15 | 928px | 97.6% |
| `Alex_Rajcoomar_Resume_V2_Assurance` | 10.0pt | 1.11 | 933px | 98.2% |
| `Alex_Rajcoomar_Resume_V3_FPA` | 10.0pt | 1.13 | 932px | 98.1% |

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

## Editing

Edit the markdown, re-run the compiler, and read what it says. Every document
sits above 97% of the page, so one added line will fail the build rather than
quietly produce a two-page resume. That is the point: a resume that spilled is
a defect the sender cannot see in the file they attach.

If a document will not fit, the compiler names how many lines to cut. Cut them
in the markdown. Do not widen the margins or drop below 10pt.
