# Pipeline Evaluation Framework

Draft version: 2026-06-15

## 1. Purpose

This framework defines how to evaluate the project pipeline from input papers to knowledge graph, CMOCs, cross-study synthesis, and final programme theory.

It directly answers the professor's main concern:

How do we know the difference between the LLM output and the human Richmond outcome, and what metrics will we use at each step?

## 2. Evaluation Principle

The project is not evaluated only at the final report stage.

Each pipeline step must have:

1. A defined input.
2. A defined output.
3. A gold or reference standard.
4. A metric.
5. A human review point.
6. A refinement action if the output is wrong.

This makes the project auditable. If the final output is wrong, we can identify whether the failure came from corpus coverage, extraction, graph construction, CMOC formation, synthesis, or reporting.

## 3. Final Target of the Project

The final target is not simply to "build a knowledge graph."

The final target is to reproduce and evaluate a machine-assisted realist synthesis pipeline against Richmond et al.'s human realist review. The pipeline should:

1. Represent the same 28-study corpus.
2. Extract clinically meaningful Context, Intervention, Mechanism, and Outcome concepts.
3. Build directed, typed, evidence-supported relationships among those concepts.
4. Generate CMOCs and assign them to Richmond-style programme theory statements.
5. Produce a final synthesis comparable to Richmond's human conclusion.
6. Show where the model agrees, disagrees, misses evidence, or over-generates claims.

The knowledge graph is therefore an intermediate evidence structure, not the final research contribution by itself.

## 4. Pipeline Stages and Evaluation Design

| Stage | Input | Output | Gold / Reference | Metrics | Human Review |
|---|---|---|---|---|---|
| 0. Review question and initial theory | Richmond topic and project question | Review question, scope, initial programme theory | Richmond aim and realist review method | Scope alignment; traceability to Richmond | Confirm project target and inclusion logic. |
| 1. Search and screening | Candidate papers or benchmark registry | Included/excluded study list | Richmond 28 included papers and PRISMA counts | Recall, precision, F1, false negatives | Review all exclusions and uncertain studies. |
| 2. Document ingestion | 20 PDFs plus 8 abstract/metadata records | Text corpus and document registry | `data/studies_metadata.jsonl`; 28-study inventory | Document coverage, extraction success, missing-text count | Confirm each study is represented. |
| 3. GraphRAG indexing | Text corpus | Chunks, embeddings, graph extraction input | 28-study corpus | Indexed document count; chunk coverage | Inspect missing or malformed documents. |
| 4. Entity extraction | Text chunks and prompts | Raw KG nodes | E01-E47 | Entity precision, recall, F1, category accuracy, evidence support | Map raw nodes to E-codes; reject unsupported nodes. |
| 5. Relationship extraction | Raw nodes and text evidence | Directed typed edges | R01-R40 | Strict edge F1, relaxed edge F1, direction accuracy, predicate accuracy, evidence support | Check source, target, predicate, direction, and evidence. |
| 6. CMOC extraction | Papers, KG evidence, ontology | Per-paper CMOCs | Human-adjudicated CMOC gold; interim PTS1-PTS5 alignment | CMOC tuple accuracy, PTS assignment, polarity accuracy, quote support | Review study-level CMOCs and error labels. |
| 7. Cross-study synthesis | Per-paper CMOCs | Demi-regularities, contradictions, PTS synthesis | Richmond five-context programme theory | PTS coverage, chain fidelity, contradiction handling, negative mechanism capture | Confirm synthesis does not flatten context differences. |
| 8. Final programme theory | Synthesized CMOCs and evidence | Final report / programme theory | Richmond final conclusion and discussion | Claim coverage, unsupported-claim rate, alignment with five contexts | Human signoff before final use. |
| 9. Refinement loop | Metrics and human feedback | Revised prompts, mappings, outputs | Prior scored run | Delta in metrics; error reduction | Decide whether to rerun, accept, or stop. |

## 5. Stage 0: Review Question and Initial Theory

Evaluation question:

Does the pipeline address the same realist question as Richmond?

Reference:

- Richmond's review asks how educational interventions develop analytical and non-analytical clinical reasoning, and why they work differently for different learners and contexts.
- Source: `data/paper-Richmond-original.pdf`, Abstract and Introduction.

Required output:

- Review question.
- Scope statement.
- Initial programme theory.
- Inclusion/exclusion criteria.

Metric:

| Metric | Pass Rule |
|---|---|
| Scope alignment | Must include educational interventions, clinical reasoning, undergraduate medical/healthcare students, and analytical/non-analytical reasoning. |
| Realist framing | Must ask what works, for whom, why, and under what circumstances. |
| Traceability | Each scope decision must be linked to Richmond or professor-approved project scope. |

## 6. Stage 1: Search and Screening

Evaluation question:

Can the pipeline recover the same included corpus as Richmond?

Gold:

- 28 included papers.
- Richmond reports 149 full texts retrieved and 28 ultimately included.
- Local source: `data/studies_metadata.jsonl`.

Current project status:

- `main.py` currently uses benchmark mode, which automatically includes all 28 Richmond papers.
- This is acceptable for downstream benchmarking, but it does not evaluate a real screening agent.

Metrics:

| Metric | Formula |
|---|---|
| Screening recall | Richmond included papers recovered / 28. |
| Screening precision | Correct included papers / all papers included by the model. |
| False negatives | Richmond papers incorrectly excluded. |
| False positives | Non-Richmond papers incorrectly included. |

Pass rule:

For the benchmark version, recall is expected to be 28/28 because the included set is provided. For a production search/screening version, false negatives require manual review.

## 7. Stage 2: Document Ingestion

Evaluation question:

Are all 28 Richmond studies available to the pipeline in a usable text form?

Reference:

- 20 local PDF full texts.
- 8 abstract/metadata-only records.
- Source: `outputs/evidence_base/study_inventory.tsv`.

Current project concern:

- `graphrag/input` contains 28 text records.
- `outputs/graphrag_data/stats.json` reports 20 indexed documents.
- This must be resolved before official KG evaluation.

Metrics:

| Metric | Pass Rule |
|---|---|
| Study registry coverage | 28/28 records present. |
| Full-text extraction coverage | 20/20 PDFs extracted. |
| Abstract record coverage | 8/8 abstract records represented and labelled. |
| Index coverage | Official KG index should represent 28/28 records. |

Refinement action:

If fewer than 28 records are indexed, rebuild the KG index and produce a document-level coverage report before continuing.

## 8. Stage 3: GraphRAG Indexing

Evaluation question:

Does GraphRAG receive and index the correct corpus?

Required output:

- Document registry.
- Chunk table.
- Entity extraction input.
- Graph extraction logs or stats.

Metrics:

| Metric | Meaning |
|---|---|
| Indexed document count | Number of documents represented in graph index. |
| Chunk coverage | Whether each study contributes chunks. |
| Empty document count | Documents with no usable extracted text. |
| Evidence traceability | Whether later nodes/edges can point back to document/chunk evidence. |

Pass rule:

No official entity or relationship score is reported unless corpus coverage is first confirmed.

## 9. Stage 4: Entity Extraction

Evaluation question:

Does the model extract Richmond-relevant concepts, and can those concepts be mapped to E01-E47?

Gold:

- E01-E47 in `data/gold_standard.json`.

Required output:

- Raw node list.
- Node category.
- Evidence source.
- Mapping to E-code or rejection reason.

Metrics:

| Metric | Target |
|---|---|
| Strict entity precision | Count only exact E-code matches. |
| Strict entity recall | Count recovered E-codes out of 47. |
| Relaxed entity F1 | Allow approved synonyms and abstraction-level matches. |
| Category accuracy | Correct C/I/M/O family assignment. |
| Evidence support rate | Accepted entities should have source evidence. |
| Unmapped rate | Should be reviewed and reduced over refinement rounds. |

Current baseline:

- `outputs/Phase1_Evaluation.md` reports E-code coverage of 0.66.
- This is useful as an interim coverage metric, but it is not yet a complete KG node verification score because raw GraphRAG nodes still need systematic E-code mapping.

Refinement action:

If entity recall is low, inspect missing E-codes by category and update prompts, ontology examples, or normalization rules.

## 10. Stage 5: Relationship Extraction

Evaluation question:

Does the model produce directed, typed, evidence-supported relationships that match Richmond's programme theory?

Gold:

- R01-R40 in `data/gold_standard.json`.

Required output:

```text
source_e_code
predicate
target_e_code
source_document
evidence
confidence
```

Metrics:

| Metric | Meaning |
|---|---|
| Strict edge precision | Exact source-predicate-target matches / predicted triples. |
| Strict edge recall | Gold R01-R40 triples recovered / 40. |
| Strict edge F1 | Overall exact edge performance. |
| Direction accuracy | Correct direction among conceptually matched edges. |
| Predicate accuracy | Correct relation type among matched source-target pairs. |
| Relaxed edge F1 | Allows approved predicate aliases and human-approved equivalent entities. |
| Evidence support rate | Edges with source evidence / accepted edges. |

Current gaps:

- `outputs/relationships_long.json` uses local within-CMOC IDs, not E-code triples.
- `scripts/evaluate_phase1.py` does not yet compute strict edge fidelity against R01-R40.
- `core/ontology.py` must be reconciled with the gold predicate `CONSTRAINS`.

Refinement action:

Materialize relationships into E-code triples, score against R01-R40, then inspect missing edges and wrong-predicate edges separately.

## 11. Stage 6: CMOC Extraction

Evaluation question:

Can the model extract Context-Mechanism-Outcome configurations from each study in a way that supports Richmond's theory?

Gold:

- Interim: Richmond PTS1-PTS5 and E-code coverage.
- Strong: a new human-adjudicated per-paper CMOC gold table.

Required output:

```text
paper_id
context
intervention
mechanism_resource
mechanism_response
outcome
pts_assignment
polarity
evidence
```

Metrics:

| Metric | Meaning |
|---|---|
| CMOC count per paper | Detects under-extraction and over-extraction. |
| Tuple accuracy | Correct context, mechanism, outcome combination. |
| PTS assignment accuracy | Correct assignment to PTS1-PTS5. |
| Polarity accuracy | Correct positive, negative, mixed, or unclear label. |
| Quote/evidence support | Accepted CMOCs supported by paper text. |
| Multi-CMOC rate | Whether the model avoids one-CMOC-per-paper oversimplification. |

Current status:

- Current outputs report either 56 or 57 CMOCs depending on artifact.
- `outputs/evidence_table.md` and `outputs/PRISMA_report.md` report 57 CMOCs.
- `outputs/Phase1_Evaluation.md` reports 56 CMOCs.
- This mismatch must be reconciled before using CMOC count as an official result.

Refinement action:

Create a single canonical CMOC output file, score it, and log differences between generated CMOCs and human-adjudicated CMOCs.

## 12. Stage 7: Cross-Study Synthesis

Evaluation question:

Does the model synthesize across studies in the same conceptual structure as Richmond?

Gold:

- Richmond's five-context programme theory.
- PTS1-PTS5 in `data/gold_standard.json`.

Required output:

- PTS-specific synthesis sections.
- Demi-regularities.
- Contradiction register.
- Evidence table linking claims to studies.

Metrics:

| Metric | Pass Rule |
|---|---|
| PTS coverage | Must recover all 5 Richmond PTS categories. |
| Chain fidelity | CMOCs should follow valid realist chains. |
| Negative mechanism capture | Must include low confidence, cognitive load, stress, and negative outcomes where supported. |
| Contradiction handling | Must identify where the same intervention works differently under different contexts. |
| Evidence traceability | Each synthesis claim should link to supporting studies. |

Current baseline:

- `outputs/Phase1_Evaluation.md` reports PTS coverage of 1.0.
- It also reports ontology chain fidelity of 0.411, which indicates that coverage alone is not enough. The model may mention all PTS categories while still producing weak or incomplete chains.

Refinement action:

Prioritize chain fidelity and negative-mechanism correctness, not only PTS coverage.

## 13. Stage 8: Final Programme Theory and Report

Evaluation question:

Does the final report match Richmond's human conclusion without making unsupported claims?

Gold:

- Richmond final conclusion and Discussion.
- Five context-specific programme theory statements.

Metrics:

| Metric | Meaning |
|---|---|
| Final claim coverage | Does the report include Richmond's main conclusions? |
| Context sensitivity | Does it avoid one-size-fits-all claims? |
| Analytical/non-analytical balance | Does it discuss both reasoning forms and when each is appropriate? |
| Unsupported claim rate | Claims without evidence / all claims. |
| Omission list | Richmond conclusions missing from model output. |
| Contradiction list | Model claims that conflict with Richmond. |

Pass rule:

The final report must recover the Richmond conclusion that intervention effectiveness depends on learner knowledge, confidence, self-efficacy, coping, feedback, and opportunities to practice reasoning in authentic or simulated settings.

## 14. Stage 9: Human-in-the-Loop Refinement

Incorrect outputs are handled through a controlled refinement loop.

Recommended loop:

1. Run one pipeline stage.
2. Score the output.
3. Human reviewer labels errors.
4. Localize the error source.
5. Update only the relevant prompt, schema, mapping rule, or extraction logic.
6. Rerun the affected stage.
7. Compare metrics before and after.
8. Freeze the improved output or log why it remains unresolved.

Error localization table:

| If the Error Is... | Likely Cause | Refinement Action |
|---|---|---|
| Missing study | Corpus/indexing problem | Rebuild document registry and GraphRAG index. |
| Missing entity category | Prompt or ontology example too weak | Add category examples and mapping rules. |
| Wrong E-code | Normalization problem | Improve E-code mapping table and human examples. |
| Wrong edge direction | Relation prompt/schema problem | Add directed triple examples and direction tests. |
| Wrong relation type | Predicate vocabulary problem | Freeze relation set and add alias mapping. |
| Missing negative mechanism | Model bias toward positive findings | Add negative CMOC examples and polarity scoring. |
| Weak final theory | Cross-study synthesis problem | Require PTS-specific evidence and contradiction handling. |
| Unsupported claim | Reporting problem | Enforce source-linked claims only. |

Current project gap:

The existing orchestrator has human-in-the-loop checkpoints, but benchmark behavior can auto-approve outputs. For final evaluation, auto-approval is replaced by explicit review records.

## 15. Minimum Publication-Ready Evaluation Package

Before project results are claimed, the following package is produced:

| Artifact | Why It Matters |
|---|---|
| Corpus coverage report | Shows all 28 Richmond studies are represented. |
| Richmond gold memo | Defines what the human benchmark is. |
| Entity mapping table | Makes node verification auditable. |
| Relationship triple table | Makes edge verification auditable. |
| CMOC adjudication table | Creates per-paper extraction gold. |
| Pipeline metrics report | Shows performance at each stage. |
| Error analysis report | Shows what failed and how it was refined. |
| Final Richmond comparison memo | Shows agreement, disagreement, omissions, and added claims. |

## 16. Immediate Next Work Plan

The next work should follow this order:

1. Freeze the Richmond programme-theory gold package: E01-E47, R01-R40, and PTS1-PTS5.
2. Reconcile the 56 vs 57 CMOC mismatch in current outputs.
3. Verify or rebuild GraphRAG indexing so all 28 records are represented.
4. Convert generated relationships into directed E-code triples.
5. Add strict and relaxed relationship metrics against R01-R40.
6. Create the per-paper CMOC adjudication table, starting with the 20 full-text PDFs and marking the 8 abstract-only records separately.
7. Run the full pipeline evaluation and produce a stage-by-stage metrics report.
8. Use human review to refine the weakest stage before writing final project claims.

## 17. Current Status Summary

What the project already has:

- A 28-study Richmond benchmark registry.
- 20 PDF full-text papers and 8 abstract/metadata records.
- A Richmond-derived gold entity set: E01-E47.
- A Richmond-derived gold relationship set: R01-R40.
- Five programme theory statements: PTS1-PTS5.
- A working multi-agent pipeline that generates CMOCs and reports.
- Preliminary Phase 1 metrics.

What the project still needs:

- Verified 28-document KG indexing.
- Strict entity and relationship verification tables.
- E-code materialization for relationship outputs.
- Reconciled CMOC counts.
- Human-adjudicated per-paper CMOC gold.
- Explicit human review records instead of auto-approval for official evaluation.

## 18. Conclusion

This framework turns the project from "we built a graph" into a defensible research workflow:

Richmond is the human reference. The KG is an intermediate structure. The final contribution is an evaluated pipeline that shows whether LLM-assisted realist synthesis can recover Richmond's programme theory, where it agrees, where it fails, and how human feedback improves it.

## 19. Citation and Evidence Policy

This framework uses three levels of evidence:

1. Richmond et al. (2020) as the human realist synthesis benchmark.
2. GraphRAG and related graph-based retrieval work as the technical rationale for graph-supported sensemaking.
3. Local repository artifacts as implementation evidence for what the current pipeline actually does.

The final project paper should distinguish local project evidence from external scholarly evidence. Local artifacts are reported as implementation evidence, while published papers justify the research design, evaluation logic, and methodological contribution.

## 20. References

Richmond, A., Cooper, N., Gay, S., Atiomo, W., & Patel, R. (2020). The student is key: A realist review of educational interventions to develop analytical and non-analytical clinical reasoning ability. Medical Education, 54(8), 709-719. https://doi.org/10.1111/medu.14137

Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S., Metropolitansky, D., Ness, R. O., & Larson, J. (2025). From local to global: A GraphRAG approach to query-focused summarization. arXiv:2404.16130v2.

Professor project abstract. (2026). Proposed AI Agent Pipeline for Systematic Review in Education. Local file: `documents/abstract-from-professor/abstract.md`.

Professor verification plan. (2026). Plan for model verification using Richmond et al. as benchmark. Local file: `documents/plan_verification_text.txt`.
