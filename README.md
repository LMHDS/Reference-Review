# Reference Review

**Two ways to build a trustworthy, well-formatted bibliography.**

| Input | What the workflow does | Output per paper |
|---|---|---|
| **An existing reference list** | Check existence/identity, compare metadata and editions, flag duplicates, review or suggest keywords | Source evidence + citation previews + keywords |
| **Topic keywords** | Search for relevant papers and check their source records | Source evidence + citation previews + keywords |

Both routes lead to the same simple review page: **paper identity → citation format → keywords**. Preview APA and BibTeX before making a decision. Human review covers the bibliography only; it does not require reading full papers or assessing manuscript sentences.

## Quick start

Requires Python 3.10+ and Node.js 20+.

```sh
git clone https://github.com/LMHDS/Reference-Review.git
cd Reference-Review
npm ci --ignore-scripts
python3 scripts/run_acceptance.py --out runs/demo
```

Open `runs/demo/sparse-attention.review.html`, `kv-cache-quantization.review.html`, or `small-reference-list.review.html` locally. All examples include source links, citation previews and keywords. They remain pending until a human explicitly records a decision.

To use as a Codex skill, place this repository in your skill directory under `reference-verification` and install the Node dependencies. [SKILL.md](SKILL.md) is the agent entry point. The helpers also run independently of an assistant.

## 1. Audit an existing reference list

Example request:

> Check this reference list for real paper identities, correct bibliography fields and citation formatting. Review the supplied keywords or suggest keywords with their sources. Prepare a bibliography review page.

```sh
RUN=runs/my-list
node scripts/citations.cjs parse references.bib "$RUN/input.json"
python3 scripts/audit.py audit "$RUN/input.json" --cache "$RUN/evidence" --out "$RUN/audit.json"
python3 scripts/audit.py render "$RUN/audit.json" --out "$RUN/review.html"
```

Supports BibTeX, RIS, CSL JSON, DOI/arXiv lists, and agent-extracted pasted references. Original entries and citation keys are retained. Ambiguous candidates require source matching before a citation can be proposed.

## 2. Discover papers from topic keywords

Example request:

> Find ten representative papers on KV-cache quantization. Check primary-source identity, provide citation previews and keywords, and briefly explain topic relevance.

```sh
RUN=runs/topic-search
python3 scripts/audit.py discover 'ti:"KV cache" AND all:quantization' --provider arxiv --limit 10 --cache "$RUN/evidence" --out "$RUN/candidates.json"
python3 scripts/audit.py render "$RUN/candidates.json" --out "$RUN/review.html"
```

The agent inspects results for relevance and corroborates identities on primary pages. CLI search results alone are candidates. Crossref is also supported. These searches do not guarantee exhaustive coverage or rank papers by quality.

## Shared output and review

Each card displays identity evidence and source links, edition/version details, metadata differences, APA/BibTeX previews, and keywords with provenance. Source-provided keywords are distinguished from AI title/abstract suggestions and automatic title-term extraction. Keywords supplied in your list remain available for comparison.

Choose **Approve bibliography**, **Request correction**, **Choose another paper**, or **Exclude**. Click **Record decision**, then **Download decisions JSON**. A correction request returns to the workflow for a new review; it never silently approves unseen changes.

```sh
python3 scripts/audit.py merge "$RUN/audit.json" bibliography_decisions.json --out "$RUN/reviewed.json"
python3 scripts/audit.py export "$RUN/reviewed.json" --out "$RUN/approved.csl.json"
node scripts/citations.cjs format "$RUN/approved.csl.json" "$RUN/approved.bib" --format bibtex
```

Use the exact audit filename behind your review page (`candidates.json` for the discovery example). Only approved references enter the reviewed export. Keyword provenance remains in the accompanying audit. [Detailed commands](references/commands.md) cover enrichment, other formats and independent CSL styles.

## Acceptance

[The report](reports/acceptance.md) includes 10 sparse-attention papers, 10 KV-cache-quantization papers and 5 controlled list entries. All 25 records have keyword sets and citation previews. Controlled errors cover year, title, missing authors and duplicates. The source metadata was retrieved separately from primary pages; automated acceptance replays the saved records and is not a new online search.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/run_acceptance.py --out runs/acceptance
node tests/ui.cjs runs/acceptance
```

## Scope, sources and privacy

The workflow uses open-source [Citation.js](https://citation.js.org/) and public Crossref/arXiv APIs. No API key or paid model service is required by the helpers. The agent provides source matching and useful title/abstract keyword suggestions; the standalone CLI offers conservative lexical keywords.

A lookup failure does not prove fabrication. An existing record does not certify research quality. Limited registry notice checks do not establish comprehensive integrity. Preprint and proceedings metadata stay separate. Check inferred author-name segmentation and the actual required style; APA/BibTeX previews are not a venue-policy certification.

The local HTML page uploads nothing; source links open external sites. CLI requests send identifiers or search terms to the selected provider. Local review decisions are self-reported records, not signatures. Keep private bibliography runs out of public repositories.

Version 0.2 uses schema 2. Preserve older files and start a new run; old claim-review decisions are intentionally not migrated. Manuscript-content verification is outside this focused workflow.

## License

MIT for project code and documentation. Bibliographic facts retain source attribution; full papers are not redistributed. Dependencies retain their own licenses.
