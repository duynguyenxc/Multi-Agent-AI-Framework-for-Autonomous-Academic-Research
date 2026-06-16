import json
import os
import re

ROOT = r"d:\LLM-Knowledge-Graph"
EVIDENCE_TABLE = os.path.join(ROOT, "outputs", "evidence_table.json")
REL_LONG = os.path.join(ROOT, "outputs", "relationships_long.json")
GOLD_STANDARD = os.path.join(ROOT, "data", "gold_standard.json")

OUT_TRIPLES = os.path.join(ROOT, "outputs", "relationships_triples.json")
OUT_MD = os.path.join(ROOT, "outputs", "Phase1_Relationship_Evaluation.md")
OUT_JSON = os.path.join(ROOT, "outputs", "Phase1_Relationship_Evaluation.json")
OUT_CSV = os.path.join(ROOT, "outputs", "relationships_triples.csv")
OUT_UNIQUE = os.path.join(ROOT, "outputs", "unique_programme_level_triples.json")

import csv

def get_ecode(cmoc, node_id):
    prefix = re.match(r'([A-Za-z]+)', node_id).group(1)
    mapping = {
        'c': 'context_code',
        'i': 'intervention_code',
        'mr': 'mechanism_resource_code',
        'mresp': 'mechanism_response_code',
        'o': 'outcome_code'
    }
    return cmoc.get(mapping[prefix])

def evaluate_relationships():
    with open(EVIDENCE_TABLE, "r", encoding="utf-8") as f:
        evidence = json.load(f)
    with open(REL_LONG, "r", encoding="utf-8") as f:
        rels = json.load(f)
    with open(GOLD_STANDARD, "r", encoding="utf-8") as f:
        gold = json.load(f)

    cmoc_map = {c["cmoc_id"]: c for c in evidence}
    
    instance_level_triples = []
    unique_programme_level_triples = set()
    
    for r in rels:
        cmoc = cmoc_map.get(r["cmoc_id"])
        if not cmoc: continue
        
        src_code = get_ecode(cmoc, r["source_id"])
        tgt_code = get_ecode(cmoc, r["target_id"])
        pred = r["relation_type"]
        if pred == "INHIBITS":
            pred = "CONSTRAINS"
        
        if not src_code or not tgt_code: continue
            
        instance_level_triples.append({
            "study_id": r["study_id"],
            "cmoc_id": r["cmoc_id"],
            "source_e_code": src_code,
            "predicate": pred,
            "target_e_code": tgt_code,
            "evidence_quote": r["evidence_quote"]
        })
        unique_programme_level_triples.add((src_code, pred, tgt_code))

    os.makedirs(os.path.dirname(OUT_TRIPLES), exist_ok=True)
    with open(OUT_TRIPLES, "w", encoding="utf-8") as f:
        json.dump(instance_level_triples, f, indent=2)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        if instance_level_triples:
            writer = csv.DictWriter(f, fieldnames=instance_level_triples[0].keys())
            writer.writeheader()
            writer.writerows(instance_level_triples)

    unique_list = [{"source_e_code": s, "predicate": p, "target_e_code": t} for s, p, t in unique_programme_level_triples]
    with open(OUT_UNIQUE, "w", encoding="utf-8") as f:
        json.dump(unique_list, f, indent=2)

    gold_rels = gold.get("relationships", [])
    gold_triples = set((r["subject_code"], r["predicate"], r["object_code"]) for r in gold_rels)
    gold_pairs = set((r["subject_code"], r["object_code"]) for r in gold_rels)
    gold_pairs_undirected = set(frozenset([r["subject_code"], r["object_code"]]) for r in gold_rels)
    
    pred_triples = unique_programme_level_triples
    pred_pairs = set((t[0], t[2]) for t in pred_triples)
    pred_pairs_undirected = set(frozenset([t[0], t[2]]) for t in pred_triples)

    # Metrics
    # Strict
    strict_tp = len(pred_triples.intersection(gold_triples))
    strict_fp = len(pred_triples - gold_triples)
    strict_fn = len(gold_triples - pred_triples)
    strict_precision = strict_tp / (strict_tp + strict_fp) if (strict_tp + strict_fp) > 0 else 0
    strict_recall = strict_tp / (strict_tp + strict_fn) if (strict_tp + strict_fn) > 0 else 0
    strict_f1 = 2 * strict_precision * strict_recall / (strict_precision + strict_recall) if (strict_precision + strict_recall) > 0 else 0

    # Relaxed (Correct direction, ignore predicate)
    relaxed_tp = len(pred_pairs.intersection(gold_pairs))
    relaxed_fp = len(pred_pairs - gold_pairs)
    relaxed_fn = len(gold_pairs - pred_pairs)
    relaxed_precision = relaxed_tp / (relaxed_tp + relaxed_fp) if (relaxed_tp + relaxed_fp) > 0 else 0
    relaxed_recall = relaxed_tp / (relaxed_tp + relaxed_fn) if (relaxed_tp + relaxed_fn) > 0 else 0
    relaxed_f1 = 2 * relaxed_precision * relaxed_recall / (relaxed_precision + relaxed_recall) if (relaxed_precision + relaxed_recall) > 0 else 0

    # Direction Accuracy
    # Out of all predicted pairs that share an edge in gold (undirected), how many have correct direction?
    dir_denom = len(pred_pairs_undirected.intersection(gold_pairs_undirected))
    dir_num = len(pred_pairs.intersection(gold_pairs))
    direction_accuracy = dir_num / dir_denom if dir_denom > 0 else 0

    # Predicate Accuracy
    # Out of all relaxed matches (correct source->target), how many have correct predicate?
    pred_denom = relaxed_tp
    pred_num = strict_tp
    predicate_accuracy = pred_num / pred_denom if pred_denom > 0 else 0

    missing_gold = gold_triples - pred_triples
    extra_pred = pred_triples - gold_triples
    
    wrong_predicate = [(s, p, t) for (s, p, t) in extra_pred if (s, t) in gold_pairs]
    wrong_direction = [(s, p, t) for (s, p, t) in extra_pred if (t, s) in gold_pairs]

    md_content = f"""# Phase 1 Relationship Evaluation

## Note on Golden Standard Scope
> [!IMPORTANT]
> The R01-R40 metrics below are evaluated at the **Programme-Theory Level**, representing the global synthesis of the Richmond review. They measure the overall capacity of the Knowledge Graph to recover the synthesized causal pathways. Per-paper relationship adjudication requires human review of the instance-level triples.

## Summary Metrics
| Metric | Value |
|---|---|
| Total Instance-Level Triples | {len(instance_level_triples)} |
| Unique Programme-Level Triples | {len(unique_programme_level_triples)} |
| Gold R-codes | {len(gold_triples)} |

## F1 Scores
| Evaluation Type | Precision | Recall | F1 Score |
|---|---|---|---|
| **Strict** (Source + Predicate + Target) | {strict_precision:.3f} | {strict_recall:.3f} | {strict_f1:.3f} |
| **Relaxed** (Source + Target) | {relaxed_precision:.3f} | {relaxed_recall:.3f} | {relaxed_f1:.3f} |

## Component Accuracies
| Component | Accuracy | Explanation |
|---|---|---|
| **Direction Accuracy** | {direction_accuracy:.3f} | Correct direction among valid undirected edges. |
| **Predicate Accuracy** | {predicate_accuracy:.3f} | Correct predicate among valid directed edges. |

## Error Analysis

### 1. Wrong Predicate Cases ({len(wrong_predicate)})
*(Correct source/target, but model chose wrong relation type)*
"""
    for w in wrong_predicate:
        md_content += f"- Predicted `{w[0]} -[{w[1]}]-> {w[2]}`\n"

    md_content += f"\n### 2. Wrong Direction Cases ({len(wrong_direction)})\n*(Valid edge exists, but direction is reversed)*\n"
    for w in wrong_direction:
        md_content += f"- Predicted `{w[0]} -[{w[1]}]-> {w[2]}` (Gold is `{w[2]} -> {w[0]}`)\n"

    md_content += f"\n### 3. Missing Gold Triples ({len(missing_gold)})\n*(False Negatives: Model failed to extract these)*\n"
    for w in missing_gold:
        md_content += f"- Missing: `{w[0]} -[{w[1]}]-> {w[2]}`\n"

    md_content += f"\n### 4. Extra Predicted Triples ({len(extra_pred)})\n*(False Positives: Model extracted these but they aren't in Gold)*\n"
    for w in extra_pred:
        md_content += f"- Extra: `{w[0]} -[{w[1]}]-> {w[2]}`\n"

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    evaluation_results = {
        "metrics": {
            "strict_precision": strict_precision,
            "strict_recall": strict_recall,
            "strict_f1": strict_f1,
            "relaxed_precision": relaxed_precision,
            "relaxed_recall": relaxed_recall,
            "relaxed_f1": relaxed_f1,
            "direction_accuracy": direction_accuracy,
            "predicate_accuracy": predicate_accuracy
        },
        "counts": {
            "instance_level_triples": len(instance_level_triples),
            "unique_programme_level_triples": len(unique_programme_level_triples),
            "gold_triples": len(gold_triples),
            "wrong_predicate_cases": len(wrong_predicate),
            "wrong_direction_cases": len(wrong_direction),
            "missing_gold": len(missing_gold),
            "extra_predicted": len(extra_pred)
        }
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(evaluation_results, f, indent=2)

    print(f"Generated metrics in multiple formats.")

if __name__ == "__main__":
    evaluate_relationships()
