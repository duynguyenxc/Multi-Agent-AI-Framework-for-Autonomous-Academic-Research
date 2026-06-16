# Selective Research Foundation Map

Draft version: 2026-06-15

## 1. Purpose

This document defines the selection policy for external papers, algorithms, tools, and concepts used in the project.

The goal is not to collect as many references as possible. The goal is to use only the knowledge that makes the project more scientifically defensible, easier to evaluate, or more likely to work as a real research pipeline.

## 2. Selection Rule

A paper, method, tool, or concept is added to the project only if it supports at least one of these functions:

1. Defining the human benchmark.
2. Representing the systematic or realist review workflow.
3. Defining entities and relationships.
4. Constructing and querying the knowledge graph.
5. Evaluating retrieval, extraction, and synthesis.
6. Supporting human feedback and refinement.
7. Strengthening the project as a defensible research contribution.

References outside these functions are not added to the main project documents.

## 3. Core References to Keep

These are core because they directly support the project's design and evaluation.

| Area | Source | Why it is useful | How to use it |
|---|---|---|---|
| Human benchmark | Richmond et al. (2020) | Provides the worked realist review, 28-paper corpus, five-context programme theory, and final conclusion. | Treat as the project-specific human benchmark. |
| Realist synthesis standards | Wong et al. (2013), RAMESES publication standards | Defines what a realist synthesis should report and why C-M-O reasoning is central. | Use to justify CMOC structure, programme theory reporting, and interpretive human judgment. |
| Systematic review transparency | PRISMA 2020; PRISMA-S | Provides reporting/search transparency standards for review workflows. | Use for PRISMA flow, search/screening documentation, and reproducibility. |
| Graph-based global sensemaking | Edge et al. (2024/2025), GraphRAG | Explains why graph-based community summaries help answer global questions over a corpus. | Use to justify GraphRAG as the evidence/sensemaking layer, not as the gold standard. |
| Community detection | Traag et al. (2019), Leiden algorithm | GraphRAG uses community detection to partition graph structures for summary and sensemaking. | Use only if discussing graph community construction or community reports. |
| Structured scientific information extraction | Dunn/Dagdelen et al. (2022/2024) | Supports schema-constrained extraction of entities and relations from scientific text. | Use to justify constrained JSON/Pydantic extraction for CMOC, NER, and relation extraction. |
| RAG evaluation | RAGAS; ARES | Provides concepts such as faithfulness, context relevance, and answer relevance. | Use as secondary evaluation for retrieval/reporting quality, not as replacement for Richmond gold. |
| Corrective retrieval | CRAG; Self-RAG | Shows retrieval quality can be evaluated and corrected before generation. | Use only if adding retrieval-quality gates or citation-faithfulness refinement. |
| Human-in-the-loop screening | ASReview / active learning review tools | Supports interactive screening and reviewer feedback for systematic reviews. | Use if the project evaluates real search/screening beyond benchmark mode. |

## 4. References to Treat as Secondary, Not Core

These can be useful, but they should not drive the current implementation unless a specific gap requires them.

| Area | Example | Why secondary |
|---|---|---|
| General AI systematic review frameworks | PRISMA-DFLLM, L-PRISMA, AgentSLR | Useful for positioning, but too broad to define our Richmond-specific evaluation. |
| Link prediction / graph embeddings | AUROC-based KG completion methods | Entity/relation definition and verification are higher priority than link prediction. |
| Full RLHF training | RLHF for agent policies | Too large for current timeline; human feedback can first be implemented as adjudication and prompt/schema refinement. |
| Neo4j or graph database migration | Neo4j, NebulaGraph | Useful later for querying/visualization, but not required to define or score E-code/R-code triples. |
| Fine-tuning domain LLMs | education-specific LLM fine-tuning | Valuable long-term, but current project needs benchmark evaluation and artifact consistency first. |

## 5. Methods to Adopt Now

The project should adopt these methods immediately because they directly solve current problems:

1. Controlled ontology for entities: E01-E47 from Richmond-derived gold.
2. Frozen predicate vocabulary for relationships: PROVIDES, ENABLES, TRIGGERS, LEADS_TO, CONSTRAINS.
3. Directed E-code triples for edge scoring.
4. Stage-by-stage evaluation: corpus, indexing, entity extraction, relationship extraction, CMOC extraction, synthesis, final theory.
5. Strict and relaxed matching for entities and relationships.
6. Evidence support requirement for every accepted node and edge.
7. Human adjudication table for per-paper CMOC/entity/relation gold.
8. Error categories that feed directly into prompt, schema, or mapping refinement.

## 6. Methods to Delay

The project should not adopt these yet:

1. Training a new domain-specific LLM.
2. Implementing full RLHF.
3. Building graph neural network link prediction.
4. Migrating the project to Neo4j before E-code triple scoring exists.
5. Expanding the literature corpus beyond Richmond's 28 papers before the benchmark is stable.
6. Adding broad AI review frameworks that do not improve Richmond comparison.

These may be useful later, but adding them now would make the project harder to finish and harder to explain.

## 7. How This Map Should Affect the Six Main Documents

The six main documents are not designed as long literature reviews. External references are used only where they support a specific decision:

| Main document | External references to use |
|---|---|
| Richmond Golden Standard Memo | Richmond et al. (2020); RAMESES. |
| Entity/Relationship Definition and Modeling Specification | Richmond; RAMESES; GraphRAG; structured information extraction; Leiden only if discussing communities. |
| Entity/Relationship Verification Protocol | Richmond; NER/RE evaluation; strict/relaxed precision, recall, F1; human adjudication. |
| Pipeline Evaluation Framework | PRISMA 2020; PRISMA-S; RAMESES; RAGAS/ARES only for retrieval/reporting faithfulness. |
| Current Project Status and Gap Report | Mostly local project evidence; external citations only for method context. |
| Next-Step Work Plan | Minimal citations; focus on tasks, outputs, and gates. |

## 8. Practical Rule for Future Additions

Before adding a new paper or tool to the main project, ask:

```text
Which project gap does this solve?
Which professor question does this answer?
Which output artifact will change because of it?
Which metric or verification step becomes stronger because of it?
Does it add more clarity than complexity?
```

If the answer is unclear, keep it out of the main documents.

## 9. References and Source Links

Richmond, A., Cooper, N., Gay, S., Atiomo, W., & Patel, R. (2020). The student is key: A realist review of educational interventions to develop analytical and non-analytical clinical reasoning ability. Medical Education, 54(8), 709-719. https://doi.org/10.1111/medu.14137

Wong, G., Greenhalgh, T., Westhorp, G., Buckingham, J., & Pawson, R. (2013). RAMESES publication standards: realist syntheses. BMC Medicine, 11, 21. https://doi.org/10.1186/1741-7015-11-21

Page, M. J., et al. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ, 372, n71. https://doi.org/10.1136/bmj.n71

Rethlefsen, M. L., et al. (2021). PRISMA-S: an extension to the PRISMA Statement for Reporting Literature Searches in Systematic Reviews. Systematic Reviews, 10, 39. https://doi.org/10.1186/s13643-020-01542-z

Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S., Metropolitansky, D., Ness, R. O., & Larson, J. (2024/2025). From Local to Global: A GraphRAG Approach to Query-Focused Summarization. arXiv:2404.16130. https://arxiv.org/abs/2404.16130

Traag, V. A., Waltman, L., & van Eck, N. J. (2019). From Louvain to Leiden: guaranteeing well-connected communities. Scientific Reports, 9, 5233. https://doi.org/10.1038/s41598-019-41695-z

Dunn, A., Dagdelen, J., Walker, N., Lee, S., Rosen, A. S., Ceder, G., Persson, K., & Jain, A. (2022/2024). Structured information extraction from complex scientific text with fine-tuned large language models. arXiv:2212.05238. https://arxiv.org/abs/2212.05238

Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2023). RAGAS: Automated Evaluation of Retrieval Augmented Generation. arXiv:2309.15217. https://arxiv.org/abs/2309.15217

Saad-Falcon, J., Khattab, O., Potts, C., & Zaharia, M. (2023). ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems. arXiv:2311.09476. https://arxiv.org/abs/2311.09476

Yan, S.-Q., Gu, J.-C., Zhu, Y., & Ling, Z.-H. (2024). Corrective Retrieval Augmented Generation. arXiv:2401.15884. https://arxiv.org/abs/2401.15884

Asai, A., Wu, Z., Wang, Y., Sil, A., & Hajishirzi, H. (2023). Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. arXiv:2310.11511. https://arxiv.org/abs/2310.11511

van de Schoot, R., et al. (2020). Open Source Software for Efficient and Transparent Reviews. arXiv:2006.12166. https://arxiv.org/abs/2006.12166
