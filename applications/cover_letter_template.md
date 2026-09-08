# LEESHARAM (ALEX) RAJCOOMAR

Brampton, ON | (647) 471-3023 | a2rajcoo@uwaterloo.ca
linkedin.com/in/leesharam-rajcoomar | **alexrajcoomar.github.io**
*Available for a January to April 2027 co-op work term*

---

## HOW TO USE

Four blocks make a letter: the opening, paragraph 1, one paragraph 2, then
paragraphs 3 and 4. Only paragraph 2 changes between applications, and inside
it only the bracketed closing sentence changes between firms. Assembled, a
letter runs about 210 words and lands on one page with room to spare.

Three minutes per application: fill the four brackets in the opening and
paragraph 1, pick the option, write the one bracketed sentence at the end of
it, done. Do not fill a bracket with a phrase that would fit any other firm. If
you cannot name something specific to this one, delete the sentence instead:
an empty slot reads better than a compliment that fits anyone.

`build_resumes.py` compiles each option into its own one-page PDF and DOCX, so
in practice you open the compiled file for the option you want and type into
the brackets. Option A is the one saved as `Cover_Letter_Template`, because
Domains 1 and 2 take 24 of the 50 applications.

| Option | Use for | Compiled as |
|---|---|---|
| A | Regional CPA practices, MNP tax, corporate tax, any January to April season | `Cover_Letter_Template` |
| B | Big Four assurance, Crowe Soberman, OAG Ontario, CIRO, HOOPP, forensic and dispute advisory | `Cover_Letter_Option_B_Assurance` |
| C | Corporate FP&A, commercial finance, treasury, fund reporting | `Cover_Letter_Option_C_FPA` |
| D | Accounting technology, FinOps, workflow automation, SR&ED | `Cover_Letter_Option_D_FinOps` |

Every figure below is verified against the repository. Before changing one,
read `applications/VERIFIED_METRICS.md`: the site publishes the same numbers,
and a recruiter who follows the link will see them.

## BLOCK: opening

[Date]

[Hiring contact name]
[Firm name]
[City, Province]

Dear [Hiring contact name],

## BLOCK: p1

I am applying for the [exact posting title], WaterlooWorks posting [ID], at
[firm name]. I am a second-year Accounting and Financial Management student at
the University of Waterloo, available full time from January to April 2027. I
have already worked a complete Canadian personal tax season, preparing and
reviewing 200+ T1 returns in DT Max, so I can be billable in the first week of
the term rather than the fourth.

## BLOCK: p2-a | Tax and staff accounting

Your term runs across the 2027 filing season, which is work I have already
done. At Taxwide I built 200+ T1 files in DT Max from client documentation and
CRA Auto-fill my return downloads, then reviewed every return against its
source slips before signature. That review is where the work actually sat:
unreported slips, spouse or common-law partner amount claims turning on a
spouse's net income, and balances owing reconciled to CRA administrative
positions before a client could be told what they owed and why. [One sentence
naming something specific to this firm.]

## BLOCK: p2-b | Audit, assurance and investigations

The work your team would care about is published rather than claimed. Flagged
in Hindsight runs the Beneish M-Score ex ante on five Canadian frauds and
reports that none of the three computable test years crossed the standard
cut-off, with the script and inputs published so the result can be re-run and
attacked. My IFRS 15 trainer carries
62 revenue scenarios verified against Part I of the CPA Canada Handbook, and it
separates what the standard settles from what it leaves to judgment. Both rest
on the habit a tax file teaches: agree the figure to its source first. [One sentence naming this team's mandate.]

## BLOCK: p2-c | FP&A and financial analysis

I model capital decisions and test whether they survive being wrong.
For a Pet Valu strategic growth case I built three-year pro formas for two
capital deployment strategies behind a $575M expansion, stress-testing ROA,
debt to EBITDA and net profit margin, and recommended the conservative path to
a simulated CEO and CFO panel on a sustained 16% ROA against a decline from 17%
to 10% under the aggressive case. I build the reporting layer as well as the
model, in Tableau and in Python, and I have reconciled the data at volume
through a tax season. [One sentence on this company's own capital or
margin problem.]

## BLOCK: p2-d | Accounting technology and FinOps

Most people who can write the code cannot read a deferred tax note, and most
people who can read it cannot write the code. I do both, and the evidence is
public: 14,719 lines of Python behind a research platform that recomputes every
figure it publishes and refuses to deploy when the page and the model disagree.
The reconciliation instinct came from a tax season where 200+ files had to
agree to their source slips before release, and the automation instinct came
from watching how much of that reconciliation was mechanical. [One sentence on
the workflow this role would automate.]

## BLOCK: p3

Everything above is published at alexrajcoomar.github.io, where every figure
names its source, every derived number is labelled as derived, and the build
refuses to publish if a number does not match the data behind it. I would
rather be checkable than impressive, and I expect to be asked how I know
something.

## BLOCK: p4

I would welcome the chance to discuss the role with you. I can be reached at
a2rajcoo@uwaterloo.ca or (647) 471-3023.

## BLOCK: sign

Sincerely,

Leesharam (Alex) Rajcoomar
