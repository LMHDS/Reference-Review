# Reference Review

**Tool-assisted reference verification with an explicit human review step.**

Turn a research topic or an existing reference list into an evidence-backed audit, a local review page, and a bibliography containing only explicitly approved entries. Use it as a Codex skill or run the command-line helpers yourself.

A plausible citation is a search lead. A source record establishes bibliographic evidence. Neither automatically proves a manuscript claim.

```text
Research topic / existing references
                ↓
Search primary sources and resolve paper identity
                ↓
Compare metadata, versions, duplicates, and claim evidence
                ↓
Local human review: approve · rewrite · replace · reject
                ↓
Merge decisions tied to the evidence version
                ↓
Export approved references in BibTeX, RIS, or CSL styles
```

## What it does

- Accepts BibTeX, RIS, CSL JSON, DOI/arXiv lists, and agent-assisted extraction from pasted text or manuscripts.
- Uses open-source [Citation.js](https://citation.js.org/) for parsing and formatting, plus Crossref and arXiv public APIs for discovery and identifier lookup.
- Retains original entries, candidate records, source links, retrieval times, metadata differences, and limited integrity-check coverage.
- Separates paper existence/identity, citation metadata, source support for claims, formatting, and human decisions.
- Produces a self-contained English HTML review page. Decisions can be downloaded as JSON; optional drafts stay in the browser.
- Blocks reviewed export until explicit human approval. Partial or unsupported claims cannot pass. Evidence changes invalidate earlier approvals.

The helpers do **not** autonomously read and interpret every PDF. An agent or reviewer must inspect the relevant full text, attach located evidence, and state remaining uncertainty. No API key or paid LLM service is required by the helpers.

## Setup

Requirements: Python 3.10+ and Node.js 20+.

```sh
git clone https://github.com/LMHDS/Reference-Review.git
cd Reference-Review
npm ci --ignore-scripts
```

For use as a skill, place or clone this repository in your skill directory under the folder name `reference-verification`, then install its Node dependencies. [SKILL.md](SKILL.md) is the agent entry point. The helpers are otherwise independent of a specific assistant.

Example requests:

> Use reference-verification to find candidate papers on sparse attention. Explain why each is relevant, inspect primary sources, and prepare a human review page. Keep unverified claims explicit.

> Audit my references.bib and these manuscript sentences. Check identity, metadata, duplicates, and whether each exact sentence is supported. Produce a review page before exporting approved references.

## Try the included examples

```sh
python3 scripts/run_acceptance.py --out runs/demo
```

Open `runs/demo/small-reference-list.review.html` locally. Read the source links, enter your reviewer name, record each decision, and download the decisions JSON. The VAR example deliberately omits a rejection-sampling condition, so it requires a rewrite and renewed evidence review before approval.

There are also review pages for ten sparse-attention papers and ten KV-cache-quantization papers. These are curated examples, not an exhaustive literature review or a ranking of the best papers. Their selected edition is the recorded arXiv preprint; original submission year is kept separate from revision history and proceedings publication.

The acceptance command replays metadata previously retrieved from primary pages. It does **not** perform a fresh online verification. See [the acceptance report](reports/acceptance.md) and [source records](examples/source-records.json).

## Audit your own list

Use a new output directory for each run; output files are never silently overwritten.

```sh
RUN=runs/my-review
node scripts/citations.cjs parse references.bib "$RUN/input.json"
python3 scripts/audit.py audit "$RUN/input.json" --cache "$RUN/evidence" --out "$RUN/audit.json"
python3 scripts/audit.py render "$RUN/audit.json" --out "$RUN/review.html"
```

For discovery:

```sh
python3 scripts/audit.py discover 'ti:"sparse attention"' --provider arxiv --limit 10 --cache runs/search/evidence --out runs/search/candidates.json
```

Discovery results are candidates. Inspect sources and use `enrich` to add identity reasoning, full-text claim evidence, or alternate records. [Execution instructions](references/commands.md) describe the patch format, source provenance, API errors, and custom CSL styles; [evidence guidance](references/evidence.md) explains assessment boundaries.

After the human records and downloads decisions:

```sh
python3 scripts/audit.py merge "$RUN/audit.json" human_decisions.json --out "$RUN/reviewed.json"
python3 scripts/audit.py export "$RUN/reviewed.json" --out "$RUN/approved.csl.json"
node scripts/citations.cjs format "$RUN/approved.csl.json" "$RUN/approved.bib" --format bibtex
```

Use the exact audit version displayed by the review page. For revised claims, add evidence for the revised wording, render a new page, and obtain a new human decision. Metadata-only approval never establishes support for a manuscript claim.

## Acceptance and tests

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/run_acceptance.py --out runs/acceptance
node tests/ui.cjs runs/acceptance
```

The test suite covers stale approvals, identity selection, API failures, metadata differences, duplicates, claim evidence, reviewed export, citation roundtrips, and the review interface. API unit tests use fixtures. The report distinguishes those tests from the separate primary-page retrieval used to curate the 20-paper datasets.

## Limits and privacy

- A lookup failure means unresolved evidence, not a fabricated paper. Title search does not automatically select a match.
- Crossref update checks are limited to linked notices in that registry. No notice found is not an integrity guarantee. arXiv records and other registries need their own checks.
- Exact claim support requires the relevant full text, conditions, tables, and version. Abstracts alone are insufficient for specific experimental claims.
- Correct formatting is not proof of compliance with every venue policy. Review the actual submission style and author instructions. Check inferred name segmentation and capitalization.
- Review decisions are self-reported, editable local records, not authenticated signatures. This is a workflow aid, not a tamper-proof certification system. The formatter can format arbitrary input; use the reviewed export path for final references.
- The local HTML page makes no uploads or model calls. Source links open external sites. CLI searches send identifiers/query strings to the chosen provider; the audit and its raw references can contain sensitive manuscript text. Keep your own runs out of public repositories.

## License

MIT for the project code and documentation. Bibliographic facts and short source excerpts retain their source attribution; this repository does not redistribute full papers. Dependencies retain their own licenses.
