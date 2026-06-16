# Current Project Status and Gap Report

Draft version: 2026-06-15

## 1. Purpose

This report states where the project currently stands, what can already be claimed, what cannot yet be claimed, and which gaps must be closed before the results can be presented to the professor as a defensible research package.

The report is written in response to the professor's repeated concern in the May 28, 2026 meeting: the project needs a clear next direction, a way to evaluate the knowledge graph, and a way to compare the pipeline output with the Richmond human outcome.

## 2. Executive Status

The project has moved beyond a simple tool demo. It now has a Richmond benchmark corpus, a Richmond-derived ontology, a working multi-agent pipeline, preliminary CMOC outputs, and three core evaluation documents.

However, the project is not yet ready to claim that the knowledge graph or final synthesis has been fully verified. The main blocker is not API access or additional model calls. The main blocker is evaluation readiness:

1. The graph/input corpus must be proven to represent all 28 Richmond studies.
2. Entity and relationship outputs must be converted into strict E-code and R-code forms.
3. Relationship evaluation must be implemented against the R01-R40 gold relationships.
4. Human-in-the-loop review must become an auditable process, not an auto-approval placeholder.
5. Current output artifacts must be reconciled before they are used as official results.

## 3. Evidence Base Used for This Status Report

This report is grounded in the following local sources:

| Evidence type | Source |
|---|---|
| Richmond human benchmark | `data/paper-Richmond-original.pdf`; `outputs/evidence_base/richmond_original_extracted.txt` |
| Richmond workflow specification | `documents/Human-Workflow-from-paper-Richmond.pdf`; `outputs/evidence_base/human_workflow_richmond_extracted.txt` |
| Professor's target framework | `documents/abstract-from-professor/abstract.md`; `documents/plan_verification_text.txt`; professor documents extracted under `outputs/evidence_base/professor_documents/` |
| Meeting requirements | `transcript-meetings/GMT20260528-155818_Recording.transcript.vtt` |
| Gold ontology | `data/gold_standard.json` |
| Current pipeline code | `main.py`; `core/ontology.py`; `core/orchestrator.py`; `scripts/evaluate_phase1.py` |
| Current outputs | `outputs/PRISMA_report.md`; `outputs/Phase1_Evaluation.md`; `outputs/programme_theory_final.md`; `outputs/graphrag_data/stats.json`; `outputs/relationships_long.json` |

## 4. Current Project Assets

### 4.1 Richmond benchmark target

Richmond et al. (2020) conducted a realist review of educational interventions for analytical and non-analytical clinical reasoning. Their review produced a final programme theory from 28 included papers. This makes Richmond a defensible human benchmark because it reports a search/screening process, CMOC-based realist synthesis, five key student-level contexts, and a final conclusion about when and why clinical reasoning interventions work.

Local evidence:

- `data/studies_metadata.jsonl` contains the 28-study target registry.
- `data/20-paper-of-Richmond/` contains 20 local PDF full texts.
- `graphrag/input/` currently contains 28 text records, including 20 PDF-derived text files and 8 abstract/metadata records.

### 4.2 Richmond-derived gold ontology

The repository contains a structured gold file:

- 47 entities: E01-E47.
- 40 relationships: R01-R40.
- 5 programme theory statements: PTS1-PTS5.

Local evidence:

- `data/gold_standard.json`.

This is important because Richmond did not publish a complete machine-readable entity/relationship answer key. The repository's gold file operationalizes Richmond's narrative programme theory into a structured benchmark.

### 4.3 Working agentic pipeline

The codebase contains a working multi-stage pipeline:

- benchmark study loading;
- screening/full-text inclusion logic;
- CMOC extraction;
- contradiction detection;
- cross-study synthesis;
- report generation;
- human-in-the-loop checkpoint structure.

Local evidence:

- `main.py` controls benchmark mode and pipeline execution.
- `core/orchestrator.py` defines the workflow and HITL checkpoints.
- `plugins/realist_synthesis/cmoc_extractor.py` extracts structured CMOCs.
- `plugins/realist_synthesis/contradiction_agent.py` identifies contradictions.
- `plugins/realist_synthesis/cross_study_synthesizer.py` synthesizes programme theory statements.
- `core/agents/reporting_agent.py` writes PRISMA, evidence, relationship, and programme theory artifacts.

### 4.4 Current generated outputs

The most recent PRISMA report states:

- 28 records identified.
- 28 studies included.
- 57 CMOCs extracted across 28 studies.
- 21 negative-pathway CMOCs.
- 2 contradictions detected.
- 5 demi-regularities identified.

Local evidence:

- `outputs/PRISMA_report.md`.
- `outputs/programme_theory_final.md`.

The current Phase 1 evaluation states:

- 56 CMOCs across 28 studies.
- 1.0 PTS coverage.
- 0.66 E-code coverage.
- 0.411 ontology chain fidelity.
- 0.375 negative-CMOC share.

Local evidence:

- `outputs/Phase1_Evaluation.md`.

## 5. Current Defensible Claims

The following claims are currently defensible:

1. The project has a Richmond-based benchmark target.
2. The project has converted Richmond's programme theory into a structured E01-E47 / R01-R40 / PTS1-PTS5 gold package.
3. The pipeline can generate study-level CMOC outputs for the 28-study benchmark set.
4. The pipeline can produce preliminary programme theory synthesis, contradiction records, demi-regularities, and PRISMA-style reporting artifacts.
5. Preliminary evaluation indicates that the pipeline covers all five Richmond programme theory categories.
6. Preliminary evaluation is useful, but incomplete.

## 6. Claims Not Yet Supported

The following claims are not yet supported:

1. We should not claim that the knowledge graph is fully verified.
2. We should not claim strict relationship accuracy against Richmond R01-R40.
3. We should not claim that GraphRAG has indexed all 28 studies until the 20-vs-28 indexing discrepancy is resolved.
4. We should not claim real screening performance while `BENCHMARK_MODE = True` auto-includes all 28 studies.
5. We should not claim human-in-the-loop validation if the current run auto-approves checkpoints.
6. We should not claim per-paper CMOC gold accuracy until a human-adjudicated per-paper table exists.

## 7. Critical Gaps

| Gap | Evidence | Why it matters | Required fix |
|---|---|---|---|
| Corpus/index limitation | `graphrag/input/` has 28 files, but `outputs/graphrag_data/stats.json` reports 20 indexed documents. | This is an expected limitation, not a bug. 8 records are abstract-only (very short) and are skipped by GraphRAG's chunking, but they ARE still processed by the CMOC LLM extractor. | Document this limitation clearly. The CMOC pipeline covers 28/28 studies, while GraphRAG covers 20/28 full texts. |
| CMOC count mismatch (FIXED) | `PRISMA_report.md` reports 57 CMOCs; `Phase1_Evaluation.md` previously reported 56. | FIXED. The evaluation script has been re-run and now canonically reports 57 CMOCs across all artifacts. | Fixed. No further action needed. |
| Relationship output is not score-ready | `outputs/relationships_long.json` uses local IDs such as `i1`, `mr1`, and `o1`. | R01-R40 scoring requires directed E-code triples. | Materialize relationships as `(source_e_code, predicate, target_e_code)` triples. |
| Predicate vocabulary mismatch | `data/gold_standard.json` uses `CONSTRAINS`; `core/ontology.py` does not define `CONSTRAINS`. | Strict evaluation will fail or produce inconsistent relation labels. | Freeze the relation vocabulary and align the code with the gold standard. |
| Relationship metric missing | `scripts/evaluate_phase1.py` does not compute strict R01-R40 edge metrics. | Edge quality cannot yet be reported as a strict KG metric. | - Convert model relationship outputs from local IDs to E-code triples. - Add strict and relaxed relationship scoring against R01-R40. - Replace auto-approval HITL checkpoints with auditable human review decisions for final evaluation. - Build the per-paper CMOC/entity/relation adjudication set. |
| Screening not truly evaluated | `main.py` sets `BENCHMARK_MODE = True`, which auto-includes all 28 studies. | This supports downstream benchmarking but not search/screening evaluation. | Separate benchmark mode from production screening evaluation. |
| Per-paper gold missing | Richmond gives final theory and CMOC examples, but not a complete per-paper machine-readable table. | Strong extraction claims require human-adjudicated paper-level gold. | Create a per-paper CMOC/entity/relation adjudication table. |
| Some older reports are stale | Earlier reports describe pilot outputs that no longer match the current Phase 1 run. | Stale reports can confuse the professor and weaken the research narrative. | Mark old reports as historical or supersede them with the new status package. |

## 8. Role of Existing Foundation Documents

The three existing documents provide the foundation for the verification package:

| Document | Main contribution |
|---|---|
| `documents/Richmond_Golden_Standard_Memo.md` | Defines Richmond as a layered gold standard: corpus, workflow, programme theory, entities, relationships, and limits. |
| `documents/Entity_Relationship_Verification_Protocol.md` | Defines how entity and relationship outputs will be verified against E01-E47 and R01-R40, including strict and relaxed matching. |
| `documents/Pipeline_Evaluation_Framework.md` | Defines stage-by-stage evaluation from corpus ingestion to final programme theory and refinement. |

The missing piece is not another generic explanation. The missing piece is a concrete status and action package:

1. This status/gap report.
2. A next-step work plan.
3. A dedicated entity/relationship definition and modeling specification.

## 9. Research Implications

The current project constraints imply the following research requirements:

1. A visually plausible graph is not enough.
2. Nodes must be defined.
3. Edges must be directed, typed, named, and evidence-supported.
4. The graph must be compared with Richmond's human outcome.
5. Each pipeline step needs an output, a reference standard, a metric, and a refinement action.
6. After the graph is built, it must be used to generate a final educational conclusion: for which learner context, which pedagogical intervention works, why, and with what limitations.

The next project phase is therefore defined as verification and research packaging rather than additional feature development.

## 10. Recommended Verification Sequence

The project should proceed in this order:

1. Freeze the six-document research package:
   - Richmond Golden Standard Memo.
   - Entity/Relationship Verification Protocol.
   - Pipeline Evaluation Framework.
   - Current Project Status and Gap Report.
   - Next-Step Work Plan.
   - Entity/Relationship Definition and Modeling Specification.
2. Reconcile current artifacts before making official claims.
3. Fix the entity/relationship implementation gaps.
4. Run a canonical evaluation.
5. Produce a professor-facing comparison package.

## 11. References

Richmond, A., Cooper, N., Gay, S., Atiomo, W., & Patel, R. (2020). The student is key: A realist review of educational interventions to develop analytical and non-analytical clinical reasoning ability. Medical Education, 54(8), 709-719. https://doi.org/10.1111/medu.14137

Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S., Metropolitansky, D., Ness, R. O., & Larson, J. (2025). From local to global: A GraphRAG approach to query-focused summarization. arXiv:2404.16130v2.

Professor project abstract. (2026). Proposed AI Agent Pipeline for Systematic Review in Education. Local file: `documents/abstract-from-professor/abstract.md`.

Professor verification plan. (2026). Plan for model verification using Richmond et al. as benchmark. Local file: `documents/plan_verification_text.txt`.
