# Acceptance report

Executed: 2026-09-29T00:33:36+00:00

## Result

All three acceptance datasets passed the implemented workflow checks. The 25 entries cover 21 distinct papers. All 25 actual reference records remain **pending human review**, and reviewed exports contain **zero** entries. Synthetic approval tests exercise the gate only; they are not real reviewer decisions.

| Dataset | Entries | Primary-source identities | Human pending | Reviewed export |
|---|---:|---:|---:|---:|
| Sparse attention | 10 | 10 | 10 | 0 |
| KV-cache quantization | 10 | 10 | 10 | 0 |
| Controlled reference list | 5 | 5 | 5 | 0 |

## What was checked

- Live primary arXiv landing pages were read separately with a web retrieval tool. Titles, ordered author names, identifiers, initial submission years, and available version history were recorded in [source-records.json](../examples/source-records.json). The manifest records actual retrieval times. It is a structured transcription, not a raw API-response archive.
- The automated acceptance run used those saved records through the real enrichment, comparison, duplicate detection, rendering, and export commands. Replaying these records is **not** a new online lookup or an independent confirmation of their transcription.
- The controlled list detected an incorrect year, an incorrect title, a missing author list, and a duplicate. The clean control had no metadata differences. A VAR claim omitting rejection sampling remained partial and could not receive claim approval.
- Twenty-one Python unit tests passed. API behavior in these tests uses fixtures. BibTeX key/nested-brace parsing, BibTeX/RIS author-year roundtrips, and APA rendering passed.
- DOM interface tests passed: five-card rendering, blocked partial-claim approval, explicit rewrite and metadata-only decisions, local draft persistence, and search. Skill structure validation passed.

## Coverage limits

The topic sets are curated representative examples, not a systematic search, citation-count ranking, or full-text verification of all methods. Topic relevance notes are provisional title/abstract-level summaries. Author full strings/order are sourced; given/family segmentation is inferred. Years refer to original arXiv submission, not a claim about proceedings publication. No comprehensive integrity-notice search or venue-specific manuscript compliance audit was performed. Native Crossref/arXiv API acceptance could not be run in the local network environment; primary pages were accessible through the separate web tool. Browser visual layout was not inspected; DOM testing is the interface evidence. GitHub Actions is configured separately and its status must be read on GitHub.

## Review the examples

Download the repository to open the self-contained review pages locally. GitHub normally displays HTML source rather than executing it.

- [Small list: review page](examples/small-reference-list.review.html) · [audit JSON](examples/small-reference-list.audit.json)
- [Sparse attention: review page](examples/sparse-attention.review.html) · [audit JSON](examples/sparse-attention.audit.json)
- [KV-cache quantization: review page](examples/kv-cache-quantization.review.html) · [audit JSON](examples/kv-cache-quantization.audit.json)

## Controlled input cases

These are intentionally constructed inputs using real papers. They are not a private bibliography or a claim that an AI produced these particular mistakes.

| Input | Intended finding | Observed |
|---|---|---|
| VAR, year changed to 2023 | Source year is 2024 | Difference flagged |
| Sparse Transformers, title changed to Infinite Sequences | Source says Long Sequences | Difference flagged |
| KIVI, author field removed | Source author list available | Missing field flagged |
| Second KIVI entry | Same underlying paper | Duplicate candidate flagged |
| Longformer, clean metadata | No injected error | All compared fields match |
| VAR, FID 1.73 without sampling condition | Table 1 distinguishes rejection sampling | Partial; approval blocked |

## Sparse attention: ten selected papers

| Paper (initial arXiv year) | Why included |
|---|---|
| [Generating Long Sequences with Sparse Transformers](https://arxiv.org/abs/1904.10509) (2019) | Sparse factorized attention for long autoregressive sequences; an early reference for the topic. |
| [Longformer: The Long-Document Transformer](https://arxiv.org/abs/2004.05150) (2020) | Local-window and global attention for long documents. |
| [Big Bird: Transformers for Longer Sequences](https://arxiv.org/abs/2007.14062) (2020) | Block-sparse attention combining local, global, and random connections. |
| [Reformer: The Efficient Transformer](https://arxiv.org/abs/2001.04451) (2020) | Locality-sensitive hashing provides a content-dependent sparse attention mechanism. |
| [Efficient Content-Based Sparse Attention with Routing Transformers](https://arxiv.org/abs/2003.05997) (2020) | Content-based routing offers another way to select sparse attention connections. |
| [Swin Transformer: Hierarchical Vision Transformer using Shifted Windows](https://arxiv.org/abs/2103.14030) (2021) | Shifted local windows extend sparse attention ideas to hierarchical visual representations. |
| [Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention](https://arxiv.org/abs/2502.11089) (2025) | An example of trainable sparse attention designed with hardware efficiency in mind. |
| [MoBA: Mixture of Block Attention for Long-Context LLMs](https://arxiv.org/abs/2502.13189) (2025) | Block-level routing offers a mixture-of-experts-inspired approach to sparse attention. |
| [MInference 1.0: Accelerating Pre-filling for Long-Context LLMs via Dynamic Sparse Attention](https://arxiv.org/abs/2407.02490) (2024) | Dynamic sparse attention targets long-context prefill acceleration. |
| [FlexPrefill: A Context-Aware Sparse Attention Mechanism for Efficient Long-Sequence Inference](https://arxiv.org/abs/2502.20766) (2025) | Context-aware sparse attention adapts the prefill computation to the input. |

## KV-cache quantization: ten selected papers

| Paper (initial arXiv year) | Why included |
|---|---|
| [KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache](https://arxiv.org/abs/2402.02750) (2024) | Asymmetric low-bit quantization treats keys and values differently. |
| [KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization](https://arxiv.org/abs/2401.18079) (2024) | KV-cache quantization for very long-context inference. |
| [GEAR: An Efficient KV Cache Compression Recipe for Near-Lossless Generative Inference of LLM](https://arxiv.org/abs/2403.05527) (2024) | Combines KV-cache compression techniques to reduce quantization error. |
| [No Token Left Behind: Reliable KV Cache Compression via Importance-Aware Mixed Precision Quantization](https://arxiv.org/abs/2402.18096) (2024) | Importance-aware mixed precision aims to retain information from all tokens. |
| [QServe: W4A8KV4 Quantization and System Co-design for Efficient LLM Serving](https://arxiv.org/abs/2405.04532) (2024) | A serving system that co-designs weight, activation, and KV-cache quantization. |
| [SKVQ: Sliding-window Key and Value Cache Quantization for Large Language Models](https://arxiv.org/abs/2405.06219) (2024) | Sliding-window KV-cache quantization balances recent tokens and compressed history. |
| [RotateKV: Accurate and Robust 2-Bit KV Cache Quantization for LLMs via Outlier-Aware Adaptive Rotations](https://arxiv.org/abs/2501.16383) (2025) | Rotations address outliers in low-bit KV-cache quantization. |
| [AsymKV: Enabling 1-Bit Quantization of KV Cache with Layer-Wise Asymmetric Quantization Configurations](https://arxiv.org/abs/2410.13212) (2024) | Layer-wise asymmetric configurations explore very low-bit KV-cache storage. |
| [TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate](https://arxiv.org/abs/2504.19874) (2025) | Online vector quantization is relevant to KV-cache compression; broader than KV-only methods. |
| [MiniKV: Pushing the Limits of LLM Inference via 2-Bit Layer-Discriminative KV Cache](https://arxiv.org/abs/2411.18077) (2024) | Layer-discriminative two-bit KV-cache compression explores memory reduction. |

## Reproduce

```sh
npm ci --ignore-scripts
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/run_acceptance.py --out runs/acceptance
node tests/ui.cjs runs/acceptance
```

Use a fresh output directory. Audit IDs and timestamps will differ between runs; assertions and datasets remain the same.
