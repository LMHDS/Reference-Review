# Acceptance report: focused bibliography workflow

Version: 0.2.0 · Schema: 2 · Executed: 2026-09-29T00:57:46+00:00

## Scope and result

Exactly two entry points: audit an existing reference list, or discover papers from topic keywords. Both produce identity evidence, citation-format previews and keywords. Manuscript-sentence verification has been removed.

| Dataset | Records | Source identities | Keyword sets | APA + BibTeX previews | Human pending |
|---|---:|---:|---:|---:|---:|
| Sparse attention | 10 | 10 | 10 | 10 pairs | 10 |
| KV-cache quantization | 10 | 10 | 10 | 10 pairs | 10 |
| Controlled reference list | 5 | 5 | 5 | 5 pairs | 5 |

All checks passed locally. The 25 records represent 21 distinct papers. All real references remain pending; approved exports contain zero entries. Synthetic decisions exercise review behavior without creating real approvals.

## Evidence and limits

Primary arXiv pages were read separately with a web retrieval tool. The [source manifest](../examples/source-records.json) records titles, author order, identifiers, original submission years, versions and retrieval times. It is a structured transcription, not a raw API archive. This acceptance run replays those saved source records through enrichment, metadata comparison, preview generation, review rendering and export. It is not a fresh online search or independent proof of the transcription.

The two topic lists are curated examples, not exhaustive or ranked searches. Keywords are explicitly labeled as title/abstract-based suggestions, not author-provided keywords. Years refer to the original arXiv submission; preprint editions are not merged with proceedings editions. Author-name segmentation remains a review item. Native API connectivity and comprehensive integrity checks were not part of this local acceptance. No full-text reading is required by this version. Browser visuals were not inspected; interface checks use the DOM.

## Tests

- 21 Python tests passed, including keyword provenance, stale approval rejection, bibliography-only approval scope, missing review checks, old-schema rejection and preview generation from corrected metadata.
- Citation-key preservation is checked in a real Citation.js preview. A discovered automatic-key-rewriting issue was fixed by explicitly retaining the input key; unsafe or duplicate keys fail clearly.
- BibTeX nested-brace parsing, BibTeX/RIS author-year roundtrips and APA rendering passed.
- DOM tests passed: citation and keyword previews before approval, blocked incomplete review, explicit approval/correction decisions, local drafts and search.
- Skill structure validation passed. GitHub Actions runs the same behavioral checks; see its live status for the published commit.

## Controlled list

These are deliberately constructed inputs using real papers, not private references or an observed AI failure log.

| Input | Expected and observed |
|---|---|
| VAR year changed to 2023 | Source year 2024 flagged as different |
| Sparse Transformers title changed | Source title flagged as different |
| KIVI author field removed | Missing authors flagged |
| Second KIVI entry | Duplicate candidate flagged |
| Longformer clean control | All compared fields match |

## Open the review pages

Download the repository and open HTML locally. Each page displays source identity, APA/BibTeX previews and keyword origin before the reviewer makes a decision.

- [Reference-list review](examples/small-reference-list.review.html)
- [Sparse-attention review](examples/sparse-attention.review.html)
- [KV-cache-quantization review](examples/kv-cache-quantization.review.html)

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

Use a fresh output directory. Old schema-1 audits remain in repository history; start a new schema-2 run rather than reusing earlier decisions.
