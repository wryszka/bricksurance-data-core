# "One Number" — the insurance context demo

> Audience: C-suite and actuaries, not engineers. One question, one number,
> one screen per beat. Richness on pull ("Explore"), never pushed.
> Built on the Bricksurance Data Core (serverless workspace).

## The pain we start from (what they struggle with today)

The CEO asks a simple question before the board meeting:
**"What is our Commercial Property loss ratio this year?"**

Today three teams answer, and all three are "right":

| Team | What they count | Basis |
|---|---|---|
| Finance | claims paid so far | over written premium |
| Underwriting | paid + case reserves | over written premium |
| Actuarial | paid + case + IBNR (+ ALAE for long-tail) | over earned premium |

Three numbers, a reconciliation meeting, and nobody trusts the AI pilot
because it gives a fourth number with total confidence.

## The track (6 beats, ~8 minutes)

1. **The question.** The CEO's question, and the three answers teams give today,
   side by side. Message: *the problem isn't data, it's agreement.*
2. **Ask the AI, no context.** Genie on raw tables. It answers confidently, and
   we show in plain English what it actually counted. Message: *AI without your
   definitions is a confident guesser.*
3. **Give it the rulebook.** Three cards, each something a business person
   already recognises:
   - **The industry dictionary**: ACORD terms (what "policy", "claim" and
     "earned premium" mean), already standard.
   - **Our definition page**: the loss-ratio definition by line of business,
     written and signed off by the Chief Actuary. It's the page that exists in
     every reserving manual today.
   - **One outside source**: who the client really is (Dun & Bradstreet-style
     company data: industry, size, financial risk), joined by company ID.
4. **Ask again.** The same question gets the right number. Genie states the
   basis, shows the definition it used, and who approved it. Follow-up only
   possible with the outside data: *"…for manufacturing clients over £50m
   revenue?"*
5. **Change the rule.** The Chief Actuary includes ALAE for long-tail lines,
   then approves (maker/checker). The number updates everywhere at once, with an
   audit trail. Message: *the business owns the meaning, not IT.*
6. **How you get here.** The ladder, with each step taking weeks rather than
   years:
   1. Write down the definitions you already have (your Excel glossary).
   2. Put them next to the data.
   3. Point the AI assistant at them.
   4. Bring in one outside source.
   5. Govern the changes.
   For each step: who does it, roughly how long, and what you get.

## Rules for the build
- Every screen has a "What am I seeing / why it matters" explainer and an
  "About this demo" disclaimer (all data is synthetic).
- Numbers are always computed live from the data core. Never hard-coded.
- Genie runs live, with a verified cached answer as a fallback so the room
  never waits.
- No product names on the main track. Product names (Unity Catalog, metric
  views, Genie) appear only under "Explore → how it works".
- The definitions page is our own wording in the style of actuarial syllabi,
  not copied exam material.

## Build pieces
1. Model: new entity `enrichment.business_firmographics` (DUNS-style company ID,
   industry, revenue band, employees, financial-stress score) plus world-engine
   rows for commercial parties.
2. Content: a loss-ratio definition page (by line of business, short- vs
   long-tail, components) loaded as a governed document and versioned
   definition rows.
3. Semantics: loss-ratio definition variants as governed definitions, plus a
   metric view that is republished on approval.
4. Genie: a "no context" space (raw tables, no instructions) and the governed
   space, both called live from the app with cached fallbacks.
5. App: a new guided route in the Data Core Console (`#/one-number`) with the
   6 beats, the edit-and-approve panel, and the ladder.

## Status: built and live (2026-10-06)

- **App:** Data Core Console, route `#/one-number`:
  https://data-core-console-7474659673789953.aws.databricksapps.com/#/one-number
- **Genie, no context:** `01f1c1a0a1e01f179ab9237da5ba42ee`. Raw policy, premium,
  claim and party tables only.
- **Genie, governed:** `01f1c1a0a23816179ff3850103e0fe6e`. Metric view, rulebook
  and firmographics. Its instructions are rewritten on every approval.
- **Objects (`lr_serverless_aws_us_catalog`):**
  - `bricksurance_semantics.loss_ratio_components` (view)
  - `.loss_ratio_definition` (the rulebook)
  - `.loss_ratio_metrics` (metric view, owned by the app's service principal)
  - `bricksurance_enrichment.business_firmographics`
- **Code:**
  - `app/backend/one_number.py` (all logic and API)
  - `app/frontend/src/views/OneNumberView.tsx`
  - `tools/one_number_setup.py` (first-time setup)
  - Saved answers: `app/backend/data/one_number_cache.json`

### Verified numbers (Commercial Property, GBP, whole book)
| | Value |
|---|---|
| Finance view (paid / written) | 45.4% |
| Underwriting view (paid + case - recoveries / written) | 55.1% |
| Actuarial view (ultimate incl. ALAE / earned) | 70.9% |
| Company v1 (paid + case + IBNR - recoveries / earned) | **66.6%** |
| Company v2 (v1 + ALAE) | **70.9%** (lands on the Actuarial view) |
| AI with no context, 3 live attempts | "no answer", "no answer", 54.1% (mixed CHF/EUR/GBP/USD, labelled $) |
| AI with the rulebook, 3 live attempts | 66.6% x3, then 70.9% x3 after approval |
| Clients under financial stress vs the rest (v1) | 70.4% vs 38.5% |

### Running it live
1. Before the room: open the app, go to step 6, Explore, and click **Reset the
   demo** (restores v1). Ask once in step 3 to warm the warehouse.
2. Walk the steps with the arrow keys. "Ask it three times" is live: about 30s
   for no context and about 15s governed, with a counter on the button.
   **Show saved answer** gives the verified earlier run instantly if the
   network is slow.
3. Step 6: Submit (as Reserving Manager), try to approve as Reserving Manager
   (blocked: four eyes), approve as Chief Actuary, then "Ask the assistant
   again" shows 70.9% v2.
4. Reset after the session.

### Known limits
- The book is small and synthetic. Aldgate Mills dominates Commercial Property,
  which makes the financial-stress split vivid but concentrated.
- IBNR is line-level, allocated to policies by share of open case reserves.
- The no-context assistant varies run to run by nature. The saved answer is
  the documented run.
