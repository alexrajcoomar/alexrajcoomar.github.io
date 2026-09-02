# -*- coding: utf-8 -*-
"""The change ledger, machine-readable: content/ledger.json.

One entry per piece. What the entry says is computed from the files, not
typed: the class of the piece against the invariance record (untouched,
styling only, copy edits, new), and the readable-text diff between the
baseline tree and the file as it stands now, sentence by sentence. What a
machine cannot know is read from build/ledger-notes.json, which is written by
hand during the pass: the kinds of change made, the sentences struck and the
residue each left, stale-count fixes, measurements before and after, what was
deliberately not done, and the claims the pass would challenge but did not
touch.

The build reads the ledger twice: the invariance check reads each piece's
declared strikes and count fixes, and the colophon prints one sentence from
the summary. Check 16 recomputes every class from the files and refuses the
build when the ledger's classes are stale, so the sentence on the colophon
cannot drift from the tree.

usage: python3 build/ledger.py            rewrite content/ledger.json
"""
import difflib, json, os, subprocess, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "build"))
import invariance  # noqa: E402

NOTES_PATH = os.path.join(ROOT, "build", "ledger-notes.json")
LEDGER_PATH = os.path.join(ROOT, "content", "ledger.json")


def _load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def baseline_text(baseline, url):
    """The readable text of a piece at the baseline commit, from git."""
    try:
        raw = subprocess.run(["git", "show", "%s:%s" % (baseline, url)], cwd=ROOT,
                             capture_output=True, check=True).stdout.decode("utf-8", "ignore")
    except subprocess.CalledProcessError:
        return None
    return invariance.readable(raw)


def text_diff(before, after):
    """Sentence-level unified diff, no context: every changed sentence, and
    nothing that did not change."""
    a = invariance.sentences(before or "")
    b = invariance.sentences(after or "")
    out = []
    for line in difflib.unified_diff(a, b, lineterm="", n=0):
        if line.startswith(("---", "+++", "@@")):
            continue
        out.append(line)
    return out


def build_ledger():
    notes = _load(NOTES_PATH, {})
    content = json.load(open(os.path.join(ROOT, "content", "pieces.json"), encoding="utf-8"))
    pieces = content["pieces"]
    passinfo = notes.get("pass") or {}
    baseline = passinfo.get("baseline")
    classes = invariance.classes(ROOT, pieces)
    entries = {}
    for p in pieces:
        slug, url = p["slug"], p["url"]
        n = (notes.get("pieces") or {}).get(slug) or {}
        entry = {"url": url, "title": p["t"], "class": classes.get(slug, "new")}
        for key in ("changes", "strikes", "count_fixes", "additions", "spellings", "notes", "kept", "challenge",
                    "before", "after", "accepted"):
            if key in n:
                entry[key] = n[key]
        if baseline and os.path.exists(os.path.join(ROOT, url)):
            now = invariance.readable(open(os.path.join(ROOT, url), encoding="utf-8", errors="ignore").read())
            was = baseline_text(baseline, url)
            if was is None:
                entry["text_diff"] = ["(new in this pass: no baseline text)"]
            elif entry["class"] in ("copy", "new"):
                entry["text_diff"] = text_diff(was, now)
            else:
                entry["text_diff"] = []
        entries[slug] = entry
    summary = Counter(e["class"] for e in entries.values())
    ledger = {
        "note": ("Written by build/ledger.py from the files and build/ledger-notes.json. The class of "
                 "every piece is computed against content/invariants.json; the build refuses to run "
                 "when this file's classes are stale. The colophon's sentence about this pass is "
                 "printed from the summary below."),
        "pass": passinfo,
        "summary": {"copy": summary.get("copy", 0), "styling": summary.get("styling", 0),
                    "untouched": summary.get("untouched", 0), "new": summary.get("new", 0),
                    "pieces": len(entries)},
        "pieces": entries,
    }
    json.dump(ledger, open(LEDGER_PATH, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(LEDGER_PATH, "a", encoding="utf-8").write("\n")
    return ledger


if __name__ == "__main__":
    L = build_ledger()
    s = L["summary"]
    print("ledger: %d pieces; copy edits %d, styling only %d, untouched %d, new %d"
          % (s["pieces"], s["copy"], s["styling"], s["untouched"], s["new"]))
