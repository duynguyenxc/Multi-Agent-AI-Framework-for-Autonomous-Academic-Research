import json
import os
import csv

ROOT = r"d:\LLM-Knowledge-Graph"
EVIDENCE_TABLE = os.path.join(ROOT, "outputs", "evidence_table.json")
REL_TRIPLES = os.path.join(ROOT, "outputs", "relationships_triples.json")
GRAPHRAG_INPUT = os.path.join(ROOT, "graphrag", "input")
OUT_CSV = os.path.join(ROOT, "outputs", "per_paper_adjudication_template.csv")

def build_study_mapping():
    metadata_file = os.path.join(ROOT, "data", "studies_metadata.jsonl")
    mapping = {}
    if not os.path.exists(metadata_file):
        return mapping
        
    seen_dois = {}
    study_counter = 1
    with open(metadata_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            record = json.loads(line)
            doi = (record.get("doi") or "").lower().strip()
            title = (record.get("title") or "").lower().strip()[:80]
            dup_key = doi if doi else title
            if dup_key and dup_key in seen_dois: continue
            seen_dois[dup_key] = True
            
            sid = f"S{study_counter:03d}"
            source = record.get("source_id", "")
            url = record.get("url", "") or ""
            if "pubmed" in source or "pubmed" in url:
                mapping[sid] = "Abstract Only"
            else:
                mapping[sid] = "Full-text"
            study_counter += 1
    return mapping

def create_template():
    mapping = build_study_mapping()
    with open(EVIDENCE_TABLE, "r", encoding="utf-8") as f:
        evidence = json.load(f)
        
    try:
        with open(REL_TRIPLES, "r", encoding="utf-8") as f:
            rels = json.load(f)
    except Exception:
        rels = []

    # group rels by cmoc_id
    rels_by_cmoc = {}
    for r in rels:
        cid = r["cmoc_id"]
        if cid not in rels_by_cmoc:
            rels_by_cmoc[cid] = []
        rels_by_cmoc[cid].append(f"{r['source_e_code']}-[{r['predicate']}]->{r['target_e_code']}")

    headers = [
        "study_id", "cmoc_id", "evidence_level", "model_pts", "model_polarity",
        "model_context_code", "model_context_text",
        "model_intervention_code", "model_intervention_text",
        "model_mechanism_code", "model_mechanism_text",
        "model_outcome_code", "model_outcome_text",
        "model_relationship_triples",
        "evidence_quote",
        "human_corrected_context", "human_corrected_intervention", "human_corrected_mechanism", "human_corrected_outcome",
        "human_corrected_triples", "human_corrected_pts",
        "decision_status", "error_category", "reviewer_notes"
    ]

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for cmoc in evidence:
            cid = cmoc["cmoc_id"]
            triples_str = "; ".join(rels_by_cmoc.get(cid, []))
            
            row = {
                "study_id": cmoc.get("study_id", ""),
                "cmoc_id": cid,
                "evidence_level": mapping.get(cmoc.get("study_id", ""), "Unknown"),
                "model_pts": cmoc.get("pts", ""),
                "model_polarity": "Negative" if cmoc.get("is_negative") else "Positive",
                "model_context_code": cmoc.get("context_code", ""),
                "model_context_text": cmoc.get("context", ""),
                "model_intervention_code": cmoc.get("intervention_code", ""),
                "model_intervention_text": cmoc.get("intervention", ""),
                "model_mechanism_code": cmoc.get("mechanism_response_code", ""),
                "model_mechanism_text": cmoc.get("mechanism_response", ""),
                "model_outcome_code": cmoc.get("outcome_code", ""),
                "model_outcome_text": cmoc.get("outcome", ""),
                "model_relationship_triples": triples_str,
                "evidence_quote": cmoc.get("context_evidence", "")[:200] + "...",  # Preview
                "human_corrected_context": "",
                "human_corrected_intervention": "",
                "human_corrected_mechanism": "",
                "human_corrected_outcome": "",
                "human_corrected_triples": "",
                "human_corrected_pts": "",
                "decision_status": "PENDING",
                "error_category": "",
                "reviewer_notes": ""
            }
            writer.writerow(row)
            
    print(f"Generated {OUT_CSV}")

if __name__ == "__main__":
    create_template()
