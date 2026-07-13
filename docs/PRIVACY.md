# Privacy & Erasure Design

How the model answers GDPR's hardest structural question — the right to
erasure against immutable, auditable transactions — plus the artifacts a
privacy office needs day to day.

## 1. The design principle: PII anchors, surrogate history

PII is deliberately **concentrated** in two places: `party` (name, country)
and `contact_point` (email, phone, address) — plus a handful of declared
columns elsewhere (`vehicle.registration_number`, reported insured names on
inbound bordereau lines). Everything transactional — policies, claims,
payments, decisions — references parties only by **surrogate key**.

**Erasure therefore never touches history.** Executing an ERASURE request
means redacting the anchors: overwrite `party.name` with `ERASED-<hash>`,
delete/blank the party's `contact_point` rows, and redact declared PII
columns for that subject. Every transaction, reserve movement, audit row and
ledger posting survives intact, still keyed to the (now meaningless)
surrogate — the actuarial and accounting record is preserved, the person is
gone. A stronger variant (crypto-shredding: encrypt anchors per-subject,
erase the key) drops in without model change.

## 2. Where legal bases beat erasure

Erasure is not absolute: claims files under litigation, records retained
under regulatory minimums, and fraud-relevant data are retained on legal
grounds. That is why `data_subject_request` carries a REFUSED status with
grounds in `notes` — a refusal is an auditable outcome, not a gap.

## 3. The privacy office's standing questions, answered from the model

| Question | Answer surface |
|---|---|
| What personal data do we hold, where? | `data_dictionary` filtered to `classification = 'pii'` (the Governance Genie answers this in one line) |
| Under what consents? | `consent` per party per purpose, withdrawal timestamps intact |
| Who asked for what, and did we respond in time? | `data_subject_request` against `received_date` |
| What left the company? | Delta Sharing is governed and revocable; every share carries the dictionary, and share revocation is the recall mechanism for exchanged PII |
| Is any of this hand-maintained? | No — classifications are declared in specs and generated as tags, comments and dictionary rows |

## 4. What this is not (yet)

Not legal advice; not a full RoPA (purposes exist on consent, processing
activities register is a documentation exercise on top of the dictionary);
retention schedules per entity are declared nowhere yet — a natural next
`retention_class` tag in the taxonomy. Pseudonymisation of `party_role`
context joins for analytics users is achievable today with UC column masks
bound to the classification tags ([TAGGING.md](TAGGING.md)).
