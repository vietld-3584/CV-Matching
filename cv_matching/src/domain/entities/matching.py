"""
CV Matching Domain Entities

The six weighted criteria a candidate is scored on, the per-criterion result
models the LLM fills in, and the aggregated matching result.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


def _ensure_list(value: Any) -> list:
    return [] if value is None else value


class InvalidWeightsError(ValueError):
    """Raised when the caller supplies weights that cannot be applied."""


class RecommendationAction(str, Enum):
    SHORTLIST = "SHORTLIST"
    REVIEW_CAREFULLY = "REVIEW_CAREFULLY"
    REJECT = "REJECT"


SHORTLIST_THRESHOLD = 70
REVIEW_THRESHOLD = 40


class Criterion(str, Enum):
    """A scoring criterion. The value is the stable key clients send weights under."""

    YEARS_OF_EXPERIENCE = "years_of_experience"
    LOCATION = "location"
    SKILLS = "skills"
    BACKGROUND = "background"
    RELEVANT_PROJECT_COUNT = "relevant_project_count"
    TITLE_ROLE = "title_role"

    @property
    def label(self) -> str:
        """Human readable name, shown in the API response and in prompts."""
        return _CRITERION_LABELS[self]


_CRITERION_LABELS: dict["Criterion", str] = {
    Criterion.YEARS_OF_EXPERIENCE: "Years of Experience",
    Criterion.LOCATION: "Location",
    Criterion.SKILLS: "Skills",
    Criterion.BACKGROUND: "Background (University)",
    Criterion.RELEVANT_PROJECT_COUNT: "Relevant Project Count",
    Criterion.TITLE_ROLE: "Title/Role",
}

#: Default weighting, in percent. Sums to 100.
#:
#: Location carries no weight by default. Measured against 50 CVs over 10 JDs it scored
#: an AUC of 0.41-0.53 across six different models - it does not move when the JD changes,
#: because every posting is a Vietnam-based role and every candidate is in Vietnam. What it
#: did do was award a flat 100 to 85% of candidates and a 0 to whoever left an address off
#: their CV, which is a fact about CV formatting rather than about fit. It is still scored
#: and reported, so a recruiter can see it; it just no longer moves the total. Callers who
#: hire across regions can weight it back up through `custom_weights`.
DEFAULT_WEIGHTS: dict[Criterion, float] = {
    Criterion.YEARS_OF_EXPERIENCE: 15.0,
    Criterion.LOCATION: 0.0,
    Criterion.SKILLS: 40.0,
    Criterion.BACKGROUND: 10.0,
    Criterion.RELEVANT_PROJECT_COUNT: 25.0,
    Criterion.TITLE_ROLE: 10.0,
}


def resolve_weights(custom_weights: Optional[dict[str, float]] = None) -> dict[Criterion, float]:
    """Merge caller supplied weights over the defaults and rescale them to 100%.

    Callers may override any subset of the criteria; the untouched ones keep
    their default weight. The result is always normalised so that
    `match_score` stays on a 0-100 scale whatever the caller sends.

    Raises:
        InvalidWeightsError: on unknown criterion keys, negative weights, or a
            set of weights that adds up to zero. Silently ignoring those hides
            a client typo behind a plausible looking score.
    """
    if not custom_weights:
        return dict(DEFAULT_WEIGHTS)

    unknown = sorted(set(custom_weights) - {criterion.value for criterion in Criterion})
    if unknown:
        raise InvalidWeightsError(
            f"Unknown criteria: {', '.join(unknown)}. "
            f"Valid keys: {', '.join(criterion.value for criterion in Criterion)}."
        )

    merged: dict[Criterion, float] = {}
    for criterion, default in DEFAULT_WEIGHTS.items():
        weight = custom_weights.get(criterion.value)
        if weight is None:
            merged[criterion] = default
            continue
        if weight < 0:
            raise InvalidWeightsError(f"Weight for '{criterion.value}' must not be negative.")
        merged[criterion] = float(weight)

    total = sum(merged.values())
    if total <= 0:
        raise InvalidWeightsError("At least one criterion must carry a weight greater than 0.")

    factor = 100.0 / total
    return {criterion: round(weight * factor, 2) for criterion, weight in merged.items()}


class CriterionScore(BaseModel):
    """One criterion's contribution to the overall match score."""

    criterion: Criterion
    criterion_name: str = Field(..., description="Human readable criterion name")
    score: int = Field(..., ge=0, le=100, description="Score from 0 to 100")
    weight: float = Field(..., ge=0, le=100, description="Weight percentage for this criterion")
    weighted_score: float = Field(..., description="score * weight / 100")
    explanation: str = Field(..., description="Brief reason for the score")


# --- Per-criterion LLM response models -------------------------------------


class CriterionScoreResult(BaseModel):
    """Fields every scorer returns."""

    score: int = Field(..., ge=0, le=100)
    explanation: str


class ExperienceScoreResult(CriterionScoreResult):
    candidate_years: Optional[float] = Field(None, description="Số năm kinh nghiệm của ứng viên")
    required_years: Optional[float] = Field(None, description="Số năm yêu cầu trong JD")


class LocationScoreResult(CriterionScoreResult):
    candidate_location: Optional[str] = None
    required_location: Optional[str] = None
    is_remote: bool = Field(default=False, description="JD có cho phép remote không")
    onsite_conflict: bool = Field(
        default=False,
        description=(
            "True ONLY when the JD requires working on-site at a specific location, the "
            "candidate lives somewhere else, and the CV shows no sign they would relocate. "
            "False when the JD allows remote/hybrid, when it lists the candidate's city among "
            "its locations, or when the candidate's location is simply unknown - an absent "
            "address is missing information, not a conflict."
        ),
    )


class SkillsScoreResult(CriterionScoreResult):
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    extra_skills: list[str] = Field(default_factory=list)

    @field_validator("matched_skills", "missing_skills", "extra_skills", mode="before")
    @classmethod
    def ensure_skill_lists(cls, value: Any) -> list:
        return _ensure_list(value)


class BackgroundScoreResult(CriterionScoreResult):
    candidate_university: Optional[str] = None
    candidate_degree: Optional[str] = None
    required_degree: Optional[str] = None


class ProjectCountScoreResult(CriterionScoreResult):
    relevant_project_count: int = Field(default=0)
    relevant_projects: list[str] = Field(
        default_factory=list, description="Tên các project liên quan"
    )

    @field_validator("relevant_projects", mode="before")
    @classmethod
    def ensure_projects_list(cls, value: Any) -> list:
        return _ensure_list(value)


class TitleRoleScoreResult(CriterionScoreResult):
    candidate_level: Optional[str] = Field(None, description="e.g., Senior, Mid, Junior, Lead")
    required_level: Optional[str] = None


# --- Aggregated result ------------------------------------------------------


class StrengthArea(BaseModel):
    title: str
    description: str
    keywords: list[str] = Field(default_factory=list)

    @field_validator("keywords", mode="before")
    @classmethod
    def ensure_keywords_list(cls, value: Any) -> list:
        return _ensure_list(value)


class ImprovementArea(BaseModel):
    title: str
    description: str
    suggestions_for_improvement: str = Field(
        ..., description="Actionable suggestions for the candidate or interviewer"
    )
    keywords: list[str] = Field(default_factory=list)

    @field_validator("keywords", mode="before")
    @classmethod
    def ensure_keywords_list(cls, value: Any) -> list:
        return _ensure_list(value)


class SkillOrKeyword(BaseModel):
    keyword: str
    resume_presence: bool
    job_description_presence: bool
    relevance_score: Optional[float] = Field(
        None, ge=0, le=1, description="Relevance score from 0 to 1"
    )


class MatchingResult(BaseModel):
    match_score: int = Field(
        ..., ge=0, le=100, description="Weighted sum of the six criterion scores"
    )
    overall_summary: str = Field(..., description="Summary paragraph of the overall fit")
    criterion_scores: list[CriterionScore] = Field(
        ..., description="One entry per criterion, in the order declared by Criterion"
    )
    recommendation: RecommendationAction
    recommendation_reason: Optional[str] = Field(
        None, description="Brief justification for the recommendation"
    )
    strengths: list[StrengthArea] = Field(
        default_factory=list, description="Key areas where the candidate excels for this role"
    )
    areas_to_address: list[ImprovementArea] = Field(
        default_factory=list, description="Gaps or weaknesses relative to the JD"
    )
    matched_keywords_and_skills: list[SkillOrKeyword] = Field(
        default_factory=list,
        description="Important skills/keywords from both resume and JD, with presence in each",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Issues found during the analysis. Empty when nothing went wrong.",
    )

    @field_validator("warnings", mode="before")
    @classmethod
    def ensure_warnings_list(cls, value: Any) -> list:
        return _ensure_list(value)


def recommend(match_score: int) -> RecommendationAction:
    if match_score >= SHORTLIST_THRESHOLD:
        return RecommendationAction.SHORTLIST
    if match_score >= REVIEW_THRESHOLD:
        return RecommendationAction.REVIEW_CAREFULLY
    return RecommendationAction.REJECT
