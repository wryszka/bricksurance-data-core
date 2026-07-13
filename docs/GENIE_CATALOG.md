# Genie Catalog — "What genies can we run?"

The literal answer to the client question. Five spaces are **live today** on
the demo estate; the rest are defined here with exactly the data they need,
so standing one up is provisioning, not invention. All spaces are generated
from the model (`tools/create_genie_space.py`) with instructions, examples
and SQL-verified benchmarks; Genie One surfaces the certified ones together.

## Live today

| Genie space | Persona | Answers things like | Backed by |
|---|---|---|---|
| [P&C Book](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17ade46ec18bc8da2cb30b55a26a6) | Underwriting & portfolio | GWP/loss ratio by line, outstanding reserves, broker on a policy, quote conversion | policy/claim domains + `underwriting_metrics` |
| [Reinsurance & Exchange](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17b83371f1d56bba2404ad475e29d) | Ceded re / capacity | Cessions by treaty, bound submissions, modelled-vs-reported event losses, bordereau contents | reinsurance/exchange domains + 2 metric views |
| [Life & Valuations](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17b8339b41106b9f5784f0b2d04a4) | Chief actuary / finance | BEL by product and date, run recipes (assumptions/scenarios/model version), RED-run gate | life/finance domains + `valuation_metrics` |
| [Distribution, Underwriting & Conduct](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17ec37dd71693a552cac8383e1651) | Distribution director / COO / conduct | Funnel by channel (incl. machine agents), agent-vs-human decisions, net commission by broker, complaints & redress, retention | product/distribution/conduct/events domains |
| [Data Governance](https://fevm-lr-serverless-aws-us.cloud.databricks.com/genie/rooms/01f17ec380b415dc94608c7fabfe1bd7) | CDO / privacy office | "Which columns hold PII?", entity definitions, ACORD crosswalk coverage, applied migrations | `data_dictionary` + `schema_migration` |

## Ready to stand up (data exists; space = one config entry)

| Genie space | Persona | Needs |
|---|---|---|
| Exposure & Accumulation | Cat / exposure management | insured_object (geo live), event_loss, cat_event — richer once more objects are geocoded |
| Claims Operations | Claims manager | claim/claim_transaction + business_event (FNOL→payment cycle times) |
| Finance Close | CFO office | valuation_result + premium/claim transactions + schema_migration (close audit) |

## Needs data first (the provisioning backlog, honestly)

| Genie space | Persona | Missing |
|---|---|---|
| Customer 360 | Service / CMO | contact points, consent & preferences, household/corporate hierarchy |
| Fraud & SIU | SIU lead | fraud signals/network entities (pattern exists in the claims workbench) |
| Consumer Duty Outcomes | Board conduct | outcome measures beyond complaints (fair-value metrics per product) |
| Expense & Combined Ratio | CUO/CFO | expense allocation + earning patterns |
| Sanctions & Financial Crime | Compliance | screening results entities |
| People/Operations | COO | out of scope for the core by design |

## Rules every space follows

30-table hard limit per space · label + code dimension pairs · currency
discipline in every money answer · benchmarks stored as SQL ground truths and
re-run after model changes (they are the semantic regression tests) · the
dictionary is always included, so "what does X mean" works everywhere.
