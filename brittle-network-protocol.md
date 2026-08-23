# Cascading Network Failure in Antiquity

## Modeling the 1177 BC Late Bronze Age Collapse as a Complex Systems Breakdown

**Research Protocol and Methodological Framework — v1.0**

| Field | Value |
| --- | --- |
| Document type | Pre-registration-grade research protocol (methodology only; no results claimed) |
| Temporal universe | 1250–1100 BCE, with 1400–1250 BCE baseline and 1100–1000 BCE recovery window |
| Spatial universe | Aegean, Anatolia, Cyprus, the Levant and Egypt (core, ~20°E–40°E / 27°N–42°N), with Mesopotamian, Central Mediterranean, and Central Asian tin-source extensions |
| Primary unit of analysis | The inter-polity exchange network, not the individual polity |
| Design class | Multiproxy observational study with formal model comparison; no experimental manipulation is possible |
| Inferential target | Relative support for competing generative models of systemic failure, expressed as posterior model probabilities |
| Required disciplines | Archaeology (Aegean, Anatolian, Levantine, Cypriot, Egyptian), Assyriology/Ugaritic philology, palynology, speleothem geochemistry, archaeoseismology, archaeometallurgy, statistical chronology, network science, agent-based modelling |

---

## 0. Scope Statement, Premise Audit, and Epistemic Contract

Before any framework is specified, three corrections to the framing of the research question are entered into the record. A protocol that inherits an imprecise premise will produce precise-looking answers to the wrong question.

### 0.1 "Prove or disprove" is not an available inferential mode

The collapse is a single, unrepeatable historical realization with n = 1 at the system level. No dataset can *prove* a causal architecture for it. The protocol therefore replaces proof with **severity of test** in the Mayo sense: each hypothesis is required to generate predictions that would very probably have failed had the hypothesis been false, and the analysis reports **posterior model probabilities and Bayes factors**, not verdicts. Where a hypothesis cannot be made to generate a differential prediction against its rivals, it is declared **empirically inert for this study** and excluded rather than argued about.

The operative question is therefore not *"did the network cause the collapse?"* but:

> Given the observed spatiotemporal pattern of destruction, abandonment, contraction, and survival across the Eastern Mediterranean between 1250 and 1100 BCE, which class of generative model — exogenous-shock-only, network-topology-only, or shock-propagating-through-brittle-topology — assigns the highest likelihood to the observed pattern, and how large is the margin relative to the uncertainty in the evidence?

### 0.2 The date "1177 BC" is a heuristic anchor, not a datum

1177 BCE corresponds to Year 8 of Ramesses III as recorded in the Medinet Habu inscriptions, the occasion of the best-known Egyptian account of conflict with the coalition conventionally labelled the Sea Peoples. Cline himself deploys the date as a narrative anchor for a multi-decadal process, not as the year of a discrete event. This protocol treats the collapse as a **transition interval**, provisionally 1225–1130 BCE, whose boundaries are themselves parameters to be estimated from a Bayesian chronological model (§2.3), not assumed.

### 0.3 The Hallstatt plateau is the wrong radiocarbon obstacle for this period — correction entered

The source brief cites the Hallstatt plateau as the chronological hazard. **This is a period misassignment and the protocol does not adopt it.** The Hallstatt plateau spans approximately **800–400 cal BC**: radiocarbon determinations near 2450 BP calibrate across that entire four-century span regardless of measurement precision, because atmospheric ¹⁴C concentration changed in a way that flattens the calibration curve there. It lies two to six centuries *after* the study window and is irrelevant to 1250–1100 BCE.

The genuine chronological hazards for this window are different in kind and are addressed in §2.3:

1. **Calibration-curve structure at 1250–1050 BC.** IntCal20 is comparatively well-behaved here relative to the Hallstatt interval, but wiggles in the twelfth–eleventh century produce multi-modal calibrated distributions that routinely span 60–120 years at 95.4% probability for single determinations — a resolution *coarser than the entire causal sequence under investigation.*
2. **Regional and growing-season radiocarbon offsets.** Demonstrated offsets between Northern Hemisphere calibration data and Eastern Mediterranean/southern Levantine samples arise from differing growing seasons and regional carbon-cycle behaviour. These are of the order of a few decades — which is negligible for most prehistoric questions and *decisive* for a question about the ordering of events within a century.
3. **Dating-target ambiguity.** A radiocarbon date typically dates a plant's death, not a destruction. Old-wood effects in structural timber, curated heirloom objects, and residual charcoal in fills all displace the date from the event.
4. **The Aegean–Levantine chronological interlock.** The relative sequences of Mycenaean LH IIIB/IIIC ceramics, Cypriot LC IIC/IIIA, Levantine LB IIB/Iron IA, and Egyptian regnal chronology are cross-linked by ceramic synchronisms. An error in any one link propagates through the whole grid; the protocol therefore models these synchronisms as **uncertain priors, not as fixed pegs**.

### 0.4 Epistemic contract

The following commitments are binding on all four phases and are auditable at review.

- **Non-fabrication.** No site, text, tablet siglum, core, ingot, or study is cited unless it is verifiable in the published record. Where the required evidence class exists but a specific dataset has not been confirmed by the protocol authors, the document specifies the **evidence type, acceptance criteria, and sampling requirement** in place of a citation. Such placeholders are marked `[DATA REQUIREMENT]`.
- **Separation of layers.** Evidence, model, and interpretation are kept in separate registers throughout. A quantity produced by the model is never reported in the same sentence as a quantity observed in the ground without an explicit marker.
- **Pre-registration.** §5.1 specifies the analysis plan, the falsification criteria, and the stopping rules *before* data compilation begins. Deviations are logged in an amendment register, not silently absorbed.
- **Adversarial review.** Each phase is reviewed by a named scholar who is on record as sceptical of the hypothesis (§5.5).

---

# Phase 1 — Theoretical Framework and Literature Synthesis

**Objective:** establish the historiographical trajectory from monocausal invasion narrative to systems explanation, and — critically — translate each historiographical position into a *formal object* that the Phase 3 model can instantiate and discriminate between. Synthesis that does not terminate in a formalizable claim is not admitted.

## 1.1 The historiographical arc

The literature falls into five broad, partially overlapping generations. The protocol characterizes each by its **causal topology**, because that is what determines whether the position can be tested by network methods.

### Generation I — Migrationist / catastrophist (late 19th c. – mid 20th c.)

Causal topology: **single exogenous agent → many simultaneous failures.** Derived principally from Egyptian royal inscriptions (Medinet Habu, Year 8 of Ramesses III; the Great Karnak Inscription of Merneptah) read as reportage, supplemented by destruction horizons excavated at Levantine and Anatolian sites and interpreted as the archaeological signature of a named invading coalition.

Formal representation: an exogenous node-deletion process with a **spatially contiguous, temporally near-simultaneous** removal schedule, applied to a network whose topology is causally inert.

Testable implication: destruction dates should cluster tightly in time along a coherent spatial front, and destruction incidence should be **uncorrelated with network position** once coastal exposure is controlled.

### Generation II — Systems collapse (Renfrew, Tainter, and successors)

Causal topology: **internal structural properties → failure under generic stress.** Renfrew's formulation of systems collapse for the Aegean, and Tainter's argument that complex societies collapse when the marginal return on added complexity turns negative, moved the explanatory weight from the identity of an external agent to the internal architecture of the society. Collapse becomes a *property of the system's organization* rather than an event that befalls it.

- Renfrew, C. 1979. "Systems Collapse as Social Transformation," in *Transformations: Mathematical Approaches to Culture Change* (Renfrew & Cooke, eds.). Academic Press.
- Tainter, J.A. 1988. *The Collapse of Complex Societies.* Cambridge University Press. ISBN 9780521386739.

Formal representation: a system with a state-dependent failure probability that rises as an internal complexity or specialization parameter rises, independent of the shock's identity.

Testable implication: failure severity should scale with pre-collapse measures of specialization and administrative elaboration, and should be **insensitive to which exogenous shock is applied**.

### Generation III — Multicausal "perfect storm" (Cline and the confluence literature)

Causal topology: **conjunction of several sufficient-in-combination, insufficient-in-isolation stressors.** The anchor text for this study:

- Cline, E.H. 2014/2021. *1177 B.C.: The Year Civilization Collapsed.* Princeton University Press. Revised and updated edition 2021, ISBN 9780691208015 (orig. ISBN 9780691140896). JSTOR stable ID `j.ctv15r58dw`.
- Cline, E.H. 2024. *After 1177 B.C.: The Survival of Civilizations.* Princeton University Press, ISBN 9780691192130. Essential to this protocol because it addresses **differential survival** — the outcome variable that most sharply discriminates between the competing models (§1.4).

Cline's argument assembles drought, famine, earthquakes, internal rebellion, invasion, and the severing of international trade routes into a conjunctural explanation, and explicitly invokes complexity-science vocabulary — hypercoherence, systems collapse — as the integrating frame.

Formal representation: a multiplicative or threshold interaction among stressors, in which no single stressor exceeds the failure threshold alone.

Testable implication: interaction terms in the failure model carry significant weight; the marginal effect of each stressor conditional on the others is materially larger than its unconditional effect.

**Where Generation III stops short — and where this study begins.** The confluence model states that stressors interacted; it does not specify *the mechanism of interaction*, nor does it predict *which* polities fail and which survive. The step this protocol takes is to name the interaction medium as the exchange network itself and to make that claim quantitative.

### Generation IV — Formal network and complexity approaches

Causal topology: **exogenous shock → topologically structured propagation → spatially patterned, temporally lagged failure.**

The essential methodological precedent is the Aegean maritime-network modelling programme, which established that formal, spatially explicit network models can generate archaeologically testable expectations about which centres matter and what happens when the network is perturbed:

- Knappett, C., Evans, T. & Rivers, R. 2008. "Modelling maritime interaction in the Aegean Bronze Age." *Antiquity* 82(318): 1009–1024.
- Knappett, C., Rivers, R. & Evans, T. 2011. "The Theran eruption and Minoan palatial collapse: new interpretations gained from modelling the maritime network." *Antiquity* 85(329): 1008–1023. DOI `10.1017/S0003598X00068459`.
- Knappett, C. (ed.) 2013. *Network Analysis in Archaeology: New Approaches to Regional Interaction.* Oxford University Press.
- Leidwanger, J. & Knappett, C. (eds.) 2018. *Maritime Networks in the Ancient Mediterranean World.* Cambridge University Press. ISBN 9781108429948. Chapters 1–3 supply the connectivity framework and the robustness-of-spatial-network-analysis treatment this protocol adopts.

The 2011 Thera paper is the direct methodological ancestor of the present design: it perturbs a modelled network by removing a node and reads the systemic consequence, rather than inferring consequence from destruction layers alone.

For the diplomatic layer, a directly relevant precedent already exists and must be built upon rather than duplicated:

- Cline, D.H. & Cline, E.H. 2015. "Text Messages, Tablets, and Social Networks: The 'Small World' of the Amarna Letters," in J. Mynářová, P. Onderka & P. Pavúk (eds.), *There and Back Again — the Crossroads II*, 17–44. Prague: Charles University. (An expanded treatment by the same authors has since appeared; the protocol will cite the version of record at write-up.)

### Generation V — The revisionist correction (mandatory counterweight)

Any protocol that only reads the collapse literature will overfit to collapse. The following body of work argues that the destruction horizon is thinner, later, more staggered, and less trade-terminating than the standard narrative asserts, and that "collapse" partly reflects excavation and publication practice:

- Millek, J.M. 2023. *Destruction and Its Impact on Ancient Societies at the End of the Bronze Age.* Columbus: Lockwood Press. ISBN 9781948488839.
- Millek, J.M. 2021. "Dual Narratives: Collapse and Transition at the End of the Late Bronze Age," in F. Manuelli & C.W. Hess (eds.), *Bridging the Gap: Disciplines, Times, and Spaces in Dialogue*, vol. 1, 252–264. Oxford: Archaeopress.
- Millek, J.M. 2022. "The Impact of Destruction on Trade at the End of the Late Bronze Age in the Southern Levant," in F. Hagemeyer (ed.), *Jerusalem and the Coastal Plain in the Iron Age and Persian Periods*, 39–60. Tübingen: Mohr Siebeck.

Millek's re-examination of claimed destruction layers is the single most important control on this project. If a substantial fraction of the "destructions" in the standard corpus are misidentified — collapse from abandonment, fire from industrial activity or post-depositional processes, or dated by circular ceramic reasoning — then the observed pattern that Phase 3 is asked to explain is partly an artefact. **The Millek re-audit is therefore not a citation but a data-processing stage (§2.4).**

For the Sea Peoples specifically, the philological and archaeological source-criticism must be read at first hand rather than through synthesis:

- Killebrew, A.E. & Lehmann, G. (eds.) 2013. *The Philistines and Other "Sea Peoples" in Text and Archaeology.* Society of Biblical Literature, Archaeology and Biblical Studies 15. ISBN 9781589831292.

## 1.2 The translation: from historiographical claim to mathematical object

This is the pivotal deliverable of Phase 1. Each narrative claim is mapped to a formal operator so that Phase 3 can implement it. Terms are defined in Appendix A.

| Historiographical claim | Formal object | Perturbation operator | Discriminating observable |
| --- | --- | --- | --- |
| "The Sea Peoples destroyed the palaces" | Exogenous, spatially correlated node deletion on a causally inert graph | Delete set of coastal nodes over a short interval Δt; topology plays no role | Destruction incidence predicted by coastal exposure alone; **no** residual effect of centrality |
| "Drought caused famine and unrest" | Reduction in node-level agricultural carrying capacity | Scale node production capacity `π_i → (1−δ_i)π_i`, `δ_i` drawn from the hydroclimate field | Failure severity tracks the *local* hydroclimate gradient, with short lag |
| "Earthquake storms shattered the palaces" | Temporally clustered, tectonically constrained node damage | Delete/degrade nodes along active fault systems on a clustered point process | Damage confined to seismogenic zones; failure order follows fault geometry, not trade rank |
| "Trade routes were cut" | Edge deletion, targeted or random | Remove edges by weight rank, by geography, or at random | Loss of connectivity precedes loss of settlement; downstream nodes fail before upstream ones |
| "The system was hypercoherent / over-optimized" | High global efficiency `E_glob`, low structural redundancy, heavy-tailed degree distribution | No perturbation — a *property of the intact graph* measured against null models | Intact network has high `E_glob` and low `R` (robustness index) relative to degree-preserving and spatial null models |
| "A cascading failure occurred" | Load-redistribution dynamics on a weighted graph | Motter–Lai cascade: capacity `C_i = (1+α)L_i(0)` with tolerance `α`; failures redistribute load | Failure times are **temporally ordered along network paths**, with lags proportional to path distance from the seed |
| "The collapse was a phase transition" | Percolation transition in the supply-satisfaction functional | Sweep removal fraction `f`; locate critical point | Order parameter shows a sharp drop; susceptibility `χ` peaks; finite-size scaling consistent with a transition rather than gradual decline |
| "Interdependence between subsystems amplified failure" | Coupled multiplex with inter-layer dependency links | Buldyrev-type iterative cascade between metals, grain, and political layers | Transition is **first-order (discontinuous)** rather than continuous — the signature of interdependence |
| "The Sea Peoples were a symptom" | Endogenous generation of mobile actors by prior system stress | Migration/raiding intensity is an output of the model, not an input | Textual and archaeological attestations of raiding **post-date** the onset of supply and hydroclimate stress at the source regions |

The last row is the study's central historiographical wager, and it is falsifiable in a clean way: if the earliest robust attestations of Sea Peoples activity **precede** the earliest robust indicators of network and climate stress, the symptom hypothesis fails, and it fails independently of anything the network model produces.

## 1.3 Foundational positions on the environmental and economic drivers

Five verified anchors, selected because each supplies a distinct, independently derived proxy stream rather than a restatement of the same evidence.

1. **Langgut, D., Finkelstein, I. & Litt, T. 2013.** "Climate and the Late Bronze Collapse: New Evidence from the Southern Levant." *Tel Aviv* 40(2): 149–175. DOI `10.1179/033443513X13753505864205`. High-resolution palynological study including the Sea of Galilee core; identifies a dry episode in the Late Bronze–Iron transition in the southern Levant. This is the paper behind the "Sea of Galilee pollen" evidence named in the brief.
2. **Kaniewski, D., Van Campo, E., Guiot, J., Le Burel, S., Otto, T. & Baeteman, C. 2013.** "Environmental Roots of the Late Bronze Age Crisis." *PLOS ONE* 8(8): e71004. DOI `10.1371/journal.pone.0071004`. Larnaca Salt Lake core, Cyprus (adjacent to Hala Sultan Tekke); argues for a ca. 300-year drought episode beginning in the late thirteenth century BCE and explicitly frames the Sea Peoples as consequence rather than cause.
3. **Drake, B.L. 2012.** "The influence of climatic change on the Late Bronze Age Collapse and the Greek Dark Ages." *Journal of Archaeological Science* 39(6): 1862–1870. Uses sea-surface-temperature and stable-isotope evidence to argue for reduced Mediterranean precipitation preceding the collapse. Supplies the *marine* proxy stream, methodologically independent of terrestrial pollen.
4. **Nur, A. & Cline, E.H. 2000.** "Poseidon's Horses: Plate Tectonics and Earthquake Storms in the Late Bronze Age Aegean and Eastern Mediterranean." *Journal of Archaeological Science* 27(1): 43–63. The origin of the "earthquake storm" hypothesis — temporally clustered large events along a fault system releasing accumulated strain in sequence. To be used as a **hypothesis to be tested**, not as an established chronology; see §2.2.3 for the archaeoseismological quality filter.
5. **Powell, W., Frachetti, M., Pulak, C., Bankoff, H.A., Barjamovic, G., Johnson, M., Mathur, R., Yener, K.A. & Price, M. 2022.** "Tin from Uluburun shipwreck shows small-scale commodity exchange fueled continental tin supply across Late Bronze Age Eurasia." *Science Advances* 8(48): eabq3766. DOI `10.1126/sciadv.abq3766`. Tin-isotope and trace-element provenancing of the Uluburun tin, indicating supply from geographically remote sources including Central Asian and Anatolian deposits, distributed through small-scale exchange rather than a single controlled artery. **This result is load-bearing for the entire study** and cuts both ways: it lengthens the tin supply chain (raising exposure) while suggesting it was polycentric at the extraction end (lowering single-source risk). Phase 3 must model both properties.

A published response contesting aspects of Powell et al. 2022 exists and must be read and cited alongside it; the protocol treats tin provenance as **contested**, and propagates that contestation as a prior over source configurations rather than selecting a winner.

Supporting positions to be integrated but not treated as anchors: Weiberg & Finné on Peloponnesian resilience and persistence under climate change (*World Archaeology*, 2018, DOI `10.1080/00438243.2018.1515035`); Finné et al. on Mediterranean Holocene hydroclimate synthesis (*The Holocene*, 2019, DOI `10.1177/0959683619826634`); and the Aegean hydroclimate synthesis of Jacobson, Seguin & Finné (*The Holocene*, 2024, DOI `10.1177/09596836241275028`), which is the current statement of how divergent the regional records actually are.

## 1.4 Competing hypotheses and their discriminating predictions

The study is a **model comparison**, so the rival models must be stated in advance with predictions that differ.

| ID | Model | Core statement | Prediction that separates it from the others |
| --- | --- | --- | --- |
| **H₀** | Null / stochastic | Failures are independent draws with a common rate; apparent pattern is chronological imprecision plus excavation bias | Failure times, once corrected for dating uncertainty and excavation intensity, are indistinguishable from a homogeneous process; no spatial or topological structure survives |
| **H₁** | Exogenous shock only | Climate and seismicity fully determine failure; topology is inert | Failure severity is fully explained by local hydroclimate anomaly and seismic exposure; network centrality adds no predictive power |
| **H₂** | Invasion / migration primary | An external agent drives failure | Destruction dates cluster along a coherent migration front; attestations of intrusive material culture **precede** local decline indicators |
| **H₃** | Endogenous fragility only | The network would have failed under generic stress; the specific shock is incidental | Failure pattern is reproduced by *random* perturbation of the empirical topology as well as by the historical shock schedule |
| **H₄** | **Shock × brittle topology (study hypothesis)** | Exogenous shocks of historically plausible magnitude produce systemic collapse **only** when applied to the empirical topology, and not when applied to counterfactual topologies of equal size and equal total trade volume | (a) Interaction term dominates main effects; (b) failure order follows network paths with measurable lag; (c) the same shock applied to degree-randomized or redundancy-augmented null topologies fails to cascade; (d) **survivors are correctly predicted by low dependency and high substitution capacity** |

Prediction **(d)** deserves emphasis. The literature is saturated with explanations of why centres fell; comparatively few explain why Egypt contracted without collapsing, why several Cypriot and Phoenician coastal centres show substantial continuity, and why Assyria's trajectory differs. A model that predicts everyone's failure equally well predicts nothing. **Differential survival is the primary discriminating outcome of this study.**

## 1.5 Phase 1 deliverables

- **D1.1** Annotated historiographical review, ~12,000 words, organized by causal topology rather than chronology.
- **D1.2** The claim→operator translation table (§1.2) in machine-readable form, each row bound to the Phase 3 module that implements it.
- **D1.3** Pre-registered hypothesis set H₀–H₄ with quantitative discriminating predictions and prior model probabilities elicited from the advisory panel by structured expert elicitation (Cooke's classical method, with calibration questions on independently verifiable archaeological facts to weight each expert).
- **D1.4** A register of **inert claims** — assertions in the literature that cannot be made to generate a differential prediction — with reasons. This is published, not suppressed.

---

# Phase 2 — Data Architecture and Multiproxy Evidence Normalization

**Objective:** construct a single, version-controlled, uncertainty-bearing evidence base from datasets that differ in physical medium, temporal resolution, spatial support, and error structure — without manufacturing agreement between them.

**Governing principle:** proxies are *never* aligned by assumption. Every correlation between two proxy streams must survive a test in which the alignment itself is treated as an unknown with a prior.

## 2.1 The historical universe

### 2.1.1 Spatial definition

The universe is defined by **participation in the exchange system**, not by modern geography. A site enters the universe if it satisfies at least one of:

- documented possession of imported goods traceable to another region within the universe (ceramics, metals, ivory, glass, faience, resins);
- attestation in an inter-polity textual corpus (Amarna, Hittite state archives, Ugaritic correspondence, Egyptian administrative and monumental texts, Linear B where relevant to commodity flow);
- production or transhipment of a commodity attested in circulation elsewhere in the universe.

Core cultural spheres, as named in the brief and retained: Mycenaean Greece and the Aegean islands; Crete; the Hittite empire and its Anatolian and North Syrian dependencies; Cyprus (Alashiya); the Levantine coast and interior (Ugarit, Amurru, Canaanite city-states); Egypt.

**Mandatory extensions** — without these the tin question cannot be posed:

- **Mesopotamia and the Middle Euphrates**, as the overland conduit for eastern tin (Assyria, Babylonia, Mari's successors, Emar).
- **Central Asian and Anatolian tin sources** implicated by tin-isotope provenancing.
- **Central Mediterranean nodes** (Sardinia, Sicily, southern Italy) where oxhide ingots and Aegean-type material occur, as an outlet/alternative circuit.

### 2.1.2 Temporal definition

| Window | Interval | Role |
| --- | --- | --- |
| Baseline | 1400–1250 BCE | Characterizes the network at maturity; supplies the "normal operating" distribution against which anomalies are defined |
| Transition | 1250–1100 BCE | The study window |
| Aftermath | 1100–1000 BCE | Tests recovery, substitution (notably the ferrous transition), and reconfiguration; supplies the differential-survival outcome |

The baseline window is not optional. A brittleness claim is meaningless without a prior state to be brittle relative to.

### 2.1.3 Evidence tiers

Every datum carries a tier label, and tier is a covariate in every downstream model.

| Tier | Definition | Example | Treatment |
| --- | --- | --- | --- |
| **A** | Directly measured, independently replicable, with published analytical uncertainty | Isotope ratio with stated 2σ; radiocarbon determination with lab code and δ¹³C | Full weight |
| **B** | Directly observed but interpretation-dependent | Stratigraphic destruction layer with published section drawing | Full weight on observation, modelled uncertainty on interpretation |
| **C** | Reported in primary excavation literature without full supporting documentation | Destruction asserted in a preliminary report | Down-weighted; flagged for Millek-protocol re-audit |
| **D** | Textual attestation | Ugaritic letter; Amarna letter | Treated as evidence of *claims made by ancient actors*, never directly as event data (§2.2.5, §2.5.3) |
| **E** | Synthetic or secondary | Figure redrawn from a synthesis | Excluded from analysis; permitted only in narrative |

## 2.2 Data streams and their acceptance criteria

### 2.2.1 Stream P — Palynological and terrestrial hydroclimate

`[DATA REQUIREMENT]` Acceptance criteria for a core to enter the analysis:

- Published age–depth model built from **≥ 5 dated horizons** within or bracketing 1600–900 BCE, with a stated age-model method (Bacon, Bchron, clam) and a published uncertainty envelope. Cores with linear interpolation between two dates are excluded.
- Sampling resolution equivalent to **≤ 50 years per sample** across the transition window.
- Published raw counts or percentages by taxon, not only an interpretive curve.
- Explicit treatment of the anthropogenic-signal problem: arboreal-pollen decline can indicate aridity *or* clearance *or* the abandonment of orchard husbandry. Cores lacking a stated discrimination strategy are admitted only with an inflated interpretive-uncertainty term.

Confirmed candidate cores: Sea of Galilee (Langgut, Finkelstein & Litt 2013); Larnaca Salt Lake, Cyprus (Kaniewski et al. 2013). The Aegean and Anatolian coverage must be assembled from the syntheses of Finné et al. 2019 and Jacobson, Seguin & Finné 2024 and each constituent record audited individually against the criteria above.

**Mandatory heterogeneity test.** The Aegean hydroclimate synthesis literature reports *divergent* regional patterns. The protocol therefore does not fit a single "Eastern Mediterranean drought" field. It estimates a **spatially varying hydroclimate anomaly field** with explicit between-record disagreement, and carries that disagreement into the network model as parameter uncertainty. A drought signal that exists only after averaging away regional divergence is treated as an artefact of averaging.

### 2.2.2 Stream S — Speleothem, marine, and independent physical climate proxies

Included to break the circularity risk in Stream P (pollen responds to human land use as well as climate). Requirements: U–Th chronology with published errors; δ¹⁸O and δ¹³C series; stated hydrological interpretation for the specific cave system. Marine records per Drake 2012 supply an additional independent axis. Agreement between P, S, and marine streams is a *finding*; disagreement is *data*, not noise to be smoothed.

### 2.2.3 Stream E — Archaeoseismological

This is the weakest-evidenced and most over-interpreted stream in the collapse literature, and the protocol treats it with corresponding severity.

Every candidate seismic event must be scored on a formal **archaeoseismic quality index** derived from the established criteria literature (Stiros 1996 in Stiros & Jones, eds., *Archaeoseismology*, Fitch Laboratory Occasional Paper 7; and subsequent methodological treatments including Sintubin's work on the identification problem and Kázmér's damage typology):

| Criterion | Score 0 | Score 1 | Score 2 |
| --- | --- | --- | --- |
| Damage typology | Fire/collapse only | Directional wall collapse | Diagnostic: rotated/displaced masonry, tilted walls, chevron fractures, ground-rupture offset |
| Site-effect control | None | Qualitative | Modelled local site amplification / geotechnical assessment |
| Independent geological corroboration | None | Regional palaeoseismic literature | Dated palaeoseismic trench or offset feature within the region |
| Chronological control on the damage | Ceramic phase only | One ¹⁴C date | Bayesian model with multiple dates |
| Alternative-cause exclusion | Not addressed | Discussed | Systematically excluded (siege, subsidence, structural failure, post-depositional) |

**Admission threshold: total ≥ 6 of 10, with a non-zero score on damage typology and on alternative-cause exclusion.** Events below threshold are retained in a shadow register and used only in sensitivity analysis. The Nur & Cline earthquake-storm hypothesis is then tested as a *point-process hypothesis*: does the admitted event set exhibit temporal clustering beyond a homogeneous Poisson process, given the region's long-term seismicity rate? This is a Ripley's-K-in-time / conditional-intensity test with an explicit null, not a narrative assessment.

### 2.2.4 Stream M — Archaeometallurgical and provenance

The purpose of this stream is to reconstruct **flow**, not merely presence.

**Lead-isotope analysis (LIA) of copper.** The reference framework is Stos-Gale et al. 1997, "Lead isotope characteristics of the Cyprus copper ore deposits applied to provenance studies of copper oxhide ingots," *Archaeometry* 39(1), DOI `10.1111/j.1475-4754.1997.tb00792.x`, together with the OXALID reference database. The protocol adopts LIA **with the standard methodological cautions treated as first-class model components, not footnotes**:

- ore-field isotopic fields overlap, so provenance is a **posterior distribution over sources**, never a point assignment;
- recycling and mixing of metal from multiple sources shift isotopic composition along mixing lines, and mixing must be modelled explicitly (a two- or three-endmember mixing model with unknown proportions);
- reference-database coverage is incomplete, so an "unmatched" result is evidence of a gap in the reference set as much as of an exotic source;
- trace-element and, where available, copper-isotope data are required as an independent check before any provenance claim is admitted.

**Tin.** Tin-isotope and trace-element provenancing per Powell et al. 2022, with the published critical response carried as an alternative hypothesis. Because tin has no significant Eastern Mediterranean sources, its provenance directly determines the length and vulnerability of the most critical supply chain in the system.

**Uluburun as calibration, not as universe.** The Uluburun wreck (ca. late 14th c. BCE; ~10 tonnes of copper in oxhide and other ingot forms, ~1 tonne of tin — a ratio of approximately 10:1, matching the alloy proportion of standard tin bronze) is a single cargo and cannot be treated as a sample of the trade. It is used for three specific purposes and no others: (i) to calibrate the copper:tin ratio moving as a bundled consignment; (ii) to establish the compositional diversity of a single shipment; (iii) as a **taphonomic anchor** — a snapshot of goods in transit, uncontaminated by the deposition biases of settlement contexts.

`[DATA REQUIREMENT]` Systematic compilation of all published oxhide-ingot finds with LIA, all published tin finds with isotopic data, and all published Cypriot slag and smelting-site data within the temporal universe, each with lab, method, uncertainty, and reference-database version recorded.

### 2.2.5 Stream T — Textual

The three principal corpora — the Amarna correspondence (EA 1–382, standard edition: Moran, W.L. 1992, *The Amarna Letters*, Johns Hopkins University Press), the Hittite state archives from Boğazköy/Ḫattuša, and the Ugaritic and Akkadian correspondence from Ras Shamra — supply the political-dependency layer and the only direct evidence of contemporaneous perception of stress (grain shortages, requests for shipments, reports of hostile ships).

**Handling rule.** Texts are Tier D. A letter reporting a grain shortage is evidence that a shortage was *asserted by an interested party in a specific rhetorical context*, and is coded as such: `{sender, recipient, date-range, commodity, direction of request, rhetorical register, corroboration status}`. It is never entered as a measured famine. Diplomatic hyperbole, negotiating posture, and formulaic language are coded explicitly.

The late Ugaritic correspondence relating to the city's final phase — including the well-known reports of enemy ships and of grain shipments — is central and must be handled by a specialist philologist working from the published editions, with the *dating and archaeological context of the tablets themselves* treated as an open question. Several of the most-quoted texts have contested find-contexts and contested dates; the protocol requires each cited tablet to carry its siglum, publication reference, and a stated confidence in its date and context. **No text is quoted in the study from a secondary synthesis.**

## 2.3 Chronological normalization

The single hardest problem in the design. Approach: **do not attempt to place events on an absolute calendar; estimate the joint posterior over event orderings and intervals.**

### 2.3.1 Bayesian chronological modelling

All ¹⁴C determinations are modelled in OxCal (or an equivalent implementation) using IntCal20 with:

- `Sequence` / `Phase` / `Boundary` structures encoding stratigraphic relations at each site;
- `Outlier_Model` (general and charcoal outlier models) applied to every determination, with the charcoal model mandatory for structural timber and unidentified charcoal, to absorb old-wood offsets;
- a **regional offset parameter** `Δ_R` estimated jointly, with a prior informed by the demonstrated Eastern Mediterranean growing-season and regional offsets (Manning et al. 2018, *PNAS*; Manning et al. 2020, *Science Advances*, DOI `10.1126/sciadv.aaz1096`; Manning et al. 2020, *Scientific Reports*, DOI `10.1038/s41598-020-69287-2`);
- ceramic synchronisms encoded as **informative priors on phase boundaries with explicit uncertainty**, never as fixed constraints;
- `KDE_Plot` for the distribution of destruction events, so that apparent clustering can be distinguished from the sum of individually wide calibrated distributions.

### 2.3.2 The ordering test — the actual inferential workhorse

Causal claims here are claims about order and lag. The protocol therefore computes, for every pair of events (A, B), the posterior probability

> `P(t_A < t_B | D)` and the posterior distribution of the lag `Δ_AB = t_B − t_A`

directly from the joint Bayesian chronology, using difference queries between modelled parameters. Reporting convention: **an ordering claim is admissible only where `P(t_A < t_B) ≥ 0.90`.** Pairs below that threshold are reported as chronologically unresolved. This will disqualify a large fraction of the sequences the narrative literature relies on, and that outcome is itself a publishable finding.

### 2.3.3 Coping with irreducible imprecision

Where dating cannot resolve order, three fallbacks:

1. **Coarsening.** Aggregate to 25-year bins and test hypotheses at that resolution, accepting the loss of power rather than manufacturing precision.
2. **Wiggle-matching.** Where sequences of dated samples exist (dendrochronological sequences, stratified short-lived samples), wiggle-matching against the calibration curve can achieve decadal resolution. Prioritize excavation and sampling programmes that would yield such sequences (§5.4).
3. **Order-free tests.** Some predictions do not require ordering. The prediction that failure severity correlates with network centrality after controlling for exposure is a cross-sectional test, and survives total chronological failure. **The design deliberately front-loads such tests** so that the study still discriminates between H₁, H₃, and H₄ even in the worst chronological case.

## 2.4 The destruction-horizon re-audit (Millek protocol)

Before any site-level "failure" enters the model, its destruction claim is re-derived from primary excavation documentation against a fixed rubric:

- Is there a published section drawing or plan showing the destruction deposit?
- Is burning attested, and is its extent architectural or localized (a kiln, a hearth, an industrial installation)?
- Are there de-facto refuse assemblages consistent with sudden abandonment, or is the assemblage consistent with planned departure?
- Are there weapons, unburied human remains, or other trauma indicators — and are these published or asserted?
- What is the independent dating of the destruction deposit, as opposed to dating by assumed correlation with the collapse horizon?
- Is there evidence of immediate reoccupation, which materially changes the meaning of the event?

Each site receives a graded outcome — `destroyed (violent)`, `destroyed (cause indeterminate)`, `burnt (localized/non-destructive)`, `abandoned (gradual)`, `abandoned (rapid, non-violent)`, `continuity`, `insufficient documentation` — with a confidence score. **Outcome is a categorical response variable with measurement error, not a binary.** Circular dating (a layer dated to 1200 BCE *because* it is a destruction layer) is flagged and the site is excluded from chronological tests while remaining in cross-sectional tests.

## 2.5 Missing data, survivorship, and the selection problem

Four distinct biases, each with a distinct correction. Conflating them is the standard error in this literature.

### 2.5.1 Excavation-intensity bias

Large, rich, historically famous sites are excavated more, published more, and dated more. Correction: construct an **excavation-intensity covariate** for every site — excavated area, number of seasons, publication volume, number of ¹⁴C dates — and include it in every model. Additionally, use **survey data** (regional field survey, where systematic and published) as a second, differently-biased sampling frame. Where excavation-based and survey-based estimates of settlement change disagree, the disagreement bounds the bias.

### 2.5.2 Destruction-preservation bias

Catastrophic burning preserves floor assemblages and bakes clay tablets; gradual abandonment leaves swept floors and a thin, ambiguous record. The archaeological record therefore **systematically over-represents violent endings**, which structurally favours H₂. Correction: model the probability of detection `P(detect | ending type)` explicitly and apply inverse-probability weighting; report all key results both weighted and unweighted.

### 2.5.3 The archive-survival paradox

This deserves separate treatment because it is the most seductive trap in the corpus. **The Ugaritic letters describing the crisis survive because Ugarit burned.** The textual record of the collapse is conditioned on the collapse. Selecting on the outcome and then reading the texts as an unbiased account of causes is a textbook collider-stratification error. Correction: the textual stream may be used to *generate* and *characterize* hypotheses, and to establish that certain conditions were perceived by contemporaries, but it may **not** be used as the outcome variable in any test of causal structure. Where a text is used quantitatively, the analysis must include sites in the same tier that produced no archive, coded as missing-not-at-random.

### 2.5.4 Chronological-resolution bias

Better-dated sites are better-dated because they are better-funded, which correlates with size and importance, which correlates with network centrality. Naive analysis will therefore find that central sites have sharper failure signatures **as an artefact of dating quality**. Correction: dating quality enters as a covariate; and a **matched analysis** is run in which each high-centrality site is matched to a low-centrality site of comparable dating quality.

### 2.5.5 The causal firewall

No causal claim is admitted unless it clears all five gates:

| Gate | Requirement |
| --- | --- |
| **Temporal** | Cause precedes effect at `P ≥ 0.90` in the Bayesian chronology |
| **Dose–response** | Effect magnitude scales monotonically with cause magnitude across the sample |
| **Spatial coherence** | The spatial gradient of the effect matches the spatial gradient of the proposed cause, and does not match the gradient of the leading confounders |
| **Mechanism specificity** | The proposed mechanism predicts a *distinctive* signature that generic stress does not |
| **Negative control** | There exist cases exposed to the cause that did **not** exhibit the effect, and the model correctly predicts which |

The negative-control gate is the one this literature most often fails. Egypt, several Cypriot centres, and the northern Levantine coastal cities experienced comparable environmental conditions with materially different outcomes. A model that cannot reproduce that differential is rejected regardless of how well it reproduces the failures.

## 2.6 Data infrastructure

- **Storage:** relational schema (PostgreSQL + PostGIS) with entities `Site`, `Context`, `Sample`, `Determination`, `Artefact`, `AnalyticalResult`, `TextualAttestation`, `NetworkEdgeEvidence`, `SourceReference`. Every row references a `SourceReference` and carries a `Tier`.
- **Uncertainty representation:** no scalar values for uncertain quantities. Dates are posterior distributions; provenance is a distribution over sources; edge weights are distributions. The database stores distributions (parametric where adequate, sampled where not).
- **Provenance and versioning:** Git-tracked ETL; every analytical figure regenerable from raw inputs by a single command; data releases DOI-minted through Zenodo or the ADS.
- **Standards:** CIDOC CRM alignment for interoperability; ISO 8601 with explicit BCE handling; coordinates in WGS84 with published precision, and **deliberate coordinate fuzzing for sites at looting risk**.
- **Openness:** all derived data and code released under CC-BY / MIT at publication; third-party data released only where licensing permits, with acquisition instructions otherwise.

---

# Phase 3 — Systems Modelling and Network Vulnerability Testing

**Objective:** construct a spatially and temporally explicit multilayer model of the Late Bronze Age exchange system, subject it to historically constrained perturbations, and identify the conditions under which localized failure becomes systemic.

**Design commitment:** the model is built to be *broken*, and to be broken in ways that could have failed to reproduce the observed record. Every result is reported against degree-preserving, spatial, and volume-matched null models. A cascade that also occurs in the null models is not evidence for H₄.

## 3.1 Formal specification of the network

### 3.1.1 The multilayer object

The system is represented as a temporal, weighted, directed multiplex

```
M(t) = ( V, {E^(α)(t)}_{α ∈ L}, {W^(α)(t)}_{α ∈ L}, D(t) )
```

| Symbol | Definition |
| --- | --- |
| `V` | Node set: polities and exchange places, `|V| ≈ 120–250` after inclusion filtering |
| `L` | Layer set: `{Cu, Sn, Au/Ag, grain, prestige/finished goods, political-dependency, information}` |
| `E^(α)(t)` | Directed edge set in layer `α` at time `t` |
| `W^(α)(t)` | Edge weights in layer `α`: expected commodity flow, or dependency intensity for the political layer |
| `D(t)` | Inter-layer dependency links: node `i`'s function in layer `α` conditional on its state in layer `β` |

Separating commodities into layers is not cosmetic. Copper and tin have different source geographies, different substitutability, and different route structures; treating "trade" as one graph destroys precisely the asymmetry the study is testing.

### 3.1.2 Nodes

Node attributes, each carried as a distribution rather than a scalar:

| Attribute | Symbol | Estimation basis |
| --- | --- | --- |
| Location | `x_i` | Excavated coordinates; WGS84 |
| Settlement extent | `a_i(t)` | Published site-size estimates by phase |
| Administrative complexity | `c_i(t)` | Composite index: presence of archives, sealing practice, standardized weights, storage architecture, craft-specialization indicators |
| Agricultural capacity | `π_i(t)` | Catchment-based estimate from soil/terrain within a cost-distance radius, scaled by the hydroclimate field |
| Storage buffer | `σ_i` | Excavated storage volume (magazines, pithoi, silos) converted to person-months of supply, with a wide uncertainty band |
| Metallurgical dependency | `μ_i` | Bronze consumption inferred from assemblage; local ore access (binary/graded) |
| Political dependency | `ρ_i` | Vassalage and tribute obligations from the textual corpora |

Named exemplars in the brief — Ḫattuša, Mycenae, Ugarit, Pi-Ramesses — enter as ordinary nodes. **No node is privileged a priori.** Their prominence in the narrative literature is itself a bias to be controlled: prominence correlates with excavation intensity (§2.5.1).

### 3.1.3 Edges

An edge `(i → j)` in layer `α` requires positive evidence of directional flow. Three independent edge-evidence classes, combined by evidence synthesis rather than by union:

1. **Material provenance.** Object of source `s` found at `j`, with `s` attributable to `i`'s catchment. Contributes a likelihood over the edge's existence and volume, discounted by the provenance posterior (§2.2.4) and by the number of plausible intermediaries.
2. **Textual attestation.** Shipment, tribute, gift-exchange, or dependency recorded in a Tier-D source. Contributes to the political-dependency layer at full strength and to commodity layers only weakly, because diplomatic gift-exchange is a poor proxy for bulk volume.
3. **Route feasibility.** A gravity/cost-distance prior on the existence of an edge, from least-cost-path analysis over sea (accounting for prevailing winds, currents, seasonality, and the coastal-tramping character of Bronze Age sailing) and land (terrain cost surfaces, known route corridors, pass accessibility).

Combined edge-existence probability, with `θ` a learned weighting over evidence classes:

```
P(e_ij^(α) = 1 | evidence) ∝ P_prov(·) · P_text(·) · P_route(·)^θ
```

Edges are directed and, in general, asymmetric: `w_ij ≠ w_ji`.

### 3.1.4 Weights

Two distinct weight semantics, kept separate:

- **Volume weight** `w_ij^(α)` — estimated flow of commodity `α`, in mass units where possible, calibrated against the few quantifiable anchors (cargo assemblages such as Uluburun; administrative texts recording quantities; ingot mass distributions). Reported as an order-of-magnitude posterior, never as a point figure.
- **Dependency weight** `d_ij^(α)` — the share of `j`'s consumption of `α` that transits `i`:

```
d_ij^(α) = w_ij^(α) / Σ_k w_kj^(α)
```

`d` is the quantity that matters for cascade dynamics. A node may carry small absolute volume and still be structurally critical if it is a sole supplier.

**The Amarna dependency layer.** Following and extending Cline & Cline 2015, the diplomatic corpus is coded into a directed graph of correspondence and obligation. Coding is done in duplicate by independent coders with inter-coder reliability reported (Krippendorff's α, threshold ≥ 0.80 for admission). Critically, the Amarna archive dates predominantly to the **mid-14th century**, roughly a century before the transition window; it is therefore used to parameterize *baseline* political topology and the persistence of dependency structures, with an explicit decay/uncertainty model for extrapolation forward. Using Amarna directly as a 1200 BCE snapshot would be an anachronism, and the protocol forbids it.

## 3.2 Network metrics

Standard definitions, stated explicitly so that results are reproducible.

### 3.2.1 Centrality

Weighted degree (strength):

```
s_i^(α) = Σ_j w_ij^(α)
```

Betweenness on the cost-weighted graph, where `σ_st` is the number of shortest paths from `s` to `t` and `σ_st(i)` the number passing through `i`:

```
B_i = Σ_{s ≠ i ≠ t} σ_st(i) / σ_st
```

Eigenvector centrality `A x = λ_max x`, and — more appropriate for a directed dependency graph — **Katz** and **PageRank** variants, since eigenvector centrality is ill-behaved on directed acyclic substructures.

A purpose-built measure for this problem, **Supply Criticality**, capturing the extent to which a node is the sole conduit for a critical commodity to others:

```
SC_i^(α) = Σ_{j ≠ i} d_ij^(α) · ( 1 − r_j^(α) )
```

where `r_j^(α) ∈ [0,1]` is `j`'s substitution capacity for commodity `α` (local sourcing, stock, alternative supplier). A node with high `SC` for tin is a single point of failure for bronze production downstream.

### 3.2.2 Structural robustness of the intact network

**Percolation / Molloy–Reed.** A giant connected component exists in a configuration-model graph iff

```
κ ≡ ⟨k²⟩ / ⟨k⟩ > 2
```

and under random removal of a fraction `f` of nodes the giant component vanishes at

```
f_c = 1 − 1 / (κ₀ − 1),        κ₀ = ⟨k²⟩₀ / ⟨k⟩₀
```

(Cohen, Erez, ben-Avraham & Havlin 2000, "Resilience of the Internet to random breakdowns," *Physical Review Letters* 85(21): 4626–4628, DOI `10.1103/PhysRevLett.85.4626`.)

For heavy-tailed degree distributions with exponent `2 < γ ≤ 3`, `⟨k²⟩` diverges, `κ₀ → ∞`, and `f_c → 1`: the network is extremely robust to *random* failure while remaining acutely vulnerable to *targeted* removal of hubs. This **robust-yet-fragile** asymmetry is the precise formal content of the "hyper-connected but brittle" thesis, and measuring `γ` for the reconstructed network is therefore a primary Phase 3 result. It must be estimated with the maximum-likelihood plus goodness-of-fit procedure of Clauset, Shalizi & Newman (2009, *SIAM Review* 51(4): 661–703) and tested against log-normal and stretched-exponential alternatives — a heavy tail is a hypothesis here, not an assumption, and the sample size is small enough that naive log-log fitting would be misleading.

**Global efficiency** (Latora & Marchiori 2001, *Physical Review Letters* 87: 198701):

```
E_glob = 1 / (N(N−1)) · Σ_{i ≠ j} 1 / d_ij
```

**Redundancy.** By Menger's theorem, the number of edge-disjoint paths between `i` and `j` equals the minimum edge cut. Define pairwise redundancy `R_ij` as that count, and network redundancy as the mean over pairs weighted by dependency. Low `R` under high `E_glob` is the structural fingerprint of over-optimization.

**Robustness index** (Schneider, Moreira, Andrade, Havlin & Herrmann 2011, *PNAS* 108(10): 3838–3841):

```
R = (1/N) · Σ_{q=1}^{N} S(q)
```

where `S(q)` is the fraction of nodes in the largest connected component after removal of `q` nodes under a specified attack strategy. `R ∈ (0, 0.5]`, with 0.5 the theoretical maximum. Define the study's headline **Brittleness Index**:

```
B = 1 − 2R  ∈ [0, 1)
```

`B` is computed under (i) random removal, (ii) degree-targeted removal, (iii) betweenness-targeted removal, and (iv) the **historically constrained** removal schedule derived from the hydroclimate and seismic fields. The gap between (i) and (iv) is a direct measure of how much the specific historical shock exploited the specific network structure.

### 3.2.3 Cascade dynamics

**Load-redistribution model** (Motter & Lai 2002, "Cascade-based attacks on complex networks," *Physical Review E* 66: 065102(R), DOI `10.1103/PhysRevE.66.065102`). Each node carries load `L_i` (initialized to betweenness) and capacity proportional to initial load:

```
C_i = (1 + α) · L_i(0),        α ≥ 0 the tolerance parameter
```

A node fails at step `τ` if `L_i(τ) > C_i`; load then redistributes over remaining shortest paths, potentially triggering further failures. Iterate to a fixed point; measure the relative size of the surviving largest component `G = N'/N`.

**Interpretation of `α` for this system.** `α` is the fraction of spare capacity — the slack a polity holds above ordinary operating throughput. It is *not* free: it is granary volume, standing surplus, redundant shipping, alternative suppliers. A command economy optimizing for extraction and display consumption drives `α` down. **The over-optimization hypothesis is, in this formalism, the claim that the LBA system operated at low `α`.** `α` is therefore estimated empirically from excavated storage capacity relative to estimated consumption (§3.1.2, `σ_i`), rather than tuned, and the estimate is reported with its uncertainty as a headline result.

**Interdependent-network cascade** (Buldyrev, Parshani, Paul, Stanley & Havlin 2010, "Catastrophic cascade of failures in interdependent networks," *Nature* 464: 1025–1028, DOI `10.1038/nature08932`). Where a node's function in one layer depends on its function in another — a palace cannot administer grain redistribution if its metallurgical and prestige economy has failed, and cannot sustain a metallurgical economy without agricultural surplus — the iterative failure process between coupled layers produces a **first-order (discontinuous) percolation transition**, in contrast to the continuous transition of a single network. Interdependence converts graceful degradation into abrupt collapse.

**This is the sharpest available signature.** Under H₁ (exogenous shock only), decline should be roughly proportional to shock magnitude. Under H₄ with interdependence, there should be a threshold below which the system absorbs the shock and above which it disintegrates. Discriminating a first-order from a second-order transition in the *modelled* system is straightforward; the empirical counterpart is the shape of the aggregate decline curve reconstructed in Phase 2, tested for discontinuity against a smooth alternative.

## 3.3 The tin bottleneck — commodity-flow layer

The metals system is modelled explicitly because it is where the argument is most testable.

**Production constraint.** Tin bronze at the standard ~10% Sn requires inputs in near-fixed proportion, i.e. a Leontief technology with negligible short-run substitution:

```
b_i = min( cu_i / (1 − θ) , sn_i / θ ),        θ ≈ 0.10
```

Because copper was available within the Eastern Mediterranean (Cypriot deposits above all, with Levantine and Sinai sources) while tin had **no abundant, securely exploited source in the Eastern Mediterranean at the scale of demand** — the small Anatolian deposits notwithstanding — and travelled great distances from Central Asian, Anatolian, and possibly European deposits, the binding term is overwhelmingly `sn_i / θ`. The elasticity of bronze output with respect to tin availability is ≈ 1 in the binding regime and ≈ 0 with respect to copper.

Consequences the model must reproduce:

- **Asymmetric criticality.** A given proportional disruption to tin flow should produce a far larger reduction in bronze output than the same proportional disruption to copper. Archaeologically, this predicts a *specific and testable* signature: declining Sn content in bronzes, rising rates of recycling (visible in trace-element and lead-isotope mixing signatures), and increasing use of unalloyed copper or low-tin bronze, appearing **before** rather than after settlement failure at affected nodes.
- **Path length as exposure.** The Powell et al. 2022 result lengthens the tin chain and adds intermediary nodes outside the Eastern Mediterranean. Each intermediary is an additional failure point. This is captured by modelling exposure as a function of path length and per-hop reliability, `Π_hops p_survive`.
- **Polycentricity as mitigation.** The same result indicates multiple extraction sources feeding the system via small-scale exchange, which *reduces* source concentration risk. **The two effects act in opposite directions and the net effect is an empirical question the model must answer, not assume.** This is the single most important modelling result the study can produce.
- **Substitution.** The eventual ferrous transition is a substitution response, not merely a technological succession. `r_j` (substitution capacity) becomes time-varying, and the aftermath window (1100–1000 BCE) tests whether the network reconfigured around a commodity with ubiquitous sources — which is, structurally, a shift from a long-chain, high-criticality input to a short-chain, low-criticality one.

## 3.4 Perturbation operators

Each operator is calibrated to the empirical fields of Phase 2, and each has a "historical" and a "counterfactual" mode.

| ID | Operator | Empirical calibration | Free parameters |
| --- | --- | --- | --- |
| **O1** | Hydroclimate stress | `π_i → (1 − δ_i(t)) π_i`, `δ_i` from the spatially varying anomaly field (§2.2.1) with its between-record disagreement | Severity scaling; lag from anomaly to yield loss |
| **O2** | Seismic node damage | Node capacity and administrative function degraded at sites in the admitted seismic register (§2.2.3), on the estimated event chronology | Damage-to-function mapping; recovery rate |
| **O3** | Edge severance | Removal of maritime/overland edges: (a) random, (b) targeted by weight, (c) targeted by betweenness, (d) geographically clustered | Fraction removed; duration |
| **O4** | Node deletion | Removal of nodes: random, degree-targeted, betweenness-targeted, or on the historically attested destruction schedule from §2.4 | Fraction; schedule |
| **O5** | Demand shock | Reduction in elite prestige-goods demand, modelling loss of legitimacy expenditure | Magnitude |
| **O6** | Endogenous mobility | Displaced population generated as a *function of model state*: `m_i(t) = f(unmet subsistence, failure of neighbours)`; displaced groups then act on the network as raiders/migrants | Threshold; mobility rate; predation intensity |

**O6 is the operationalization of the study's central claim.** In H₂ (invasion primary) the mobile actors are exogenous inputs. In H₄ they are *outputs* that then feed back. The two are formally distinguishable: under H₄, the model reproduces the observed pattern of intrusive material culture and raiding attestation **without** any exogenous injection of raiders, and predicts their timing and geography from prior stress. If an exogenous injection is required to fit the data, H₄'s strongest form is falsified.

## 3.5 Experimental matrix

Full factorial over shocks, network configurations, and parameters, run as a Monte Carlo ensemble sampling the uncertainty in every input.

| Factor | Levels |
| --- | --- |
| Shock set | none · O1 · O2 · O1+O2 · O1+O2+O3 · full (O1–O6) |
| Network | Empirical reconstruction · degree-preserving rewire · spatially constrained random · volume-matched random · **redundancy-augmented counterfactual** · **low-efficiency counterfactual** |
| Tolerance `α` | Empirical posterior · {0.05, 0.1, 0.2, 0.5, 1.0} |
| Tin configuration | Powell et al. polycentric · single-source concentrated · intermediate, weighted by the provenance-debate prior |
| Interdependence coupling `q` | 0 (independent layers) → 1 (full coupling), 11 levels |
| Substitution capacity `r` | Fixed low · fixed high · time-varying with the ferrous transition |

Ensemble size: ≥ 10⁴ realizations per cell, or until Monte Carlo standard error on the primary outcome falls below 1% of its range. Latin hypercube sampling over continuous parameters. Full seed and configuration logging; every reported figure regenerable.

### 3.5.1 Counterfactual networks — the decisive comparison

The **redundancy-augmented counterfactual** is the study's most important control. It holds constant the number of nodes, the total trade volume, and the geography, while adding alternative paths (raising `R`, lowering `E_glob` slightly). If the historical shock schedule collapses the empirical network but *not* the redundancy-augmented one, the brittleness claim is supported in the strongest available sense: the collapse is attributable to topology given the shock, and neither to the shock alone nor to topology alone.

## 3.6 Locating the tipping point

The brief's central question — the exact point at which localized failure becomes systemic — is answered as a **critical-phenomena measurement**, not as a narrative judgement.

**Order parameter.** Rather than the bare largest-component fraction, the protocol uses a functional outcome, the **system supply-satisfaction ratio**:

```
Ψ(f) = ( Σ_i  min( supply_i(f), demand_i ) ) / ( Σ_i demand_i )
```

evaluated on the bronze-production layer. `Ψ` measures whether the system is *doing its job*, which is the historically meaningful notion of collapse; largest-component fraction is reported alongside as the conventional comparator.

**Susceptibility.** With `n_s` the number of clusters of size `s` and the largest cluster excluded from the sums:

```
χ(f) = Σ'_s s² n_s / Σ'_s s n_s
```

`χ` peaks at the critical point. The location of that peak, `f_c`, is the tipping point.

**Order of the transition.** Discriminate first-order from second-order by (i) the presence of a discontinuity in `Ψ` in the infinite-size extrapolation, (ii) bimodality of the `Ψ` distribution across ensemble members near `f_c`, and (iii) hysteresis under a reverse sweep in which capacity is restored.

**Finite-size scaling.** `N ≈ 120–250` is small, so apparent sharpness may be a finite-size artefact. Run the model at scaled network sizes generated by the same generative process and fit

```
f_c(N) = f_c(∞) + a · N^(−1/ν)
```

reporting `f_c(∞)` and `ν`. **Any claim of a sharp transition unaccompanied by finite-size analysis is inadmissible.**

**Critical-slowing-down early warning.** Approaching a bifurcation, systems show rising autocorrelation, rising variance, and rising skewness in fluctuations (Scheffer et al. 2009, *Nature* 461: 53–59). In the model these are directly measurable. The corresponding **empirical** test is deliberately weaker and must be presented as exploratory: whether pre-collapse archaeological indicators (settlement-size variance, import-diversity variance, hoarding frequency, ceramic-assemblage heterogeneity) show rising variance and autocorrelation in the decades before failure. Archaeological time-series resolution is close to the limit of what this test needs, and a negative result would be uninformative — which must be stated when it is reported.

**Attribution decomposition.** Finally, decompose the systemic outcome into contributions from shock magnitude, topology, and their interaction using a Shapley-value attribution over the factorial design. H₄ predicts the interaction term carries the largest share. This converts "the shocks interacted with a brittle network" from a metaphor into a number with a confidence interval.

## 3.7 Model validation

A model that fits the collapse is worthless unless it could have failed to.

1. **Out-of-sample temporal validation.** Fit on 1400–1250 BCE (baseline dynamics only), predict 1250–1100 BCE. No collapse-window data touches the fitting stage.
2. **Spatial hold-out.** Withhold entire regions (e.g. Cyprus, or the southern Levant), fit on the remainder, predict the withheld region's pattern of failure and survival.
3. **Independent-event validation.** Apply the identical pipeline to the Theran eruption horizon, where an exogenous shock to an Aegean network is comparatively well characterized and where the Knappett–Rivers–Evans results provide a published benchmark. If the pipeline cannot reproduce known results there, it is not trusted here.
4. **Prediction of survival, not only failure.** Scored by balanced accuracy and by Matthews correlation coefficient across the failure/survival classification, because the classes are imbalanced and accuracy alone would be misleading.
5. **Adversarial fitting.** An independent team attempts to fit the same observations with H₁ and H₂ maximally favoured, with equal computational budget. Bayes factors are computed between the best H₄ model and the best adversarial model.
6. **Sensitivity and robustness.** Global sensitivity analysis (Sobol indices) over all parameters; results reported for the full posterior, not a maximum-likelihood point.
7. **Prior-sensitivity.** Every substantive conclusion re-run under the advisory panel's most sceptical elicited prior. Conclusions that do not survive are reported as prior-dependent.

## 3.8 Implementation

Python (`networkx` / `graph-tool` for graph operations, `numpy`/`scipy`, `pymc` or `Stan` for Bayesian components, `mesa` or a bespoke engine for the agent-based layer), `OxCal` for chronological modelling, `R` (`rcarbon`, `Bchron`) for radiocarbon summed-probability and KDE work, PostGIS for spatial operations. Containerized (Docker) with a pinned lockfile; the full analysis reproducible end-to-end by a single command; compute logged for carbon accounting.

---

# Phase 4 — Macro-Historical Impact, Brittleness, and Modern Parallels

**Objective:** convert the network results into a general account of how efficiency-seeking generates fragility, and establish — under strict conditions — what, if anything, transfers to modern systems.

**Standing warning.** This phase carries the highest risk of the entire project. The pull toward a satisfying contemporary moral is strong, the incentives to indulge it are strong, and the resulting literature is largely worthless. The protocol therefore imposes a **formal homology test** that must be passed before any parallel is asserted, and requires that disanalogies be published with equal prominence. If the homology test fails, Phase 4 reports that it fails. That is a legitimate and publishable outcome.

## 4.1 Operationalizing "brittleness"

Brittleness is not a mood. It is a measurable property of a system's response function, and the protocol defines it as a five-component vector so that no single number can hide a trade-off.

| Component | Symbol | Definition | Measured from |
| --- | --- | --- | --- |
| Structural redundancy deficit | `1 − R̄` | Mean edge-disjoint path count, normalized, dependency-weighted | Reconstructed topology |
| Buffer deficit | `1 − ᾱ` | Spare capacity relative to throughput | Excavated storage volume vs. estimated consumption |
| Input criticality | `SC` | Supply criticality on the binding commodity (tin) | Commodity-flow layer |
| Substitution rigidity | `1 − r̄` | Inability to substitute inputs or suppliers within the shock's timescale | Leontief production constraint; source geography |
| Coupling | `q` | Strength of inter-layer dependency | Multiplex dependency links |

The composite **Brittleness Index** `B = 1 − 2R` (§3.2.2) is the headline scalar; the vector is what is actually interpreted, because two systems can share a `B` for entirely different reasons and will fail differently.

### 4.1.1 The efficiency–resilience frontier

The central theoretical construct. Plot each network configuration in `(E_glob, R)` space. The hypothesis to be tested is that:

- the empirical LBA network sits at **high `E_glob`, low `R`** relative to degree-preserving and spatial null models — that is, it is *more efficient and less robust* than chance would produce; and
- the redundancy-augmented counterfactual (§3.5.1), which pays a modest efficiency cost for a large robustness gain, survives the historical shock schedule that destroys the empirical configuration.

If the empirical network is **not** unusually efficient relative to nulls, the over-optimization thesis is falsified at its root, and the study should say so plainly. This is a real risk: a network reconstructed from surviving imports and cost-distance priors may be biased *toward* apparent efficiency, because the evidence for a route is more likely to survive when the route was heavily used. That bias must be quantified by simulation before the frontier result is interpreted.

### 4.1.2 The mechanism of over-optimization in a palatial command economy

The formal argument, stated so that it can be checked against the data rather than merely asserted:

1. **Centralized redistribution suppresses redundancy.** A palatial economy that concentrates the collection, storage, and reallocation of surplus creates single points of administrative failure. When the palace ceases to function, the redistribution it performed does not degrade — it stops. Testable: the sharpest discontinuities in material culture should occur at sites with the highest administrative-complexity index `c_i`, and lesser settlements dependent on palatial redistribution should show failure lagging their palace by a short, measurable interval.
2. **Elite prestige demand rewards long chains.** Value accrues to the exotic. A system whose legitimacy expenditure depends on distant imports is structurally committed to long, thin supply chains — the precise configuration with the lowest per-hop survival probability.
3. **Specialization raises efficiency and lowers substitutability.** Regional specialization in production raises `E_glob` and lowers `r`.
4. **Buffers are politically expensive.** Stored surplus that is neither consumed nor displayed generates no legitimacy return. Under competitive display pressure, `α` is driven down. Testable: storage capacity relative to estimated catchment yield should *decline* through the thirteenth century at high-complexity sites — a genuinely surprising prediction that could straightforwardly fail.
5. **Coupling is a by-product of integration.** The same institutions manage metals, grain, and diplomacy, so their layers are strongly coupled — and per Buldyrev et al., strong coupling makes the transition discontinuous.

Point 4 is the sharpest empirical hook in Phase 4 and should be prioritized: it is a claim about excavated storage volumes over time, it is measurable, and it could easily come out the other way.

### 4.1.3 Differential survival — the explanatory payoff

The brittleness vector must **predict who survives**. Broadly, the expectation is that survival correlates with low coupling, high substitution capacity, short supply chains, and less palace-dependent economic organization. Egypt's contraction-without-collapse, the continuity visible at a number of Cypriot and northern Levantine coastal centres, and the differing trajectory of the Assyrian core are the test cases. The analysis is a classification problem with the brittleness vector as predictor, evaluated by cross-validated balanced accuracy, and reported with the confusion matrix — including, explicitly, the cases the model gets wrong.

If the model predicts collapse well and survival badly, the honest conclusion is that it has learned the *shock* and not the *structure*, and it should be reported that way.

## 4.2 The homology test for modern parallels

No parallel to modern supply chains is asserted unless the following gate is passed. The comparison is between the reconstructed LBA system and a specified modern system — the protocol requires that the modern comparator be **named and characterized in advance**, not left as "globalization."

| # | Dimension | LBA measurement | Required modern counterpart | Pass condition |
| --- | --- | --- | --- | --- |
| 1 | Degree-distribution class | `γ` from Clauset et al. MLE, with model comparison | Same estimator on the modern trade/supplier graph | Same distributional class, overlapping `γ` credible intervals |
| 2 | Critical-input concentration | `SC` for tin; source-geography concentration (HHI) | `SC` and HHI for the modern critical input | Same order of magnitude |
| 3 | Buffer-to-throughput ratio | `α` from storage vs. consumption | Days-of-inventory / strategic reserve coverage | Same order of magnitude |
| 4 | Substitution elasticity | Leontief rigidity of the alloy constraint | Short-run elasticity of substitution for the critical input | Both < 0.2 in the relevant horizon |
| 5 | Route redundancy | Edge-disjoint paths on the critical layer | Independent logistics corridors for the critical input | Comparable normalized `R` |
| 6 | Coupling across functional layers | `q` | Coupling between logistics, finance, energy, information | Comparable, or explicitly bounded |

**Scoring.** A parallel is asserted only where at least four of six dimensions pass and none fails catastrophically. Where fewer pass, the finding is reported as *structural difference*, which is equally informative and considerably rarer in the literature.

### 4.2.1 The disanalogy register — published, not buried

The following differences are large, and the protocol requires them to appear in the same section as any parallel, at comparable length:

- **Information velocity.** Bronze Age messages travelled at the speed of a ship or a donkey; disruption was detectable only after it had propagated. Modern systems have near-instant signalling, which enables both faster correction and faster contagion. The sign of this difference is genuinely ambiguous and must not be asserted.
- **Price signals and market clearing.** Palatial redistribution and gift-exchange are not price-clearing markets. Modern supply chains reallocate through prices, which is a powerful adaptive mechanism absent from the ancient case. This is the single largest disanalogy.
- **Capital and technological substitution.** Modern systems can build new capacity in months to years; a Bronze Age polity could not conjure a new tin source.
- **State capacity and deliberate policy.** Strategic reserves, industrial policy, and coordinated crisis response have no close ancient analogue.
- **Energy basis.** Solar-agricultural versus fossil/nuclear/renewable energy bases produce different constraint structures entirely.
- **Scale and demographic buffer.** Population sizes, urbanization rates, and mobility differ by orders of magnitude.
- **Data asymmetry.** Modern supply-chain data is dense, contemporaneous, and directly measured; LBA data is sparse, indirect, and centuries-averaged. Any quantitative comparison is a comparison between quantities of radically different evidential quality, and confidence intervals must reflect that rather than being presented on a common footing.

### 4.2.2 What actually transfers

If the homology test passes, the transferable content is **structural and conditional**, not predictive. Candidate propositions, each to be stated with the model evidence that supports it and the conditions under which it holds:

1. **Efficiency and robustness trade off, and the trade-off is invisible in normal operation.** A network optimized for throughput exhibits no distress signal while conditions remain in-distribution. The absence of failure is not evidence of robustness. Formally: `E_glob` and `R` are anti-correlated across the configuration ensemble, and the observable performance metrics of a high-`E`, low-`R` system are indistinguishable from those of a robust one until the shock arrives.
2. **Robust-yet-fragile is a topological property, not a management failure.** Heavy-tailed networks are exceptionally tolerant of random failure and exceptionally intolerant of targeted or correlated failure. Systems that have survived many random shocks may have learned precisely the wrong lesson about their own resilience.
3. **Interdependence converts gradual degradation into discontinuous collapse.** The Buldyrev result is general. Coupling functional layers — logistics, finance, energy, information — moves the transition from second-order to first-order, which means that the warning interval between "stressed" and "failed" shrinks toward zero.
4. **The binding constraint is the long-chain, low-substitutability input, regardless of its share of value.** Tin was a small fraction of cargo mass and an absolute constraint on bronze. Criticality is a function of substitution elasticity and chain length, not of cost share — which is exactly the quantity conventional procurement accounting does not measure.
5. **Correlated shocks defeat diversification.** Route diversification protects against independent failures. When drought, seismicity, and unrest are spatially correlated, apparently independent routes fail together, and measured diversification overstates real protection.
6. **The visible agent of collapse may be an output of the system's own stress.** If the endogenous-mobility result holds (§3.4, O6), then attributing collapse to the actor who appears at the moment of failure is a category error. The modern read is about the interpretation of proximate triggers in crises with long structural build-ups, and it should be stated at that level of generality and no further.

**Proposition 6 is the study's contribution to general theory, and also the one most at risk of being over-claimed.** It must be stated as conditional on the model result, with the model's limitations attached.

## 4.3 Conclusion architecture

The concluding argument is written to a fixed structure that makes the strength of each claim visible:

1. **What the evidence shows** — Phase 2 findings, stated with tiers and uncertainties, independent of any model.
2. **What the model shows** — Phase 3 results, always paired with the null-model comparison.
3. **Posterior model probabilities** for H₀–H₄, with prior sensitivity.
4. **What remains unresolved**, with the specific evidence that would resolve it.
5. **What generalizes**, gated by the homology test.
6. **What does not generalize** — the disanalogy register.

The concluding claim, if the hypothesis is supported, is bounded in the following form and no stronger:

> The observed spatiotemporal pattern of failure and survival in the Eastern Mediterranean between 1250 and 1100 BCE is better explained by exogenous climatic and seismic shocks propagating through a highly efficient, low-redundancy, strongly coupled exchange network than by those shocks alone, by network structure alone, or by exogenous migration. The mobile groups recorded in Egyptian sources are, on this account, consistent with an output of the failing system rather than its initiating cause — though the textual record is too thin, and its survival too strongly conditioned on the collapse itself, to exclude an independent migratory contribution.

If the hypothesis is not supported, the corresponding statement is written in advance (§5.1) so that the framing cannot drift after the results are seen.

---

# 5. Governance, Falsification, and Programme Management

## 5.1 Pre-registration and falsification criteria

Registered before data compilation, at OSF or an equivalent registry, with a timestamped hash.

**The study hypothesis H₄ is rejected if any of the following obtains:**

| # | Falsification condition |
| --- | --- |
| F1 | The reconstructed network's efficiency and robustness are within the 90% interval of degree-preserving and spatially constrained null models — i.e. it is not unusually brittle |
| F2 | Failure incidence and severity show no association with network position after controlling for hydroclimate exposure, seismic exposure, excavation intensity, and dating quality |
| F3 | The historically constrained shock schedule collapses the redundancy-augmented counterfactual network as readily as the empirical one |
| F4 | Failure times show no path-ordered structure: lag between connected node failures is unrelated to network distance, at the resolution the chronology permits |
| F5 | The earliest robust attestations of Sea Peoples activity **precede** the earliest robust indicators of supply-chain and hydroclimate stress in the source regions |
| F6 | The Millek-protocol re-audit reduces the corpus of securely attested destructions below the threshold needed to detect the predicted spatial pattern with power ≥ 0.8 |
| F7 | Bayes factor for H₄ against the best adversarial H₁/H₂ model is < 3 |

F6 deserves emphasis: it is a condition under which the study **cannot answer the question** rather than one under which the answer is negative, and the two must not be conflated in reporting. If F6 obtains, the deliverable becomes the audited evidence base and a power analysis specifying what new excavation and dating would be required — which is a real contribution.

**Pre-written null result.** The abstract to be published if H₄ fails is drafted and registered at the outset.

## 5.2 Phase structure and dependencies

| Phase | Duration | Depends on | Gate to proceed |
| --- | --- | --- | --- |
| 1 — Framework | Months 1–9 | — | Hypothesis set and operator table approved by advisory panel |
| 2 — Data | Months 6–30 | Phase 1 operators | Evidence base passes external audit; ≥ 60% of target sites at Tier A/B |
| 3 — Modelling | Months 24–45 | Phase 2 release v1.0 | Validation suite (§3.7) passed, including the Thera benchmark |
| 4 — Synthesis | Months 42–54 | Phase 3 results | Homology test executed and reported regardless of outcome |

Phases overlap deliberately; the Phase 2 → Phase 3 gate is hard, and modelling on unaudited data is prohibited.

## 5.3 Team composition

Minimum viable team: a network scientist with percolation and multilayer expertise; a computational archaeologist; four regional archaeological specialists (Aegean, Anatolian, Levantine/Cypriot, Egyptian); a philologist covering Akkadian/Ugaritic/Hittite; a palaeoclimatologist; an archaeometallurgist; a Bayesian chronologist; a data engineer; and a research-ethics and heritage-liaison officer.

**Anti-siloing requirement.** Every quantitative result is presented to the regional specialists in domain terms before publication, with authority to veto claims that misrepresent their evidence. Every archaeological interpretation is presented to the modellers with authority to flag unfalsifiable claims. Disagreements that survive are published as disagreements.

## 5.4 Data acquisition priorities

Where the existing record is inadequate, the protocol specifies what new work would most improve inference, ranked by expected reduction in posterior uncertainty:

1. **High-resolution, well-dated hydroclimate records for the Anatolian plateau and the northern Levant**, the largest current spatial gaps in the drought field.
2. **Dendrochronologically anchored or wiggle-matched sequences from destruction contexts**, the only realistic route to decadal ordering.
3. **Systematic LIA and tin-isotope programmes on stratified metal assemblages spanning 1300–1050 BCE**, to convert the tin-supply argument from provenance snapshots into a time series.
4. **Re-excavation or archival re-study of destruction contexts flagged as insufficiently documented** by the §2.4 audit.
5. **Systematic quantification of storage capacity by phase** at palatial sites — currently the weakest link in the `α` estimate, and the input on which the sharpest Phase 4 prediction depends.

## 5.5 Adversarial review and conflict of interest

Each phase is reviewed by at least one scholar on record as sceptical of the systems-collapse framing; reviewers are named in the publication. All model code and derived data are released at submission, not on request. Where a team member has a prior public commitment to one of H₀–H₄, that commitment is declared, and that member does not have final authority over the analysis pipeline for the test that bears on it.

## 5.6 Ethics and heritage

Coordinates for sites at looting risk are fuzzed in public releases. Sampling of archaeological material requires permits from the relevant national authorities and is minimized in favour of legacy-collection reanalysis. Regional scholars and institutions in the countries where the evidence originates are collaborators with authorship, not data providers. Published language avoids the framing of collapse as civilizational judgement, and avoids the deployment of ancient migration as commentary on modern migration — a use of this material that is both historically indefensible and politically instrumentalized.

## 5.7 Risk register

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Destruction corpus collapses under re-audit (F6) | Medium | High | Front-load the audit; design order-free tests (§2.3.3) that survive it |
| Chronology cannot resolve ordering | High | High | Cross-sectional tests as primary; wiggle-matching programme; report unresolved pairs honestly |
| Network reconstruction is circular (routes inferred from the same finds used to test the model) | High | Critical | Strict separation of edge-construction evidence from outcome evidence; spatial hold-out validation; simulate the survival bias and quantify its effect on the frontier result |
| Overfitting to a single realization | High | High | Out-of-sample and hold-out validation; independent-event benchmark; Sobol sensitivity |
| Modern-parallel over-claiming | High | High (reputational) | Homology gate; disanalogy register; external review of Phase 4 by an economist and a supply-chain specialist |
| Proxy disagreement dismissed as noise | Medium | High | Between-record disagreement carried as parameter uncertainty, never averaged away |
| Team siloing | Medium | Medium | Cross-domain veto rights; disagreements published |

## 5.8 Deliverables

| ID | Deliverable |
| --- | --- |
| D1 | Historiographical synthesis and formal operator table (Phase 1) |
| D2 | Audited, versioned, DOI-minted multiproxy evidence base with full uncertainty representation |
| D3 | Destruction-horizon re-audit catalogue — a standalone contribution regardless of the study's outcome |
| D4 | Bayesian chronological model with published posterior orderings and an explicit register of unresolved pairs |
| D5 | Open-source multilayer network model and cascade simulation suite, containerized and reproducible |
| D6 | Primary results paper: model comparison and tipping-point analysis |
| D7 | Methods paper: multiproxy normalization and the causal firewall, written for transfer to other collapse studies |
| D8 | Phase 4 synthesis: brittleness, the efficiency–resilience frontier, and the homology assessment |
| D9 | Public-facing interactive visualization of the network and its failure dynamics |

---

# Appendix A — Notation

| Symbol | Meaning |
| --- | --- |
| `M(t)` | Temporal multiplex network |
| `V`, `N` | Node set; number of nodes |
| `L`, `α` | Layer set; layer index (also used for cascade tolerance — disambiguated by context) |
| `w_ij^(α)` | Volume weight, `i → j`, layer `α` |
| `d_ij^(α)` | Dependency weight: share of `j`'s consumption of `α` transiting `i` |
| `k`, `⟨k⟩`, `⟨k²⟩` | Degree; first and second moments |
| `κ` | `⟨k²⟩/⟨k⟩`; Molloy–Reed parameter |
| `f`, `f_c` | Removal fraction; critical removal fraction |
| `γ` | Degree-distribution tail exponent |
| `B_i` | Betweenness centrality of node `i` |
| `SC_i^(α)` | Supply criticality of node `i` for commodity `α` |
| `E_glob` | Global efficiency |
| `R_ij`, `R̄` | Pairwise edge-disjoint path count; dependency-weighted mean |
| `R` | Schneider robustness index, `(1/N)Σ_q S(q)` |
| `B` | Brittleness index, `1 − 2R` |
| `L_i`, `C_i` | Node load; node capacity |
| `α` (cascade) | Tolerance parameter, `C_i = (1+α)L_i(0)` |
| `q` | Inter-layer coupling strength |
| `Ψ(f)` | Supply-satisfaction ratio (order parameter) |
| `χ(f)` | Percolation susceptibility |
| `ν` | Finite-size-scaling exponent |
| `π_i`, `σ_i`, `c_i`, `ρ_i`, `μ_i` | Node agricultural capacity, storage buffer, administrative complexity, political dependency, metallurgical dependency |
| `r_j^(α)` | Substitution capacity of node `j` for commodity `α` |
| `θ` | Tin fraction in bronze (≈ 0.10) |
| `δ_i(t)` | Hydroclimate-driven capacity reduction at node `i` |
| `Δ_R` | Regional radiocarbon offset parameter |
| `t_A`, `Δ_AB` | Modelled event date; posterior lag between events |

---

# Appendix B — Verified Source Register

Every item below was checked against a publisher, journal, or institutional record during protocol preparation. Identifiers are reproduced as published.

## Anchor monographs

| Source | Identifier |
| --- | --- |
| Cline, E.H. *1177 B.C.: The Year Civilization Collapsed.* Princeton UP, 2014; rev. ed. 2021 | ISBN 9780691208015 (rev.); 9780691140896 (1st); JSTOR `j.ctv15r58dw` |
| Cline, E.H. *After 1177 B.C.: The Survival of Civilizations.* Princeton UP, 2024 | ISBN 9780691192130 |
| Tainter, J.A. *The Collapse of Complex Societies.* Cambridge UP, 1988 | ISBN 9780521386739 |
| Renfrew, C. "Systems Collapse as Social Transformation," in *Transformations*, 1979 | Academic Press |
| Millek, J.M. *Destruction and Its Impact on Ancient Societies at the End of the Bronze Age.* Lockwood Press, 2023 | ISBN 9781948488839 |
| Killebrew, A.E. & Lehmann, G. (eds.) *The Philistines and Other "Sea Peoples" in Text and Archaeology.* SBL, 2013 | ISBN 9781589831292 |
| Leidwanger, J. & Knappett, C. (eds.) *Maritime Networks in the Ancient Mediterranean World.* Cambridge UP, 2018 | ISBN 9781108429948 |
| Knappett, C. (ed.) *Network Analysis in Archaeology.* Oxford UP, 2013 | — |
| Moran, W.L. *The Amarna Letters.* Johns Hopkins UP, 1992 | Standard edition, EA 1–382 |

## Climate and environment

| Source | Identifier |
| --- | --- |
| Langgut, Finkelstein & Litt 2013, "Climate and the Late Bronze Collapse: New Evidence from the Southern Levant," *Tel Aviv* 40(2): 149–175 | DOI `10.1179/033443513X13753505864205` |
| Kaniewski et al. 2013, "Environmental Roots of the Late Bronze Age Crisis," *PLOS ONE* 8(8): e71004 | DOI `10.1371/journal.pone.0071004` |
| Drake, B.L. 2012, *Journal of Archaeological Science* 39(6): 1862–1870 | — |
| Finné, Woodbridge, Labuhn & Roberts 2019, "Holocene hydro-climatic variability in the Mediterranean," *The Holocene* | DOI `10.1177/0959683619826634` |
| Jacobson, Seguin & Finné 2024, "Holocene hydroclimate synthesis of the Aegean," *The Holocene* | DOI `10.1177/09596836241275028` |
| Weiberg & Finné 2018, "Resilience and persistence of ancient societies in the face of climate change," *World Archaeology* | DOI `10.1080/00438243.2018.1515035` |

## Seismicity

| Source | Identifier |
| --- | --- |
| Nur, A. & Cline, E.H. 2000, "Poseidon's Horses," *Journal of Archaeological Science* 27(1): 43–63 | — |
| Stiros, S. 1996, "Identification of earthquakes from archaeological data," in Stiros & Jones (eds.), *Archaeoseismology*, Fitch Laboratory Occasional Paper 7 | — |

## Metals and provenance

| Source | Identifier |
| --- | --- |
| Powell et al. 2022, "Tin from Uluburun shipwreck…," *Science Advances* 8(48): eabq3766 | DOI `10.1126/sciadv.abq3766` |
| Stos-Gale et al. 1997, "Lead isotope characteristics of the Cyprus copper ore deposits…," *Archaeometry* 39(1) | DOI `10.1111/j.1475-4754.1997.tb00792.x` |
| OXALID lead-isotope reference database, University of Oxford | Online reference database |

## Chronology

| Source | Identifier |
| --- | --- |
| Reimer et al. 2020, IntCal20 Northern Hemisphere calibration curve, *Radiocarbon* 62(4) | — |
| Manning et al. 2020, "Mediterranean radiocarbon offsets and calendar dates for prehistory," *Science Advances* | DOI `10.1126/sciadv.aaz1096` |
| Manning et al. 2020, "Radiocarbon offsets and old world chronology…," *Scientific Reports* | DOI `10.1038/s41598-020-69287-2` |
| Manning et al. 2018, "Fluctuating radiocarbon offsets observed in the southern Levant," *PNAS* 115(24): 6141 | — |

## Network science

| Source | Identifier |
| --- | --- |
| Knappett, Evans & Rivers 2008, "Modelling maritime interaction in the Aegean Bronze Age," *Antiquity* 82(318): 1009–1024 | — |
| Knappett, Rivers & Evans 2011, "The Theran eruption and Minoan palatial collapse," *Antiquity* 85(329): 1008–1023 | DOI `10.1017/S0003598X00068459` |
| Cline, D.H. & Cline, E.H. 2015, "Text Messages, Tablets, and Social Networks: The 'Small World' of the Amarna Letters," in *There and Back Again — the Crossroads II*, 17–44 | Charles University, Prague |
| Cohen, Erez, ben-Avraham & Havlin 2000, "Resilience of the Internet to random breakdowns," *Phys. Rev. Lett.* 85(21): 4626 | DOI `10.1103/PhysRevLett.85.4626` |
| Motter & Lai 2002, "Cascade-based attacks on complex networks," *Phys. Rev. E* 66: 065102(R) | DOI `10.1103/PhysRevE.66.065102` |
| Buldyrev et al. 2010, "Catastrophic cascade of failures in interdependent networks," *Nature* 464: 1025–1028 | DOI `10.1038/nature08932` |
| Schneider et al. 2011, "Mitigation of malicious attacks on networks," *PNAS* 108(10): 3838–3841 | — |
| Latora & Marchiori 2001, "Efficient behavior of small-world networks," *Phys. Rev. Lett.* 87: 198701 | — |
| Clauset, Shalizi & Newman 2009, "Power-law distributions in empirical data," *SIAM Review* 51(4): 661–703 | — |
| Scheffer et al. 2009, "Early-warning signals for critical transitions," *Nature* 461: 53–59 | — |

## `[DATA REQUIREMENT]` — evidence classes specified but not resolved to particular datasets in this protocol

1. Comprehensive site-level destruction/abandonment catalogue for 1250–1100 BCE meeting the §2.4 rubric.
2. Anatolian and northern Levantine hydroclimate records meeting the §2.2.1 acceptance criteria.
3. Complete published corpus of oxhide-ingot and tin LIA/tin-isotope determinations within the temporal universe, with analytical metadata.
4. Storage-capacity-by-phase measurements at palatial sites, for estimation of `α`.
5. Systematic excavation-intensity metadata for all sites in the universe.
6. Regional field-survey datasets, systematically collected and published, as a second sampling frame.
7. Palaeoseismic trench and offset-feature data for the relevant fault systems, for the §2.2.3 corroboration criterion.

---

*Protocol v1.0. Methodology only — no empirical results are claimed or implied. All quantities designated `[DATA REQUIREMENT]` must be resolved to specific, verifiable datasets before any analysis is executed.*
