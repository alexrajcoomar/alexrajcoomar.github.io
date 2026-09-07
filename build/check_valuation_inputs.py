# -*- coding: utf-8 -*-
"""Check a filled content/valuation-inputs.json before anything is computed from it.

The harvest happens outside this repository, in a browser. This is the gate it has
to pass on the way back in: every figure present, every figure carrying the statement,
note, page and accession it was read from, and the internal ties that the filing
itself must satisfy. A null is allowed and is not an error, but it has to be declared
in harvest_log.not_disclosed, so that an absence is a decision on the record rather
than a field somebody forgot.

Run:  python3 build/check_valuation_inputs.py
Exit: 0 when the file is ready for build/valuation.py, 1 otherwise.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "content", "valuation-inputs.json")
META = ("statement", "note", "page", "accession")
# A note number is not required: the harvest brief tells the harvester to leave
# "note" null for a figure read off the face of a statement rather than out of a
# note, so demanding one would fail a correct file. A page is not required either
# when the leaf declares itself as not coming from the filing, which is how the
# share price is recorded. Statement and accession are always required, because
# without them a figure has no provenance at all.
REQUIRED_META = ("statement", "accession")


def _leaf(o):
    return isinstance(o, dict) and "current" in o and "accession" in o


def _walk(o, path=""):
    """Every provenance-bearing figure in the file, with its dotted path."""
    if _leaf(o):
        yield path, o
        return
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, "%s.%s" % (path, k) if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, "%s[%d]" % (path, i))


def main():
    if not os.path.exists(PATH):
        print("no content/valuation-inputs.json"); return 1
    d = json.load(open(PATH, encoding="utf-8"))
    problems, filled, empty = [], 0, []

    if d.get("status") == "template, unfilled":
        print("valuation inputs: still the unfilled template; nothing to check yet.")
        return 1

    declared = set(d.get("harvest_log", {}).get("not_disclosed") or [])

    for path, leaf in _walk(d):
        has = leaf.get("current") is not None
        if has:
            filled += 1
            need = list(REQUIRED_META)
            if str(leaf.get("statement") or "").strip().lower() != "not from the filing":
                need.append("page")
            missing = [m for m in need if not leaf.get(m)]
            if missing:
                problems.append("%s: has a value but no %s" % (path, ", ".join(missing)))
        else:
            empty.append(path)
            if path not in declared and not (leaf.get("comment") or "").strip():
                problems.append("%s: null, and neither declared in harvest_log.not_disclosed "
                                "nor explained in its comment" % path)

    # the issuer and the filing have to identify themselves
    for sec, keys in (("issuer", ("name", "ticker", "fiscal_year_end_date",
                                  "presentation_currency", "statement_units")),
                      ("filing", ("document_type", "filed_date", "sedar_accession"))):
        for k in keys:
            if not (d.get(sec) or {}).get(k):
                problems.append("%s.%s is not recorded" % (sec, k))

    # the rows the harvester repeats
    cats = (d.get("ppe_note") or {}).get("categories") or []
    if not cats or all(c.get("name") in (None, "") for c in cats):
        problems.append("ppe_note.categories: no asset category was recorded")
    for i, c in enumerate(cats):
        if c.get("name") in (None, ""):
            continue
        for k in ("cost_opening", "additions", "cost_closing", "net_book_value_closing"):
            if c.get(k) is None:
                problems.append("ppe_note.categories[%d] (%s): %s missing" % (i, c["name"], k))
        # the note's own roll-forward has to tie
        o, a, dp, t, cl = (c.get("cost_opening"), c.get("additions"), c.get("disposals"),
                           c.get("transfers"), c.get("cost_closing"))
        if None not in (o, a, cl):
            calc = o + a - (dp or 0) + (t or 0)
            if abs(calc - cl) > max(1.0, abs(cl) * 0.005):
                problems.append("ppe_note.categories[%d] (%s): cost does not roll forward, "
                                "%s + %s - %s + %s = %s against a closing balance of %s"
                                % (i, c["name"], o, a, dp or 0, t or 0, calc, cl))

    tr = (d.get("debt_note") or {}).get("tranches") or []
    if not tr or all(t.get("description") in (None, "") for t in tr):
        problems.append("debt_note.tranches: no instrument was recorded")
    for i, t in enumerate(tr):
        if t.get("description") in (None, ""):
            continue
        for k in ("carrying_amount", "maturity_date"):
            if t.get(k) is None:
                problems.append("debt_note.tranches[%d] (%s): %s missing" % (i, t["description"], k))
        if t.get("coupon_rate") is None and t.get("effective_interest_rate") is None:
            problems.append("debt_note.tranches[%d] (%s): neither a coupon nor an effective rate"
                            % (i, t["description"]))

    # the one thing that would quietly corrupt the whole shield
    rou = ((d.get("leases_note") or {}).get("right_of_use_assets_net_book_value") or {}).get("current")
    names = " ".join((c.get("name") or "").lower() for c in cats)
    if "right of use" in names or "right-of-use" in names:
        problems.append("ppe_note.categories names a right of use asset. A leased asset is not "
                        "depreciable capital property to the lessee; move it to leases_note.")
    if rou is None and "leases_note.right_of_use_assets_net_book_value" not in declared:
        problems.append("leases_note.right_of_use_assets_net_book_value is null and not declared; "
                        "under IFRS 16 it has to be recorded so the CCA base can exclude it")

    # A structural fault is worth more attention than a field nobody filled yet,
    # so the two are reported apart and the undeclared nulls are summarised rather
    # than listed one by one. Forty lines of the same sentence hides the one line
    # that matters.
    undeclared = [p for p in problems if p.endswith("nor explained in its comment")]
    structural = [p for p in problems if p not in undeclared]

    print("valuation inputs: %d figures filled, %d left null (%d declared as not disclosed)"
          % (filled, len(empty), len(declared)))
    if structural:
        print("%d structural problem(s):" % len(structural))
        for p in structural:
            print("  " + p)
    if undeclared:
        print("%d field(s) null without a declaration or a comment:" % len(undeclared))
        for p in undeclared[:8]:
            print("  " + p.split(":")[0])
        if len(undeclared) > 8:
            print("  and %d more" % (len(undeclared) - 8))
    if problems:
        return 1
    print("ready for build/valuation.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
