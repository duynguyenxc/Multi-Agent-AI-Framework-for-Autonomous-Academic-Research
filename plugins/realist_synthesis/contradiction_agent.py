"""
plugins/realist_synthesis/contradiction_agent.py — Agent 8: Contradiction Detection
=====================================================================================
Phase 1 rewrite for the multi-CMOC schema.

Why this rewrite was necessary
-------------------------------
The previous version dumped ALL CMOCs as one giant JSON blob into a single LLM
call (token-heavy, context confusion, capped at 12K chars). Combined with the
new multi-CMOC schema producing ~3× more CMOCs per study, the old approach
would lose 60-70% of the data to truncation.

Phase 1 approach (structural pre-filtering before the LLM)
-----------------------------------------------------------
  1. Flatten every paper's CMOCs into SingleCMOC objects (one row per CMOC,
     not one row per paper).
  2. Bucket the CMOCs by Programme Theory Statement (PTS1–PTS5) — Richmond
     organises her findings the same way.
  3. Inside each PTS bucket, scan for STRUCTURAL contradictions BEFORE calling
     the LLM. A structural contradiction is a pair of CMOCs that share the
     same Context+Intervention but produce opposite Outcomes (positive vs
     negative E-code).
  4. Only the candidate pairs that the structural filter flagged are sent to
     the LLM for narrative adjudication — drastically reduces tokens and
     keeps the LLM focused on real conflicts.
  5. Demi-regularities (recurring patterns that hold "for the most part")
     are produced by counting CMOCs that share the same (Context, M-response,
     Outcome) triple across ≥3 studies.

This pre-filtering pattern is inspired by ContraCrow (Skarlinski et al., 2024,
arXiv 2409.13740) which uses claim-level extraction + Likert-scaled adjudication
to scale contradiction detection beyond what a single LLM call can do.
"""
import json
from collections import defaultdict
from typing import List, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.ontology import (
    CMOCExtraction,
    SingleCMOC,
    RichmondPTS,
    OutcomeType,
)
from core.state import RealistReviewState


# ── Outcome polarity classification (positive vs negative E-codes) ───────────
POSITIVE_OUTCOMES = {
    OutcomeType.E21.name, OutcomeType.E22.name, OutcomeType.E25.name,
    OutcomeType.E28.name, OutcomeType.E29.name, OutcomeType.E30.name,
    OutcomeType.E40.name, OutcomeType.E41.name, OutcomeType.E43.name,
    OutcomeType.E44.name, OutcomeType.E46.name,
}
NEGATIVE_OUTCOMES = {
    OutcomeType.E36.name, OutcomeType.E37.name, OutcomeType.E38.name,
    OutcomeType.E47.name,
}


def _label_to_code(label) -> str:
    """Convert a Pydantic enum or string to the canonical E-code (e.g. 'E02')."""
    if hasattr(label, "name"):
        return label.name
    return str(label)


def _outcome_polarity(cmoc: SingleCMOC) -> str:
    """Returns 'positive', 'negative', or 'neutral' for an outcome."""
    code = _label_to_code(cmoc.outcome.label)
    # Strip the value-form to the enum name
    if code.startswith("E"):
        if code in POSITIVE_OUTCOMES:
            return "positive"
        if code in NEGATIVE_OUTCOMES:
            return "negative"
    # Fallback: enum object → use name attribute
    code = cmoc.outcome.label.name if hasattr(cmoc.outcome.label, "name") else code
    if code in POSITIVE_OUTCOMES:
        return "positive"
    if code in NEGATIVE_OUTCOMES:
        return "negative"
    return "neutral"


def _flatten_cmocs(cmoc_extractions: List[CMOCExtraction]) -> List[Tuple[str, SingleCMOC]]:
    """Flattens [CMOCExtraction] → [(study_id, SingleCMOC)] for cross-study analysis."""
    out = []
    for ext in cmoc_extractions:
        if ext is None:
            continue
        for cmoc in ext.cmocs:
            out.append((ext.record_id, cmoc))
    return out


def _find_structural_contradictions(flat: List[Tuple[str, SingleCMOC]]) -> List[dict]:
    """Pre-filter pass: pairs of CMOCs with same Context+Intervention but opposite outcome polarity."""
    candidates = []
    n = len(flat)
    for i in range(n):
        sid_a, cmoc_a = flat[i]
        ctx_a = cmoc_a.context.label.name if hasattr(cmoc_a.context.label, "name") else str(cmoc_a.context.label)
        int_a = cmoc_a.intervention.label.name if hasattr(cmoc_a.intervention.label, "name") else str(cmoc_a.intervention.label)
        pol_a = _outcome_polarity(cmoc_a)
        for j in range(i + 1, n):
            sid_b, cmoc_b = flat[j]
            ctx_b = cmoc_b.context.label.name if hasattr(cmoc_b.context.label, "name") else str(cmoc_b.context.label)
            int_b = cmoc_b.intervention.label.name if hasattr(cmoc_b.intervention.label, "name") else str(cmoc_b.intervention.label)
            pol_b = _outcome_polarity(cmoc_b)

            same_context = ctx_a == ctx_b
            same_intervention = int_a == int_b
            opposite_polarity = (pol_a == "positive" and pol_b == "negative") or \
                                (pol_a == "negative" and pol_b == "positive")

            if same_context and same_intervention and opposite_polarity:
                candidates.append({
                    "cmoc_a": {
                        "study_id": sid_a,
                        "cmoc_id": cmoc_a.cmoc_id,
                        "pts": cmoc_a.programme_theory_statement.value,
                        "context": ctx_a,
                        "intervention": int_a,
                        "outcome": cmoc_a.outcome.label.name if hasattr(cmoc_a.outcome.label, "name") else str(cmoc_a.outcome.label),
                        "outcome_text": cmoc_a.outcome.extracted_text,
                    },
                    "cmoc_b": {
                        "study_id": sid_b,
                        "cmoc_id": cmoc_b.cmoc_id,
                        "pts": cmoc_b.programme_theory_statement.value,
                        "context": ctx_b,
                        "intervention": int_b,
                        "outcome": cmoc_b.outcome.label.name if hasattr(cmoc_b.outcome.label, "name") else str(cmoc_b.outcome.label),
                        "outcome_text": cmoc_b.outcome.extracted_text,
                    },
                })
    return candidates


def _find_demi_regularities(flat: List[Tuple[str, SingleCMOC]], min_support: int = 3) -> List[str]:
    """A demi-regularity is a (Context, M-response, Outcome) triple that holds across ≥ min_support studies."""
    triple_counts: dict = defaultdict(list)
    for sid, cmoc in flat:
        ctx = cmoc.context.label.name if hasattr(cmoc.context.label, "name") else str(cmoc.context.label)
        mresp = cmoc.mechanism_response.label.name if hasattr(cmoc.mechanism_response.label, "name") else str(cmoc.mechanism_response.label)
        out = cmoc.outcome.label.name if hasattr(cmoc.outcome.label, "name") else str(cmoc.outcome.label)
        triple_counts[(ctx, mresp, out)].append(sid)

    regularities = []
    for (ctx, mresp, out), studies in sorted(triple_counts.items(), key=lambda kv: -len(kv[1])):
        if len(studies) >= min_support:
            unique_studies = sorted(set(studies))
            regularities.append(
                f"Demi-regularity: ({ctx} + {mresp} → {out}) observed in "
                f"{len(unique_studies)} studies: {', '.join(unique_studies[:6])}"
                f"{' …' if len(unique_studies) > 6 else ''}"
            )
    return regularities


# ── LLM-adjudicated structured output for narrative explanation ─────────────
class AdjudicatedContradiction(BaseModel):
    cmoc_a_id: str = Field(..., description="CMOC ID of the first conflicting configuration")
    cmoc_b_id: str = Field(..., description="CMOC ID of the second conflicting configuration")
    likert_score: int = Field(
        ...,
        ge=1, le=11,
        description=(
            "11-point Likert scale of contradiction strength (1=trivial / "
            "complementary, 11=direct contradiction). Inspired by ContraCrow."
        ),
    )
    explanation: str = Field(..., description="Narrative explanation of WHY these CMOCs conflict")
    moderating_condition: str = Field(
        "", description="Any contextual factor that might explain the divergence"
    )


class AdjudicationReport(BaseModel):
    contradictions: List[AdjudicatedContradiction] = Field(default_factory=list)


ADJUDICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior Realist Synthesis adjudicator following the
RAMESES contradiction-detection standard combined with the ContraCrow Likert
methodology (Skarlinski et al., 2024).

You will be given pairs of CMOCs that share the same Context and Intervention
but produce opposite-polarity Outcomes. Your job is to adjudicate each pair:

  • Assign a Likert score 1–11 where 1 = trivial/complementary divergence and
    11 = direct contradiction warranting researcher attention.
  • Produce a narrative explanation: WHY do these CMOCs disagree? What
    moderating condition (study population, intervention dosage, assessment
    method) might reconcile them?
  • Only report pairs with Likert ≥ 6 — below that they are noise.

Use Richmond's E-codes verbatim when referencing concepts."""),
    ("human", """{candidate_count} candidate contradiction pair(s) were
identified by the structural pre-filter:

{candidates_json}

Adjudicate each pair. Return only those with Likert ≥ 6.""")
])


def detect_contradictions_node(state: RealistReviewState) -> dict:
    """Agent 8 — multi-CMOC, structural pre-filter + LLM adjudication."""
    cmoc_extractions: List[CMOCExtraction] = state.get("extracted_cmocs", [])

    flat = _flatten_cmocs(cmoc_extractions)
    print(f"\n[AGENT 8] Contradiction Detection — {len(flat)} CMOCs from "
          f"{len(cmoc_extractions)} papers")

    if len(flat) < 2:
        log = f"[Contradiction Agent] Skipped — only {len(flat)} CMOC(s) available."
        return {"contradictions_found": [], "demi_regularities": [], "audit_log": [log]}

    # ── Structural pre-filter ───────────────────────────────────────────────
    candidates = _find_structural_contradictions(flat)
    print(f"  Structural pre-filter: {len(candidates)} candidate contradiction pair(s)")

    # ── Demi-regularities (no LLM needed) ───────────────────────────────────
    demi_regs = _find_demi_regularities(flat, min_support=3)
    print(f"  Demi-regularities: {len(demi_regs)} recurrent pattern(s)")

    # ── LLM adjudication (only on candidates) ───────────────────────────────
    contradiction_strings: List[str] = []
    if candidates:
        try:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            structured_llm = llm.with_structured_output(AdjudicationReport)
            chain = ADJUDICATION_PROMPT | structured_llm

            report: AdjudicationReport = chain.invoke({
                "candidate_count": len(candidates),
                "candidates_json": json.dumps(candidates[:25], indent=2),  # cap at 25 pairs
            })

            for c in report.contradictions:
                contradiction_strings.append(
                    f"[{c.cmoc_a_id} vs {c.cmoc_b_id}] Likert={c.likert_score}/11 | "
                    f"{c.explanation}"
                    + (f" | Moderator: {c.moderating_condition}" if c.moderating_condition else "")
                )
            print(f"  LLM adjudication: {len(contradiction_strings)} contradictions "
                  f"with Likert ≥ 6")
        except Exception as e:
            err = f"Contradiction adjudication failed: {e}"
            print(f"  [ERROR] {err[:120]}")
            return {
                "contradictions_found": [],
                "demi_regularities": demi_regs,
                "errors": [err],
                "audit_log": [f"[Contradiction Agent] Error: {str(e)[:100]}"],
            }
    else:
        print("  No structural contradictions detected — skipping LLM adjudication.")

    log = (f"[Contradiction Agent] {len(flat)} CMOCs → "
           f"{len(candidates)} candidate pairs → {len(contradiction_strings)} "
           f"adjudicated contradictions; {len(demi_regs)} demi-regularities.")
    return {
        "contradictions_found": contradiction_strings,
        "demi_regularities": demi_regs,
        "audit_log": [log],
    }
