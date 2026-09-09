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

## Handing this to another model

`CANDIDATE_BRIEF.md` is a self-contained handoff. It carries the candidate
profile including the transcript problem stated plainly, the verified portfolio
evidence mapped to the kind of role each piece would prove something for, the
constraints, the full WaterlooWorks pool of 263 postings, a prior 50-application
allocation with its reasoning, and a section naming where that reasoning is most
likely to be wrong. A model reading only that file should be able to decide
which postings to apply to and defend the decision without this conversation.

## Links

Three destinations are declared once in `build_resumes.py` and matched wherever
their display text appears, so a link cannot exist in the header and be missing
from the body, and the shown text cannot drift from where it goes.

| Shown | Goes to |
|---|---|
| `a2rajcoo@uwaterloo.ca` | `mailto:a2rajcoo@uwaterloo.ca` |
| `linkedin.com/in/leesharam-rajcoomar` | `https://www.linkedin.com/in/leesharam-rajcoomar/` |
| `alexrajcoomar.github.io` | `https://alexrajcoomar.github.io` |

Two signals carry every link: the accent `#1F4E79`, which is Word's own Blue
Accent 1 Darker 50%, and a 0.4pt rule in the same colour dropped 1.8pt clear of
the baseline. In Word both are written as explicit run properties rather than
by applying the built-in Hyperlink style, which paints a brighter blue that
changes with the theme.

The rule is not decoration and is not optional, and the reason is measured
rather than felt. The accent reads 8.7:1 against white, comfortably legible at
10pt, but only **2.42:1 against the black beside it**, under the 3:1 at which
one colour becomes distinguishable from another. A greyscale printer renders
the accent at 7% luminance against black's 0%. Rendering the header through
`pdftoppm -gray`, which is what a laser print produces, the colour disappears
entirely and the hairline is the only thing still saying a link is there. The
same holds for the roughly one man in twelve with a colour vision deficiency.
Colour alone would signal the portfolio to a recruiter reading on screen and
hide it from the one who cared enough to print the page.

The portfolio is bold in the header, the only emphasis in that line. It earns
it by sitting last: the eye lands on the terminal item in a centred line, so
bold there reads as a deliberate terminus rather than an accident, and at 9.5pt
it cannot compete with a 17pt name. Three alternatives were rendered and
rejected. Moving the portfolio ahead of LinkedIn puts it in a weaker position
and breaks the conventional email-then-profile order. Labelling it "Portfolio:"
raises the question of why only one item is labelled. Leaving all three equal
under-signals the one piece of evidence a reader can actually go and check. The
same token appears again, bold and accented, as the entry title of the
Independent Research section, so it reads as one object seen twice.

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
