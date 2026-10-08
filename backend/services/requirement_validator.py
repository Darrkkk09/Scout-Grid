from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from models.search import ParsedRequirements


class LLMRequirementSchema(BaseModel):
    role: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    semantic_query: Optional[str] = None

    @field_validator("skills", mode="before")
    def validate_skills(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(s).strip() for s in v if str(s).strip()]
        if isinstance(v, str) and v.strip():
            return [s.strip() for s in v.split(",") if s.strip()]
        return []

    @field_validator("min_experience", "max_experience", mode="before")
    def validate_exp(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            val = float(v)
            return val if val >= 0 else None
        except (ValueError, TypeError):
            return None


class RequirementValidator:
    """
    Validation layer for LLM requirement extraction output.
    Ensures structural integrity, sensible experience ranges, and data type correctness.
    """

    @classmethod
    def validate_and_convert(cls, raw_data: Dict[str, Any]) -> Optional[ParsedRequirements]:
        if not isinstance(raw_data, dict):
            return None

        try:
            validated = LLMRequirementSchema(**raw_data)

            # Additional logical validation
            min_exp = validated.min_experience
            max_exp = validated.max_experience
            if min_exp is not None and max_exp is not None and min_exp > max_exp:
                # Swapped bounds validation correction
                validated.min_experience, validated.max_experience = max_exp, min_exp

            # Convert to standard ParsedRequirements model
            return ParsedRequirements(
                skills=validated.skills,
                location=validated.location if validated.location and str(validated.location).strip() else None,
                min_experience=validated.min_experience,
                max_experience=validated.max_experience,
                job_title=validated.role if validated.role and str(validated.role).strip() else None,
                semantic_query=validated.semantic_query if validated.semantic_query and str(validated.semantic_query).strip() else None,
            )
        except Exception:
            return None
