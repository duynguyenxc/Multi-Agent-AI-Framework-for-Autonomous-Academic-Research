"""
core/agents/reporting_agent.py — Agent 9 (final): Reporting & Audit Agent
==========================================================================
Richmond Alignment: Technical Writer
Role: Generates PRISMA flow counts, structured evidence tables, programme
theory documents, contradiction registers, and AERA-RRE repository-ready
audit artifacts.

v4 Changes:
  - Multi-CMOC support (iterates over extraction.cmocs)
  - Evidence table shows EVERY CMOC chain, not just the first
  - Richmond-aligned PTS grouping in evidence_table.md
  - Typed relationships visible in evidence output
  - Added comparison_with_richmond.md for benchmark validation
  - Added entity_relationship_summary.md for easy node/edge visualization
"""
import os
import json
from datetime import datetime
from collections import defaultdict
from core.state import RealistReviewState


OUTPUT_DIR = r"d:\LLM-Knowledge-Graph\outputs"


def _truncate(text: str, max_len: int) -> str:
    """Truncates text to max_len with ellipsis indicator."""
    return text[:max_len] + "…" if len(text) > max_len else text


def _get_label_str(label) -> str:
    """Safely extract label string whether it's an Enum or str."""
    return label.value if hasattr(label, "value") else str(label)


def generate_reporting_node(state: RealistReviewState) -> dict:
    """
    Agent 9: Reporting & Audit Agent
    INPUT:  Entire shared state (all previous agent outputs)
    OUTPUT: PRISMA report, evidence table, audit log exported to /outputs/
    """
    print("\n[AGENT 9] Reporting & Audit Agent — Generating repository artifacts...")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Gather state data ────────────────────────────────────────────────────
    prisma = state.get("prisma_counts", {})
    registry = state.get("study_registry", [])
    included = state.get("included_studies", [])
    cmoc_extractions = state.get("extracted_cmocs", [])
    contradictions = state.get("contradictions_found", [])
    demi_regs = state.get("demi_regularities", [])
    theory = state.get("draft_programme_theory", "Not yet synthesized.")
    audit_log = state.get("audit_log", [])
    ipt = state.get("ipt_hypothesis", "Not specified")
    is_benchmark = state.get("benchmark_mode", False)

    # ── Flatten all individual CMOCs from all extractions ────────────────────
    all_cmocs = []
    for extraction in cmoc_extractions:
        if not extraction:
            continue
        # Handle new multi-CMOC format
        if hasattr(extraction, 'cmocs') and extraction.cmocs:
            for cmoc in extraction.cmocs:
                all_cmocs.append({
                    "study_id": extraction.record_id,
                    "cmoc_id": cmoc.cmoc_id,
                    "pts": _get_label_str(cmoc.programme_theory_statement),
                    "is_negative": getattr(cmoc, 'is_negative', False),
                    "confidence": getattr(cmoc, 'confidence', 0.8),
                    "context_code": cmoc.context.id,
                    "context_label": _get_label_str(cmoc.context.label),
                    "context_quote": cmoc.context.extracted_text,
                    "intervention_code": cmoc.intervention.id,
                    "intervention_label": _get_label_str(cmoc.intervention.label),
                    "intervention_quote": cmoc.intervention.extracted_text,
                    "mech_resource_code": cmoc.mechanism_resource.id,
                    "mech_resource_label": _get_label_str(cmoc.mechanism_resource.label),
                    "mechanism_response_code": cmoc.mechanism_response.id,
                    "mechanism_response_label": _get_label_str(cmoc.mechanism_response.label),
                    "mechanism_response_quote": cmoc.mechanism_response.extracted_text,
                    "outcome_code": cmoc.outcome.id,
                    "outcome_label": _get_label_str(cmoc.outcome.label),
                    "outcome_quote": cmoc.outcome.extracted_text,
                    "relationships": [
                        {
                            "source": r.source_id,
                            "target": r.target_id,
                            "type": _get_label_str(r.relation_type),
                            "evidence": r.evidence_quote
                        }
                        for r in cmoc.causal_chain
                    ]
                })
        else:
            # Backward compatibility with old flat format
            entities = {}
            for e in extraction.entities:
                label_val = _get_label_str(e.label)
                cat_val = e.category.value if hasattr(e.category, 'value') else str(e.category)
                entities[cat_val] = {"code": e.id, "label": label_val}
            all_cmocs.append({
                "study_id": extraction.record_id,
                "cmoc_id": f"{extraction.record_id}_CMOC1",
                "pts": "Unknown",
                "is_negative": False,
                "confidence": 0.5,
                "context_code": entities.get("Context", {}).get("code", "—"),
                "context_label": entities.get("Context", {}).get("label", "—"),
                "context_quote": "",
                "intervention_code": entities.get("Intervention", {}).get("code", "—"),
                "intervention_label": entities.get("Intervention", {}).get("label", "—"),
                "intervention_quote": "",
                "mech_resource_code": "E19",
                "mech_resource_label": "multiple relevant resources",
                "mechanism_response_code": entities.get("Mechanism_Response", {}).get("code", "—"),
                "mechanism_response_label": entities.get("Mechanism_Response", {}).get("label", "—"),
                "mechanism_response_quote": "",
                "outcome_code": entities.get("Outcome", {}).get("code", "—"),
                "outcome_label": entities.get("Outcome", {}).get("label", "—"),
                "outcome_quote": "",
                "relationships": []
            })

    # ── 1. PRISMA Flow Report ────────────────────────────────────────────────
    records_identified = len(registry)
    records_screened = prisma.get("records_screened", records_identified)
    ta_excluded = prisma.get("title_abstract_excluded", 0)
    ft_assessed = prisma.get("full_texts_assessed", records_screened - ta_excluded)
    ft_excluded = prisma.get("full_text_excluded", 0)
    studies_included = prisma.get("studies_included", len(included))

    prisma_report = f"""# PRISMA Flow Report
Generated: {now}
Mode: {'BENCHMARK (Richmond et al. 2020 — all studies pre-included)' if is_benchmark else 'PRODUCTION (LLM screening)'}

## Search & Identification
- Records identified: {records_identified}
- Records after deduplication: {records_identified}

## Screening
- Records screened (title/abstract): {records_screened}
- Records excluded at title/abstract: {ta_excluded}
- Full texts assessed for eligibility: {ft_assessed}
- Full texts excluded: {ft_excluded}

## Included
- Studies included in synthesis: {studies_included}

## Realist Review Outputs
- Total CMOCs extracted: {len(all_cmocs)}
  - Positive pathways: {sum(1 for c in all_cmocs if not c['is_negative'])}
  - Negative pathways: {sum(1 for c in all_cmocs if c['is_negative'])}
- Contradictions detected: {len(contradictions)}
- Demi-regularities identified: {len(demi_regs)}
- Programme Theory: {'Generated' if theory and not theory.startswith('[SYNTHESIS ERROR]') else 'Pending'}
"""
    with open(os.path.join(OUTPUT_DIR, "PRISMA_report.md"), "w", encoding="utf-8") as f:
        f.write(prisma_report)
    print("  [SAVED] PRISMA_report.md")

    # ── 2. Evidence Table (JSON — full detail) ───────────────────────────────
    with open(os.path.join(OUTPUT_DIR, "evidence_table.json"), "w", encoding="utf-8") as f:
        json.dump(all_cmocs, f, indent=2, ensure_ascii=False)
    print(f"  [SAVED] evidence_table.json ({len(all_cmocs)} CMOC entries)")

    # ── 3. Evidence Table (Markdown — grouped by PTS) ────────────────────────
    md_table = f"# Evidence Table: Extracted CMOCs\nGenerated: {now}\n"
    md_table += f"Total CMOCs: {len(all_cmocs)} from {len(cmoc_extractions)} studies\n\n"

    # Group by PTS for Richmond-aligned presentation
    pts_groups = defaultdict(list)
    for cmoc in all_cmocs:
        pts_groups[cmoc["pts"]].append(cmoc)

    for pts_label, cmocs_in_group in sorted(pts_groups.items()):
        neg_count = sum(1 for c in cmocs_in_group if c['is_negative'])
        md_table += f"\n## {pts_label}\n"
        md_table += f"CMOCs in this group: {len(cmocs_in_group)} ({neg_count} negative)\n\n"
        md_table += "| # | Study | CMOC | Context | Intervention | Mech. Response | Outcome | Neg? | Conf |\n"
        md_table += "|---|-------|------|---------|-------------|---------------|--------|------|------|\n"
        for i, cmoc in enumerate(cmocs_in_group, 1):
            neg_flag = "❌" if cmoc['is_negative'] else "✓"
            conf = f"{cmoc['confidence']:.1f}"
            md_table += (
                f"| {i} "
                f"| {cmoc['study_id']} "
                f"| {cmoc['cmoc_id'].split('_')[-1]} "
                f"| {cmoc['context_code']}: {_truncate(cmoc['context_label'], 30)} "
                f"| {cmoc['intervention_code']}: {_truncate(cmoc['intervention_label'], 30)} "
                f"| {cmoc['mechanism_response_code']}: {_truncate(cmoc['mechanism_response_label'], 25)} "
                f"| {cmoc['outcome_code']}: {_truncate(cmoc['outcome_label'], 25)} "
                f"| {neg_flag} "
                f"| {conf} |\n"
            )
        md_table += "\n"

    with open(os.path.join(OUTPUT_DIR, "evidence_table.md"), "w", encoding="utf-8") as f:
        f.write(md_table)
    print("  [SAVED] evidence_table.md")

    # ── 4. Entity & Relationship Summary (for visualization) ─────────────────
    nodes = {}  # code -> {label, category, count, studies}
    edges = []  # list of {source, target, type, count}
    edge_counter = defaultdict(int)

    for cmoc in all_cmocs:
        for entity_key in ['context', 'intervention', 'mechanism_response', 'outcome']:
            code = cmoc[f'{entity_key}_code']
            label = cmoc[f'{entity_key}_label']
            category = entity_key.replace('_', ' ').title()
            if code not in nodes:
                nodes[code] = {"label": label, "category": category, "count": 0, "studies": set()}
            nodes[code]["count"] += 1
            nodes[code]["studies"].add(cmoc["study_id"])

        # Count relationship types
        for rel in cmoc.get("relationships", []):
            key = (rel["source"], rel["target"], rel["type"])
            edge_counter[key] += 1

    # Build edge list
    for (src, tgt, rtype), count in edge_counter.items():
        edges.append({"source": src, "target": tgt, "type": rtype, "weight": count})

    # Write node summary
    er_summary = f"# Entity & Relationship Summary\nGenerated: {now}\n\n"
    er_summary += "## Nodes (Entities)\n\n"
    er_summary += "| Code | Category | Label | Frequency | Studies |\n"
    er_summary += "|------|----------|-------|-----------|--------|\n"
    for code in sorted(nodes.keys()):
        n = nodes[code]
        studies_str = ", ".join(sorted(n["studies"]))
        er_summary += f"| {code} | {n['category']} | {_truncate(n['label'], 50)} | {n['count']} | {studies_str} |\n"

    er_summary += f"\n\n## Edges (Relationships)\n\n"
    er_summary += "| Source | → Type → | Target | Weight |\n"
    er_summary += "|--------|----------|--------|--------|\n"
    for edge in sorted(edges, key=lambda e: -e["weight"]):
        er_summary += f"| {edge['source']} | {edge['type']} | {edge['target']} | {edge['weight']} |\n"

    er_summary += "\n\n## Graph Statistics\n\n"
    er_summary += f"- **Unique Entity Codes**: {len(nodes)}\n"
    er_summary += f"- **Unique Relationship Edges**: {len(edges)}\n"
    er_summary += f"- **Total CMOCs**: {len(all_cmocs)}\n"
    er_summary += f"- **Studies with CMOCs**: {len(cmoc_extractions)}\n"
    er_summary += f"- **PTS Distribution**:\n"
    for pts_label in sorted(pts_groups.keys()):
        er_summary += f"  - {pts_label}: {len(pts_groups[pts_label])} CMOCs\n"

    with open(os.path.join(OUTPUT_DIR, "entity_relationship_summary.md"), "w", encoding="utf-8") as f:
        f.write(er_summary)
    print("  [SAVED] entity_relationship_summary.md")

    # ── 5. Programme Theory Document ─────────────────────────────────────────
    theory_doc = f"""# Final Programme Theory
Generated: {now}
CMOCs Analyzed: {len(all_cmocs)}
PTS Groups Covered: {len(pts_groups)}

## Initial Programme Theory (IPT)
{ipt}

## Synthesized Programme Theory (Refined)
{theory}

## Contradictions Identified
{chr(10).join(f'- {c}' for c in contradictions) if contradictions else 'None detected.'}

## Demi-Regularities (Recurrent Patterns)
{chr(10).join(f'- {d}' for d in demi_regs) if demi_regs else 'Not identified.'}
"""
    with open(os.path.join(OUTPUT_DIR, "programme_theory_final.md"), "w", encoding="utf-8") as f:
        f.write(theory_doc)
    print("  [SAVED] programme_theory_final.md")

    # ── 6. Full Audit Trail ──────────────────────────────────────────────────
    audit_doc = f"# Full Audit Trail\nGenerated: {now}\nTotal entries: {len(audit_log)}\n\n"
    for i, entry in enumerate(audit_log, 1):
        audit_doc += f"{i}. {entry}\n"

    with open(os.path.join(OUTPUT_DIR, "audit_trail.md"), "w", encoding="utf-8") as f:
        f.write(audit_doc)
    print(f"  [SAVED] audit_trail.md ({len(audit_log)} entries)")

    # ── 7. Contradiction Register ────────────────────────────────────────────
    if contradictions:
        cr_doc = f"# Contradiction Register\nGenerated: {now}\n"
        cr_doc += f"Total contradictions: {len(contradictions)}\n\n"
        for i, c in enumerate(contradictions, 1):
            cr_doc += f"## Contradiction {i}\n{c}\n\n---\n\n"
        with open(os.path.join(OUTPUT_DIR, "contradiction_register.md"), "w", encoding="utf-8") as f:
            f.write(cr_doc)
        print(f"  [SAVED] contradiction_register.md ({len(contradictions)} entries)")

    # ── 8. Demi-Regularity Report ────────────────────────────────────────────
    if demi_regs:
        dr_doc = f"# Demi-Regularity Report\nGenerated: {now}\n"
        dr_doc += f"Total patterns: {len(demi_regs)}\n\n"
        for i, dr in enumerate(demi_regs, 1):
            dr_doc += f"## Pattern {i}\n{dr}\n\n"
        with open(os.path.join(OUTPUT_DIR, "demi_regularity_report.md"), "w", encoding="utf-8") as f:
            f.write(dr_doc)
        print(f"  [SAVED] demi_regularity_report.md ({len(demi_regs)} patterns)")

    # ── 9. PTS Coverage Comparison (vs Richmond benchmark) ───────────────────
    richmond_benchmark = {
        "PTS1": {"context": "E02", "expected_studies": 15, "expected_cmocs": "~20"},
        "PTS2": {"context": "E03", "expected_studies": 5, "expected_cmocs": "~6"},
        "PTS3": {"context": "E04", "expected_studies": 4, "expected_cmocs": "~5"},
        "PTS4": {"context": "E05", "expected_studies": 3, "expected_cmocs": "~4 (negative)"},
        "PTS5": {"context": "E06", "expected_studies": 3, "expected_cmocs": "~4"},
    }

    comparison = f"# Richmond Benchmark Comparison\nGenerated: {now}\n\n"
    comparison += "## PTS Coverage\n\n"
    comparison += "| PTS | Context | Richmond (expected) | Our System | Match |\n"
    comparison += "|-----|---------|--------------------:|----------:|---------|\n"
    for pts_key, benchmark in richmond_benchmark.items():
        pts_full = [k for k in pts_groups.keys() if pts_key in k]
        our_count = sum(len(pts_groups[k]) for k in pts_full) if pts_full else 0
        match_icon = "✅" if our_count > 0 else "❌"
        comparison += (
            f"| {pts_key} | {benchmark['context']} "
            f"| {benchmark['expected_cmocs']} "
            f"| {our_count} "
            f"| {match_icon} |\n"
        )

    comparison += "\n## Entity Code Distribution\n\n"
    comparison += "### Context Codes Used\n"
    ctx_dist = defaultdict(int)
    for cmoc in all_cmocs:
        ctx_dist[cmoc["context_code"]] += 1
    for code, count in sorted(ctx_dist.items(), key=lambda x: -x[1]):
        comparison += f"- {code}: {count} CMOCs ({count/len(all_cmocs)*100:.0f}%)\n"

    comparison += "\n### Mechanism Response Codes Used\n"
    mr_dist = defaultdict(int)
    for cmoc in all_cmocs:
        mr_dist[cmoc["mechanism_response_code"]] += 1
    for code, count in sorted(mr_dist.items(), key=lambda x: -x[1]):
        comparison += f"- {code}: {count} CMOCs ({count/len(all_cmocs)*100:.0f}%)\n"

    comparison += "\n### Outcome Codes Used\n"
    out_dist = defaultdict(int)
    for cmoc in all_cmocs:
        out_dist[cmoc["outcome_code"]] += 1
    for code, count in sorted(out_dist.items(), key=lambda x: -x[1]):
        comparison += f"- {code}: {count} CMOCs ({count/len(all_cmocs)*100:.0f}%)\n"

    with open(os.path.join(OUTPUT_DIR, "richmond_comparison.md"), "w", encoding="utf-8") as f:
        f.write(comparison)
    print("  [SAVED] richmond_comparison.md")

    print(f"\n  All repository artifacts saved to {OUTPUT_DIR}")
    log = (f"[Reporting Agent] {len(all_cmocs)} CMOC rows, {len(contradictions)} contradictions, "
           f"{len(demi_regs)} demi-regularities. All artifacts exported.")

    # Build backward-compatible evidence_table for state
    evidence_rows = []
    for cmoc in all_cmocs:
        evidence_rows.append({
            "study_id": cmoc["study_id"],
            "cmoc_id": cmoc["cmoc_id"],
            "pts": cmoc["pts"],
            "context": cmoc["context_label"],
            "intervention": cmoc["intervention_label"],
            "mechanism_resource": cmoc["mech_resource_label"],
            "mechanism_response": cmoc["mechanism_response_label"],
            "outcome": cmoc["outcome_label"],
            "is_negative": cmoc["is_negative"],
            "confidence": cmoc["confidence"],
            "relationship_count": len(cmoc.get("relationships", []))
        })

    return {"audit_log": [log], "evidence_table": evidence_rows}
