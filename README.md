# My website

This folder **is** the website. Every file in it gets published exactly as it is.
There is nothing to install, nothing to compile, and no command to run.

Live at: `https://alexrajcoomar.github.io`

---

## The pages that hold it together

| File | What it is |
|---|---|
| `index.html` | The home page: the headline, the four statistics, the three sections, six featured pieces |
| `research.html` | Section 1. The data essays and the primer, plus the method pieces |
| `coursework.html` | Section 2. Everything grouped by course, with the coverage table |
| `tools.html` | Section 3. The six interactive tools |
| `library.html` | The full searchable, filterable list of all 21 pieces |
| `about.html` | Bio, what the portfolio demonstrates, contact |
| `reader.html` | Displays any `.md` file in this folder using the site's own typography |
| `404.html` | Shown when an address does not exist |
| `site.css` | The look of all of the above. Change a colour here and every page changes. |
| `site.js` | The search box, the filters, the theme switch, the scroll reveals |

Everything else is a project. Each project is one self-contained `.html` file
named after its web address: `skill-forge.html` is live at
`https://alexrajcoomar.github.io/skill-forge.html`.

Projects do **not** use `site.css` or `site.js`. Each one carries its own styling
inside itself, so changing the site's look can never break a project, and a
broken project can never break the site.

---

## Press `/` anywhere

On any of the pages above, pressing the `/` key opens a search box over the page
that finds any of the 21 pieces by title, course or topic. `Cmd + K` or
`Ctrl + K` does the same. Arrow keys move, `Enter` opens, `Esc` closes.

---

## Adding a new project

**Step 1.** Rename your file to lowercase with hyphens instead of spaces.
`My New Thing.html` becomes `my-new-thing.html`. This becomes its web address,
so keep it short.

**Step 2.** Go to your repository on github.com. Click **Add file**, then
**Upload files**. Drag the file onto the page. Scroll down, click
**Commit changes**.

**Step 3.** Wait about a minute, then open
`https://alexrajcoomar.github.io/my-new-thing.html`. It is live.

At this point the project works but is not *listed* anywhere. To get it into the
right section, the library and the search box, ask Claude: *"add
my-new-thing.html to my site, it belongs under coursework for AFM 291."*
Claude hands back the shell pages that changed and you upload those the same
way. Tell it which section it belongs in, because that is the one thing it
cannot work out from the file.

## Adding research written in Markdown

**Step 1.** Upload the `.md` file exactly like any other file.

**Step 2.** Link to it through the reader, not directly:

```
reader.html?doc=my-paper.md
```

A raw `.md` address makes the browser download the file instead of showing it,
which is the reason `reader.html` exists. The reader handles headings, bold and
italic, links, images, bullet and numbered lists, quotes, tables, code blocks
and horizontal rules. It ignores a YAML block at the top of the file if there is
one, and it prints the word count and a reading estimate.

Ask Claude to add the link into `research.html` so the piece is listed.

## Replacing a file

Upload a file with the same name. GitHub overwrites it. Same one-minute wait.

## Deleting a project

On github.com, click the file, then the trash icon at the top right of the file
view, then **Commit changes**. Ask Claude to regenerate the shell pages
afterwards so it stops being listed.

---

## Things that will save you a support call

- **Nothing appears / an old version appears.** Wait a minute, then reload with
  the cache bypassed: `Cmd + Shift + R`. GitHub takes 30 to 60 seconds to
  publish, and browsers hold onto old copies.
- **Never put a space in a filename.** Spaces turn into `%20` in the address
  and links break. Hyphens only.
- **Never rename `index.html`.** That file *is* the home page.
- **Don't delete `.nojekyll` or `sw.js`.** `.nojekyll` stops GitHub from trying
  to reinterpret your HTML. `sw.js` is what lets the installable apps be added
  to a phone home screen.
- **The reader only works on the published site.** Opening `reader.html` from
  your own disk fails, because browsers refuse to let a local page read local
  files. This is not a bug in the page.
- **Everything here is public.** Anyone with the address can read it, and search
  engines will index it. Do not upload anything with marks, personal
  information, or graded work you have not submitted yet.

---

## Two things worth adding when you have them

- **A LinkedIn or GitHub link.** There is a place for it in the footer of every
  page and in the contact list on `about.html`. It was left out rather than
  guessed at. Send Claude the address and it goes in.
- **A résumé PDF.** Upload `resume.pdf` and ask for a download link in the
  header. It was not built as an empty button, because a link to a file that is
  not there is worse than no link.

---

## What this site is built on

Plain HTML and CSS, served by GitHub Pages. No framework, no build step, no
monthly cost. The counts and statistics on the pages are generated from the
files themselves rather than typed in, so they cannot drift out of date without
the pages being regenerated.

The only outside dependency is the Inter typeface from a public CDN. If that
ever fails, a metric-matched fallback takes over and the page does not shift.
Everything works with JavaScript switched off: the search box and the filters
disappear, and every link, list and page still works.
