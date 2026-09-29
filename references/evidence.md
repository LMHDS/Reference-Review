# Evidence and decisions

## Audit record

Top level: `schema_version: 1`, unique `run_id`, `created_at`, `mode`, optional original document/query, and `entries`.

An entry has:

- `id`: stable input citation key; never reuse a key for another paper silently.
- `original`: original structured input and/or raw reference text.
- `candidates`: source-backed candidate records. Each contains `csl`, `source` (`provider`, `url`, `retrieved_at`, optional response `sha256`/snapshot), and version/relationship information where available.
- `selected`: candidate index or null. A selection is a proposal, not human approval.
- `identity`: `identifier_resolved`, `source_record`, `candidates_only`, `evidence_matched`, `unresolved`, or `lookup_error`, with the actual reason.
- `metadata_diff`: per-field input/source values and `matches`, `differs`, `missing_in_input`, `not_in_source`. Text normalization is conservative and does not equate author abbreviations with complete author lists.
- `integrity`: `not_checked`, `no_notice_found`, `notice_found`, or `lookup_error`; scope, check time, source evidence and limitations. No global `clean` flag.
- `claims`: one record for every claim/source pair, containing exact sentence, manuscript location, assessment, short source evidence and limitations. Each evidence item must have URL, locator, excerpt, retrieval time; source version is strongly preferred.
- `extra_sources`: additional actually inspected primary sources for metadata/corroboration. Search engines are discovery tools, not independent publisher records. Crossref/OpenAlex/S2 may share upstream metadata, so two API responses do not guarantee independent evidence.
- `duplicate_of`: tentative duplicate/version flags. They never remove records automatically.
- `formatting`: missing basic fields and rendering status. Do not fill missing fields with invented values.
- `human`: pending until explicit human action.
- `evidence_hash`: deterministic hash over the entry excluding `human` and the hash itself. It binds original input, selected metadata, source evidence, claims, and caveats.

## Claim decisions

`supported` means the inspected evidence supports the exact wording and scope, including conditions, metrics, comparison baseline, population and version. It remains an AI assessment pending human check.

`partial` means there is related evidence but a material qualification is omitted or scope is broader. Suggest narrower wording; do not replace the stored manuscript sentence until the user requests/accepts that change.

`contradicted` needs a specific incompatible statement/result, not just failure to locate support.

`not_found` records that a specified search did not find support. `full_text_unavailable` means the needed text could not be read. Neither means fake paper.

`human_supported` is used only after the user supplies/identifies missing supporting evidence. Record that evidence, regenerate the review card, and obtain approval for its new hash. Do not use this status as an AI override.

When sources disagree, preserve both and describe the disagreement. Version-specific table values, correction notices, rejection sampling, precision/recall settings, and evaluation scope are examples of conditions that change a claim.

## Human decision contract

`human_decisions.json` contains `schema_version: 1`, `run_id`, and `decisions` with:

```json
{
  "id": "existing-citation-key",
  "decision": "approve",
  "evidence_hash": "hash copied by the UI",
  "reviewer": "actual reviewer",
  "reviewed_at": "actual ISO timestamp",
  "scope": "metadata",
  "identity_checked": true,
  "metadata_checked": true,
  "limitations_acknowledged": true,
  "claims_checked": false,
  "confirmed_claim_ids": [],
  "note": "Optional except for unresolved notices, missing fields, or duplicate/version disposition"
}
```

Actions: `approve`, `rewrite`, `replace`, `reject`, `pending`. Non-approval dispositions need a reason. Attached claims force claim scope; every claim must have located evidence, a supported assessment and explicit human confirmation. Metadata-only approval cannot be presented as permission for an unspecified manuscript sentence.

Notice-bearing references can legitimately be cited (for example, in a discussion of a retraction). Keep the notice and require written human disposition; approval is not removal of the notice. Missing core metadata or intentional duplicates likewise require a written explanation.

Changing metadata, source evidence, claim wording, version or caveats invalidates old decisions. `enrich` resets affected approvals. `merge` rejects mismatched runs/hashes; `export` validates the gate again. This protects against accidental stale decisions, not malicious edits by someone controlling all local files.

## Agent-to-human handoff

Prepare all accessible evidence before asking for review. If something is inaccessible, disclose the exact gap in the card and continue preparing other items. Do not ask the human to approve an unseen future correction.

For a user reply in chat, map it only to the named records and current wording/version. “Please check these papers” is permission to audit, not human approval. “Approve the metadata for refs A and B as shown” is an explicit metadata decision. “Rewrite that claim” requests revision and a new review, not approval of the revision.
