# System architecture and creative brief

**For:** an agent working in a separate workspace, without access to the
conversation that produced this file.
**Repository:** `alexrajcoomar/alexrajcoomar.github.io`, served at
https://alexrajcoomar.github.io
**Written:** 12 September 2026, against commit `a958d07`.
**Status of every number below:** read out of the repository at that commit. If
you find one that no longer holds, the repository is right and this file is
stale. Say so rather than working around it.

---

## 0. The contract

You are being asked to add atmosphere to a site whose entire argument is that
nothing on it is decorative. Every visual element already on this site is
derived from a recorded measurement, and the build refuses to deploy when a
page claims something its data does not support.

That constraint is not a style preference. It is the product. The site's
headline is *"I make arguments you can audit."* A visual effect that cannot
state where its values came from is off-thesis no matter how good it looks.

So the brief is narrower than "make it atmospheric." It is:

> Make the existing evidence more legible and more arresting, using light,
> depth and typography, without introducing a single value that is not either
> measured, derived, or declared in a file a reader can open.

Work that satisfies that is welcome and wanted. Work that adds mood on top of
the data is a regression, and the build will usually catch it.

---

## 1. Stop conditions

Read these before writing any code. Each one has failed at least once in this
repository's history, which is why it is written down.

### 1.1 Do not edit the generated HTML

Most `.html` files at the repository root are **written by the build**, not
authored. `build/build_site.py` is 7,222 lines and regenerates the shell pages
on every run. If you edit `index.html`, `about.html`, `atlas.html`,
`library.html`, `selected.html`, `colophon.html`, `controls.html`,
`resume.html`, `research.html`, `tools.html` or `404.html` directly, your
change is reverted the next time the build runs, which happens on every push to
`main`.

Visual changes to those pages belong in one of:

* `build/build_site.py` for structure and markup
* `site.css` for presentation
* `site.js` or `atlas.js` for behaviour
* `figures.css` for a figure's colour scope

The converted documents (the study guides, essays and research pieces) are a
different case: those are authored files listed in `content/pieces.json` and
the build wraps rather than rewrites them. Check `content/pieces.json` before
assuming which kind a file is.

### 1.2 The build must be idempotent

The workflow runs `build/build_site.py` a second time and greps the log for the
exact string `rewrote: nothing`. If your change makes the build write a
different byte on a second identical run, the deploy does not happen. The usual
cause is a timestamp, a random seed, or a dict iteration order leaking into
output. Derive from recorded data, sort your keys, and never call `random` or
`datetime.now()` in a code path that writes a file.

### 1.3 Zero idle frames

`build/audit.js` wraps `requestAnimationFrame`, loads each page, waits for it to
settle, then counts frames requested during one idle second. Every page in
`content/audit.json` currently records `idle.frames: 0`.

**A mist, fog, ember, flicker, drift, pulse or shimmer that animates while the
page sits still will set that number above zero and fail the audit.**

This is the constraint most likely to kill the aesthetic as originally
imagined. The resolution is in section 6: atmosphere here is *static depth plus
input-driven response*, not ambient animation. Anything that moves must be
driven by a pointer, a scroll, a focus change or a key press, and must stop
requesting frames when the input stops.

### 1.4 Zero external requests

`build/audit.js` counts every request whose URL does not start with the site's
own origin, `data:`, or the GitHub API host that `admin.html` legitimately
calls. The current count is zero on every page. No CDN, no Google Fonts, no
analytics, no remote texture, no external script. Fonts are already subset and
self-hosted (`InterVariable-sub.woff2`, plus `fonts/`). Any asset you add must
live in the repository.

### 1.5 Contrast is measured, not eyeballed

Check 36 reads the colour tokens out of `site.css` itself, composites both
ambient light layers over the paper at full strength, and requires every text
token to clear **4.5:1** on every surface it can sit on, in both themes. A
control's border must clear **3:1**, because on a control the border is the
only thing telling a reader the control exists.

If you add an overlay, a vignette, a mist layer or a torch gradient, check 36
composites it and re-measures. An overlay that dims text below the floor fails
the build. Design to the floor from the start rather than discovering it at the
end.

### 1.6 Do not edit the measurement records

`content/audit.json`, `content/negatives.json`, `content/invariants.json`,
`content/metrics.json` and `content/fingerprints.json` are **outputs**. They are
what the tools recorded. Editing them by hand to make a check pass is the exact
failure the site exists to argue against, and it is trivially detectable in the
diff. If a record needs to change, change the thing being measured and re-run
the tool that writes it.

### 1.7 Timing

Waterloo co-op applications for the January to April 2027 term close on
**17 September 2026 at 9:00 AM**. This site is linked from cover letters
submitted in that cycle. Until that date passes, **nothing merges to `main`**.
Work on a branch, open a pull request, and leave the merge decision to the
owner. A half-landed redesign on the live site during the week recruiters are
opening it is a worse outcome than shipping nothing.

---

## 2. What the site is

A static portfolio, served by GitHub Pages from the repository root. No server,
no framework, no build-time dependency beyond Python 3 and Node for two
measurement scripts. It holds roughly 90 documents: independent research,
university coursework, and a set of interactive study tools.

**The thesis.** Every claim the site makes about itself is checked by the build.
The word counts, the link counts, the corpus totals, the capability mappings and
the figures are read from `content/*.json`, and a check fails the build when a
page prints a number the data does not support. The colophon and the controls
page print the register of those checks, with denominators, so a reader can see
what was checked and how much of it was looked at.

**The two faces.** `OBSIDIAN` (dark) and `ARCHIVAL LIGHT` (light), selected by a
two-state control that writes `data-theme` on the root element and stores the
choice. When no choice is stored, `prefers-color-scheme` decides. Both faces are
first-class and both are measured. There is no "primary" theme.

**The two instruments.** A sphere on the home page and a larger Atlas on
`atlas.html`. Both are 2D canvas, drawn from data emitted by the build:

* each document is placed by rule, not by hand. Latitude comes from the
  document's origin (independent, coursework, tool, and the author's own
  entry), longitude from its rank by word count, and its disc area from its
  share of the corpus.
* hovering or tapping a mark draws **chords** to the documents that document's
  prose actually links to. The links are real links, extracted at build time.
* at rest, neither instrument requests an animation frame.

This is the part of the site that most resembles what you have been asked to
build, and it is already doing the honest version of it. Read `atlas.js`
(2,246 lines) and the sphere section of `site.js` (1,637 lines) before
proposing to replace either.

---

## 3. Architecture

### 3.1 The pipeline

```
content/*.json  (declared data and recorded measurements)
      |
      v
build/measure_plan.py   decides what actually needs re-measuring
      |
      +--> build/measure.js    opens changed pieces in Chromium, records size and shape
      +--> build/cards.js      redraws link-preview cards whose titles changed
      |
      v
build/build_site.py     writes the shell pages, then runs check_site()
      |                 41 checks, each tallying a denominator
      v
build/negatives.py      70 falsifications: breaks the tree on purpose,
      |                 requires the build to refuse and name the right check
      v
build/audit.js          loads every page in Chromium, records what it measures
build/audit.js --falsify  breaks each runtime claim, requires the measurement to fail it
      |
      v
build/claims.py         records the run
build/build_site.py     second pass, prints the records onto the pages
build/build_site.py     third pass, must rewrite nothing
      |
      v
commit generated files, package the tree, deploy to Pages
```

The whole chain is in `.github/workflows/build.yml`. It fires on push to `main`
and on manual dispatch. The deploy job depends on the build job, so a red build
leaves the previous site live. The commit-back carries `[skip ci]` so it cannot
retrigger itself.

### 3.2 The check system

`check_site()` begins at line 4853 of `build/build_site.py`. There are 41 check
identifiers: `1` through `39`, plus `11a` and `11b`. Each one appends to a
`problems` list through `_p(id, message)` and records what it looked at in two
structures:

* `check_site.tally` gives the denominator, so the register can print
  "checked 1,247 links across 91 pages" rather than a bare green tick.
* `check_site.records` gives the outcome per page per check, so the controls
  page can draw one glyph per pair.

**If you add a visual feature, you add a check.** A check that holds the feature
to its own claim. If you draw a lineage overlay from recorded link data, the
check asserts that every line drawn corresponds to a link in the data and that
no link in the data is silently dropped.

### 3.3 The falsification suite

`build/negatives.py` holds exactly 70 cases. Each one copies the tree, breaks
one specific thing, runs the build, and requires the build to fail *and to name
the check that should have caught it*. A falsification the checks miss fails
the run. This is what makes the register a test of controls rather than a list
of intentions.

**A new check without a falsification is not finished.** Add at least one case
per check you add: the minimal edit that should make your check scream.

---

## 4. Acceptance criteria

Your work is done when all of the following hold on your branch. Run them in
this order.

| # | Command | Requirement |
|---|---|---|
| 1 | `python3 build/build_site.py` | exits clean, no check fails |
| 2 | `python3 build/build_site.py` | second run prints `rewrote: nothing` |
| 3 | `python3 build/negatives.py --jobs 3` | every falsification is caught and names its check |
| 4 | `node build/audit.js` | `idle.frames` is 0 on every page |
| 5 | `node build/audit.js` | `ext.external` is 0 on every page |
| 6 | `node build/audit.js` | `errors` is 0 on every page |
| 7 | `node build/audit.js --falsify` | every runtime claim fails when broken |
| 8 | manual | `fit.overflow` false at 320px; no horizontal scroll at 320, 360, 390, 768, 1440 |
| 9 | manual | both themes: every surface, every state, both instruments |
| 10 | manual | keyboard only: every interactive element reachable, focus ring always visible (`keyboard.noRing` is 0) |
| 11 | manual | JavaScript disabled: the page still reads and every document is still reachable |
| 12 | manual | print stylesheet: the ambient light layers are already forced transparent for print, keep it that way |
| 13 | `python3 build/emdash.py` | zero em dashes in prose. This is a house rule and it is checked |

Requirement 11 deserves emphasis. The instruments are enhancements over a
document list that works without them. If your change makes any document
unreachable without JavaScript, it is wrong regardless of how it measures.

---

## 5. The design system you are inheriting

### 5.1 Tokens

Defined on `:root` in `site.css`, redefined under
`@media (prefers-color-scheme: dark)` and again under `:root[data-theme="dark"]`
so the explicit selector wins in both directions. Every colour carries its
measured contrast ratio in a comment. Light values:

| Token | Value | Role |
|---|---|---|
| `--paper` | `#faf9f6` | page ground |
| `--panel` | `#f2f0e9` | raised surface |
| `--panel-2` | `#ebe8df` | second raised surface |
| `--ink` | `#16150f` | body text, 18.4:1 on paper |
| `--ink-2` | `#55524a` | secondary text, 7.5:1 |
| `--ink-3` | `#66635a` | smallest text, 4.9:1 on the worst surface it sits on |
| `--rule` | `#ddd9cf` | hairline, decorative |
| `--rule-strong` | `#bfb9aa` | heavier hairline, decorative, 1.9:1 and therefore never a control border |
| `--edge` | `#8a847c` | the border of anything interactive, 3.3:1 on panel |
| `--accent` | `#14509b` | links and independent work, 7.4:1 |
| `--accent-2` | `#1a5fb4` | accent's second step |
| `--link` | `#5a36c9` | **reserved**, see below |
| `--cobalt` | `#0047ab` | **reserved**, see below |
| `--tool` | `#0f6b58` | the interactive tools |
| `--ref` | `#8a5410` | reference material |
| `--lamp-cool` | `rgba(20,80,155,.05)` | the cool wash behind the instrument |
| `--lamp-warm` | `rgba(190,168,120,.16)` | the warm reading light behind the type column |
| `--radius` | `0px` | editorial, no rounded corners anywhere |
| `--shell` | `76rem` | outer width |
| `--measure` | `38rem` | reading measure |

### 5.2 The hue allocation is already spent

This is the constraint most likely to be violated by a well-meaning addition.

Three hues on this site carry a single, exclusive meaning, recorded in the
stylesheet and printed in the colophon:

* **Violet `--link`** means one thing: a link that one document's prose makes to
  another document. It is the colour of the chords on both instruments, of the
  key entry naming them, and of the link counts in a mark's card. It appears
  nowhere else. Violet was chosen because no figure on the site had spent it.
* **Cobalt `--cobalt`** means one thing: two capabilities evidenced by the same
  piece. Not a citation, not a link, not the accent.
* **Accent blue** means independent work and every navigational link.

Green is the tools and the investment share. Amber is a heading carried by
several documents. Orange and blue are the two anchors in one specific figure.
Red and blue are inside and outside a number in another.

**You may not introduce a new hue without retiring an old one or claiming a new
meaning and recording it in the colophon.** "Bioluminescent teal because it
looks good" is exactly the kind of unsourced decision this site argues against.
If a new meaning genuinely exists, name it, pick a hue no figure has spent,
prove its contrast, and add it to the colophon's ledger.

### 5.3 The two lights already exist

Note `--lamp-cool` and `--lamp-warm`. The site already has a two-light model: a
cool wash behind the instrument and a warmer reading light behind the column of
type. They are gradients on elements that already exist, not layers added to
carry them, they touch no text colour, and check 36 composites both at full
strength before measuring contrast.

**Extend this model rather than replacing it.** The atmospheric direction you
have been given is, in this system's terms, a request to make those two lights
do more work. That is a legitimate and well-scoped change. Adding a separate fog
layer on top is not.

---

## 6. The creative direction, resolved

The owner named three visual sources. They do not carry equal weight and one of
them does not transfer at all. Here is the resolution, with reasons, so you are
not guessing.

### 6.1 Alan Wake 2: take the case board, not the fog

The transferable idea is not volumetric mist. It is the **investigation board**:
evidence pinned to a wall, connected by physical string, read by a light the
investigator carries. The meaning of that image is that *the connections were
always there, and the light only reveals them*.

That is an unusually exact match for this site's thesis, and for the chord
system that already exists. The mechanic to build is **illumination as query**:

* a light source follows the pointer, or the focused element when the user is on
  a keyboard, or the tapped mark on touch.
* within its radius, the provenance of what it touches is revealed: where a
  number came from, which check holds it, which documents link to this one.
* **the light reveals only what is already in the document and already reachable
  another way.** It is a lens, never a source. Anything the torch shows must be
  obtainable by clicking through, by keyboard, and with JavaScript disabled.

That last rule is what makes the whole aesthetic compatible with the thesis
rather than at war with it. Write it into every component you build.

The typography cue is more directly usable: Remedy's classified-dossier
lettering is a monospaced, heavily tracked, small-caps stamp used for metadata
and status. This site already has a metadata grammar (`--meta-size: .72rem`,
`--meta-track: .08em`, `--meta-weight: 560`). Pushing that grammar toward the
dossier register is cheap, reversible, and touches no data.

### 6.2 The Witcher: take the root system, not the magic

The transferable idea is a network whose branching is **structural and older
than the viewer**: roots that hold something up, not vines that decorate it.
Applied here, that is the provenance chain. A figure on the Dollarama valuation
page descends from a schedule, which descends from an input, which descends from
a filing. That chain is real, it is in `content/valuation-inputs.json` and
`content/valuation-output.json`, and it is currently rendered as tables.

Rendering it as a rooted, radial or dendritic structure, in the existing hues,
driven by the recorded lineage, would be a genuine improvement and is fully
on-thesis. Lantern-lit warmth is available through `--lamp-warm`, which already
exists and is already measured.

What does not transfer is bioluminescence as a new palette. See 5.2.

### 6.3 Grand Theft Auto VI: does not transfer

The reference pack supplied is neon magenta and cyan on chrome, at high
saturation, in a nostalgic 1980s register. It is a good-looking set of images
and it is the opposite of every other input to this brief. It fights Swiss
Modernism, it fights the archival palette, it fights both themes, and it fights
the thesis, since its entire visual language is atmosphere for its own sake.

Recommendation: drop it. If some element must survive, the only defensible
extraction is the **hard horizontal light bar** as a structural device, in
existing hues, at existing contrast. Not the colour, not the glow, not the
chrome.

### 6.4 Swiss Modernism is the governing grammar, not one of three inputs

The site is already Swiss: a strict grid, zero border radius, a tight type
scale, generous negative space, and colour used as signal rather than
decoration. The game references supply *atmosphere within* that grammar. Where
they conflict, the grid wins. If you find yourself loosening the grid to make an
effect work, the effect is wrong.

---

## 7. Work packages

Five packages, ordered by ratio of effect to risk. Each names where the code
goes, the check it must add, and the falsification that proves the check.

### WP1: the dossier metadata register (lowest risk, ships first)

Push the existing metadata grammar toward the classified-dossier register:
tracked small caps, a rule above, a status stamp for the document's origin and
its check status. Applies to the library rows, the piece headers and the Atlas
key.

* **Where:** `site.css` only, plus the metadata emitter in `build/build_site.py`
  if a status stamp needs new markup.
* **Check:** extend check 36's token set if you introduce any new colour. If you
  introduce none, no new check is needed, and say so explicitly in the pull
  request rather than leaving it implied.
* **Risk:** low. Reversible in one commit. No data touched.

### WP2: the two lights, deepened

Give `--lamp-cool` and `--lamp-warm` more range: a stronger falloff, an
asymmetric placement tied to the instrument's position, a subtle grain that is a
static `data:` SVG rather than an animated canvas.

* **Where:** `site.css`, in the existing lamp block.
* **Check:** check 36 already composites the lamps. If you add a third light,
  add it to `_lamp36`'s pattern so it is composited too. **This is mandatory.**
  A light that check 36 does not know about is an unmeasured overlay on text.
* **Falsification:** a case in `build/negatives.py` that raises a lamp's alpha
  until a text token drops under 4.5:1 and requires check 36 to catch it.
* **Risk:** low to medium. The failure mode is contrast, and it is measured.

### WP3: illumination as query, on the instruments

The torch. A radial reveal that follows the pointer over the sphere and the
Atlas, raising the contrast of marks inside its radius and drawing the chords
for whatever it touches.

* **Where:** `site.js` and `atlas.js`, both 2D canvas. Both already have
  hit-testing and a chord renderer. You are adding a light term to an existing
  draw, not writing a new renderer.
* **Idle frames:** the draw loop must request frames only while the pointer is
  moving, a key is held, or a spring is still settling, and must stop. The
  existing code already does this for the scroll-driven camera. Copy that
  pattern, do not invent a new one.
* **Keyboard parity:** arrow keys or tab must move the light between marks. The
  reveal must not be pointer-only.
* **Touch parity:** a tap places the light. This already exists for chords.
* **Reduced motion:** under `prefers-reduced-motion: reduce`, the light snaps
  instead of springing. It does not disappear, because it carries information.
* **Check:** a new check asserting that every chord the torch can draw
  corresponds to a link recorded in the build's emitted link data, and that the
  count of drawable chords equals the recorded link count.
* **Falsification:** two cases. One deletes a link from the emitted data and
  requires the count check to fail. One makes the renderer draw a chord with no
  backing record and requires the same.
* **Risk:** medium. This is the package most likely to breach the idle-frame
  invariant. Measure after every commit, not at the end.

### WP4: the provenance root system

Render the lineage of a figure as a rooted structure rather than a table: filing
to input to schedule to figure, drawn from the recorded chain.

* **Where:** a new emitter in `build/build_site.py` writing a static SVG, in the
  manner of the existing figures, plus a scope in `figures.css`. **Check 5 fails
  the build if a figure appears on a page without a colour scope in
  `figures.css`.** That check exists because exactly this was forgotten once and
  a figure rendered in default black.
* **Static first:** build it as a static SVG that is correct with JavaScript
  disabled, then add interaction on top.
* **Check:** every node in the drawn tree corresponds to a record in
  `content/valuation-inputs.json` or `content/valuation-output.json`, and every
  recorded ancestor of the figure appears in the tree.
* **Falsification:** remove one ancestor from the data and require the check to
  name the missing node.
* **Risk:** medium. High value, because it turns the site's best analytical
  piece into its best visual one.

### WP5: depth on the shell

Layering, edge treatment and a sense of recession on the page shell itself, in
the archival register: the feel of a document in a folder in a drawer.

* **Where:** `site.css`.
* **Constraint:** `--radius` stays `0px`. No drop shadows that imply material
  the rest of the system does not have. Depth through value and rule weight,
  not through blur.
* **Risk:** low, and easy to overdo. Stop before it looks like a UI kit.

---

## 8. Out of scope

Do not, without going back to the owner first:

* touch `admin.html`. It is the owner's editor, it is protected by check 33,
  and four falsifications exist specifically to keep the build from writing to
  it.
* touch anything under `applications/`. It is not part of the site's design.
* change `content/pieces.json` other than through the editor. It is the content
  record.
* add a dependency, a package, a font, or any file loaded from another origin.
* change the theme names, the theme control's behaviour, or the stored-choice
  logic. It is measured by the audit and has its own register row.
* rewrite `atlas.js` or the sphere from scratch. Extend them.
* introduce a new hue. See 5.2.
* merge to `main` before 17 September 2026. See 1.7.

---

## 9. Verification protocol

Per commit, not per pull request:

```
python3 build/build_site.py && python3 build/build_site.py | grep "rewrote: nothing"
```

Before opening the pull request, the full chain:

```
python3 build/build_site.py
python3 build/negatives.py --jobs 3
node build/audit.js
node build/audit.js --falsify
python3 build/claims.py --record-run 1
python3 build/build_site.py
python3 build/build_site.py | tee /tmp/again.log && grep -q "rewrote: nothing" /tmp/again.log
```

Then, by hand, requirements 8 through 13 in section 4.

**In the pull request body, state the before and after for every number you
moved, with its denominator.** That is the house convention and it is not
optional. "Improved contrast" is not a finding. "The smallest text token moved
from 4.9:1 to 5.4:1 on the worst of the three surfaces it sits on" is.

State the hostile case first: the strongest argument a sceptical reviewer would
make against the change, before the argument for it.

---

## 10. Provenance and attribution

Two requirements, both non-negotiable on a site with this thesis.

**Do not ship the reference images.** The mood references are promotional art
belonging to Remedy Entertainment, CD Projekt and Rockstar Games. They are
research input, held locally. No frame, texture, colour sample lifted from a
screenshot, or derivative of one goes into the repository.

**Record the derivation.** `colophon.html` already carries a ledger naming where
every mark and every glyph on this site came from. If the visual language now
owes something to a named source, the colophon says so, in one line, the way it
already does for everything else. A portfolio arguing for auditable provenance
cannot have an unsourced visual identity. This is the cheapest possible fix and
skipping it is the single most damaging thing you could do here.

---

## 11. Repository glossary

| Term | Meaning here |
|---|---|
| **check** | one of 41 assertions in `check_site()`. Fails the build and names itself |
| **falsification / negative** | one of 70 cases in `build/negatives.py` that breaks the tree and requires a named check to catch it |
| **the register** | the table on `colophon.html` and `controls.html` printing every check with its denominator and its when-false condition |
| **denominator** | how much a check looked at. A pass without one is not reported |
| **the instruments** | the home sphere and the Atlas |
| **chord** | a drawn line between two marks, meaning one document's prose links to the other |
| **origin** | a document's provenance class: independent, coursework, tool, or the author's own entry |
| **the two faces** | `OBSIDIAN` and `ARCHIVAL LIGHT` |
| **the two lights** | `--lamp-cool` and `--lamp-warm` |
| **idempotence** | a second identical build rewrites nothing. Enforced by the workflow |
| **piece** | an entry in `content/pieces.json` |

---

## 12. If you disagree with this brief

Say so in the pull request, with the measurement that supports you. This
repository's convention is that the evidence decides, and a brief written
without seeing your work is not privileged over a result. What is not open is
section 1: those are invariants, and a change that breaks one is rejected on
sight regardless of how it looks.
