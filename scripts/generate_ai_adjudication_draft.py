import csv
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher


ROOT = r"d:\LLM-Knowledge-Graph"
METADATA_PATH = os.path.join(ROOT, "data", "studies_metadata.jsonl")
EVIDENCE_PATH = os.path.join(ROOT, "outputs", "evidence_table.json")
TRIPLES_PATH = os.path.join(ROOT, "outputs", "relationships_triples.json")
GOLD_PATH = os.path.join(ROOT, "data", "gold_standard.json")
INPUT_DIR = os.path.join(ROOT, "graphrag", "input")
OUT_DIR = os.path.join(ROOT, "outputs", "adjudication")
OUT_CSV = os.path.join(OUT_DIR, "per_paper_adjudication_ai_draft.csv")
OUT_JSON = os.path.join(OUT_DIR, "per_paper_adjudication_ai_draft.json")
OUT_MD = os.path.join(OUT_DIR, "AI_Adjudication_Draft_Summary.md")

STRICT_PREDICATES = {"PROVIDES", "ENABLES", "TRIGGERS", "LEADS_TO", "CONSTRAINS"}
PREDICATE_ALIASES = {"INHIBITS": "CONSTRAINS"}
NEGATIVE_MECHANISMS = {"E23", "E32", "E33", "E34", "E35", "E45"}
NEGATIVE_OUTCOMES = {"E36", "E37", "E38", "E47"}
CONTEXT_TO_PTS = {
    "E02": "PTS1",
    "E03": "PTS2",
    "E04": "PTS3",
    "E05": "PTS4",
    "E06": "PTS5",
}


def norm_text(text):
    text = text or ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def safe_read(path):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    return ""


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_metadata():
    rows = []
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            record = json.loads(line)
            study_id = f"S{i:03d}"
            source_id = record.get("source_id") or ""
            if record.get("source") == "url" and "pubmed.ncbi.nlm.nih.gov" in source_id:
                pmid = source_id.rstrip("/").split("/")[-1]
                text_path = os.path.join(INPUT_DIR, f"pubmed_{pmid}.txt")
                evidence_level = "Abstract Only"
            else:
                text_path = os.path.join(INPUT_DIR, source_id + ".txt")
                evidence_level = "Full-text"
            text_len = os.path.getsize(text_path) if os.path.exists(text_path) else 0
            if evidence_level == "Full-text" and text_len and text_len < 5000:
                evidence_level = "Partial Full-text"
            rows.append({
                "study_id": study_id,
                "source": record.get("source", ""),
                "source_id": source_id,
                "source_text_path": text_path,
                "text_length": text_len,
                "evidence_level": evidence_level,
                "title": record.get("title", ""),
                "authors": "; ".join(record.get("authors") or []),
                "year": record.get("year") or "",
                "doi": record.get("doi") or "",
                "abstract": record.get("abstract") or "",
                "text": safe_read(text_path),
            })
    return {r["study_id"]: r for r in rows}


def quote_support(quote, source_text):
    quote_norm = norm_text(quote)
    source_norm = norm_text(source_text)
    if not quote_norm:
        return {"status": "missing_quote", "score": 0.0}
    if quote_norm in source_norm:
        return {"status": "exact", "score": 1.0}
    words = quote_norm.split()
    if len(words) >= 8:
        for i in range(0, max(1, len(words) - 7)):
            fragment = " ".join(words[i:i + 8])
            if fragment in source_norm:
                return {"status": "partial_8_word", "score": 0.75}
    if not source_norm:
        return {"status": "source_text_missing", "score": 0.0}
    # Compact approximate score against local windows. This avoids overclaiming
    # when PDF extraction changed punctuation or line breaks.
    best = 0.0
    q_len = len(quote_norm)
    for start in range(0, max(1, len(source_norm) - q_len), max(100, q_len // 2)):
        window = source_norm[start:start + q_len + 200]
        best = max(best, SequenceMatcher(None, quote_norm, window).ratio())
        if best >= 0.68:
            break
    status = "approximate" if best >= 0.58 else "not_found"
    return {"status": status, "score": round(best, 3)}


def normalize_predicate(predicate):
    return PREDICATE_ALIASES.get(predicate, predicate)


def format_triples(triples):
    return "; ".join(
        f"{t['source_e_code']}-[{normalize_predicate(t['predicate'])}]->{t['target_e_code']}"
        for t in triples
    )


def chain_issues(cmoc, pts_meta):
    pts = cmoc.get("pts", "")
    meta = pts_meta.get(pts)
    if not meta:
        return [f"unknown_pts:{pts}"]
    issues = []
    checks = [
        ("context", cmoc.get("context_code"), {meta["context_code"]}),
        ("intervention", cmoc.get("intervention_code"), set(meta["expected_interventions"])),
        ("mechanism", cmoc.get("mechanism_response_code"), set(meta["expected_mechanism_responses"])),
        ("outcome", cmoc.get("outcome_code"), set(meta["expected_outcomes"])),
    ]
    for label, actual, expected in checks:
        if actual not in expected:
            issues.append(f"{label}:{actual}_not_in_{'/'.join(sorted(expected))}")
    return issues


def adjudicate_row(cmoc, triples, metadata, gold):
    study = metadata[cmoc["study_id"]]
    source_text = study["text"]
    evidence_checks = {
        "context": quote_support(cmoc.get("context_evidence"), source_text),
        "intervention": quote_support(cmoc.get("intervention_evidence"), source_text),
        "mechanism": quote_support(cmoc.get("mechanism_response_evidence"), source_text),
        "outcome": quote_support(cmoc.get("outcome_evidence"), source_text),
    }
    supported_count = sum(1 for v in evidence_checks.values() if v["score"] >= 0.58)
    evidence_score = round(sum(v["score"] for v in evidence_checks.values()) / 4, 3)

    pts_meta = gold["programme_theory_statements"]
    issues = chain_issues(cmoc, pts_meta)
    predicates = [t["predicate"] for t in triples]
    alias_used = any(p in PREDICATE_ALIASES for p in predicates)
    invalid_predicates = [
        p for p in predicates
        if normalize_predicate(p) not in STRICT_PREDICATES
    ]

    expected_pts_from_context = CONTEXT_TO_PTS.get(cmoc.get("context_code"), cmoc.get("pts", ""))
    polarity_should_be_negative = (
        cmoc.get("context_code") == "E05"
        or cmoc.get("mechanism_response_code") in NEGATIVE_MECHANISMS
        or cmoc.get("outcome_code") in NEGATIVE_OUTCOMES
    )
    polarity_issue = bool(cmoc.get("is_negative")) != polarity_should_be_negative

    error_tags = []
    if study["evidence_level"] != "Full-text":
        error_tags.append("provisional_evidence_level")
    if supported_count < 3:
        error_tags.append("weak_quote_support")
    if issues:
        error_tags.append("pts_chain_mismatch")
    if expected_pts_from_context != cmoc.get("pts"):
        error_tags.append("pts_context_mismatch")
    if alias_used:
        error_tags.append("predicate_alias_normalized")
    if invalid_predicates:
        error_tags.append("invalid_predicate")
    if polarity_issue:
        error_tags.append("polarity_check_needed")

    if not error_tags:
        decision_status = "AI_DRAFT_ACCEPT_READY_FOR_HUMAN_SIGNOFF"
        review_priority = "LOW"
    elif error_tags == ["predicate_alias_normalized"]:
        decision_status = "AI_DRAFT_ACCEPT_WITH_NORMALIZED_PREDICATE"
        review_priority = "LOW"
    elif study["evidence_level"] == "Abstract Only":
        decision_status = "AI_DRAFT_REVIEW_REQUIRED_ABSTRACT_ONLY"
        review_priority = "HIGH"
    else:
        decision_status = "AI_DRAFT_REVIEW_REQUIRED"
        review_priority = "MEDIUM" if supported_count >= 3 else "HIGH"

    confidence = 0.35
    confidence += 0.35 * evidence_score
    confidence += 0.15 if not issues else 0.0
    confidence += 0.10 if not polarity_issue else 0.0
    confidence += 0.05 if not invalid_predicates else 0.0
    confidence = min(0.95, round(confidence, 3))

    combined_evidence = (
        f"C: {cmoc.get('context_evidence', '')} | "
        f"I: {cmoc.get('intervention_evidence', '')} | "
        f"M: {cmoc.get('mechanism_response_evidence', '')} | "
        f"O: {cmoc.get('outcome_evidence', '')}"
    )

    corrected_triples = format_triples(triples)
    corrected_pts = expected_pts_from_context if "pts_context_mismatch" in error_tags else cmoc.get("pts", "")
    reviewer_note = (
        "AI-assisted draft, not final human gold. "
        f"Evidence support {supported_count}/4; "
        f"chain issues: {', '.join(issues) if issues else 'none'}; "
        f"predicate aliases normalized: {'yes' if alias_used else 'no'}."
    )

    return {
        "study_id": cmoc["study_id"],
        "cmoc_id": cmoc["cmoc_id"],
        "study_title": study["title"],
        "year": study["year"],
        "doi": study["doi"],
        "source_id": study["source_id"],
        "source_text_path": study["source_text_path"],
        "evidence_level": study["evidence_level"],
        "source_text_length": study["text_length"],
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
        "model_relationship_triples": "; ".join(
            f"{t['source_e_code']}-[{t['predicate']}]->{t['target_e_code']}"
            for t in triples
        ),
        "evidence_quote": combined_evidence,
        "quote_support_context": evidence_checks["context"]["status"],
        "quote_support_intervention": evidence_checks["intervention"]["status"],
        "quote_support_mechanism": evidence_checks["mechanism"]["status"],
        "quote_support_outcome": evidence_checks["outcome"]["status"],
        "evidence_support_score": evidence_score,
        "human_corrected_context": cmoc.get("context_code", ""),
        "human_corrected_intervention": cmoc.get("intervention_code", ""),
        "human_corrected_mechanism": cmoc.get("mechanism_response_code", ""),
        "human_corrected_outcome": cmoc.get("outcome_code", ""),
        "human_corrected_triples": corrected_triples,
        "human_corrected_pts": corrected_pts,
        "decision_status": decision_status,
        "review_priority": review_priority,
        "ai_adjudication_confidence": confidence,
        "error_category": "; ".join(error_tags) if error_tags else "none",
        "reviewer_notes": reviewer_note,
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    metadata = load_metadata()
    evidence = load_json(EVIDENCE_PATH)
    triples = load_json(TRIPLES_PATH) if os.path.exists(TRIPLES_PATH) else []
    gold = load_json(GOLD_PATH)

    triples_by_cmoc = defaultdict(list)
    for triple in triples:
        triples_by_cmoc[triple["cmoc_id"]].append(triple)

    rows = [
        adjudicate_row(cmoc, triples_by_cmoc.get(cmoc["cmoc_id"], []), metadata, gold)
        for cmoc in evidence
    ]

    headers = list(rows[0].keys())
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    status_counts = Counter(r["decision_status"] for r in rows)
    evidence_counts = Counter(r["evidence_level"] for r in rows)
    priority_counts = Counter(r["review_priority"] for r in rows)
    error_counts = Counter()
    for row in rows:
        for tag in row["error_category"].split("; "):
            if tag:
                error_counts[tag] += 1

    summary = [
        "# AI-Assisted Per-Paper Adjudication Draft Summary",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "This is an AI-assisted draft for human adjudication. It is not a final human gold standard.",
        "",
        "## Counts",
        f"- Rows / CMOCs: {len(rows)}",
        f"- Studies: {len(set(r['study_id'] for r in rows))}",
        "",
        "## Evidence Level",
    ]
    summary += [f"- {k}: {v}" for k, v in sorted(evidence_counts.items())]
    summary += ["", "## Decision Status"]
    summary += [f"- {k}: {v}" for k, v in sorted(status_counts.items())]
    summary += ["", "## Review Priority"]
    summary += [f"- {k}: {v}" for k, v in sorted(priority_counts.items())]
    summary += ["", "## Error / Review Tags"]
    summary += [f"- {k}: {v}" for k, v in sorted(error_counts.items())]
    summary += [
        "",
        "## Recommended Human Workflow",
        "1. Review HIGH priority rows first, especially abstract-only rows.",
        "2. Confirm or revise the human_corrected_* columns.",
        "3. Keep accepted rows as-is only after human sign-off.",
        "4. Use this signed file as the per-paper gold standard for refinement.",
    ]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(summary) + "\n")

    print(f"Generated {OUT_CSV}")
    print(f"Generated {OUT_JSON}")
    print(f"Generated {OUT_MD}")


if __name__ == "__main__":
    main()
