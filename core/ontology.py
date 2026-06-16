"""
core/ontology.py — Richmond-Aligned E01-E47 Ontology + Multi-CMOC Schema
==========================================================================
Defines the complete entity taxonomy from Richmond et al. (2020), enforced
via Pydantic enums to prevent LLM hallucination of arbitrary labels.

v4 Changes:
  - Added SingleCMOC model for structured C→I→M_R→M_Resp→O chains
  - CMOCExtraction now contains a LIST of SingleCMOC (multi-CMOC per study)
  - Added confidence score and PTS mapping per CMOC
  - Added RelationType.INHIBITS and MODERATES for contradiction modeling
  - Added RichmondPTS enum for Programme Theory Statement mapping
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Entity Categories ────────────────────────────────────────────────────────

class EntityCategory(str, Enum):
    CONTEXT = "Context"
    INTERVENTION = "Intervention"
    MECHANISM_RESOURCE = "Mechanism_Resource"
    MECHANISM_RESPONSE = "Mechanism_Response"
    OUTCOME = "Outcome"


# ── Context Types (E01-E06) ──────────────────────────────────────────────────

class ContextType(str, Enum):
    E01 = "undergraduate students in medical or health care professions education"
    E02 = "students with 'low knowledge,' low clinical domain-specific knowledge, or an inability to use knowledge in a reasoning situation"
    E03 = "students with high clinical domain-specific knowledge"
    E04 = "positive student coping strategies or appropriate level of self-confidence or self-efficacy"
    E05 = "negative student coping strategies or lacking self-confidence or self-efficacy"
    E06 = "students with different levels of knowledge within a group"


# ── Intervention Types (E07-E18) ─────────────────────────────────────────────

class InterventionType(str, Enum):
    E07 = "an expert's reasoning processes or thoughts are explicitly revealed and discussed"
    E08 = "instructed to use analytical reasoning alone"
    E09 = "teaching resources that allow them to make mistakes"
    E10 = "real-life scenarios, including simulation and simulated patients"
    E11 = "real cases"
    E12 = "strategies that promote knowledge retention"
    E13 = "accurate and timely feedback"
    E14 = "feedback is absent, incomplete or contains errors"
    E15 = "explicit and clear explanation of expert's reasoning"
    E16 = "passive observation of experts without receiving explanation about their reasoning processes"
    E17 = "listen to near-peer think aloud their reasoning with the use of prompts and examples"
    E18 = "instructing to use both 'non-analytical' or pattern recognition and analytical or step-wise approach to reasoning"


# ── Mechanism Resource (E19) ─────────────────────────────────────────────────

class MechanismResourceType(str, Enum):
    E19 = "multiple relevant resources"


# ── Mechanism Response Types (E20-E45) ───────────────────────────────────────

class MechanismResponseType(str, Enum):
    E20 = "understanding"
    E23 = "frustrated"
    E24 = "rely on non-analytical reasoning"
    E26 = "grateful for the learning experience"
    E27 = "build understanding"
    E31 = "pressure that their decision making could have a real impact"
    E32 = "fear"
    E33 = "stress"
    E34 = "pressure to perform"
    E35 = "cognitive load is increased"
    E39 = "build upon what they already know"
    E42 = "develop understanding of their successes and failures and generate plans for improvement"
    E45 = "confusion"


# ── Outcome Types (E21-E47) ──────────────────────────────────────────────────

class OutcomeType(str, Enum):
    E21 = "insight into the reasoning process when diagnosing and managing patients"
    E22 = "positive learning experience"
    E25 = "high diagnostic accuracy"
    E28 = "positive impact on learning"
    E29 = "more complete illness scripts"
    E30 = "more accurate non-analytical reasoning"
    E36 = "poor illness script development"
    E37 = "faulty future non-analytical reasoning"
    E38 = "negative learning outcomes"
    E40 = "increased learning"
    E41 = "further engagement"
    E43 = "complete illness scripts"
    E44 = "successful non-analytical reasoning in the future"
    E46 = "increase in learning gain or outcomes, or increase in diagnostic accuracy"
    E47 = "decrease in learning gain or outcomes, or decrease in diagnostic accuracy"


# ── Relationship Types ───────────────────────────────────────────────────────

class RelationType(str, Enum):
    PROVIDES = "PROVIDES"
    ENABLES = "ENABLES"
    LEADS_TO = "LEADS_TO"
    TRIGGERS = "TRIGGERS"
    INHIBITS = "INHIBITS"
    MODERATES = "MODERATES"
    CONSTRAINS = "CONSTRAINS"


# ── Richmond Programme Theory Statement Mapping ──────────────────────────────

class RichmondPTS(str, Enum):
    """Maps to Richmond's 5 Programme Theory Statements by Context type."""
    PTS1 = "PTS1: Low knowledge students (E02)"
    PTS2 = "PTS2: High knowledge students (E03)"
    PTS3 = "PTS3: Positive coping / self-efficacy (E04)"
    PTS4 = "PTS4: Negative coping / lacking self-efficacy (E05)"
    PTS5 = "PTS5: Mixed-level groups (E06)"


# ── Union Type for All Labels ────────────────────────────────────────────────

from typing import Union

LabelType = Union[
    ContextType, InterventionType, MechanismResourceType,
    MechanismResponseType, OutcomeType
]


# ── Entity Model ─────────────────────────────────────────────────────────────

class Entity(BaseModel):
    id: str = Field(
        ..., description="A unique identifier, e.g. 'E02' or 'node_1'"
    )
    category: EntityCategory = Field(
        ..., description="The high-level CMO category"
    )
    label: LabelType = Field(
        ..., description="The EXACT concept string from the E01-E47 specification"
    )
    extracted_text: str = Field(
        ..., description="VERBATIM quote from the paper justifying this label"
    )


# ── Relationship Model ──────────────────────────────────────────────────────

class Relationship(BaseModel):
    source_id: str = Field(..., description="ID of the source entity")
    target_id: str = Field(..., description="ID of the target entity")
    relation_type: RelationType = Field(
        ..., description="The type of causal link"
    )
    evidence_quote: str = Field(
        ..., description="Exact sentence from the paper proving this relationship"
    )


# ── Single CMOC (one C→I→M_R→M_Resp→O chain) ───────────────────────────────

class SingleCMOC(BaseModel):
    """One complete Context-Mechanism-Outcome Configuration chain."""
    cmoc_id: str = Field(
        ..., description="Unique CMOC ID, e.g. 'S001_CMOC1'"
    )
    context: Entity = Field(
        ..., description="The Context entity (E01-E06)"
    )
    intervention: Entity = Field(
        ..., description="The Intervention entity (E07-E18)"
    )
    mechanism_resource: Entity = Field(
        ..., description="The Mechanism Resource entity (E19)"
    )
    mechanism_response: Entity = Field(
        ..., description="The Mechanism Response entity (E20-E45) — student's INTERNAL reaction"
    )
    outcome: Entity = Field(
        ..., description="The Outcome entity (E21-E47)"
    )
    causal_chain: List[Relationship] = Field(
        default_factory=list,
        description="The causal relationships forming the C→I→M_R→M_Resp→O chain"
    )
    programme_theory_statement: RichmondPTS = Field(
        ..., description="Which of Richmond's 5 PTS this CMOC maps to"
    )
    is_negative: bool = Field(
        default=False,
        description="True if this CMOC describes a FAILED intervention or negative pathway (PTS4)"
    )
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0,
        description="Confidence score 0-1 for this CMOC extraction"
    )


# ── Multi-CMOC Extraction (per study) ───────────────────────────────────────

class CMOCExtraction(BaseModel):
    """All CMOCs extracted from a single study. A study may contain 1-3+ CMOCs."""
    record_id: str = Field(
        ..., description="The study ID (e.g. 'S001') this was extracted from"
    )
    cmocs: List[SingleCMOC] = Field(
        default_factory=list,
        description="List of all CMOC chains found in this study"
    )

    # Backward compatibility: expose flat entity/relationship lists
    @property
    def entities(self) -> list:
        """Flatten all entities from all CMOCs for backward compatibility."""
        result = []
        for cmoc in self.cmocs:
            result.extend([
                cmoc.context, cmoc.intervention,
                cmoc.mechanism_resource, cmoc.mechanism_response,
                cmoc.outcome
            ])
        return result

    @property
    def relationships(self) -> list:
        """Flatten all relationships from all CMOCs for backward compatibility."""
        result = []
        for cmoc in self.cmocs:
            result.extend(cmoc.causal_chain)
        return result

    model_config = {
        "json_schema_extra": {
            "example": {
                "record_id": "S001",
                "cmocs": [
                    {
                        "cmoc_id": "S001_CMOC1",
                        "context": {
                            "id": "E02",
                            "category": "Context",
                            "label": "students with 'low knowledge,' low clinical domain-specific knowledge, or an inability to use knowledge in a reasoning situation",
                            "extracted_text": "Year 3 medical students with limited diagnostic experience"
                        },
                        "intervention": {
                            "id": "E17",
                            "category": "Intervention",
                            "label": "listen to near-peer think aloud their reasoning with the use of prompts and examples",
                            "extracted_text": "students were instructed to self-explain while solving clinical cases"
                        },
                        "mechanism_resource": {
                            "id": "E19",
                            "category": "Mechanism_Resource",
                            "label": "multiple relevant resources",
                            "extracted_text": "clinical cases with diagnostic information"
                        },
                        "mechanism_response": {
                            "id": "E42",
                            "category": "Mechanism_Response",
                            "label": "develop understanding of their successes and failures and generate plans for improvement",
                            "extracted_text": "generating explanations activated biomedical knowledge links"
                        },
                        "outcome": {
                            "id": "E46",
                            "category": "Outcome",
                            "label": "increase in learning gain or outcomes, or increase in diagnostic accuracy",
                            "extracted_text": "better diagnostic performance on subsequent unfamiliar cases"
                        },
                        "causal_chain": [
                            {
                                "source_id": "E17",
                                "target_id": "E19",
                                "relation_type": "PROVIDES",
                                "evidence_quote": "self-explanation procedure provided multiple relevant learning resources"
                            },
                            {
                                "source_id": "E19",
                                "target_id": "E42",
                                "relation_type": "TRIGGERS",
                                "evidence_quote": "generating explanations activated biomedical knowledge links"
                            },
                            {
                                "source_id": "E42",
                                "target_id": "E46",
                                "relation_type": "LEADS_TO",
                                "evidence_quote": "better diagnostic performance on subsequent unfamiliar cases"
                            }
                        ],
                        "programme_theory_statement": "PTS1: Low knowledge students (E02)",
                        "confidence": 0.9
                    }
                ]
            }
        }
    }
