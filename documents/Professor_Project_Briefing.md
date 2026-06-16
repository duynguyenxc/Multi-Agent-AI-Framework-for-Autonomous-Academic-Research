# Project Briefing Report

Draft version: 2026-06-15

## 1. Executive Summary

This project develops and evaluates an AI-assisted, knowledge-graph-supported pipeline for realist evidence synthesis. Richmond et al. (2020) is used as the benchmark case because it provides a completed human realist review of 28 studies, a final programme theory, and a clear conclusion about educational interventions for clinical reasoning.

The immediate research objective is to determine whether the current AI pipeline can reproduce key analytic operations from the Richmond review, including corpus representation, concept extraction, relationship modeling, CMOC construction, cross-study synthesis, contradiction handling, and final programme theory comparison.

The project is currently in the transition from prototype output to verification-ready research evidence.

## 2. Project Background

Richmond et al. manually reviewed 28 papers to explain which educational interventions support clinical reasoning, for which learners, under what circumstances, and through what mechanisms. This type of realist review is rigorous but time-consuming and difficult to scale.

The proposed project investigates whether an AI-assisted workflow can structure parts of this process while preserving human oversight, traceability, and evaluation against a known human reference.

## 3. Benchmark Rationale

Richmond et al. is treated as the benchmark because it provides:

1. A 28-study included corpus.
2. A documented human realist review workflow.
3. A final programme theory.
4. Five main student-level contexts explaining intervention success or failure.
5. A final conclusion about the importance of learner knowledge, self-confidence, self-efficacy, coping, feedback, and practice opportunities.

Richmond is therefore more than background literature. It is the reference case used to evaluate whether the AI pipeline reaches comparable conclusions.

## 4. Pipeline Overview

The intended workflow is:

```text
Richmond 28-study corpus
  -> document ingestion
  -> entity extraction
  -> relationship extraction
  -> knowledge graph construction
  -> CMOC extraction
  -> cross-study synthesis
  -> final programme theory generation
  -> comparison with Richmond's human synthesis
```

The knowledge graph is an intermediate evidence structure. The final research contribution is the evaluated pipeline and its comparison with the Richmond human review.

## 5. Entity and Relationship Definitions

An entity is a review-relevant realist synthesis concept, not any arbitrary word or phrase. Official entity categories are:

1. Context.
2. Intervention.
3. Mechanism Resource.
4. Mechanism Response.
5. Outcome.

A relationship is a directed, typed, evidence-supported connection between two normalized entities. For final evaluation, each relationship requires:

1. source entity;
2. target entity;
3. relation type;
4. direction;
5. evidence source.

This definition ensures that the graph can be evaluated scientifically rather than treated as a visual artifact.

## 6. Current Project Assets

The project currently has:

1. The Richmond original paper.
2. A 28-study Richmond registry.
3. 20 full-text PDFs and 8 abstract/metadata-only records.
4. A Richmond-derived gold package:
   - 47 entities: E01-E47.
   - 40 relationships: R01-R40.
   - 5 programme theory statements: PTS1-PTS5.
5. A working prototype pipeline that generates CMOCs and reports.
6. Preliminary outputs including PRISMA-style reporting, evidence tables, programme theory text, contradictions, and demi-regularities.
7. Supporting documents defining the benchmark, entity/relationship logic, evaluation framework, current gaps, and immediate work plan.

## 7. Current Verification Limitations

The current outputs are not yet sufficient to claim that the knowledge graph is fully verified.

The main limitations are:

1. GraphRAG indexing must be audited because current evidence suggests a 20-vs-28 document mismatch.
2. Current outputs disagree on whether the pipeline produced 56 or 57 CMOCs.
3. Relationship outputs must be converted into E-code triples before comparison with R01-R40.
4. The relation type `CONSTRAINS` must be aligned between the gold standard and code implementation.
5. Human-in-the-loop checkpoints need stronger review records.
6. A per-paper human-adjudicated CMOC/entity/relation table is still required for strong extraction claims.

## 8. Document Package Structure

The supporting documents serve different functions:

| Document | Function |
|---|---|
| `Richmond_Golden_Standard_Memo.md` | Defines Richmond as the benchmark. |
| `Entity_Relationship_Definition_Modeling_Specification.md` | Defines node and edge semantics. |
| `Entity_Relationship_Verification_Protocol.md` | Defines entity and relationship verification. |
| `Pipeline_Evaluation_Framework.md` | Defines stage-by-stage pipeline evaluation. |
| `Current_Project_Status_Gap_Report.md` | Reports current assets, gaps, and unsupported claims. |
| `Next_Step_Work_Plan.md` | Defines the immediate verification work plan. |
| `Selective_Research_Foundation_Map.md` | Defines the selection policy for external references and tools. |

## 9. Immediate Verification Agenda

The next phase is a 48-hour verification sprint focused on producing evidence rather than additional conceptual planning:

1. Create a professor-facing response matrix.
2. Audit representation of all 28 Richmond studies.
3. Reconcile the 56-vs-57 CMOC discrepancy.
4. Convert relationship outputs into directed E-code triples.
5. Prepare relationship evaluation against R01-R40.
6. Draft the KG verification report and Richmond comparison memo.

## 10. Conclusion

The project direction is to benchmark Richmond, verify knowledge-graph entities and relationships, evaluate each pipeline stage, compare final synthesis with Richmond, and package the result as a defensible research contribution.

The project is presented as an evaluated AI-assisted realist synthesis pipeline rather than a graph-building exercise.
