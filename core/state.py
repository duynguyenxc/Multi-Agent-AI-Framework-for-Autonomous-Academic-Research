"""
core/state.py — Complete Shared State for the Full 10-Agent Pipeline
=====================================================================
Tracks the entire lifecycle of a systematic review, from Protocol IPT
seeding through to Final Programme Theory sign-off.
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from .ontology import CMOCExtraction


def merge_list(a: List[Any], b: List[Any]) -> List[Any]:
    if not a: return b
    if not b: return a
    return a + b


class StudyRecord(TypedDict):
    """Represents a single study in the Study Registry."""
    study_id: str           # e.g. "S001"
    title: str
    authors: str
    year: str
    doi: str
    source_file: str        # path to PDF or txt
    abstract: str
    screening_decision: str # "include" | "exclude" | "uncertain"
    screening_rationale: str
    full_text_decision: str # "include" | "exclude"
    full_text_rationale: str


class RealistReviewState(TypedDict):
    """
    LangGraph Complete State Machine — Full 10-Agent Realist Review Pipeline.
    Aligns with the Richmond et al. (2020) Human Reference Standard.
    """
    # ── Phase 0: Protocol / IPT ─────────────────────────────────────────────
    ipt_hypothesis: str                      # Initial Programme Theory
    inclusion_criteria: str                  # Researcher-defined criteria
    review_question: str                     # RQ driving the review

    # ── Phase 1: Search & Registry ──────────────────────────────────────────
    raw_candidate_pool: Annotated[List[Dict[str, Any]], merge_list]  # raw harvest
    study_registry: List[StudyRecord]        # deduplicated, stable StudyIDs

    # ── Phase 2: Two-Stage Screening ────────────────────────────────────────
    title_abstract_decisions: List[Dict[str, str]]  # per-study decisions
    full_text_decisions: List[Dict[str, str]]
    included_studies: List[StudyRecord]      # final included set

    # ── Phase 3: CMOC Extraction (Realist Plugin) ───────────────────────────
    current_record_id: str
    current_paper_text: str
    extracted_cmocs: Annotated[List[CMOCExtraction], merge_list]

    # ── Phase 4: HITL Checkpoints ───────────────────────────────────────────
    validation_status: str   # "pending" | "approved" | "rejected"
    human_feedback: str
    hitl_checkpoint: str     # which checkpoint we are at

    # ── Phase 5: Synthesis ──────────────────────────────────────────────────
    leiden_communities: List[Dict[str, Any]]  # GraphRAG output
    contradictions_found: Annotated[List[str], merge_list]
    demi_regularities: List[str]              # recurrent patterns
    draft_programme_theory: str
    programme_theory_version: int             # track refinement iterations

    # ── Phase 6: Reporting ──────────────────────────────────────────────────
    prisma_counts: Dict[str, int]             # PRISMA flow numbers
    evidence_table: List[Dict[str, str]]      # structured evidence table
    audit_log: Annotated[List[str], merge_list]  # every decision logged

    # ── Meta ────────────────────────────────────────────────────────────────
    errors: Annotated[List[str], merge_list]
    iteration_count: int
    benchmark_mode: bool                     # True = Richmond benchmark (skip screening)
