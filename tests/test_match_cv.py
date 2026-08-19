import asyncio
from datetime import date

import pytest

from cv_matching.src.application.dtos.matching_dtos import (
    ExtractedCvDTO,
    MatchCvResponse,
    MatchingResultDTO,
)
from cv_matching.src.application.use_cases.match_cv import (
    InsightsResult,
    MatchCvError,
    MatchCvUseCase,
)
from cv_matching.src.domain.entities.matching import (
    Criterion,
    CriterionScore,
    DEFAULT_WEIGHTS,
    InvalidWeightsError,
    LocationScoreResult,
    RecommendationAction,
    SHORTLIST_THRESHOLD,
    resolve_weights,
)
from cv_matching.src.domain.entities.resume import (
    Education,
    LanguageSkill,
    Project,
    ResumeData,
    WorkExperience,
)
from cv_matching.src.domain.services import resume_profile
from cv_matching.src.domain.services.criterion_scorers import CriterionScorers

TODAY = date(2026, 8, 1)


def _resume(**overrides) -> ResumeData:
    values = {
        "name": "Nguyen Van A",
        "email": "a@example.com",
        "tags": ["HN", "hust"],
        "address": "Hanoi, Vietnam",
        "tech_skills": ["Python", "FastAPI"],
        "education": [Education(institution="HUST", degree="Bachelor", field="Computer Science")],
        "working_experience": [
            WorkExperience(
                company="Sun Asterisk",
                position="Senior Engineer",
                start_date="2022-01",
                end_date="Present",
                achievements=["Built a RAG pipeline with LangChain"],
            )
        ],
    }
    values.update(overrides)
    return ResumeData(**values)


class FakeLLMService:
    """Returns a canned instance of whatever response_model is asked for."""

    def __init__(self, *, score: int = 80, fail_on: tuple[type, ...] = ()):
        self.score = score
        self.fail_on = fail_on
        self.calls: list[str] = []

    async def analyze_text(self, *, response_model, **kwargs):
        self.calls.append(response_model.__name__)
        if response_model in self.fail_on:
            raise RuntimeError(f"LLM exploded on {response_model.__name__}")
        if response_model is ResumeData:
            return _resume()
        if response_model is InsightsResult:
            return InsightsResult(overall_summary="Good fit.")
        return response_model(score=self.score, explanation="because")


class FakeDocumentParser:
    def __init__(self, text: str = "CV text"):
        self.text = text

    async def extract_text(self, file_path: str, model_id=None) -> str:
        return self.text


class FresherLLM(FakeLLMService):
    """Extracts a CV with no job history - the candidate is a new graduate."""

    async def analyze_text(self, *, response_model, **kwargs):
        if response_model is ResumeData:
            self.calls.append(response_model.__name__)
            return _resume(working_experience=[])
        return await FakeLLMService.analyze_text(self, response_model=response_model, **kwargs)


def _use_case(llm: FakeLLMService, parser: FakeDocumentParser = None) -> MatchCvUseCase:
    return MatchCvUseCase(
        llm_service=llm,
        document_parser=parser or FakeDocumentParser(),
        criterion_scorers=CriterionScorers(llm),
    )


def _match(llm: FakeLLMService, **kwargs):
    """Run the use case and hand back the matching half, which most tests are about."""
    return asyncio.run(_use_case(llm).execute(**kwargs)).matching


# --- weights ---------------------------------------------------------------


def test_resolve_weights_defaults_to_the_house_weighting():
    assert resolve_weights(None) == DEFAULT_WEIGHTS
    assert sum(DEFAULT_WEIGHTS.values()) == 100


def test_resolve_weights_rescales_partial_overrides_back_to_100():
    weights = resolve_weights({"skills": 70})

    # Untouched criteria keep their relative default weighting...
    assert weights[Criterion.BACKGROUND] == weights[Criterion.TITLE_ROLE]
    # ...and the whole set still totals 100 so match_score stays on a 0-100 scale.
    assert round(sum(weights.values())) == 100
    assert weights[Criterion.SKILLS] > DEFAULT_WEIGHTS[Criterion.SKILLS]


def test_location_carries_no_default_weight():
    # It scored an AUC of 0.41-0.53 across six models: it does not react to the JD,
    # it just handed a flat 100 to anyone who printed an address on their CV.
    assert DEFAULT_WEIGHTS[Criterion.LOCATION] == 0
    assert resolve_weights(None)[Criterion.LOCATION] == 0


def test_location_can_be_weighted_back_up_for_cross_region_hiring():
    weights = resolve_weights({"location": 20})

    assert weights[Criterion.LOCATION] > 0
    assert round(sum(weights.values())) == 100


def test_resolve_weights_lets_a_criterion_be_switched_off():
    weights = resolve_weights({"location": 0})

    assert weights[Criterion.LOCATION] == 0
    assert round(sum(weights.values())) == 100


def test_resolve_weights_rejects_a_misspelled_criterion():
    # Silently ignoring the typo would hand back a plausible score computed
    # from weights the caller never asked for.
    with pytest.raises(InvalidWeightsError, match="skill"):
        resolve_weights({"skill": 50})


@pytest.mark.parametrize("weights", [{"skills": -1}, {key.value: 0 for key in Criterion}])
def test_resolve_weights_rejects_unusable_weightings(weights):
    with pytest.raises(InvalidWeightsError):
        resolve_weights(weights)


# --- experience arithmetic -------------------------------------------------


def test_total_experience_counts_the_end_month_as_worked():
    resume = _resume(
        working_experience=[
            WorkExperience(company="A", position="Dev", start_date="2024-01", end_date="2024-12")
        ]
    )
    assert resume_profile.total_experience_years(resume, today=TODAY) == 1.0


def test_total_experience_counts_overlapping_roles_once():
    # A day job with a concurrent side contract is one year of experience,
    # not two - summing the entries independently would double count it.
    resume = _resume(
        working_experience=[
            WorkExperience(company="A", position="Dev", start_date="2024-01", end_date="2024-12"),
            WorkExperience(
                company="B", position="Freelancer", start_date="2024-06", end_date="2024-12"
            ),
        ]
    )
    assert resume_profile.total_experience_years(resume, today=TODAY) == 1.0


def test_total_experience_sums_separate_periods():
    resume = _resume(
        working_experience=[
            WorkExperience(company="A", position="Dev", start_date="2022-01", end_date="2022-12"),
            WorkExperience(company="B", position="Dev", start_date="2024-01", end_date="2024-12"),
        ]
    )
    assert resume_profile.total_experience_years(resume, today=TODAY) == 2.0


def test_total_experience_reads_present_as_today():
    resume = _resume(
        working_experience=[
            WorkExperience(company="A", position="Dev", start_date="2025-08", end_date="Present")
        ]
    )
    assert resume_profile.total_experience_years(resume, today=TODAY) == 1.0


@pytest.mark.parametrize("start,end", [("not a date", "2024-12"), ("2024-01", "sometime")])
def test_total_experience_skips_undatable_entries(start, end):
    # Guessing a duration for an unreadable entry is what inflated the old score.
    resume = _resume(
        working_experience=[
            WorkExperience(company="A", position="Dev", start_date=start, end_date=end)
        ]
    )
    assert resume_profile.total_experience_years(resume, today=TODAY) == 0.0


def test_latest_title_uses_dates_not_list_order():
    resume = _resume(
        working_experience=[
            WorkExperience(
                company="A", position="Junior", start_date="2020-01", end_date="2021-12"
            ),
            WorkExperience(company="B", position="Lead", start_date="2022-01", end_date="Present"),
        ]
    )
    assert resume_profile.latest_title(resume, today=TODAY) == "Lead"


def test_collect_tech_skills_merges_listed_and_mentioned_skills():
    resume = _resume(tech_skills=["Python"])

    skills = resume_profile.collect_tech_skills(resume)

    assert "Python" in skills  # listed on the CV
    assert "LangChain" in skills  # only named inside an achievement
    assert len(skills) == len({skill.casefold() for skill in skills})


# --- the projects section --------------------------------------------------


def _project(**overrides) -> Project:
    values = {
        "name": "Mosan Ewallet",
        "role": "Mobile + Backend Dev",
        "description": "E-wallet app for a telco client",
        "tech_stack": ["React Native", "Java SpringBoot", "Oracle"],
        "customer": "Viettel Digital",
        "team_size": "14",
    }
    values.update(overrides)
    return Project(**values)


def test_collect_tech_skills_reads_the_projects_section():
    # A dev CV routinely names its strongest stack only under Projects; before this
    # was extracted, those technologies never reached the skills scorer at all.
    resume = _resume(tech_skills=["Python"], projects=[_project()])

    skills = resume_profile.collect_tech_skills(resume)

    assert "Oracle" in skills
    assert "React Native" in skills


def test_format_projects_covers_both_the_job_history_and_the_projects_section():
    text = resume_profile.format_projects(_resume(projects=[_project()]))

    assert "Sun Asterisk" in text  # from working_experience
    assert "Mosan Ewallet" in text  # from projects
    assert "Viettel Digital" in text
    assert "Oracle" in text


def test_format_projects_still_reports_projects_when_there_is_no_job_history():
    text = resume_profile.format_projects(_resume(working_experience=[], projects=[_project()]))

    assert "Mosan Ewallet" in text
    assert "No work experience or projects listed." not in text


def test_format_projects_says_so_when_the_cv_has_neither():
    text = resume_profile.format_projects(_resume(working_experience=[], projects=[]))

    assert text == "No work experience or projects listed."


def test_format_work_experience_keeps_every_achievement():
    # Capping at three hid the technologies listed further down each role from the
    # skills scorer, which reads this same text.
    resume = _resume(
        working_experience=[
            WorkExperience(
                company="A",
                position="Dev",
                start_date="2022-01",
                end_date="Present",
                achievements=[f"bullet {index}" for index in range(7)],
            )
        ]
    )

    text = resume_profile.format_work_experience(resume)

    assert "bullet 6" in text
    assert all(f"bullet {index}" in text for index in range(7))


# --- use case --------------------------------------------------------------


def test_execute_scores_every_criterion_and_recommends():
    llm = FakeLLMService(score=80)

    result = _match(llm, file_path="cv.pdf", jd_text="Senior Python dev")

    assert [score.criterion for score in result.criterion_scores] == list(Criterion)
    assert result.match_score == 80
    assert result.recommendation is RecommendationAction.SHORTLIST
    assert result.warnings == []
    # 1 extraction + 6 criteria + 1 insights, each a separate structured call.
    assert len(llm.calls) == 8


def test_execute_applies_custom_weights_to_the_match_score():
    class SkewedLLM(FakeLLMService):
        async def analyze_text(self, *, response_model, **kwargs):
            if response_model.__name__ == "SkillsScoreResult":
                return response_model(score=100, explanation="perfect skills")
            if response_model in (ResumeData, InsightsResult):
                return await FakeLLMService.analyze_text(self, response_model=response_model)
            return response_model(score=0, explanation="nothing else matches")

    # Skills alone decides the outcome once every other weight is zeroed.
    weights = {criterion.value: 0.0 for criterion in Criterion} | {"skills": 100.0}
    result = _match(SkewedLLM(), file_path="cv.pdf", jd_text="Python dev", custom_weights=weights)

    assert result.match_score == 100
    assert result.recommendation is RecommendationAction.SHORTLIST


def test_execute_rejects_bad_weights_before_calling_the_llm():
    llm = FakeLLMService()

    with pytest.raises(InvalidWeightsError):
        asyncio.run(
            _use_case(llm).execute(
                file_path="cv.pdf", jd_text="Python dev", custom_weights={"skill": 50}
            )
        )

    assert llm.calls == []


def test_execute_without_a_jd_returns_the_extracted_cv_and_no_match():
    llm = FakeLLMService()

    analysis = asyncio.run(_use_case(llm).execute(file_path="cv.pdf"))

    assert analysis.resume.name == "Nguyen Van A"
    assert analysis.matching is None
    # Extraction only: none of the six scorers nor the insights call is paid for.
    assert llm.calls == ["ResumeData"]


def test_execute_reads_a_blank_jd_as_no_jd():
    llm = FakeLLMService()

    analysis = asyncio.run(_use_case(llm).execute(file_path="cv.pdf", jd_text="   "))

    assert analysis.matching is None
    assert llm.calls == ["ResumeData"]


def test_execute_still_rejects_bad_weights_without_a_jd():
    # Nothing here applies the weights, but accepting a misspelled criterion quietly
    # would hide the typo until the caller finally sent a JD with it.
    llm = FakeLLMService()

    with pytest.raises(InvalidWeightsError):
        asyncio.run(_use_case(llm).execute(file_path="cv.pdf", custom_weights={"skill": 50}))

    assert llm.calls == []


def test_extract_only_still_reports_what_the_cv_is_missing():
    llm = FresherLLM()

    analysis = asyncio.run(_use_case(llm).execute(file_path="cv.pdf"))

    assert any("work experience" in warning for warning in analysis.warnings)


def test_execute_fails_loudly_when_a_criterion_cannot_be_scored():
    # Skills carries 35% of the result; scoring it 0 on an LLM error would
    # surface as a genuine REJECT rather than as a failure.
    from cv_matching.src.domain.entities.matching import SkillsScoreResult

    llm = FakeLLMService(fail_on=(SkillsScoreResult,))

    with pytest.raises(MatchCvError):
        asyncio.run(_use_case(llm).execute(file_path="cv.pdf", jd_text="Python dev"))


def test_execute_keeps_the_scores_when_only_the_insights_fail():
    llm = FakeLLMService(score=80, fail_on=(InsightsResult,))

    result = _match(llm, file_path="cv.pdf", jd_text="Python dev")

    assert result.match_score == 80
    assert result.criterion_scores
    assert result.strengths == []
    assert any("insights" in warning for warning in result.warnings)


def test_onsite_conflict_blocks_the_automatic_shortlist():
    # Location carries no weight, so a candidate in the wrong city can still score 80+
    # on skills alone. The conflict has to stop the shortlist on its own.
    class WrongCityLLM(FakeLLMService):
        async def analyze_text(self, *, response_model, **kwargs):
            if response_model is LocationScoreResult:
                self.calls.append(response_model.__name__)
                return LocationScoreResult(
                    score=40,
                    explanation="Hanoi role, candidate in HCMC",
                    candidate_location="Ho Chi Minh City",
                    required_location="Hanoi",
                    onsite_conflict=True,
                )
            return await FakeLLMService.analyze_text(self, response_model=response_model, **kwargs)

    result = _match(WrongCityLLM(score=90), file_path="cv.pdf", jd_text="Onsite in Hanoi")

    assert result.match_score >= SHORTLIST_THRESHOLD  # would have been shortlisted
    assert result.recommendation is RecommendationAction.REVIEW_CAREFULLY
    assert any("Hanoi" in warning and "Ho Chi Minh" in warning for warning in result.warnings)
    assert "on-site" in result.recommendation_reason


def test_a_matching_location_leaves_the_shortlist_alone():
    result = _match(FakeLLMService(score=90), file_path="cv.pdf", jd_text="Onsite in Hanoi")

    assert result.recommendation is RecommendationAction.SHORTLIST
    assert result.warnings == []


def test_onsite_conflict_does_not_promote_a_weak_candidate():
    # The flag only ever blocks a shortlist; it must not rewrite a REJECT.
    class WrongCityLLM(FakeLLMService):
        async def analyze_text(self, *, response_model, **kwargs):
            if response_model is LocationScoreResult:
                self.calls.append(response_model.__name__)
                return LocationScoreResult(score=20, explanation="wrong city", onsite_conflict=True)
            return await FakeLLMService.analyze_text(self, response_model=response_model, **kwargs)

    result = _match(WrongCityLLM(score=10), file_path="cv.pdf", jd_text="Onsite in Hanoi")

    assert result.recommendation is RecommendationAction.REJECT


def test_recommendation_reason_ignores_criteria_that_carry_no_weight():
    # Location scores low for anyone without an address; naming it as the reason a
    # candidate needs review would point the recruiter at something that scored nothing.
    scores = [
        CriterionScore(
            criterion=Criterion.LOCATION,
            criterion_name=Criterion.LOCATION.label,
            score=0,
            weight=0,
            weighted_score=0,
            explanation="no address on the CV",
        ),
        CriterionScore(
            criterion=Criterion.SKILLS,
            criterion_name=Criterion.SKILLS.label,
            score=30,
            weight=40,
            weighted_score=12,
            explanation="thin",
        ),
    ]

    reason = MatchCvUseCase._recommendation_reason(RecommendationAction.REVIEW_CAREFULLY, scores)

    assert Criterion.SKILLS.label in reason
    assert Criterion.LOCATION.label not in reason


def test_execute_rejects_an_empty_cv():
    llm = FakeLLMService()

    with pytest.raises(MatchCvError, match="empty"):
        asyncio.run(
            _use_case(llm, FakeDocumentParser(text="  ")).execute(
                file_path="cv.pdf", jd_text="Python dev"
            )
        )


def _response(analysis) -> dict:
    """Build the response body the route builds, so DTO gaps surface in the tests."""
    return MatchCvResponse(
        success=True,
        cv_data=ExtractedCvDTO.model_validate(analysis.resume, from_attributes=True),
        result=(
            MatchingResultDTO.model_validate(analysis.matching, from_attributes=True)
            if analysis.matching is not None
            else None
        ),
        warnings=analysis.warnings,
    ).model_dump(mode="json")


def test_result_serialises_into_the_api_response_dto():
    # The route hands the domain result straight to the DTO, so a field that
    # does not survive that conversion would only show up in production.
    llm = FakeLLMService(score=80)
    analysis = asyncio.run(_use_case(llm).execute(file_path="cv.pdf", jd_text="Python dev"))

    payload = _response(analysis)
    result = payload["result"]

    assert result["match_score"] == 80
    assert result["recommendation"] == "SHORTLIST"
    assert [score["criterion"] for score in result["criterion_scores"]] == [
        criterion.value for criterion in Criterion
    ]
    assert result["criterion_scores"][0]["criterion_name"] == Criterion.YEARS_OF_EXPERIENCE.label
    # The extracted CV rides along with the match rather than replacing it.
    assert payload["cv_data"]["name"] == "Nguyen Van A"


def test_extracted_cv_serialises_with_every_section_it_carries():
    class RichLLM(FakeLLMService):
        async def analyze_text(self, *, response_model, **kwargs):
            if response_model is ResumeData:
                self.calls.append(response_model.__name__)
                return _resume(
                    projects=[Project(name="ERP Portal", tech_stack=["Python", "PostgreSQL"])],
                    languages=[LanguageSkill(language="English", proficiency="Intermediate")],
                )
            return await FakeLLMService.analyze_text(self, response_model=response_model, **kwargs)

    analysis = asyncio.run(_use_case(RichLLM()).execute(file_path="cv.pdf"))

    payload = _response(analysis)

    assert payload["result"] is None
    assert payload["cv_data"]["working_experience"][0]["company"] == "Sun Asterisk"
    assert payload["cv_data"]["education"][0]["institution"] == "HUST"
    assert payload["cv_data"]["projects"][0]["tech_stack"] == ["Python", "PostgreSQL"]
    assert payload["cv_data"]["languages"][0]["proficiency"] == "Intermediate"


def test_execute_warns_when_the_cv_has_no_work_experience():
    result = _match(FresherLLM(score=30), file_path="cv.pdf", jd_text="Python dev")

    assert any("work experience" in warning for warning in result.warnings)
    assert result.recommendation is RecommendationAction.REJECT
