# Verification Report: Evaluating the Multi-Agent Realist Synthesis Framework Against the Richmond et al. (2020) Human Benchmark

**Author:** Duy Nguyen
**Date:** May 2026
**Advisor:** Professor Wei Zheng

---

## 1. Background — What Is This Project and Why Does It Exist?

In 2020, a team of five researchers (Richmond, Cooper, Gay, Atiomo, and Patel) published a realist review titled *"The student is key"* in the journal *Medical Education*. Over several months, the team manually read 28 research papers and produced a structured report answering:

> *"What works, for whom, in what circumstances, and why — when teaching clinical reasoning to medical students?"*

Their method is called **Realist Synthesis**. Unlike a standard literature review that simply counts "does it work?", realist synthesis digs into the causal chain behind each finding by breaking it into three components:

- **Context (C):** The starting conditions. *Who is the student?* (e.g., a beginner with low clinical knowledge)
- **Mechanism (M):** The causal engine. *What does the teaching method provide (Resource), and how does the student react internally (Response)?*
- **Outcome (O):** The result. *What happens?* (e.g., improved diagnostic accuracy, or negative learning outcomes)

A single combination of Context → Mechanism → Outcome is called a **CMOC** (Context-Mechanism-Outcome Configuration). Richmond's team produced multiple CMOCs organized around five student types (Contexts 1–5), then synthesized them into a unified **Programme Theory** — a narrative explanation of how and why things work.

**The goal of this project** is to test whether an AI system, built with multiple specialized agents and a knowledge graph, can perform the same analytical operations that Richmond's human team performed. If the AI's output aligns with the human benchmark, it provides evidence that this technology can assist researchers in conducting systematic reviews — reducing the manual workload while maintaining analytical rigor. The system does not claim to replace human judgment; it claims to externalize and structure the analytical labor.

---

## 2. The E01–E47 Ontology — The Shared Vocabulary

To ensure consistency across papers, Richmond's team created a **standardized dictionary of 47 concepts** (labeled E01 through E47). Every finding from every paper must be mapped to one of these 47 concepts. Our AI system uses the same dictionary, hard-coded as a Pydantic schema. The AI cannot invent new concepts outside this list — this is the primary mechanism for preventing hallucination.

### Context — Who is the student? (E01–E06)
| Code | Definition |
|------|-----------|
| E01 | Undergraduate students in medical or healthcare professions education |
| E02 | Students with "low knowledge," low clinical domain-specific knowledge, or inability to use knowledge in reasoning |
| E03 | Students with high clinical domain-specific knowledge |
| E04 | Positive student coping strategies or appropriate self-confidence/self-efficacy |
| E05 | Negative student coping strategies or lacking self-confidence/self-efficacy |
| E06 | Students with different levels of knowledge within a group |

### Intervention — What teaching method is used? (E07–E18)
| Code | Definition |
|------|-----------|
| E07 | An expert's reasoning processes are explicitly revealed and discussed |
| E08 | Instructed to use analytical reasoning alone |
| E09 | Teaching resources that allow students to make mistakes |
| E10 | Real-life scenarios, including simulation and simulated patients |
| E11 | Real cases |
| E12 | Strategies that promote knowledge retention |
| E13 | Accurate and timely feedback |
| E14 | Feedback is absent, incomplete, or contains errors |
| E15 | Explicit and clear explanation of expert's reasoning |
| E16 | Passive observation of experts without explanation |
| E17 | Listen to near-peer think aloud their reasoning with prompts and examples |
| E18 | Instructing to use both non-analytical and analytical reasoning |

### Mechanism Resource — What does the intervention provide? (E19)
| Code | Definition |
|------|-----------|
| E19 | Multiple relevant resources |

### Mechanism Response — How does the student react internally? (E20–E45)
| Code | Definition |
|------|-----------|
| E20 | Understanding |
| E23 | Frustrated |
| E24 | Rely on non-analytical reasoning |
| E26 | Grateful for the learning experience |
| E27 | Build understanding |
| E31 | Pressure that their decision making could have a real impact |
| E32 | Fear |
| E33 | Stress |
| E34 | Pressure to perform |
| E35 | Cognitive load is increased |
| E39 | Build upon what they already know |
| E42 | Develop understanding of successes/failures and generate improvement plans |
| E45 | Confusion |

### Outcome — What is the measurable result? (E21–E47)
| Code | Definition |
|------|-----------|
| E21 | Insight into the reasoning process when diagnosing and managing patients |
| E22 | Positive learning experience |
| E25 | High diagnostic accuracy |
| E28 | Positive impact on learning |
| E29 | More complete illness scripts |
| E30 | More accurate non-analytical reasoning |
| E36 | Poor illness script development |
| E37 | Faulty future non-analytical reasoning |
| E38 | Negative learning outcomes |
| E40 | Increased learning |
| E41 | Further engagement |
| E43 | Complete illness scripts |
| E44 | Successful non-analytical reasoning in the future |
| E46 | Increase in learning gain or diagnostic accuracy |
| E47 | Decrease in learning gain or diagnostic accuracy |

---

## 3. System Architecture — How the AI Pipeline Works

The system has two major components: a **10-Agent Pipeline** (built with LangGraph) and a **Knowledge Graph** (built with Microsoft GraphRAG). They serve different but complementary purposes.

### 3.1 The 10-Agent Pipeline (LangGraph)

**LangGraph** is an open-source framework that models workflows as directed graphs — a series of nodes (agents) connected by edges (transitions). Each agent is a Python function that receives a shared state, performs one specific task, and returns its results. The framework automatically passes the updated state to the next agent.

**Why this architecture:** Realist synthesis is inherently a sequential process — you cannot extract CMOCs before screening papers, and you cannot write a Programme Theory before extracting CMOCs. A directed graph enforces this ordering while keeping each step isolated and testable.

| Step | Agent | Input | Output |
|------|-------|-------|--------|
| 0 | Protocol Agent | Review question | Initial Programme Theory (IPT) |
| 1 | Deduplication Agent | PDF files | Deduplicated study registry with stable IDs |
| 2a | Screening Agent | Titles + abstracts | Include/exclude/uncertain decisions |
| — | **HITL Checkpoint 1** | Uncertain cases | Human adjudication |
| 2b | Full-Text Agent | Full paper text | Final included list |
| 3 | CMOC Extractor | Full paper text + E01–E47 schema | Structured C-M-O data |
| — | **HITL Checkpoint 2** | Extracted CMOCs | Human verification |
| 4 | Contradiction Agent | All CMOCs | Contradictions identified |
| — | **HITL Checkpoint 3** | Contradictions | Human resolution |
| 5 | Theory Synthesizer | Validated CMOCs + contradictions | Narrative Programme Theory |
| — | **HITL Checkpoint 4** | Draft theory | Human sign-off |
| 6 | Reporting Agent | All pipeline data | PRISMA report, evidence tables, audit trail |

**HITL (Human-In-The-Loop):** At four points, the pipeline pauses and waits for human review. In the current pilot, these checkpoints auto-approved to allow the pipeline to complete. In a production setting, a researcher would review and approve at each checkpoint.

### 3.2 The Knowledge Graph (Microsoft GraphRAG)

**GraphRAG** processes the same papers through a separate pipeline:
1. **Text chunking:** Each paper is split into overlapping segments.
2. **Entity extraction:** An LLM reads each segment and identifies concepts (entities) and their relationships.
3. **Graph construction:** All entities and relationships are assembled into a single large graph.
4. **Community detection (Leiden algorithm):** The graph is partitioned into clusters of closely related concepts. Each cluster represents a "topic" or "theme" that emerges from the data.
5. **Community reports:** An LLM summarizes each cluster into a human-readable report.

**Why this matters:** The Leiden communities represent what Richmond's team discovered through months of reading — the recurring themes and concepts across the literature. If the AI's communities match Richmond's themes, it suggests the knowledge graph accurately captures the conceptual structure of the corpus.

---

## 4. Verification — Step-by-Step Comparison Against Richmond

This section follows the verification protocol from Professor Wei Zheng's "Plan for Model Verification" (Part A, Steps 1–8).

### Step 1: Search & Screening Alignment

**Richmond's benchmark:** 28 papers included after searching 4 databases and applying inclusion/exclusion criteria.

**Our setup:** We fed the same 28 papers directly into the system (since we are using Richmond's corpus as the benchmark, not performing an independent search). The AI then screened these papers.

**Results:**

| Stage | Richmond | AI System |
|-------|---------|-----------|
| Papers input | 28 (from 4 databases) | 28 (same papers, provided as input) |
| After deduplication | 28 | 28 |
| After title/abstract screening | 28 included | 10 included, 16 excluded, 2 uncertain |
| After full-text review | 28 included | 12 included |

**Assessment:** There is a significant divergence. The 28 papers we provided are Richmond's *final included set* — they had already passed all human screening. The AI should ideally have retained all 28. The fact that it excluded 16 suggests the Screening Agent applied its criteria too aggressively. This is a known issue with LLM-based screening: the AI tends toward conservative exclusion when abstracts are ambiguous or incomplete (due to PDF extraction artifacts).

**Impact:** Downstream outputs (CMOC extraction, Programme Theory) are based on only 12 papers instead of 28.

---

### Step 2: CMO Extraction Fidelity

**Richmond's benchmark:** For each included paper, the human team extracted C-M-O components using the E01–E47 codes.

**Our test:** We ran extraction on one paper (Linn et al., 2012) as a pilot.

**Result — direct comparison for Linn (2012):**

| C-M-O Field | AI Extracted | Code | What Richmond Coded | Match? |
|-------------|-------------|------|--------------------|---------| 
| Context | "students with 'low knowledge,' low clinical domain-specific knowledge, or an inability to use knowledge in a reasoning situation" | E02 | Context 1 = E02 (low knowledge students) | ✅ |
| Intervention | "teaching resources that allow them to make mistakes" | E09 | Clinical teaching framework where students practice | ✅ |
| Mechanism Resource | "multiple relevant resources" | E19 | "multiple relevant resources" (same phrase) | ✅ |
| Mechanism Response | "build understanding" | E27 | Building student understanding | ✅ |
| Outcome | "positive impact on learning" | E28 | Positive learning outcomes | ✅ |

**Assessment:** All five fields match Richmond's coding. Zero hallucination — every label is a valid E-code from the ontology.

**Important caveat:** This is one paper out of 28. A sample of n=1 cannot establish statistical reliability. To properly assess extraction fidelity, extraction must be run on all included papers and compared field-by-field against Richmond's full coding. This pilot demonstrates that the extraction *mechanism works correctly*, not that it will work correctly on every paper.

---

### Step 3: Knowledge Graph — Entities and Relationships

**Richmond's benchmark:** Richmond did not produce a knowledge graph. This is a novel contribution of our system that extends beyond what the human team did.

**GraphRAG output statistics:**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Documents processed | 20 out of 28 | 71% of Richmond's corpus (8 PDFs failed extraction) |
| Entities extracted | 1,318 | Concepts identified across all papers |
| Relationships extracted | 1,672 | Connections between concepts |
| Relationship-to-entity ratio | 1.27 | Each entity connects to ~1.3 others on average |
| Community clusters | 245 | Thematic groupings found by Leiden algorithm |

**Assessment:** The entity types in GraphRAG were configured to match Richmond's C-M-O categories (Context, Intervention, Mechanism_Resource, Mechanism_Response, Outcome). This means the knowledge graph is structured around the same conceptual framework that Richmond used. The 1,318 entities and 1,672 relationships form a rich, interconnected network. However, with only 71% corpus coverage, some themes may be under-represented.

---

### Step 4: Community–Mechanism Alignment

This step checks whether the themes that emerged from GraphRAG's automatic clustering correspond to the themes that Richmond's human team identified through manual reading.

**Source of Richmond's themes:** Richmond's paper discusses the following topics extensively across multiple sections (Introduction, Results, Discussion). These are not a numbered list in the paper, but rather the dominant subjects that the authors repeatedly analyze and discuss:

| # | Topic Richmond discusses at length | GraphRAG Community | Rank | Found? |
|---|-----------------------------------|-------------------|------|--------|
| 1 | Diagnostic reasoning strategies and their effect on accuracy | "Diagnostic Accuracy and Reasoning Strategies in Medical Education" | 8.5 | ✅ |
| 2 | Self-explanation as a technique for improving clinical reasoning | "Clinical Reasoning and Self-Explanation in Medical Education" | 8.5 | ✅ |
| 3 | Simulation and game-based learning for clinical decision-making | "Medialis and Surgical Training Community" | 8.5 | ✅ |
| 4 | Virtual patient cases and EHR-based education | "Casebook Application and Virtual Patient Education" | 8.5 | ✅ |
| 5 | Repeated testing and assessment for knowledge retention | "Medical Education Assessment Community" | 8.5 | ✅ |
| 6 | Cognitive biases affecting diagnostic decisions | "Cognitive Biases and Diagnostic Errors in Medical Education" | 8.0 | ✅ |
| 7 | Cognitive Forcing Strategies (CFS) as a debiasing tool | "Cognitive Forcing Strategies and Diagnostic Errors" | 7.5 | ✅ |
| 8 | Structured reflection to improve diagnostic competence | "Structured Reflection in Medical Education" | 7.5 | ✅ |
| 9 | Schema-based instruction for clinical reasoning | "Schema-Based Instruction in Medical Education" | 7.5 | ✅ |
| 10 | Combining analytic and non-analytic reasoning approaches | "Combined Reasoning Strategies for Novice Diagnosticians" | 7.5 | ✅ |
| 11 | Dual-Process Theory as the theoretical foundation | No dedicated community | — | ⚠️ Partial |

**Assessment:** 10 out of 11 topics match. Dual-Process Theory is the theoretical lens that underlies the entire review — it is referenced throughout the paper but not as a standalone intervention or context. It makes sense that the algorithm did not cluster it as a separate community because it is a meta-level concept, not a specific educational intervention.

**Note on methodology:** The 11 topics listed above were identified by reading Richmond's paper and extracting the major subjects of analysis. This is a qualitative comparison — a more rigorous evaluation would involve an independent rater (e.g., a second researcher) identifying Richmond's themes and comparing them to the communities.

---

### Step 5: Programme Theory Comparison

**Richmond's Programme Theory** is organized around five student Contexts:
- **Context 1 (E02):** Students with low knowledge
- **Context 2 (E03):** Students with high knowledge
- **Context 3 (E04):** Students with positive coping strategies / self-efficacy
- **Context 4 (E05):** Students with negative coping strategies
- **Context 5 (E06):** Mixed-level groups

For each Context, Richmond describes a full CMOC chain (Context → Intervention → Mechanism → Outcome).

**AI's Programme Theory** covers only **Context 1 (E02)**. Below is a field-by-field comparison for that Context:

| Element | Richmond's Statement | AI's Statement | Match? |
|---------|---------------------|---------------|--------|
| Target population | Students with low knowledge (Context 1) | "novice learners... who possess 'low knowledge,' limited clinical domain-specific knowledge" | ✅ |
| Intervention | Expert demonstration with resources that allow practice | "teaching resources that allow students to make mistakes... clinicians demonstrating clinical consultations" | ✅ |
| Mechanism response | Building understanding of reasoning processes | "designed to build understanding by assisting students in comprehending the clinician's thought process" | ✅ |
| Outcome | Positive impact on learning and reasoning development | "positive impact on learning, specifically the development of clinical reasoning skills" | ✅ |
| Causal logic (C→M→O) | Present and explicit | Present and explicit | ✅ |
| Academic writing quality | Publication-ready | Clear, logical, professional tone | ✅ |

**What is missing compared to Richmond:**

| Element | Present in Richmond? | Present in AI? |
|---------|---------------------|----------------|
| Context 2 analysis (high knowledge) | ✅ | ❌ |
| Context 3 analysis (positive coping) | ✅ | ❌ |
| Context 4 analysis (negative coping) | ✅ | ❌ |
| Context 5 analysis (mixed groups) | ✅ | ❌ |
| Contradictory findings (e.g., CFS) | ✅ | ❌ "None detected" |
| Demi-Regularities | ✅ | ❌ "Not yet computed" |

**Assessment:** For Context 1, the AI's theory is substantively correct. But it covers only 1 of 5 Contexts because only 1 CMOC was extracted. This is a limitation of the pilot run, not of the system architecture.

---

### Step 6: Audit Trail and Transparency

| RAMESES Transparency Criterion | Richmond | AI System |
|-------------------------------|---------|-----------|
| Search process documented | Yes (Methods section of paper) | Yes (audit_trail.md, entry 2: "Registry built: 28 unique studies") |
| Screening decisions with rationale | Aggregated counts only | Per-paper decisions: "10 include, 16 exclude, 2 uncertain" |
| Human review checkpoints | Described generally in Methods | Logged explicitly: 4 named HITL checkpoints with entry numbers |
| Data extraction logged | Described in Methods | Logged: "Extracted 5 entities, 4 relations from [paper]" |

**Assessment:** The AI system provides a more granular audit trail than Richmond's published paper. Each agent decision is logged individually. This is an advantage for reproducibility.

---

### Step 7: Evidence-Grounded Q&A Demonstration

The Plan for Model Verification (Step 7) specifies testing the system with realist questions such as *"What works, for whom, in what contexts, and why?"*

**Status:** This step has not been performed yet. To complete it, we would need to:
1. Define a fixed set of realist questions based on Richmond's review question.
2. Run each question through GraphRAG's query engine.
3. Evaluate whether the AI's answers cite specific papers, use C-M-O framing, and align with Richmond's conclusions.

**This is a gap in the current evaluation.** It should be addressed in the next phase.

---

### Step 8: Boundary Statement — What Is and Is Not Replicated

Following the Plan for Model Verification (Step 8):

**What the system successfully reproduced (simulated):**
| Operation | Evidence |
|-----------|---------|
| Screening logic | Agent applied inclusion/exclusion criteria and produced reasoned decisions (though over-excluded) |
| CMO extraction with ontology enforcement | 1 CMOC extracted with 5/5 field accuracy, using E01–E47 schema |
| Knowledge graph construction | 1,318 entities, 1,672 relationships from 20 papers |
| Cross-study pattern detection | 245 Leiden communities; 10/11 match Richmond's themes |
| Programme Theory generation | Context 1 theory structurally and substantively matches Richmond |
| Decision audit trail | More detailed than Richmond's published methodology |

**What the system did NOT replace:**
| Operation | Reason |
|-----------|--------|
| Final interpretive judgment | Deliberate design choice — humans retain authority per realist methodology |
| Normative theory selection | The AI generates candidate theories; humans decide which is "best" |
| Full-scale extraction (all 28 papers) | Not yet executed — pilot ran on 1 paper only |
| Contradiction resolution | Requires multiple CMOCs; not triggered in pilot |
| Independent search and retrieval | Papers were pre-supplied; the AI did not perform literature search |

---

## 5. Summary of Findings

| Verification Step | Status | Key Finding |
|-------------------|--------|-------------|
| Step 1: Search & Screening | ⚠️ Partial | AI retained 12/28 papers (over-excluded). Screening Agent needs recalibration. |
| Step 2: CMO Extraction | ✅ Pilot passed | 1 CMOC extracted, 5/5 fields correct. Needs full-scale validation. |
| Step 3: Knowledge Graph | ✅ Built | 1,318 entities, 1,672 relationships, 71% corpus coverage. |
| Step 4: Community Alignment | ✅ Strong | 10/11 themes match Richmond (91% alignment). |
| Step 5: Programme Theory | ✅ Partial | Context 1 correct. Contexts 2–5 not yet covered. |
| Step 6: Audit Trail | ✅ Strong | More granular than Richmond's published process. |
| Step 7: Q&A Demonstration | ❌ Not done | Needs to be performed in next phase. |
| Step 8: Boundary Statement | ✅ Documented | Clear separation of what is replicated vs. not replaced. |

---

## 6. Conclusion

The pilot run provides evidence that the system's architecture is **capable of performing the core analytical operations of realist synthesis**: screening, CMO extraction, cross-study pattern detection, and programme theory generation. The single CMOC extracted from Linn (2012) matches Richmond's coding across all five fields, and the Knowledge Graph independently identified 10 of 11 major themes from the literature.

However, the current output is a **proof of concept**, not a complete replication. Three items must be addressed before the system's output can stand alongside Richmond's results:

1. **Run extraction on all included papers** to produce a full set of CMOCs covering Richmond's 5 Contexts.
2. **Recalibrate or bypass screening** for this benchmark test, since the input papers are already Richmond's final included set.
3. **Complete Step 7** (evidence-grounded Q&A) to demonstrate end-to-end query capability.

Once these steps are completed, the system will have produced a full set of comparable outputs for formal evaluation against the human benchmark.

---

*This report follows the verification protocol outlined in "Plan for Model Verification" (Part A, Steps 0–8), provided by Professor Wei Zheng.*
