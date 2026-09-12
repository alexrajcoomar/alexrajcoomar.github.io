# System architecture and creative brief

**For:** a creative technologist working in a separate workspace, without access
to the conversation that scoped this.
**Repository:** `alexrajcoomar/alexrajcoomar.github.io`, served at
https://alexrajcoomar.github.io
**Written:** 12 September 2026, against commit `26f0084`.
**Every number below** was read out of the repository at that commit. If one no
longer holds, the repository is right and this file is stale. Say so rather than
working around it.

---

## 1. The world this is set in

The author builds financial arguments the way other people build maps of a
haunted town. The interest in Alan Wake and The Witcher is not a hobby that
leaked into a portfolio. It is the same instinct that makes someone want to
audit a deferred tax note: the conviction that a real structure sits underneath
the surface, that it can be reached, and that reaching it is the whole pleasure.

Three images matter, and each one is a claim about how knowledge works.

**The torch in the dark.** Something true is already there. You do not create it
by looking. You carry a light and the light decides what you can currently
account for. Everything outside the radius still exists.

**The roots under the tree.** The structure that holds a thing up is older and
larger than the thing, and it is usually underground. Trace it and the canopy
stops being mysterious.

**The evidence board.** Pinned documents with string between them. The string is
not decoration. It is a claim that this connects to that, and the claim can be
wrong, and someone can check it.

This site should feel like all three. Not because they are attractive images,
though they are, but because they are already what it does.

---

## 2. Why the atmosphere here can be real

Here is the thing worth understanding before you write any code, because it is
the mandate and everything else in this file follows from it.

**In a game, the fog hides nothing.** The level was authored to look good under
a torch. There is no ground truth beneath the mist. The atmosphere is a
photograph of investigation, and it is beautiful, and it is fake. That is fine.
It is a game.

**On this site there is something under every number.** Every figure comes from
a recorded chain: a filing, an input file, a schedule, a computation, an
assertion that fails the build when the chain breaks. Pull one input out of
`content/valuation-inputs.json` and a figure changes, a check screams, and the
deploy does not happen. The roots here are load-bearing. The string between the
pinned documents is extracted from the documents' own prose at build time.

So the mandate is not *make it feel like the game*. It is:

> **Be the thing the game is depicting.**

An atmosphere that reveals real provenance is doing something no game has ever
done, because no game has anything to reveal. That is the ambition here, and it
is a larger one than pastiche. If a visitor comes away thinking "that looked
like Alan Wake," the work half succeeded. If they come away having *found
something*, and having noticed that the finding was there before they looked, it
fully succeeded.

### The fusion is one idea, not two

Swiss Modernism is the site's grammar. That is not a second, competing taste
bolted onto the first. Swiss design is the grammar of **instruments**: a Braun
dial, a railway clock, an aircraft panel. Those objects are beautiful because
nothing on them is decorative. Every mark is load-bearing, and the discipline of
removing everything else is what produces the calm.

That is the same principle as an audit. It is the same principle as the torch
that reveals rather than invents.

**"Nothing decorative" is simultaneously the Swiss rule, the audit rule, and the
reason the cinematic atmosphere can be honest here.** Forensic Noir and Swiss
Modernism are not being reconciled. They were always the same sentence.

---

## 3. The physics of this world

Every world has rules that cannot be broken from inside it. These are this
one's. They are not bureaucracy layered on top of the design. They are the
reason the design means anything, and each one has been violated at least once
here, which is why it is written down.

### 3.1 The pages are grown, not written

Most root `.html` files are **output**. `build/build_site.py` is 7,222 lines and
regenerates them on every run. Edit `index.html` directly and your change is
reverted on the next push.

Visual work belongs in `build/build_site.py` (structure), `site.css`
(presentation), `site.js` and `atlas.js` (behaviour), or `figures.css` (a
figure's colour scope). The converted documents listed in `content/pieces.json`
are authored files that the build wraps rather than rewrites. Check that file
before assuming which kind you are holding.

### 3.2 The world is stable when nobody is looking

The build runs a second time and the workflow greps its log for
`rewrote: nothing`. If an identical run produces a different byte, nothing
deploys. Never call `random` or `datetime.now()` on a path that writes a file.
Sort your keys. Derive from recorded data.

### 3.3 Stillness is the default state

`build/audit.js` wraps `requestAnimationFrame`, loads each page, lets it settle,
and counts frames requested during one idle second. Every page currently records
zero.

This is the constraint most likely to collide with the aesthetic as first
imagined, so here is the resolution rather than the prohibition. **Drifting mist
is ambient motion: the page performing atmosphere at a reader who is not doing
anything.** It is also, on reflection, the least interesting version of the
idea, because it moves whether or not anyone is investigating.

What this world does instead is **respond**. A light that moves because the
reader moved it is dramatically stronger than a light that wanders on its own,
and it is the honest version: the torch is the reader's, not the site's. Motion
must be driven by a pointer, a scroll, a focus change or a key, and must stop
requesting frames when the input stops. Static depth is unlimited. Gradients,
vignettes, grain baked into a `data:` SVG, layered value, heavy atmospheric
falloff: all free, all still.

### 3.4 The world is sealed

Zero requests leave the origin. No CDN, no remote font, no analytics, no
external texture. Fonts are already subset and self-hosted. Anything you add
lives in the repository. The audit counts this on every page and the count is
currently zero everywhere.

### 3.5 Darkness never costs legibility

Check 36 reads the colour tokens out of `site.css`, composites both ambient
light layers over the paper at full strength, and requires every text token to
clear **4.5:1** on every surface it can sit on, in both faces. A control's
border must clear **3:1**, because on a control the border is the only thing
telling a reader the control exists.

Add an overlay and check 36 composites it and re-measures. This is not a
limitation on drama. Cinematographers work to exactly this discipline: the
deepest shadow in a well-graded frame still holds detail. Design to the floor
from the first commit rather than discovering it at the end.

### 3.6 The records are testimony, not configuration

`content/audit.json`, `content/negatives.json`, `content/invariants.json`,
`content/metrics.json` and `content/fingerprints.json` are what the tools
observed. Editing one by hand to make a check pass is the exact failure this
site exists to argue against, and it is visible in the diff. Change the thing
being measured, then re-run the tool that writes the record.

### 3.7 Nothing merges before 17 September 2026

Waterloo co-op applications for the January to April 2027 term close that
morning, and this site is linked from letters already submitted. Work on a
branch, open a pull request, and leave the merge to the owner.

---

## 4. The language already spoken here

### 4.1 The palette is a vocabulary, not a mood board

Three hues carry one exclusive meaning each, recorded in the stylesheet and
printed in the colophon:

* **Violet `--link` `#5a36c9`** means one thing: a link one document's prose
  makes to another. It is the colour of the chords on both instruments, of the
  key entry that names them, and of the link counts in a mark's card. Nowhere
  else. It was chosen because no figure on the site had spent it.
* **Cobalt `--cobalt` `#0047ab`** means one thing: two capabilities evidenced by
  the same piece.
* **Accent blue `--accent` `#14509b`** means independent work, and every
  navigational link.

Green is the tools. Amber is a heading several documents carry. Orange and blue
are the two anchors of one specific figure. Red and blue are inside and outside
a number in another.

This is a language with a working grammar, and it is the reason a reader can
learn to read the instruments at all. **A new hue is not forbidden. It is
expensive.** It costs a claimed meaning, a contrast proof, and a colophon entry,
the same way every existing hue paid. If you have a genuinely new relationship
to express, name it and buy it. If you want teal because teal is atmospheric,
the answer is no, and the reason is that "because it looked good" is the
sentence this entire site was built to stop saying.

### 4.2 The two lights already exist

```
--lamp-cool: rgba(20,80,155,.05)   the cool wash behind the instrument
--lamp-warm: rgba(190,168,120,.16) the warm reading light behind the type column
```

There is already a two-light model here: cool over the instrument, warm over the
reading. They are gradients on elements that already exist rather than layers
added to carry them, they touch no text colour, and check 36 composites both
before measuring.

In this system's terms, the atmospheric direction you have been given is a
request to **make those two lights do far more work**. That is a legitimate,
well-scoped and genuinely exciting change. Extend the model. A separate fog
layer stacked on top is the weaker move and the one that fails check 36.

### 4.3 The full token set

Light values, with the measured ratios the stylesheet records:

| Token | Value | Role |
|---|---|---|
| `--paper` | `#faf9f6` | page ground |
| `--panel` | `#f2f0e9` | raised surface |
| `--panel-2` | `#ebe8df` | second raised surface |
| `--ink` | `#16150f` | body text, 18.4:1 |
| `--ink-2` | `#55524a` | secondary, 7.5:1 |
| `--ink-3` | `#66635a` | smallest text, 4.9:1 on its worst surface |
| `--rule` | `#ddd9cf` | hairline, decorative |
| `--rule-strong` | `#bfb9aa` | heavier hairline, 1.9:1, never a control border |
| `--edge` | `#8a847c` | the border of anything interactive, 3.3:1 on panel |
| `--tool` | `#0f6b58` | the interactive tools |
| `--ref` | `#8a5410` | reference material |
| `--radius` | `0px` | editorial. No rounded corners anywhere |
| `--shell` | `76rem` | outer width |
| `--measure` | `38rem` | reading measure |
| `--meta-size` / `--meta-track` / `--meta-weight` | `.72rem` / `.08em` / `560` | the metadata grammar |

### 4.4 The two faces are both finished

`OBSIDIAN` and `ARCHIVAL LIGHT`, chosen by a two-state control that writes
`data-theme` on the root and stores the choice. With no stored choice,
`prefers-color-scheme` decides, which means **you do not control which face a
given reader lands on.**

Resist the temptation to treat OBSIDIAN as the real design and ARCHIVAL LIGHT as
a concession. A reader arriving in the light face must get a finished,
atmospheric, confident object, not a washed-out print of the dark one. The
archival register has its own drama available to it: heavy rules, deep ink, a
warm lamp on cream, the feel of a document pulled from a drawer under a desk
lamp. Different light, same investigation.

There is a practical edge to this. The people opening this site in the next four
months include partners at accounting firms. The atmosphere has to read as
**instrument craft**, not genre homage. A well-made instrument that happens to
be lit dramatically is compelling to that reader. Fan art is not. If a component
would look at home in a game's launcher, it is wrong; if it would look at home
on an aircraft panel or in a forensic report, it is right. That is the line, and
it is an aesthetic line before it is a commercial one.

---

## 5. Where the author's voice actually lives

This section exists because "add personality" usually produces decoration, and
there are four places here where it produces structure instead.

**He is already in the data model.** The author is not a footer credit. He is a
fourth origin zone on both instruments, placed by the same geometric rules as
every document, carrying a polar datum mark, linking to `about.html#author`.
`build/atlas.py` treats `author` as a first-class surface alongside
`independent`, `course` and `personal`. The most personal thing on this site is
already expressed as a placement rule. Extend that idea before adding anything
that sits outside the system.

**The naming register is the voice.** OBSIDIAN. ARCHIVAL LIGHT. The register.
The descent. Chords. The two lights. Falsifications. This site names things the
way a field manual names things, and that voice is more distinctive than any
visual treatment. New components get named in that register or they read as
imported.

**Stating the hostile case first is a personality trait.** Every write-up in this
repository opens with the strongest argument against itself. That is unusual,
it is the author's, and it should survive into anything the visual layer says
about itself.

**The colophon is where the influence gets said out loud.** `colophon.html`
already carries a ledger naming the derivation of every mark and glyph. If the
visual language comes to owe something to Remedy's dossier typography or to a
root system, the colophon says so in one line, the way it already does for
everything else. Naming your influences is more confident than hiding them, and
on a site arguing for auditable provenance, an unsourced visual identity is a
self-inflicted wound.

---

## 6. Open problems

This section deliberately does not prescribe solutions. It names problems worth
solving, states what a good answer achieves, and leaves the form to you. If you
see a better form than anything implied here, build that and prove it.

### P1. Illumination as query

**The problem.** The site's connective tissue exists but is quiet. A reader has
to already care before they discover that hovering a mark draws its real
citations.

**What a good answer does.** Makes the act of investigating physical and
immediate. The reader carries something, and what it touches gives up its
provenance: where a number came from, which check holds it, what links here.

**The invariant that gives this its meaning.** The light is a lens, never a
source. Everything it reveals must already be in the document and reachable
another way: by clicking, by keyboard, and with JavaScript disabled. This is not
an accessibility tax. It is the difference between revealing a truth and
performing one, and it is the whole thesis in a single rule.

**Where.** `site.js` and `atlas.js`, both 2D canvas, both with existing
hit-testing and chord rendering. Add a light term to an existing draw.

**Acceptance.** Idle frames stay at zero. Keyboard moves the light between marks.
Touch places it. Under `prefers-reduced-motion` it snaps rather than springs,
and does not disappear, because it carries information. A new check asserts
every drawable chord corresponds to a recorded link and that the drawable count
equals the recorded count. Two falsifications: delete a link from the data, and
make the renderer draw one with no record. Both must be caught.

### P2. The root system

**The problem.** The Dollarama valuation is the strongest analytical work here
and its provenance is rendered as tables. The lineage from filing to input to
schedule to figure is real, recorded, and currently invisible.

**What a good answer does.** Makes the chain legible as structure. A reader sees
that the figure is held up by something, and can follow it down.

**Where.** A new emitter in `build/build_site.py` writing a static SVG, plus a
scope in `figures.css`. **Check 5 fails the build if a figure appears without a
colour scope there.** That check exists because this was forgotten once and a
figure rendered in default black.

**Acceptance.** Correct and readable with JavaScript disabled, then enhanced. A
check asserts every drawn node corresponds to a record in the valuation input or
output files, and that every recorded ancestor appears. A falsification removes
one ancestor and requires the check to name it.

### P3. The dossier register

**The problem.** The metadata grammar is competent and anonymous.

**What a good answer does.** Gives the site's smallest type a voice: tracked
caps, a status stamp, a rule that means something. Remedy's classified-dossier
lettering is the reference, and this is the cheapest, most reversible way to
move the whole site's register.

**Where.** `site.css`, plus the metadata emitter if a stamp needs markup.
Lowest risk in this document. Ship it first.

### P4. Deepen the two lights

**The problem.** The lamps are subtle to the point of invisibility.

**What a good answer does.** Gives them range, falloff, asymmetry tied to the
instrument's real position, and grain, without touching a text colour.

**Acceptance.** If you add a third light, **add it to check 36's lamp pattern**
so it is composited before contrast is measured. A light the check does not know
about is an unmeasured overlay sitting on text. Add a falsification that raises
a lamp's alpha until a token drops under the floor and requires check 36 to
catch it.

### P5. Depth on the shell

**The problem.** The page shell is flat in a way that reads as unfinished rather
than as restraint.

**What a good answer does.** Recession and layering in the archival register: a
document in a folder in a drawer. Depth through value and rule weight.
`--radius` stays `0px`. No drop shadows implying material the rest of the system
does not have.

### P6. Something not on this list

You are being brought in for a perspective this document does not contain. If
the strongest move is one nobody here has imagined, build it. The requirements
are the same as for everything above: derive it from recorded data, make it
still at rest, keep it sealed, hold the contrast floor, give it a check, and
falsify the check. Meet those and the form is entirely yours.

---

## 7. Architecture reference

```
content/*.json  (declared data and recorded measurements)
      |
      v
build/measure_plan.py     decides what actually needs re-measuring
      +--> build/measure.js   opens changed pieces in Chromium, records size and shape
      +--> build/cards.js     redraws link-preview cards whose titles changed
      v
build/build_site.py       writes the shell pages, then check_site()
      |                   41 checks, each tallying a denominator
      v
build/negatives.py        70 falsifications: breaks the tree on purpose,
      |                   requires the build to refuse and name the right check
      v
build/audit.js            loads every page in Chromium, records what it measures
build/audit.js --falsify  breaks each runtime claim, requires the measurement to fail it
      v
build/claims.py           records the run
build/build_site.py       second pass, prints the records onto the pages
build/build_site.py       third pass, must rewrite nothing
      v
commit generated files, package the tree, deploy to Pages
```

`check_site()` begins at line 4853 of `build/build_site.py`. There are 41 check
identifiers: `1` through `39`, plus `11a` and `11b`. Each appends through
`_p(id, message)` and records into two structures: `check_site.tally` gives the
denominator, so the register prints "checked 1,247 links across 91 pages" rather
than a bare tick, and `check_site.records` gives the outcome per page per check,
so the controls page can draw one glyph per pair.

`build/negatives.py` holds exactly 70 cases. Each copies the tree, breaks one
thing, runs the build, and requires the build to fail *and name the check that
should have caught it*. A falsification the checks miss fails the run. This is
what makes the register a test of controls rather than a list of intentions.

**A check without a falsification is not finished.** Add at least one case per
check you add: the minimal edit that should make your check scream.

---

## 8. Acceptance criteria

| # | Command | Requirement |
|---|---|---|
| 1 | `python3 build/build_site.py` | exits clean, no check fails |
| 2 | `python3 build/build_site.py` | second run prints `rewrote: nothing` |
| 3 | `python3 build/negatives.py --jobs 3` | every falsification caught and named |
| 4 | `node build/audit.js` | `idle.frames` is 0 on every page |
| 5 | `node build/audit.js` | `ext.external` is 0 on every page |
| 6 | `node build/audit.js` | `errors` is 0 on every page |
| 7 | `node build/audit.js --falsify` | every runtime claim fails when broken |
| 8 | manual | no horizontal scroll at 320, 360, 390, 768, 1440 |
| 9 | manual | both faces complete: every surface, every state, both instruments |
| 10 | manual | keyboard only: everything reachable, focus ring always visible |
| 11 | manual | JavaScript disabled: every document still reachable and readable |
| 12 | manual | print: the ambient lights are already forced transparent. Keep it |
| 13 | `python3 build/emdash.py` | zero em dashes in prose. House rule, and checked |

Requirement 11 deserves emphasis. The instruments enhance a document list that
works without them. A change that makes any document unreachable without
JavaScript is wrong regardless of how it measures.

Full chain before opening a pull request:

```
python3 build/build_site.py
python3 build/negatives.py --jobs 3
node build/audit.js
node build/audit.js --falsify
python3 build/claims.py --record-run 1
python3 build/build_site.py
python3 build/build_site.py | tee /tmp/again.log && grep -q "rewrote: nothing" /tmp/again.log
```

**In the pull request, state the before and after for every number you moved,
with its denominator, and open with the hostile case.** That is the house
convention. "Improved contrast" is not a finding. "The smallest text token moved
from 4.9:1 to 5.4:1 on the worst of the three surfaces it sits on" is.

---

## 9. Out of scope

Without going back to the owner first, do not: touch `admin.html`, which is the
owner's editor, protected by check 33 and four falsifications; touch
`applications/`, which is private working material excluded from the build;
change `content/pieces.json` other than through the editor; add any dependency,
font or asset loaded from another origin; change the theme names or the stored
choice logic; rewrite `atlas.js` or the sphere from scratch rather than
extending them; or merge to `main` before 17 September 2026.

---

## 10. Provenance

**Do not ship the reference imagery.** The mood references are promotional art
belonging to Remedy Entertainment, CD Projekt and Rockstar Games. They are
research input, held locally. No frame, no texture, no colour sampled from a
screenshot, no derivative of one enters the repository.

**Record the derivation.** See section 5. One line in the colophon, the way
every other mark on this site already declares where it came from.

---

## 11. Glossary

| Term | Meaning here |
|---|---|
| **check** | one of 41 assertions in `check_site()`. Fails the build and names itself |
| **falsification** | one of 70 cases in `build/negatives.py` that breaks the tree and requires a named check to catch it |
| **the register** | the table on `colophon.html` and `controls.html` printing every check, its denominator, and its when-false condition |
| **denominator** | how much a check looked at. A pass without one is not reported |
| **the instruments** | the home sphere and the Atlas, both 2D canvas |
| **chord** | a drawn line between two marks: one document's prose links to the other |
| **origin** | a document's provenance class: independent, coursework, tool, or the author |
| **the two faces** | `OBSIDIAN` and `ARCHIVAL LIGHT` |
| **the two lights** | `--lamp-cool` and `--lamp-warm` |
| **idempotence** | a second identical build rewrites nothing. Enforced by the workflow |
| **piece** | an entry in `content/pieces.json` |

---

## 12. Disagreeing with this brief

Everything in sections 4 through 6 is open. If a measurement supports you
against this document, the measurement wins and the document is wrong. That is
the house rule and it applies to briefs as much as to figures.

Section 3 is not open. Those are the physics. A change that breaks one is
rejected on sight, however good it looks, because a site arguing that its claims
can be audited cannot ship a visual layer that cannot be.

The ambition here is not restraint. It is the specific, difficult, uncommon
thing of making rigour feel like atmosphere, in a medium where atmosphere is
almost always the opposite of rigour. That is worth doing well.
