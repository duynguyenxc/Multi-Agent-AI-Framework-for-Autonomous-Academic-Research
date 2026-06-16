import json
import os
from datetime import datetime

ROOT = r"d:\LLM-Knowledge-Graph"
OUT_MD = os.path.join(ROOT, "outputs", "HITL_Audit_Log.md")
OUT_JSONL = os.path.join(ROOT, "outputs", "hitl_audit_log.jsonl")

HITL_MODE = os.environ.get("HITL_MODE", "demo")

def init_log():
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    if not os.path.exists(OUT_MD):
        with open(OUT_MD, "w", encoding="utf-8") as f:
            f.write(f"# HITL Audit Log\n\nStarted: {datetime.now().isoformat()}\n\n")
    if not os.path.exists(OUT_JSONL):
        open(OUT_JSONL, "w", encoding="utf-8").close()

def log_hitl_event(checkpoint_name, pending_items_count, details=None):
    init_log()
    
    status = "auto_pass_demo" if HITL_MODE == "demo" else "pending_human_review"
    timestamp = datetime.now().isoformat()
    
    event = {
        "timestamp": timestamp,
        "checkpoint": checkpoint_name,
        "status": status,
        "items_count": pending_items_count,
        "details": details or []
    }
    
    with open(OUT_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
        
    md_entry = f"## [{timestamp}] Checkpoint: {checkpoint_name}\n"
    md_entry += f"- **Status:** `{status}`\n"
    md_entry += f"- **Items to Review:** {pending_items_count}\n"
    if details:
        md_entry += "- **Samples:**\n"
        for d in details[:3]:
            md_entry += f"  - {d}\n"
    md_entry += "- [ ] HUMAN APPROVED\n\n"
    
    with open(OUT_MD, "a", encoding="utf-8") as f:
        f.write(md_entry)
        
    return status
