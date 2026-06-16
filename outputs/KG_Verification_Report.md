# Knowledge Graph Verification Report
**Date:** June 15, 2026

## 1. Corpus & Extraction Completeness
The CMOC pipeline successfully processed **28/28 studies** and extracted **57 unique CMOCs**. 
*Note on Visual Graph (GraphRAG):* GraphRAG indexes 20/28 documents. The remaining 8 are abstract-only and are skipped by GraphRAG's chunking algorithm due to their short length. This is an expected visualization limitation, not an extraction failure.

## 2. Programme-Theory Benchmark
The extracted CMOCs were decomposed into relationship triples (Source -> Predicate -> Target) and scored against the Richmond (2020) R01-R40 golden standard.

*(Detailed relationship metrics are stored in `Phase1_Relationship_Evaluation.md`)*
- **Strict Matching** (Source + Predicate + Target)
- **Relaxed Matching** (Source + Target)
- **Error Analysis** tracks missing gold edges, extra predictions, wrong direction, and wrong predicates.

## 3. Human-in-the-loop (HITL) Audit
All pipeline checkpoints now support explicit structured logging (`HITL_Audit_Log.md` and `hitl_audit_log.jsonl`) configurable in `demo` or `review` mode, preventing silent auto-approvals in production research.

## 4. Next Steps
A per-paper adjudication template (`per_paper_adjudication_template.csv`) has been generated. The model's context, intervention, mechanism, outcome, and triples are pre-filled. Human reviewers must now complete the "human corrected" columns.
