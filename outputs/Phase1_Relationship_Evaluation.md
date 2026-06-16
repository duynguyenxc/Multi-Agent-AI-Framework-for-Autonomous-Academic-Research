# Phase 1 Relationship Evaluation

## Note on Golden Standard Scope
> [!IMPORTANT]
> The R01-R40 metrics below are evaluated at the **Programme-Theory Level**, representing the global synthesis of the Richmond review. They measure the overall capacity of the Knowledge Graph to recover the synthesized causal pathways. Per-paper relationship adjudication requires human review of the instance-level triples.

## Summary Metrics
| Metric | Value |
|---|---|
| Total Instance-Level Triples | 171 |
| Unique Programme-Level Triples | 36 |
| Gold R-codes | 40 |

## F1 Scores
| Evaluation Type | Precision | Recall | F1 Score |
|---|---|---|---|
| **Strict** (Source + Predicate + Target) | 0.083 | 0.075 | 0.079 |
| **Relaxed** (Source + Target) | 0.088 | 0.075 | 0.081 |

## Component Accuracies
| Component | Accuracy | Explanation |
|---|---|---|
| **Direction Accuracy** | 1.000 | Correct direction among valid undirected edges. |
| **Predicate Accuracy** | 1.000 | Correct predicate among valid directed edges. |

## Error Analysis

### 1. Wrong Predicate Cases (0)
*(Correct source/target, but model chose wrong relation type)*

### 2. Wrong Direction Cases (0)
*(Valid edge exists, but direction is reversed)*

### 3. Missing Gold Triples (37)
*(False Negatives: Model failed to extract these)*
- Missing: `E12 -[TRIGGERS]-> E39`
- Missing: `E10 -[TRIGGERS]-> E32`
- Missing: `E42 -[LEADS_TO]-> E43`
- Missing: `E04 -[ENABLES]-> E26`
- Missing: `E03 -[ENABLES]-> E24`
- Missing: `E27 -[LEADS_TO]-> E29`
- Missing: `E32 -[LEADS_TO]-> E35`
- Missing: `E13 -[TRIGGERS]-> E42`
- Missing: `E20 -[LEADS_TO]-> E22`
- Missing: `E06 -[ENABLES]-> E39`
- Missing: `E16 -[TRIGGERS]-> E47`
- Missing: `E09 -[TRIGGERS]-> E26`
- Missing: `E08 -[TRIGGERS]-> E23`
- Missing: `E11 -[TRIGGERS]-> E31`
- Missing: `E31 -[LEADS_TO]-> E22`
- Missing: `E10 -[TRIGGERS]-> E33`
- Missing: `E33 -[LEADS_TO]-> E35`
- Missing: `E35 -[LEADS_TO]-> E38`
- Missing: `E35 -[LEADS_TO]-> E36`
- Missing: `E20 -[LEADS_TO]-> E21`
- Missing: `E20 -[LEADS_TO]-> E40`
- Missing: `E14 -[TRIGGERS]-> E45`
- Missing: `E07 -[PROVIDES]-> E20`
- Missing: `E26 -[LEADS_TO]-> E27`
- Missing: `E10 -[TRIGGERS]-> E26`
- Missing: `E34 -[LEADS_TO]-> E35`
- Missing: `E17 -[TRIGGERS]-> E46`
- Missing: `E18 -[TRIGGERS]-> E46`
- Missing: `E15 -[TRIGGERS]-> E46`
- Missing: `E05 -[CONSTRAINS]-> E38`
- Missing: `E27 -[LEADS_TO]-> E30`
- Missing: `E20 -[LEADS_TO]-> E41`
- Missing: `E10 -[TRIGGERS]-> E34`
- Missing: `E27 -[LEADS_TO]-> E28`
- Missing: `E35 -[LEADS_TO]-> E37`
- Missing: `E03 -[ENABLES]-> E20`
- Missing: `E39 -[LEADS_TO]-> E20`

### 4. Extra Predicted Triples (33)
*(False Positives: Model extracted these but they aren't in Gold)*
- Extra: `E14 -[CONSTRAINS]-> E19`
- Extra: `E19 -[TRIGGERS]-> E24`
- Extra: `E39 -[LEADS_TO]-> E46`
- Extra: `E19 -[TRIGGERS]-> E42`
- Extra: `E19 -[TRIGGERS]-> E23`
- Extra: `E24 -[PROVIDES]-> E19`
- Extra: `E27 -[LEADS_TO]-> E46`
- Extra: `E19 -[TRIGGERS]-> E32`
- Extra: `E19 -[TRIGGERS]-> E45`
- Extra: `E15 -[PROVIDES]-> E19`
- Extra: `E27 -[LEADS_TO]-> E44`
- Extra: `E18 -[PROVIDES]-> E19`
- Extra: `E17 -[PROVIDES]-> E19`
- Extra: `E13 -[PROVIDES]-> E19`
- Extra: `E19 -[TRIGGERS]-> E27`
- Extra: `E07 -[PROVIDES]-> E19`
- Extra: `E45 -[LEADS_TO]-> E36`
- Extra: `E27 -[LEADS_TO]-> E25`
- Extra: `E10 -[PROVIDES]-> E19`
- Extra: `E39 -[LEADS_TO]-> E22`
- Extra: `E26 -[LEADS_TO]-> E22`
- Extra: `E27 -[LEADS_TO]-> E22`
- Extra: `E19 -[TRIGGERS]-> E26`
- Extra: `E19 -[CONSTRAINS]-> E45`
- Extra: `E12 -[PROVIDES]-> E19`
- Extra: `E19 -[TRIGGERS]-> E39`
- Extra: `E39 -[LEADS_TO]-> E43`
- Extra: `E08 -[PROVIDES]-> E19`
- Extra: `E09 -[PROVIDES]-> E19`
- Extra: `E26 -[LEADS_TO]-> E28`
- Extra: `E32 -[LEADS_TO]-> E36`
- Extra: `E23 -[LEADS_TO]-> E38`
- Extra: `E14 -[PROVIDES]-> E19`
