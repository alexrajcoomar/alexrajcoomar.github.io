# Harvest brief: Dollarama annual financial statements into `valuation-inputs.json`

You are the harvester in a three step pipeline. Another agent wrote the template you are
filling. A third will compute a discounted cash flow and a capital cost allowance tax shield
from it and publish the result. **Your only job is to transcribe figures from a primary source
and record where each one came from.** You are not valuing anything and you are not deciding
anything.

The single rule that matters: **if you cannot find a figure in the filing, leave it `null` and
say so.** Never estimate, never carry a number over from a summary site, never use a figure from
the MD&A where the template asks for the statements. A null is a correct answer. A guess is the
one outcome that ruins the piece downstream, because the receiving repository refuses to publish
a number it cannot trace.

---

## 1. Target

**Dollarama Inc.**, TSX: **DOL**. Its most recent **audited annual consolidated financial
statements**.

Take the fiscal year from the filing itself and record it. Dollarama reports on a 52 or 53 week
retail year that does not end on 31 December, so **do not assume the year end date or the week
count**. Read both off the statements and put them in `issuer.fiscal_year_end_date` and
`issuer.weeks_in_fiscal_year`.

If the most recent annual statements are not available, take the prior year and record which
year you took. Do not mix years.

### Why this issuer, so you can sanity check the choice

Dollarama is a single format retailer whose operations and assets are overwhelmingly Canadian,
which matters because capital cost allowance is a Canadian tax concept. Alimentation Couche-Tard
was rejected for exactly that reason: most of its asset base sits outside Canada, so a CCA shield
computed on consolidated property would be a category error rather than a modelling
simplification. Canadian Tire was rejected because its consolidated statements combine a retailer,
a bank and a REIT, so neither the free cash flow nor the capital structure is clean.

If, when you open the filing, Dollarama turns out to have a large non-Canadian asset base you did
not expect, **stop and report that** rather than harvesting anyway.

---

## 2. Where to go

Try these in order and record which one you used in `filing.sedar_document_url`.

1. **SEDAR+**, `https://www.sedarplus.ca`. Search the issuer name, open the company profile, filter
   the document type to annual financial statements, and take the most recent. Record the
   accession or document number SEDAR+ shows.
2. **The investor relations site**, if SEDAR+ is slow or the search is awkward. Look for
   Investors, then Financial Reports or Annual Reports. The audited statements are usually inside
   the annual report PDF or offered as a separate document.

**Prefer the standalone audited consolidated financial statements PDF.** If only a combined
annual report is available, that is fine, but note it in `filing.document_type` and take page
numbers from that PDF.

If SEDAR+ has no accession number visible, put the document URL in `filing.sedar_accession` and
explain in `filing.comment`. Do not invent an accession format.

---

## 3. How to record every figure

The template repeats one shape for every figure:

```json
{
  "current": null,
  "prior": null,
  "unit": "CAD thousands",
  "statement": null,
  "note": null,
  "page": null,
  "accession": null,
  "comment": ""
}
```

- **`current`** is the fiscal year you are harvesting. **`prior`** is the comparative column
  printed beside it. Every Canadian annual statement shows both. Fill both.
- **Enter numbers as they are printed, without changing the scale.** If the statements are in
  thousands, enter thousands and leave `"unit": "CAD thousands"`. If they are in millions, enter
  millions and change the unit to `"CAD millions"`. **Do not convert.** Getting this wrong by a
  factor of a thousand is the most common and most damaging error in this kind of transcription.
- **A figure in brackets is negative.** Enter it as a negative number.
- **`statement`** is the name of the statement or note as printed, for example
  `"Consolidated Statements of Financial Position"`.
- **`note`** is the note number as printed, for example `"12"`. Leave `null` for figures taken
  from the face of a statement rather than a note.
- **`page`** is the **PDF page number** you were on, not the printed page number, because the
  next agent will reopen the same PDF. If they differ, put the printed one in `comment`.
- **`accession`** is the same value in every leaf. Fill it once and copy it.

Set `"status": "harvested"` at the top of the file when you are done, and complete `harvest_log`.

---

## 4. What to open, section by section

Work in this order. It follows the order of a set of financial statements, so you will mostly be
moving forward through the PDF.

### 4.1 `issuer` and `filing`
From the cover page and the first page of the statements. Currency and units are almost always
stated in a line under the statement heading, such as "in thousands of Canadian dollars". The
auditor's name is on the independent auditor's report.

### 4.2 `balance_sheet`
**Consolidated Statements of Financial Position.** Take the face of the statement.

Watch the split between borrowings and leases. Under IFRS 16 the balance sheet shows **lease
liabilities** separately from **long term debt**. They are different things for this valuation:
put lease liabilities in the lease fields and borrowings in the debt fields. If the statement
combines them, record what it shows and explain in `comment`.

`bank_indebtedness` may not exist. If there is no such line, leave it `null` and add it to
`harvest_log.not_disclosed`.

### 4.3 `income_statement`
**Consolidated Statements of Net Earnings** or Statements of Income. Take the face.

`depreciation_and_amortisation_book` may not appear on the face; it is often in the cash flow
statement or a note. Record wherever you found it. This figure is collected deliberately so the
piece can contrast book depreciation against capital cost allowance, so it matters that it is the
book charge and nothing else.

### 4.4 `tax_note`
**The income taxes note.** Find the **rate reconciliation**, the table that starts from a
statutory rate and reconciles to the effective rate.

- `statutory_rate_combined` is the combined federal and provincial rate the reconciliation starts
  from. Enter it as a percentage, so 26.5 not 0.265.
- If the note gives only the combined rate and not the federal and provincial split, leave the
  two component fields `null` and declare them. Do not split it yourself.
- `deferred_tax_liability_ppe` is the deferred tax balance attributable to property, plant and
  equipment, from the table of temporary differences. If the note does not break it out that far,
  leave it `null` and declare it.

### 4.5 `cash_flow`
**Consolidated Statements of Cash Flows.**

`additions_to_property_plant_and_equipment` is in investing activities and is the capital
expenditure figure. `payments_of_lease_liabilities_principal` is in financing activities under
IFRS 16.

### 4.6 `ppe_note` (the most important section)
**The property, plant and equipment note.** It contains a roll-forward table: opening cost,
additions, disposals, transfers, closing cost, then the same for accumulated depreciation, then
net book value.

- **One entry in `categories` per column the note shows**, for example land, buildings, leasehold
  improvements, store and warehouse equipment, computer equipment, vehicles. **Copy each category
  name verbatim.** Do not merge, rename or tidy them; the whole point of the exercise downstream
  is mapping these categories to capital cost allowance classes.
- Fill the roll-forward numbers for each category. The next agent's validator checks that
  `cost_opening + additions - disposals + transfers` equals `cost_closing` for every row, so if
  your figures do not tie, you have mis-read a column. Recheck before submitting.
- **Right of use assets do not belong here.** Under IFRS 16 a leased asset appears as a right of
  use asset, and to the lessee it is not depreciable capital property under the Income Tax Act, so
  it must be excluded from the CCA base. If the note has a right of use column, **do not put it in
  `categories`**. Put its net book value in `leases_note.right_of_use_assets_net_book_value`. The
  validator rejects a right of use asset found in `categories`.
- If the note discloses construction in progress or assets under development, record whether it is
  included in the totals in `construction_in_progress_included`.

### 4.7 `debt_note`
**The long term debt or borrowings note.**

- **One entry in `tranches` per instrument.** For each: the description as printed, the face
  principal, the carrying amount, the coupon rate, the effective interest rate, the issue and
  maturity dates, the currency, whether it is secured, and whether it is fixed or floating.
- The effective rate is the one that matters downstream, so look for it. Canadian issuers usually
  disclose it in the same table or the sentence beneath. If only a coupon is given, record the
  coupon and leave the effective rate `null`.
- Record the credit facility separately: its limit, the amount drawn at year end, its rate basis
  and its maturity.
- If the note discloses the **fair value of debt**, record it in `fair_value_of_debt_disclosed`.
  It is often in the financial instruments note instead.

### 4.8 `leases_note`
**The leases note.** Right of use asset net book value and the total lease liability. This
section exists so the CCA base can exclude leased assets, so do not skip it.

### 4.9 `share_capital`
**The share capital note and the earnings per share note.**

- Shares outstanding at period end from the share capital note.
- Weighted average basic and diluted from the earnings per share note.
- **`share_price_at_fiscal_year_end` is not in the filing.** Get the closing price on the last
  trading day of the fiscal year from a market source, put the source name and the date in
  `share_price_source`, and set `statement` to `"not from the filing"`. Be explicit about this;
  it is the one figure in the file with a different provenance.

### 4.10 `cca_mapping`
**Leave this entirely alone.** It is the next agent's judgment, not a filing figure.

---

## 5. Before you hand it back

Fill `harvest_log`:

- `harvested_by`, `harvested_on`, `tool`.
- `fields_filled` and `fields_left_null` as counts.
- `not_disclosed`: the dotted path of every field you left `null` because the filing did not
  disclose it, for example `"tax_note.deferred_tax_liability_ppe"`. **Every null needs either an
  entry here or a comment explaining it**, or the validator fails the file.
- `discrepancies`: anything that did not tie, anything ambiguous, anything you had to judge. This
  is the most valuable field in the file. If a total did not add up, say so here rather than
  quietly adjusting a number.

Then check three things yourself:

1. **Scale.** Does revenue look like the right order of magnitude for the units you declared?
2. **Ties.** Does every PP&E cost row roll forward? Does the balance sheet balance?
3. **Years.** Is `current` really the year in `issuer.fiscal_year_label`, and `prior` the
   comparative, and not the other way round?

Return the completed JSON file. Do not reformat the structure, do not remove fields you did not
fill, and do not add fields. The receiving repository validates the shape.
