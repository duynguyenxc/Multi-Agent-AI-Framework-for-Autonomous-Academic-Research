"""
core/agents/deduplication_agent.py — Agent 3: Deduplication + Study Registry
==============================================================================
Richmond Alignment: Technical Assistant
Role: Merges duplicate records from multiple databases, assigns stable StudyIDs,
and maintains the Single Source of Truth study registry.

Human Reference: Richmond searched 4 databases (MEDLINE, PsycINFO, ERIC, CINAHL)
and had to deduplicate results before screening could begin.
"""
import os
import json
import hashlib
from core.state import StudyRecord


def build_study_registry_from_input(input_dir: str, metadata_file: str) -> dict:
    """
    Agent 3: Deduplication & Study Registry Builder
    INPUT:  ingested paper text files + metadata JSONL
    OUTPUT: deduplicated study registry with stable StudyIDs + PRISMA count
    """
    print("\n[AGENT 3] Deduplication Agent — Building Study Registry...")
    print("-" * 60)

    registry: list[StudyRecord] = []
    seen_dois = {}
    seen_titles = {}
    study_counter = 1

    # Load metadata
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    source = record.get("source_id", "")
                    doi = (record.get("doi") or "").lower().strip()
                    title = (record.get("title") or "").lower().strip()[:80]

                    # Deduplication: by DOI first, then by title prefix
                    dup_key = doi if doi else title
                    if dup_key and dup_key in seen_dois:
                        print(f"  [DEDUP] Skipped duplicate: {record.get('title', '')[:50]}")
                        continue

                    seen_dois[dup_key] = True

                    # Read abstract from text file if available
                    txt_path = os.path.join(input_dir, source + ".txt")
                    # Fallback: if source_id is a PubMed URL, look for pubmed_PMID.txt
                    if not os.path.exists(txt_path) and "pubmed.ncbi.nlm.nih.gov" in source:
                        pmid = source.rstrip("/").split("/")[-1]
                        txt_path = os.path.join(input_dir, f"pubmed_{pmid}.txt")

                    abstract = record.get("abstract", "") or "No abstract extracted"
                    if os.path.exists(txt_path):
                        with open(txt_path, "r", encoding="utf-8", errors="replace") as tf:
                            content = tf.read(2000)
                            if "CONTENT:" in content:
                                abstract = content.split("CONTENT:")[-1][:1800].strip()
                            else:
                                abstract = content[:1800].strip()

                    study_id = f"S{study_counter:03d}"
                    study_counter += 1

                    entry: StudyRecord = {
                        "study_id": study_id,
                        "title": record.get("title", "Unknown"),
                        "authors": ", ".join(record.get("authors", [])),
                        "year": str(record.get("year", "")),
                        "doi": record.get("doi", ""),
                        "source_file": txt_path if os.path.exists(txt_path) else source,
                        "abstract": abstract,
                        "screening_decision": "pending",
                        "screening_rationale": "",
                        "full_text_decision": "pending",
                        "full_text_rationale": ""
                    }
                    registry.append(entry)
                    safe_title = record.get('title', '')[:55].encode('ascii', 'replace').decode('ascii')
                    print(f"  [REGISTERED] {study_id}: {safe_title}...")

                except json.JSONDecodeError:
                    continue
    else:
        # Fallback: build registry from txt files directly
        for fname in sorted(os.listdir(input_dir)):
            if not fname.endswith(".txt"):
                continue
            txt_path = os.path.join(input_dir, fname)
            with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(2000)

            title_line = "Unknown"
            for line in content.splitlines():
                if line.startswith("TITLE:"):
                    title_line = line.replace("TITLE:", "").strip()
                    break

            study_id = f"S{study_counter:03d}"
            study_counter += 1

            registry.append({
                "study_id": study_id,
                "title": title_line,
                "authors": "",
                "year": "",
                "doi": "",
                "source_file": txt_path,
                "abstract": content[:600],
                "screening_decision": "pending",
                "screening_rationale": "",
                "full_text_decision": "pending",
                "full_text_rationale": ""
            })
            print(f"  [REGISTERED] {study_id}: {title_line[:55]}...")

    print(f"\n  REGISTRY BUILT: {len(registry)} unique studies")
    log = f"[Dedup Agent] Registry built: {len(registry)} unique studies from {input_dir}"

    return {
        "study_registry": registry,
        "prisma_counts": {"records_identified": len(registry)},
        "audit_log": [log]
    }
