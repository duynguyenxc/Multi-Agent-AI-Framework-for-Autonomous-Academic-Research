"""
core/orchestrator.py — Full 10-Agent LangGraph State Machine
=============================================================
Implements the complete pipeline aligned with Richmond et al. (2020):

  [1] Protocol & IPT Agent       →  Lead Theorist
  [2] Build Study Registry       →  Librarian / Deduplication
  [3] Title/Abstract Screener    →  Primary Reviewer
  [4] HITL: Screening Review     →  Human Checkpoint 1
  [5] Full-Text Eligibility      →  Secondary Reviewer
  [6] CMOC Extraction (LOOP)     →  Subject Matter Expert (iterates all studies)
  [7] HITL: CMOC Validation      →  Human Checkpoint 2
  [8] Contradiction Detection    →  Quality Auditor
  [9] HITL: Contradiction        →  Human Checkpoint 3
  [10] Theory Synthesis          →  Synthesis Expert
  [11] HITL: Theory Sign-off     →  Human Checkpoint 4
  [12] Reporting & Artifacts     →  Technical Writer
"""
import os
from langgraph.graph import StateGraph, END
from core.state import RealistReviewState
from plugins.realist_synthesis.cmoc_extractor import extract_cmoc_node
from plugins.realist_synthesis.contradiction_agent import detect_contradictions_node
from plugins.realist_synthesis.cross_study_synthesizer import synthesis_node
from core.agents.screening_agent import (
    screen_title_abstract_node,
    full_text_eligibility_node
)
from core.agents.reporting_agent import generate_reporting_node
from core.audit_logger import log_hitl_event


# ── HITL Master Control Nodes ─────────────────────────────────────────────────

def hitl_screening_node(state: RealistReviewState) -> dict:
    """
    HITL Checkpoint 1: Researcher reviews screening decisions.
    In production: pauses for GUI input. Here: simulates auto-approve + log.
    """
    decisions = state.get("title_abstract_decisions", [])
    uncertain = [d for d in decisions if d["decision"] == "uncertain"]

    details = [f"{u['study_id']}: {u['rationale'][:70]}" for u in uncertain[:3]]
    status = log_hitl_event("Screening Adjudication", len(uncertain), details)

    return {
        "hitl_checkpoint": status,
        "validation_status": "screening_complete",
        "audit_log": [f"[HITL CP-1] Screening checkpoint: {status}"]
    }


def hitl_cmoc_validation_node(state: RealistReviewState) -> dict:
    """
    HITL Checkpoint 2: Researcher spot-checks CMOC extractions against ground truth.
    Pauses if extractions seem too generic or outside E01-E47.
    """
    cmocs = state.get("extracted_cmocs", [])
    
    details = [f"{getattr(c, 'cmoc_id', 'unknown')}: Confidence {getattr(c, 'confidence', 'N/A')}" for c in cmocs[:3]]
    status = log_hitl_event("CMOC Validation", len(cmocs), details)

    return {
        "hitl_checkpoint": status,
        "validation_status": "approved" if status == "auto_pass_demo" else "pending",
        "audit_log": [f"[HITL CP-2] CMOC validation checkpoint: {status}"]
    }


def hitl_contradiction_node(state: RealistReviewState) -> dict:
    """
    HITL Checkpoint 3: Contradiction Adjudication.
    Presents the Conflict Register to the researcher for interpretive resolution.
    """
    contradictions = state.get("contradictions_found", [])
    
    details = [str(c)[:80] for c in contradictions[:3]]
    status = log_hitl_event("Contradiction Adjudication", len(contradictions), details)

    return {
        "hitl_checkpoint": status,
        "audit_log": [f"[HITL CP-3] Contradiction checkpoint: {status}"]
    }


def hitl_theory_signoff_node(state: RealistReviewState) -> dict:
    """
    HITL Checkpoint 4: Final Theory Sign-off.
    Researcher approves the complete Programme Theory before artifact generation.
    """
    theory = state.get("draft_programme_theory", "")
    print(f"\n[HITL CP-4] Theory Sign-off Checkpoint")
    theories = state.get("synthesis_theories", [])
    
    details = [str(t)[:80] for t in theories[:3]]
    status = log_hitl_event("Theory Sign-off", len(theories), details)

    return {
        "hitl_checkpoint": status,
        "validation_status": "theory_approved",
        "audit_log": [f"[HITL CP-4] Theory sign-off: {status}"]
    }


# ── CMOC Loop Nodes ──────────────────────────────────────────────────────────

def prepare_next_study(state: RealistReviewState) -> dict:
    """
    Bridge node: loads the next unprocessed study's text for CMOC extraction.
    Iterates through included_studies, skipping any already extracted.
    Uses study_id (e.g. 'S001') as the canonical tracking key for consistency.
    """
    included = state.get("included_studies", [])
    extracted = state.get("extracted_cmocs", [])

    # Build set of already-processed study IDs (using canonical record_id)
    extracted_ids = set()
    for cmoc in extracted:
        if cmoc and hasattr(cmoc, "record_id"):
            extracted_ids.add(cmoc.record_id)

    # Find next unprocessed study (match by study_id)
    input_dir = os.path.dirname(included[0].get("source_file", "")) if included else ""
    for study in included:
        study_id = study.get("study_id", "")
        if study_id not in extracted_ids:
            source_file = study.get("source_file", "")

            # Fallback: if source_file is a PubMed URL, look for local pubmed_PMID.txt
            if not os.path.exists(source_file) and "pubmed.ncbi.nlm.nih.gov" in source_file:
                pmid = source_file.rstrip("/").split("/")[-1]
                candidate = os.path.join(input_dir, f"pubmed_{pmid}.txt")
                if os.path.exists(candidate):
                    source_file = candidate

            try:
                with open(source_file, "r", encoding="utf-8", errors="replace") as f:
                    full_text = f.read()
                # Smart truncation: keep intro (first 10K) + results/discussion (last 10K)
                if len(full_text) > 20000:
                    text = full_text[:10000] + "\n\n[...]\n\n" + full_text[-10000:]
                else:
                    text = full_text
            except (FileNotFoundError, OSError):
                text = study.get("abstract", "No text available")

            remaining = len(included) - len(extracted_ids) - 1
            print(f"\n[CMOC LOOP] Preparing: {study_id} ({remaining} remaining after this)")
            return {
                "current_record_id": study_id,
                "current_paper_text": text
            }

    # All studies processed
    print(f"\n[CMOC LOOP] All {len(included)} studies processed.")
    return {
        "current_record_id": "",
        "current_paper_text": ""
    }


def cmoc_router(state: RealistReviewState) -> str:
    """
    Conditional edge after CMOC extraction: decides whether to loop back
    for the next study or proceed to HITL validation.
    Uses study_id as canonical tracking key (matches prepare_next_study).
    """
    included = state.get("included_studies", [])
    extracted = state.get("extracted_cmocs", [])

    extracted_ids = set()
    for cmoc in extracted:
        if cmoc and hasattr(cmoc, "record_id"):
            extracted_ids.add(cmoc.record_id)

    # Check if any included study still needs extraction (by study_id)
    for study in included:
        study_id = study.get("study_id", "")
        if study_id not in extracted_ids:
            return "prepare_next_study"

    return "hitl_cmoc_validation"


# ── Build the LangGraph State Machine ────────────────────────────────────────

workflow = StateGraph(RealistReviewState)

# Add all agent nodes
workflow.add_node("screen_title_abstract", screen_title_abstract_node)
workflow.add_node("hitl_screening", hitl_screening_node)
workflow.add_node("full_text_eligibility", full_text_eligibility_node)
workflow.add_node("prepare_next_study", prepare_next_study)
workflow.add_node("extract_cmoc", extract_cmoc_node)
workflow.add_node("hitl_cmoc_validation", hitl_cmoc_validation_node)
workflow.add_node("check_contradictions", detect_contradictions_node)
workflow.add_node("hitl_contradiction", hitl_contradiction_node)
workflow.add_node("synthesis_theory", synthesis_node)
workflow.add_node("hitl_theory_signoff", hitl_theory_signoff_node)
workflow.add_node("generate_report", generate_reporting_node)

# Wire the pipeline (linear flow with CMOC loop)
workflow.set_entry_point("screen_title_abstract")
workflow.add_edge("screen_title_abstract", "hitl_screening")
workflow.add_edge("hitl_screening", "full_text_eligibility")
workflow.add_edge("full_text_eligibility", "prepare_next_study")
workflow.add_edge("prepare_next_study", "extract_cmoc")
workflow.add_conditional_edges("extract_cmoc", cmoc_router,
                               {"prepare_next_study": "prepare_next_study",
                                "hitl_cmoc_validation": "hitl_cmoc_validation"})
workflow.add_edge("hitl_cmoc_validation", "check_contradictions")
workflow.add_edge("check_contradictions", "hitl_contradiction")
workflow.add_edge("hitl_contradiction", "synthesis_theory")
workflow.add_edge("synthesis_theory", "hitl_theory_signoff")
workflow.add_edge("hitl_theory_signoff", "generate_report")
workflow.add_edge("generate_report", END)

# Compile
orchestrator_app = workflow.compile()
# Note: recursion_limit is set at invocation time in main.py, not here.
