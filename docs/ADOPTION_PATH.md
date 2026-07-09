# Adoption Path — first steps from old to new

You have policy admin systems, claims platforms, warehouses, spreadsheets and
twenty years of accumulated meaning. This is the incremental path from there
to a governed semantic layer — **no big bang, no re-platforming precondition,
value at every step.** Each step stands alone; stop at any of them and you are
still better off.

## Step 0 — Pick the argument you need to win (week 0)

Choose ONE: LLM answers you can trust · one definition of a contested measure ·
a data exchange that keeps meaning · a regulator-ready data inventory. The
path is the same; the first artifact you build differs. Name the business
owner who will arbitrate definitions — that person, not the platform, is the
critical dependency.

## Step 1 — Import the ontology, deploy STRUCTURE only (weeks 1–2)

Import the ontology JSON ([GETTING_STARTED.md](GETTING_STARTED.md), Path B),
bind it to a **sandbox catalog**, deploy without synthetic data. You now have
the target vocabulary as living tables: definitions, relationships, code
sets, dictionary — something concrete for the business to react to. Reacting
to a concrete model is 10× faster than workshopping a blank page.

## Step 2 — Crosswalk one domain (weeks 2–6)

Pick the domain from step 0 (say, claims). For each source system feeding it,
map source fields → ontology attributes **in a crosswalk table, not in code**:
`(source_system, source_field) → (entity, attribute, transform_note)`. The
dictionary is your contract; the LLM-assisted mapping pattern
(`ingest_bordereau.py`) works as well on your legacy extracts as it does on a
coverholder's spreadsheet — let the model propose, let a human approve.
Where your business genuinely differs from the ontology, **extend it** (new
optional attributes, new codes — MINOR changes under
[EVOLUTION.md](EVOLUTION.md)) rather than bending your meaning to fit.
That is what "use as a base" means.

## Step 3 — Shadow, don't switch (weeks 4–10)

Build conformance views/pipelines that populate the ontology tables **from**
your existing gold layer — read-only, alongside everything that already runs.
Nothing is migrated; nothing can break. Now run the tie-outs: does GWP through
the metric view reconcile to the number finance reports? Where it doesn't,
you have found either a mapping bug or — more valuable — a place where two
departments were never actually using the same definition.

## Step 4 — Point the LLMs at it (weeks 6–12)

Stand up one Genie space over the conformed domain with the generated
instructions; write 5 benchmark questions with SQL ground truths from your
own book. This is the step 0 payoff made visible: questions your analysts ask
weekly, answered correctly, with the definitions on screen. Measure it —
benchmark pass rate is your semantic-layer KPI.

## Step 5 — First real consumers, first real exchange (months 3–6)

- Route ONE report/dashboard through the metric views (retire its private SQL).
- New builds (a new workbench, a new product) start **on** the ontology —
  born conformant is far cheaper than retrofitted.
- If you exchange data with a counterparty who has adopted the same base:
  share the conformed tables **with the dictionary** and retire one
  bordereau. If they haven't: share anyway — the dictionary makes your data
  self-describing, which is a competitive courtesy they will notice.

## Step 6 — Make it the system of definitions (months 6+)

Ownership per domain, changes through the semver/migration process, maturity
tags driving certification, the dictionary as the privacy office's inventory.
Legacy systems keep running — they become *sources with crosswalks* rather
than competing definitions. Decommissioning, where it happens, is a
consequence, never the prerequisite.

## Anti-patterns (we will say this in every meeting)

- **Boiling the ocean**: conforming all domains before any consumer exists.
- **Meaning-bending**: forcing your business into the base ontology instead
  of extending it — the extension mechanism exists precisely so you don't.
- **Hand-tagged governance**: anything humans must remember to do decays;
  generate it or lose it.
- **LLM-last**: leaving Genie/agents until "the data is perfect". Point them
  at each domain as it conforms — they are your best gap-detector.
