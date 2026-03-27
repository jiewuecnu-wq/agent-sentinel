"""Load experiments/seed.py into a Sentinel instance and build SessionContext presets."""

from __future__ import annotations

from typing import Any, Dict

from sentinel import Sentinel, Scope, SessionContext
from sentinel.models import Document, EntityStatus, Project, Sensitivity

try:
    from .seed import CONTACTS, DOCUMENTS, PROJECTS, RELATIONS
except ImportError:
    from seed import CONTACTS, DOCUMENTS, PROJECTS, RELATIONS


def _map_scope(name: str) -> Scope:
    return getattr(Scope, (name or "INTERNAL").upper())


def _map_sensitivity(name: str) -> Sensitivity:
    key = (name or "INTERNAL").upper()
    if key == "PUBLIC":
        return Sensitivity.PUBLIC
    if key == "CONFIDENTIAL":
        return Sensitivity.CONFIDENTIAL
    if key in ("CRITICAL", "HIGH_VALUE"):
        return Sensitivity.CRITICAL
    return Sensitivity.INTERNAL


def _map_status(raw: str) -> EntityStatus:
    if raw == "inactive":
        return EntityStatus.INACTIVE
    if raw == "archived":
        return EntityStatus.ARCHIVED
    return EntityStatus.ACTIVE


def build_sentinel_from_seed() -> Sentinel:
    s = Sentinel()

    for p in PROJECTS:
        if p.get("type") != "project":
            continue
        s.add_project(
            id=p["id"],
            name=p["name"],
            scope=_map_scope(p.get("scope", "INTERNAL")),
            sensitivity=_map_sensitivity(p.get("sensitivity", "INTERNAL")),
        )

    for c in CONTACTS:
        if c.get("type") != "contact":
            continue
        valid_until = c.get("valid_until")
        s.add_contact(
            id=c["id"],
            name=c["name"],
            emails=list(c.get("emails") or []),
            role=c.get("role", "") or "",
            org=c.get("org", "") or "",
            scope=_map_scope(c.get("scope", "INTERNAL")),
            sensitivity=_map_sensitivity(c.get("sensitivity", "INTERNAL")),
            status=_map_status(c.get("status", "active")),
            valid_until=valid_until,
        )

    for d in DOCUMENTS:
        if d.get("type") != "document":
            continue
        s.add_document(
            id=d["id"],
            title=d.get("title", d["id"]),
            path=d.get("path"),
            doc_type=d.get("kind", "file"),
            scope=_map_scope(d.get("scope", "INTERNAL")),
            sensitivity=_map_sensitivity(d.get("sensitivity", "INTERNAL")),
            audience=d.get("audience"),
            thread_importance=d.get("thread_importance"),
        )

    for src, tgt, rel in RELATIONS:
        if rel == "MEMBER_OF":
            s.add_membership(src, tgt)

    return s


def _path_to_doc_id() -> Dict[str, str]:
    return {d["path"]: d["id"] for d in DOCUMENTS if d.get("type") == "document" and d.get("path")}


def preset_to_context(preset: Dict[str, Any]) -> SessionContext:
    path_id = _path_to_doc_id()
    ctx = SessionContext()
    ctx.current_project = preset.get("current_project")
    ctx.current_group = preset.get("current_group")
    for path in preset.get("data_sources") or []:
        did = path_id.get(path)
        if did:
            ctx.data_sources.add(did)
    ss = preset.get("source_scope")
    if ss:
        ctx.source_scope = getattr(Scope, str(ss).upper())
    return ctx
