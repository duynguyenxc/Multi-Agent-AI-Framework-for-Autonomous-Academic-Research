"""
main.py — Full 10-Agent Pipeline Runner (v3 — Full-Scale)
==========================================================
Runs the complete Multi-Agent Realist Synthesis Framework aligned with
the Richmond et al. (2020) Human Reference Standard.

v3 Changes:
  - BENCHMARK_MODE: auto-includes all 28 papers (Richmond's final set)
  - CMOC extraction loops all included studies (not just 1)
  - GraphRAG Leiden communities loaded from parquet
  - Duration tracking for pipeline execution

Pipeline:
  Phase 0: Protocol & IPT
  Phase 1: Study Registry Build (Deduplication)
  Phase 2: Two-Stage Screening (T/A + Full Text) with HITL CP1
  Phase 3: CMOC Extraction Loop (ALL included studies) with HITL CP2
  Phase 4: Contradiction Detection with HITL CP3
  Phase 5: Theory Synthesis with HITL CP4
  Phase 6: Reporting & Audit Artifacts
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

from core.orchestrator import orchestrator_app
from core.state import RealistReviewState
from core.agents.deduplication_agent import build_study_registry_from_input
from core.agents.protocol_agent import run_protocol_agent

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
INPUT_DIR     = r"d:\LLM-Knowledge-Graph\graphrag\input"
METADATA_FILE = r"d:\LLM-Knowledge-Graph\data\studies_metadata.jsonl"
OUTPUT_DIR    = r"d:\LLM-Knowledge-Graph\outputs"
GRAPHRAG_DIR  = r"d:\LLM-Knowledge-Graph\outputs\graphrag_data"

# Set True for Richmond benchmark (auto-includes all 28 papers, skips screening)
# Set False for production mode (LLM-based screening applied)
BENCHMARK_MODE = True

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Review Question (researcher-defined) ──────────────────────────────────────
REVIEW_QUESTION = """
How do educational interventions develop clinical reasoning ability 
(analytical and non-analytical) in undergraduate medical and healthcare students?
"""


def load_leiden_communities() -> list:
    """
    Loads GraphRAG Leiden community reports from parquet.
    Returns a list of dicts with community title, summary, and rank.
    Gracefully returns empty list if pandas/parquet not available.
    """
    parquet_path = os.path.join(GRAPHRAG_DIR, "community_reports.parquet")
    if not os.path.exists(parquet_path):
        print("  [WARN] community_reports.parquet not found — communities will be empty")
        return []

    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)

        # Extract relevant columns for synthesis
        communities = []
        for _, row in df.iterrows():
            communities.append({
                "title": row.get("title", ""),
                "summary": str(row.get("summary", ""))[:500],  # cap to reduce token usage
                "rank": row.get("rank", 0),
                "community_id": str(row.get("community", row.get("id", "")))
            })

        # Sort by rank descending (most important first)
        communities.sort(key=lambda x: x.get("rank", 0), reverse=True)
        print(f"  Loaded {len(communities)} Leiden communities from GraphRAG")
        return communities

    except ImportError:
        print("  [WARN] pandas not installed — cannot load community reports")
        return []
    except Exception as e:
        print(f"  [WARN] Failed to load communities: {e}")
        return []


def run_full_pipeline():
    pipeline_start = time.time()

    print("=" * 70)
    print("  MULTI-AGENT REALIST SYNTHESIS FRAMEWORK v3.0 (FULL-SCALE)")
    print("  10-Agent Pipeline | Richmond et al. (2020) Benchmark")
    print("=" * 70)
    print(f"  Timestamp:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Benchmark Mode: {'ON — all studies auto-included' if BENCHMARK_MODE else 'OFF — LLM screening active'}")
    print(f"  Review Question: {REVIEW_QUESTION.strip()}")
    print("=" * 70)

    # ── PHASE 0: Protocol & IPT ───────────────────────────────────────────────
    print("\n[PHASE 0] Generating Initial Programme Theory...")
    protocol_state = run_protocol_agent(REVIEW_QUESTION)
    ipt = protocol_state["ipt_hypothesis"]
    criteria = protocol_state["inclusion_criteria"]

    # ── PHASE 1: Build Study Registry ─────────────────────────────────────────
    print("\n[PHASE 1] Building Study Registry from ingested papers...")
    registry_state = build_study_registry_from_input(INPUT_DIR, METADATA_FILE)
    study_registry = registry_state["study_registry"]
    print(f"  Registry: {len(study_registry)} unique studies")

    # ── Load GraphRAG Leiden Communities ──────────────────────────────────────
    print("\n[PHASE 1.5] Loading GraphRAG community data...")
    leiden_communities = load_leiden_communities()

    # ── Initialize Full LangGraph State ──────────────────────────────────────
    # Note: current_record_id and current_paper_text are set by prepare_next_study
    # node in the orchestrator loop — no need to pre-load a single paper here.
    initial_state: RealistReviewState = {
        # Phase 0
        "ipt_hypothesis": ipt,
        "inclusion_criteria": criteria,
        "review_question": REVIEW_QUESTION.strip(),
        # Phase 1
        "raw_candidate_pool": [],
        "study_registry": study_registry,
        # Phase 2 (populated by screening agents)
        "title_abstract_decisions": [],
        "full_text_decisions": [],
        "included_studies": [],
        # Phase 3 CMOC (populated by prepare_next_study loop)
        "current_record_id": "",
        "current_paper_text": "",
        "extracted_cmocs": [],
        # HITL
        "validation_status": "pending",
        "human_feedback": "",
        "hitl_checkpoint": "none",
        # Synthesis
        "leiden_communities": leiden_communities,
        "contradictions_found": [],
        "demi_regularities": [],
        "draft_programme_theory": "",
        "programme_theory_version": 1,
        # Reporting
        "prisma_counts": registry_state.get("prisma_counts", {}),
        "evidence_table": [],
        "audit_log": protocol_state.get("audit_log", []) + registry_state.get("audit_log", []),
        # Meta
        "errors": [],
        "iteration_count": 0,
        "benchmark_mode": BENCHMARK_MODE
    }

    # ── PHASES 2-6: Run LangGraph Pipeline ───────────────────────────────────
    print("\n[PHASES 2-6] Executing LangGraph Multi-Agent Pipeline...")
    print("-" * 70)

    final_state = orchestrator_app.invoke(
        initial_state,
        config={"recursion_limit": 100}  # 28 studies × 3 nodes/loop = 84 steps
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    duration = time.time() - pipeline_start
    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Duration:              {duration:.1f}s ({duration/60:.1f} min)")
    print(f"  Benchmark Mode:        {'ON' if BENCHMARK_MODE else 'OFF'}")
    print(f"  Studies in registry:   {len(final_state.get('study_registry', []))}")
    print(f"  Studies included:      {len(final_state.get('included_studies', []))}")
    print(f"  CMOCs extracted:       {len(final_state.get('extracted_cmocs', []))}")
    print(f"  Contradictions:        {len(final_state.get('contradictions_found', []))}")
    print(f"  Demi-regularities:     {len(final_state.get('demi_regularities', []))}")
    print(f"  Leiden communities:    {len(final_state.get('leiden_communities', []))}")
    print(f"  Audit log entries:     {len(final_state.get('audit_log', []))}")
    print(f"  Errors:                {len(final_state.get('errors', []))}")
    print(f"  HITL checkpoints:      4 (Screening / CMOC / Contradiction / Theory)")
    print(f"  Output directory:      {OUTPUT_DIR}")
    print("=" * 70)
    print("\n  Output files:")
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        fpath = os.path.join(OUTPUT_DIR, fname)
        if os.path.isfile(fpath):
            fsize = os.path.getsize(fpath)
            print(f"    {fname:<40} ({fsize:,} bytes)")

    # Log any errors
    errors = final_state.get("errors", [])
    if errors:
        print(f"\n  [!] ERRORS ({len(errors)}):")
        for err in errors[:5]:
            print(f"    - {err[:100]}")


if __name__ == "__main__":
    run_full_pipeline()
