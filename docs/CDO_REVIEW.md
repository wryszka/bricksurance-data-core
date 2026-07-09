# CDO Review — Bricksurance Data Core

**Reviewer: Group CDO persona (adversarial review, 2026-07-09).**
*This is a persona exercise commissioned by the project: I am playing the Group
Chief Data Officer of a European/UKI multi-line insurer — P&C commercial and
motor, life, some inward re, eight policy admin systems from acquisitions,
Solvency II and IFRS 17 reporting, a stalled two-year governance transformation,
and a board impatient about GenAI. I reviewed the repo as handed to me:
README, all of docs/, the model specs, and the tooling. Nothing here is a
statement about any real company.*

---

## 1. Verdict up front

**Adopt-with-conditions.** I would take this as the *base* for my semantic
layer and my LLM-context strategy. I would not represent it to anyone as an
enterprise data model for a multi-line group — at 24 entities it is a spine,
not a skeleton, and the operating model around it is currently one talented
author and a generator.

What I would tell my board, in three sentences: *"We have found an open,
ACORD-aligned insurance model where the business definitions are the source
code and the catalog, documentation and AI context are compiled from them —
which is the discipline our own programme has failed to enforce for two years.
It demonstrably makes GenAI answer actuarial questions correctly, with
regression tests, which is the first credible LLM governance story I have seen.
It covers perhaps a third of what we need, so I am proposing we adopt it as a
base and fund the extension, not buy it as a product."*

## 2. What genuinely impressed me

- **The inversion is real, not rhetorical.** "Business layer first, toolset
  generated" is what every consultancy deck says; here it is literally how the
  repo works — one YAML spec becomes DDL, comments, tags, dictionary, ERD and
  Genie instructions. Why I care: my catalog and my documentation have never
  agreed with each other in my tenure. Here they *cannot* disagree, because
  they are the same file. That kills an entire category of governance toil.
- **LLM benchmarks as the acceptance test of semantics** (METRICS.md §4).
  Storing benchmark questions with SQL ground truths, and treating a failed
  benchmark after a model change as a failing regression test, is the single
  smartest idea in the pack. It converts "is our semantic layer any good?" from
  a workshop question into a pass rate I can put on a board slide.
- **Derived, never stored.** Balances as sums over signed transactions, with
  smoke tests that tie published reserves back to the movements that produced
  them. My auditors and my Solvency II data-quality attestation would love
  this pattern. The hard rules "learned live" (label vs code dimensions,
  currency discipline) read like genuine scar tissue, not theory.
- **Semantics that travel with the share.** Shipping the `data_dictionary`
  table inside every Delta Share is a quietly excellent answer to the
  bordereau problem. Meaning crossing the company boundary with the rows is
  something ACORD has been promising the market for decades.
- **The evolution discipline.** Semver judged from the consumer's view, a
  migration planner that diffs ontology versions, classifies changes, refuses
  a mismatched version bump, and *never auto-applies* — with a worked example
  (v0.4.0→v0.5.0) committed. Most vendor models don't survive their second
  version; this one has thought about change harder than about anything else.
- **The adoption path is honest.** "Shadow, don't switch", "reacting to a
  concrete model is 10× faster than workshopping a blank page", and the
  anti-patterns list read like they were written by someone who has watched a
  programme like mine stall. The candour throughout (deferred FX "until it can
  be honest", loss ratio "not earned-adjusted in this version") buys a lot of
  trust.

## 3. Gaps from my side

Ranked by how hard each bites a real group programme.

### HIGH

**H1. Model coverage is a spine, not an estate.** What I did not find, and
would need within a year: **product/product-catalog** (nothing between
`line_of_business` codes and the policy — I cannot model rating versions,
product variants or life riders); **distribution and commission** (brokers
exist only as party roles; no intermediary agreement, no commission terms or
statements, no channel — that is a third of my P&L conversation with sales);
**billing, payments and receivables** (premium is written but never collected:
no instalment plans, direct debits, cash allocation, dunning or aged debt);
**documents** (policy schedules, claims correspondence — the actual substrate
of most GenAI use cases); **consent and GDPR artifacts** (no lawful-basis,
consent, DSAR or erasure entities anywhere); **general ledger linkage** (no
posting/journal entity, so finance reconciliation stops at "valuation
result"); **expenses and earning patterns** (acknowledged as roadmap — but
without them there is no combined ratio and no earned loss ratio, i.e. no
underwriting P&L). Life is a valuation-run slice, not a life admin model: no
riders, surrenders, unit funds, annuities in payment. *Why it bites:* every
missing domain is a place where my units will invent their own definitions —
exactly the disease this cures. *Remedy I'd accept:* a published coverage map
against ACORD's domain list with a dated extension roadmap, and evidence that
one non-trivial domain (billing is the acid test) was added by someone other
than the original author under the MINOR/MAJOR contract.

**H2. "Mastered across source systems" is asserted, not implemented.** The
party grain says one row per legal person "mastered across source systems",
but the entity carries four business attributes (type, name, country, source
system). No addresses, contact points, dates of birth, company registration
numbers or LEIs — so there is nothing to match *on*. No match keys, no
survivorship rules, no merge/unmerge audit, no golden-record vs source-record
distinction. With eight PAS from acquisitions, party resolution is half my
budget. *Why it bites:* if I deploy this and tell the business "party is
mastered", I have lied to them in a spec file. *Remedy:* either a real MDM
sub-model (source_party, match rules, survivorship policy, steward queue) or —
more honestly — reword the grain to "one row per party as resolved by your
mastering process, which sits upstream of this model", and document the
interface.

**H3. No operating model.** METRICS.md says "ownership is named per domain" —
no owner is named anywhere. There is no stewardship model, no change advisory
board, no arbitration process when Motor and Commercial disagree about a
definition, no funding model, and no answer to who reviews a pull request
against `model/claim/claim.yaml` in *my* fork. The `maturity: draft` tag is on
every single entity — the certification workflow exists as a tag value, not
as a process anyone has run. *Why it bites:* my last transformation stalled
precisely here, with better tooling than my teams deserved. *Remedy:* a
RACI-per-domain template, a worked definition-dispute example, and the
maturity workflow exercised end-to-end on at least one entity (draft →
stable → certified, with named evidence).

**H4. Regulatory lens is a tagline, not a capability.** Solvency II and IFRS 17
appear as `valuation_measure` codes on a well-shaped result entity — good bones
— but: no **records of processing** or purpose limitation; no **right-to-
erasure** story (and a real tension the docs never confront: transactions are
"derived, never overwritten" and immutable, while GDPR requires me to erase a
natural person — I need a documented crypto-shredding or pseudonymisation
pattern, not silence); no **Solvency II data-quality evidence** (the directive
expects demonstrable accuracy/completeness/appropriateness per data item
feeding the internal model — the dictionary is a start, the evidence chain
does not exist); IFRS 17 needs **cohorts, groups of contracts, coverage units
and transition amounts**, not just a CSM measure code; and nothing at all on
**DORA** — no register of ICT dependencies, no criticality classification of
the data services this layer becomes once my regulator reports depend on it.
*Remedy:* a REGULATORY.md mapping each regime's data requirements to model
elements, with honest "not covered" rows; an erasure design note; a DQ
evidence design (see M1).

### MEDIUM

**M1. Data quality stops at structure.** The `quality:` blocks in specs are
prose rules "generated into docs now; DQ expectations later". The smoke test
is genuinely good (16 checks, cross-domain tie-outs) but it validates the
*demo world*, not *my data*. No thresholds, no DQ scoring, no exception
management, no reconciliation framework against source systems. *Remedy:*
compile `quality:` rules to executable expectations (DLT expectations or
constraint checks) with results landed in an auditable DQ log — the generator
architecture makes this a natural extension, which is why I'll hold them to it.

**M2. No history, no bitemporality.** Entities are current-state: policy and
claim rows have no effective/system time, no SCD treatment; party_role has
start/end dates but nothing else does. Transactions give me an audit trail for
*money* — excellent — but "what did we believe this policy looked like on
31 December, as known on 15 January" is the question Solvency II resubmissions
and IFRS 17 restatements actually ask. The `as-of` pattern exists exactly once
(event_loss snapshots — demo 9 is lovely) and needs to become a model-wide
convention. *Remedy:* a documented temporal strategy (even "system time =
Delta time travel + snapshot views; valid time = explicit columns on these
entities") — decided, not deferred.

**M3. Volume realism.** The deployed world is ~700 rows, 60 policies, with a
`--scale` knob. Nothing about the architecture worries me at scale — it's
Delta tables — but zero evidence exists for metric-view performance, Genie
accuracy, or migration tooling behaviour at 10M policies and 300M
transactions. Genie benchmarks that pass on 18 claims tell me little about
disambiguation on a real book. *Remedy:* one published run at `--scale`
equivalent to a mid-size carrier, with benchmark pass rates and query timings.

**M4. Security model is classification-deep.** Four classification values
compiled to column tags, with masking-policy *guidance*. No row-level story
(unit A must not see unit B's book; the broker-facing pattern from my other
context is exactly what's missing here), no purpose-based access, no persona
model, no segregation between the demo's god-mode deploy identity and any
real operating roles. *Remedy:* a reference RBAC/ABAC design per domain and
one worked row-filter example bound to the tags.

### LOW

**L1. "Who maintains the standard?"** The market-standard ambition (import one
JSON, two adopters exchange without mapping) collapses the moment two adopters
extend `claim_status` differently — the crosswalk fields help humans, not
machines. There is no governance body, no namespace convention for extensions,
no conformance test for "still compatible with base". Fine for a base-to-fork;
fatal for a *standard* until someone owns it. *Remedy:* an extension namespace
convention and a conformance checker; longer term, a home (ORX-style consortium
or an ACORD working relationship) — the standards note shows they understand
the licensing boundary, which is a good start.

**L2. Snowflake federation is thinner than advertised.** The federation story
is prominent in README/DESIGN; the Snowflake binding is 7 lines and phase 10
is "deferred". Honest in the roadmap table, oversold in the prose.

**L3. Single-workspace assumptions.** Fixed demo catalog, tag prefix
workarounds, share "pending a metastore grant" — all fine for a demo, all
signals that no second party has actually completed the adoption path. Demo 6
("adopt in five minutes") generates a model tree; it has not yet generated a
second *organisation*.

## 4. Fit likelihood for my case

**60% as it stands, as a base — conditions attached.** The spine matches my
book (P&C commercial + motor, life, inward re is genuinely unusual and welcome),
the ACORD alignment protects my exit, Apache 2.0 means I own my fork, and the
model-as-code discipline is the thing my programme was missing. The 40%
discount is: coverage (H1) means most of my estate has no target to conform
to yet; the MDM gap (H2) sits exactly on my biggest pain; and I would be
adopting a one-author project as group infrastructure.

**What gets it to 90%:** (1) party/MDM either implemented or honestly
re-scoped with a clean interface; (2) two of billing, distribution/commission,
product delivered under the evolution contract by a second contributor;
(3) the regulatory mapping document with the erasure design note; (4) DQ rules
compiled to executable expectations; (5) one reference adopter — even a
fictional second insurer stood up from the ontology import (their own phase 9)
— completing the exchange loop both ways.

## 5. What I'd need before showing my board

1. A one-page **coverage map**: model domains vs my estate's domains, green/
   amber/absent — I will not let the board discover the billing gap themselves.
2. The **Genie benchmark demo run on a conformed slice of OUR data** (one
   domain, shadow-mode per their own Step 3), with the pass rate — not the
   synthetic world.
3. The **erasure-vs-immutability design note** — Legal will ask in the first
   ten minutes, and "the transactions are append-only" is currently an answer
   to the opposite question.
4. A costed **operating model proposal**: domain owners named from my org,
   change-board cadence, and what my two FTE data modellers do differently
   under model-as-code.
5. The **maturity workflow exercised once for real**: one entity taken from
   draft to certified with named reviewers, so "certification routes the LLM
   to the right context" is a demonstrated loop, not a slogan.
6. A statement of **maintenance intent** for the upstream project: cadence,
   contribution rules, and what happens to my fork when version 1.0 breaks
   something.

---

*Net: the most convincing embodiment of "governance as code, semantics for
LLMs" I have reviewed — and I have reviewed several this year that were
slideware. It earns the right to be my base. It has not yet earned the right
to be called a standard, a master data solution, or a complete insurance
model, and its own documentation is mostly honest about that, which is
precisely why I'm still at the table.*
