# Agent Playbook — "Can an agent do X?"

How any agentic ask decomposes into this foundation's primitives, and what
already runs. The company goal in one line: **make insurance data and context
available to LLM agents, and prove the difference.**

## The action layer

Agents don't just read here — the ontology declares what they may DO.
`kind: function` specs compile to Unity Catalog functions: typed, documented,
classification-aware, versioned with the model. Live today:

| Governed tool | What it does |
|---|---|
| `fn_appetite_check(lob, country, sum_insured)` | Evaluates the live appetite rules; returns effect + the rule's business description |
| `fn_indicative_quote(product_code, sum_insured)` | Indicative premium from the product's declared base rate |
| `fn_policy_snapshot(policy_number)` | One-line policy state |
| `fn_claim_status(claim_number)` / `fn_outstanding_reserve(claim_number)` | Claim state; reserve derived live from movements |
| `fn_cession_trace(policy_number)` | Which treaties, what shares |
| `fn_define(term)` | The model explains itself from the dictionary |

`tools/agent_demo.py` wires Claude to these tools straight from the specs —
no per-agent glue. **The agentic-buyer scenario runs live**: a MACHINE_AGENT
party ("Athena Procurement Agent") requests £8m warehouse cover; the agent
checks appetite (WITHIN), quotes indicatively (112,000), answers claim and
definition questions — every figure from a governed tool, every decision
recorded in `underwriting_decision` with `decided_by_agent = true`, audited
identically to a human underwriter.

## The six shapes of any client ask

| Client asks... | Decomposes into | Status |
|---|---|---|
| "What can I ask?" | [GENIE_CATALOG.md](GENIE_CATALOG.md) — 5 live spaces + defined backlog | live |
| "Can an agent do X?" | function specs + the tool loop above | live (7 tools) |
| "Does it handle my process?" | product / appetite_rule / underwriting_decision / business_event — process state as data | live for underwriting; claims workflow next |
| "Does it handle my data kind?" | documents (+ vector index), events stream, geo on objects, transactions everywhere | live thin slices |
| "Can it talk to Y?" | exchange domain + Delta Sharing + the dictionary that travels + ontology import for adopters | bordereau live; Re share pending grant |
| "Will it survive my reality?" | evolution contract + migration planner + log, CDO review gaps as graded backlog | process live; scale/MDM on backlog |

## Worked example — "make underwriting work with agentic buyers"

1. **Identity**: the buyer agent is a `MACHINE_AGENT` party with a
   `BUYER_AGENT` role on its quotes — a governed counterparty, not an API key.
2. **Discovery**: the agent reads `product`, `underwriting_question` and
   `appetite_rule` — the product is machine-readable by construction.
3. **Negotiation**: `fn_appetite_check` + `fn_indicative_quote` — the same
   rules a human underwriter reads.
4. **Decision**: recorded in `underwriting_decision` citing the rule, flagged
   agent-decided, feeding the same funnel metrics and audit as everything else.
5. **Bind**: the quote converts; premium, commission, events and reinsurance
   all flow because it is one world.
   
Demo it: `uv run --with databricks-sdk,pyyaml tools/agent_demo.py` and then
ask the Distribution Genie "which quotes came from machine buyer agents and
what was decided?"

## Assembly estimates for new asks

New Genie space over existing data: **~1 hour** (config entry + benchmarks).
New governed tool over existing entities: **~1-2 hours** (spec + regenerate +
deploy). New entity/domain + world data: **half a day to a day** (specs,
engine section, smoke checks). New exchange counterparty: **~half a day**
(share config or open-sharing recipient). New unstructured corpus: **~half a
day** (documents + index sync). The primitives compose; the ask decomposes.
