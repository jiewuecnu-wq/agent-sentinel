from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import Optional


class Sensitivity(IntEnum):
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    CRITICAL = 3


class Scope(IntEnum):
    """Data flow boundary. Higher value = more restricted."""

    EXTERNAL = 0
    TEAM = 1
    INTERNAL = 2
    RESTRICTED = 3


class EntityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Decision(str, Enum):
    ALLOW = "allow"
    CLARIFY = "clarify"
    BLOCK = "block"


@dataclass
class Contact:
    id: str
    name: str
    emails: list[str]
    role: str = ""
    org: str = ""
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    scope: Scope = Scope.INTERNAL
    status: EntityStatus = EntityStatus.ACTIVE
    valid_until: Optional[str] = None


@dataclass
class Project:
    id: str
    name: str
    status: str = "active"
    scope: Scope = Scope.INTERNAL
    sensitivity: Sensitivity = Sensitivity.INTERNAL


@dataclass
class Group:
    id: str
    name: str
    group_type: str = "internal"
    scope: Scope = Scope.INTERNAL


@dataclass
class Document:
    id: str
    title: str
    path: Optional[str] = None
    doc_type: str = "file"
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    scope: Scope = Scope.INTERNAL


@dataclass
class ResolvedEntity:
    entity_id: Optional[str]
    matched_value: str
    match_type: str  # "exact_email", "name_match", "ambiguous_name", "unresolved"
    confidence: float = 1.0


@dataclass
class Candidate:
    entity_id: str
    name: str
    email: str
    reason: str


@dataclass
class VerificationResult:
    decision: Decision
    explanation: str
    target: Optional[ResolvedEntity] = None
    candidates: list[Candidate] = field(default_factory=list)


@dataclass
class SessionContext:
    current_project: Optional[str] = None
    current_group: Optional[str] = None
    data_sources: set = field(default_factory=set)
