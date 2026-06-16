"""
core/agents/screening_agent.py — Agent 4: Title/Abstract Screener + Agent 6: Full-Text Eligibility
=====================================================================================================
Richmond Alignment:
  - Agent 4 → Primary Reviewer (two-stage screening: title/abstract then full text)
  - Agent 6 → Secondary Reviewer (methodological rigour + theory contribution)

Human Reference: Richmond screened for: undergraduate medical students, clinical reasoning
training interventions, post-2000 publications. They used a TWO-STAGE process.
"""
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List
from core.state import RealistReviewState, StudyRecord


class ScreeningDecision(BaseModel):
    """Structured screening output matching PRISMA standards."""
    study_id: str
    decision: str = Field(..., description="Must be exactly: 'include', 'exclude', or 'uncertain'")
    rationale: str = Field(..., description="Evidence-grounded rationale for the decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


SCREENING_SYSTEM_PROMPT = """You are a Primary Reviewer in a RAMESES-compliant Realist Systematic Review.
You apply strict inclusion/exclusion criteria to screen literature, exactly as a human researcher would.

RICHMOND BENCHMARK CRITERIA:
- Population: Undergraduate students in medical or healthcare professions education
- Intervention: Educational interventions targeting clinical reasoning (analytical or non-analytical)
- Outcome: Any measurable learning outcome (diagnostic accuracy, illness scripts, clinical performance)
- Date: Post-2000 publications
- Study type: Any study design with sufficient methodological rigour for theory building

DECISION RULES:
- 'include': Clearly meets all criteria
- 'exclude': Clearly fails one or more criteria — state EXACTLY which criterion fails
- 'uncertain': Borderline — requires human adjudication (HITL checkpoint)

IMPORTANT: When in doubt, mark 'uncertain' to preserve recall (do not auto-exclude).
"""

SCREENING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SCREENING_SYSTEM_PROMPT),
    ("human", """Inclusion Criteria (researcher-defined):
{inclusion_criteria}

Study to Screen:
Study ID: {study_id}
Title: {title}
Abstract: {abstract}

Classify this study for inclusion in the RAMESES realist review.
""")
])

FULLTEXT_SYSTEM_PROMPT = """You are a Secondary Reviewer performing full-text eligibility assessment.
You evaluate: (1) Methodological rigour, (2) Contribution to developing theory (CMOCs extractable?).

This is Stage 2 of a two-stage screening process aligned with Richmond et al. (2020).
Even studies with limited quality CAN be included if they contribute meaningfully to theory building.
"""

FULLTEXT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", FULLTEXT_SYSTEM_PROMPT),
    ("human", """Inclusion Criteria:
{inclusion_criteria}

Study ID: {study_id}
Full Text (first 3000 chars):
{full_text}

Assess methodological rigour AND contribution to theory building.
Can CMOCs (Context-Mechanism-Outcome configurations) be extracted from this paper?
""")
])


def screen_title_abstract_node(state: RealistReviewState) -> dict:
    """
    Agent 4: Title/Abstract Screener
    INPUT:  study_registry with metadata
    OUTPUT: title_abstract_decisions with include/exclude/uncertain per study

    Supports benchmark_mode: when True, auto-includes all studies (Richmond's
    final set is already human-screened — re-screening distorts the benchmark).
    """
    studies = state.get("study_registry", [])
    inclusion_criteria = state.get("inclusion_criteria", "Standard RAMESES criteria for medical education")
    is_benchmark = state.get("benchmark_mode", False)

    if not studies:
        return {"errors": ["No studies in registry to screen."]}

    # ── Benchmark Mode: auto-include all (Richmond's final included set) ──
    if is_benchmark:
        print(f"\n[AGENT 4] Title/Abstract Screener — BENCHMARK MODE")
        print(f"  All {len(studies)} studies auto-included (Richmond's final included set)")
        decisions = [
            {"study_id": s["study_id"], "decision": "include",
             "rationale": "Benchmark mode — study is part of Richmond et al. (2020) final included set",
             "confidence": 1.0}
            for s in studies
        ]
        log = f"[Screening Agent] BENCHMARK MODE: All {len(studies)} studies auto-included"
        return {
            "title_abstract_decisions": decisions,
            "prisma_counts": {"records_screened": len(studies), "title_abstract_excluded": 0},
            "audit_log": [log]
        }

    # ── Production Mode: LLM-based screening ──────────────────────────────
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(ScreeningDecision)
    chain = SCREENING_PROMPT | structured_llm

    decisions = []
    include_count = exclude_count = uncertain_count = 0

    print(f"\n[AGENT 4] Title/Abstract Screener — Processing {len(studies)} studies...")
    print("-" * 60)

    for study in studies:
        try:
            decision = chain.invoke({
                "inclusion_criteria": inclusion_criteria,
                "study_id": study["study_id"],
                "title": study.get("title", "Unknown"),
                "abstract": study.get("abstract", "No abstract available")[:1500]
            })
            decisions.append({
                "study_id": study["study_id"],
                "decision": decision.decision,
                "rationale": decision.rationale,
                "confidence": decision.confidence
            })

            if decision.decision == "include": include_count += 1
            elif decision.decision == "exclude": exclude_count += 1
            else: uncertain_count += 1

            flag = "✓" if decision.decision == "include" else ("?" if decision.decision == "uncertain" else "✗")
            print(f"  {flag} [{study['study_id']}] {decision.decision.upper()} (conf={decision.confidence:.2f})")

        except Exception as e:
            decisions.append({"study_id": study["study_id"], "decision": "uncertain",
                              "rationale": f"Error: {e}", "confidence": 0.0})
            uncertain_count += 1

    print(f"\n  SCREENING RESULT: {include_count} included | {exclude_count} excluded | {uncertain_count} uncertain")

    log = f"[Screening Agent] Title/Abstract: {include_count} include, {exclude_count} exclude, {uncertain_count} uncertain"
    return {
        "title_abstract_decisions": decisions,
        "prisma_counts": {"records_screened": len(studies), "title_abstract_excluded": exclude_count},
        "audit_log": [log]
    }


def full_text_eligibility_node(state: RealistReviewState) -> dict:
    """
    Agent 6: Full-Text Eligibility Agent
    INPUT:  Studies that passed title/abstract screen + their full text
    OUTPUT: Final included_studies list

    Supports benchmark_mode: auto-includes all candidates when True.
    """
    registry = {s["study_id"]: s for s in state.get("study_registry", [])}
    ta_decisions = state.get("title_abstract_decisions", [])
    inclusion_criteria = state.get("inclusion_criteria", "")
    is_benchmark = state.get("benchmark_mode", False)

    candidates = [d for d in ta_decisions if d["decision"] in ("include", "uncertain")]
    print(f"\n[AGENT 6] Full-Text Eligibility — Reviewing {len(candidates)} candidates...")
    print("-" * 60)

    if not candidates:
        return {"included_studies": [], "full_text_decisions": [],
                "audit_log": ["[FullText Agent] No candidates passed title/abstract screen."]}

    # ── Benchmark Mode: auto-include all ──────────────────────────────────
    if is_benchmark:
        print(f"  BENCHMARK MODE: All {len(candidates)} candidates auto-included")
        final_included = [registry.get(d["study_id"], {}) for d in candidates]
        final_included = [s for s in final_included if s]  # filter empty
        full_text_decisions = [
            {"study_id": d["study_id"], "decision": "include",
             "rationale": "Benchmark mode — Richmond's final included set"}
            for d in candidates
        ]
        log = f"[FullText Agent] BENCHMARK MODE: {len(final_included)} studies auto-included"
        return {
            "included_studies": final_included,
            "full_text_decisions": full_text_decisions,
            "prisma_counts": {"full_texts_assessed": len(candidates), "full_text_excluded": 0,
                              "studies_included": len(final_included)},
            "audit_log": [log]
        }

    # ── Production Mode: LLM-based eligibility ────────────────────────────
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(ScreeningDecision)
    chain = FULLTEXT_PROMPT | structured_llm

    final_included = []
    full_text_decisions = []
    ft_excluded = 0

    for item in candidates:
        study = registry.get(item["study_id"], {})
        # In real system, this reads the PDF text; we use abstract as proxy if full text not available
        full_text = study.get("abstract", "Full text not available")[:3000]

        try:
            decision = chain.invoke({
                "inclusion_criteria": inclusion_criteria,
                "study_id": item["study_id"],
                "full_text": full_text
            })
            full_text_decisions.append({
                "study_id": item["study_id"],
                "decision": decision.decision,
                "rationale": decision.rationale
            })

            if decision.decision == "include":
                final_included.append(study)
                print(f"  INCLUDED: [{item['study_id']}]")
            else:
                ft_excluded += 1
                print(f"  EXCLUDED at full-text: [{item['study_id']}] — {decision.rationale[:60]}")
        except Exception as e:
            final_included.append(study)  # conservative: include on error
            print(f"  [ERROR] {item['study_id']}: {e} — conservative include")

    log = f"[FullText Agent] Final included: {len(final_included)}, excluded at full-text: {ft_excluded}"
    return {
        "included_studies": final_included,
        "full_text_decisions": full_text_decisions,
        "prisma_counts": {"full_texts_assessed": len(candidates), "full_text_excluded": ft_excluded,
                          "studies_included": len(final_included)},
        "audit_log": [log]
    }
