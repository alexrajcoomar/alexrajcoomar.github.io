# My website

Live at **https://alexrajcoomar.github.io**

This folder is the website. Adding or changing anything is done from the editor
page, not by editing files here.

---

## The editor

**https://alexrajcoomar.github.io/admin.html**

Bookmark that. It is where every routine change happens:

| What you want to do | Where |
|---|---|
| Add a new piece | **Pieces** → *Add a piece* → drop the HTML file |
| Change a title, description or tags | **Pieces** → click the row → edit on the right |
| Reorder anything | **Pieces** → drag a row, or use the ▲ ▼ buttons |
| Feature something on the home page | **Pieces** → click the row → *Feature it on the home page* |
| Replace a file with a newer version | **Pieces** → click the row → *Replace the file* |
| Upload images or a PDF | **Files** → drop them |
| Take something off the site | **Pieces** → click the row → *Remove from the site* |
| Change the headline, your email, the About text | **Site text** |

Nothing is saved until you press **Publish**. The page tells you what is waiting
to be published before you do. After you press it, GitHub rebuilds the site
itself; the change is usually live within a minute or two.

### The one-time setup

The editor needs a token so it can write to the repository. You make it once:

1. Sign in to GitHub as the account that owns the site.
2. Go to **Settings → Developer settings → Personal access tokens → Fine-grained
   tokens → Generate new token**.
3. Name it *Site editor*. Set the expiry you want.
4. **Resource owner**: the organisation that owns the site.
   **Repository access**: *Only select repositories* → pick this repository.
5. **Permissions → Repository permissions → Contents**: *Read and write*.
   Nothing else.
6. Generate, copy, and paste it into the editor's **Connection** tab.

That token is a password. The editor holds it for the current browser tab only
and forgets it when the tab closes, so expect to paste it again each time you sit
down to publish; that is deliberate, because it keeps a key that can write to the
repository out of long-term storage on the same address that serves the site. It
is sent only to GitHub. **Forget the token** clears it immediately. When it
expires the editor will say so, and you repeat the six steps above.

`admin.html` itself is a public page, but it holds no secret and can do nothing
without a token.

---

## Where content ends and design begins

This is the part worth understanding, because it is what keeps the site from
breaking.

**`content/pieces.json` is the content.** One entry per piece: its title, its
description, its tags, where it belongs, whether it is featured, what it was
built from (one line in the owner's words, rendered at the top of the piece),
and which file it opens. The order of the entries is the order on the site. The editor writes
this file and nothing else.

**`build/build_site.py` is the design.** It reads `content/pieces.json` and
writes the generated pages: `index.html`, `research.html`, `coursework.html`,
`tools.html`, `library.html`, `atlas.html`, `about.html`, `colophon.html`,
`controls.html`, `404.html`. Those files are *output*. Editing them by hand is
pointless: the next publish overwrites them.

**`site.css` is the look.** One stylesheet for the whole site. It is not
generated, and nothing in the editor touches it.

So: content changes in the editor, design changes in `build_site.py` and
`site.css`, and the two cannot collide.

---

## What happens when you press Publish

1. The editor writes `content/pieces.json` and any uploaded files in one commit.
2. GitHub starts the workflow in `.github/workflows/build.yml`.
3. It opens any piece whose file changed in a real browser and counts its words,
   figures, tables and checkpoints. This is why the reading times and the
   statistics on the home page are always right, and why you never type them in.
   Pieces that did not change are not reopened, so a title edit takes seconds.
4. It draws a link-preview card for any piece whose title or description
   changed, so pasting a link into a message or a job application shows the
   piece rather than a grey box.
5. It runs `build/build_site.py`, which regenerates the listing pages, writes
   the head metadata on every piece, refreshes `sitemap.xml` and the offline
   cache, and then **checks its own work**: thirty-odd checks, from every
   link resolving to every number on a generated page being one the build
   computed. Every claim the site makes about itself is a row on
   `controls.html`, beside the check that tests it and its last result.
6. It **falsifies its own checks** (`build/negatives.py`): for each check, a
   copy of the site is edited so the claim is false, and the build must
   refuse, naming that check. A claim prints *held* only while a falsification
   its check caught is on record for the current code; otherwise *untested*.
   This runs only when the checks' code changed.
7. It opens the generated pages and every piece in the browser once more and
   measures what they claim at runtime (`build/audit.js`): nothing requested
   from another origin, nothing moving while idle, focus visible, printing,
   fitting a phone, the offline copy surviving a publish. Then it makes each
   of those claims false on a copy of a page and checks that the measurement
   fails it.
8. It runs the build again and requires it to rewrite nothing, commits the
   result, and only then **deploys** it to GitHub Pages from the workflow. A
   failure anywhere in this chain leaves the last good site live.

You can watch step 2 onwards at
`https://github.com/alexrajcoomar/alexrajcoomar.github.io/actions`. A red mark
there means the rebuild failed; the site keeps serving the last good version
until it is fixed.

---

## The files

| Path | What it is |
|---|---|
| `admin.html` | The editor |
| `content/pieces.json` | **The content.** Every piece, in order |
| `content/metrics.json` | Word, figure and table counts. Written by the rebuild, not by you |
| `content/fingerprints.json` | Lets the rebuild skip pieces that did not change |
| `build/build_site.py` | Generates the listing pages and runs the checks |
| `build/claims.py` | The register of claims, the glyph walls on `controls.html`, the run record |
| `build/negatives.py` | The tests of controls: a falsification per check, and what caught it |
| `build/audit.js` | Measures the runtime claims in a browser; `--falsify` makes each false on a copy |
| `build/atlas.py` | Places every section of every piece on the sphere: an equal area to every section, zoned by origin |
| `build/invariance.py`, `build/ledger.py` | Hold every piece to its record; write the change ledger |
| `build/emdash.py` | The rule that took the em dashes out of the prose |
| `content/audit.json`, `content/negatives.json` | What the browser measured; what each falsification did. Written by the rebuild |
| `content/declared.json` | The named exceptions: the six records kept as written, the pages allowed past 320px |
| `content/invariants.json`, `content/ledger.json` | The record every piece is held to, and the change ledger |
| `build/measure.js` | Counts what is on each page, in a real browser |
| `build/measure_plan.py` | Works out which pieces need recounting |
| `build/cards.js` | Draws the link-preview card for each piece |
| `build/figures.json`, `specimens.json`, `refit.json` | The figures lifted out of pieces and shown on the site's own pages |
| `content/cards.json` | Lets the rebuild skip cards whose text did not change |
| `cards/`, `og-card.png` | The link-preview images. Written by the rebuild |
| `sitemap.xml`, `robots.txt`, `sw.js` | Generated. Do not edit: the next rebuild overwrites them |
| `.github/workflows/build.yml` | The instruction that runs all of the above after every change |
| `site.css` | The look of every listing page |
| `site.js` | The search box, the filters, the theme switch |
| `.nojekyll` | Tells GitHub to publish the files exactly as they are |
| everything else `.html` | A piece. Self-contained, carries its own styling |

Each piece is one self-contained file named after its address:
`skill-forge.html` is live at `https://alexrajcoomar.github.io/skill-forge.html`.
Pieces do not use `site.css`, so changing the site's look can never break a
piece, and a broken piece can never break the site.

---

## Naming files

Lowercase, hyphens instead of spaces, ending in `.html`:
`deferred-tax-ladder.html`. The editor cleans up names it is given, but a name
chosen well stays in the address bar forever, so it is worth a second's thought.

A file's name is its web address. Renaming a published piece breaks every link
anyone has to it, which is why the editor replaces files in place rather than
uploading a second copy under a new name.

---

## If something goes wrong

**The editor says the token was refused.** It expired, or a space was copied
with it. Make a new one; the six steps are above.

**A piece was published but shows no reading time.** Anything under 1,200 words
is treated as an instrument rather than a document and carries no reading time
by design. The colophon explains the rule.

**The rebuild went red and names a check.** That is the check doing its job:
the message opens with `check N:` and names the page and what is wrong (a link
to a file that is not there, a numeral typed where nothing computed it, a
spelling, an em dash in prose). Fix it and publish again; the deploy waits for
the checks, so the site was never published broken. `controls.html` lists
every check with the falsification that proved it can catch what it claims.

**The site did not update.** Check the Actions tab (link above). If the rebuild
failed, the message there says why. Nothing is lost: every version is in the
repository's history and can be restored.

**Something was removed by mistake.** *Remove from the site* only unlists a
piece; the file is still there and the link still works. Add it back from
**Pieces → Add a piece → Add an entry for it**.
