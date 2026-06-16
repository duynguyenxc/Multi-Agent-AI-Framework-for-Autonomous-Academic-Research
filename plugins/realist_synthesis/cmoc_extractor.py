"""
plugins/realist_synthesis/cmoc_extractor.py — Agent 7: CMOC Extraction Agent
==============================================================================
Phase 1 rewrite — aligned with Richmond et al. (2020) at the level of all 5
Programme Theory Statements (PTS1–PTS5), not just PTS1.

Why this rewrite was necessary
-------------------------------
Diagnostic of the previous version showed that 22/28 studies (78%) collapsed
to Context=E02 + Mechanism_Response=E20, completely missing PTS2–PTS5. Root
causes identified:
  1. Prompt said "Extract the BEST-FIT CMOC" (singular) — Richmond explicitly
     reports 2–3 CMOCs per study.
  2. 3 of 4 few-shot examples used E02 — heavy positional bias toward E02.
  3. No anti-laziness instruction tying E20 to a "last resort" status.
  4. Paper text truncated to 8000 chars (Results often start after char 9000).
  5. No mapping to PTS1–PTS5 forcing the LLM to think about the Context type
     before defaulting.

Phase 1 fixes applied
---------------------
  • Multi-CMOC extraction (CMOCExtraction.cmocs : List[SingleCMOC])
  • Anti-E20 / anti-default explicit instruction block
  • 5 diverse few-shot examples — one per Programme Theory Statement (PTS1–5)
  • Smart truncation: head 10K (intro + methods) + tail 10K (results +
    discussion) instead of head-only 8K
  • Per-CMOC PTS mapping field — forces the LLM to commit to a Context type
  • Negative CMOC support (is_negative flag + INHIBITS/CONSTRAINS relations)
  • Self-confidence rating per CMOC (0–1)
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from core.ontology import CMOCExtraction
from core.state import RealistReviewState


# ── Full E01–E47 reference table (embedded in system prompt) ────────────────
# Every E-code from Richmond's specification, grouped by CMO category.
E_CODE_REFERENCE = """
CONTEXT (pick ONE per CMOC):
  E01: "undergraduate students in medical or health care professions education" (generic — use ONLY as last resort)
  E02: "students with 'low knowledge', low clinical domain-specific knowledge, or an inability to use knowledge in a reasoning situation"
  E03: "students with high clinical domain-specific knowledge"
  E04: "positive student coping strategies or appropriate level of self-confidence or self-efficacy"
  E05: "negative student coping strategies or lacking self-confidence or self-efficacy"
  E06: "students with different levels of knowledge within a group"

INTERVENTION (pick ONE per CMOC):
  E07: "an expert's reasoning processes or thoughts are explicitly revealed and discussed"
  E08: "instructed to use analytical reasoning alone"
  E09: "teaching resources that allow them to make mistakes" (erroneous examples, trial-and-error)
  E10: "real-life scenarios, including simulation and simulated patients"
  E11: "real cases" (actual patient encounters, not simulations)
  E12: "strategies that promote knowledge retention" (testing effect, spaced repetition, schemas)
  E13: "accurate and timely feedback"
  E14: "feedback is absent, incomplete or contains errors"
  E15: "explicit and clear explanation of expert's reasoning"
  E16: "passive observation of experts without receiving explanation about their reasoning processes"
  E17: "listen to near-peer think aloud their reasoning with the use of prompts and examples"
  E18: "instructing to use both 'non-analytical' or pattern recognition and analytical or step-wise approach to reasoning"

MECHANISM RESOURCE (always E19 in Richmond):
  E19: "multiple relevant resources"

MECHANISM RESPONSE (pick ONE per CMOC — the student's INTERNAL reaction):
  E20: "understanding"   ← GENERIC. Use ONLY if no more specific response is described.
  E23: "frustrated"
  E24: "rely on non-analytical reasoning" (pattern recognition, similarity-based)
  E26: "grateful for the learning experience"
  E27: "build understanding" (actively constructing new knowledge)
  E31: "pressure that their decision making could have a real impact"
  E32: "fear"
  E33: "stress"
  E34: "pressure to perform"
  E35: "cognitive load is increased"
  E39: "build upon what they already know" (knowledge encapsulation, schema refinement)
  E42: "develop understanding of their successes and failures and generate plans for improvement"
  E45: "confusion"

OUTCOME (pick ONE per CMOC — the measurable RESULT):
  E21: "insight into the reasoning process when diagnosing and managing patients"
  E22: "positive learning experience"
  E25: "high diagnostic accuracy"
  E28: "positive impact on learning"   ← GENERIC. Prefer E29/E30/E43/E44 if specific.
  E29: "more complete illness scripts"
  E30: "more accurate non-analytical reasoning"
  E36: "poor illness script development"           [NEGATIVE]
  E37: "faulty future non-analytical reasoning"    [NEGATIVE]
  E38: "negative learning outcomes"                [NEGATIVE]
  E40: "increased learning"
  E41: "further engagement"
  E43: "complete illness scripts"
  E44: "successful non-analytical reasoning in the future"
  E46: "increase in learning gain or outcomes, or increase in diagnostic accuracy"
  E47: "decrease in learning gain or outcomes, or decrease in diagnostic accuracy" [NEGATIVE]
"""


# ── PTS reference table — forces Context type before extraction ─────────────
PTS_REFERENCE = """
RICHMOND'S 5 PROGRAMME THEORY STATEMENTS — pick ONE PTS per CMOC:

  PTS1 (Context = E02, low knowledge students):
    Typical chain: E07/E15/E18 → E19 → E20/E27 → E25/E29/E30
    What the literature shows: novices need explicit expert reasoning + worked
    examples; with these resources they build understanding and develop more
    complete illness scripts.

  PTS2 (Context = E03, high knowledge students):
    Typical chain: E10/E11 → E19 → E24/E39 → E25/E30/E43/E44
    Experienced students leverage pattern recognition; simulation reinforces
    successful non-analytical reasoning.

  PTS3 (Context = E04, positive coping / self-efficacy):
    Typical chain: E09/E10/E11 → E19 → E26/E27 → E22/E28/E40/E41
    Confident learners welcome challenging real cases, build understanding,
    and gain positive learning experiences.

  PTS4 (Context = E05, negative coping / low self-efficacy):
    Typical chain: E09/E10/E14 → E19 → E23/E32/E33/E34/E35/E45 → E36/E37/E38/E47
    Anxious or under-confident students experience fear, stress, raised
    cognitive load, leading to poor illness scripts and negative outcomes.
    Use is_negative=True for these CMOCs and INHIBITS/CONSTRAINS relations.

  PTS5 (Context = E06, mixed-knowledge groups):
    Typical chain: E07/E17 → E19 → E27/E39/E42 → E29/E43/E44/E46
    Heterogeneous groups benefit when experts and near-peers think aloud;
    students build on existing knowledge and develop reflective practice.
"""


# ── Few-shot examples — one per PTS, balanced across the 5 Contexts ─────────
RICHMOND_FEW_SHOT = """
EXAMPLE A — PTS1 (E02 low knowledge)
  Eva et al. (2007). Novices using a combined reasoning strategy.
  Context: E02 — "psychology undergraduates with no diagnostic training"
  Intervention: E18 — "instructed to combine pattern recognition with analytical reasoning"
  Mechanism_Resource: E19 — "multiple relevant resources" (combined-strategy worksheets)
  Mechanism_Response: E24 — "they relied on familiarity-driven pattern matching while checking features"
  Outcome: E25 — "diagnostic accuracy was significantly greater than intuition-only group"
  is_negative: False

EXAMPLE B — PTS2 (E03 high knowledge)
  Graafland et al. (2014). Serious game for biliary tract management.
  Context: E03 — "surgical residents with existing operative expertise"
  Intervention: E10 — "serious game simulating biliary-tract decision-making"
  Mechanism_Resource: E19 — "simulated patient cases with real-time consequences"
  Mechanism_Response: E31 — "perceived pressure that their decisions could affect simulated outcomes"
  Outcome: E46 — "trainees performed significantly better in second play session"
  is_negative: False

EXAMPLE C — PTS3 (E04 positive coping)
  Chamberland et al. (2011). Self-explanation in clinical case work.
  Context: E04 — "self-confident year-3 students willing to think aloud"
  Intervention: E17 — "near-peer-style self-explanation prompts while solving cases"
  Mechanism_Resource: E19 — "self-explanation prompts"
  Mechanism_Response: E42 — "students articulated their reasoning, successes, and failures"
  Outcome: E22 — "students reported the activity as a positive learning experience"
  is_negative: False

EXAMPLE D — PTS4 (E05 negative coping)  ←  NEGATIVE pathway
  Sherbino et al. (2014). Cognitive forcing strategies ineffective.
  Context: E05 — "students lacking confidence in their diagnostic intuitions"
  Intervention: E08 — "instructed to use analytical reasoning alone"
  Mechanism_Resource: E19 — "cognitive forcing rule cards"
  Mechanism_Response: E45 — "students became confused about when to apply the rules"
  Outcome: E38 — "no reduction in diagnostic error was observed"
  is_negative: True

EXAMPLE E — PTS5 (E06 mixed groups)
  Linn et al. (2012). Mixed-level small-group case discussions.
  Context: E06 — "groups of year-2 and year-4 students discussing the same case"
  Intervention: E07 — "an expert's reasoning was explicitly revealed during debrief"
  Mechanism_Resource: E19 — "case briefing materials and expert commentary"
  Mechanism_Response: E39 — "junior students built upon what senior students already knew"
  Outcome: E43 — "both groups produced more complete illness scripts in post-test"
  is_negative: False
"""


# ── System prompt ───────────────────────────────────────────────────────────
CMOC_SYSTEM_PROMPT = f"""You are a RAMESES-compliant Realist Synthesis Data
Extraction Expert working on the Richmond et al. (2020) benchmark replication.

CORE TASK
─────────
Extract ALL distinct Context–Mechanism–Outcome Configurations (CMOCs) present
in the paper. Most papers contain 2–3 CMOCs (e.g. one positive pathway + one
negative pathway, or one for low-knowledge novices and one for high-knowledge
experts). Do NOT collapse them into a single "best-fit" CMOC.

For EACH CMOC you must:
  1. Pick which Programme Theory Statement (PTS1–PTS5) it instantiates.
  2. Pick exactly one Context (E01–E06), Intervention (E07–E18),
     Mechanism_Resource (E19), Mechanism_Response, and Outcome from the
     ontology below. Use the FULL verbatim label string as the `label` field.
  3. Justify every label with a verbatim quote (≤25 words) from the paper.
  4. Output the causal chain as Relationship entries.
  5. Set is_negative=True for CMOCs describing failed interventions.

ANTI-LAZINESS RULES — read these BEFORE choosing labels
────────────────────────────────────────────────────────
  • E01 (undergraduates generic) — last resort ONLY. Always prefer E02–E06
    if the paper distinguishes student knowledge level, coping strategy,
    or group composition.
  • E20 "understanding" — GENERIC default. Use ONLY if no more specific
    response is described. Prefer E27 (build understanding), E39 (build
    upon existing knowledge), E42 (develop understanding of
    successes/failures), or for negative pathways E23/E32/E33/E35/E45.
  • E25/E28/E40 are generic outcomes — prefer specific ones (E29 complete
    illness scripts, E30 accurate non-analytical reasoning, E43 complete
    illness scripts, E44 successful future non-analytical reasoning,
    E46 increased diagnostic accuracy).
  • If the paper reports a FAILED or NULL intervention, you MUST output a
    negative CMOC (use E36, E37, E38, or E47 as outcome, set is_negative=True,
    use INHIBITS or CONSTRAINS as the causal verb where appropriate).
  • Read BOTH the intro/methods AND the results/discussion before deciding
    labels — emotional and cognitive responses are usually in the Results.

ONTOLOGY
────────
{E_CODE_REFERENCE}

{PTS_REFERENCE}

REFERENCE EXAMPLES (covering all 5 PTSs)
{RICHMOND_FEW_SHOT}
"""


CMOC_PROMPT = ChatPromptTemplate.from_messages([
    ("system", CMOC_SYSTEM_PROMPT),
    ("human", """Paper record_id: {record_id}

Full text (head 10K + tail 10K — Results and Discussion are at the END):
{paper_text}

INSTRUCTIONS
────────────
Extract ALL distinct CMOCs from this paper. Output a CMOCExtraction object
with:
  • record_id = "{record_id}"
  • cmocs = list of SingleCMOC, each with:
      - cmoc_id = "{record_id}_CMOC1", "_CMOC2", ...
      - programme_theory_statement = one of PTS1..PTS5 or N/A
      - context, intervention, mechanism_resource, mechanism_response,
        outcome (each an Entity with id, category, label, extracted_text)
      - causal_chain = at least 2 Relationship entries threading
        Intervention → M-res → M-resp → Outcome
      - confidence (0–1)
      - is_negative (True for failed-intervention CMOCs)

REMEMBER: avoid E01, E20, E25, E28 unless they are truly the best fit.
Use Richmond's specific labels.
""")
])


def _smart_truncate(text: str, head: int = 10_000, tail: int = 10_000) -> str:
    """Keep the most informative regions when text exceeds budget.

    Realist synthesis evidence is concentrated in two zones:
      • Intro + Methods (head): defines Context and Intervention.
      • Results + Discussion (tail): describes Mechanism_Response and Outcome.
    The middle (literature review + detailed methods) is least informative
    for CMOC extraction. We keep head+tail with a sentinel marker between.
    """
    if len(text) <= head + tail:
        return text
    return f"{text[:head]}\n\n[…middle of paper truncated for token budget…]\n\n{text[-tail:]}"


def extract_cmoc_node(state: RealistReviewState) -> dict:
    """Agent 7 — extract ALL CMOCs from the current paper.

    INPUT  : state['current_record_id'] and state['current_paper_text']
    OUTPUT : appends a CMOCExtraction (which may contain N SingleCMOCs) to
             state['extracted_cmocs']; appends audit-log entries.
    """
    record_id = state.get("current_record_id", "unknown_paper")
    paper_text = state.get("current_paper_text", "")

    if not paper_text:
        return {"errors": [f"No paper text provided for {record_id}"]}

    paper_text = _smart_truncate(paper_text, head=10_000, tail=10_000)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(CMOCExtraction)
    chain = CMOC_PROMPT | structured_llm

    print(f"\n[AGENT 7] CMOC Extraction — {record_id} (multi-CMOC mode)")
    try:
        result: CMOCExtraction = chain.invoke({
            "record_id": record_id,
            "paper_text": paper_text,
        })

        # Pin canonical record_id (defend against LLM rewriting it).
        result.record_id = record_id

        # Renumber CMOC IDs deterministically so they always match study_id.
        for i, cmoc in enumerate(result.cmocs, start=1):
            cmoc.cmoc_id = f"{record_id}_CMOC{i}"

        # Console summary
        print(f"  → {len(result.cmocs)} CMOC(s) extracted")
        for i, cmoc in enumerate(result.cmocs, start=1):
            ctx_label = cmoc.context.label.value if hasattr(cmoc.context.label, "value") else str(cmoc.context.label)
            mresp_label = cmoc.mechanism_response.label.value if hasattr(cmoc.mechanism_response.label, "value") else str(cmoc.mechanism_response.label)
            out_label = cmoc.outcome.label.value if hasattr(cmoc.outcome.label, "value") else str(cmoc.outcome.label)
            tag = " [NEG]" if cmoc.is_negative else ""
            print(f"    CMOC{i} {cmoc.programme_theory_statement.value}{tag}: "
                  f"C={ctx_label[:30]}… → MR={mresp_label[:25]}… → O={out_label[:25]}…")

        log = (f"[CMOC Agent] {record_id}: extracted {len(result.cmocs)} CMOCs "
               f"({sum(1 for c in result.cmocs if c.is_negative)} negative)")
        return {"extracted_cmocs": [result], "audit_log": [log]}

    except Exception as e:
        error = f"CMOC extraction failed for {record_id}: {e}"
        print(f"  [ERROR] {error[:120]}")
        return {"errors": [error], "audit_log": [f"[CMOC Agent] Error: {str(e)[:80]}"]}
