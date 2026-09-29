# Bibliography evidence and decisions

Schema version: **2**. Top-level fields: `run_id`, `created_at`, `mode`, optional query/original document, and `entries`. The two product entry points are `audit` and `discover`; acceptance replay is a test mode.

Each entry contains:

- `original`: untouched supplied fields and stable citation key.
- `candidates`: CSL metadata, source provider/URL/retrieval time, and edition/version details.
- `selected`: candidate index or null; selection is not human approval.
- `identity`: `identifier_resolved`, `source_record`, `candidates_only`, `evidence_matched`, `unresolved`, or `lookup_error`, with the actual observed basis. Resolving a DOI proves that record exists, not that the supplied citation describes it correctly.
- `metadata_diff`: original/source comparison; differences remain visible.
- `keywords`: `terms`, `basis`, `source_url`, and `note`. Basis is `source_keywords`, `agent_title_abstract`, `title_terms`, or `unavailable`. Source categories or inferred terms must not be called author-supplied keywords. Keyword provenance is included in the evidence hash.
- `integrity`: limited notice-check coverage and results. Absence of a notice is not a guarantee.
- `duplicate_of`, `extra_sources`, `errors`: retained evidence and unresolved issues.
- `formatting`: missing-field indicators. `render` separately generates a top-level `previews` map containing APA and BibTeX based on the selected metadata and original key; the stored source audit remains unchanged.
- `human`: pending until an explicit user decision.
- `evidence_hash`: hash over the entry excluding `human` and the hash itself. Evidence changes invalidate old decisions.

## Decision file

```json
{
  "schema_version": 2,
  "run_id": "CURRENT_RUN_ID",
  "decisions": [{
    "id": "existing-key",
    "decision": "approve",
    "evidence_hash": "CURRENT_ENTRY_HASH",
    "reviewer": "actual reviewer",
    "reviewed_at": "actual ISO timestamp",
    "scope": "bibliography",
    "identity_checked": true,
    "metadata_checked": true,
    "format_checked": true,
    "keywords_checked": true,
    "limitations_acknowledged": true,
    "note": "Disposition required for retained duplicates, missing core fields or integrity notices."
  }]
}
```

Decisions: `approve`, `revise`, `replace`, `reject`, `pending`. Non-approval actions need a reason. Approving requires a selected sourced record and explicit review of metadata, citation previews and keyword provenance. Keywords are organizational suggestions, not verified scientific findings.

Corrections to metadata, identity, keywords or source evidence require enrichment and a new review. `merge` rejects stale evidence/run IDs; `export` emits only approved records. Formatting can also be used independently; a formatted candidate is not an approved reference.

The review record is self-reported, not authenticated or tamper-proof. No full-text interpretation or manuscript assertion is part of the approval. Older schema-1 decisions cannot be reused as schema-2 bibliography approvals.
