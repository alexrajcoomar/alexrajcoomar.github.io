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
description, its tags, where it belongs, whether it is featured, and which file
it opens. The order of the entries is the order on the site. The editor writes
this file and nothing else.

**`build/build_site.py` is the design.** It reads `content/pieces.json` and
writes the seven pages that list things: `index.html`, `research.html`,
`coursework.html`, `tools.html`, `library.html`, `about.html`, `colophon.html`.
Those seven files are *output*. Editing them by hand is pointless: the next
publish overwrites them.

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
   cache, and then **checks its own work**: every link, every canonical
   address, every icon and every listed file has to resolve, and no page may
   name an address other than this site's. If any of that fails, the rebuild
   goes red and the site keeps serving the last good version.
6. It commits the result. GitHub Pages publishes it.

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
| `build/build_site.py` | Generates the seven listing pages |
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

**The rebuild went red and says something does not resolve.** That is the check
doing its job: a link, an image or a listed file is pointing at something that
is not there. The message names the page and the address. Usually it means a
file was renamed or a piece was added to the list before its file was uploaded.
Fix it in the editor and publish again; the site was never published broken.

**The site did not update.** Check the Actions tab (link above). If the rebuild
failed, the message there says why. Nothing is lost: every version is in the
repository's history and can be restored.

**Something was removed by mistake.** *Remove from the site* only unlists a
piece; the file is still there and the link still works. Add it back from
**Pieces → Add a piece → Add an entry for it**.
