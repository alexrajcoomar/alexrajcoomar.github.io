# -*- coding: utf-8 -*-
"""The invariance check: what a piece claims may not change under an edit.

Every piece page is content. A pass over the pieces may change how they read
and how they look, but not what they say: not a numeral, not a URL, not a
citation or a standard reference, not a provenance label, not an anchor id,
and not a sentence that states a result, a verdict, a cut-off or a prediction.
This module records those sets for every piece at a baseline and refuses the
build when any of them differs from the record.

The record is `content/invariants.json`. It is written once from the tree
the pass started from (`--baseline`), and a piece's entry is renewed only by
an explicit `--accept <slug>`, which is a content decision and is logged in
the ledger. The build never renews an entry on its own.

Two kinds of edit are allowed to move a set, and only when the ledger
declares them for that piece in `content/ledger.json`:

  "strikes":     sentences removed whole (an assistant's offer to the owner,
                 a "send them and I'll rebuild"), each declared verbatim with
                 the residue it leaves, if any. Every token the strike takes
                 away must be found in the declared text.
  "count_fixes": a stale count about the site itself ("48 pieces"), declared
                 as the exact before and after strings.
  "additions":   text the pass added, declared verbatim: a label declared in
                 a key, a built_from line. Nothing may be lost by an addition.
  "spellings":   word substitutions, declared as exact pairs ("defense" to
                 "defence"). A result sentence that differs from its record
                 only by declared pairs is the same sentence; a sentence that
                 differs by anything else is not.

Anything else that moves a set is a problem, and the build exits non-zero.

Sentences are compared with their punctuation removed, so replacing an em
dash with a comma, a colon or parentheses leaves the sentence's record
unchanged, while any change to a word does not.
"""
import hashlib, html, json, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = os.path.join(ROOT, "content", "invariants.json")
LEDGER_PATH = os.path.join(ROOT, "content", "ledger.json")

# Blocks the build writes into a piece. They are chrome and carry the site's
# own counts, which move on purpose; nothing inside them is a claim of the
# piece. The head is chrome too: the build owns the title and the metadata.
_OWNED = re.compile(
    r"<!--__rb-->.*?<!--/__rb-->"
    r"|<!--__rbp-->.*?<!--/__rbp-->"
    r"|<!--__meta-->.*?<!--/__meta-->"
    r"|<!--__docend[^>]*-->.*?<!--/__docend-->"
    r"|<!--__foot-->.*?<!--/__foot-->"
    r"|<!--__tail-->.*?<!--/__tail-->"
    r"|\s*<!--__from-->.*?<!--/__from-->"
    r"|\s*<!--__long-->.*?<!--/__long-->"
    r'|<style id="__mobile_fit">.*?</style>'
    r"|<!-- injected by the site build.*?-->", re.S)
_HEAD = re.compile(r"<head\b.*?</head>", re.S | re.I)
_CODE = re.compile(r"<(script|style|noscript)\b[^>]*>.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")

# numerals: 1,234 · 0.33 · 2026 · 4-22 is two numerals and keeps both
_NUM = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
# standard references and citations, as tokens with their number attached
_REF = re.compile(
    r"\b(?:IFRS|IAS|IFRIC|SIC|ASPE|CAS|CSAE|CSQM|ISA|ISQM|IPSAS|ASC|SFAS|FAS|SAB|ASU|IRC|ITA|ETA|CBCA|OBCA|"
    r"CPA\s?Canada\s?Handbook|Handbook)\s?(?:Part\s?[IV]+\s?)?(?:Section\s?)?\d+[\w.\-]*"
    r"|¶\s?\d+[\d.\-–,]*(?:\s?(?:to|and)\s?\d+[\d.]*)?"
    r"|\bpara(?:graph)?s?\.?\s?\d+[\w.()\-–]*"
    r"|\b(?:s|ss|sec|sub|subs)\.\s?\d+[\w.()\-–]*"
    r"|\b(?:Section|section|Subsection|subsection)\s\d+[\w.()\-–]*"
    r"|\bSEDAR\+?\b|\bEDGAR\b|\bForm\s(?:10-K|10-Q|8-K|40-F|20-F|6-K)\b"
    r"|\b(?:AIF|MD&A|MD&amp;A)\b"
    r"|\b\d{4}\s(?:ONSC|ONCA|SCC|BCSC|ABQB|FCA|FC|TCC|ONSEC|OSC)\s\d+\b"
    r"|\bR\.?S\.?C\.?\s?(?:1985|\d{4})?,?\s?c\.\s?[\w-]+")
# provenance and verdict labels, in the vocabulary the pieces use
_LABEL = re.compile(
    r"\b(VERIFIED|INFERRED|REPRODUCED|FROM MEMORY|UNDETERMINED|SUPPORTED|REFUTED|CONFIRMED|"
    r"UNVERIFIED|VERIFY|Audit fix|Tutor-added|ESTIMATED|ASSUMED|ASSERTED|DOCUMENTED|COMPUTED|"
    r"OBSERVED|DERIVED|NORMATIVE|POSITIVE|NOT PROBABLE|PROBABLE)\b")
_CHIP_CLASS = re.compile(
    r"(?:^|\s)(?:tag|chip|mchip|pill|badge|kicker|verdict|tier|lbl|label|cw|v|w-badge|step-tag|"
    r"crit-badge|wire-tag|section-label|prov|ev|status|grade|flag)(?:\s|$)")
_CHIP = re.compile(
    r'<(span|b|em|i|strong|small|kbd|abbr|mark|div|p|a|td|th|li|dt|dd|sup)\b[^>]*class="([^"]*)"[^>]*>(.*?)</\1>',
    re.S)
_HEADING = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.S | re.I)
_ID = re.compile(r'\bid="([^"]*)"')
_URL = re.compile(r'\b(?:href|src)="([^"]*)"')
# the vocabulary of a sentence that states a result, a verdict, a cut-off or a
# prediction, beyond the numerals, references and labels it may carry
_VERDICT = re.compile(
    r"\b(?:conclud\w*|verdict\w*|results?|cut-?offs?|thresholds?|predict\w*|forecast\w*|flag\w*|"
    r"refut\w*|support\w*|undetermined|confirmed|wrong|correct\w*|errors?|therefore|thus|hence|"
    r"holds?|fails?|pass(?:es|ed)?|is not|are not|does not|do not|did not|cannot|never|always|"
    r"must|shall|should not|no longer|only)\b", re.I)
_PUNCT = re.compile("[,:;()\\[\\]{}\"'“”‘’—–\\-…·•*_/]")
_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"“(\[])")


_BLOCK_TAG = re.compile(
    r"</?(?:p|li|td|th|div|dd|dt|h[1-6]|blockquote|summary|figcaption|caption|tr|section|article|"
    r"details|ul|ol|table|thead|tbody|header|footer|main|body|br|hr|pre|nav|aside|figure)\b[^>]*>", re.I)


def readable(raw):
    """The body of the piece as text: owned blocks, head, scripts and styles
    removed, block tags turned to line breaks and other tags to spaces,
    entities decoded, whitespace collapsed within lines."""
    t = _OWNED.sub(" ", raw)
    t = _HEAD.sub(" ", t)
    t = _CODE.sub(" ", t)
    t = re.sub(r"\s+", " ", t)              # a line wrap in the source is not a break
    t = _BLOCK_TAG.sub("\n", t)             # a block boundary is
    t = _TAG.sub(" ", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t\r\f\v\u00a0]+", " ", t)
    t = re.sub(r" ?\n ?", "\n", t)
    return re.sub(r"\n+", "\n", t).strip()


def stripped(raw):
    """The file with the owned blocks and the head removed, for the byte
    record. The head is the build's: it stamps asset versions there on every
    stylesheet change and owns the title and the metadata, so a head that
    moved says nothing about the piece."""
    return _HEAD.sub("", _OWNED.sub("", raw))


def norm_sentence(s):
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", s)).strip()


def sentences(text):
    """Split into sentences, for reading: the ledger's diffs use this. A
    block boundary (a line break in the readable text) always ends one."""
    out = []
    for line in text.split("\n"):
        out.extend(s.strip() for s in _SPLIT.split(line) if s.strip())
    return out


def record_sentences(text):
    """Split into sentences for the record. Punctuation other than a full
    stop, a question mark or an exclamation mark is whitespace first, so a
    dash or a colon that once stood beside a sentence end, and is now gone or
    changed, does not move where the sentences begin; a block boundary always
    ends a sentence, so a callout's title and its first sentence are two."""
    out = []
    for line in text.split("\n"):
        line = _PUNCT.sub(" ", line)
        out.extend(s for s in _SPLIT.split(line) if s.strip())
    return out


def is_result(s):
    return bool(_NUM.search(s) or _REF.search(s) or _LABEL.search(s) or _VERDICT.search(s)
                or "“" in s or '"' in s)


def _h(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def extract_text_sets(text):
    """The sets a run of readable text carries. Used both for a whole piece and
    for a declared strike, so what a strike removes can be measured the same
    way the piece is."""
    nums = Counter(_NUM.findall(text))
    refs = Counter(m.group(0).strip().rstrip(",.;:") for m in _REF.finditer(text))
    labels = Counter(m.group(1) for m in _LABEL.finditer(text))
    sents = Counter()
    for s in record_sentences(text):
        if is_result(s):
            n = norm_sentence(s)
            if n:
                sents[_h(n)] += 1
    return {"numerals": nums, "refs": refs, "labels": labels, "sentences": sents}


def extract(raw):
    """Everything the check holds constant for one piece file."""
    body = _OWNED.sub(" ", raw)
    body = _HEAD.sub(" ", body)
    text = readable(raw)
    sets = extract_text_sets(text)
    nocode = _CODE.sub(" ", body)
    ids = Counter(_ID.findall(nocode))
    urls = Counter(u for u in _URL.findall(nocode) if u and u != "#")
    chips = Counter()
    for m in _CHIP.finditer(nocode):
        if _CHIP_CLASS.search(m.group(2)):
            inner = norm_sentence(html.unescape(_TAG.sub("", m.group(3))))
            if 0 < len(inner) <= 60:
                chips[inner] += 1
    heads = Counter()
    for m in _HEADING.finditer(nocode):
        inner = html.unescape(re.sub(r"\s+", " ", _TAG.sub(" ", m.group(2)))).strip()
        if inner:
            heads[norm_sentence(inner)] += 1
    sets.update({"ids": ids, "urls": urls, "chips": chips, "headings": heads})
    return {"bytes": _h(stripped(raw)), "text": _h(text), "words": len(text.split()),
            "sets": {k: dict(sorted(v.items())) for k, v in sets.items()}}


def _load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def _files(pieces, extra):
    out = []
    for p in pieces:
        if p.get("url", "").endswith(".html") and "/" not in p["url"]:
            out.append((p["slug"], p["url"]))
    for slug in extra or []:
        out.append((slug, slug + ".html"))
    return out


def _read(out_dir, url, commit=None):
    """A piece's file: from the tree, or from a commit when the record is
    being rewritten for a tree that has already moved on."""
    if commit:
        import subprocess
        r = subprocess.run(["git", "show", "%s:%s" % (commit, url)], cwd=out_dir, capture_output=True)
        return r.stdout.decode("utf-8", "ignore") if r.returncode == 0 else None
    path = os.path.join(out_dir, url)
    if not os.path.exists(path):
        return None
    return open(path, encoding="utf-8", errors="ignore").read()


def snapshot(out_dir, pieces, extra=None, commit=None):
    snap = {}
    for slug, url in _files(pieces, extra):
        raw = _read(out_dir, url, commit)
        if raw is None:
            continue
        snap[slug] = extract(raw)
        snap[slug]["url"] = url
    return snap


def write_baseline(out_dir, pieces, extra=None, accept=None, commit=None, new=False):
    base = _load(BASE_PATH, {"note": "", "pieces": {}})
    snap = snapshot(out_dir, pieces, extra, commit)
    if accept:
        for slug in accept:
            if slug not in snap:
                raise SystemExit("invariance: no such piece to accept: %s" % slug)
            was = base["pieces"].get(slug) or {}
            base["pieces"][slug] = snap[slug]
            if new or was.get("added"):
                base["pieces"][slug]["added"] = True
    else:
        base["pieces"] = snap
    base["note"] = ("Per piece: the numerals, references, provenance labels, chips, anchor ids, "
                    "URLs, headings and result sentences the piece carried when the record was "
                    "written, plus a byte and a text digest. The build refuses any undeclared "
                    "change to these sets. Renew an entry only with build/invariance.py --accept.")
    json.dump(base, open(BASE_PATH, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False, sort_keys=True)
    open(BASE_PATH, "a", encoding="utf-8").write("\n")
    return snap


def _declared(ledger, slug):
    entry = (ledger.get("pieces") or {}).get(slug) or {}
    lost_text, gained_text = [], []
    for s in entry.get("strikes") or []:
        lost_text.append(s.get("text") or "")
        gained_text.append(s.get("residue") or "")
    for c in entry.get("count_fixes") or []:
        lost_text.append(c.get("from") or "")
        gained_text.append(c.get("to") or "")
    for a in entry.get("additions") or []:
        gained_text.append(a.get("text") or "")
    lost, gained = extract_text_sets(" ".join(lost_text)), extract_text_sets(" ".join(gained_text))
    # a struck sentence may have been respelled by a declared pair before it
    # was struck: its record hash is the old spelling, so both are allowed
    pairs = [(x.get("from") or "", x.get("to") or "") for x in entry.get("spellings") or []]
    for text in lost_text:
        back = text
        for a, b in pairs:
            if a and b:
                back = re.sub(r"\b%s\b" % re.escape(b), a, back)
                back = re.sub(r"\b%s\b" % re.escape(b.capitalize()), a.capitalize(), back)
        if back != text:
            for k, v in extract_text_sets(back)["sentences"].items():
                lost["sentences"][k] = max(lost["sentences"].get(k, 0), v)
    # an addition may also bring a chip, an id or a heading with it
    for cat in ("chips", "ids", "headings"):
        gained[cat] = Counter()
        for a in entry.get("additions") or []:
            for tok in a.get(cat) or []:
                gained[cat][tok] += 1
        lost[cat] = Counter()
    return lost, gained


def _explain(cat, tokens, cur_text):
    """A problem line: which tokens, and for sentences, the sentence itself
    when it can still be found in the current text."""
    shown = []
    for tok, n in list(tokens.items())[:6]:
        if cat == "sentences":
            found = next((s for s in record_sentences(cur_text) if _h(norm_sentence(s)) == tok), None)
            shown.append(("“%s”" % found[:120]) if found else tok)
        else:
            shown.append("%s%s" % (tok, ("×%d" % n) if n > 1 else ""))
    more = len(tokens) - len(shown)
    return ", ".join(shown) + (" and %d more" % more if more > 0 else "")


def check(out_dir, pieces, extra=None):
    """Compare every piece to its record. Returns (problems, summary)."""
    base = _load(BASE_PATH, None)
    if base is None:
        return (["content/invariants.json is missing; write it with build/invariance.py --baseline"],
                {"held": 0, "checked": 0, "declared": 0, "missing": []})
    ledger = _load(LEDGER_PATH, {})
    problems, held, checked, declared, missing = [], 0, 0, 0, []
    for slug, url in _files(pieces, extra):
        path = os.path.join(out_dir, url)
        if not os.path.exists(path):
            continue
        rec = base["pieces"].get(slug)
        if rec is None:
            missing.append(slug)
            problems.append("%s: no invariance record; accept it with build/invariance.py --accept %s"
                            % (url, slug))
            continue
        checked += 1
        raw = open(path, encoding="utf-8", errors="ignore").read()
        now = extract(raw)
        cur_text = readable(raw)
        allowed_lost, allowed_gained = _declared(ledger, slug)
        entry = (ledger.get("pieces") or {}).get(slug) or {}
        if any(entry.get(k) for k in ("strikes", "count_fixes", "additions", "spellings")):
            declared += 1
        ok = True
        pairs = [(x.get("from") or "", x.get("to") or "") for x in entry.get("spellings") or []]
        pairs = [(a, b) for a, b in pairs if a and b]
        for cat in ("numerals", "refs", "labels", "sentences", "ids", "urls", "chips", "headings"):
            was = Counter(rec["sets"].get(cat, {}))
            is_ = Counter(now["sets"].get(cat, {}))
            lost = was - is_
            gained = is_ - was
            if cat in allowed_lost:
                lost = lost - allowed_lost[cat]
                gained = gained - allowed_gained[cat]
            if cat in ("sentences", "headings") and pairs and (lost or gained):
                # a gained sentence that, spelled the old way, is a lost one
                # is the same sentence under a declared pair
                for s in (record_sentences(cur_text) if cat == "sentences" else list(is_.keys())):
                    key = _h(norm_sentence(s)) if cat == "sentences" else s
                    if key not in gained:
                        continue
                    back = s
                    for a, b in pairs:
                        back = re.sub(r"\b%s\b" % re.escape(b), a, back)
                        back = re.sub(r"\b%s\b" % re.escape(b.capitalize()), a.capitalize(), back)
                    old = _h(norm_sentence(back)) if cat == "sentences" else norm_sentence(back)
                    if old in lost:
                        n = min(lost[old], gained[key])
                        lost[old] -= n; gained[key] -= n
                lost = +lost; gained = +gained
            if lost:
                ok = False
                problems.append("%s: %s lost, not declared in the ledger: %s"
                                % (url, cat, _explain(cat, lost, cur_text)))
            if gained:
                ok = False
                problems.append("%s: %s gained, not declared in the ledger: %s"
                                % (url, cat, _explain(cat, gained, cur_text)))
        if ok:
            held += 1
    return problems, {"held": held, "checked": checked, "declared": declared, "missing": missing}


def classes(out_dir, pieces):
    """How each listed piece stands against its record: untouched (bytes the
    same outside the owned blocks), styling (bytes moved, readable text the
    same), copy (readable text moved). Computed from the files, never typed."""
    base = _load(BASE_PATH, {"pieces": {}})
    out = {}
    for slug, url in _files(pieces, None):
        path = os.path.join(out_dir, url)
        rec = base["pieces"].get(slug)
        if rec is None or not os.path.exists(path):
            out[slug] = "new"
            continue
        if rec.get("added"):
            out[slug] = "new"            # accepted into the record by this pass
            continue
        raw = open(path, encoding="utf-8", errors="ignore").read()
        b, t = _h(stripped(raw)), _h(readable(raw))
        out[slug] = "untouched" if b == rec["bytes"] else ("styling" if t == rec["text"] else "copy")
    return out


def _main(argv):
    sys.path.insert(0, os.path.join(ROOT, "build"))
    content = json.load(open(os.path.join(ROOT, "content", "pieces.json"), encoding="utf-8"))
    pieces = content["pieces"]
    metrics = json.load(open(os.path.join(ROOT, "content", "metrics.json"), encoding="utf-8"))
    listed = {p["slug"] for p in pieces}
    extra = sorted(k for k in metrics if k not in listed and os.path.exists(os.path.join(ROOT, k + ".html")))
    if "--baseline" in argv:
        commit = None
        if "--from" in argv:
            commit = argv[argv.index("--from") + 1]
        snap = write_baseline(ROOT, pieces, extra, commit=commit)
        print("invariance: record written for %d pieces (%d listed, %d transcripts)%s"
              % (len(snap), len([s for s in snap if s in listed]), len([s for s in snap if s not in listed]),
                 (" from commit %s" % commit) if commit else ""))
        return 0
    if "--accept" in argv:
        slugs = [a for a in argv[argv.index("--accept") + 1:] if not a.startswith("--")]
        write_baseline(ROOT, pieces, extra, accept=slugs, new="--new" in argv)
        print("invariance: record %s for %s" % ("written" if "--new" in argv else "renewed", ", ".join(slugs)))
        return 0
    if "--classes" in argv:
        c = classes(ROOT, pieces)
        n = Counter(c.values())
        for slug in sorted(c):
            print("%-44s %s" % (slug, c[slug]))
        print(dict(n))
        return 0
    problems, s = check(ROOT, pieces, extra)
    print("invariance: %d of %d pieces hold; %d carry declared strikes or count fixes"
          % (s["held"], s["checked"], s["declared"]))
    for line in problems:
        print("  " + line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
