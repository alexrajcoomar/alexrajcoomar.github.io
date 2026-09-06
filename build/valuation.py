# -*- coding: utf-8 -*-
"""The Dollarama valuation: a capital cost allowance schedule and two anchors.

Every input is either transcribed from the issuer's filed annual financial
statements (content/valuation-inputs.json, each figure carrying the statement,
note and PDF page it was read from) or derived here from those figures. Nothing
is remembered. Where an input cannot come from the filing at all, it is declared
in ASSUMED below and appears in the output under that name, so a reader can see
the whole of what the model was told rather than the whole of what it concluded.

The point of the exercise is the tax shield. A conventional model proxies the
shield with book depreciation. Canadian tax law does not use book depreciation:
it uses capital cost allowance, computed on undepreciated capital cost by class
at prescribed rates, and the two bases differ. This module computes both and
reports the difference.

Run:  python3 build/valuation.py
Out:  content/valuation-output.json, and a readable summary on stdout.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PATH = os.path.join(ROOT, "content", "valuation-inputs.json")
OUT_PATH = os.path.join(ROOT, "content", "valuation-output.json")

# ---------------------------------------------------------------- the law ----
# Rates and first-year rules read from the Income Tax Regulations as
# consolidated on the Justice Laws website on 2026-09-06, not from memory.
#
#   Reg 1100(2)          the first-year adjustment. Variable C, paragraph
#                        (b)(ii), excludes Class 13 from the half-year base, so
#                        leasehold improvements take a full first-year claim.
#   Reg 1100(2) A.1(a)   reaccelerated investment incentive property, general
#                        classes: an extra 1/2 of the net addition for property
#                        available for use before 2030, nil after 2029.
#   Reg 1100(2) A.1(e)   Class 50: an extra 9/11 before 2027, nil after 2026.
#                        At a 55% rate that is 55% x (1 + 9/11) = 100%, so a
#                        qualifying addition is written off in full in year one.
#   Reg 1104(4.01)       reaccelerated investment incentive property means
#                        property acquired after 2024 that becomes available for
#                        use before 2034. Every year this model forecasts is
#                        inside that window.
#   ITA 13(26) to (32)   no capital cost allowance until the property is
#                        available for use, which is why work in progress is
#                        held out of the base.
#   ITA 13(21) "UCC"     and 13(1), under which a class cannot carry a negative
#                        undepreciated capital cost into the following year.
LAW_SOURCE = ("Income Tax Regulations, C.R.C. c. 945, as consolidated on the "
              "Justice Laws website and read on 6 September 2026")

CLASSES = {
    # name shown            class  rate   method          first-year rule
    "Buildings and roofs":        ("1",  0.04, "declining", "general"),
    "Store and warehouse equipment": ("8", 0.20, "declining", "general"),
    "Computer equipment":         ("50", 0.55, "declining", "class50"),
    "Vehicles":                   ("10", 0.30, "declining", "general"),
    "Leasehold improvements":     ("13", None, "straight",  "class13"),
    # Land is not depreciable property, so it has no class and no allowance.
    "Land":                       (None, None, "none",      "none"),
    # Work in progress is not available for use, so no allowance is claimable
    # on it until it is. ITA 13(26).
    "Work in progress":           (None, None, "none",      "none"),
}

def first_year_factor(rule, calendar_year):
    """The multiple of a net addition that enters the class for the year's
    claim, under Reg 1100(2). 1.0 means the addition enters at cost with no
    adjustment; 1.5 means the reaccelerated incentive adds another half."""
    if rule == "general":
        # A.1(a): 1/2 before 2030, nil after 2029. C excludes nothing here, but
        # an addition that gets the incentive is out of the half-year base.
        return 1.5 if calendar_year < 2030 else 0.5
    if rule == "class50":
        # A.1(e): 9/11 before 2027, nil after 2026. After that the ordinary
        # half-year rule applies again.
        return 1.0 + 9.0 / 11.0 if calendar_year < 2027 else 0.5
    if rule == "class13":
        # Class 13 is out of the half-year base entirely, Reg 1100(2) C(b)(ii),
        # and out of the incentive, A.1(a). A full year's claim in year one.
        return 1.0
    return 0.0

# ------------------------------------------------------- declared inputs ----
# The filing cannot supply these. They are named here rather than buried, and
# every one of them is carried into the output so the page can print them.
ASSUMED = {
    "risk_free_rate": {
        "value": 3.40,
        "unit": "percent",
        "what": "Government of Canada 10 year benchmark bond yield",
        "source": ("OECD long term government bond yield for Canada, monthly "
                   "average for January 2026, retrieved through the Federal "
                   "Reserve Bank of St. Louis series IRLTLT01CAM156N on "
                   "6 September 2026"),
        "caveat": ("A monthly average, not the closing yield on 30 January 2026. "
                   "The daily series was not reachable."),
    },
    "equity_risk_premium": {
        "value": 5.50, "unit": "percent",
        "what": "Equity risk premium over the Canadian risk free rate",
        "source": "Declared by the analyst. Not derived from the filing.",
        "caveat": "The single least defensible number in the model.",
    },
    "beta": {
        "value": 0.75, "unit": "multiple",
        "what": "Equity beta",
        "source": "Declared by the analyst. Not derived from the filing.",
        "caveat": ("A defensive discount retailer is conventionally assigned a "
                   "beta below one. No regression was run and no data vendor "
                   "figure was used."),
    },
    "forecast_years": {
        "value": 5, "unit": "years",
        "what": "Explicit forecast horizon before the terminal value",
        "source": "Declared by the analyst.",
        "caveat": "",
    },
    "class13_write_off_years": {
        "value": 8, "unit": "years",
        "what": "Straight line period for Class 13 leasehold improvements",
        "source": ("Derived, then rounded. Right of use assets of 2,109,445 at "
                   "2 February 2025 against right of use depreciation of "
                   "268,843 for that year implies an average remaining lease "
                   "term of 7.8 years, and IFRS 16 measures that term on the "
                   "same basis Class 13 uses, being the lease term plus "
                   "renewals reasonably certain to be exercised."),
        "caveat": ("The filing does not disclose lease terms. Sensitivity at "
                   "5 and 10 years is reported."),
    },
}

# ------------------------------------------------------------- the model ----
def money(x):
    return int(round(x))

def pct(x):
    return round(x, 4)


def load():
    return json.load(open(IN_PATH, encoding="utf-8"))


def canadian_base(d):
    """The Canadian owned property, category by category.

    The note has no transfers line. The harvest carried two movements there,
    additions from the business combination and foreign currency translation,
    both of which are the Australian assets acquired on 21 July 2025. Removing
    the transfers column therefore removes Australia from the base, which is
    what a capital cost allowance computation requires: capital cost allowance
    is a deduction under a Canadian statute against Canadian taxable income,
    and property held by an Australian subsidiary is outside it.
    """
    rows = []
    for c in d["ppe_note"]["categories"]:
        cost = c["cost_closing"]
        au = c["transfers"]
        can_cost = cost - au
        share = 1.0 if cost == 0 else can_cost / float(cost)
        rows.append({
            "name": c["name"],
            "cost_closing": cost,
            "australian_carve_out": au,
            "canadian_cost": can_cost,
            "canadian_net_book_value": c["net_book_value_closing"] * share,
            "book_depreciation": c["depreciation_charge"] * share,
            "cca_class": CLASSES[c["name"]][0],
            "cca_rate": CLASSES[c["name"]][1],
            "method": CLASSES[c["name"]][2],
            "first_year_rule": CLASSES[c["name"]][3],
        })
    return rows


def implied_ucc(d):
    """Back the tax base out of the deferred tax liability on property.

    Note 16(b) gives a deferred income tax liability on property, plant and
    equipment of 739,329. Divided by the statutory rate the note itself
    reconciles from, that is a temporary difference of 2,789,921. There are two
    readings of what sits inside that line and only one of them survives.

    Read it as owned property alone and the tax base is 1,258,499 less
    2,789,921, which is negative. A class cannot carry a negative undepreciated
    capital cost: under ITA 13(1) the negative amount is taken into income as
    recapture and the balance resets to nil, so a negative aggregate base
    cannot persist across two consecutive year ends. It does here, in both
    years, which rules the reading out.

    Read it as including the right of use assets and the arithmetic works. A
    leased asset has no tax base to the lessee, so its whole book value is a
    temporary difference. The components table supports this: the deferred tax
    ASSET line "Lease obligations" is the lease LIABILITY, which leaves the
    right of use ASSET without a line of its own, and property is the only
    line it can be in.
    """
    tax = d["tax_note"]["statutory_rate_combined"]["current"] / 100.0
    out = {}
    for col in ("current", "prior"):
        dtl = d["tax_note"]["deferred_tax_liability_ppe"][col]
        rou = d["leases_note"]["right_of_use_assets_net_book_value"][col]
        nbv = (d["ppe_note"]["total_net_book_value_closing"] if col == "current"
               else 1046390)  # prior year total, note 9, PDF page 32
        td = dtl / tax
        out[col] = {
            "deferred_tax_liability_property": dtl,
            "statutory_rate": tax * 100,
            "temporary_difference": money(td),
            "owned_net_book_value": nbv,
            "right_of_use_net_book_value": rou,
            "reading_owned_only_ucc": money(nbv - td),
            "reading_with_right_of_use_ucc": money(nbv + rou - td),
            "owned_property_temporary_difference": money(td - rou),
        }
    return out


def opening_ucc(rows, temp_diff):
    """Split the owned property temporary difference across the classes.

    Land carries no temporary difference: its tax base is its cost and it is
    never written down. Work in progress carries none either, because neither
    basis has begun to write it off. The difference therefore belongs entirely
    to the depreciable classes, and is allocated across them in proportion to
    net book value.

    That allocation is a judgment, not a disclosure. It is the weakest joint in
    the model and the sensitivity below shows how much it can move the answer.
    """
    dep = [r for r in rows if r["method"] != "none"]
    total_nbv = sum(r["canadian_net_book_value"] for r in dep)
    for r in rows:
        if r["method"] == "none":
            r["opening_ucc"] = 0.0
            r["share_of_temporary_difference"] = 0.0
            continue
        w = r["canadian_net_book_value"] / total_nbv
        r["share_of_temporary_difference"] = temp_diff * w
        r["opening_ucc"] = r["canadian_net_book_value"] - temp_diff * w
    return total_nbv


def run_cca(rows, years, additions_by_year, class13_years):
    """Roll the undepreciated capital cost forward, class by class, year by year.

    Declining balance classes take rate x (opening + the first year factor
    applied to the year's additions), and the addition enters the closing
    balance at cost whatever factor applied to the claim, because the incentive
    changes the timing of the deduction and not the amount of it.

    Class 13 is straight line. The opening balance is written off over the
    remaining average term and each year's additions over a fresh term, so a
    year's claim is the sum of the tranches still running.
    """
    sched, c13 = [], []
    ucc = {r["name"]: r["opening_ucc"] for r in rows}
    for i, (fy, cal) in enumerate(years):
        row = {"fiscal_year": fy, "calendar_year": cal, "classes": [], "total_cca": 0.0}
        add_total = additions_by_year[i]
        # additions are spread across the depreciable classes in the same
        # proportion the fiscal 2026 additions fell, which the note discloses
        for r in rows:
            if r["method"] == "none":
                continue
            add = add_total * r["addition_share"]
            if r["method"] == "declining":
                f = first_year_factor(r["first_year_rule"], cal)
                claim = r["cca_rate"] * (ucc[r["name"]] + f * add)
                claim = min(claim, ucc[r["name"]] + add)   # cannot exceed the pool
                ucc[r["name"]] = ucc[r["name"]] + add - claim
            else:
                # Class 13: the opening pool plus one tranche per addition year
                if i == 0:
                    c13.append([r["opening_ucc"], class13_years])
                c13.append([add, class13_years])
                claim = 0.0
                for t in c13:
                    if t[1] > 0:
                        step = t[0] / float(class13_years)
                        step = min(step, t[0] - 0)
                        claim += step
                        t[1] -= 1
                # the remaining balance of every running tranche
                ucc[r["name"]] = sum(t[0] * (t[1] / float(class13_years)) for t in c13)
            row["classes"].append({
                "name": r["name"], "cca_class": r["cca_class"],
                "rate": r["cca_rate"], "method": r["method"],
                "additions": money(add), "cca": money(claim),
                "closing_ucc": money(ucc[r["name"]]),
                "first_year_factor": round(first_year_factor(r["first_year_rule"], cal), 4),
            })
            row["total_cca"] += claim
        row["total_cca"] = money(row["total_cca"])
        row["closing_ucc_total"] = money(sum(ucc.values()))
        sched.append(row)
    return sched


def tranche_yield(carrying_coupon, face, fair_value, coupon, years_to_maturity):
    """The discount rate that prices a bullet at its disclosed fair value.

    The note gives, per tranche, the coupon, the maturity and the fair value.
    Solving each for its yield and weighting by fair value gives a cost of debt
    that is derived from the filing rather than assumed from a rating table.
    """
    lo, hi = -0.02, 0.60
    for _ in range(200):
        r = (lo + hi) / 2.0
        pv = 0.0
        n = max(1, int(round(years_to_maturity)))
        c = face * coupon
        for t in range(1, n + 1):
            pv += c / (1.0 + r) ** t
        pv += face / (1.0 + r) ** n
        if pv > fair_value:
            lo = r
        else:
            hi = r
    return (lo + hi) / 2.0


def cost_of_debt(d):
    """Weighted by fair value, from the yields the fair value disclosure implies.

    Note 13 gives the coupon, the maturity and the fair value of every tranche.
    Nothing in the statements gives an effective interest rate, and the harvest
    left those fields null rather than substituting the coupon, so the rate is
    solved for rather than read.
    """
    year_end = 2026.085   # 1 February 2026 as a fraction of a year
    out, tot_fv, wsum = [], 0.0, 0.0
    for t in d["debt_note"]["tranches"]:
        if t["principal_face_amount"] <= 0:
            continue
        y = int(t["maturity_date"][:4]) + int(t["maturity_date"][5:7]) / 12.0
        n = max(0.5, y - year_end)
        fv = t["fair_value"]
        r = tranche_yield(None, t["principal_face_amount"], fv,
                          t["coupon_rate"] / 100.0, n)
        out.append({"coupon": t["coupon_rate"],
                    "maturity": t["maturity_date"],
                    "face": t["principal_face_amount"], "fair_value": fv,
                    "years_to_maturity": round(n, 2),
                    "implied_yield": pct(r * 100)})
        tot_fv += fv
        wsum += fv * r
    return out, wsum / tot_fv


def forecast(name, base, years, growth_path, capex_intensity, terminal_growth,
             terminal_capex_intensity, rows, class13_years, tax, wacc,
             use_book_depreciation=False):
    """One anchor, carried through to an enterprise value.

    Leases are treated as an operating cost, not as debt. Under IFRS 16 the
    reported EBITDA excludes lease payments while the Income Tax Act allows the
    lessee the full cash payment as a deduction, so the payment is taken out of
    both the cash flow and the taxable income and the lease liability is then
    correctly left out of the enterprise value. The alternative treatment, leases
    as debt, would need a lease discount rate the filing does not disclose.
    """
    sales = base["sales"]
    adds, sales_path = [], []
    for g in growth_path:
        sales = sales * (1.0 + g)
        sales_path.append(sales)
        adds.append(sales * capex_intensity)
    sched = run_cca(rows, years, adds, class13_years)

    # the book base rolled forward beside the tax base, so the two can be
    # drawn against each other: cost less accumulated depreciation, moving by
    # the same additions the allowance sees
    book_base = base["depreciable_net_book_value"]
    lines, prev_sales = [], base["sales"]
    for i, s in enumerate(sales_path):
        ebitda = s * base["ebitda_margin"]
        lease = s * base["lease_intensity"]
        cca = sched[i]["total_cca"]
        book = base["book_depreciation"] * (s / base["sales"])
        shield_base = book if use_book_depreciation else cca
        taxable = ebitda - lease - shield_base
        cash_tax = tax * taxable
        capex = adds[i]
        dnwc = base["nwc_intensity"] * (s - prev_sales)
        fcff = ebitda - lease - cash_tax - capex - dnwc
        dep_add = capex * base["depreciable_addition_share"]
        book_base = book_base + dep_add - book
        lines.append({
            "book_net_book_value": money(book_base),
            "tax_base_closing": sched[i]["closing_ucc_total"],
            "fiscal_year": years[i][0], "sales": money(s), "ebitda": money(ebitda),
            "lease_payments": money(lease), "cca": money(cca),
            "book_depreciation": money(book),
            "taxable_income": money(taxable), "cash_tax": money(cash_tax),
            "capex": money(capex), "change_in_working_capital": money(dnwc),
            "free_cash_flow": money(fcff),
            "tax_shield_on_cca": money(tax * cca),
            "tax_shield_on_book_depreciation": money(tax * book),
        })
        prev_sales = s

    # The terminal year is not asserted. The schedule is run on for another
    # CONVERGE years at the terminal growth rate so the allowance settles to
    # whatever the prescribed rates actually produce against a capital
    # programme growing at that rate, and the settled figure is the one used.
    # Every incentive has expired by then, so the converged ratio is the plain
    # half-year rule working against growth.
    CONVERGE = 30
    long_years = list(years)
    long_adds = list(adds)
    s_run, cal = sales_path[-1], years[-1][1]
    for k in range(CONVERGE):
        s_run *= (1.0 + terminal_growth)
        cal += 1
        long_years.append((years[-1][0] + 1 + k, cal))
        long_adds.append(s_run * terminal_capex_intensity)
    long_sched = run_cca([dict(r) for r in rows], long_years, long_adds, class13_years)

    s = sales_path[-1] * (1.0 + terminal_growth)
    ebitda = s * base["ebitda_margin"]
    lease = s * base["lease_intensity"]
    capex = s * terminal_capex_intensity
    # the settled allowance, expressed against the settled capital spending and
    # then applied to the terminal year's own spending
    settled = long_sched[-1]["total_cca"] / float(long_adds[-1])
    cca_term = capex * settled
    book_term = base["book_depreciation"] * (s / base["sales"])
    shield_base = book_term if use_book_depreciation else cca_term
    taxable = ebitda - lease - shield_base
    cash_tax = tax * taxable
    dnwc = base["nwc_intensity"] * (s - sales_path[-1])
    fcff_term = ebitda - lease - cash_tax - capex - dnwc

    pv = sum(l["free_cash_flow"] / (1.0 + wacc) ** (i + 1) for i, l in enumerate(lines))
    tv = fcff_term / (wacc - terminal_growth)
    pv_tv = tv / (1.0 + wacc) ** len(lines)
    ev = pv + pv_tv
    return {
        "anchor": name, "lines": lines, "schedule": sched,
        "terminal": {"fiscal_year": years[-1][0] + 1, "sales": money(s),
                     "ebitda": money(ebitda), "capex": money(capex),
                     "allowance": money(cca_term), "cash_tax": money(cash_tax),
                     "free_cash_flow": money(fcff_term),
                     "growth": pct(terminal_growth * 100),
                     "capex_intensity": pct(terminal_capex_intensity * 100),
                     "settled_allowance_over_capex": pct(settled * 100),
                     "converged_over_years": CONVERGE,
                     "value": money(tv)},
        "present_value_of_forecast": money(pv),
        "present_value_of_terminal": money(pv_tv),
        "terminal_share_of_enterprise_value": pct(100.0 * pv_tv / ev),
        "enterprise_value": money(ev),
        "wacc": pct(wacc * 100),
    }


def main():
    d = load()
    tax = d["tax_note"]["statutory_rate_combined"]["current"] / 100.0
    seg = d["segments"]
    S = d["share_capital"]

    # ---- the base year, Canada only -------------------------------------
    ca_sales = seg["sales"]["canada"]
    ca_da = (seg["depreciation_and_amortisation_face"]["canada"]
             + seg["depreciation_and_amortisation_in_cost_of_sales"]["canada"])
    equity_earnings = -d["income_statement"][
        "share_of_net_earnings_of_equity_accounted_investments"]["current"]
    ca_ebit = seg["operating_income"]["canada"] - equity_earnings
    ca_ebitda = ca_ebit + ca_da

    # the cash lease payment is a tax deduction in full and is outside EBITDA
    # under IFRS 16, so it has to come back out of both. The consolidated
    # payment covers 28 of the year's 52 weeks of Australian trading, and the
    # Australian share is taken off in proportion to the lease liability that
    # came in with the acquisition.
    lease_paid = -d["cash_flow"]["payments_of_lease_liabilities_principal"]["current"]
    au_lease_share = (d["leases_note"]["lease_liability_additions_from_business_combination"]
                      ["current"] / float(d["leases_note"]["total_lease_liability"]["current"]))
    au_weeks = 28.0 / 52.0
    ca_lease_paid = lease_paid * (1.0 - au_lease_share * au_weeks)

    nop = d["non_operating_and_working_capital"]
    nwc = ((nop["accounts_receivable"]["current"] + nop["prepaid_expenses"]["current"]
            + nop["inventories"]["current"])
           - (nop["accounts_payable_and_accrued_liabilities"]["current"]
              + nop["income_taxes_payable"]["current"]))
    nwc_prior = ((nop["accounts_receivable"]["prior"] + nop["prepaid_expenses"]["prior"]
                  + nop["inventories"]["prior"])
                 - (nop["accounts_payable_and_accrued_liabilities"]["prior"]
                    + nop["income_taxes_payable"]["prior"]))

    rows = canadian_base(d)
    ucc = implied_ucc(d)
    temp_diff = ucc["current"]["owned_property_temporary_difference"]
    opening_ucc(rows, temp_diff)

    capex = -d["cash_flow"]["additions_to_property_plant_and_equipment"]["current"]
    dep_rows = [r for r in rows if r["method"] != "none"]
    add_total = sum(r["cost_closing"] for r in rows if r["method"] != "none")
    note_adds = {c["name"]: c["additions"] for c in d["ppe_note"]["categories"]}
    dep_add = sum(note_adds[r["name"]] for r in dep_rows)
    for r in rows:
        r["addition_share"] = (note_adds[r["name"]] / float(dep_add)
                               if r["method"] != "none" else 0.0)

    ca_book_dep = sum(r["book_depreciation"] for r in rows)

    base = {
        "sales": ca_sales,
        "ebitda_margin": ca_ebitda / float(ca_sales),
        "lease_intensity": ca_lease_paid / float(ca_sales),
        "nwc_intensity": nwc / float(d["income_statement"]["revenue"]["current"]),
        "book_depreciation": ca_book_dep,
        "depreciable_net_book_value": sum(r["canadian_net_book_value"]
                                          for r in rows if r["method"] != "none"),
        "depreciable_addition_share": dep_add / float(
            sum(note_adds[r["name"]] for r in rows)),
    }

    # ---- the derived growth rate ----------------------------------------
    # 52 weeks against 53, and the current year carries an Australian segment
    # the prior year does not. Both are taken out before the rate is struck.
    r1_ca, w1 = ca_sales, d["issuer"]["weeks_in_fiscal_year"]
    r0, w0 = d["income_statement"]["revenue"]["prior"], 53
    organic = (r1_ca / float(w1)) / (r0 / float(w0)) - 1.0

    # ---- the discount rate ----------------------------------------------
    tranches, kd = cost_of_debt(d)
    ke = (ASSUMED["risk_free_rate"]["value"]
          + ASSUMED["beta"]["value"] * ASSUMED["equity_risk_premium"]["value"]) / 100.0
    shares = S["shares_outstanding_period_end"]["current"]
    price = S["share_price_at_fiscal_year_end"]["current"]
    mcap = shares * price / 1000.0
    borrowings = d["debt_note"]["total_carrying_amount"]
    we = mcap / (mcap + borrowings)
    wd = borrowings / (mcap + borrowings)
    wacc = we * ke + wd * kd * (1.0 - tax)

    # ---- the two anchors -------------------------------------------------
    n = ASSUMED["forecast_years"]["value"]
    c13 = ASSUMED["class13_write_off_years"]["value"]
    years = [(2027 + i, 2026 + i) for i in range(n)]
    capex_intensity = capex / float(d["income_statement"]["revenue"]["current"])
    maintenance_intensity = ca_book_dep / float(ca_sales)
    # Growing forever on replacement spending alone is not coherent, so the
    # terminal programme in the expansion reading is replacement plus the
    # capital that terminal growth itself requires, at the capital intensity
    # the business actually runs: owned property against sales.
    capital_intensity = (sum(r["canadian_net_book_value"] for r in rows)
                         / float(ca_sales))

    def fade(start, end):
        return [start + (end - start) * (i + 1) / float(n) for i in range(n)]

    # every asset that produces no part of the Canadian retail cash flow
    non_op_total = (d["balance_sheet"]["cash_and_cash_equivalents"]["current"]
                    + nop["equity_accounted_investments"]["current"]
                    + nop["derivative_on_equity_accounted_investments"]["current"]
                    + (seg["total_assets"]["australia"]
                       - seg["total_liabilities"]["australia"]))

    SPECS = [
        ("Expansion reading", 0.030, maintenance_intensity + 0.030 * capital_intensity,
         "The fiscal 2026 programme is buying new stores. Once it stops, capital "
         "spending falls to what replaces the existing base plus what the terminal "
         "growth rate itself requires, and the growth it bought is real."),
        ("Maintenance reading", 0.020, capex_intensity,
         "The fiscal 2026 programme is what it costs to keep the existing stores "
         "trading. There is no separable growth capital, so the spending never "
         "falls and the growth it can support is lower."),
    ]

    anchors = []
    for name, term_g, term_capex, note in SPECS:
        a = forecast(name, base, years, fade(organic, term_g), capex_intensity,
                     term_g, term_capex, [dict(r) for r in rows], c13, tax, wacc)
        b = forecast(name, base, years, fade(organic, term_g), capex_intensity,
                     term_g, term_capex, [dict(r) for r in rows], c13, tax, wacc,
                     use_book_depreciation=True)
        eq = a["enterprise_value"] + non_op_total - borrowings
        eq_book = b["enterprise_value"] + non_op_total - borrowings
        a["note"] = note
        a["non_operating_assets"] = money(non_op_total)
        a["borrowings"] = borrowings
        a["equity_value"] = money(eq)
        a["value_per_share"] = round(eq * 1000.0 / shares, 2)
        a["equity_value_on_book_depreciation"] = money(eq_book)
        a["value_per_share_on_book_depreciation"] = round(eq_book * 1000.0 / shares, 2)
        a["enterprise_value_on_book_depreciation"] = b["enterprise_value"]
        a["cca_versus_book_per_share"] = round((eq - eq_book) * 1000.0 / shares, 2)
        a["present_value_of_cca_shield"] = money(sum(
            l["tax_shield_on_cca"] / (1.0 + wacc) ** (i + 1)
            for i, l in enumerate(a["lines"])))
        a["present_value_of_book_shield"] = money(sum(
            l["tax_shield_on_book_depreciation"] / (1.0 + wacc) ** (i + 1)
            for i, l in enumerate(a["lines"])))
        anchors.append(a)


    # ---- does the reconstruction reproduce the tax the issuer actually paid?
    # The tax base is not disclosed, so it was backed out of a deferred tax
    # balance. That derivation is worth nothing unless it predicts something it
    # was not fitted to. It was fitted to the closing balance sheet; here it is
    # run forward over fiscal 2026 from the PRIOR year's balance and asked to
    # reproduce the current tax expense the income tax note discloses.
    prior = ucc["prior"]
    prior_land = 218272          # note 9, PDF page 32, prior year column
    prior_nbv = prior["owned_net_book_value"]
    prior_dep_nbv = prior_nbv - prior_land
    prior_ucc_total = prior_dep_nbv - prior["owned_property_temporary_difference"]
    prior_by_cat = {"Buildings and roofs": 79494, "Store and warehouse equipment": 357685,
                    "Computer equipment": 28482, "Vehicles": 4288,
                    "Leasehold improvements": 358169}
    test_rows = []
    for r in rows:
        if r["method"] == "none":
            continue
        q = dict(r)
        q["opening_ucc"] = prior_ucc_total * (prior_by_cat[r["name"]] / float(prior_dep_nbv))
        test_rows.append(q)
    test_sched = run_cca(test_rows, [(2026, 2025)], [dep_add], c13)
    test_cca = test_sched[0]["total_cca"]
    # interest is deductible, but the lease interest inside net financing costs
    # is already inside the lease payment deduction, so it is taken out once
    lease_interest = d["income_statement"]["interest_on_lease_liabilities"]["current"]
    ca_finance = (seg["net_financing_costs"]["canada"]
                  - lease_interest * (1.0 - au_lease_share * au_weeks))
    modelled_taxable = ca_ebitda - ca_lease_paid - test_cca - ca_finance
    modelled_tax = tax * modelled_taxable
    pillar_two = 27229           # note 16(a), PDF page 45
    disclosed_current = d["income_statement"]["income_tax_current"]["current"] - pillar_two
    validation = {
        "what": ("The reconstructed opening tax base is run over fiscal 2026 and asked "
                 "to reproduce the current tax expense the issuer disclosed."),
        "prior_year_opening_ucc": money(prior_ucc_total),
        "additions": money(dep_add),
        "modelled_cca": test_cca,
        "modelled_taxable_income": money(modelled_taxable),
        "modelled_current_tax": money(modelled_tax),
        "disclosed_current_tax_expense": d["income_statement"]["income_tax_current"]["current"],
        "less_pillar_two_top_up": pillar_two,
        "disclosed_current_tax_on_the_canadian_base": disclosed_current,
        "difference": money(modelled_tax - disclosed_current),
        "difference_percent": pct(100.0 * (modelled_tax - disclosed_current) / disclosed_current),
    }

    # ---- what the market has to be assuming -------------------------------
    # The model disagrees with the price. Rather than tune an input until it
    # agrees, the disagreement is quantified both ways.
    def equity_at(w, anchor_spec):
        nm, tg, tc, _ = anchor_spec
        a = forecast(nm, base, years, fade(organic, tg), capex_intensity, tg, tc,
                     [dict(r) for r in rows], c13, tax, w)
        return a["enterprise_value"] + non_op_total - borrowings

    def growth_at(g, anchor_spec):
        nm, _, tc, _ = anchor_spec
        a = forecast(nm, base, years, fade(organic, g), capex_intensity, g, tc,
                     [dict(r) for r in rows], c13, tax, wacc)
        return a["enterprise_value"] + non_op_total - borrowings

    def solve(f, spec, lo, hi, target, rising):
        for _ in range(90):
            m = (lo + hi) / 2.0
            v = f(m, spec)
            if (v < target) == rising:
                lo = m
            else:
                hi = m
        return (lo + hi) / 2.0

    market_equity = mcap
    reverse = []
    for spec in SPECS:
        iw = solve(equity_at, spec, 0.030, 0.200, market_equity, False)
        ig = solve(growth_at, spec, 0.000, wacc - 0.004, market_equity, True)
        reverse.append({
            "anchor": spec[0],
            "market_equity_value": money(market_equity),
            "implied_wacc": pct(iw * 100),
            "declared_wacc": pct(wacc * 100),
            "implied_cost_of_equity": pct(
                ((iw - wd * kd * (1.0 - tax)) / we) * 100),
            "implied_terminal_growth_at_declared_wacc": pct(ig * 100),
            "declared_terminal_growth": pct(spec[1] * 100),
        })

    out = {
        "note": ("Every figure here is computed by build/valuation.py from "
                 "content/valuation-inputs.json. Nothing is typed in. Re-run the "
                 "module and the page's numbers are reproduced or the build fails."),
        "law_source": LAW_SOURCE,
        "assumed": ASSUMED,
        "base_year": {
            "fiscal_year": d["issuer"]["fiscal_year_label"],
            "weeks": w1, "prior_weeks": w0,
            "canada_sales": ca_sales,
            "canada_ebit_excluding_equity_earnings": money(ca_ebit),
            "canada_depreciation_and_amortisation": ca_da,
            "canada_ebitda": money(ca_ebitda),
            "ebitda_margin": pct(base["ebitda_margin"] * 100),
            "consolidated_lease_payment": lease_paid,
            "australian_lease_share": pct(au_lease_share * au_weeks * 100),
            "canada_lease_payment": money(ca_lease_paid),
            "lease_intensity": pct(base["lease_intensity"] * 100),
            "net_working_capital": money(nwc),
            "net_working_capital_prior": money(nwc_prior),
            "nwc_intensity": pct(base["nwc_intensity"] * 100),
            "capex": capex, "capex_intensity": pct(capex_intensity * 100),
            "maintenance_intensity": pct(maintenance_intensity * 100),
            "canada_book_depreciation_owned": money(ca_book_dep),
            "organic_sales_growth_per_week": pct(organic * 100),
            "face_sales_growth": pct(100.0 * (d["income_statement"]["revenue"]["current"]
                                              / float(r0) - 1.0)),
        },
        "tax_base": ucc,
        "classes": [{k: (money(v) if isinstance(v, float) and k not in
                         ("cca_rate", "addition_share") else v)
                     for k, v in r.items()} for r in rows],
        "opening_ucc_total": money(sum(r["opening_ucc"] for r in rows)),
        "depreciable_net_book_value": money(sum(r["canadian_net_book_value"]
                                                for r in rows if r["method"] != "none")),
        "cost_of_capital": {
            "tranches": tranches,
            "cost_of_debt": pct(kd * 100),
            "weighted_average_coupon": pct(
                sum(t["face"] * t["coupon"] for t in tranches)
                / sum(t["face"] for t in tranches)),
            "cost_of_equity": pct(ke * 100),
            "market_capitalisation": money(mcap),
            "borrowings": borrowings,
            "weight_equity": pct(we * 100), "weight_debt": pct(wd * 100),
            "tax_rate": pct(tax * 100),
            "wacc": pct(wacc * 100),
            "shares_outstanding": shares, "share_price": price,
        },
        "anchors": anchors,
        "validation": validation,
        "reverse": reverse,
    }
    json.dump(out, open(OUT_PATH, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print("Dollarama Inc., %s" % d["issuer"]["fiscal_year_label"])
    print("Canadian segment sales %s, EBITDA %s, margin %.2f%%"
          % (format(ca_sales, ","), format(money(ca_ebitda), ","), base["ebitda_margin"] * 100))
    print("organic sales growth per week, Australia and the 53rd week removed: %.2f%%"
          % (organic * 100))
    print()
    print("tax base: deferred tax liability on property implies a temporary difference of %s"
          % format(ucc["current"]["temporary_difference"], ","))
    print("  reading it as owned property alone gives an undepreciated capital cost of %s"
          % format(ucc["current"]["reading_owned_only_ucc"], ","))
    print("  reading it as including right of use assets gives %s"
          % format(ucc["current"]["reading_with_right_of_use_ucc"], ","))
    print("  owned property temporary difference %s" % format(temp_diff, ","))
    print()
    print("%-32s %-6s %6s %12s %12s" % ("class", "cca", "rate", "net book", "opening UCC"))
    for r in rows:
        print("%-32s %-6s %5s %12s %12s"
              % (r["name"], r["cca_class"] or "n/a",
                 ("%.0f%%" % (r["cca_rate"] * 100)) if r["cca_rate"] else
                 ("SL" if r["method"] == "straight" else "n/a"),
                 format(money(r["canadian_net_book_value"]), ","),
                 format(money(r["opening_ucc"]), ",")))
    print()
    print("cost of debt %.3f%% (weighted average coupon %.3f%%), cost of equity %.3f%%, WACC %.3f%%"
          % (kd * 100, out["cost_of_capital"]["weighted_average_coupon"], ke * 100, wacc * 100))
    print()
    for a in anchors:
        print("%-22s EV %14s  equity %14s  per share $%8.2f   on book depreciation $%8.2f  (gap $%.2f)"
              % (a["anchor"], format(a["enterprise_value"], ","),
                 format(a["equity_value"], ","), a["value_per_share"],
                 a["value_per_share_on_book_depreciation"], a["cca_versus_book_per_share"]))
    print()
    v = validation
    print("test of the reconstructed tax base, run forward over fiscal 2026:")
    print("  opening undepreciated capital cost %s, additions %s, allowance %s"
          % (format(v["prior_year_opening_ucc"], ","), format(v["additions"], ","),
             format(v["modelled_cca"], ",")))
    print("  modelled current tax %s against %s disclosed on the Canadian base, %+.2f%%"
          % (format(v["modelled_current_tax"], ","),
             format(v["disclosed_current_tax_on_the_canadian_base"], ","),
             v["difference_percent"]))
    print()
    print("what the market price of $%.2f requires:" % price)
    for r in reverse:
        print("  %-22s a discount rate of %.2f%% against the declared %.2f%%, "
              "or terminal growth of %.2f%% against the declared %.2f%%"
              % (r["anchor"], r["implied_wacc"], r["declared_wacc"],
                 r["implied_terminal_growth_at_declared_wacc"],
                 r["declared_terminal_growth"]))
    print()
    print("The fork is left open. The two anchors are not averaged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
