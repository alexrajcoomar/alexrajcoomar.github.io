# -*- coding: utf-8 -*-
"""Decide whether anything needs measuring before the site is rebuilt.

Measuring means opening every piece in a real browser and counting its words,
figures and tables after its scripts have run. That is slow, so it only
happens when a piece's file has actually changed. This script compares each
file's fingerprint against the last recorded one and reports how many pages
are stale, which lets the workflow skip installing a browser on the common
case: an edit to a title or a reordering, where no piece file changed at all.
"""
import hashlib, json, os, re, sys

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELL = {"index.html", "library.html", "about.html", "404.html", "research.html",
         "coursework.html", "tools.html", "reader.html", "colophon.html", "admin.html"}

def load(name, default):
    path = os.path.join(ROOT, "content", name)
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default

# The build adds a return bar and a mobile stylesheet to each piece, and an
# earlier version of the build added the same bar in a slightly different
# shape. All of it is stripped before hashing, and the remaining whitespace is
# collapsed, so the build's own edits never make a page look changed and send
# it back to be measured again.
_INJECTED = re.compile(
    r"<!--__rb-->.*?<!--/__rb-->"
    r"|<!--__rbp-->.*?<!--/__rbp-->"
    r"|<!-- injected by the site build.*?-->"
    r'|<style id="__rb-style">.*?</style>'
    r'|<div id="__rb">.*?</div>'
    r'|<a id="__rb-pill"[^>]*>.*?</a>'
    r"|<script>\s*\(function\(\)\{\s*var p=document\.getElementById\('__rb-pill'\).*?</script>"
    r'|<style id="__mobile_fit">.*?</style>', re.S)

def fingerprint(text):
    return hashlib.sha1(
        re.sub(r"\s+", " ", _INJECTED.sub("", text)).strip().encode("utf-8")).hexdigest()

def fingerprints():
    out = {}
    for f in sorted(os.listdir(ROOT)):
        if not f.endswith(".html") or f in SHELL:
            continue
        out[f] = fingerprint(open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read())
    return out

def stale():
    now  = fingerprints()
    old  = load("fingerprints.json", {})
    seen = load("metrics.json", {})
    return [f for f, h in now.items()
            if old.get(f) != h or f[:-5] not in seen]

if __name__ == "__main__":
    todo = stale()
    out = os.environ.get("GITHUB_OUTPUT")
    line = f"needs={'1' if todo else '0'}\ncount={len(todo)}\n"
    if out:
        open(out, "a", encoding="utf-8").write(line)
    sys.stderr.write(f"{len(todo)} page(s) need measuring"
                     + (": " + ", ".join(todo[:8]) + ("…" if len(todo) > 8 else "")
                        if todo else "")
                     + "\n")
    print(line, end="")
