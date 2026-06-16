# Phase 1 Improvement Report — Multi-CMOC + PTS-Aware Realist Synthesis

Generated: 2026-05-27
Run duration: 29.6 min (28 studies, 4 LLM models)
Baseline reference: previous evidence_table.json (v3.0, single-CMOC pre-Phase-1)
Gold-standard reference: `data/gold_standard.json` (Richmond E01–E47 + R01–R40 + PTS1–5)

---

## 1. Executive Summary

Phase 1 refactor replaced the legacy single-CMOC, E20-default schema with a
multi-CMOC, programme-theory-anchored schema. The pipeline now:

- Extracts **56 distinct CMOCs from 28 papers** (2.0 × baseline) instead of 28 CMOCs
- Populates **all 5 Programme Theory Statements** (Richmond's PTS1–PTS5) instead of collapsing onto PTS1
- Generates **21 negative-pathway CMOCs** (37% of total) — previously 0
- Uses **31 of Richmond's 47 entity codes** (66% E-code coverage) — previously ~12 codes
- Achieves **zero E20 "understanding" laziness** — previously ≈ 78% of all responses
- Detects **2 cross-study contradictions** with Likert ≥ 6 + **5 demi-regularities** (3+ studies each)
- Writes **5 PTS-anchored programme-theory sections** + integration paragraph

All six Phase-1 acceptance thresholds were met.

---

## 2. Headline metrics vs targets

| Metric | Baseline (v3.0) | Phase 1 | Target | Status |
|---|---|---|---|---|
| Multi-CMOC ratio | 1.00 | **2.00** | > 1.5 | PASS |
| Negative-CMOC share | 0% | **37.5%** | > 5% | PASS |
| E-code coverage (out of 47) | ~26% (≈12 codes) | **66%** (31 codes) | ≥ 60% | PASS |
| PTS coverage (1.0 = all 5 populated) | 0.20 (PTS1 only) | **1.00** | ≥ 0.60 | PASS |
| Ontology chain fidelity | ~0% (PTS not declared) | **41.1%** | ≥ 40% | PASS |
| Context-code Shannon diversity | low | **0.78** | ≥ 0.50 | PASS |
| E20 "understanding" share | **≈ 78%** | **0.0%** | < 40% | PASS |
| E01 "undergraduates" share | medium | **0.0%** | < 20% | PASS |

Raw evaluation file: `outputs/Phase1_Evaluation.json` and `Phase1_Evaluation.md`

---

## 3. PTS distribution (gold-standard vs Phase 1)

| PTS | Context anchor | Phase 1 CMOCs | Richmond coverage |
|---|---|---|---|
| PTS1 | E02 low knowledge | **20** | strongly covered |
| PTS2 | E03 high knowledge | **2** | sparse — paper set under-represents experts |
| PTS3 | E04 positive coping | **12** | well covered |
| PTS4 | E05 negative coping (negative pathway) | **19** | strongly covered |
| PTS5 | E06 mixed-knowledge groups | **3** | sparse — only 4 papers used mixed groups |

PTS2 and PTS5 sparseness reflects the underlying corpus rather than extraction
failure — the 28-paper benchmark contains few studies focused on experienced
trainees or heterogeneous groups.

---

## 4. What changed in the codebase

### Files rewritten (clean-rewrite, no backward-compat)

1. **`core/ontology.py`** — added `SingleCMOC`, `CMOCExtraction.cmocs: List[SingleCMOC]`, `ProgrammeTheoryStatement` enum, `INHIBITS`/`CONSTRAINS`/`MODERATES` relations, `is_negative` flag, per-CMOC confidence, `label_to_e_code()` utility.
2. **`plugins/realist_synthesis/cmoc_extractor.py`** — multi-CMOC prompt, anti-laziness rules (E01/E20/E25/E28 demoted), 5 few-shot examples (one per PTS), PTS reference table, smart truncation (10K head + 10K tail), per-CMOC confidence rating.
3. **`plugins/realist_synthesis/contradiction_agent.py`** — structural pre-filter (Context + Intervention same, Outcome polarity opposite) before any LLM call; ContraCrow-inspired 11-point Likert adjudication; cap candidates at 25.
4. **`plugins/realist_synthesis/cross_study_synthesizer.py`** — bucketed by PTS; **one focused LLM call per populated PTS** + integration call; empty-PTS placeholders explicitly forbid speculation.
5. **`core/agents/reporting_agent.py`** — one evidence-table row per CMOC; markdown grouped by PTS; new `cmoc_distribution.json` artifact feeding the evaluator.
6. **`graphrag/prompts/extract_graph.txt`** — replaced stock-market / hostage exemplars with three medical-education exemplars (positive PTS1, negative PTS4, mixed-group PTS5).

### Files created

7. **`data/gold_standard.json`** — Richmond's full E01–E47 + R01–R40 + 5 PTS chains as a machine-readable benchmark.
8. **`scripts/evaluate_phase1.py`** — computes E-code coverage, PTS coverage, ontology fidelity, laziness shares, Shannon diversity, multi-CMOC ratio, chain-mismatch examples.

### State / orchestrator: no changes required

`core/state.py` and `core/orchestrator.py` continued to work unchanged because
`extracted_cmocs: List[CMOCExtraction]` still has the same outer type — only
the internal structure changed.

---

## 5. Cross-study findings (real outputs from this run)

### Demi-regularities (≥ 3 studies)

See `outputs/demi_regularity_report.md`. Top recurring patterns:

- (E02 low-knowledge students + E27 build understanding → E46 increased learning) observed across multiple studies — empirical confirmation of PTS1.
- (E05 negative coping + E45 confusion → E36 poor illness-script development) observed across multiple studies — empirical confirmation of PTS4 negative pathway.

### Adjudicated contradictions (Likert ≥ 6)

See `outputs/contradiction_register.md`. Both pairs were flagged by the structural filter (same Context + same Intervention, opposite Outcome polarity) and confirmed by the GPT-4o adjudicator at Likert 6–7.

---

## 6. Known limitations + Phase 2+ roadmap

### Honest limitations of this Phase 1 run

- **Two parallel knowledge graphs still co-exist**: GraphRAG Parquet (245 communities, 4 138 entities) and the LangGraph CMOC graph (56 CMOCs). Multi-hop Cypher queries are not yet possible. → **Phase 2 (Neo4j unification)**.
- **No Search Agent yet**: the 28 papers were preloaded. Richmond's literature search has not been programmatically reproduced. → **Phase 3 (Search Agent with OpenAlex / PubMed E-utils + PaperQA2-style screener)**.
- **The 41% ontology chain fidelity** is partly an artefact of gold-standard granularity: many CMOCs that the LLM correctly mapped to outcome E46 ("increase in learning gain") were marked "deviating" because Richmond's canonical PTS1 chain only enumerated E25/E29/E30. A future Phase-5 gold-standard refinement should treat E46 as a supertype outcome compatible with PTS1.
- **No per-paper gold standard exists yet** — current evaluation is at the ontology level only. Manual coding of all 28 papers (Cohen's κ, F1) is recommended as Phase 5 work.

### Phase 2–6 (recommended order)

| Phase | Goal | Why | Effort |
|---|---|---|---|
| **Phase 2** | Migrate to Neo4j 5 with native vector | Unifies GraphRAG + LangGraph CMOCs; enables multi-hop Cypher queries; HybridCypherRetriever for RAG | 3–4 days |
| **Phase 3** | Implement Search Agent | Reproduces Richmond's literature search; OpenAlex + PubMed E-utils + PaperQA2 patterns | 4–5 days |
| **Phase 4** | Entity normalisation (MetaMap / scispaCy / SapBERT) + LazyGraphRAG indexing | Cuts entity duplication; 700× cheaper rebuild during iteration | 3 days |
| **Phase 5** | Full evaluation framework (RAGAS + DeepEval + manual κ on 28 papers) | Required for RRE 2026 methodological paper | 1 week |
| **Phase 6** | RAMESES reporting artefacts (PRISMA-AI flow diagram + L-PRISMA checklist) | Required for journal submission | 2 days |

---

## 7. Reproduction recipe

```bash
python -u main.py             # ~30 min, ~$3–4 OpenAI cost
python scripts/evaluate_phase1.py  # < 5 s
```

All artefacts are written to `outputs/`:

- `evidence_table.json` (machine-readable, 56 rows)
- `evidence_table.md` (markdown, grouped by PTS)
- `cmoc_distribution.json` (PTS / E-code distribution)
- `programme_theory_final.md` (Refined Programme Theory with 5 PTS sections)
- `contradiction_register.md` (adjudicated contradictions)
- `demi_regularity_report.md` (recurrent patterns)
- `Phase1_Evaluation.json` + `Phase1_Evaluation.md` (vs gold standard)
- `Phase1_run_log.txt` (full pipeline log)

---

## 8. Papers cited / inspired by this phase

- Richmond A. et al. (2020). *Medical Education* 54(8), 709-719. — gold standard.
- Edge D. et al. (2024). *GraphRAG*. arXiv:2404.16130. — community-aware retrieval.
- Skarlinski M. et al. (2024). *PaperQA2 / ContraCrow*. arXiv:2409.13740. — contradiction adjudication pattern (Likert + structural pre-filter).
- Traag V. et al. (2019). *Leiden algorithm*. Sci Rep 9:5233. — community detection.
- LangGraph (LangChain Inc., 2025). — multi-agent state machine.
- Wong G., Greenhalgh T., Westhorp G., Buckingham J., Pawson R. (2013). *RAMESES standards*. BMC Med 11:21. — realist synthesis reporting.
