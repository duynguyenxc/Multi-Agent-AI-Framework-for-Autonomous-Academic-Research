"""
plugins/realist_synthesis/cross_study_synthesizer.py — Agent 10: Theory Synthesizer
=====================================================================================
Phase 1 rewrite — Programme-Theory-Statement-aware synthesis.

Why this rewrite was necessary
-------------------------------
The previous synthesizer made ONE mega-call dumping all CMOCs + all
communities + all contradictions into a single LLM context window. This:
  • Forced the LLM to hallucinate filler ("data does not explicitly address…")
    for PTS3 and PTS4 because the bucket was empty after the lazy E02 collapse.
  • Lost CMOC data to the 15K-char cap when more than ~10 studies were extracted.
  • Could not produce a publication-grade theory because each PTS section
    needed deep focus, not a single generic instruction.

Phase 1 approach (one sub-call per PTS, plus a final integration call)
-----------------------------------------------------------------------
  1. Bucket all CMOCs (across all studies) by Programme Theory Statement
     (PTS1–PTS5).
  2. For each PTS that has ≥1 CMOC, run a focused synthesis call producing
     the PTS section in academic prose, evidence-grounded.
  3. For empty PTS buckets, write a transparent "No evidence found" placeholder
     — explicitly forbidden from speculation.
  4. Concatenate the 5 PTS sections with a brief integration paragraph
     summarising demi-regularities and cross-PTS contradictions.
"""
import json
from typing import Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.ontology import CMOCExtraction, RichmondPTS, SingleCMOC
from core.state import RealistReviewState


# ── PTS metadata (canonical from Richmond, Results §3.2) ─────────────────────
PTS_META: Dict[str, Dict[str, str]] = {
    "PTS1": {
        "context_code": "E02",
        "context_label": "Students with low clinical domain-specific knowledge",
        "typical_chain": "E07/E15/E18 → E19 → E20/E27 → E25/E29/E30",
    },
    "PTS2": {
        "context_code": "E03",
        "context_label": "Students with high clinical domain-specific knowledge",
        "typical_chain": "E10/E11 → E19 → E24/E39 → E25/E30/E43/E44",
    },
    "PTS3": {
        "context_code": "E04",
        "context_label": "Students with positive coping / self-efficacy",
        "typical_chain": "E09/E10/E11 → E19 → E26/E27 → E22/E28/E40/E41",
    },
    "PTS4": {
        "context_code": "E05",
        "context_label": "Students with negative coping / lacking self-efficacy",
        "typical_chain": "E09/E10/E14 → E19 → E23/E32/E33/E34/E35/E45 → E36/E37/E38/E47",
    },
    "PTS5": {
        "context_code": "E06",
        "context_label": "Students with different levels of knowledge within a group",
        "typical_chain": "E07/E17 → E19 → E27/E39/E42 → E29/E43/E44/E46",
    },
}


PTS_SECTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a master theoretician in RAMESES-compliant Realist
Synthesis, writing a section of Richmond et al. (2020)-style programme theory.

You will receive ALL CMOCs that map to ONE specific Programme Theory Statement
(PTS). Your job is to compose that single PTS section.

REQUIREMENTS
  • Write in formal academic prose suitable for Medical Education / RRE.
  • Cite every claim by record_id (e.g. "S001", "S014").
  • Use Richmond's E-codes verbatim in parentheses, e.g. "low-knowledge
    students (E02)".
  • Surface convergent patterns (3+ studies pointing the same way) and any
    intra-PTS contradictions.
  • If is_negative CMOCs are present, integrate them as boundary conditions.
  • Be evidence-grounded — NEVER speculate beyond the provided CMOCs.
  • Keep the section to 250–400 words."""),
    ("human", """Programme Theory Statement: {pts_id}
Context anchor: {context_code} — "{context_label}"
Canonical chain (Richmond): {typical_chain}
CMOCs in this PTS bucket ({n} total):

{cmocs_json}

Cross-study evidence summary (from contradiction & demi-regularity agents):
{evidence_summary}

Write the {pts_id} programme-theory section now.""")
])


INTEGRATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the senior author finalising Richmond-style programme
theory. You will be given five PTS section drafts. Produce a 150–250 word
INTEGRATION paragraph that:
  • States which PTSs had strong evidence vs which were under-evidenced.
  • Names the most important cross-PTS demi-regularities.
  • Names the most consequential cross-PTS contradictions (if any).
  • Echoes Richmond's framing: "what works, for whom, in what contexts, how,
    and why".

Do NOT repeat the section content — assume it is rendered below your paragraph.
"""),
    ("human", """Sections produced:
{section_summaries}

Demi-regularities identified system-wide:
{demi_regs}

Contradictions adjudicated system-wide:
{contradictions}

Write the integration paragraph now.""")
])


def _label_value(label) -> str:
    """Resolve a label (enum or string) to its full Richmond label string."""
    if hasattr(label, "value"):
        return label.value
    return str(label)


def _label_code(label) -> str:
    """Resolve a label to its E-code (e.g. 'E02')."""
    if hasattr(label, "name"):
        return label.name
    return str(label)


def _cmoc_to_dict(study_id: str, cmoc: SingleCMOC) -> dict:
    return {
        "study_id": study_id,
        "cmoc_id": cmoc.cmoc_id,
        "is_negative": cmoc.is_negative,
        "confidence": cmoc.confidence,
        "context": {"code": _label_code(cmoc.context.label),
                    "label": _label_value(cmoc.context.label),
                    "evidence": cmoc.context.extracted_text},
        "intervention": {"code": _label_code(cmoc.intervention.label),
                         "label": _label_value(cmoc.intervention.label),
                         "evidence": cmoc.intervention.extracted_text},
        "mechanism_resource": {"code": _label_code(cmoc.mechanism_resource.label),
                               "evidence": cmoc.mechanism_resource.extracted_text},
        "mechanism_response": {"code": _label_code(cmoc.mechanism_response.label),
                               "label": _label_value(cmoc.mechanism_response.label),
                               "evidence": cmoc.mechanism_response.extracted_text},
        "outcome": {"code": _label_code(cmoc.outcome.label),
                    "label": _label_value(cmoc.outcome.label),
                    "evidence": cmoc.outcome.extracted_text},
    }


def synthesis_node(state: RealistReviewState) -> dict:
    """Agent 10 — synthesize one section per PTS, then integrate."""
    cmoc_extractions: List[CMOCExtraction] = state.get("extracted_cmocs", [])
    contradictions = state.get("contradictions_found", [])
    demi_regs = state.get("demi_regularities", [])
    leiden_clusters = state.get("leiden_communities", [])

    # ── Bucket CMOCs by PTS ─────────────────────────────────────────────────
    buckets: Dict[str, List[dict]] = {pts: [] for pts in PTS_META.keys()}
    buckets["N/A"] = []
    for ext in cmoc_extractions:
        if ext is None:
            continue
        for cmoc in ext.cmocs:
            pts = cmoc.programme_theory_statement.value
            buckets.setdefault(pts, []).append(_cmoc_to_dict(ext.record_id, cmoc))

    total_cmocs = sum(len(v) for v in buckets.values())
    print(f"\n[AGENT 10] Theory Synthesizer — {total_cmocs} CMOCs across "
          f"{sum(1 for v in buckets.values() if v)} populated PTS bucket(s)")
    for pts, lst in buckets.items():
        if lst:
            print(f"  {pts}: {len(lst)} CMOC(s)")

    # ── Evidence summary string for sub-call context ────────────────────────
    evidence_summary_parts = []
    if demi_regs:
        evidence_summary_parts.append("Demi-regularities:")
        evidence_summary_parts.extend(f"  • {d}" for d in demi_regs[:10])
    if contradictions:
        evidence_summary_parts.append("Contradictions:")
        evidence_summary_parts.extend(f"  • {c}" for c in contradictions[:10])
    if leiden_clusters:
        top_communities = sorted(leiden_clusters, key=lambda x: x.get("rank", 0), reverse=True)[:5]
        evidence_summary_parts.append("Top GraphRAG communities:")
        for com in top_communities:
            title = com.get("title", "untitled")[:80]
            evidence_summary_parts.append(f"  • {title}")
    evidence_summary = "\n".join(evidence_summary_parts) if evidence_summary_parts else "None."

    # ── One LLM call per populated PTS ──────────────────────────────────────
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    pts_section_chain = PTS_SECTION_PROMPT | llm

    sections: Dict[str, str] = {}
    for pts in ("PTS1", "PTS2", "PTS3", "PTS4", "PTS5"):
        meta = PTS_META[pts]
        bucket = buckets.get(pts, [])
        if not bucket:
            sections[pts] = (
                f"## {pts} — {meta['context_label']} ({meta['context_code']})\n\n"
                f"*No evidence found in the included studies for this Programme "
                f"Theory Statement. We do not speculate beyond what the data "
                f"supports. Canonical Richmond chain: {meta['typical_chain']}.*"
            )
            continue
        try:
            response = pts_section_chain.invoke({
                "pts_id": pts,
                "context_code": meta["context_code"],
                "context_label": meta["context_label"],
                "typical_chain": meta["typical_chain"],
                "n": len(bucket),
                "cmocs_json": json.dumps(bucket, indent=2, default=str)[:12_000],
                "evidence_summary": evidence_summary[:3_000],
            })
            section_text = response.content.strip()
            if not section_text.startswith("#"):
                section_text = (
                    f"## {pts} — {meta['context_label']} ({meta['context_code']})\n\n"
                    + section_text
                )
            sections[pts] = section_text
            print(f"  ✓ {pts} section drafted ({len(section_text)} chars)")
        except Exception as e:
            err = f"PTS {pts} synthesis failed: {e}"
            print(f"  [ERROR] {err[:120]}")
            sections[pts] = f"## {pts} — synthesis error\n\n{str(e)[:200]}"

    # ── Integration paragraph ───────────────────────────────────────────────
    section_summaries = "\n\n".join(
        f"{pts} (n={len(buckets.get(pts, []))}):\n{txt[:600]}…" for pts, txt in sections.items()
    )
    try:
        integration_response = (INTEGRATION_PROMPT | llm).invoke({
            "section_summaries": section_summaries[:10_000],
            "demi_regs": "\n".join(f"  • {d}" for d in demi_regs[:10]) or "None.",
            "contradictions": "\n".join(f"  • {c}" for c in contradictions[:10]) or "None.",
        })
        integration_text = integration_response.content.strip()
    except Exception as e:
        integration_text = f"*Integration synthesis failed: {str(e)[:200]}*"

    # ── Stitch full programme theory document ───────────────────────────────
    final_theory = (
        "# Refined Programme Theory (Richmond-aligned, 5 PTS structure)\n\n"
        "## Integration\n\n"
        + integration_text + "\n\n"
        + "\n\n".join(sections[pts] for pts in ("PTS1", "PTS2", "PTS3", "PTS4", "PTS5"))
    )

    log = (f"[Synthesis Agent] Multi-PTS theory generated: {len(final_theory)} chars; "
           f"buckets {[(pts, len(buckets.get(pts, []))) for pts in ('PTS1','PTS2','PTS3','PTS4','PTS5')]}")
    print(f"  Full theory: {len(final_theory)} chars")
    return {"draft_programme_theory": final_theory, "audit_log": [log]}
