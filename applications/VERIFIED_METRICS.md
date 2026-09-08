# Verified repository metrics, 7 September 2026

Every figure below was read out of this repository at commit `8683a21`, not from
memory and not from the previous resume. Anything a resume states must come from
this file. The right-hand column names the file that holds the number, so a
recruiter who asks can be shown where it lives.

## Corpus

| Claim | Value | Source of truth |
|---|---|---|
| Published pieces | 67 | `content/pieces.json`, list length |
| Independent research | 25 | `content/pieces.json`, `surface == "independent"` |
| Coursework pieces | 35 | `content/pieces.json`, `surface == "course"` |
| Personal pieces | 7 | `content/pieces.json`, `surface == "personal"` |
| Words | 492,485 | `content/metrics.json`, summed |
| Figures | 188 | `content/metrics.json`, summed |
| Tables | 799 | `content/metrics.json`, summed |
| Interactive tools | 7 | `content/pieces.json`, `k == "Tool"` |
| Pieces carrying an interactive demo | 20 | `content/pieces.json`, `demo` non-empty |
| Featured pieces | 7 | `content/pieces.json`, `featured == true` |
| Python written | 14,719 lines | `build/*.py` and `mscore.py`, standard library only |
| JavaScript written | 5,222 lines | `build/*.js`, `site.js`, `atlas.js`, `long.js`, `sw.js` |

The previous resume (W27_5_2.pdf) states 61 pieces, 23 independent and 181
figures. All three are stale. The corpus has grown by six pieces since.

## Flagged in Hindsight (Beneish M-Score)

| Claim | Value | Source of truth |
|---|---|---|
| Piece length | 5,008 words, 4 figures, 6 tables | `content/metrics.json` |
| Cases examined | 5 | Sino-Forest, Nortel, Poseidon Concepts, Livent, Philip Services |
| Computable test years | 3 | `mscore-results.csv` |
| Test years flagging at the -1.78 cut-off | 0 | `mscore-results.csv` |
| Test years flagging at the -2.22 cut-off | 1 (Sino-Forest FY2010) | `mscore-results.csv` |
| Cases not computable | 2 (Livent FY1997, Philip Services FY1996), inputs not retrievable | `mscore-results.csv` |
| Cases where the model does not apply | 1 (Poseidon, interim receivables diagnostic instead) | `mscore.py` |
| Reproducible from a clean checkout | Yes, `python3 mscore.py` reprints every score | verified this session |

Computed scores, reproduced this session: Sino-Forest FY2010 -1.9293,
Sino-Forest FY2009 -2.7374, Nortel FY2002 -3.8062.

Do not write "no year flagged". One year flags at the permissive cut-off. The
defensible sentence is "none of the three computable test years crossed the
standard -1.78 cut-off".

## IFRS 15 Judgment Trainer

| Claim | Value | Source of truth |
|---|---|---|
| Scenarios | 62 | embedded item bank, `meta.item_count` |
| Determinate items (scored) | 29 | `meta.type_split` |
| Judgment items (reasoning scored, not the answer) | 33 | `meta.type_split` |
| Distinct sources registered | 20 | item bank `sources` |
| Items citing CPA Canada Handbook Part I | 62 of 62 | source S20 appears on every item |
| Governing text | IFRS 15, Part I of the CPA Canada Handbook, 2026 Edition, in effect 1 January 2026 | source S20 |
| Where it was read | Knotia, University of Waterloo library proxy | source S20 |
| Verification date | 21 August 2026 | `meta.verified_against_handbook` |
| Coverage | Full standard, Appendices A to C, all 65 illustrative examples | `meta.verified_against_handbook` |
| Judgment areas drilled | 9 | item bank, `judgment_point` |
| Five steps plus adjacent categories | 5 + 2 (contract costs, presentation and disclosure) | item bank, `step` |

The bank was drafted from AASB 15, NZ IFRS 15 and the IFRS Foundation
illustrative examples, then verified paragraph by paragraph against the CPA
Canada Handbook. The Handbook is the governing citation, and the resume may say
so. The build history is recorded on the page rather than hidden.

## The tax base nobody discloses (Dollarama, CCA valuation)

| Claim | Value | Source of truth |
|---|---|---|
| Piece length | 5,632 words, 4 figures, 4 tables | `content/metrics.json` |
| Issuer and year | Dollarama, fiscal year ended 1 February 2026 | `content/valuation-output.json` |
| CCA classes modelled | 7 | `valuation-output.json`, `classes` |
| Reconstructed opening UCC | $558.4M | `opening_ucc_total` = 558,395 (thousands) |
| Depreciable net book value | $951.1M | `depreciable_net_book_value` = 951,107 |
| WACC | 5.56% | `cost_of_capital.wacc` = 5.5568 |
| Cost of equity | 5.73% | `cost_of_equity` = 5.726 |
| Cost of debt | 3.17% | `cost_of_debt` = 3.1698 |
| Statutory tax rate | 26.5% | `tax_rate` |
| Expansion anchor, value per share | $187.16 | `anchors[0].value_per_share` |
| Maintenance anchor, value per share | $125.14 | `anchors[1].value_per_share` |
| Market share price used | $183.50 | `cost_of_capital.share_price` |
| PV of the CCA shield | $229.8M (expansion) / $228.4M (maintenance) | `present_value_of_cca_shield` |
| PV of a book depreciation proxy shield | $138.6M / $138.3M | `present_value_of_book_shield` |
| Statutory over book, per share | $1.78 (expansion) to $2.27 (maintenance) | `cca_versus_book_per_share` |
| Terminal share of enterprise value | 89.6% / 84.7% | `terminal_share_of_enterprise_value` |
| Out-of-sample validation | Reconstructed base run over a year it was not fitted to, reproducing the issuer's disclosed current tax expense | `validation` |
| Statutory authority | Income Tax Regulations, C.R.C. c. 945, read 6 September 2026 | `law_source` |

## Pet Valu Strategic Growth Case: NOT a repository artefact

Searched the whole tree. "Pet Valu" appears in exactly two files, `content/resume.json`
and the `resume.html` the build writes from it. There is no model, no script, no
data file and no published piece. It is a 2025 four-person case competition,
declared on the resume like any other line of employment history, and nothing on
the site computes or verifies it.

Consequence for the cover letter: variant C must not say the Pet Valu model is on
the site or that a reader can check it. The auditable claim belongs to the
Dollarama valuation, which is published and recomputed on every build. Pet Valu
stays on the resume as a competition result and is described as one.

## Claims on the current PDF that no longer hold

1. "61 pieces (23 independent) ... 181 figures". Now 67, 25 and 188.
2. "Excel (advanced)", "IFRS and ASPE (introductory)". Self-ratings, and the site
   states as a design rule that it carries no levels and no self-ratings.
   Corrected: the first is now "Excel", the second "IFRS as adopted in Canada
   (Part I) and ASPE (Part II)", which is a designation rather than a level.
3. "Tableau". Not evidenced in this repository, which is the only thing this
   file can check. Alex supplied the grounding it was missing: Introduction to
   Performance Analytics is the School of Accounting and Finance's data
   visualisation course and is taught in Tableau, and the UW CISA competition
   dashboard was built in it. Tableau stays, and both resumes and the site now
   name where it came from rather than asserting it bare. Recorded here because
   the evidence is a transcript and a competition, not a file in this tree, and
   a reader of this file should know which kind of evidence they are getting.
4. "R". Evidenced by the CISA competition line, not by anything published here.
   Kept, attached to that line.
