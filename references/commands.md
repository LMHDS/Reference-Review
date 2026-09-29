# Two entry points

Run commands from the skill/repository directory. Python 3.10+ and Node.js 20+ are required. Outputs refuse to overwrite existing files; choose a fresh run directory.

```sh
npm ci --ignore-scripts
RUN=runs/my-review
```

## 1. Existing reference list

```sh
node scripts/citations.cjs parse references.bib "$RUN/input.json"
python3 scripts/audit.py audit "$RUN/input.json" --cache "$RUN/evidence" --out "$RUN/audit.json"
```

The parser accepts `.bib`, `.ris`, and CSL `.json`. Python accepts JSON or `.txt`/`.doi` with one reference/identifier per line. Agent extraction of wrapped text retains the exact original entry. A supplied `keyword` or `keywords` field remains in the original record; compare it with source-backed suggestions.

## 2. Topic keywords

```sh
python3 scripts/audit.py discover 'ti:"sparse attention"' --provider arxiv --limit 10 --cache "$RUN/evidence" --out "$RUN/audit.json"
```

Crossref discovery accepts ordinary keyword strings with `--provider crossref`. Search records are candidates. The agent checks their relevance and primary-source identity, then enriches the results. Keep the query and limits; ten selected papers are not a systematic review.

## Resolve candidates and add keywords

`enrich` accepts source-backed candidates, a selected index, identity reasoning, source notices, keywords, extra sources, and discovery notes. Values below are descriptive placeholders, not evidence:

```json
{
  "run_id": "CURRENT_RUN_ID",
  "entries": [{
    "id": "existing-key",
    "evidence_hash": "CURRENT_ENTRY_HASH",
    "selected": 0,
    "identity": {"status": "evidence_matched", "reason": "Actual title, author, identifier, and version match observed on the primary page."},
    "keywords": {
      "terms": ["sparse attention", "long-context inference"],
      "basis": "agent_title_abstract",
      "source_url": "ACTUAL_INSPECTED_SOURCE_URL",
      "note": "Inferred from the title/abstract; not author-supplied keywords. Explain differences from user-supplied terms here."
    }
  }]
}
```

```sh
python3 scripts/audit.py enrich "$RUN/audit.json" "$RUN/patch.json" --out "$RUN/audit-v2.json"
python3 scripts/audit.py render "$RUN/audit-v2.json" --out "$RUN/review.html"
```

Rendering runs Citation.js locally and displays APA and BibTeX previews before review. Unselected records have no proposed citation. For API-only runs without an enrichment step, render `audit.json` instead.

## Human review and export

Open the review HTML locally. Inspect identity evidence, bibliography differences, citation previews and keyword origin. Enter a reviewer name, choose a decision and click **Record decision**, then **Download decisions JSON**. Return corrections to the workflow for a new audit version; a correction request is not approval.

```sh
python3 scripts/audit.py merge "$RUN/audit-v2.json" bibliography_decisions.json --out "$RUN/reviewed.json"
python3 scripts/audit.py export "$RUN/reviewed.json" --out "$RUN/approved.csl.json"
node scripts/citations.cjs format "$RUN/approved.csl.json" "$RUN/approved.bib" --format bibtex
node scripts/citations.cjs format "$RUN/approved.csl.json" "$RUN/approved.ris" --format ris
```

Use exactly the audit version behind the review page. Keyword lists and provenance remain in the audit. Citation keys are preserved; unsafe or duplicate keys cause an explicit formatting error.

For another style, use `--format csl --style /path/to/independent-style.csl` and review that output before use. Standard page previews are explicitly APA/BibTeX, not proof of every venue's compliance.

## Evidence and failures

The API cache stores raw bytes and hashes. `--offline` explicitly reuses those records with their original retrieval times. Online runs retrieve again. Crossref is not the registry for all DOIs; failures or absent records require another primary source, not a fabrication verdict. Optional `REFCHECK_CONTACT` sets a user-provided contact for requests.

`validate FILE.json` checks evidence hashes and workflow invariants. Schema v2 rejects older claim-review audits. Start a new run and preserve previous audit/decision files.
