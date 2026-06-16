# Project Direction and Verification Matrix

Draft version: 2026-06-15

## 1. Executive Summary

This matrix consolidates the project's current research direction, benchmark position, verification status, and immediate work plan. It is intended to provide a concise entry point before the supporting documents are reviewed.

The project direction is to transform the current AI and knowledge-graph prototype into a verified research pipeline. Richmond et al. (2020) is used as the human benchmark. The AI-generated outputs will be evaluated at the levels of corpus coverage, entity mapping, relationship triples, CMOC structure, cross-study synthesis, and final programme theory alignment.

## 2. Direction Statement

The core direction is:

```text
Benchmark against Richmond
  -> verify corpus representation
  -> verify entities and relationships
  -> evaluate pipeline stages
  -> compare final synthesis with Richmond
  -> produce a defensible research evidence package
```

The intended research claim is:

```text
This project evaluates whether an AI-assisted GraphRAG and multi-agent pipeline can reproduce key analytic operations of Richmond et al.'s human realist review, including corpus representation, entity/relationship modeling, CMOC extraction, synthesis, contradiction handling, and final programme theory comparison.
```

## 3. Verification Matrix

| Project issue | Current position | Evidence base | Verification action |
|---|---|---|---|
| Final project goal | Produce and evaluate an AI-assisted realist synthesis pipeline against Richmond's human review. | `Pipeline_Evaluation_Framework.md`; current matrix. | Maintain focus on verified synthesis rather than graph visualization. |
| Richmond benchmark | Richmond provides a layered benchmark: 28 included studies, human realist workflow, five context-specific programme theory findings, final conclusion, and E01-E47/R01-R40 operationalization. | `Richmond_Golden_Standard_Memo.md`; `data/gold_standard.json`. | Use Richmond for corpus, theory, entity, relationship, and final synthesis comparison. |
| Available gold standard | Gold exists at the corpus, programme-theory, entity, and relationship-structure levels. Full per-paper extraction gold is not yet available. | 28-study registry; E01-E47; R01-R40; PTS1-PTS5. | Create a human-adjudicated per-paper CMOC/entity/relation table after the initial verification package. |
| Richmond conclusion | Intervention effects depend on learner knowledge, confidence, self-efficacy, coping, feedback, and opportunities for clinical reasoning practice. | Richmond et al. (2020); `Richmond_Golden_Standard_Memo.md`. | Compare AI final synthesis against Richmond's five-context programme theory. |
| Entity definition | An entity is a Richmond-relevant realist synthesis concept: Context, Intervention, Mechanism Resource, Mechanism Response, or Outcome. | `Entity_Relationship_Definition_Modeling_Specification.md`; E01-E47. | Normalize raw graph nodes to E01-E47 or classify them as rejected/new human-approved concepts. |
| Relationship definition | A relationship is a directed, typed, evidence-supported link between two normalized entities. | `Entity_Relationship_Definition_Modeling_Specification.md`; R01-R40. | Export model edges as `(source_e_code, predicate, target_e_code)` triples. |
| Relation vocabulary | Final edge types are PROVIDES, ENABLES, TRIGGERS, LEADS_TO, and CONSTRAINS. | `data/gold_standard.json`; entity/relationship specification. | Align code and output artifacts with the frozen relation vocabulary. |
| KG verification status | Preliminary outputs exist, but KG verification is incomplete. | Current gaps: 20-vs-28 GraphRAG issue, 56-vs-57 CMOC mismatch, no strict R01-R40 relationship F1. | Audit corpus coverage, reconcile CMOC count, and compute entity/relationship metrics. |
| AI-human comparison | Comparison will be performed at multiple levels: corpus coverage, entity mapping, relationship triples, CMOC structure, PTS coverage, contradiction handling, and final programme theory alignment. | `Pipeline_Evaluation_Framework.md`; `Entity_Relationship_Verification_Protocol.md`. | Produce `KG_Verification_Report.md`, `Pipeline_Metrics_Report.md`, and `Richmond_Comparison_Memo.md`. |
| Error refinement | Errors will be localized, categorized, corrected through prompt/schema/mapping updates, rerun, and re-scored. | HITL refinement loop in evaluation and verification documents. | Replace auto-approval behavior with human-readable review records for official evaluation. |
| Post-KG use | The KG supports CMOC extraction, cross-study synthesis, contradiction detection, and final programme theory comparison. | Current pipeline generates CMOCs, contradictions, demi-regularities, and programme theory text. | Verify the KG before using it as evidence for final comparison. |
| Immediate execution direction | Complete a 48-hour verification sprint. | `Next_Step_Work_Plan.md`. | Finish corpus audit, CMOC reconciliation, relationship triple export plan, and report structures. |

## 4. Immediate Verification Sprint

The next work phase is a 48-hour verification sprint.

| Priority | Deliverable | Function |
|---|---|---|
| P0 | `Professor_Response_Matrix.md` | Concise project direction and verification matrix. |
| P0 | `outputs/corpus_coverage_report.md` | Confirms representation of all 28 Richmond studies. |
| P0 | CMOC reconciliation note | Resolves the official CMOC count. |
| P0 | Relationship triple export plan | Defines conversion from current relationship outputs to R01-R40 scoring format. |
| P1 | `outputs/KG_Verification_Report.md` draft | Prepares node and edge verification reporting. |
| P1 | `outputs/Richmond_Comparison_Memo.md` draft | Prepares AI-vs-human synthesis comparison. |

## 5. Supporting Documentation

The response matrix is the entry document. The supporting documents provide detail when needed.

| Supporting document | Function |
|---|---|
| `Professor_Project_Briefing.md` | Concise project overview. |
| `Richmond_Golden_Standard_Memo.md` | Richmond benchmark definition. |
| `Entity_Relationship_Definition_Modeling_Specification.md` | Entity and relationship semantics. |
| `Entity_Relationship_Verification_Protocol.md` | Entity and relationship metrics. |
| `Pipeline_Evaluation_Framework.md` | Stage-by-stage evaluation design. |
| `Current_Project_Status_Gap_Report.md` | Current assets, gaps, and unsupported claims. |
| `Next_Step_Work_Plan.md` | Immediate verification work plan. |
| `Selective_Research_Foundation_Map.md` | Reference and tool selection policy. |

## 6. Conclusion

The project has a defined direction and benchmark structure. The immediate requirement is to convert the current prototype and planning documents into verification evidence: corpus coverage, reconciled CMOC counts, relationship triples, KG metrics, and final Richmond comparison.
