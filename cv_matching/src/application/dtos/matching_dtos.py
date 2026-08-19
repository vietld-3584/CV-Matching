"""
Data Transfer Objects (DTOs)

Request and response models for the CV matching endpoints.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from cv_matching.src.domain.entities.matching import (
    Criterion,
    ImprovementArea,
    SkillOrKeyword,
    StrengthArea,
)
from cv_matching.src.domain.entities.resume import ResumeData


class ExtractedCvDTO(ResumeData):
    """The parsed CV exactly as it comes out of extraction.

    Only `tags` is restated: its extraction description is a list of ~60 university
    codes written for the parsing model, which is noise in the API docs.
    """

    tags: list[str] = Field(
        default_factory=list,
        description=(
            "Nhãn suy ra từ CV: nơi làm việc (HN, HCM, DN, JP...) và mã trường "
            "(hust, uit, fpt...). 'other' khi không khớp trường nào"
        ),
    )


class CriterionScoreDTO(BaseModel):
    criterion: Criterion = Field(..., description="Mã tiêu chí, dùng khi muốn chỉnh trọng số")
    criterion_name: str = Field(..., description="Tên tiêu chí hiển thị cho người dùng")
    score: int = Field(..., ge=0, le=100, description="Điểm của riêng tiêu chí này")
    weight: float = Field(
        ..., ge=0, le=100, description="Trọng số (%) đã được chuẩn hoá về tổng 100"
    )
    weighted_score: float = Field(
        ..., description="score * weight / 100, phần đóng góp vào điểm tổng"
    )
    explanation: str = Field(..., description="Lý do chấm điểm")


class MatchingResultDTO(BaseModel):
    match_score: int = Field(
        ..., ge=0, le=100, description="Điểm tổng, tổng có trọng số của 6 tiêu chí"
    )
    overall_summary: str = Field(..., description="Nhận xét tổng quan về mức độ phù hợp")
    criterion_scores: list[CriterionScoreDTO] = Field(..., description="Điểm từng tiêu chí")
    recommendation: Literal["SHORTLIST", "REVIEW_CAREFULLY", "REJECT"] = Field(
        ..., description="SHORTLIST khi >= 70, REVIEW_CAREFULLY khi >= 40, còn lại REJECT"
    )
    recommendation_reason: Optional[str] = Field(None, description="Lý do cho khuyến nghị")
    strengths: list[StrengthArea] = Field(
        default_factory=list, description="Điểm mạnh của ứng viên so với JD"
    )
    areas_to_address: list[ImprovementArea] = Field(
        default_factory=list, description="Điểm còn thiếu so với JD"
    )
    matched_keywords_and_skills: list[SkillOrKeyword] = Field(
        default_factory=list, description="Kỹ năng / từ khoá và sự xuất hiện của chúng ở CV và JD"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Vấn đề gặp phải khi phân tích, rỗng nếu mọi bước đều thành công",
    )


class MatchCvResponse(BaseModel):
    success: bool
    cv_data: Optional[ExtractedCvDTO] = Field(
        None, description="Thông tin trích xuất từ CV, luôn có khi phân tích thành công"
    )
    result: Optional[MatchingResultDTO] = Field(
        None,
        description=(
            "Kết quả đối chiếu CV với JD. Chỉ có khi request truyền `jd_text`; "
            "null khi chỉ yêu cầu trích xuất CV"
        ),
    )
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Vấn đề gặp phải khi phân tích, rỗng nếu mọi bước đều thành công. "
            "Khi có `result` thì trùng với `result.warnings`"
        ),
    )
