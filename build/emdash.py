# -*- coding: utf-8 -*-
"""Em dashes out of the prose of the pieces, by rule.

The site's rule is that no em dash stands in the prose of any page except
the six declared records (check 23). The pieces the last pass touched were
converted then; this converts the rest the same way, and prints what it
did per file so the ledger can carry it.

The rules, applied to each text node of the document in turn, never inside
script, style, pre, code, svg or textarea, never inside a tag, and never to
a dash that stands alone as a cell or a chip (a dash inside quotation marks
is converted like any other: the quoted words do not move):

  - a dash between two digits becomes an en dash (2019–2020);
  - a pair of dashes setting off a phrase in one text node becomes a pair
    of commas, or parentheses when the phrase itself carries a comma or
    opens with a figure;
  - a single dash becomes a colon inside a heading, a table head, a
    caption or a summary, and otherwise a colon before a capital letter, a
    digit, a currency sign, a quotation mark or an opening bracket, and a
    comma before anything else;
  - a dash with nothing after it in its node is dropped with the space
    before it.

No word moves: the invariance check compares sentences with their
punctuation removed, so a converted page holds its record; a dash that was
set tight between two words becomes a comma and a space, which the word
count sees as one word more, so converted pieces are measured again.

usage: python3 build/emdash.py --dry [files...]     report only
       python3 build/emdash.py --write [files...]   convert, print a summary
       (no files: every listed piece that is not a declared record)
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = "—"
EN = "–"
SKIP = {"script", "style", "pre", "code", "svg", "textarea", "noscript"}
COLON_CTX = {"h1", "h2", "h3", "h4", "h5", "h6", "th", "caption", "summary", "figcaption", "dt"}
TOKEN = re.compile(r"(<script\b.*?</script\s*>|<style\b.*?</style\s*>|<textarea\b.*?</textarea\s*>|<!--.*?-->|<[^>]+>)", re.S | re.I)
OPAQUE = re.compile(r"<(script|style|textarea)\b", re.I)
TAG = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9-]*)")
CURRENCY = "$€£¥"
OPENERS = "\"“‘'([‘"


def declared_records():
    try:
        d = json.load(open(os.path.join(ROOT, "content", "declared.json"), encoding="utf-8"))
        return set(d.get("records") or [])
    except Exception:
        return set()


def _inside_quote(text, i):
    """Whether position i sits inside an open quotation in this node."""
    before = text[:i]
    return (before.count("“") - before.count("”")) > 0 or (before.count('"') % 2 == 1)


def convert_text(text, ctx, stats):
    """One text node. Returns the converted text."""
    if DASH not in text:
        return text
    # a dash standing alone: a nil cell, a verdict chip, a placeholder
    if text.strip("  \t\n") == DASH:
        stats["kept alone"] += 1
        return text
    out = text
    # digits either side: an en dash
    def en(m):
        stats["en dash"] += 1
        return m.group(1) + EN + m.group(2)
    out = re.sub(r"(\d)\s?%s\s?(\d)" % DASH, en, out)
    if DASH not in out:
        return out
    # a pair setting off a phrase, when neither dash is in a quotation and no
    # sentence end lies between them
    def pair(m):
        phrase = m.group(2).strip()
        lead, trail = m.group(1), m.group(3)
        if "," in phrase or (phrase and (phrase[0].isdigit() or phrase[0] in CURRENCY)):
            stats["parentheses"] += 1
            return lead.rstrip() + " (" + phrase + ")" + (trail if trail.startswith((",", ".", ";", ":", "?", "!")) else " " + trail.lstrip())
        stats["commas"] += 1
        return lead.rstrip() + ", " + phrase + ", " + trail.lstrip()
    out = re.sub(r"([^%s]*?)\s?%s\s?([^%s.!?]+?)\s?%s\s?(.*)" % (DASH, DASH, DASH, DASH), pair, out, count=0) if out.count(DASH) >= 2 else out
    # singles
    def single(m):
        lead, rest = m.group(1), m.group(2)
        nxt = rest.lstrip()
        if not nxt:
            stats["dropped at end"] += 1
            return lead.rstrip()
        if ctx & COLON_CTX:
            stats["colon in a heading"] += 1
            return lead.rstrip() + ": " + nxt
        if nxt[0].isupper() or nxt[0].isdigit() or nxt[0] in CURRENCY or nxt[0] in OPENERS:
            stats["colon"] += 1
            return lead.rstrip() + ": " + nxt
        stats["comma"] += 1
        return lead.rstrip() + ", " + nxt
    out2 = out
    out = re.sub(r"([^%s]*?)\s?%s\s?([^%s]*)" % (DASH, DASH, DASH), single, out2)
    return out


def convert_html(raw):
    stats = {k: 0 for k in ("en dash", "commas", "parentheses", "colon", "colon in a heading", "comma",
                            "dropped at end", "kept alone", "kept in code")}
    parts = TOKEN.split(raw)
    stack = []
    in_head = False
    for i, part in enumerate(parts):
        if i % 2 == 1:
            if part.startswith("<!--"):
                continue
            if OPAQUE.match(part):
                stats["kept in code"] += part.count(DASH)
                continue
            m = TAG.match(part)
            if not m:
                continue
            closing, name = m.group(1) == "/", m.group(2).lower()
            if name == "head":
                in_head = not closing
            if closing:
                if name in stack:
                    while stack and stack.pop() != name:
                        pass
            elif not part.endswith("/>") and name not in ("br", "hr", "img", "input", "meta", "link", "wbr", "source", "col"):
                stack.append(name)
            continue
        if DASH not in part:
            continue
        if in_head or (set(stack) & SKIP):
            stats["kept in code"] += part.count(DASH)
            continue
        parts[i] = convert_text(part, set(stack), stats)
    return "".join(parts), stats


def prose_dashes(raw):
    """How many em dashes stand in a page's prose: in text nodes outside
    script, style, textarea, pre, code, svg and the head, not counting a dash
    that stands alone as a cell or a chip. Returns (prose, alone, code)."""
    parts = TOKEN.split(raw)
    stack, in_head = [], False
    prose = alone = code = 0
    for i, part in enumerate(parts):
        if i % 2 == 1:
            if part.startswith("<!--"):
                continue
            if OPAQUE.match(part):
                code += part.count(DASH)
                continue
            m = TAG.match(part)
            if not m:
                continue
            closing, name = m.group(1) == "/", m.group(2).lower()
            if name == "head":
                in_head = not closing
            if closing:
                if name in stack:
                    while stack and stack.pop() != name:
                        pass
            elif not part.endswith("/>") and name not in ("br", "hr", "img", "input", "meta", "link", "wbr", "source", "col"):
                stack.append(name)
            continue
        c = part.count(DASH)
        if not c:
            continue
        if in_head or (set(stack) & SKIP):
            code += c
        elif part.strip("  \t\n") == DASH:
            alone += 1
        else:
            prose += c
    return prose, alone, code


def main(argv):
    write = "--write" in argv
    files = [a for i, a in enumerate(argv) if not a.startswith("--") and not (i and argv[i - 1] == "--json")]
    if not files:
        content = json.load(open(os.path.join(ROOT, "content", "pieces.json"), encoding="utf-8"))
        records = declared_records()
        files = [p["url"] for p in content["pieces"] if p["url"] not in records]
    summary = {}
    total_before = total_after = 0
    for f in files:
        path = os.path.join(ROOT, f)
        raw = open(path, encoding="utf-8").read()
        new, stats = convert_html(raw)
        changed = sum(v for k, v in stats.items() if not k.startswith("kept"))
        if changed == 0 and new == raw:
            continue
        summary[f] = stats
        total_before += raw.count(DASH); total_after += new.count(DASH)
        if write and new != raw:
            open(path, "w", encoding="utf-8").write(new)
        print("%-46s replaced %3d  (%s)  kept %d" % (f, changed,
              ", ".join("%s %d" % (k, v) for k, v in stats.items() if v and not k.startswith("kept")),
              sum(v for k, v in stats.items() if k.startswith("kept"))))
    print("%d files; em dashes %d before, %d after%s" % (len(summary), total_before, total_after, "" if write else " (dry run, nothing written)"))
    if "--json" in argv:
        json.dump(summary, open(argv[argv.index("--json") + 1], "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
