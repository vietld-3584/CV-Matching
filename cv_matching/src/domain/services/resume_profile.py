"""
Resume Profile Helpers

Pure functions that derive facts from a `ResumeData` and render the sections a
scorer needs into prompt text. No LLM, no I/O - so the arithmetic below stays
unit-testable on its own.
"""

import re
from datetime import date
from typing import Iterable, Optional

from cv_matching.src.domain.entities.resume import ResumeData, WorkExperience

_ONGOING = {"present", "current", "now", "today", "hiện tại", "đến nay", "nay"}

# Dates on a CV are month-granular at best and reach us in whatever shape the
# LLM read them in, so match the common layouts rather than a single format.
_DATE_PATTERNS = (
    re.compile(r"^(?P<year>\d{4})[-/.](?P<month>\d{1,2})(?:[-/.]\d{1,2})?$"),  # 2024-03, 2024/03/15
    re.compile(r"^(?P<month>\d{1,2})[-/.](?P<year>\d{4})$"),  # 03/2024
    re.compile(r"^(?P<year>\d{4})$"),  # 2024
)

_TECH_PATTERN = re.compile(
    "|".join(
        (
            r"\b(?:Python|Java|JavaScript|TypeScript|Go|Rust|C\+\+|C#|Ruby|PHP|Swift|Kotlin)\b",
            r"\b(?:React|Vue|Angular|Node\.js|Django|Flask|FastAPI|Spring|\.NET|Rails)\b",
            r"\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|CI/CD|Git|GitHub)\b",
            r"\b(?:PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|SQL|NoSQL)\b",
            r"\b(?:TensorFlow|PyTorch|scikit-learn|Pandas|NumPy|LangChain|OpenAI|RAG|LLM|GenAI|AI|ML|NLP)\b",
            r"\b(?:REST|API|GraphQL|microservices|serverless|DevOps|Agile|Scrum)\b",
        )
    ),
    re.IGNORECASE,
)


def _parse_month(value: Optional[str]) -> Optional[tuple[int, int]]:
    """Parse a CV date into a (year, month) pair, or None when unreadable."""
    if not value:
        return None
    text = value.strip()
    if not text or text.casefold() in _ONGOING:
        return None
    for pattern in _DATE_PATTERNS:
        match = pattern.match(text)
        if match is None:
            continue
        year = int(match.group("year"))
        month = int(match.groupdict().get("month") or 1)
        if 1 <= month <= 12:
            return year, month
    return None


def _is_ongoing(value: Optional[str]) -> bool:
    return bool(value) and value.strip().casefold() in _ONGOING


def _month_index(year: int, month: int) -> int:
    """Absolute month number, so periods can be compared and subtracted."""
    return year * 12 + (month - 1)


def _period(experience: WorkExperience, today: date) -> Optional[tuple[int, int]]:
    """Half-open [start, end) month range worked, or None when undatable.

    A stated end month counts as worked - "2024-01 to 2024-03" is three months,
    not two - hence the half-open range. An ongoing role stops at the start of
    the current month instead, since that month is only partly behind them.
    """
    start = _parse_month(experience.start_date)
    if start is None:
        return None

    current_month = _month_index(today.year, today.month)
    end_parsed = _parse_month(experience.end_date)
    if end_parsed is not None:
        # A CV that claims to end in the future is more likely mis-parsed than true.
        end = min(_month_index(*end_parsed) + 1, current_month + 1)
    elif _is_ongoing(experience.end_date) or not experience.end_date:
        end = current_month
    else:
        return None

    start_index = _month_index(*start)
    if end <= start_index:
        return None
    return start_index, end


def total_experience_years(resume: ResumeData, today: Optional[date] = None) -> float:
    """Total years worked, counting overlapping positions only once.

    Concurrent roles (a day job plus a side contract) are common on a CV and
    summing them independently inflates the total, so the periods are merged
    before being counted. Undatable entries are skipped rather than guessed at.
    """
    today = today or date.today()

    periods = [
        period
        for period in (_period(experience, today) for experience in resume.working_experience)
        if period is not None
    ]
    if not periods:
        return 0.0

    merged: list[list[int]] = []
    for start, end in sorted(periods):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    months = sum(end - start for start, end in merged)
    return round(months / 12.0, 1)


def latest_position(resume: ResumeData, today: Optional[date] = None) -> Optional[WorkExperience]:
    """The most recent role, by end date rather than by list order.

    Reverse-chronological order is the convention, not a guarantee: the CV
    itself may be ordered differently and the extraction preserves whatever it
    read. Undatable entries fall back to their position in the list.
    """
    if not resume.working_experience:
        return None
    today = today or date.today()

    def sort_key(item: tuple[int, WorkExperience]) -> tuple[int, int]:
        index, experience = item
        period = _period(experience, today)
        return (period[1] if period else -1, -index)

    return max(enumerate(resume.working_experience), key=sort_key)[1]


def latest_title(resume: ResumeData, today: Optional[date] = None) -> Optional[str]:
    experience = latest_position(resume, today)
    return experience.position if experience else None


def collect_tech_skills(resume: ResumeData) -> list[str]:
    """Technical skills the candidate lists, plus the ones named in their history.

    Extraction fills `tech_skills` directly; scanning the experience text on top
    of that catches technologies mentioned only in passing inside an achievement.
    """
    skills: dict[str, str] = {}

    def add(skill: str) -> None:
        cleaned = skill.strip()
        if cleaned:
            skills.setdefault(cleaned.casefold(), cleaned)

    for skill in resume.tech_skills:
        add(skill)

    for experience in resume.working_experience:
        for text in (*experience.achievements, experience.description or ""):
            for match in _TECH_PATTERN.finditer(text):
                add(match.group())

    # A dedicated projects section usually names its stack explicitly, so those
    # entries are taken as listed rather than pattern-matched out of prose.
    for project in resume.projects:
        for skill in project.tech_stack:
            add(skill)
        for match in _TECH_PATTERN.finditer(project.description or ""):
            add(match.group())

    return sorted(skills.values(), key=str.casefold)


def format_work_experience(resume: ResumeData) -> str:
    if not resume.working_experience:
        return "No work experience listed."

    lines: list[str] = []
    for index, experience in enumerate(resume.working_experience, 1):
        lines.append(f"{index}. {experience.position} at {experience.company}")
        lines.append(
            f"   Duration: {experience.start_date or 'N/A'} - {experience.end_date or 'N/A'}"
        )
        # Every bullet is rendered: the skills scorer reads this text, and a cap
        # here silently hid the technologies listed further down each role.
        for achievement in experience.achievements:
            lines.append(f"   - {achievement}")
    return "\n".join(lines)


def format_education(resume: ResumeData) -> str:
    if not resume.education:
        return "No education information provided."

    lines: list[str] = []
    for education in resume.education:
        if education.degree and education.field:
            degree = f"{education.degree} in {education.field}"
        else:
            degree = education.degree or education.field or "Degree"
        lines.append(f"- {degree} from {education.institution}")
        if education.gpa:
            lines.append(f"  GPA: {education.gpa}")
    return "\n".join(lines)


def format_projects(resume: ResumeData) -> str:
    """Everything a project counter should look at: the job history and the projects section."""
    if not resume.working_experience and not resume.projects:
        return "No work experience or projects listed."

    lines: list[str] = []
    if resume.working_experience:
        lines.append("From work experience:")
    for experience in resume.working_experience:
        lines.append(
            f"\n{experience.position} at {experience.company} "
            f"({experience.start_date or 'N/A'} - {experience.end_date or 'N/A'}):"
        )
        if experience.description:
            lines.append(f"  Overview: {experience.description}")
        for achievement in experience.achievements:
            lines.append(f"  - {achievement}")

    if resume.projects:
        lines.append("\nFrom the projects section:")
        lines.append(format_project_section(resume))
    return "\n".join(lines)


def format_project_section(resume: ResumeData) -> str:
    """Only the dedicated projects section, for prompts that render the job history separately."""
    if not resume.projects:
        return "No separate projects section on the CV."

    lines: list[str] = []
    for project in resume.projects:
        header = project.name
        if project.role:
            header += f" - {project.role}"
        period = f"{project.start_date or 'N/A'} - {project.end_date or 'N/A'}"
        lines.append(f"\n{header} ({period}):")
        if project.customer:
            lines.append(f"  Customer: {project.customer}")
        if project.team_size:
            lines.append(f"  Team size: {project.team_size}")
        if project.description:
            lines.append(f"  Overview: {project.description}")
        if project.tech_stack:
            lines.append(f"  Tech stack: {', '.join(project.tech_stack)}")
    return "\n".join(lines)


def format_list(values: Iterable[str], empty: str) -> str:
    joined = ", ".join(value for value in values if value)
    return joined or empty
