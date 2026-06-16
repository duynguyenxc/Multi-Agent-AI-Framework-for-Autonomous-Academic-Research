# Deep Diagnostic & Implementation Plan — LLM-Knowledge-Graph v4.0

> **Date**: 2026-05-26  
> **Status**: Awaiting user approval before execution  
> **Rule**: "mỗi hành động phải luôn được xem xét cân nhắc kĩ càng suy luận tư duy"

---

## 🚨 CRITICAL DIAGNOSTIC: What's Wrong Right Now

I analyzed the entire codebase, all agent prompts, the current [evidence_table.json](file:///d:/LLM-Knowledge-Graph/outputs/evidence_table.json), and the [programme_theory_final.md](file:///d:/LLM-Knowledge-Graph/outputs/programme_theory_final.md). Here are **3 severe problems** discovered:

### Problem 1: CMOC Extraction is Too Generic — E02+E20 Domination

The evidence table shows **22 out of 28 studies** (78%) are labeled as Context = E02 (low knowledge students). This is **WRONG** — Richmond explicitly identified CMOCs across **all 5 Context types** (E02–E06).

| What Richmond Found | What Our System Produced |
|---------------------|-------------------------|
| CMOCs distributed across E02, E03, E04, E05, E06 | 22/28 = E02, 5/28 = E03, 1/28 = E06 |
| E04 (positive coping) & E05 (negative coping) present | **0 studies** classified as E04 or E05 |
| Rich diversity of Mechanism_Response (E20, E23, E24, E26, E27, E31–E35, E39, E42, E45) | **18/28 = E20 "understanding"** — lazy default! |
| Negative outcomes (E36, E37, E38, E47) appear in failed interventions | Only **1 study (S025)** has negative outcome |
| Multiple CMOCs per study (some studies contain 2-3 CMOCs) | **Exactly 1 CMOC per study** — information loss |

> [!CAUTION]
> The LLM is defaulting to the safest/most generic labels (E02 for Context, E20 for Mechanism_Response, E25/E22 for Outcome). This directly contradicts Richmond's nuanced findings and makes our system look like it cannot reproduce human-level synthesis. **This is the #1 problem to fix.**

### Problem 2: Two Separate "Graphs" — Disconnected Architecture

The project has **TWO completely separate graph systems** that don't talk to each other:

1. **Microsoft GraphRAG Graph** ([graph.graphml](file:///d:/LLM-Knowledge-Graph/outputs/graphrag_data/graph.graphml)) — Built by the `graphrag` indexer using `extract_graph.txt` prompt. Contains entities of type `Context, Intervention, Mechanism_Resource, Mechanism_Response, Outcome`. Produces community reports via Leiden clustering. Stored as **Parquet files + LanceDB**.

2. **LangGraph Pipeline CMOCs** ([cmoc_extractor.py](file:///d:/LLM-Knowledge-Graph/plugins/realist_synthesis/cmoc_extractor.py)) — Built by Agent 7 using a completely different prompt and Pydantic schema. Produces `CMOCExtraction` objects stored in **Python state dict** (RAM only).

These two systems use **different prompts**, **different extraction strategies**, and produce **different outputs**. The Leiden communities from System 1 are loaded into System 2 as context, but there's no structural integration.

> [!WARNING]
> This means our "Literature Knowledge Graph" is actually just community summary text being dumped into a synthesis prompt — it's NOT true GraphRAG retrieval with subgraph traversal as the professor's abstract describes.

### Problem 3: GraphRAG `extract_graph.txt` Prompt is GENERIC

Looking at [extract_graph.txt](file:///d:/LLM-Knowledge-Graph/graphrag/prompts/extract_graph.txt):
- Uses Microsoft's **default template** with generic examples (stock markets, hostages)
- Has no domain-specific guidance for medical education
- Entity types are set correctly in `settings.yaml` (`Context, Intervention, Mechanism_Resource, Mechanism_Response, Outcome`) but the **few-shot examples don't teach the LLM what these mean**
- Result: GraphRAG extracts entities that are too noisy and generic

---

## 📐 Question 1: What Algorithm Are We Using? — GraphRAG Architecture Clarified

**Yes, GraphRAG is the correct core algorithm.** But we must be precise about what it means in our system:

### GraphRAG = Two Operations

```
┌─────────────────────────────────────────────────────────┐
│  INDEXING (Build-time)                                   │
│  Papers → Chunks → LLM Entity/Relation Extraction        │
│        → Knowledge Graph (nodes + edges)                 │
│        → Leiden Community Detection                      │
│        → Community Summary Reports                       │
│        → Vector Embeddings (LanceDB)                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  QUERYING (Run-time)                                     │
│  Query → Retrieve relevant subgraph/communities          │
│        → Augment LLM context with graph structure        │
│        → Generate grounded response                      │
└─────────────────────────────────────────────────────────┘
```

### What Must Be True for Nodes & Relationships to Be Accurate

| Requirement | Current Status | Fix |
|-------------|---------------|-----|
| Domain-specific extraction prompt | ❌ Generic template | Rewrite `extract_graph.txt` with E01-E47 ontology |
| Few-shot examples from Richmond domain | ❌ Stock market examples | Add 3 medical education examples |
| Entity type enforcement | ✅ `entity_types` in settings.yaml | Keep |
| Relationship semantic types | ❌ Free-text only | Add `PROVIDES, ENABLES, LEADS_TO, TRIGGERS` guidance |
| Multi-CMOC per paper | ❌ Not designed for it | Restructure CMOC extractor to extract ALL CMOCs |
| Neo4j storage for query | ❌ Parquet only | Migrate to Neo4j |

---

## 📦 Question 2: Database Decision — Neo4j + PostgreSQL

### Architecture Decision

| Layer | Database | Purpose |
|-------|----------|---------|
| **Knowledge Graph** | **Neo4j** (primary) | Store entities (E01-E47), relationships, CMOCs, communities. Enable Cypher queries for subgraph retrieval, multi-hop reasoning, pattern matching |
| **Metadata & Audit** | **PostgreSQL** | Store study registry, PRISMA counts, screening decisions, audit logs, pipeline run history. Relational data that needs SQL queries |
| **Vector Search** | **Neo4j Vector Index** | Replace LanceDB. Neo4j 5.x has native vector indexing. Unified store = no data sync issues |

### Why Neo4j (not just Parquet)?

| Need | Parquet | Neo4j |
|------|---------|-------|
| "Find all studies where E02 context + E18 intervention → negative outcome" | Impossible (flat files) | `MATCH (c:Context {code:'E02'})-[:IN_CMOC]->(cmoc)<-[:IN_CMOC]-(i:Intervention {code:'E18'}) RETURN cmoc` |
| "Show me all mechanism pathways that lead to E47 (decreased accuracy)" | Load all into RAM, filter manually | `MATCH path = (m:Mechanism)-[:LEADS_TO*]->(o:Outcome {code:'E47'}) RETURN path` |
| "Which communities contain contradictory outcomes?" | Read all community summaries as text | Community nodes linked to CMOC nodes — traverse directly |
| "Trace citation from claim → paper → evidence span" | Not possible | Full provenance chain as graph edges |

### Why PostgreSQL for metadata?

- Study registry is inherently **tabular** (28 rows × 10 columns)
- PRISMA counts, screening decisions, audit logs = relational data
- PostgreSQL supports **JSONB** for flexible fields
- Pipeline run history with timestamps = perfect for SQL

### Neo4j Schema Design

```cypher
// --- Nodes ---
(:Study {study_id, title, authors, year, doi, source_file})
(:Context {code, label, category: "Context"})
(:Intervention {code, label, category: "Intervention"})
(:MechanismResource {code, label, category: "Mechanism_Resource"})
(:MechanismResponse {code, label, category: "Mechanism_Response"})
(:Outcome {code, label, category: "Outcome"})
(:CMOC {cmoc_id, study_id, evidence_quote})
(:Community {community_id, title, summary, rank})

// --- Relationships ---
(:Study)-[:HAS_CMOC]->(:CMOC)
(:CMOC)-[:HAS_CONTEXT]->(:Context)
(:CMOC)-[:HAS_INTERVENTION]->(:Intervention)
(:CMOC)-[:HAS_MECHANISM_RESOURCE]->(:MechanismResource)
(:CMOC)-[:HAS_MECHANISM_RESPONSE]->(:MechanismResponse)
(:CMOC)-[:HAS_OUTCOME]->(:Outcome)
(:Context)-[:ENABLES]->(:MechanismResponse)
(:Intervention)-[:PROVIDES]->(:MechanismResource)
(:MechanismResource)-[:TRIGGERS]->(:MechanismResponse)
(:MechanismResponse)-[:LEADS_TO]->(:Outcome)
(:Study)-[:IN_COMMUNITY]->(:Community)
```

---

## 📐 Question 3: Ontology & Schema — Aligning with Richmond

### Current Ontology Audit

The [ontology.py](file:///d:/LLM-Knowledge-Graph/core/ontology.py) is **correctly structured** but has key issues:

| Aspect | Status | Issue |
|--------|--------|-------|
| E01-E47 enum definitions | ✅ Correct | Matches Richmond |
| Entity categories (C, I, M_R, M_Resp, O) | ✅ Correct | Matches Richmond |
| Relationship types | ⚠️ Incomplete | Missing `INHIBITS`, `MODERATES` for contradictions |
| Multi-CMOC per study | ❌ Not supported | `CMOCExtraction` has ONE set of entities per study |
| Extracted text as evidence | ✅ Exists | `extracted_text` field in Entity |
| Evidence quote in relationships | ✅ Exists | `evidence_quote` field |

### What Richmond Actually Produced

Richmond organized findings around **5 Programme Theory Statements (PTS)**, each tied to a specific Context:

| PTS | Context | Key CMO Chains |
|-----|---------|----------------|
| PTS1 | E02 (low knowledge) | E07/E15/E18 → E19 → E20/E27 → E25/E29/E30 |
| PTS2 | E03 (high knowledge) | E10/E11 → E19 → E24/E39 → E25/E30/E43/E44 |
| PTS3 | E04 (positive coping) | E09/E10/E11 → E19 → E26/E27 → E22/E28/E40/E41 |
| PTS4 | E05 (negative coping) | E09/E10/E14 → E19 → E23/E32/E33/E34/E35/E45 → E36/E37/E38/E47 |
| PTS5 | E06 (mixed groups) | E07/E17 → E19 → E27/E39/E42 → E29/E43/E44/E46 |

> [!IMPORTANT]
> Our system currently produces **PTS1 only** (and poorly). PTS2-PTS5 are almost completely missing from the evidence table. This is the gap between "working demo" and "publication-ready benchmark comparison."

### Schema Fix: Multi-CMOC Extraction

```python
# PROPOSED: Allow multiple CMOCs per paper
class CMOCExtraction(BaseModel):
    record_id: str
    cmocs: List[SingleCMOC]  # Changed from flat entities/relationships
    
class SingleCMOC(BaseModel):
    cmoc_id: str  # e.g., "S001_CMOC1"
    context: Entity
    intervention: Entity
    mechanism_resource: Entity
    mechanism_response: Entity
    outcome: Entity
    causal_chain: List[Relationship]
    evidence_quotes: List[str]
    confidence: float  # 0-1
    programme_theory_statement: str  # Which PTS this maps to
```

---

## 📐 Question 4: Prompt Engineering Audit — What's Wrong & How to Fix

### Agent 7 (CMOC Extractor) — [cmoc_extractor.py](file:///d:/LLM-Knowledge-Graph/plugins/realist_synthesis/cmoc_extractor.py)

**Current Issues:**

1. **Anti-laziness instruction is not strong enough.** Despite saying "choose the MOST SPECIFIC label", the LLM still defaults to E02 + E20 + E25 for 78% of studies.

2. **Only 4 few-shot examples** and 3 of them use E02 as Context. This biases the LLM toward E02.

3. **"Extract the BEST-FIT CMOC"** — singular. This tells the LLM to extract exactly 1 CMOC per paper, when many papers contain 2-3 CMOCs.

4. **Paper text is truncated to 8000 chars** (`paper_text[:8000]`). For some papers, the Methods section alone is longer than this. The Results/Discussion (where CMOCs are most clearly stated) may be cut off.

**Proposed Fix:**

```python
# Key changes to CMOC_SYSTEM_PROMPT:

# 1. Change "extract BEST-FIT CMOC" → "extract ALL CMOCs"
"YOUR TASK: Extract ALL Context-Mechanism-Outcome Configurations from the paper."

# 2. Add NEGATIVE few-shot examples (critical!)
EXAMPLE_NEGATIVE = """
EXAMPLE — Sherbino et al. (2014): Cognitive forcing strategies FAILED
  Context: E02 (low knowledge students in emergency medicine)
  Intervention: E08 (instructed to use analytical reasoning alone)
  Mechanism_Response: E45 (confusion — no change in diagnostic search behavior)
  Outcome: E38 (negative learning outcomes — no reduction in diagnostic error)
  NOTE: This is a NEGATIVE result. Use negative labels when evidence shows failure.
"""

# 3. Add explicit anti-E20 instruction:
"For Mechanism_Response: E20 'understanding' is GENERIC. Use it ONLY if no more 
specific response is described. Look for emotional responses (E23 frustrated, 
E32 fear, E33 stress, E45 confusion) and cognitive responses (E24 rely on 
non-analytical, E27 build understanding, E39 build upon existing knowledge, 
E42 develop understanding of successes/failures)."

# 4. Add PTS mapping instruction:
"After extracting each CMOC, identify which of Richmond's 5 Programme Theory 
Statements (PTS1-PTS5) it most likely maps to based on the Context type."
```

### Agent 8 (Contradiction Detection) — [contradiction_agent.py](file:///d:/LLM-Knowledge-Graph/plugins/realist_synthesis/contradiction_agent.py)

**Current Issues:**
- Receives ALL CMOCs as one giant JSON dump → token-heavy, context confusion
- No structural guidance on how to compare CMOCs systematically
- CMOC data is capped at 12000 chars — may cut off important later studies

**Proposed Fix:**
- Pre-group CMOCs by Context type before sending to LLM
- Add explicit comparison template: "For each Context type, compare Interventions that produce opposing Outcomes"
- Use Neo4j Cypher queries to find contradictions structurally (pre-filter before LLM)

### Agent 10 (Synthesis) — [cross_study_synthesizer.py](file:///d:/LLM-Knowledge-Graph/plugins/realist_synthesis/cross_study_synthesizer.py)

**Current Issues:**
- CMOC data capped at 15000 chars — loses data for large corpora
- Generates "filler" for Contexts 3, 4 where no data exists (the output says "data does not explicitly address…" for E04 and E05 — this is hallucination filler)
- Does NOT use Neo4j/graph structure — just text-in, text-out

**Proposed Fix:**
- Use Neo4j to query CMOCs grouped by Context type → feed pre-structured data
- Add instruction: "If no evidence exists for a Context type, state 'No evidence found' — do NOT speculate"
- Break synthesis into 5 sub-calls (one per PTS) instead of 1 mega-call

### GraphRAG `extract_graph.txt` — [extract_graph.txt](file:///d:/LLM-Knowledge-Graph/graphrag/prompts/extract_graph.txt)

**Proposed Fix:** Replace generic examples with domain-specific ones:

```
Example — Medical Education (Clinical Reasoning):
Entity_types: Context, Intervention, Mechanism_Resource, Mechanism_Response, Outcome
Text: "Year 3 medical students with limited diagnostic experience were instructed to 
self-explain while solving clinical cases. Self-explanation activated biomedical 
knowledge links, leading to better diagnostic performance on subsequent unfamiliar cases."

Output:
("entity"|YEAR 3 MEDICAL STUDENTS|Context|Students with low clinical domain-specific 
knowledge, limited diagnostic experience)
("entity"|SELF-EXPLANATION|Intervention|Instructional procedure where students explain 
reasoning aloud while solving cases)
("entity"|BIOMEDICAL KNOWLEDGE ACTIVATION|Mechanism_Response|Self-explanation activated 
links between biomedical and clinical knowledge)  
("entity"|BETTER DIAGNOSTIC PERFORMANCE|Outcome|Improved diagnostic accuracy on 
unfamiliar cases after intervention)
("relationship"|SELF-EXPLANATION|BIOMEDICAL KNOWLEDGE ACTIVATION|Self-explanation 
triggered activation of biomedical knowledge links|8)
("relationship"|BIOMEDICAL KNOWLEDGE ACTIVATION|BETTER DIAGNOSTIC PERFORMANCE|
Activated knowledge links led to improved diagnostic performance|9)
```

---

## 📋 Phased Implementation Roadmap

### Phase 1: Fix CMOC Extraction Quality (HIGHEST PRIORITY) — ~2 days

> [!IMPORTANT]
> This is the single most important fix. Without accurate CMOCs, everything downstream (contradictions, synthesis, programme theory) will be wrong.

- [ ] Rewrite `ontology.py` → multi-CMOC schema (`SingleCMOC` + `CMOCExtraction.cmocs`)
- [ ] Rewrite `cmoc_extractor.py` prompt → anti-E20, negative examples, multi-CMOC, PTS mapping
- [ ] Rewrite `extract_graph.txt` → domain-specific examples
- [ ] Add few-shot examples for E03, E04, E05, E06 Contexts (not just E02)
- [ ] Re-run pipeline and compare new evidence table vs Richmond

### Phase 2: Neo4j Integration — ~3 days

- [ ] Design and create Neo4j schema (Cypher CREATE constraints)
- [ ] Write migration script: Parquet → Neo4j (entities + relationships)
- [ ] Write migration script: CMOC extractions → Neo4j
- [ ] Create `core/database/neo4j_client.py` — connection pooling, Cypher queries
- [ ] Create `core/database/postgres_client.py` — study registry, audit logs
- [ ] Replace `load_leiden_communities()` with Neo4j community query
- [ ] Add Neo4j vector index (replace LanceDB)

### Phase 3: Prompt & Agent Quality Improvements — ~2 days

- [ ] Rewrite contradiction agent → pre-group by Context, structured comparison
- [ ] Rewrite synthesis agent → 5 sub-calls (one per PTS), no speculation
- [ ] Add Verification Agent (Agent 11) → validate citations back to source text
- [ ] Add proper logging (Python `logging` module, not `print()`)
- [ ] Add `git` integration for commit tracking

### Phase 4: Evaluation Framework — ~2 days

- [ ] Build gold-standard from Richmond paper (manually code expected CMOCs for all 28 studies)
- [ ] Implement CMO precision/recall calculator
- [ ] Implement screening F1 calculator
- [ ] Implement Cohen's κ for inter-agent agreement
- [ ] Generate automated benchmark report

### Phase 5: Production Polish — ~2 days

- [ ] LangGraph state checkpointing (SQLite)
- [ ] HITL interface (Streamlit) for interactive CMOC review
- [ ] PRISMA diagram generator (mermaid)
- [ ] Full test suite
- [ ] Documentation

---

## Open Questions for Your Review

> [!IMPORTANT]
> **Neo4j Connection**: You said you have Neo4j Desktop installed. I need:
> 1. Which version? (Neo4j 5.x recommended)
> 2. What's the bolt URL? (default: `bolt://localhost:7687`)
> 3. Username/password for the database?
> 4. Have you created a database, or should I create one?

> [!IMPORTANT]
> **PostgreSQL Connection**: You said you have PostgreSQL installed. I need:
> 1. Which version?
> 2. Host/port? (default: `localhost:5432`)
> 3. Username/password?
> 4. Should I create a new database called `realist_review`?

> [!WARNING]
> **Phase Priority**: I recommend starting with **Phase 1** (fix CMOC extraction) because:
> - It requires NO new infrastructure
> - It's the most impactful change for publication quality
> - We can immediately re-run the pipeline and see improvement
> - All downstream agents (contradiction, synthesis) automatically improve
> 
> Do you agree with Phase 1 first, or do you want to start with Neo4j?

> [!NOTE]
> **API Cost**: Re-running CMOC extraction for 28 studies with multi-CMOC and longer context will cost approximately $2-3 in GPT-4o-mini API calls. The synthesis agent using GPT-4o will add ~$1. Total: ~$4 per full pipeline run.
