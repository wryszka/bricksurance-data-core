# Tagging Strategy

How the model uses Unity Catalog tags, what belongs in tags versus the data
dictionary, and what we recommend an adopter does in their first 90 days.

## 1. Principles

1. **Tags are generated, never hand-set.** Every tag comes from the specs via
   the generator. A hand-set tag is drift waiting to happen; if a fact is
   worth tagging, it is worth putting in the spec.
2. **Tags are for machines and filters; the dictionary is for meaning.**
   Tags answer "find me everything that is X" (discovery, policy binding,
   cost attribution). Definitions, grains and crosswalks live in column
   comments and the `data_dictionary` table — prose does not belong in tags.
3. **Namespace everything.** All model tags carry a binding-configurable
   prefix (`bxc_` here). Enterprises govern tag keys centrally (this demo
   workspace reserves `domain`, which we discovered the honest way); a
   namespaced key never collides with an organisation's governed tag
   policies, and an adopter sets their own prefix in one line of the binding.

## 2. The taxonomy

| Tag (prefixed) | Level | Values | Drives |
|---|---|---|---|
| `bxc_model` | table | model name | Estate discovery: everything this model owns |
| `bxc_model_version` | table | semver | Version audit; pairs with the `schema_migration` log |
| `bxc_domain` | table | reference / party / policy / claim / reinsurance / life / finance / exchange / semantics | Domain browsing, ownership routing |
| `bxc_maturity` | table | draft / stable / certified | Trust signalling; certification workflow |
| `bxc_acord_ref` | table | ACORD element name | Standards crosswalk at a glance |
| `bxc_classification` | column | public / internal / confidential / pii | Masking policies, access reviews, GDPR mapping |

## 3. Classification is the workhorse

Every attribute in the specs declares a classification; the generator turns it
into a column tag. That single pipeline is what makes the following cheap:

- **Masking/ABAC**: bind masking policies to `bxc_classification = 'pii'`
  rather than to column lists that rot. New PII columns arrive pre-tagged.
- **Access reviews**: "show me every PII column and who can read it" is one
  query over `information_schema` + tags.
- **GDPR/DPIA support**: the dictionary + classification tags are, in
  practice, the data inventory a privacy office keeps asking for.

## 4. What deliberately does NOT go in tags

- Definitions and grains (comments + dictionary — semantics travel with
  shares; tags do not cross share boundaries).
- Lineage (Unity Catalog captures it automatically).
- Environment/deployment facts (the migration log and bindings own those).
- Anything a human writes ad hoc — see principle 1.

## 5. Certification

`bxc_maturity` is the model's own signal (an entity graduates draft → stable →
certified as its definitions are reviewed by the owning domain). Pair it with
the platform's native certification affordances where available so certified
metric views and Genie spaces are visibly trusted — Genie One prefers
certified assets, which closes the loop: **certification is what routes the
LLM to the right context.**

## 6. Adopter's first 90 days

1. Pick your prefix; if you have governed tag policies, register the model's
   keys and allowed values with them (weeks 1–2).
2. Adopt `classification` end-to-end first — it pays for itself fastest
   (masking + reviews) and forces the useful arguments about what is
   actually PII (weeks 2–6).
3. Wire `maturity` into your certification/stewardship workflow — who
   promotes an entity, on what evidence (weeks 6–12).
4. Only then extend the taxonomy (cost centre, retention class, source
   criticality...) — additively, per the evolution contract.
