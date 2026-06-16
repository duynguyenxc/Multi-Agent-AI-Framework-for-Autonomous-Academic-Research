# Project Status Summary: Richmond Realist Synthesis Simulation
**Prepared for:** Prof. Zheng
**Date:** June 15, 2026

## Executive Summary
This report summarizes the verification of the LLM-Knowledge-Graph pipeline against the Richmond et al. (2020) benchmark. We have addressed the evaluation and methodological questions raised in our last meeting, and we now have a defensible measurement system in place. The first measurement shows substantial gaps requiring refinement.

### 1. Corpus Coverage: The "20 vs 28" Question
Our document registry contains 28 files. The CMOC extraction pipeline successfully processed **28/28** of these files, yielding **57 CMOCs**. 
However, the visual GraphRAG tool only indexed 20 files. Our current audit suggests that the remaining 8 files are "abstract-only" and too short for GraphRAG's default chunking logic. Therefore, the extraction is complete (28/28), and the graph visualization reflects the 20 full-text sources.

### 2. Pre-defined Relations & Golden Standard
To answer the question *"Have you pre-defined the relations?"*: Yes. We mapped the pipeline's output to the Richmond Golden Standard (R01-R40).
- The model uses a constrained vocabulary of causal predicates. (Note: The pipeline extracts `INHIBITS`, which we map to `CONSTRAINS` to match the exact 5 R01-R40 verbs: `PROVIDES`, `ENABLES`, `TRIGGERS`, `LEADS_TO`, `CONSTRAINS`).
- The system exports directed E-code triples (e.g., `E07 -> PROVIDES -> E20`) and calculates F1 metrics against human gold standards.
- **Current Baseline Metrics:** Strict F1 is **0.079** and Relaxed F1 is **0.081**. This low baseline is expected for a zero-shot LLM pass and highlights the necessity of the human adjudication step to refine the prompts.

### 3. Transparent Human-in-the-Loop (HITL) Auditing
We have implemented a structured Audit Logger. Rather than the pipeline running to completion automatically, it records "Pending Human Review" at 4 critical checkpoints (Screening, CMOC Validation, Contradiction Adjudication, and Theory Sign-off) into a `hitl_audit_log.jsonl` file.

### 4. Next Action: Per-Paper Adjudication
The pipeline outputs metrics at the **Programme-Theory level**. To calculate granular, per-paper metrics, we have generated `per_paper_adjudication_template.csv`. This template pre-fills the AI's predictions and provides columns for a human researcher to accept, reject, or correct the extraction. This will serve as our final, rigorous evaluation dataset.
