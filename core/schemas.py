"""Контракты данных (pydantic v2)."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    years: Optional[str] = None


class Experience(BaseModel):
    org: str
    role: str
    period: Optional[str] = None
    bullets: list[str] = Field(default_factory=list)


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


class TrackResult(BaseModel):
    track: Literal["Industry", "Research", "Education", "Startup"]
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    runner_up: Optional[str] = None


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
