# Immediate Verification Work Plan

Draft version: 2026-06-15

## 1. Strategic Direction

The project is moving from a working prototype to a verified research pipeline. The immediate objective is to establish a defensible evidence package showing how the AI pipeline will be compared with Richmond et al.'s human realist review.

The strategic direction is:

```text
Richmond benchmark
  -> corpus verification
  -> entity and relationship verification
  -> stage-by-stage pipeline evaluation
  -> final synthesis comparison
  -> research-ready handoff package
```

The work should prioritize verification evidence over additional feature development.

## 2. 48-Hour Sprint Objective

The next phase is scheduled as a 1-2 day verification sprint.

The sprint objective is to convert the current planning documents and prototype outputs into a clear verification package:

1. benchmark definition;
2. current status;
3. known gaps;
4. evaluation metrics;
5. immediate technical outputs;
6. professor-facing project direction.

## 3. Workstreams and Deliverables

| Priority | Workstream | Deliverable | Function |
|---|---|---|---|
| P0 | Project direction consolidation | `documents/Professor_Response_Matrix.md` | Provides one concise entry document for research discussion. |
| P0 | Benchmark clarification | Richmond benchmark section in the response matrix | Defines which gold-standard layers already exist and which require human adjudication. |
| P0 | Corpus verification | `outputs/corpus_coverage_report.md` | Confirms whether all 28 Richmond studies are represented. |
| P0 | CMOC reconciliation | CMOC reconciliation note or updated evaluation report | Resolves the 56-vs-57 CMOC discrepancy. |
| P0 | Relationship verification preparation | Relationship triple export plan | Defines how current relationships become E-code triples for R01-R40 scoring. |
| P1 | KG verification reporting | `outputs/KG_Verification_Report.md` draft | Makes node and edge verification visible and auditable. |
| P1 | Final synthesis comparison | `outputs/Richmond_Comparison_Memo.md` draft | Structures the comparison between AI synthesis and Richmond's human programme theory. |

## 4. Completion Criteria

At the end of the sprint, the project will document:

1. the Richmond benchmark layers available for evaluation;
2. the current corpus coverage status;
3. the official CMOC output count;
4. the relationship export path for R01-R40 scoring;
5. the remaining need for human-adjudicated per-paper gold data;
6. the report structure for KG verification and Richmond comparison.

## 5. Scope Control

The following activities are out of scope until the verification package is stable:

1. expanding beyond the Richmond 28-study benchmark;
2. migrating to a new graph database;
3. training or fine-tuning a new model;
4. adding unrelated external literature;
5. claiming KG verification before relationship metrics exist;
6. sending all supporting documents without an entry matrix.

## 6. Communication Summary

The project now has a defined research direction: Richmond et al. is the benchmark, entities and relationships are CMOC-based graph components, the pipeline is evaluated step by step, and final synthesis is compared with Richmond's programme theory.

The immediate work is to complete verification evidence within 1-2 days by auditing corpus coverage, reconciling current outputs, and preparing entity/relationship metrics.

## 7. Final Handoff Package

The final project handoff should include:

1. professor-facing response matrix;
2. corpus coverage report;
3. KG verification report;
4. pipeline metrics report;
5. Richmond comparison memo;
6. supporting benchmark, ontology, and evaluation documents.

The expected research contribution is:

```text
An evaluated AI-assisted realist synthesis pipeline benchmarked against Richmond et al.'s human realist review.
```

## 8. References

Richmond, A., Cooper, N., Gay, S., Atiomo, W., & Patel, R. (2020). The student is key: A realist review of educational interventions to develop analytical and non-analytical clinical reasoning ability. Medical Education, 54(8), 709-719. https://doi.org/10.1111/medu.14137

Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S., Metropolitansky, D., Ness, R. O., & Larson, J. (2025). From local to global: A GraphRAG approach to query-focused summarization. arXiv:2404.16130v2.
