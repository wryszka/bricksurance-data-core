# Genie Room Map — every natural place for a Genie room, with a data verdict

The question behind this doc: *across a whole insurer, where would you
naturally put a Genie room, and do we have the data to stand each one up?*
The answer is the map below. **Eight spaces are live today**; the rest are
scoped with the exact data they need, so each is a provisioning step, not an
open question. Genie One surfaces the certified spaces as one front door; an
agent supervisor can orchestrate them as tools.

Every space obeys the same rules: ≤30 tables, label+code dimension pairs,
currency discipline, SQL-verified benchmarks, the data dictionary always
included so "what does X mean" works everywhere. New datasets slot into an
existing space (up to 30 tables) or spawn a new one — the estate is built to
expand.

## Live today (8)

| Room | Persona / where it sits | Data verdict |
|---|---|---|
| **P&C Book** | Underwriting, portfolio, pricing | ✅ policy/claim domains, underwriting + performance metric views, fraud signals |
| **Reinsurance & Exchange** | Ceded re, capacity, exchange | ✅ submissions, treaties/layers, cessions, cat events, bordereaux |
| **Life & Valuations** | Chief actuary, life finance | ✅ model points, assumption/scenario sets, valuation runs, BEL |
| **Distribution, Underwriting & Conduct** | Distribution director, COO, conduct | ✅ products, appetite, quote funnel (incl. machine agents), commissions, complaints, events |
| **Customer & Privacy** | Service, CMO, privacy office | ✅ parties, contacts, consents, DSARs, receivables |
| **Finance & Controllership** | Financial controller, FP&A | ✅ ledger (balances), statements, receivables/expense/tax, budget — solo & group |
| **Capital, Investments & IFRS 17** | Group CRO/CFO, investments | ✅ SCR/MCR/own funds solo+group, investment portfolio, CSM roll-forward |
| **Data Governance** | CDO, privacy office | ✅ data dictionary, schema-migration history |

## Ready to stand up (data exists; one config entry)

| Room | Persona | Uses |
|---|---|---|
| **Claims Operations** | Claims director | claim + claim_transaction + business_event (FNOL→payment cycle) |
| **Exposure & Accumulation** | Cat/exposure mgmt | insured_object (lat/long), event_loss, cat_event |
| **Group Regulatory Reporting** | SII reporting | valuation_result + legal_entity + reporting_level (solo/group split) |
| **Investment & ALM** (solo) | CIO / treasury | investment_metrics filtered per legal entity |
| **New-business Pricing** | Pricing actuary | quote + product + appetite_rule + underwriting_decision |

## Needs data first (named backlog)

| Room | Persona | Missing entity/domain |
|---|---|---|
| Reserving & Triangles | Reserving actuary | reserving-triangle view (derivable from claim_transaction) |
| Sanctions & Financial Crime | Compliance | screening-result entities |
| Consumer Duty Outcomes | Board conduct | fair-value / outcome metrics beyond complaints |
| HR / Operations | COO / people | out of scope for the core by design |
| Claims Supply Chain | Claims ops | repairer/supplier network entities |

## How this stays expandable

- A new dataset that fits a theme joins that room's object list (until 30).
- A new business area gets its own room via one `spaces_config` entry in
  `tools/create_genie_space.py` — instructions, examples and benchmarks are
  generated; the dictionary and label-resolution rule come for free.
- Because every room reads the same governed model, a fact added once
  (e.g. a new metric view) is answerable in every room that includes it — no
  per-room data engineering.
