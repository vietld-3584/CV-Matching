"""
Resume Domain Entities

Structured representation of a candidate CV. These models double as the
structured-output schema handed to the LLM during extraction, so every field
carries a description the model can act on.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


def _ensure_list(value: Any) -> list:
    """Models sometimes emit null instead of an empty list for absent sections."""
    return [] if value is None else value


class LanguageSkill(BaseModel):
    """Language proficiency information."""

    language: str = Field(..., description="Language name (e.g., English, Vietnamese)")
    proficiency: Optional[str] = Field(
        None, description="Proficiency level (e.g., Fluent, Native, Intermediate)"
    )


class SocialProfile(BaseModel):
    """Social media or professional profile."""

    platform: str = Field(..., description="Platform name (e.g., linkedin, github, website)")
    url: str = Field(..., description="Full URL to the profile")


class WorkExperience(BaseModel):
    """Professional work experience entry."""

    company: str = Field(..., description="Company or organization name")
    position: str = Field(..., description="Job title or position held")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM format")
    end_date: Optional[str] = Field(
        None, description="End date in YYYY-MM format, or 'Present' if current"
    )
    location: Optional[str] = Field(None, description="Work location (city, country)")
    description: Optional[str] = Field(
        None,
        description="Brief job overview or summary (optional). Main details should be in achievements.",
    )
    achievements: list[str] = Field(
        default_factory=list,
        description=(
            "List of responsibilities, accomplishments, key tasks, and achievements. "
            "Each item should be a separate bullet point. This is the PRIMARY field for job details."
        ),
    )

    @field_validator("achievements", mode="before")
    @classmethod
    def ensure_achievements_list(cls, value: Any) -> list:
        return _ensure_list(value)


class Education(BaseModel):
    """Educational background entry."""

    institution: str = Field(..., description="School, university, or institution name")
    degree: Optional[str] = Field(None, description="Degree type (e.g., Bachelor, Master, PhD)")
    field: Optional[str] = Field(None, description="Field of study or major")
    start_date: Optional[str] = Field(None, description="Start year in YYYY format")
    end_date: Optional[str] = Field(None, description="End year in YYYY format")
    gpa: Optional[str] = Field(None, description="GPA or grade")
    description: Optional[str] = Field(None, description="Additional information about education")


class Project(BaseModel):
    """A project listed in its own section, separate from an employment entry.

    Vietnamese dev CVs routinely put their strongest evidence here - client, team
    size and tech stack per project - rather than inside the job history, so a
    schema without this field drops the part of the CV the scoring most needs.
    """

    name: str = Field(..., description="Project name or title")
    role: Optional[str] = Field(None, description="The candidate's position on the project")
    description: Optional[str] = Field(
        None, description="What the project was and what the candidate did on it"
    )
    tech_stack: list[str] = Field(
        default_factory=list,
        description="Technologies, languages, frameworks and tools used on this project",
    )
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM format")
    end_date: Optional[str] = Field(
        None, description="End date in YYYY-MM format, or 'Present' if ongoing"
    )
    team_size: Optional[str] = Field(None, description="Number of people on the project")
    customer: Optional[str] = Field(None, description="Client or customer the project was for")

    @field_validator("tech_stack", mode="before")
    @classmethod
    def ensure_tech_stack_list(cls, value: Any) -> list:
        return _ensure_list(value)


class ResumeData(BaseModel):
    """Complete structured resume data extracted from a CV document."""

    name: str = Field(..., description="Full name of the candidate")
    email: str = Field(..., description="Email address")
    tags: list[str] = Field(
        default_factory=list,
        description="""AVAILABLE TAGS:
        Locations: "Talent Pool", "HN", "DN", "HCM", "JP", "Japan", "Tokyo"
        Universities: "hust", "uit", "uet", "fpt", "hcmut", "haui", "hcmus", "tlu", "humg", "ptit", "hus", "kma", "neu", "wru", "epu", "utt", "uneti", "utc", "vin uni", "dut", "hutech", "bav", "vlu", "tmu", "utc2", "ufm", "hou", "hcmue", "fptpoly", "ueh", "dtu", "hub", "aof", "hcmiu", "hcmute", "hcmou", "hcmptit", "uel", "hubt", "hanu", "hunre", "iuh", "huit", "greenwich", "tdtu", "due", "huce", "uef", "huflit", "vku", "ctu", "ued", "vnu", "stu", "codegym", "rmit", "dau", "hiec", "uth", "hic", "other"

        Detection rules:
        - Location: Based on address/phone/city (Hanoi->HN, Ho Chi Minh->HCM, Da Nang->DN, Japan->JP)
        - University: Match institution names to codes (HUST->hust, UET->uet, FPT->fpt, etc.)
        - Add 'Talent Pool' if candidate is qualified
        - Use 'other' if no specific university match""",
    )

    date_of_birth: Optional[str] = Field(None, description="Date of birth in YYYY-MM-DD format")
    phone_number: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Physical address")
    social_profile: list[SocialProfile] = Field(
        default_factory=list, description="List of social media and professional profiles"
    )
    tech_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Technical skills: programming languages, frameworks, libraries, databases, "
            "cloud platforms, tools and methodologies. Collect them from the whole CV - "
            "the skills section as well as the technologies named inside work experience."
        ),
    )
    non_tech_skills: list[str] = Field(
        default_factory=list,
        description="Non-technical skills (e.g., communication, leadership, teamwork)",
    )
    languages: list[LanguageSkill] = Field(
        default_factory=list, description="Languages spoken and proficiency levels"
    )
    education: list[Education] = Field(
        default_factory=list, description="Educational background in reverse chronological order"
    )
    working_experience: list[WorkExperience] = Field(
        default_factory=list, description="Work experience in reverse chronological order"
    )
    projects: list[Project] = Field(
        default_factory=list,
        description=(
            "Projects from a dedicated projects section of the CV (Projects, Dự án, "
            "Personal Projects, Notable Projects). Extract every one of them, including "
            "the technologies each used - do not fold them into working_experience and "
            "do not skip them when the section is long."
        ),
    )

    @field_validator(
        "tags",
        "social_profile",
        "tech_skills",
        "non_tech_skills",
        "languages",
        "education",
        "working_experience",
        "projects",
        mode="before",
    )
    @classmethod
    def ensure_list_fields(cls, value: Any) -> list:
        return _ensure_list(value)
