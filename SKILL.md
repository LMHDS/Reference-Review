---
name: reference-verification
description: Audit an existing reference list or discover papers from topic keywords. Check paper identity against external sources, compare bibliographic metadata, preview citation formats, and provide keywords with provenance. Use for reference checking or verified literature discovery.
---

# Reference verification

Support exactly two entry points:

1. **Reference list → audit:** preserve the supplied entries and citation keys; check paper existence/identity, metadata and versions, duplicate candidates, citation formatting, and keywords.
2. **Topic keywords → discover:** search external sources, select relevant candidate papers, and provide the same identity evidence, citation previews, and keyword output.

Both produce a bibliography review page. Do not add manuscript interpretation, sentence-to-source support checks, or full-text reading requirements to this workflow.

## Shared result per paper

- Identity status with original-source link, retrieval time, selected version, and unresolved discrepancies.
- Original versus proposed title, ordered author names, date, venue/edition, and identifier.
- A readable formatted citation plus BibTeX preview **before** human review.
- A short keyword list with provenance: source-provided terms or agent-inferred title/abstract terms. Show supplied keywords separately when present and explain meaningful mismatches.
- Duplicate/version candidates and source coverage limits. A failed lookup is unresolved evidence, not proof of fabrication.

## Execute

Read [commands](references/commands.md) for the CLI and [evidence](references/evidence.md) for records and decisions. [Providers](references/providers.md) describes supported services.

1. Parse BibTeX/RIS/CSL JSON with `citations.cjs`; preserve raw pasted references when extracting fields. DOI/arXiv/text lists can go directly to `audit.py audit`. Do not silently merge editions or delete duplicates.
2. For a topic, use `discover` with relevant search terms. Keep the query and selection rationale. Results are candidates, not a systematic or exhaustive literature review. Review relevance using the title/abstract; do not invent findings.
3. Resolve identifiers or match title/author/year against primary records. Built-in Crossref/arXiv providers are helpers, not universal registries. Title search selects no candidate automatically. Inspect a publisher/proceedings/arXiv page, then `enrich` with the selected candidate and matching reason. Preserve disagreements and source failures.
4. Check metadata and version choice. A preprint's submission year can differ from a proceedings year. Preserve the input key. Never invent venue, page range, author, DOI, or missing date. Source full names may need given/family segmentation before rendering; check the split instead of treating personal names as organizations.
5. Provide 3–6 useful topical keywords where evidence permits. Exact author/source terms use `source_keywords`; suggestions based on title/abstract use `agent_title_abstract`. Record a source URL and explain the basis. The CLI's `title_terms` fallback is lexical extraction only, not author keywords or a relevance verdict. If supplied terms are unsupported, retain them in the original record and explain a proposed correction.
6. Render the review page; it generates APA and BibTeX previews with Citation.js before approval. Default output is BibTeX with an APA readability preview. A user-specified CSL style can be rendered separately and reviewed before use; do not call APA another venue's style. Show unresolved fields and duplicate flags alongside the preview.
7. Human review covers bibliography identity/metadata, formatting, and keyword origin only. The user can approve, request correction, choose another paper, or exclude. Do not operate approval controls for the user. Corrections are requests for a new sourced record/review, not approval of unseen edits.
8. Merge downloaded decisions and export approved CSL/BibTeX. Retain the audit and keyword provenance. Any metadata, keyword, source, or version change invalidates the old decision. Candidate previews can be delivered immediately; they are not approved exports.

Prepare a concrete reviewable result before asking for human input. If the user has explicitly approved named entries in chat, transcribe the actual decision with reviewer, time, scope, and current evidence hash; otherwise leave it pending.

## Scope and installation

This is bibliography assistance, not a certificate of research quality or a venue-policy audit. Limited registry notice checks may flag corrections/retractions; no notice found is not an integrity guarantee. No full-text reading is needed for the standard workflow.

Install local Node dependencies with `npm ci --ignore-scripts`; Python uses the standard library. Keep runs in a writable project directory. If global skill installation is unavailable, deliver/invoke this folder in the authorized workspace. Schema v2 deliberately rejects older claim-review audits; preserve old files and start a new run rather than silently converting prior decisions.
