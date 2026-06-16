import json
import os
from datetime import datetime

ROOT = r"d:\LLM-Knowledge-Graph"
OUT_JSON = os.path.join(ROOT, "outputs", "verification_manifest.json")
OUT_MD = os.path.join(ROOT, "outputs", "verification_manifest.md")

def generate_manifest():
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "source_of_truth": {
            "official_cmoc_file": "outputs/evidence_table.json",
            "official_relationship_file": "outputs/relationships_triples.json",
            "gold_file": "data/gold_standard.json"
        },
        "current_run_stats": {
            "total_studies": 28,
            "total_cmocs": 57,
            "raw_relationships": 171
        },
        "notes": [
            "This manifest defines the canonical input and output files used for KG evaluation.",
            "Relationships are explicitly split into instance_level_triples (all 171) and unique_programme_level_triples for deduplicated evaluation."
        ]
    }
    
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    md_content = f"""# KG Verification Manifest
Generated: {manifest["generated_at"]}

## Source of Truth Files
- **Official CMOCs:** `{manifest["source_of_truth"]["official_cmoc_file"]}`
- **Official Relationships:** `{manifest["source_of_truth"]["official_relationship_file"]}`
- **Gold Standard:** `{manifest["source_of_truth"]["gold_file"]}`

## Current Run Stats
- **Total Studies:** {manifest["current_run_stats"]["total_studies"]}
- **Total CMOCs:** {manifest["current_run_stats"]["total_cmocs"]}
- **Raw Relationships:** {manifest["current_run_stats"]["raw_relationships"]}

## Notes
{chr(10).join(f'- {n}' for n in manifest["notes"])}
"""
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

if __name__ == "__main__":
    generate_manifest()
    print(f"Generated {OUT_JSON} and {OUT_MD}")
