# Providers and components

- **Crossref REST API:** DOI resolution, bibliographic candidate search, metadata and linked update notices. Crossref is not the registry for every DOI. Title results are candidates, not automatic matches. See [metadata retrieval](https://www.crossref.org/services/metadata-retrieval/) and [REST filters](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/).
- **arXiv Atom API:** identifier/version resolution and topic search. Keep submission year, revision history, related publication DOI and preprint edition distinct. Requests are spaced at least 3.1 seconds. See [API manual](https://info.arxiv.org/help/api/user-manual.html).
- **Citation.js:** open-source local BibTeX/RIS/CSL parsing and rendering. The DOI resolver plugin is deliberately not loaded. APA/BibTeX previews run locally, as does formatting to an independent CSL style. See [project](https://citation.js.org/) and [output documentation](https://citation.js.org/api/0.7/tutorial-output.html).

Additional primary publisher/proceedings pages can be supplied through agent enrichment. Other search providers may be used when available, retaining source links and actual retrieval times. Do not claim a provider is integrated into the CLI unless implemented and tested.

A record's identity, a paper's research quality, and bibliographic style compliance are separate questions. This workflow covers existence/identity and bibliography preparation. Limited Crossref notice checks can flag known updates; no notice found is not a comprehensive integrity result.

Keyword provenance is essential. Explicit author keywords can be copied with a source link. Provider subject categories must be labeled as such. AI-generated topic tags and title-term extraction must remain marked as suggestions, not author keywords. If only a title is available, keep the proposed terms conservative.

Queries send identifiers, titles, or topic terms to the selected API. Do not send unrelated manuscript text or credentials. Timeouts, rate limits, and absent records are explicit lookup gaps, never fabrication verdicts. API policies can change; consult official documentation when extending adapters.
