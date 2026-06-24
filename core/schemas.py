"""Контракты данных (pydantic v2)."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    years: Optional[str] = None


class Experience(BaseModel):
    org: Optional[str] = None
    role: Optional[str] = None
    period: Optional[str] = None
    bullets: list[str] = Field(default_factory=list)

    @field_validator("org", "role", "period", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if isinstance(v, str) and v.strip().lower() in ("null", "none", ""):
            return None
        return v


class Project(BaseModel):
    name: str
    description: Optional[str] = None
    stack: list[str] = Field(default_factory=list)
    link: Optional[str] = None


class Profile(BaseModel):
    full_name: Optional[str] = None
    contacts: dict[str, str] = Field(default_factory=dict)
    target_role: Optional[str] = None
    summary: Optional[str] = None
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    @field_validator(
        "education", "experience", "projects",
        "skills", "achievements", "languages",
        mode="before",
    )
    @classmethod
    def none_to_list(cls, v):
        if v is None:
            return []
        if isinstance(v, dict):        # модель прислала один объект вместо списка
            return [v]
        return v

    @field_validator("languages", mode="before")
    @classmethod
    def normalize_languages(cls, v):
        if not isinstance(v, list):
            return v
        out = []
        for item in v:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                if "language" in item or "name" in item:
                    lang = item.get("language") or item.get("name") or ""
                    level = item.get("level") or ""
                    out.append(f"{lang} {level}".strip())
                else:                                                       # {'Английский': 'B2'}
                    for k, val in item.items():
                        out.append(f"{k} {val}".strip())
        return out


class TrackResult(BaseModel):
    track: Literal["Industry", "Research", "Education", "Startup"]
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    runner_up: Optional[str] = None

    @field_validator("confidence", mode="before")
    @classmethod
    def word_to_number(cls, v):
        if isinstance(v, str):
            return {"low": 0.3, "medium": 0.6, "high": 0.9}.get(v.strip().lower(), 0.5)
        return v

    @field_validator("runner_up", mode="before")
    @classmethod
    def dict_to_none(cls, v):
        return None if isinstance(v, dict) else v


class SkillMatch(BaseModel):
    target_role: str
    have: list[str]
    partial: list[str]
    missing: list[str]
    recommendations: list[str]


class TurnResult(BaseModel):
    reply: str
    profile_patch: dict = Field(default_factory=dict)
    completeness: float = Field(ge=0, le=1)
    ready_to_render: bool = False

    @field_validator("completeness", mode="before")
    @classmethod
    def word_to_number(cls, v):
        if isinstance(v, str):
            return {"low": 0.3, "partial": 0.5, "medium": 0.6, "high": 0.9, "full": 1.0}.get(v.strip().lower(), 0.5)
        return v


class ResumeOutput(BaseModel):
    fmt: Literal["hh", "habr_career", "linkedin"] = "hh"
    content_markdown: str
    warnings: list[str] = Field(default_factory=list)


class Critique(BaseModel):
    grounding_ok: bool
    fabricated_claims: list[str]
    completeness: float = Field(ge=0, le=1)
    format_ok: bool
    fixes: list[str]
