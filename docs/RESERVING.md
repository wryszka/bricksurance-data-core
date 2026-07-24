# Reserving — the spreadsheet workflow, done on the platform

*Bricksurance SE is fictional; all data is synthetic.*

## The point

Actuarial reserving is one of the last strongholds of the spreadsheet. Triangles
are pasted into Excel, development factors are typed into cells, methods are
locked in formulas, and the reserve that goes to the regulator depends on one
analyst's workbook that nobody else can reproduce.

This demo does the **same workflow on the data platform** — and shows why that's
better. Excel is not the hero here. It is the frontend the actuarial team is
trying to leave. We show it only to name what it costs.

## Excel as the frontend you're leaving

The failure modes are the ones Anthropic's own reserving example calls out — and
they are structural, not carelessness:

| The spreadsheet | Why it hurts | On the platform |
|---|---|---|
| Triangle pasted in | Drifts from the claims system the moment a claim moves | `reserving.loss_development` is a **view** over `claim.claim_transaction` — reconciles to the penny, always current |
| Hard-coded factor (`Triangles!K47 = 0.987`) | A silent override understates reserves by millions | Factors are **computed** from the triangle in the notebook — nowhere to hide one |
| Method locked in formulas | Changing basis means rebuilding the sheet | Method is a **swappable, recorded choice** — chain-ladder ↔ Bornhuetter-Ferguson, re-run and compare |
| Wrong column reference | Off by hundreds of thousands, invisibly | The triangle is generated from the model; references can't rot |
| No audit trail | "Who set these reserves, on what basis?" — nobody knows | Every run writes a **dated attestation**; IBNR ties to `finance.valuation_result` |
| One analyst's laptop | Not reproducible, not shareable, not queryable | Governed in Unity Catalog, runnable by anyone with access, **answerable in Genie** |

If a customer wants Excel to stay as a *reading* surface, it still can — through
the Databricks connector, Excel reads these governed tables with Unity Catalog
permissions enforced. But the truth, the method and the audit trail live on the
platform, not in the file.

## What's in the reserving domain

Generated from the model like everything else (`model/reserving/`):

- **`loss_development`** (view) — the loss-development triangle: incremental and
  cumulative paid and incurred by accident year and development lag, derived by
  summation over claim transactions. Never stored.
- **`reserving_metrics`** (metric view, certified, owned by the Chief Actuary) —
  `paid_to_date`, `incurred_to_date`, `paid_ratio` by accident year, development
  lag and line of business, via `MEASURE()`.
- **`reserve_estimate`** (table) — the published result: ultimate loss, IBNR,
  case reserves and outstanding by accident year, line of business and **method**.
  One row per method, so chain-ladder and BF sit side by side; the quality rules
  enforce that paid + case + IBNR reconciles to ultimate and that ultimate never
  falls below paid.
- **`reference.reserving_method`** (code set) — chain-ladder, Bornhuetter-Ferguson,
  expected-loss-ratio, Cape Cod. The method is governed vocabulary, not a comment.

## The run

`notebooks/reserving_run.py` is the platform-native workflow, the Genie Code
equivalent of the Excel reserving sheet:

1. Read the governed triangle (`loss_development`).
2. Compute chain-ladder development factors from the triangle.
3. Project ultimates two ways — chain-ladder and Bornhuetter-Ferguson — side by side.
4. Produce the reserve walk and the exception checks a reviewer runs before sign-off.
5. Publish `reserve_estimate` and record a **dated attestation** of the method choice.
6. The same figures are then answerable in the **Reserving** Genie space in plain English.

Change the line of business, currency, a-priori loss ratio, or the chosen method
at the top and re-run — nothing downstream is hard-coded. Swap the method and a
new `reserve_estimate` row appears alongside the old one; the attestation records
which basis set the reserves and who signed off.

## Ask it in Genie (Reserving space)

- *"What is our paid-to-incurred ratio by accident year for commercial property in GBP?"*
- *"Total IBNR across accident years for commercial property, chain-ladder basis?"*
- *"Chain-ladder vs Bornhuetter-Ferguson ultimate for motor?"*
- *"Which method set the current reserves, and who signed off?"*

## When someone is amazed by the Claude-for-Excel reserving demo

Meet them there first — it *is* a great demo. The actuary stays in Excel, Claude
reads the workbook, flags the hard-coded development factor, drafts the ASOP
filing narrative. Say so: "Yes — that's exactly the assistant an actuary wants."
Then move the conversation from *the analyst* to *the system of record*.

| Their demo | This platform |
|---|---|
| Claude **validates** the triangle in the sheet | The triangle **is** a view over claim transactions — it reconciles to the claims ledger to the penny, live. Hard-coded factors aren't caught; they're **impossible** — there's nowhere to type one. |
| Output lives in one analyst's workbook | The IBNR, method and ultimate are a **governed asset in Unity Catalog** — one definition, read by finance, Genie and BI alike. |
| Audit trail = clickable cell references | **Who chose chain-ladder vs BF, when, on what evidence** is a dated attestation; lineage runs ultimate → triangle → raw claim movements; UC permissions enforced. Auditor-reproducible. |
| Switching method = rebuilding the sheet | Method is a **toggle**; both bases sit side by side in the data; the change is recorded. |
| A reserving assistant, in Excel | Reserving as **one domain on a shared insurance semantic layer** — same governance as pricing, claims, Solvency II, IFRS 17. |

**Be honest about where theirs wins:** the last mile *inside Excel* — the actuary
never leaves the tool, and the Word narrative drafting is slick. Don't pretend to
replace that. The line that turns it from us-vs-them into an easy yes:

> "Keep Claude in Excel if your team loves it — point it at **our** governed
> tables through the Databricks connector. Now the spreadsheet reads from a
> number that can't drift, with the audit trail underneath. We don't kill Excel;
> we give it a spine."

## The strongest angle: data flows in, and back out, effortlessly

A spreadsheet is a **terminus**. Data goes in, a number comes out, and it dies in
the file — to reuse it, someone re-keys it, re-pastes it, re-reconciles it. Every
onward use is a fresh copy and a fresh chance to drift.

On the layer, reserving is a **junction**, not an endpoint:

- **In, effortlessly.** The triangle isn't loaded — it *is* the claim movements,
  summed. A new claim booked this morning is in the triangle with no ETL, no
  paste, no refresh job. The same discipline runs at the boundary: a coverholder's
  messy bordereau maps itself against the model on arrival (the exchange domain),
  so third-party claims land governed, not in an inbox.
- **Out, effortlessly.** The IBNR the actuary just set is the *same* IBNR that:
  posts to the **finance close** (it ties to `finance.valuation_result`); travels
  to the **reinsurer** in a Delta Share that carries its own definitions, so the
  cedant and reinsurer reserve off one agreed number without a reconciliation
  call; answers in **Genie** in plain English; and feeds **capital and IFRS 17**
  without a single re-key. One number, many consumers, meaning intact at every hop.

That is the thing the spreadsheet can never do and the Excel-assistant demo never
claims: the output of reserving is **immediately, governed-ly reusable** by the
next function, and the input arrives the same way. The reserve stops being a
deliverable someone emails and becomes a live part of the estate.

> "Their demo makes the number inside the file better. Ours makes the number
> flow — the claims flow *in* with no ETL, and the reserve flows *out* to finance,
> to the reinsurer, to Genie, to capital, with its meaning intact and nobody
> re-keying it. The spreadsheet is where data goes to stop. The layer is where it
> keeps moving."

## The line to land

> The spreadsheet gave one analyst a number. The platform gives the whole team
> the number, the method, the lineage and the audit trail — reconciling to the
> claims system by construction, answerable in plain English, and reusable by
> every downstream function without a re-key. Reserving stops being a workbook
> and becomes part of the governed data estate.
