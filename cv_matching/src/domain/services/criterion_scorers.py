"""
Criterion Scorers

One scorer per criterion. Each builds a focused prompt and asks the LLM for a
single 0-100 score, so a criterion can be re-tuned without disturbing the
others and all six can be scored concurrently.
"""

import logging

from cv_matching.src.domain.entities.matching import (
    BackgroundScoreResult,
    CriterionScoreResult,
    ExperienceScoreResult,
    LocationScoreResult,
    ProjectCountScoreResult,
    SkillsScoreResult,
    TitleRoleScoreResult,
)
from cv_matching.src.domain.entities.resume import ResumeData
from cv_matching.src.domain.ports.llm_service import ILLMService
from cv_matching.src.domain.services import resume_profile

logger = logging.getLogger(__name__)


class CriterionScorerError(Exception):
    """Raised when a criterion could not be scored."""


_EXPERIENCE_PROMPT = """You are an expert at evaluating work experience.
Analyze the candidate's total years of experience against the job description requirements.

Scoring guidelines:
- 100: Candidate has significantly more experience than required (e.g., 8+ years when 3+ required)
- 80-90: Meets or slightly exceeds requirement
- 60-70: Close to requirement (e.g., 2.5 years when 3 required)
- 40-50: Below requirement but has some relevant experience
- 0-30: Fresh graduate or significantly below requirement

The total is computed from the work history and given to you; overlapping positions are already
counted once. If the JD states no requirement, assume a 3+ years standard."""

_LOCATION_PROMPT = """You are an expert at evaluating location match.
Analyze if the candidate's location matches the job location requirements.

Scoring guidelines:
- 100: Perfect match, or the JD lists the candidate's city among its locations, or remote/hybrid
- 70: Same country, different city, and the JD does not insist on being on-site
- 40: Different city and the JD requires on-site work, but the candidate signals relocation
- 20: Different country, no indication of relocation
- 50: Location cannot be determined from the CV

A CV with no address is missing information, not a bad match - score it 50 and say the
location is unknown. Do not treat it as worse than a candidate who is genuinely in the
wrong city.

Set `onsite_conflict` to true only when all three hold: the JD requires being on-site at a
named location, the candidate is somewhere else, and nothing in the CV suggests they would
move. A JD listing several cities is satisfied if the candidate is in any of them.

Check for keywords: remote, hybrid, onsite, relocation, willing to move."""

_SKILLS_PROMPT = """You are an expert at evaluating technical skills match.
Compare the candidate's technical skills against job requirements.

Scoring guidelines:
- 100: Has ALL required skills + preferred skills
- 80-90: Has all required skills, missing some preferred
- 60-70: Has most required skills (70-80%)
- 40-50: Has some required skills (50-60%)
- 20-30: Has few required skills (<50%)
- 0-10: Missing most critical skills

Focus on: programming languages, frameworks, tools, platforms, methodologies.
List matched_skills, missing_skills, and extra_skills."""

_BACKGROUND_PROMPT = """You are an expert at evaluating educational background.
Assess if the candidate's education matches job requirements.

Scoring guidelines:
- 100: Top university + relevant degree/major
- 80-90: Good university + relevant degree
- 60-70: Average university + relevant degree OR top university + unrelated degree
- 40-50: Relevant degree but unknown university
- 20-30: Unrelated degree or vocational training
- 0-10: No degree when required

Consider: institution reputation, degree level (PhD > Master > Bachelor), field relevance."""

_PROJECTS_PROMPT = """You are an expert at identifying relevant project experience.
Count how many projects the candidate has done that are DIRECTLY relevant to this job.

Scoring guidelines:
- 100: 5+ highly relevant projects
- 80-90: 3-4 relevant projects
- 60-70: 2 relevant projects
- 40-50: 1 relevant project
- 20-30: No direct projects but related work
- 0-10: No relevant project experience

Be strict - only count projects that match the JD's domain/technology closely.
List the names/descriptions of relevant projects found."""

_TITLE_PROMPT = """You are an expert at evaluating role seniority.
Compare the candidate's most recent title/role level against the JD's expected level.

Scoring guidelines:
- 100: Exact level match (e.g., Senior for Senior role)
- 80-90: One level higher (Senior applying for Mid role)
- 60-70: One level lower but close (Mid applying for Senior with strong experience)
- 40-50: Two levels different
- 20-30: Significantly junior for the role
- 0-10: Role level completely mismatched

Levels: Lead/Principal > Senior > Mid/Intermediate > Junior/Entry"""


class CriterionScorers:
    """Scores a candidate on one criterion at a time."""

    def __init__(self, llm_service: ILLMService):
        self._llm_service = llm_service

    async def _score(
        self,
        criterion: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[CriterionScoreResult],
    ) -> CriterionScoreResult:
        try:
            result = await self._llm_service.analyze_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
                temperature=0,
            )
        except Exception as exc:
            raise CriterionScorerError(f"Could not score '{criterion}': {exc}") from exc

        logger.info("[%s] Score: %d/100", criterion, result.score)
        return result

    async def score_years_of_experience(
        self, jd_text: str, resume: ResumeData
    ) -> ExperienceScoreResult:
        total_years = resume_profile.total_experience_years(resume)
        user_prompt = f"""Job Description:
{jd_text}

Candidate's Work Experience:
{resume_profile.format_work_experience(resume)}

Candidate has approximately {total_years:.1f} years of total work experience.
Score this candidate's years of experience (0-100) and explain."""

        return await self._score("YearsExp", _EXPERIENCE_PROMPT, user_prompt, ExperienceScoreResult)

    async def score_location(self, jd_text: str, resume: ResumeData) -> LocationScoreResult:
        user_prompt = f"""Job Description:
{jd_text}

Candidate's Location Info:
- Address: {resume.address or "Not provided"}
- Tags: {resume_profile.format_list(resume.tags, "None")}

Score the location match (0-100) and explain."""

        return await self._score("Location", _LOCATION_PROMPT, user_prompt, LocationScoreResult)

    async def score_skills(self, jd_text: str, resume: ResumeData) -> SkillsScoreResult:
        skills = resume_profile.collect_tech_skills(resume)
        user_prompt = f"""Job Description:
{jd_text}

Candidate's Technical Skills:
{resume_profile.format_list(skills, "No clear technical skills listed")}

Candidate's Work Experience:
{resume_profile.format_work_experience(resume)}

Candidate's Projects:
{resume_profile.format_project_section(resume)}

Score the skills match (0-100). Provide:
- score (0-100)
- explanation
- matched_skills: skills in both JD and resume
- missing_skills: required in JD but not in resume
- extra_skills: in resume but not mentioned in JD (bonus skills)"""

        return await self._score("Skills", _SKILLS_PROMPT, user_prompt, SkillsScoreResult)

    async def score_background(self, jd_text: str, resume: ResumeData) -> BackgroundScoreResult:
        user_prompt = f"""Job Description:
{jd_text}

Candidate's Education:
{resume_profile.format_education(resume)}

Score the educational background (0-100) and explain."""

        return await self._score(
            "Background", _BACKGROUND_PROMPT, user_prompt, BackgroundScoreResult
        )

    async def score_relevant_projects(
        self, jd_text: str, resume: ResumeData
    ) -> ProjectCountScoreResult:
        user_prompt = f"""Job Description:
{jd_text}

Candidate's Work Experience & Projects:
{resume_profile.format_projects(resume)}

Count and score the number of relevant projects (0-100).
Provide: score, explanation, relevant_project_count, relevant_projects (list of project names/descriptions)."""

        return await self._score("Projects", _PROJECTS_PROMPT, user_prompt, ProjectCountScoreResult)

    async def score_title_role(self, jd_text: str, resume: ResumeData) -> TitleRoleScoreResult:
        user_prompt = f"""Job Description:
{jd_text}

Candidate's Most Recent Title: {resume_profile.latest_title(resume) or "Not specified"}

All Work Experience:
{resume_profile.format_work_experience(resume)}

Score the title/role level match (0-100) and explain."""

        return await self._score("Title", _TITLE_PROMPT, user_prompt, TitleRoleScoreResult)
