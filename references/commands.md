# Execution

Run commands with the skill directory as the working directory. Outputs are new files; commands refuse to overwrite them. Use a new filename for every audit/enrichment/review revision. Examples use `$RUN` as a task-specific run directory; choose a writable project directory.

```sh
npm ci --ignore-scripts
node scripts/citations.cjs parse references.bib "$RUN/input.json"
python3 scripts/audit.py audit "$RUN/input.json" --cache "$RUN/evidence" --out "$RUN/reference_audit.json"
python3 scripts/audit.py render "$RUN/reference_audit.json" --out "$RUN/human_review.html"
```

The parser uses Citation.js; accepted extensions are `.bib`, `.ris`, `.json`. JSON can be a CSL array or the parser's `{entries, original_document}` wrapper. Python can directly read `.txt` / `.doi` with one full reference or identifier per line. Pasted references are searched as complete bibliographic strings; the helper never assumes a whole formatted citation is a title. Preserve raw text if the agent extracts individual fields.

## Discovery

```sh
python3 scripts/audit.py discover 'visual autoregressive next scale prediction' --provider crossref --limit 8 --cache "$RUN/evidence" --out "$RUN/candidates.json"
python3 scripts/audit.py discover 'ti:"visual autoregressive"' --provider arxiv --limit 8 --cache "$RUN/evidence" --out "$RUN/arxiv_candidates.json"
```

Discovery returns source records with summaries restricted to metadata/abstract. It does not claim relevance, corroboration, integrity checking, or full-text verification. The agent reviews candidates, searches follow-up sources, and uses enrichment for each selected record. To run the built-in integrity lookup on a discovered set, copy candidate original CSL fields into a new input file and run `audit`; retain the discovery query/provenance when enriching the resulting run.

Crossref lookup uses its registry only. For a DOI outside Crossref, use the DOI's registration agency/publisher in the agent workflow; this helper's lookup error is not a nonexistent DOI verdict. `REFCHECK_CONTACT` may optionally be set by the user for a contact User-Agent. Do not invent or expose a personal email.

The cache contains raw API bytes and source hashes. `--offline` explicitly reuses cache and retains its original retrieval time. Online runs fetch anew. Keep different run directories to preserve historic snapshots. The helper uses bounded retries for short rate-limit delays and records other failures per reference.

## Add source evidence / select a candidate / attach claims

Create a patch with the run ID and current entry hash. Only specified entries change. The `claims` array replaces the existing claims for that entry; preserve existing claims intentionally.

```json
{
  "run_id": "COPY_FROM_AUDIT",
  "entries": [{
    "id": "tian2024var",
    "evidence_hash": "COPY_CURRENT_HASH",
    "selected": 0,
    "identity": {"status": "evidence_matched", "reason": "Explain the actual observed match, not a similarity score."},
    "extra_sources": [{"url": "ACTUAL_SOURCE_URL", "retrieved_at": "ACTUAL_UTC_TIMESTAMP", "label": "Publisher / proceedings page", "note": "Fields or version relationship actually confirmed here"}],
    "claims": [{
      "id": "claim-1",
      "text": "Exact manuscript sentence",
      "manuscript_locator": "Related Work paragraph 2",
      "assessment": "partial",
      "evidence": [{"url": "ACTUAL_FULL_TEXT_URL", "retrieved_at": "ACTUAL_UTC_TIMESTAMP", "source_version": "version actually read", "locator": "Table / page / section actually inspected", "excerpt": "Short exact source passage or faithful labeled table-cell transcription"}],
      "limitations": "Explain the missing condition and propose a narrower claim separately."
    }]
  }]
}
```

The example contains descriptive placeholders, not evidence. Substitute only actual inspected sources. Additional/custom providers can supply full `candidates` with CSL fields and a `source` object following the same contract; the agent must inspect each source before adding it.

```sh
python3 scripts/audit.py enrich "$RUN/reference_audit.json" "$RUN/patch.json" --out "$RUN/audit-v2.json"
python3 scripts/audit.py render "$RUN/audit-v2.json" --out "$RUN/review-v2.html"
```

## Human check and export

Open the HTML file. Reviewer writes a name, reads source links, checks the relevant attestations, chooses a decision, and clicks **Record decision** for each item. They then click **Download decisions JSON**. No server is needed. Browser draft persistence is optional and local; downloaded JSON is the portable record.

```sh
python3 scripts/audit.py merge "$RUN/audit-v2.json" "$RUN/human_decisions.json" --out "$RUN/reviewed_audit.json"
python3 scripts/audit.py export "$RUN/reviewed_audit.json" --out "$RUN/approved.csl.json"
node scripts/citations.cjs format "$RUN/approved.csl.json" "$RUN/approved.bib" --format bibtex
node scripts/citations.cjs format "$RUN/approved.csl.json" "$RUN/approved-apa.txt" --format apa
node scripts/citations.cjs format "$RUN/approved.csl.json" "$RUN/approved-style.txt" --format csl --style /path/to/independent-style.csl
```

Bibliography style support means CSL rendering, not an automated judgment of venue submission rules. Use the user-specified style/version and inspect output for math, acronyms, article numbers, non-Latin names, or institutional requirements. For LaTeX, preserve citation keys and use the venue's actual BibTeX/BibLaTeX toolchain for the manuscript when available. Do not pretend APA output is IEEE or ACM.

Claim statuses partial/not_found/contradicted/unavailable cannot pass claim approval. After a rewrite, inspect sources for the exact new wording, enrich to a new audit file, and ask the human to review the revised card. Selecting an alternate candidate similarly requires new metadata and integrity evidence. The UI's replacement note can name the candidate index; it does not silently switch the record.

`python3 scripts/audit.py validate FILE.json` checks structural and approval invariants, not the truth of source passages.
