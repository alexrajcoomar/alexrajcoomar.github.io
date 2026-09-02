# Atlas — three directions, the evaluation, and the decision

Written for Alex, who was not present. Every judgment call I made in his
absence is recorded at the bottom, and the two rejected directions are kept as
working prototypes so the roads not taken can be walked.

---

## The problem, restated from measurement rather than impression

Phase 0 (`_audit/phase0-pipeline.md`) says the desktop Atlas is healthy:
Lighthouse 97 performance, 100 accessibility, 60 fps dragging all 1,250 marks,
zero console errors. This was never a rescue job.

The holes are elsewhere, and they are structural:

1. **There is no globe below 900px.** At 820px — an ordinary tablet — the page
   is a wall of 1,250 undifferentiated links with the explanatory key hidden
   alongside the sphere. The thesis is *every section of everything, on one
   sphere*, and on a large fraction of screens there is no sphere.
2. **First-run comprehension is near zero.** A reader who has not been told
   what the marks mean is given a rotating field of dots and a hover card.
   Nothing on the page argues that the position of a mark carries information.
3. **The list has no hierarchy.** 1,250 items at one size, one weight, one
   colour, opening on the largest coursework document.
4. **Mobile first paint is 3.1s against a 2.5s budget**, because the page is a
   276KB document — the direct cost of the (correct) decision to make the page
   its own dataset.

A redesign that only makes the sphere prettier addresses none of these.

---

## Direction A — One Continuous Space

**Prototype:** `_audit/prototypes/direction-a.html` · **Spec:** `direction-a.md`

**Concept.** There is one space and one camera: the sphere, a document and a
section are three depths of the same continuous dolly, not three pages. Every
mark visible at the far view is the same mark you fly toward, and you can keep
your eye on it the whole way in, because nothing cuts, fades or reloads.

**Interaction model.** A single number `depth ∈ [0,2]` drives a real
perspective camera at distance 6.0 → 1.90 → 1.71 sphere radii, with distance
and focal length interpolated in log space. Click a document, scroll, pinch,
press Enter on a keyboard selection, or pick a search result — all four call
the same tween.

**First five seconds.** A large annotated instrument with a document index down
the left, ordered independent work first. It reads as a machine you are
expected to operate.

**Search.** Lights matches across the sphere without moving the camera;
Enter flies to the selected result, arcing across and down into another
document.

**Labels at density.** Adaptive column bands, `⌈n·gap / 0.74h⌉` clamped by
available width, with a forward/backward ladder inside each band. Measured: all
92 sections of the worst-case document are named at 768px and wider.

**Technical cost.** ~1,150 lines of vanilla JS, 21.4KB gzipped. Replaces the
orthographic projection with a perspective one, which means the label placer,
the hit test and the depth cueing all get rewritten. 60fps held; 3.41ms/frame
with 1,250 marks and 92 laddered labels.

**390px.** A 60px orientation glyph over a scrolling document index; the sphere
becomes almost vestigial on a phone.

---

## Direction B — The Index Is the Artwork

**Prototype:** `_audit/prototypes/direction-b.html` · **Spec:** `direction-b.md`

**Concept.** The 1,250 headings are the page — one continuous typographic
field ordered north pole to south, with size, weight and tone carrying heading
level, document size and provenance. The sphere shrinks to a 288px instrument
in the margin, bound to the field in both directions.

**Interaction model.** Scroll the field and the sphere turns to keep up; drag
the sphere and the field travels, weighted continuously by
`wᵢ = max(0, f·cᵢ)⁹` over all fifty centroids. Hover lights a point; focus
rotates to it.

**The real discovery.** `atlas.py` lays centroids on a Fibonacci lattice, so
document index *is* descending latitude — region 0 sits at `y=+1.000`, region
49 at `y=-1.000`. Reading the page top to bottom is walking the sphere pole to
pole. Every binding in this direction follows from that one fact, and it is a
genuine insight about the data rather than a design conceit.

**Search.** The field contracts 33,085px → 23,472px; matches gain presence,
non-matches recede rather than vanish, so the reader keeps the whole.

**Technical cost, and the problem.** 4,538 DOM nodes. Search reflow is
**300–430ms per settled query on throttled mobile, ~390ms of it layout** — a
whole-document relayout of a 33,000px inline flow. The standard fix,
`content-visibility: auto`, was tried and correctly rejected: it turns block
offsets into estimates, and block offsets *are* the drag mapping. The defect is
structural, not an optimisation that was skipped.

**What it gives up.** A mark on the sphere **travels and focuses rather than
navigating**, because a 4px target that navigates away mid-scrub is hostile.
Defensible, and honestly documented — but it means the sphere stops being the
thing the headline advertises.

---

## Direction C — The Wall Label

**Prototype:** `_audit/prototypes/direction-c.html` · **Spec:** `direction-c.md`

**Concept.** The Atlas opens as a curated exhibition of its own corpus: six
staged views, each holding the sphere at a deliberate rotation and zoom while a
wall label beside it makes one concrete, checkable claim about what you are
looking at — including the two places where the encoding breaks down. When the
labels run out they step aside and leave you in free exploration with a sphere
that now means something.

**Interaction model.** Stepping, not scrolling. Six numbered plates advance on
`→` / Space / button / swipe. A permanent gallery guide lists all six, doubling
as progress bar, table of contents and skip control. `Esc` or `/` leaves
instantly; `localStorage` means a returning visitor opens in free mode;
`#label-3` is shareable.

**The thing that makes it work.** Each stop draws its **construction geometry**:
the 36° cap circle of the largest document, the two case guides 57° apart with
both caps drawn and the shared headings haloed in the gap, seven dotted
geodesics fanning from the AFM 291 template knot, the 34°N parallel that
separates independent work from everything else at 284/287. The claim and the
picture become one object. A caption asserts; this demonstrates.

**Every number is derived at runtime** by `computeFacts()` from the data,
including finding the best separating latitude by F1. A label cannot drift from
the sphere because it does not know its own numbers.

**Search.** Drops straight out of the sequence into free mode from any stop.

**Technical cost.** 17.0KB gzipped, 61fps dragging all 1,250 marks, 215ms to
first frame. In production it reads the existing `.apt`/`.areg` DOM instead of
fetching, so the no-JS fallback is untouched. The real recurring cost is
**editorial**: six paragraphs that must stay true and stay worth reading.

**390px.** The strongest of the three, verified in my own screenshots. A guided
path needs no precision pointing, so the phone gets the full sphere staged and
legible rather than a shrunken canvas or a glyph.

---

## Evaluation

Scored 1–5. The last row is not in the original list of criteria; I added it
because the tiebreak rules name it as decisive.

| | A · Continuous Space | B · Index as Artwork | C · Wall Label |
|---|---|---|---|
| Originality | 5 | 5 | 4 |
| Usability | 3.5 | 3.5 | **4.5** |
| Aesthetic quality | 4.5 | 3.5 | 4.5 |
| Feasibility in this codebase | 3 | 2.5 | **4.5** |
| Fit with existing identity | 4 | 4 | **5** |
| Makes data relationships legible | 4.5 | 3 | **5** |
| **Total** | 24.5 | 21.5 | **27.5** |

### Why B is rejected

Two reasons, either sufficient.

**The performance defect is structural.** 300–430ms of layout per search query
on a throttled phone is not a missed optimisation; the agent found the correct
fix and correctly refused it, because the mapping that makes the direction work
depends on the very offsets that fix would estimate. Under the tiebreak rule
that usability and feasibility outrank originality, a concept whose core
mechanism and whose performance requirement are in direct conflict loses.

**It demotes the sphere.** The page's headline is *every section of everything,
on one sphere*, and B makes the sphere a scrubber in the margin whose marks do
not navigate. That is a coherent page — but it is a different page, and it
argues against its own title.

What B found that survives: the latitude ordering insight (C uses the same fact
in its fifth label, derived independently), and the demonstration that the list
deserves real typographic hierarchy. Both are carried forward.

### Why A is rejected as the spine, and kept as a graft

A is the most technically impressive of the three and its legibility win is
real: flying into a document names all 92 of its sections, against today's
eight. But it answers the wrong question first. A reader who does not yet know
that position means anything is given a more elaborate way to move through a
space whose meaning has not been established. It improves *exploration* for
someone already convinced, and Phase 0 says the deficit is *comprehension* for
someone who is not.

Its cost is also the highest: swapping orthographic for perspective projection
rewrites the label placer, the hit test and the depth cueing at once, on a
renderer that currently holds 60fps and has zero console errors.

### Decision: C as the spine, with A's depth model grafted in

This is a combination, and the brief permits combinations only if the result is
coherent rather than stapled. Here is the test.

C's weakness is the steady state: after six labels it hands the reader back to
today's sphere. A's strength is precisely the steady state: a camera that makes
Sphere → Document → Section legible by moving through it.

**They are the same mechanism used for two purposes.** C's staged views *are*
camera positions solved from a target vector. A's flight *is* a camera move.
Building one camera and using it twice — held by the author during the labels,
driven by the reader afterwards — is one system, not two. The wall label
sequence is the guided first run; when it hands over, the reader inherits the
same camera and can fly into any document. That is the coherence test passed,
not finessed.

**One deliberate reduction.** I am not taking A's perspective projection. The
camera will fly by interpolating rotation-to-front, scale and a focus filter on
top of the existing *orthographic* projection. This gets most of A's legibility
win — a document's cap brought forward, magnified and fully named — while
preserving the renderer that already holds 60fps with no console errors. Full
perspective is a larger rewrite than the remaining gain justifies. Recorded as
assumption A2.3 below.

**From B, two cheap grafts:** real typographic hierarchy and document metadata
in the List view, and independent-work-first ordering. Both fix named Phase 0
findings and neither imports B's performance problem.

### If all three had been mediocre

They were not. All three run against the real 1,250 points, all three hold
60fps, all three have zero console errors, and each is genuinely a different
interaction model rather than a skin. No fourth direction was needed.

---

## Assumptions made in Alex's absence

**A0.1 · No framework, ever.** The footer claims "hand-written HTML and CSS, no
framework". Any direction needing three.js or a build step was disqualified on
identity grounds before feasibility was considered.

**A0.2 · "Interaction ready under 2.5s on a mid-tier connection"** is read as
Lighthouse mobile FCP under the standard mobile throttle.

**Corrected after Phase 2.** My Phase 0 baseline of 3.1s was measured against a
local server that does not compress. GitHub Pages does. Re-measured with gzip
on — 66KB of HTML on the wire rather than 276KB — the real baseline is
**mobile FCP 1.7s, performance 99, desktop 100**. The budget was never in
danger and I nearly designed around a problem that does not exist. The honest
consequence is the opposite of what I first wrote: there is no weight headroom
to spend, because the page is already at 99/100. Every byte Phase 3 adds has to
earn itself against a page that is currently perfect on this axis.

**A0.3 · "Do not regress the baseline"** is read as: no metric may get worse,
and the mobile FCP overage must improve rather than merely hold.

**A1.1 · The three directions were assigned, not free-invented.** Three agents
briefed to "invent a direction" would very likely have produced three sphere
variants. I fixed one interaction model per agent — continuous zoom, typographic
inversion, authored sequence — and let each make its own the best version of
itself. This is why they are genuinely different.

**A2.1 · Comprehension outranks exploration.** The decisive judgment. Phase 0
shows a page that is pleasant to operate and almost impossible to understand
cold. I have ranked "a first-time reader learns what a mark means" above "a
returning reader moves faster".

**A2.2 · The sphere must remain the primary object.** I treated any direction
that demotes it as arguing against the page's own headline. This is what
decided against B more than the performance defect did.

**A2.3 · Orthographic, not perspective.** The camera flies by interpolating
rotation, scale and focus rather than by changing projection model. A cheaper
90% of A's benefit on a renderer that is already correct.

**A2.4 · The tour must never be mandatory.** It is skippable from the first
frame, remembered across visits, and search always exits it. A guided path that
cannot be refused is an obstacle, not an argument.

**A2.5 · Editorial maintenance is accepted as a real cost.** Six wall labels
must stay true. Mitigated by deriving every quoted number from the data at
runtime, so a label cannot silently drift from the sphere — but the prose
itself is a maintenance surface a mechanical page would not have.
