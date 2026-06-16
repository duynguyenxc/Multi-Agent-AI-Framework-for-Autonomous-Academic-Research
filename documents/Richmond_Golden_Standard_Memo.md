# Richmond Golden Standard Memo

## 1. Purpose

This memo defines what can legitimately be used as the Richmond "golden standard" for our project. The immediate goal is to answer the professor's core concerns:

- What did Richmond et al. actually do?
- Did Richmond produce one conclusion or several conclusions?
- Which parts of Richmond can be used as a reference standard for our LLM/KG pipeline?
- Which parts are not available in the paper and therefore require our own human adjudication protocol?

## 2. Executive Summary

Richmond et al. is best treated as a layered benchmark rather than a single flat answer key.

The Richmond paper gives us one overarching realist programme theory, supported by multiple context-specific CMOC findings. In practical terms, the paper gives us:

1. A search and screening benchmark: 28 included papers.
2. A human realist synthesis workflow benchmark: initial programme theory, screening, rigour/relevance appraisal, CMOC coding, cross-study synthesis, and programme theory refinement.
3. A final programme-theory benchmark: five key student-level contexts explaining when educational interventions for clinical reasoning work or fail.
4. A conclusion benchmark: interventions should support knowledge acquisition/recall, clinical experience, and practice of reasoning in authentic or simulated clinical settings; however, learner knowledge, self-confidence, self-efficacy, and coping shape whether the same intervention helps or harms.
5. A project-specific entity/relationship benchmark: the current repository has already formalized Richmond's findings into E01-E47 entities and R01-R40 relationships in `data/gold_standard.json`.

However, Richmond does not provide a complete machine-readable per-paper CMOC table or a complete per-paper entity/relation edge list. Therefore, Richmond can serve as the gold standard for final theory alignment and high-level CMOC structure, but per-paper CMOC and edge-level verification must be created through our own human adjudication process.

## 3. Richmond et al. Human Review Workflow

Richmond et al. conducted a realist review of educational interventions intended to develop analytical and non-analytical clinical reasoning in undergraduate medical and healthcare students.

Their work can be summarized as the following human workflow:

| Stage | What Richmond Did | Evidence Source |
|---|---|---|
| Review aim | Asked why clinical reasoning education interventions work, for whom, and under what circumstances. | `data/paper-Richmond-original.pdf`, Abstract and Introduction |
| Initial theory | Built an initial programme theory using scoping search, expert opinion, and the research team's prior experience. | `data/paper-Richmond-original.pdf`, Methods |
| Search | Searched MEDLINE, PsycINFO, ERIC, and CINAHL in May 2017, using terms connected to clinical reasoning, pattern recognition, deliberate practice, illness scripts, and knowledge acquisition/recall. | `data/paper-Richmond-original.pdf`, Methods |
| Screening | Retrieved 149 full texts; included 25 from screening, 2 from reference lists, and 1 from a later search, for 28 total included papers. | `data/paper-Richmond-original.pdf`, Study Characteristics |
| Appraisal | Screened for relevance to theory development and assessed rigour through credibility and trustworthiness of the evidence. | `data/paper-Richmond-original.pdf`, Methods |
| Data extraction | Developed CMOCs for all included full texts. One reviewer performed initial CMOC coding, and another reviewer checked all 28 articles for consistency. | `data/paper-Richmond-original.pdf`, Data Extraction and Synthesis |
| Synthesis | Compared CMOCs across papers, identified recurrent CMOCs, returned to earlier papers when later theories emerged, and refined the programme theory iteratively. | `data/paper-Richmond-original.pdf`, Data Extraction and Synthesis |
| Output | Produced five key context-based explanations and a final programme theory for clinical reasoning education interventions. | `data/paper-Richmond-original.pdf`, Results and Discussion |

The local study inventory confirms that our repository represents the same 28-study target set, with 20 papers available as PDFs and 8 represented by abstract/metadata records:

- Source: `data/studies_metadata.jsonl`
- Generated inventory: `outputs/evidence_base/study_inventory.tsv`
- Count: 28 records
- Local availability: 20 PDF full-text records, 8 URL/abstract-only records

## 4. Conclusion Structure

The best answer is:

Richmond reached one overarching programme-theory conclusion, but that conclusion is expressed through several context-specific CMOC conclusions.

The paper does not reduce the review to one universal intervention rule. Instead, it argues that the same educational intervention can work differently depending on learner context. The five main contexts are the organizing structure of the final theory.

## 5. Richmond's Five Main Context-Specific Conclusions

These five contexts are the most important gold-standard theory structure for our project.

| Richmond Context | Practical Meaning | Gold-Standard Implication |
|---|---|---|
| Low clinical domain-specific knowledge | Novice learners may lack enough knowledge to benefit from expert demonstration or complex reasoning tasks unless reasoning is made explicit and scaffolded. | The model should recover that low prior knowledge is not just background information; it changes how intervention resources are received. |
| High clinical domain-specific knowledge | More advanced learners can use expert reasoning, illness scripts, and non-analytical approaches more productively. | The model should distinguish high-knowledge learners from low-knowledge learners instead of treating all learners as one group. |
| Positive coping, self-confidence, or self-efficacy | Learners with appropriate confidence may experience mistakes, realistic cases, and clinical pressure as productive learning opportunities. | The model should capture positive affective/coping mechanisms, not only cognitive mechanisms. |
| Negative coping, low confidence, or low self-efficacy | Learners with poor coping or low confidence may experience similar interventions as stressful or overwhelming, producing poor learning or faulty reasoning. | The model must capture negative mechanisms and harmful outcomes, not only successful interventions. |
| Mixed knowledge levels within a group | Groups with varied knowledge need feedback and knowledge-retention strategies so learners can understand gaps and build more complete scripts. | The model should capture feedback as a key moderator/resource in mixed learner groups. |

Source: `data/paper-Richmond-original.pdf`, Results section 3.2 and Discussion.

## 6. Richmond's Final Programme-Theory Message

Richmond's final conclusion can be stated as follows:

Educational interventions for clinical reasoning are most effective when they help students acquire and recall knowledge, gain clinical or simulated clinical experience, and practice reasoning in environments where they can use both analytical and non-analytical reasoning. The effect depends strongly on learner knowledge, self-confidence, self-efficacy, and coping. Non-analytical reasoning should be promoted more deliberately after students have enough domain knowledge to use it safely and productively.

This is the main final-output benchmark for the project. If the pipeline produces a final synthesis that does not recover this message, then the pipeline has not reproduced the Richmond human synthesis at the programme-theory level.

## 7. Golden Standard Layers for This Project

The Richmond golden standard is used at five levels.

| Layer | What We Can Use as Gold | Local Source | Current Status |
|---|---|---|---|
| Corpus gold | The target corpus contains 28 included studies. | `data/studies_metadata.jsonl`; `outputs/evidence_base/study_inventory.tsv` | Available. |
| Workflow gold | Human realist synthesis workflow: IPT, screening, appraisal, CMOC coding, cross-study synthesis, programme theory refinement. | `data/paper-Richmond-original.pdf`; `documents/Human-Workflow-from-paper-Richmond.pdf` | Available as method benchmark. |
| Programme-theory gold | Five context-specific programme theory statements. | `data/paper-Richmond-original.pdf`; `data/gold_standard.json` | Available. |
| Entity gold | E01-E47 controlled entity set. | `data/gold_standard.json` | Available, but requires model-output normalization. |
| Relationship gold | R01-R40 controlled relationship set. | `data/gold_standard.json` | Available, but current pipeline does not yet fully evaluate strict edge fidelity. |
| Per-paper CMOC gold | Study-level CMOC tuples with evidence quotes. | Not fully provided by Richmond. | Must be manually created/adjudicated. |

## 8. Directly Verifiable Benchmark Components

Richmond directly supports verification of:

1. Whether our final synthesis recovers the five key contexts.
2. Whether our final synthesis distinguishes positive and negative learner mechanisms.
3. Whether our final synthesis recognizes that prior knowledge changes intervention effectiveness.
4. Whether our final synthesis treats feedback, reasoning explanation, case exposure, and simulation/clinical practice as intervention resources.
5. Whether our final synthesis concludes that both analytical and non-analytical reasoning matter, but that non-analytical reasoning depends on sufficient knowledge and experience.
6. Whether our project includes the same 28-study corpus.

## 9. Benchmark Limitations

Richmond cannot directly verify every model-generated entity and relationship because the paper does not publish a complete per-paper machine-readable extraction set. Specifically, Richmond does not provide:

1. A full table of all entity mentions by paper.
2. A full table of all relationship triples by paper.
3. A complete per-paper CMOC answer key.
4. A formal ontology with strict machine-readable relation types.
5. A metric for entity or edge-level KG quality.

Therefore, our project must not claim that Richmond alone gives a complete entity/relationship gold standard. The defensible claim is narrower and stronger:

Richmond provides the human programme-theory reference. Our repository's E01-E47 and R01-R40 specification operationalizes that reference into an entity/relationship benchmark. Per-paper extraction gold must be produced by human adjudication.

## 10. Project-Specific Gold Package Already Available

The file `data/gold_standard.json` currently gives a usable first formalization of Richmond's programme theory:

- 47 entities: E01-E47
- 40 relationships: R01-R40
- 5 programme theory statements: PTS1-PTS5
- Entity categories: Context, Intervention, Mechanism Resource, Mechanism Response, Outcome
- Relationship predicates: PROVIDES, ENABLES, TRIGGERS, LEADS_TO, CONSTRAINS

This is valuable because it converts Richmond's narrative realist synthesis into a structured evaluation target. It is frozen as the first version of the Richmond programme-theory gold standard.

Important caveat: this gold package is a programme-theory-level benchmark, not a complete per-paper extraction benchmark.

## 11. Alignment With Project Evaluation Requirements

| Evaluation requirement | Position |
|---|---|
| Final project target | Reproduce and extend the human realist synthesis process: from corpus to KG to CMOC extraction to final programme theory, then compare the model output with Richmond's human programme theory. |
| Richmond conclusion | Clinical reasoning interventions work through learner knowledge, experience, reasoning practice, feedback, confidence, self-efficacy, and coping; the same intervention can help or harm depending on context. |
| Conclusion structure | One overarching programme theory, expressed through five context-specific CMOC conclusions. |
| Gold-standard basis | Richmond's 28-study corpus, human workflow, five-context programme theory, and the E01-E47/R01-R40 operationalization. |
| Entity and relationship verification | Programme-theory-level verification is possible using E01-E47 and R01-R40. Full per-paper verification requires a human-adjudicated extraction set. |
| Post-KG use | The KG feeds CMOC extraction, cross-study synthesis, programme theory generation, and comparison against Richmond. The KG itself is evaluated before it is used as evidence. |

## 12. Recommended Benchmark Use

For the next phase, we should treat the Richmond golden standard as three nested targets:

1. Minimum target: reproduce the five Richmond context theories and final conclusion.
2. Structured target: map model entities to E01-E47 and relationships to R01-R40.
3. Strong target: build a manually adjudicated per-paper CMOC and entity/relation dataset for all 28 papers, with evidence quotes and confidence labels.

Only the first two targets can be evaluated immediately from existing local materials. The third target is necessary before making strong claims about per-paper extraction quality.

## 13. Source Register

Primary sources used for this memo:

- `data/paper-Richmond-original.pdf`
- `data/studies_metadata.jsonl`
- `data/gold_standard.json`
- `outputs/evidence_base/study_inventory.tsv`
- `documents/Human-Workflow-from-paper-Richmond.pdf`
- `documents/Richmond-KG-Specification-my-work-before-professor-send-more-documents.pdf`

## 14. Citation and Evidence Policy

This memo separates two types of evidence:

1. Scholarly evidence: published research that justifies the research design, especially Richmond et al. (2020) and the GraphRAG literature.
2. Local project evidence: repository files that show what the current implementation and benchmark package actually contain.

Any later paper or professor-facing report should preserve this distinction. Richmond et al. (2020) can justify the human benchmark and final realist synthesis target. Local files such as `data/gold_standard.json` can justify the project-specific operationalization, but they should not be cited as if they were independently published gold standards.

## 15. References

Richmond, A., Cooper, N., Gay, S., Atiomo, W., & Patel, R. (2020). The student is key: A realist review of educational interventions to develop analytical and non-analytical clinical reasoning ability. Medical Education, 54(8), 709-719. https://doi.org/10.1111/medu.14137

Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S., Metropolitansky, D., Ness, R. O., & Larson, J. (2025). From local to global: A GraphRAG approach to query-focused summarization. arXiv:2404.16130v2.

Project gold standard. (2026). Richmond-derived E01-E47, R01-R40, and PTS1-PTS5 benchmark. Local file: `data/gold_standard.json`.

Human workflow specification. (2026). Human Workflow Specification: Richmond et al. (2020) Realist Review. Local file: `documents/Human-Workflow-from-paper-Richmond.pdf`.
