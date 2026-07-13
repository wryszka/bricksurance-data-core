# Coverage — "Can it answer my question?"

A topic-coverage stress test of the foundation: ~100 things a European/UKI
insurer's people (CEO to claims handler, regulator to buyer agent) plausibly
ask, judged **strictly against the deployed ontology**
(`build/ontology/bricksurance-data-core.ontology.json`, v0.6.0 — 33 entities,
32 code sets, 4 metric views, 7 functions, 2 semantic views). Companion to
[GENIE_CATALOG.md](GENIE_CATALOG.md), [AGENT_PLAYBOOK.md](AGENT_PLAYBOOK.md)
and the gap grades in [CDO_REVIEW.md](CDO_REVIEW.md).

## Summary

**100 topics: 52 COVERED · 22 PARTIAL · 26 MISSING.**

Top-10 highest-value MISSING items, ranked by how hard each bites:

1. **Earning patterns + expense allocation** — no earned premium, no combined
   ratio, no underwriting P&L. The single biggest analytical ceiling.
2. **Billing, payments & receivables** — premium is written but never
   collected; no instalments, cash allocation, or aged debt (CDO H1 acid test).
3. **Consent, DSAR & erasure design (GDPR)** — no lawful-basis or consent
   entities, and no answer to erasure-vs-immutable-transactions (CDO H4).
4. **General ledger linkage** — no posting/journal entity; finance
   reconciliation stops at `valuation_result`.
5. **Fraud & SIU signals** — no fraud indicator or network entities; a
   claims-director conversation stopper.
6. **Consumer Duty outcome measures** — conduct = complaints only; no
   fair-value or customer-outcome metrics, no vulnerability flags.
7. **Intermediary agreements & commission terms** — commission is
   transactional but there is no agreement, TOBA or terms entity behind it.
8. **Life administration depth** — surrenders, unit funds, annuities in
   payment, riders; life is a valuation slice, not an admin model.
9. **FX rates** — deliberately deferred; every money answer is
   per-original-currency, so no group consolidated view.
10. **Row-level security design** — classification tags exist; no row-filter,
    persona or purpose-based access pattern (CDO M4).

**Verdict.** The foundation is a genuinely answerable spine, not a façade:
the P&C written-premium/claims core, outward and inward reinsurance, the
valuation-run audit chain, conduct complaints and the agentic underwriting
loop all answer real questions today from certified metric views and governed
functions — and PARTIALs are mostly thin data or missing certification, not
missing structure. But it is a *written-basis* world: nothing that requires
earning, expenses, cash, GL or FX can be answered at all, customer and GDPR
topics fall off a cliff past the party/role spine, and the regulatory lens
(IFRS 17 groups, QRT production, DQ evidence) is measure codes rather than
capability. As a base to extend under the evolution contract it holds;
represented as complete estate coverage it would fail roughly one client
question in four outright.

---

## 1. Executive & portfolio performance (CEO / CFO / CUO)

| Topic (as the client would say it) | What answers it | Status | Gap note |
|---|---|---|---|
| "What's our GWP by line and underwriting year?" | `underwriting_metrics.gross_written_premium` over `semantics.financial_transaction`; P&C Book Genie | **COVERED** | — |
| "What's our loss ratio by line?" | `underwriting_metrics.loss_ratio` (incurred / written) | **PARTIAL** | Written-basis, not earned-adjusted — no earning patterns exist |
| "What's our combined ratio?" | — | **MISSING** | Needs expense entities + earning patterns; no expense domain at all |
| "How is the book moving month on month?" | `underwriting_metrics` dims `transaction_month`, `underwriting_year` | **COVERED** | — |
| "Net of reinsurance, where do we land by line?" | `cession_metrics.ceded_premium` + `underwriting_metrics` | **PARTIAL** | Ceded premium yes; ceded *claims* only for cat events (`event_loss.ceded_loss_amount`), not per ordinary claim |
| "Top clients/policies by premium" | `premium_transaction` + `party_role` (POLICYHOLDER) + `party` | **COVERED** | — |
| "What's our solvency coverage ratio?" | `valuation_metrics` (`OWN_FUNDS`, `SCR` measures) | **COVERED** | — |
| "Profitability by customer segment" | — | **MISSING** | No segmentation attributes on `party`; a customer_segment entity/tagging would close it |

## 2. Product, pricing & appetite (CUO / product owner)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "What products do we sell, and which are open?" | `product`, `product_coverage`, `product_status` code set | **COVERED** | — |
| "Is an £8m warehouse in GB within appetite?" | `fn_appetite_check` over `appetite_rule` | **COVERED** | Same rules humans read and agents execute |
| "Give me an indicative premium for that risk" | `fn_indicative_quote` from `product.base_rate` | **COVERED** | Indicative only, by design |
| "What does the product ask at quotation?" | `underwriting_question` (question set as data) | **COVERED** | — |
| "Which rating version priced this policy?" | — | **MISSING** | Nothing beyond a single `base_rate`; needs rating_version / rate-table entities |
| "Product variants and life riders" | — | **MISSING** | Nothing between `line_of_business` codes and the policy (CDO H1); needs variant/rider entities |
| "Fair value assessment per product" | — | **MISSING** | No fair-value/outcome measures; Consumer Duty Outcomes space is in the Genie backlog |
| "Loss ratio by product, not just by line" | `quote.product_id` → converted `quote.policy_id` → `underwriting_metrics` grain | **PARTIAL** | `policy` carries no `product_id`; only reachable via converted quotes |

## 3. Distribution, channels & intermediaries (distribution director / broker)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "Quote funnel by channel — including machine agents" | `quote` (`distribution_channel_code`, `quote_status_code`); Distribution Genie | **COVERED** | MACHINE_AGENT is a first-class channel |
| "Net commission by broker, including clawbacks" | `commission_transaction` (signed, `CLAWBACK` type) + `party` | **COVERED** | — |
| "Who's the broker on this policy?" | `party_role` (BROKER) on `policy`; `fn_policy_snapshot` | **COVERED** | — |
| "Broker-level loss ratio / book performance" | `party_role` joined to `semantics.financial_transaction` | **PARTIAL** | Computable but not certified in any metric view; no broker dimension in `underwriting_metrics` |
| "Our intermediary agreements, TOBAs, commission terms" | — | **MISSING** | No intermediary_agreement entity; commission has movements but no contractual terms behind them |
| "Delegated authority / coverholder oversight" | COVERHOLDER role + channel code + `premium_bordereau_line` | **PARTIAL** | Bordereau flow live; no binder-agreement or authority-limits entity |
| "How does the aggregator panel convert?" | `quote` funnel filtered to AGGREGATOR channel | **COVERED** | — |
| "What's our renewal retention rate?" | `policy.renews_policy_id` chain + statuses; Distribution Genie | **COVERED** | — |

## 4. Policy administration & billing (COO / operations)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "What's in force today, by status?" | `policy.policy_status_code`; `fn_policy_snapshot` | **COVERED** | — |
| "Mid-term adjustments and their premium effect" | `endorsement` + `premium_transaction` (ADJUSTMENT) | **COVERED** | Contract change and money booked separately, by design |
| "Cancellations and return premium" | `endorsement` (CANCELLATION) + `premium_transaction` (RETURN) | **COVERED** | — |
| "Which policies lapsed for non-payment?" | `policy_status` LAPSED code | **PARTIAL** | Status exists but no billing data to evidence the non-payment behind it |
| "Instalment plans, direct debits, collections" | — | **MISSING** | No billing domain — CDO H1's acid test; needs instalment_plan / payment / cash-allocation entities |
| "Aged premium debt / receivables" | — | **MISSING** | Same billing gap; premium is written, never collected |
| "What did this policy look like on 31 Dec, as known on 15 Jan?" | — | **MISSING** | No model-wide temporal strategy (CDO M2); as-of exists only on `event_loss.as_of_date` |
| "Show me the schedule issued for this policy" | `document` (SCHEDULE type, `policy_id`, `extracted_text`) | **COVERED** | — |

## 5. Claims (claims director / handler)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "What's the status of claim X?" | `fn_claim_status`; `claim` | **COVERED** | — |
| "Outstanding reserve on claim X — derived, not stored" | `fn_outstanding_reserve` summing `claim_transaction` movements | **COVERED** | — |
| "Incurred development by cause of loss" | `underwriting_metrics` (`claims_incurred`, `cause_of_loss_code` dim) | **COVERED** | — |
| "FNOL-to-payment cycle times" | `business_event` (FNOL, CLAIM_PAYMENT) timestamps | **PARTIAL** | Events exist; Claims Operations Genie space defined but not stood up |
| "Subrogation and salvage recoveries" | `claim_transaction` (RECOVERY) + `underwriting_metrics.recoveries` | **COVERED** | — |
| "Large-loss watchlist above a threshold" | `claim_transaction` summation per claim | **COVERED** | Ad-hoc query today; no certified large-loss view |
| "Fraud indicators / SIU referrals" | — | **MISSING** | No fraud-signal or network entities (pattern exists in the claims workbench, not this model) |
| "Litigation status, leakage, TPA/supplier performance" | — | **MISSING** | No litigation, handler-assignment or supplier entities |
| "Search the claim evidence — what did the surveyor say?" | `document` (CLAIM_EVIDENCE, SURVEY_REPORT) `extracted_text` + vector index | **COVERED** | — |

## 6. Reinsurance — outward and inward (reinsurance buyer / inward UW)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "Which treaties is policy X ceded to, at what share?" | `fn_cession_trace`; `cession` | **COVERED** | — |
| "Ceded premium by treaty and reporting month" | `cession_metrics` over `exchange.cession_bordereau_line` | **COVERED** | — |
| "Submission funnel and bind ratio by treaty form" | `submission_metrics` (`bind_ratio`, `requested_limit_total`) | **COVERED** | — |
| "Programme structure — layers, attachments, reinstatements" | `treaty` + `treaty_layer` (`reinstatement_count`, `reinstatement_premium_rate`) | **COVERED** | Terms held; reinstatement *premium bookings* not modelled |
| "Modelled vs reported losses for the storm" | `event_loss` (`loss_basis_code`) + `cat_event` | **COVERED** | — |
| "Reinsurance recoveries on this individual claim" | `claim_transaction` RECOVERY | **PARTIAL** | Recoveries are not attributed to treaties; treaty-level recovery only for cat via `event_loss.ceded_loss_amount` |
| "Reinsurer security — credit ratings, counterparty exposure" | — | **MISSING** | No security-rating or counterparty-limit entity on `party` |
| "How eroded is the cat layer against this year's events?" | `event_loss` vs `treaty_layer.limit_amount`/`attachment_amount` | **PARTIAL** | Joinable per event; no aggregate annual erosion measure certified |

## 7. Exposure, catastrophe & accumulation (exposure manager / CRO)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "Accumulation by postcode / country" | `insured_object` (`postcode`, `country_code`) + `coverage.sum_insured_amount` | **COVERED** | — |
| "Total sum insured within 5 km of this point" | `insured_object.latitude/longitude` | **PARTIAL** | Coordinates modelled but only partially geocoded; no geo functions shipped |
| "Cat event footprint against the in-force book" | `cat_event` + `event_loss` (MODELLED basis) | **COVERED** | — |
| "Vehicle detail — make, model, year" | `vehicle` satellite on `insured_object` | **COVERED** | The typed-satellite pattern, live for motor |
| "Flood zone / peril scores on our locations" | — | **MISSING** | No external-enrichment or peril-score entities |
| "PML and return-period outputs" | — | **MISSING** | No cat-model results entity beyond per-event `event_loss` |
| "An exposure Genie I can just ask" | insured_object + event_loss + cat_event | **PARTIAL** | Data exists; Exposure & Accumulation space is defined, not live (GENIE_CATALOG) |
| "Liability exposure — turnover, wageroll, headcount" | `insured_object_type` LIABILITY_EXPOSURE | **PARTIAL** | Abstract exposure unit exists; no liability satellite with rating detail |

## 8. Life & actuarial governance (chief actuary)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "BEL by product/line and valuation date" | `valuation_metrics`; Life & Valuations Genie | **COVERED** | — |
| "Exactly which assumptions did run X use?" | `valuation_run_assumption` + `assumption_set` versions | **COVERED** | — |
| "Where is the mortality basis in maker/checker?" | `assumption_set` (`assumption_status` lifecycle, `approved_by`) | **COVERED** | — |
| "Which economic scenario set is production-active?" | `scenario_set` (`scenario_status` ACTIVE) | **COVERED** | — |
| "In-force model points at the valuation date" | `model_point` (age × term cohorts, sums assured) | **COVERED** | — |
| "Are RED runs blocked from downstream?" | `valuation_run.run_verdict_code` gate | **COVERED** | — |
| "Actual-vs-expected experience analysis" | — | **MISSING** | No actual decrement/experience entities (deaths, lapses observed) to set against assumptions |
| "Surrenders, unit funds, annuities in payment, riders" | — | **MISSING** | Life is a valuation slice, not an admin model (CDO H1) |

## 9. Valuation, finance & regulatory reporting (CFO / regulator)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "Technical provisions by line, across regimes" | `valuation_metrics` (BEL, RISK_MARGIN, TECHNICAL_PROVISION) | **COVERED** | — |
| "IFRS 17 CSM and risk adjustment by cohort" | `valuation_result` (CSM, RISK_ADJUSTMENT codes, `cohort` attr) | **PARTIAL** | Measure codes + free-text cohort only; no groups of contracts, coverage units or transition amounts (CDO H4) |
| "Populate the Solvency II QRTs from this" | `valuation_result` + `premium/claim_transaction` sources | **PARTIAL** | Source measures exist; no QRT template mapping or extract |
| "Reconcile valuation results to the general ledger" | — | **MISSING** | No posting/journal entity; needs a gl_posting domain |
| "Earned premium and UPR at period end" | — | **MISSING** | No earning patterns; premium exists on a written basis only |
| "Expenses by function, allocated to lines" | — | **MISSING** | No expense entities anywhere in the model |
| "Group view in a single reporting currency" | — | **MISSING** | FX deliberately deferred; no fx_rate entity — every view is per-`currency_code` |
| "IBNR vs case reserves at the valuation date" | `valuation_metrics` (IBNR, CASE_RESERVE_TOTAL) | **COVERED** | — |
| "Solvency II data-quality evidence per data item" | `data_dictionary` + prose `quality:` rules | **PARTIAL** | Rules are documentation, not executable expectations with an evidence log (CDO M1) |

## 10. Conduct, complaints & customer (compliance / CMO)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "Complaints by FCA category, and uphold rate" | `complaint` (`complaint_category`/`complaint_status` per FCA groupings) | **COVERED** | — |
| "Redress paid, and what went to the ombudsman" | `complaint.redress_amount`, REFERRED_FOS status | **COVERED** | — |
| "Trace complaints back to the claim or policy" | `complaint.claim_id` / `complaint.policy_id` | **COVERED** | — |
| "A Consumer Duty outcomes dashboard" | — | **MISSING** | Conduct = complaints only; no outcome/fair-value measures (Genie backlog names this) |
| "Which customers are flagged vulnerable?" | — | **MISSING** | No customer-characteristic attributes on `party` |
| "Everything we know about this customer (360)" | `party` + `party_role` across policies, claims, treaties, quotes | **PARTIAL** | Role graph yes; no contact points, addresses, households or preferences (CDO H1/H2) |
| "Consent, marketing preferences, DSARs" | — | **MISSING** | No consent/lawful-basis/DSAR entities (CDO H4) |
| "Are we closing complaints inside the 8-week window?" | `complaint.received_date` / `closed_date` ageing | **COVERED** | Threshold applied at query time |

## 11. Data governance, privacy & audit (CDO / privacy / internal audit)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "Which columns hold PII?" | `data_dictionary` classification tags; Data Governance Genie | **COVERED** | — |
| "What exactly does 'incurred' mean here?" | `fn_define` over the data dictionary | **COVERED** | — |
| "How does this map to ACORD / Lloyd's CDR?" | `standards` crosswalk on entities, attributes and code sets | **COVERED** | Crosswalk citations, not licensed content |
| "Where did this record come from?" | `source_system_code` on every core entity + natural keys | **COVERED** | Row provenance modelled; pipeline lineage is the platform's job |
| "What changed between model versions?" | `schema_migration` log + migration planner (v0.4.0→v0.5.0 worked example) | **COVERED** | — |
| "Which entities are certified vs draft?" | `maturity` tag on every entity | **PARTIAL** | Every entity is `draft`; the certification workflow has never been run (CDO H3) |
| "Is party truly mastered across our eight PAS?" | `party` grain assertion | **PARTIAL** | No match keys, survivorship or merge audit — assertion, not implementation (CDO H2) |
| "How do we erase a person from append-only transactions?" | — | **MISSING** | No erasure/crypto-shredding design note (CDO H4) — Legal's first question |
| "Unit A must not see unit B's book" | — | **MISSING** | Column classification only; no row-filter/RBAC/persona design (CDO M4) |

## 12. AI, agents, events & data exchange (CDO / counterparties / machine buyers)

| Topic | What answers it | Status | Gap note |
|---|---|---|---|
| "What can I ask Genie today?" | 5 live spaces with SQL-verified benchmarks (GENIE_CATALOG) | **COVERED** | — |
| "Can a buyer agent get a quote end to end?" | MACHINE_AGENT `party` + BUYER_AGENT role + `fn_appetite_check` + `fn_indicative_quote` | **COVERED** | Runs live (`tools/agent_demo.py`) |
| "Are machine decisions audited like human ones?" | `underwriting_decision` (`decided_by_agent`, `appetite_rule_id`, rationale) | **COVERED** | — |
| "Ask the wordings: is flood excluded on this product?" | `document` (POLICY_WORDING) `extracted_text` + vector index | **PARTIAL** | RAG plumbing live; corpus is a thin demo slice |
| "A monitoring agent watching the business in real time" | `business_event` append-only stream (6 event types) | **PARTIAL** | Stream is the feed; no monitoring agent shipped, event vocabulary thin |
| "Send our cession bordereau to the reinsurer — with meaning" | `exchange.cession_bordereau_line` + Delta Share carrying `data_dictionary` | **PARTIAL** | Defined and generated; the Re share itself is pending a metastore grant |
| "Ingest a coverholder's premium bordereau" | `premium_bordereau_line` landing → canonical mapping via the dictionary | **COVERED** | — |
| "Ingest a TPA's *claims* bordereau" | — | **MISSING** | No claim_bordereau_line entity in the exchange domain |
| "Another insurer adopts this and we exchange without mapping" | Ontology JSON import + adoption path | **PARTIAL** | Import works; no second adopter, no extension-namespace conformance test (CDO L1) |

---

*Method note: status was judged only against what exists in the ontology JSON
and the deployed demo estate it describes. COVERED = answerable today;
PARTIAL = structure present but data, depth or certification thin (the note
says which); MISSING = the named entity/domain does not exist. Counts:
52 / 22 / 26 across 100 topics.*

---

## Live sufficiency test (2026-07-13, against the deployed estate)

A sample of the matrix exercised for real, not just mapped:

| Probe | Surface | Result |
|---|---|---|
| GWP + loss ratio by line (GBP, UWY 2026) | P&C Genie | PASS — metric view via MEASURE(), reconciles to transactions |
| Ceded premium by treaty | Reinsurance Genie | PASS — 142,369.95 = 30% of ceded book GWP |
| Term Life BEL at 30 Jun 2026 | Life Genie | PASS — −24,370,000 with run recipe |
| Machine-agent quotes and their decisions | Distribution Genie | PASS — 3 quotes, ACCEPT/DECLINE/REFER, all `bricksurance-uw-agent v1` |
| "Which attributes hold PII?" | Governance Genie | PASS — 4 attributes with definitions |
| Net commission by broker incl. clawbacks | Distribution Genie | PARTIAL — sums correct, returned party ids instead of names (join-to-label nudge needed in instructions) |
| Agentic buyer end-to-end (appetite → quote → claim status → definition) | `agent_demo.py` over 7 governed tools | PASS — five correct tool calls, zero invented figures |
| Smoke suite (structure, tie-outs, heroes, tools) | `smoke_test.py` | PASS — 22/22 |

**Verdict:** the foundation answers the majority of the topic universe today
and fails *legibly* — every MISSING row names the entity or domain that closes
it, which is exactly what "provision the data for any possible option" requires:
the gaps are a priced backlog, not unknowns.

---

## Gap closure — v0.7.0 (2026-07-13)

The top-5 MISSING clusters (and the Customer-360 PARTIAL) are now closed and
live-verified:

| Was missing | Now | Verified |
|---|---|---|
| Earning patterns + expense allocation | `expense_transaction`, `premium_earning` view, `performance_metrics` (earned/loss/expense/**combined ratio**) | Genie: CP GBP combined 1.347 = loss 0.888 + expense 0.459 |
| Billing & receivables | `receivable_transaction` (invoices/cash/write-offs; aged debt = signed sum) | smoke: aged debt derives; Customer space benchmark |
| Consent, DSAR & erasure | `consent`, `data_subject_request`, `contact_point` + **[PRIVACY.md](PRIVACY.md)** erasure design (PII anchors, surrogate history) | smoke: ERASURE refused-with-grounds on record |
| General ledger linkage | `gl_posting` derived per source transaction | smoke: GL premium postings == premium transactions to the penny |
| Fraud & SIU signals | `fraud_signal` (typed, scored, never auto-deciding) | 7 signals in world; in the P&C space |
| (PARTIAL) ids not names in answers | label-resolution rule in every space's generated instructions | Genie: commission by broker now names Marlin & Rees / Atlas |

**Updated position: ~66 COVERED / ~20 PARTIAL / ~14 MISSING.** The remaining
notable MISSING items are deliberate scope calls (people/ops), heavier builds
(bitemporal history, sanctions screening, IFRS 17 cohorts/groups-of-contracts)
or Phase 8–9 outward work (broker open sharing, regulator share, second
adopter) — all named, none unknown. A sixth Genie space
(Customer & Privacy) now serves the customer-360 and privacy-office topics.
