from pydantic import BaseModel, Field , ConfigDict
from typing import Literal


class PromoEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    hook_strength: int = Field(
        ge=1, le=5,
        description="Strength of the opening hook"
    )

    cliffhanger_strength: int = Field(
        ge=1, le=5,
        description="Strength of the ending cliffhanger"
    )

    standalone_comprehensibility: int = Field(
        ge=1, le=5,
        description="How understandable the promo is to a new viewer"
    )

    emotional_impact: int = Field(
        ge=1, le=5,
        description="Emotional intensity of the promo"
    )

    narrative_coherence: int = Field(
        ge=1, le=5,
        description="How well the events connect"
    )

    duration_suitability: int = Field(
        ge=1, le=5,
        description="Whether the selected duration is suitable"
    )

    recommendation: Literal[
        "strong",
        "moderate",
        "weak"
    ]

    hook_explanation: str

    cliffhanger_explanation: str

    standalone_explanation: str

    why_it_works: str

    weaknesses: list[str]

    missing_context: list[str]

    evidence_from_script: list[str]