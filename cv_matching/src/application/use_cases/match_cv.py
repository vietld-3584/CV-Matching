"""
Match CV Use Case

Reads a CV file and extracts it into structured resume data. When a job
description is supplied it goes on to score the candidate against it on six
weighted criteria and summarise the fit; without one it stops after the
extraction, which is a complete answer on its own.
"""

import asyncio
import json
import logging
import time
from typing import Optional

from pydantic import BaseModel, Field

from cv_matching.src.domain.entities.matching import (
    Criterion,
    CriterionScore,
    CriterionScoreResult,
    ImprovementArea,
    LocationScoreResult,
    MatchingResult,
    RecommendationAction,
    SkillOrKeyword,
    StrengthArea,
    recommend,
    resolve_weights,
)
from cv_matching.src.domain.entities.resume import ResumeData
from cv_matching.src.domain.ports.document_parser import IDocumentParser
from cv_matching.src.domain.ports.llm_service import ILLMService
from cv_matching.src.domain.services.criterion_scorers import (
    CriterionScorerError,
    CriterionScorers,
)

logger = logging.getLogger(__name__)


class MatchCvError(Exception):
    """Raised when the CV could not be matched against the job description."""


_EXTRACTION_SYSTEM_PROMPT = (
    "You are a resume parsing assistant. Extract structured information accurately. "
    "Never invent details that are not in the text."
)

_EXTRACTION_PROMPT = """Extract all resume information from the provided text.

Important guidelines:
- Extract name and email (required fields). If not found, use "Unknown" for name and "unknown@example.com" for email
- Extract tags from the listed categories
- For working experience: use "Present" for current positions
- Format dates as YYYY-MM for work experience, YYYY for education
- Extract all social profiles with platform name and full URL
- List technical and non-technical skills separately
- Include languages with proficiency levels if available
- If the CV has a projects section (Projects, Dự án, Personal Projects), extract every
  project into `projects` with its tech stack. Keep them there rather than merging them
  into working_experience, and do not stop early when the section is long
- Collect tech_skills from the whole document, including the technologies named inside
  work experience and inside project entries

Resume text:
{resume_text}"""

_INSIGHTS_SYSTEM_PROMPT = """You are an expert HR analyst.
Given the criterion scores for a resume-JD match, provide:
1. overall_summary: A concise paragraph about the candidate's fit
2. strengths: 1-3 key strengths (each with title, description, keywords)
3. areas_to_address: 1-3 gaps/weaknesses (each with title, description, suggestions_for_improvement, keywords)
4. matched_keywords_and_skills: 5-10 important skills showing presence in resume/JD and relevance

Base every statement on the resume and the job description given to you - the scores explain
what was already decided, they are not something to re-litigate."""


class InsightsResult(BaseModel):
    """Narrative half of the report, generated once the scores are known."""

    overall_summary: str
    strengths: list[StrengthArea] = Field(default_factory=list)
    areas_to_address: list[ImprovementArea] = Field(default_factory=list)
    matched_keywords_and_skills: list[SkillOrKeyword] = Field(default_factory=list)


class CvAnalysis(BaseModel):
    """Everything one run of this use case produces.

    The CV is always parsed, so `resume` is always filled in. `matching` is
    present only when the caller supplied a job description to match against.
    """

    resume: ResumeData
    matching: Optional[MatchingResult] = None
    warnings: list[str] = Field(default_factory=list)


class MatchCvUseCase:
    def __init__(
        self,
        llm_service: ILLMService,
        document_parser: IDocumentParser,
        criterion_scorers: CriterionScorers,
    ):
        self._llm_service = llm_service
        self._document_parser = document_parser
        self._scorers = criterion_scorers

    async def execute(
        self,
        file_path: str,
        jd_text: Optional[str] = None,
        custom_weights: Optional[dict[str, float]] = None,
    ) -> CvAnalysis:
        # Raises InvalidWeightsError before any LLM call is paid for. Checked even
        # when there is no JD to apply them to, so a misspelled criterion is reported
        # rather than silently accepted.
        weights = resolve_weights(custom_weights)

        started = time.monotonic()
        resume = await self._extract_resume(file_path)
        warnings: list[str] = []
        if not resume.working_experience:
            warnings.append("No work experience could be read from the CV.")

        # Without a JD there is nothing to score against, and the seven scoring calls
        # would be paid for to produce nothing. The extracted CV is the whole answer.
        if not jd_text or not jd_text.strip():
            logger.info(
                "[Matching] Extracted %r in %dms - no job description given, no scoring done",
                resume.name,
                int((time.monotonic() - started) * 1000),
            )
            return CvAnalysis(resume=resume, warnings=warnings)

        try:
            criterion_scores, raw_results = await self._score_all_criteria(jd_text, resume, weights)
        except CriterionScorerError as exc:
            # A missing criterion cannot be scored as 0: Skills alone carries 35% of the
            # result, so a silent 0 would read as a genuine rejection.
            logger.error("[Matching] Criterion scoring failed: %s", exc)
            raise MatchCvError("Could not score the CV against the job description.") from exc

        match_score = round(sum(score.weighted_score for score in criterion_scores))
        recommendation = recommend(match_score)

        # Location is a constraint, not a few points. Adding it to the total let a candidate
        # in the wrong city out-score the gap on skills alone, so instead a genuine on-site
        # conflict blocks the automatic shortlist and says why.
        location = raw_results.get(Criterion.LOCATION)
        onsite_conflict = isinstance(location, LocationScoreResult) and location.onsite_conflict
        if onsite_conflict:
            where = location.candidate_location or "another location"
            needed = location.required_location or "the job's location"
            warnings.append(
                f"On-site role in {needed}, but the candidate appears to be in {where} "
                f"with no sign of relocating."
            )
            if recommendation is RecommendationAction.SHORTLIST:
                recommendation = RecommendationAction.REVIEW_CAREFULLY

        insights = await self._generate_insights(jd_text, resume, criterion_scores)
        if insights is None:
            warnings.append("Could not generate detailed insights due to an LLM error.")

        matching = MatchingResult(
            match_score=match_score,
            overall_summary=(
                insights.overall_summary
                if insights
                else f"Match score: {match_score}/100 based on weighted criteria analysis."
            ),
            criterion_scores=criterion_scores,
            recommendation=recommendation,
            recommendation_reason=self._recommendation_reason(
                recommendation, criterion_scores, onsite_conflict
            ),
            strengths=insights.strengths if insights else [],
            areas_to_address=insights.areas_to_address if insights else [],
            matched_keywords_and_skills=insights.matched_keywords_and_skills if insights else [],
            warnings=warnings,
        )

        logger.info(
            "[Matching] Done in %dms - candidate=%r, weighted score=%d/100, recommendation=%s",
            int((time.monotonic() - started) * 1000),
            resume.name,
            matching.match_score,
            matching.recommendation.value,
        )
        return CvAnalysis(resume=resume, matching=matching, warnings=warnings)

    async def _extract_resume(self, file_path: str) -> ResumeData:
        text = await self._document_parser.extract_text(file_path)
        if not text or not text.strip():
            raise MatchCvError("The uploaded CV appears to be empty.")

        logger.info("[Matching] Extracting resume from %d chars", len(text))
        try:
            resume: ResumeData = await self._llm_service.analyze_text(
                system_prompt=_EXTRACTION_SYSTEM_PROMPT,
                user_prompt=_EXTRACTION_PROMPT.format(resume_text=text),
                response_model=ResumeData,
                temperature=0,
            )
        except Exception as exc:
            logger.exception("[Matching] Resume extraction failed: %s", exc)
            raise MatchCvError("Could not parse the CV.") from exc

        if not resume.name.strip():
            resume.name = "Unknown"
        if not resume.email.strip():
            resume.email = "unknown@example.com"
        if not resume.tags:
            resume.tags = ["other"]
        return resume

    async def _score_all_criteria(
        self,
        jd_text: str,
        resume: ResumeData,
        weights: dict[Criterion, float],
    ) -> tuple[list[CriterionScore], dict[Criterion, CriterionScoreResult]]:
        """Score the six criteria concurrently - they share no state.

        Returns the weighted scores plus the raw per-criterion results, which carry
        fields the weighted view drops - notably the location conflict flag.
        """
        scorers = {
            Criterion.YEARS_OF_EXPERIENCE: self._scorers.score_years_of_experience,
            Criterion.LOCATION: self._scorers.score_location,
            Criterion.SKILLS: self._scorers.score_skills,
            Criterion.BACKGROUND: self._scorers.score_background,
            Criterion.RELEVANT_PROJECT_COUNT: self._scorers.score_relevant_projects,
            Criterion.TITLE_ROLE: self._scorers.score_title_role,
        }

        logger.info("[Matching] Scoring %d criteria in parallel...", len(scorers))
        results: list[CriterionScoreResult] = await asyncio.gather(
            *(scorer(jd_text, resume) for scorer in scorers.values())
        )

        scores = [
            CriterionScore(
                criterion=criterion,
                criterion_name=criterion.label,
                score=result.score,
                weight=weights[criterion],
                weighted_score=round(result.score * weights[criterion] / 100.0, 2),
                explanation=result.explanation,
            )
            for criterion, result in zip(scorers, results)
        ]
        logger.info(
            "[Matching] Criteria scored: %s",
            ", ".join(f"{score.criterion_name}={score.score}" for score in scores),
        )
        return scores, dict(zip(scorers, results))

    async def _generate_insights(
        self,
        jd_text: str,
        resume: ResumeData,
        criterion_scores: list[CriterionScore],
    ) -> Optional[InsightsResult]:
        """Summarise the match. Returns None when the LLM call fails.

        The scores are the substance of the report and they are already in hand,
        so a failure here is downgraded to a warning rather than losing them.
        """
        criteria_summary = "\n".join(
            f"- {score.criterion_name}: {score.score}/100 "
            f"(weight: {score.weight}%) - {score.explanation}"
            for score in criterion_scores
        )
        resume_json = json.dumps(resume.model_dump(), indent=2, ensure_ascii=False)

        user_prompt = f"""Job Description:
{jd_text}

Candidate Resume:
{resume_json}

Criterion Scores:
{criteria_summary}

Provide comprehensive insights."""

        try:
            return await self._llm_service.analyze_text(
                system_prompt=_INSIGHTS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=InsightsResult,
                temperature=0,
            )
        except Exception as exc:
            logger.warning("[Matching] Failed to generate insights: %s", exc)
            return None

    @staticmethod
    def _recommendation_reason(
        recommendation: RecommendationAction,
        criterion_scores: list[CriterionScore],
        onsite_conflict: bool = False,
    ) -> str:
        if onsite_conflict:
            return (
                "The candidate matches the role on merit but is not in the location this "
                "on-site job requires. Confirm they can work from there before proceeding."
            )
        if recommendation is RecommendationAction.SHORTLIST:
            return "Strong overall match with good alignment across most criteria."
        if recommendation is RecommendationAction.REVIEW_CAREFULLY:
            # Only criteria that actually count toward the score can explain it.
            weak = [
                score.criterion_name
                for score in criterion_scores
                if score.score < 50 and score.weight > 0
            ]
            if weak:
                return f"Moderate fit. Needs improvement in: {', '.join(weak[:2])}."
            return "Moderate overall fit. Review carefully before deciding."
        return "Significant gaps in multiple criteria. Not recommended for this role."
