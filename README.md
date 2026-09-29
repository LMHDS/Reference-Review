# Reference Review

A Codex skill for checking references and discovering research papers. Its entry point is [SKILL.md](SKILL.md).

| Input | Skill output |
|---|---|
| An existing reference list | Paper identity evidence, bibliographic corrections, citation previews and keywords |
| Topic keywords | Relevant paper candidates with identity evidence, citation previews and keywords |

Both routes produce a local bibliography review page. APA and BibTeX previews appear before human approval. Keyword suggestions distinguish source-provided terms from AI inference. Review covers bibliography information; full-text interpretation is outside this skill.

## Install for Codex

Requires Python 3.10+ and Node.js 20+.

Clone into your Codex skill directory using the folder name `reference-verification`:

```sh
git clone https://github.com/LMHDS/Reference-Review.git ~/.codex/skills/reference-verification
cd ~/.codex/skills/reference-verification
npm ci --ignore-scripts
```

If you use a custom Codex skill directory, substitute that path. This repository itself is the skill; no example dataset is needed.

## Use

Ask Codex:

> Use $reference-verification to check my reference list for paper identity, citation formatting and keywords. Prepare a bibliography review page.

Or:

> Use $reference-verification to find five papers on my topic. Check their primary-source records and provide citation previews and keywords.

Codex retrieves sources, resolves candidate identities, prepares the review page, and merges your explicit decisions before exporting approved BibTeX. Choose **Approve bibliography**, **Request correction**, **Choose another paper**, or **Exclude**; click **Record decision**, then download the decisions JSON and return it to Codex.

[Execution instructions](references/commands.md) cover the CLI, enrichment and formatting. [Evidence and decisions](references/evidence.md) defines provenance and review records. [Providers](references/providers.md) describes the supported services.

## Contents

- `SKILL.md` and `agents/`: Codex instructions and discovery metadata.
- `scripts/`: source lookup, audit, citation parsing and formatting.
- `assets/`: the local review-page template.
- `references/`: workflow and evidence documentation.
- `tests/` and `.github/workflows/`: independent maintenance tests and CI.

Paper lists, saved source datasets, generated review pages and run reports belong in each user's working directory and are not bundled with the skill.

## Tests

```sh
npm test
```

Tests create temporary synthetic records and clean them up. They cover bibliography review gates, source lookup behavior, keyword provenance, stale decisions, citation parsing and formatting, and the review interface. They do not perform live scholarly verification.

## Sources and limits

The skill uses open-source [Citation.js](https://citation.js.org/) and public Crossref/arXiv APIs. No API key or paid model service is required by the bundled helpers. Codex provides source matching and useful title/abstract keyword suggestions; the standalone CLI offers conservative title-term extraction.

Lookup failure does not prove fabrication. Existing records do not certify research quality. Preprint and proceedings metadata stay separate. Check the required citation style and author-name segmentation. Limited notice checks do not provide comprehensive integrity certification.

The local HTML page uploads nothing; source links open external sites. CLI requests send identifiers or queries to the chosen API. Human decisions are self-reported records, not authenticated signatures. Keep private runs out of public repositories. Schema 2 deliberately rejects older claim-review decisions.

## License

MIT for project code and documentation. Dependencies retain their own licenses.
