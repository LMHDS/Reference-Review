# Providers and open-source components

Implementation choices checked against official documentation on 2026-09-28. API policies may change; verify provider requirements before adding adapters. Public metadata APIs and open-source software are separate categories.

## Built in

- **Crossref public REST API:** DOI identity records, bibliographic candidate search, metadata and DOI-linked update notices. No account/key is needed for the basic workflow. Queries use `query.bibliographic`, `/works/{doi}`, and `filter=updates:{doi}`. `update-to` describes updates from the current record to earlier works; reverse update lookup helps find notices about a selected work. This is limited metadata coverage, not a complete Retraction Watch scan. See [metadata retrieval](https://www.crossref.org/services/metadata-retrieval/) and [REST filters](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/).
- **arXiv public Atom API:** identifier/version resolution and discovery. Preserve ID/version and submission dates, and keep any related journal DOI as a relationship rather than merging it into preprint metadata. Serial requests are spaced at least 3.1 seconds. See [API manual](https://info.arxiv.org/help/api/user-manual.html).
- **Citation.js (MIT):** local BibTeX/RIS/CSL parsing and bibliography rendering with its CSL/citeproc integration. This package deliberately does not load the DOI plugin, preventing hidden network resolution during parsing. Use an independent CSL XML file for venue-specific styles. See [project and supported formats](https://citation.js.org/) and [output documentation](https://citation.js.org/api/0.7/tutorial-output.html).

## Optional agent adapters, not implemented in the bundled CLI

- **OpenAlex:** use its current authentication policy and user-provided credentials if available. Never assume old anonymous-access rules apply. [Authentication](https://help.openalex.org/api/authentication/).
- **Semantic Scholar:** good for related-paper discovery and additional records; consult official API documentation for current authentication/rate limits. It is an external service, not bundled software. Do not request a key if primary sources already suffice.
- **GROBID:** an open-source scholarly PDF parser; use a user-configured local endpoint to extract references and citation contexts. Parsing does not establish claim support. Do not start a large deployment as a hidden prerequisite of a reference-list audit. [Project](https://github.com/kermitt2/grobid).
- **Zotero/CSL:** when the user already uses Zotero, retain item identifiers and use their chosen style. Write-backs to a shared library require appropriate user authorization. The current workflow exports local files only.
- **User-maintained/open-source verifier:** accept structured candidate metadata and provenance through `enrich`; retain that tool's version and source record URLs. Inspect the evidence before accepting tool verdicts. Do not call a user repository “integrated” until its actual API/output has been read and tested.

## Failure handling

Crossref is not a registry of every paper. Non-DOI conference proceedings, DataCite DOIs, withdrawn preprints and alternate versions can require other primary sources. Use publisher pages, official proceedings or arXiv as applicable; preserve disagreement. An independent primary-source check is preferred to counting two aggregators that mirror the same registry.

Only fetch scholarly identifiers/title queries through public services. Full unpublished manuscripts remain local unless explicitly authorized. Store retrieval timestamps and evidence versions. Paywalled full text stays unavailable unless the user supplies access or a lawful accessible version.
