import json
import logging
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from cv_matching.src.application.dtos.matching_dtos import (
    ExtractedCvDTO,
    MatchCvResponse,
    MatchingResultDTO,
)
from cv_matching.src.application.use_cases.match_cv import MatchCvError
from cv_matching.src.domain.entities.matching import Criterion, InvalidWeightsError
from cv_matching.src.infrastructure.container import CvMatchingContainer
from cv_matching.src.presentation.api.dependencies.auth import verify_api_key

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpg", "jpeg"}

_WEIGHTS_EXAMPLE = ", ".join(f'"{criterion.value}": 20' for criterion in list(Criterion)[:2])


def _parse_weights(raw: Optional[str]) -> Optional[dict[str, float]]:
    """Read the optional weights form field, which arrives as a JSON object string."""
    if raw is None or not raw.strip():
        return None
    try:
        weights = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"`weights` must be a JSON object, e.g. {{{_WEIGHTS_EXAMPLE}}}. {exc}",
        )
    if not isinstance(weights, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"`weights` must be a JSON object, e.g. {{{_WEIGHTS_EXAMPLE}}}.",
        )
    for key, value in weights.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Weight for '{key}' must be a number.",
            )
    return {key: float(value) for key, value in weights.items()}


@router.post("/match", response_model=MatchCvResponse)
async def match_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ..., description="CV file to extract, and to match when a JD is given (pdf, docx, png, jpg)"
    ),
    jd_text: Optional[str] = Form(
        None,
        description=(
            "Job description to match the CV against. Optional - leave it out to get the "
            "extracted CV (`cv_data`) on its own, with no matching."
        ),
    ),
    weights: Optional[str] = Form(
        None,
        description=(
            "Optional JSON object overriding the criterion weights, e.g. "
            '{"skills": 50, "location": 5}. Keys are the `criterion` values returned in '
            "`criterion_scores`; any criterion left out keeps its default weight, and the "
            "whole set is rescaled to total 100%. Only applies when `jd_text` is given."
        ),
    ),
    _api_key: str = Depends(verify_api_key),
):
    """
    Extract a candidate CV, and match it against a job description when one is given.

    The CV is read with Azure Document Intelligence and extracted into structured
    resume data, which always comes back in `cv_data`.

    When `jd_text` is supplied the candidate is also scored on six weighted criteria -
    years of experience, location, skills, educational background, relevant project
    count and title/role - which are combined into a single 0-100 `match_score` and a
    SHORTLIST / REVIEW_CAREFULLY / REJECT recommendation, returned in `result`.
    Without a JD, `result` is null and only the extraction runs.
    """
    custom_weights = _parse_weights(weights)

    extension = (file.filename or "").rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{extension}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )

    container = CvMatchingContainer()
    file_processor = container.file_processor()

    file_content = await file.read()
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty."
        )
    file_path = await file_processor.save_temp_file(file_content, f".{extension}")
    background_tasks.add_task(file_processor.cleanup_file, file_path)

    try:
        analysis = await container.match_cv_use_case().execute(
            file_path=file_path,
            jd_text=jd_text,
            custom_weights=custom_weights,
        )
    except InvalidWeightsError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except MatchCvError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The uploaded CV file could not be found.",
        )
    except Exception as exc:
        logger.exception("Failed to match CV: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Matching failed due to an internal error.",
        )

    return MatchCvResponse(
        success=True,
        cv_data=ExtractedCvDTO.model_validate(analysis.resume, from_attributes=True),
        result=(
            MatchingResultDTO.model_validate(analysis.matching, from_attributes=True)
            if analysis.matching is not None
            else None
        ),
        warnings=analysis.warnings,
    )
