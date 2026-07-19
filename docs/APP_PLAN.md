# Data Core Atlas — plan

*A search-first explainer + lineage app over the Bricksurance Data Core semantic
model. Merges into and supersedes the existing "Data Core Console" Databricks App.
Synthesized from three persona reviews (SA, insurance data-governance lead, AE)
and a direct audit of the ontology.*

---

## 1. The one-sentence job

Type a business term — `loss ratio` — and instantly see everything that makes it
real: the plain-English definition (with its honest caveat), who owns it, the
exact metric SQL, the datasets and code sets that feed it, a focused lineage
graph, and a one-click "ask this in Genie" that returns the reconciling
number — **proving the catalog, the semantic layer and the AI cannot disagree,
because they're compiled from one file.**

## 2. What the three personas agreed on (the spine)

All three, independently, named the **same** wow moment:

> `loss ratio` → governed definition → focused lineage → **"Ask in Genie"** →
> the certified space returns the number that reconciles to the transactions,
> side-by-side with a bare-tables answer that flails.

Everything else supports that loop. The differences were about framing and depth:

- **AE:** lead with the *business outcome and the reconciling number*, ontology
  second. Role-framed "why this matters to you" (CDO / CFO / Chief Actuary).
  Keep the generator/semver/migration machinery **behind a "for engineers"
  door**. Soften "industry standard" → "ACORD/Lloyd's-**aligned** starting point
  you own." Shareable deep-links + a "what this means for you" leave-behind.
- **SA:** search *is* the product — one box, insurance-synonym-aware, ranked
  mixed results. The metric detail page is the money screen. Never render all
  195 edges — focused subgraph, one-hop expand, "golden thread" as a saved path.
  Deep-linkable everything + export. Genie deep-links are the #1 fragility →
  health check + inline SQL fallback. Keep Exchange/Network reachable from search.
- **Governance:** discovery without a **record layer is just a nicer glossary.**
  The half that survives an audit: named owners, dated certifications, review
  cadence, a classification map that **counts what hasn't been assessed**, and a
  regulatory-lineage view (SCR / CSM / loss-ratio → source tables). The killer
  feature no incumbent can match: a **"propose a change" loop** routed through
  the evolution contract, plus a **provenance stamp** ("generated from spec
  vX.Y.Z, built <date>") on every view.

## 3. Gap response — close the model debt before/with the app

The governance audit is correct (verified against the ontology JSON):

| Gap | State today | Action |
|---|---|---|
| Entity ownership | 0/52 have an owner | **Add an org-role owner to all 52 entities** (domain-owner map: CUO owns policy/product, CFO/Controller own finance, Chief Actuary owns valuation/life, Head of Reinsurance owns reinsurance, CDO owns reference/party/conduct/content, CIO owns investment). Roles, never people. |
| Attribute classification | 202/412 unclassified | **Bulk classification pass** — PII on names/DOB/addresses/registration/contact points, confidential on money/positions, internal default. Drive unclassified toward 0; surface remaining count as an explicit gauge. |
| Certification = tag, not act | 52/52 `draft`, no recorded attestation | **Don't fake it.** Build a real attestation record; run a genuine certification pass only on benchmark-backed metrics + the core P&C entity slice. Surface the honest "N/52 certified" everywhere with a completeness gauge. |
| Standards crosswalk | 18/52 entities | Surface **completeness %** honestly; widen opportunistically, don't fake-fill. |
| Quality rules | 10/52 entities | Same — show the gap as the backlog it is. |

Principle held throughout (from TAGGING.md): **the model's truth stays in the
YAML specs; the app records the human *governance process* around it
(attestations, reviews, disputes, proposals) — never a parallel truth that
drifts.** A certification badge in the app must be backed by a recorded, dated act.

## 4. Information architecture

Reuses the existing FastAPI + React (Vite) Databricks App shell and `db.py`
auth. The ontology JSON ships as a bundled asset → search + lineage are instant
and warehouse-independent; the warehouse is hit only to **prove numbers live**
(metric `MEASURE()` queries) and Genie only for the "ask it" loop.

1. **Home / Search** — big human value prop, live counters as trust, example
   searches, the **before/after money strip**, a **role toggle** (CDO/CFO/Actuary
   one-liners). One universal search box.
2. **Search results** — ranked mixed tiles: metric · entity · business term ·
   code set · function · Genie space. Insurance-synonym-aware (GWP, incurred,
   BEL, combined ratio…). Honest "on the roadmap" tiles for known-but-absent terms.
3. **Metric detail (the money screen)** — definition + caveat + owner +
   certification badge + exact `MEASURE()` SQL (copyable) + clickable source
   tables + ACORD/CDR refs + **"Ask in Genie" deep-link pre-filled with a real
   question** + live "prove the number" result with a **bare-tables vs semantic
   layer** comparison.
4. **Entity detail** — the governed data dictionary, beautifully: attributes,
   types, required, definitions, classification badges, ACORD/CDR, quality rules,
   keys, owner. Embedded focused lineage.
5. **Lineage** — interactive **focused subgraph** (react-flow + dagre), domain
   colouring, certified badges, one-hop expand, and the **"golden thread"**
   (policy → claim → cession → treaty → submission) as a saved one-click path.
   Never all 195 edges at once.
6. **Governance** — ownership board, certification board (honest counts),
   **PII/classification map with completeness gauges**, **regulatory-lineage view**
   (pick Solvency II / IFRS 17 / GDPR → the elements + join graph that serve it),
   review-cadence + attestation record, **"propose a change"** capture.
7. **Exchange** + **Network** — kept (differentiated set pieces), reachable from
   search ("cession" surfaces the exchange + the share).
8. **For engineers** — the machinery behind a labelled door: ontology export,
   install guide, generator, semver/evolution, benchmark pass rate.

Cross-cutting: **deep-linkable URLs** for every view; **copy-to-clipboard** on
every SQL/Genie question; **export** (metric one-pager, domain data-dictionary
CSV, "what this means for you" leave-behind); **provenance stamp** on every view;
mandatory **synthetic-data disclaimer**; **Genie/warehouse health indicator** with
inline-SQL fallback.

## 5. Delivery sequence (build order; highest-value, lowest-risk first)

- **A — Model gap-closing.** Add entity owners; bulk-classify attributes; add the
  attestation/certification concept; regenerate + redeploy; re-run smoke. *(Makes
  the app honest before it exists.)*
- **B — Backend.** Ontology-graph service (search index + synonyms, entity, metric,
  focused-lineage subgraph, governance rollups/gauges); live metric-proving; Genie
  deep-link resolver + health check + SQL fallback; governance-action store.
- **C — Frontend.** Search-first home + before/after + role toggle; results; detail
  pages; focused lineage graph; governance board; keep Exchange/Network; engineers'
  door; deep-links + copy + export; provenance stamp; disclaimer.
- **D — Governance record layer.** Attestation/review/issue capture + "propose a
  change" stub generator (spec-change diff, not auto-PR).
- **E — Harden + ship.** Health/warm, self-review by a "user-persona" agent,
  deploy to dev, smoke, push to `wryszka/bricksurance-data-core`, refresh docs,
  mirror to the Drive "insurance ontology" folder. Decide old-app retirement:
  the 4 old tabs are all **absorbed** (Model→search/entity+governance,
  Numbers→metric-proving, Exchange/Network→kept) — so the old Console is
  superseded in place, nothing standalone to retire.

## 6. Decisions locked after the "acts-as-Laurence" review

- **Name**: **Data Core Atlas**. Update the header brand string; keep "Data Core"
  as the through-line; do **not** rename repo or schema convention.
- **react-flow**: approved. Guardrail — never render all 195 edges; focused
  subgraph + one-hop expand only; the "golden thread" reuses the *exact*
  DEMOS.md path (POL-2026-000001 → claim → cession → treaty TR-QS-PROP-2026 →
  submission), not a new one.
- **"Propose a change"**: v1 is **capture-only** (proposal + spec-diff text shown
  in the governance board). No auto-PR, no write-back — that's v2.
- **Gap-closing stopping rule** (no sprawl): owners on **52/52** (bounded, do it
  fully); classification pass on the **core P&C slice + all obvious PII/money**,
  then surface the honest remaining count — do **not** block on 412/412; real
  dated attestations on **benchmark-backed metrics + core P&C entities only**.
  Gauges always show the *real* count (e.g. "31/52 certified"), never a faked 52/52.
- **Role toggle**: static copy per role. No data filtering, no auth. Framing only.
- **Genie/app URLs**: resolved at runtime from config/binding, **never baked into
  the frontend bundle**. The serverless URLs in DEMOS.md get repointed.

### ⚠️ The one thing needing Laurence's steer — deploy target

Verified live: the Data Core data (all 17 `bricksurance_*` schemas) and the
existing Console app are on **serverless** (`lr_serverless_aws_us_catalog`,
profile `DEFAULT`). The `DEV` catalog has **none** of it. The instruction was
"deploy in dev," and the workbench estate does live on dev — but a Databricks
App can only reach a warehouse/Genie in its **own** workspace, and the Data Core
itself is on serverless today. So:

- **Option A (recommended, lowest risk): deploy Atlas to serverless**, where the
  data + Genie spaces already are. Matches "usual repo/folder"; the live
  prove-the-number and Ask-in-Genie loop works immediately. Contradicts the
  literal "deploy in dev."
- **Option B: migrate the whole Data Core to dev** (generate + world_engine +
  Genie spaces on `DEV`), then deploy Atlas there. Matches "deploy in dev" and
  the estate-consolidation direction, but it's a bigger job and re-homes a
  currently-working estate.

Because search + lineage run off the bundled ontology JSON (warehouse-free), the
app is mostly portable either way — only the live-number + Genie loop is
workspace-bound. **Recommendation: build against serverless (A) so the headline
loop is green, and treat a dev migration as a separate follow-on.** Flagging for
a one-word steer rather than silently choosing.

## 7. Backlog explicitly deferred to v2

Auto-PR from "propose a change"; full 412/412 classification long tail;
crosswalk/quality widening beyond honest %; clickable workbench cross-links
(v1 only *names* the consuming workbench in the regulatory-lineage view); export
polish beyond the metric one-pager + domain CSV.

## 7. Non-negotiables (standing rules)

Synthetic-data / fictional-Bricksurance disclaimer on every screen and export ·
never mirror a recognizable customer estate · Claude via FMAPI (not Llama) ·
real Databricks services surfaced (Genie, metric views, UC functions), nothing
faked · public repo, push after every change · scale-to-zero.
