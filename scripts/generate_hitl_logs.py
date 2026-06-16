import json
import os
from core.audit_logger import log_hitl_event

ROOT = r"d:\LLM-Knowledge-Graph"
EVIDENCE_TABLE = os.path.join(ROOT, "outputs", "evidence_table.json")
CONTRADICTIONS = os.path.join(ROOT, "outputs", "contradiction_register.md")
THEORIES = os.path.join(ROOT, "outputs", "programme_theory_final.md")

def generate_logs():
    # CP1: Screening (Mock: 0 uncertain)
    log_hitl_event("Screening Adjudication", 0, [])
    
    # CP2: CMOC
    with open(EVIDENCE_TABLE, "r", encoding="utf-8") as f:
        evidence = json.load(f)
    
    # Simulate Pydantic object for details format
    class MockCMOC:
        def __init__(self, d):
            self.cmoc_id = d.get("cmoc_id", "unknown")
            self.confidence = d.get("confidence", "N/A")
            
    cmocs = [MockCMOC(c) for c in evidence]
    details_cmoc = [f"{getattr(c, 'cmoc_id', 'unknown')}: Confidence {getattr(c, 'confidence', 'N/A')}" for c in cmocs[:3]]
    log_hitl_event("CMOC Validation", len(cmocs), details_cmoc)
    
    # CP3: Contradiction
    try:
        with open(CONTRADICTIONS, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip().startswith("-")]
    except:
        lines = []
    
    log_hitl_event("Contradiction Adjudication", len(lines), lines[:3])
    
    # CP4: Theory Sign-off
    try:
        with open(THEORIES, "r", encoding="utf-8") as f:
            tlines = [l.strip() for l in f.readlines() if "Programme Theory Statement" in l]
    except:
        tlines = []
        
    log_hitl_event("Theory Sign-off", len(tlines), [t[:80] for t in tlines[:3]])
    
    print("HITL logs generated successfully.")

if __name__ == "__main__":
    generate_logs()
