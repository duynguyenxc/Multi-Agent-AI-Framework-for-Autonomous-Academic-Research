# Entity/Relationship Verification Protocol

## 1. Purpose

This protocol defines how we will verify entities and relationships produced by the knowledge graph and the downstream realist synthesis pipeline.

The core problem is that Richmond et al. provide a human realist synthesis, but they do not publish a full machine-readable entity and relationship answer key for every paper. Therefore, we need a defensible verification protocol that separates:

1. What Richmond directly gives us.
2. What our repository has already formalized from Richmond.
3. What still requires human adjudication.

## 2. Main Position

We do have a usable golden standard for entities and relationships at the programme-theory level:

- Entities: E01-E47 in `data/gold_standard.json`
- Relationships: R01-R40 in `data/gold_standard.json`
- Programme theory statements: PTS1-PTS5 in `data/gold_standard.json`

We do not yet have a complete per-paper gold standard for every entity mention, CMOC tuple, and relationship edge. That must be created through manual annotation and adjudication.

Therefore, evaluation must be layered:

1. Programme-theory-level verification against Richmond.
2. E-code/R-code verification against `data/gold_standard.json`.
3. Per-paper extraction verification against a new human-adjudicated dataset.

## 3. Entity Schema

All model-generated entities are normalized to one of the controlled Richmond entity categories before verification.

| Category | Meaning | Gold Codes |
|---|---|---|
| Context | Learner, group, or setting condition that changes how an intervention works. | E01-E06 |
| Intervention | Educational activity, design feature, instructional method, or feedback process. | E07-E18 |
| Mechanism Resource | Resource or opportunity offered by the intervention. | E19 |
| Mechanism Response | Learner reasoning, affective, cognitive, or coping response triggered by the resource. | E20, E23, E24, E26, E27, E31-E35, E39, E42, E45 |
| Outcome | Learning, reasoning, diagnostic, affective, or future-performance result. | E21, E22, E25, E28-E30, E36-E38, E40, E41, E43, E44, E46, E47 |

The current controlled entity set contains 47 entities:

- 6 Context entities
- 12 Intervention entities
- 1 Mechanism Resource entity
- 13 Mechanism Response entities
- 15 Outcome entities

Source: `data/gold_standard.json`.

## 4. Relationship Schema

Every relationship used for verification must be represented as a directed triple:

```text
(source_entity_code, predicate, target_entity_code)
```

Example:

```text
(E07, PROVIDES, E19)
```

The gold relationship set currently contains 40 relationships:

- R01-R40
- Source: `data/gold_standard.json`
- Required fields for verification: source E-code, relation predicate, target E-code, programme theory statement, evidence status

The relation direction matters. A relationship from intervention to mechanism resource is not equivalent to the reverse relationship.

## 5. Relation Type Policy

The current Richmond gold file uses these predicates:

- PROVIDES
- ENABLES
- TRIGGERS
- LEADS_TO
- CONSTRAINS

The current code and prompts also mention related relation types such as INHIBITS and MODERATES.

Before final evaluation, the project should freeze one relation vocabulary. The recommended policy is:

| Gold Predicate | Meaning | Allowed Alias During Relaxed Matching |
|---|---|---|
| PROVIDES | An intervention supplies a resource, case, feedback, or learning opportunity. | offers, exposes_to, supplies |
| ENABLES | A context or resource makes a mechanism possible or more likely. | supports, facilitates |
| TRIGGERS | A resource activates a learner response. | evokes, prompts |
| LEADS_TO | A mechanism response produces an outcome. | results_in, contributes_to |
| CONSTRAINS | A context or response limits, blocks, or worsens a mechanism/outcome. | inhibits, undermines, increases_risk_of |

Implementation note: `core/ontology.py` currently defines several relation types but does not include `CONSTRAINS`, while `data/gold_standard.json` and existing relationship outputs include CONSTRAINS. This mismatch must be fixed before strict relationship evaluation.

## 6. Evidence Requirement

No entity or relationship is counted as verified unless it has evidence.

Minimum evidence fields:

| Field | Required? | Purpose |
|---|---:|---|
| source_document_id | Yes | Identifies the paper or Richmond source. |
| evidence_text_or_location | Yes | Links the extraction to text evidence. |
| entity_or_relation_code | Yes | Maps raw output to E-code or R-code. |
| confidence | Yes | Allows human triage. |
| adjudication_status | Yes for gold creation | accepted, revised, rejected, or unresolved. |
| evidence_level | Yes | full-text, abstract-only, Richmond paper, or derived synthesis. |

For the 8 abstract-only studies, evidence is marked as `abstract-only` and considered provisional unless full text is later obtained.

## 7. Verification Levels

### Level 1: Corpus Coverage

Before evaluating entities and relationships, verify that the KG input corpus matches the Richmond target corpus.

Gold target:

- 28 included studies.
- 20 currently available as PDFs.
- 8 currently available as abstract/metadata records.

Required metrics:

| Metric | Definition | Pass Rule |
|---|---|---|
| Document coverage | Indexed documents / 28 | Must be 28/28 for official evaluation. |
| Full-text coverage | Indexed PDF-derived records / 20 | Must be 20/20. |
| Abstract-record coverage | Indexed abstract records / 8 | Must be 8/8, clearly labelled. |
| Extraction status | Whether each document has usable text | No silent missing documents. |

Current project gap: `outputs/graphrag_data/stats.json` reports 20 indexed documents, while the Richmond target corpus has 28 records. The official KG must be rebuilt or rechecked against all 28 records before final claims.

### Level 2: Entity Normalization

Raw model nodes must be mapped to E01-E47.

Each raw entity should receive:

```text
raw_entity_label
raw_entity_type
normalized_e_code
normalized_gold_label
match_type
evidence_document
evidence_location
confidence
human_status
```

Recommended match types:

| Match Type | Meaning |
|---|---|
| strict | Same concept and category as the E-code. |
| relaxed | Same meaning but different wording or level of abstraction. |
| category_only | Correct category, but cannot be mapped to a precise E-code. |
| unmapped_valid | Relevant Richmond concept not in the current gold set. |
| hallucinated_or_irrelevant | Not supported by evidence or outside the review scope. |

Entity metrics:

| Metric | Formula or Meaning |
|---|---|
| Strict entity precision | Correct strict E-code matches / all normalized entity predictions. |
| Strict entity recall | Gold E-codes recovered / 47 gold E-codes. |
| Relaxed entity F1 | Allows synonym/abstraction match when human-approved. |
| Category accuracy | Correct category among Context, Intervention, Mechanism Resource, Mechanism Response, Outcome. |
| Evidence support rate | Predictions with source evidence / all predictions. |
| Unmapped rate | Entity predictions that cannot be mapped to E01-E47. |

### Level 3: Relationship Triple Verification

Each model relationship must be converted to an E-code triple before scoring:

```text
(source_e_code, predicate, target_e_code)
```

Strict relationship match requires all three components:

1. Correct source E-code.
2. Correct predicate.
3. Correct target E-code.

Relationship metrics:

| Metric | Definition |
|---|---|
| Strict edge precision | Predicted triples exactly matching R01-R40 / all predicted triples. |
| Strict edge recall | Gold R01-R40 triples recovered / 40. |
| Strict edge F1 | Harmonic mean of strict precision and recall. |
| Direction accuracy | Predicted edges with correct direction / matched edge concepts. |
| Predicate accuracy | Matched source-target pairs with correct predicate. |
| Relaxed edge F1 | Allows approved predicate aliases and near-equivalent entity mapping. |
| Evidence support rate | Edges with source evidence / all edges. |

Current project gap: `outputs/relationships_long.json` currently contains local IDs such as `i1`, `mr1`, `mresp1`, and `o1`. These must be materialized into E-code triples before strict comparison against R01-R40.

### Level 4: Programme Theory Statement Verification

After entities and relationships are verified, each CMOC or graph path is assigned to one of the five Richmond programme theory statements:

| PTS | Core Context |
|---|---|
| PTS1 | Low knowledge / low clinical domain-specific knowledge. |
| PTS2 | High clinical domain-specific knowledge. |
| PTS3 | Positive coping, self-confidence, or self-efficacy. |
| PTS4 | Negative coping, low confidence, low self-efficacy, or cognitive overload. |
| PTS5 | Mixed knowledge levels within a learner group. |

PTS metrics:

| Metric | Meaning |
|---|---|
| PTS coverage | Number of Richmond PTS categories recovered out of 5. |
| PTS assignment accuracy | Whether each CMOC is assigned to the correct PTS. |
| Chain fidelity | Whether the CMOC follows a valid Context -> Intervention/Resource -> Mechanism Response -> Outcome pattern. |
| Negative-mechanism capture | Whether PTS4 and harmful outcomes are captured rather than filtered out. |

Existing `scripts/evaluate_phase1.py` already computes several useful PTS and chain metrics. However, its current implementation does not yet compute strict relationship fidelity against R01-R40, even though relationship evaluation is described in the project documentation. This metric must be added before relationship-level verification claims are made.

### Level 5: Per-Paper CMOC Gold Creation

Because Richmond does not provide a full per-paper CMOC answer key, we need a human-created verification set.

Recommended annotation unit:

```text
paper_id
study_citation
evidence_level
evidence_location
context_e_code
intervention_e_code
mechanism_resource_e_code
mechanism_response_e_code
outcome_e_code
relationship_triples
pts_assignment
polarity
annotator_notes
```

Recommended process:

1. Annotator A codes all 28 records.
2. Annotator B independently reviews at least a high-risk subset, preferably all 28 if time allows.
3. Disagreements are adjudicated into a frozen gold table.
4. Abstract-only records are labelled separately from full-text records.
5. The final table becomes the per-paper extraction gold standard for CMOC, entity, and relationship verification.

Agreement metrics:

- Entity category agreement.
- E-code agreement.
- PTS assignment agreement.
- Polarity agreement: positive, negative, mixed, or unclear.
- Relationship triple agreement.
- Cohen kappa or percent agreement, depending on sample size and label distribution.

## 8. Pass/Fail Gates

The KG is not considered verified unless it passes the following gates.

| Gate | Minimum Requirement |
|---|---|
| Corpus gate | 28/28 Richmond records indexed or explicitly represented. |
| Entity gate | Every retained node maps to an E-code, a human-approved new concept, or a rejected/unmapped category. |
| Relationship gate | Every retained edge has directed E-code endpoints and a frozen predicate. |
| Evidence gate | Every accepted node and edge has source evidence. |
| PTS gate | All five Richmond PTS categories are recoverable. |
| Human review gate | Errors are localized and either corrected, rejected, or logged before final reporting. |

## 9. Error Categories

Every failed entity or relationship receives one error category. This is necessary for refinement.

| Error Category | Example |
|---|---|
| Missing entity | Gold E-code present in Richmond but not extracted. |
| Over-generated entity | Model creates a concept unsupported by the paper. |
| Wrong category | A mechanism response is classified as an outcome. |
| Wrong abstraction level | Model extracts a narrow phrase but misses the Richmond-level concept. |
| Wrong source | Correct concept but attached to the wrong study. |
| Missing relationship | Entity pair exists but relation is not extracted. |
| Wrong predicate | Correct source and target, wrong relation type. |
| Wrong direction | Edge direction is reversed. |
| Unsupported relationship | Edge has no evidence in text or synthesis. |
| Polarity error | Harmful/negative mechanism is interpreted as beneficial, or vice versa. |

## 10. Human-in-the-Loop Refinement

The verification process must support iterative refinement:

1. Run extraction.
2. Normalize raw nodes and edges to E-codes and R-codes.
3. Compute metrics.
4. Human reviewer marks errors using the error categories above.
5. Feed targeted corrections back into prompts, ontology rules, or mapping tables.
6. Rerun only the affected step where possible.
7. Re-score and log whether the issue improved.

Current project gap: `core/orchestrator.py` contains human-in-the-loop checkpoints, but the current benchmark/prototype behavior auto-approves several checkpoints. For official evaluation, these checkpoints should produce reviewable tables and require explicit human decision records.

## 11. Required Output Files

To make the verification auditable, the project should produce these files:

| File | Purpose |
|---|---|
| `entity_mapping_table.csv` | Raw KG nodes mapped to E01-E47, with evidence and human status. |
| `relationship_triples.csv` | Directed E-code triples mapped to R01-R40. |
| `per_paper_cmoc_gold.csv` | Human-adjudicated per-paper CMOC gold set. |
| `kg_verification_report.md` | Entity, relationship, PTS, and evidence metrics. |
| `adjudication_log.md` | Human decisions, disagreements, and final resolutions. |
| `error_analysis.csv` | Error categories used for model refinement. |

## 12. Current Readiness Assessment

The current project has a strong starting point but is not yet ready to claim fully verified entity/relationship performance.

What is ready:

- Richmond 28-study registry exists.
- E01-E47 entity gold exists.
- R01-R40 relationship gold exists.
- PTS1-PTS5 programme theory gold exists.
- Phase 1 evaluation already measures E-code coverage, PTS coverage, chain fidelity, and related metrics.

What must be fixed or completed:

- Rebuild or verify KG indexing across all 28 records, not only 20.
- Add `CONSTRAINS` consistently to the ontology or map it explicitly to an approved predicate.
- Convert model relationship outputs from local IDs to E-code triples.
- Add strict and relaxed relationship scoring against R01-R40.
- Reconcile current artifact mismatch: some outputs report 56 CMOCs, while others report 57.
- Replace auto-approval HITL checkpoints with auditable human review decisions for final evaluation.
- Build the per-paper CMOC/entity/relation adjudication set.

## 13. Conclusion

A visually plausible knowledge graph is not sufficient as research evidence. The graph becomes scientifically useful only when nodes, edges, direction, relation type, and evidence can be compared against a defined reference.

Our answer is:

Richmond gives us the human programme-theory gold standard. The repository already formalizes that standard into E01-E47 and R01-R40. For per-paper extraction, we will create a human-adjudicated gold set and use strict plus relaxed metrics to verify entities, relationships, CMOCs, and final theory alignment.

## 14. Citation and Evidence Policy

This protocol is paired with `Entity_Relationship_Definition_Modeling_Specification.md`.

The definition/modeling specification defines what entities and relationships are. This protocol defines how to verify them. Both documents rely on Richmond et al. (2020) for the realist synthesis benchmark, Edge et al. (2025) for the GraphRAG rationale, and local project artifacts for implementation evidence.

No entity or relationship is treated as verified only because it appears in a graph visualization. Verification requires normalized codes, directed typed triples, evidence support, and human-readable review outputs.

## 15. References

Richmond, A., Cooper, N., Gay, S., Atiomo, W., & Patel, R. (2020). The student is key: A realist review of educational interventions to develop analytical and non-analytical clinical reasoning ability. Medical Education, 54(8), 709-719. https://doi.org/10.1111/medu.14137

Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S., Metropolitansky, D., Ness, R. O., & Larson, J. (2025). From local to global: A GraphRAG approach to query-focused summarization. arXiv:2404.16130v2.

Project gold standard. (2026). Richmond-derived E01-E47, R01-R40, and PTS1-PTS5 benchmark. Local file: `data/gold_standard.json`.

Professor project abstract. (2026). Proposed AI Agent Pipeline for Systematic Review in Education. Local file: `documents/abstract-from-professor/abstract.md`.
