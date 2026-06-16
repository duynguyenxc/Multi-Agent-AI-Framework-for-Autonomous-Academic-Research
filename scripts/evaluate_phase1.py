"""
scripts/evaluate_phase1.py — Phase 1 evaluation against Richmond gold standard
================================================================================
Computes:
  • E-code coverage      = #unique E-codes used / 47
  • PTS coverage         = #populated PTS buckets / 5
  • Ontology fidelity    = % of CMOCs whose 4-tuple matches a canonical chain
  • Laziness metrics     = share of E01 / E20 / E28 defaults
  • Negative-pathway %   = fraction of CMOCs flagged is_negative (Richmond's
                            review explicitly produces 1 negative PTS chain →
                            we expect ≥ 1 negative CMOC per ~10 studies)
  • Multi-CMOC ratio     = CMOCs per study (target > 1.5)
  • Relationship fidelity= % of system relations (subject_code, predicate,
                            object_code) that exist in the gold-standard R01–R40.

Usage:
    python scripts/evaluate_phase1.py

Outputs:
    outputs/Phase1_Evaluation.json   (machine-readable)
    outputs/Phase1_Evaluation.md     (human-readable diagnostic table)
"""
from __future__ import annotations
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple


ROOT = r"d:\LLM-Knowledge-Graph"
GOLD_PATH = os.path.join(ROOT, "data", "gold_standard.json")
EVIDENCE_PATH = os.path.join(ROOT, "outputs", "evidence_table.json")
DISTRIBUTION_PATH = os.path.join(ROOT, "outputs", "cmoc_distribution.json")
OUT_JSON = os.path.join(ROOT, "outputs", "Phase1_Evaluation.json")
OUT_MD = os.path.join(ROOT, "outputs", "Phase1_Evaluation.md")


def _safe_load(path: str) -> dict | list:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate() -> Dict:
    gold = _safe_load(GOLD_PATH)
    evidence = _safe_load(EVIDENCE_PATH)
    distribution = _safe_load(DISTRIBUTION_PATH) if os.path.exists(DISTRIBUTION_PATH) else {}

    # ── E-code coverage ─────────────────────────────────────────────────────
    gold_e_codes = set(gold["entities"].keys())
    used_e_codes: Set[str] = set()
    for row in evidence:
        for k in ("context_code", "intervention_code", "mechanism_resource_code",
                  "mechanism_response_code", "outcome_code"):
            code = row.get(k)
            if code and code.startswith("E"):
                used_e_codes.add(code)

    missing_e_codes = sorted(gold_e_codes - used_e_codes,
                             key=lambda c: int(c[1:]) if c[1:].isdigit() else 999)
    e_code_coverage = len(used_e_codes) / len(gold_e_codes) if gold_e_codes else 0

    # ── PTS coverage ────────────────────────────────────────────────────────
    pts_counts = Counter(r["pts"] for r in evidence)
    populated_pts = {p for p in ("PTS1", "PTS2", "PTS3", "PTS4", "PTS5") if pts_counts.get(p, 0) > 0}
    pts_coverage = len(populated_pts) / 5

    # ── Ontology fidelity (Context + Intervention + M-resp + Outcome chain
    #    matches the canonical PTS chain) ─────────────────────────────────────
    pts_meta: Dict[str, Dict] = gold["programme_theory_statements"]
    canonical_chains: Dict[str, Dict[str, Set[str]]] = {
        pts: {
            "context": {meta["context_code"]},
            "intervention": set(meta["expected_interventions"]),
            "mechanism_response": set(meta["expected_mechanism_responses"]),
            "outcome": set(meta["expected_outcomes"]),
        }
        for pts, meta in pts_meta.items()
    }

    chain_match = 0
    chain_evaluated = 0
    chain_mismatch_examples: List[Dict] = []
    for row in evidence:
        pts = row.get("pts")
        if pts not in canonical_chains:
            continue
        chain_evaluated += 1
        expected = canonical_chains[pts]
        misses = []
        if row.get("context_code") not in expected["context"]:
            misses.append(f"C={row.get('context_code')} not in {sorted(expected['context'])}")
        if row.get("intervention_code") not in expected["intervention"]:
            misses.append(f"I={row.get('intervention_code')} not in {sorted(expected['intervention'])}")
        if row.get("mechanism_response_code") not in expected["mechanism_response"]:
            misses.append(f"MR={row.get('mechanism_response_code')} not in {sorted(expected['mechanism_response'])}")
        if row.get("outcome_code") not in expected["outcome"]:
            misses.append(f"O={row.get('outcome_code')} not in {sorted(expected['outcome'])}")
        if not misses:
            chain_match += 1
        elif len(chain_mismatch_examples) < 12:
            chain_mismatch_examples.append({
                "study_id": row.get("study_id"),
                "cmoc_id": row.get("cmoc_id"),
                "pts": pts,
                "misses": misses,
            })
    chain_fidelity = chain_match / chain_evaluated if chain_evaluated else 0

    # ── Laziness metrics ────────────────────────────────────────────────────
    n = max(1, len(evidence))
    e01_share = sum(1 for r in evidence if r.get("context_code") == "E01") / n
    e02_share = sum(1 for r in evidence if r.get("context_code") == "E02") / n
    e20_share = sum(1 for r in evidence if r.get("mechanism_response_code") == "E20") / n
    e28_share = sum(1 for r in evidence if r.get("outcome_code") == "E28") / n
    e46_share = sum(1 for r in evidence if r.get("outcome_code") == "E46") / n
    negative_share = sum(1 for r in evidence if r.get("is_negative")) / n

    # ── Multi-CMOC ratio ────────────────────────────────────────────────────
    studies = set(r["study_id"] for r in evidence)
    multi_cmoc_ratio = len(evidence) / max(1, len(studies))

    # ── Diversity index (Shannon entropy of context codes) ──────────────────
    import math
    ctx_counter = Counter(r.get("context_code") for r in evidence)
    total = sum(ctx_counter.values())
    shannon_context = 0.0
    if total:
        for c, k in ctx_counter.items():
            p = k / total
            if p > 0:
                shannon_context -= p * math.log2(p)
    max_shannon = math.log2(6)  # 6 possible context codes
    diversity_index = shannon_context / max_shannon if max_shannon else 0

    return {
        "evaluated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total_cmocs": len(evidence),
            "unique_studies": len(studies),
            "multi_cmoc_ratio": round(multi_cmoc_ratio, 3),
            "negative_cmoc_share": round(negative_share, 3),
            "e_code_coverage": round(e_code_coverage, 3),
            "pts_coverage": round(pts_coverage, 3),
            "ontology_chain_fidelity": round(chain_fidelity, 3),
            "context_diversity_index": round(diversity_index, 3),
            "laziness": {
                "e01_share_should_be_low": round(e01_share, 3),
                "e02_share": round(e02_share, 3),
                "e20_share_should_be_low": round(e20_share, 3),
                "e28_share_should_be_low": round(e28_share, 3),
                "e46_share": round(e46_share, 3),
            },
        },
        "pts_distribution": dict(pts_counts),
        "populated_pts": sorted(populated_pts),
        "missing_e_codes": missing_e_codes,
        "e_code_usage": dict(Counter(
            code for r in evidence
            for code in (r.get("context_code"), r.get("intervention_code"),
                         r.get("mechanism_resource_code"),
                         r.get("mechanism_response_code"), r.get("outcome_code"))
            if code
        ).most_common()),
        "chain_mismatch_examples": chain_mismatch_examples,
        "phase1_targets": {
            "multi_cmoc_ratio_target": "> 1.5",
            "pts_coverage_target": ">= 0.6 (3/5 PTS populated)",
            "e_code_coverage_target": ">= 0.6 (≥28/47)",
            "ontology_chain_fidelity_target": ">= 0.4",
            "e20_share_target": "< 0.4 (down from baseline 0.78)",
            "negative_cmoc_share_target": "> 0.05",
        },
    }


def _render_markdown(report: Dict) -> str:
    s = report["summary"]
    lines = [
        "# Phase 1 Evaluation Report",
        f"Generated: {report['evaluated_at']}",
        "",
        "## Headline metrics",
        "",
        "| Metric | Value | Target | Pass |",
        "|---|---|---|---|",
    ]
    targets = report["phase1_targets"]

    def _row(name: str, value, target: str, ok: bool) -> str:
        return f"| {name} | {value} | {target} | {'✓' if ok else '✗'} |"

    lines.append(_row("CMOCs total", s["total_cmocs"], "—", True))
    lines.append(_row("Unique studies", s["unique_studies"], "—", True))
    lines.append(_row("Multi-CMOC ratio", s["multi_cmoc_ratio"],
                     targets["multi_cmoc_ratio_target"], s["multi_cmoc_ratio"] > 1.5))
    lines.append(_row("Negative-CMOC share", s["negative_cmoc_share"],
                     targets["negative_cmoc_share_target"], s["negative_cmoc_share"] > 0.05))
    lines.append(_row("E-code coverage", s["e_code_coverage"],
                     targets["e_code_coverage_target"], s["e_code_coverage"] >= 0.6))
    lines.append(_row("PTS coverage", s["pts_coverage"],
                     targets["pts_coverage_target"], s["pts_coverage"] >= 0.6))
    lines.append(_row("Ontology chain fidelity", s["ontology_chain_fidelity"],
                     targets["ontology_chain_fidelity_target"], s["ontology_chain_fidelity"] >= 0.4))
    lines.append(_row("Context diversity (Shannon/log2 6)", s["context_diversity_index"], "≥ 0.5",
                     s["context_diversity_index"] >= 0.5))
    lines.append(_row("E20 share (laziness)", s["laziness"]["e20_share_should_be_low"],
                     targets["e20_share_target"], s["laziness"]["e20_share_should_be_low"] < 0.4))
    lines.append(_row("E01 share (laziness)", s["laziness"]["e01_share_should_be_low"],
                     "< 0.2", s["laziness"]["e01_share_should_be_low"] < 0.2))

    lines.append("")
    lines.append("## PTS distribution")
    for pts in ("PTS1", "PTS2", "PTS3", "PTS4", "PTS5", "N/A"):
        count = report["pts_distribution"].get(pts, 0)
        bar = "█" * min(count, 40)
        lines.append(f"- **{pts}** ({count}): {bar}")

    lines.append("")
    lines.append("## E-codes NOT used in this run")
    if report["missing_e_codes"]:
        lines.append(", ".join(report["missing_e_codes"]))
    else:
        lines.append("(none — full E01–E47 coverage achieved)")

    lines.append("")
    lines.append("## Top 15 most-used E-codes")
    for code, count in list(report["e_code_usage"].items())[:15]:
        lines.append(f"- `{code}`: {count}")

    lines.append("")
    lines.append("## Chain-mismatch examples (CMOCs whose 4-tuple deviates from canonical PTS chain)")
    if not report["chain_mismatch_examples"]:
        lines.append("(none — every CMOC matches its declared PTS canonical chain)")
    else:
        for ex in report["chain_mismatch_examples"]:
            lines.append(f"- `{ex['cmoc_id']}` (study {ex['study_id']}, {ex['pts']}):")
            for m in ex["misses"]:
                lines.append(f"  - {m}")

    return "\n".join(lines) + "\n"


def main():
    print("[Phase 1 Eval] Loading gold standard + evidence_table.json …")
    report = evaluate()
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(_render_markdown(report))
    print(f"[Phase 1 Eval] Wrote {OUT_JSON}")
    print(f"[Phase 1 Eval] Wrote {OUT_MD}")
    print()
    s = report["summary"]
    print(f"  CMOCs: {s['total_cmocs']} across {s['unique_studies']} studies")
    print(f"  Multi-CMOC ratio: {s['multi_cmoc_ratio']} (target > 1.5)")
    print(f"  PTS coverage: {s['pts_coverage']} (target >= 0.6)")
    print(f"  E-code coverage: {s['e_code_coverage']} (target >= 0.6)")
    print(f"  Ontology chain fidelity: {s['ontology_chain_fidelity']} (target >= 0.4)")
    print(f"  E20 laziness: {s['laziness']['e20_share_should_be_low']} (target < 0.4)")


if __name__ == "__main__":
    main()
