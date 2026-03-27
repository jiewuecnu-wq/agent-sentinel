from __future__ import annotations

from typing import Optional

from sentinel.models import ResolvedEntity, SessionContext
from sentinel.world import WorldModel

TOOL_RECIPIENT_PARAMS: dict[str, list[str]] = {
    "send_email": ["to", "cc", "bcc"],
    "send_message": ["to"],
    "forward_message": ["to"],
    "forward_email": ["to"],
}

TOOL_FILE_PARAMS: dict[str, list[str]] = {
    "read_file": ["path"],
    "write_file": ["path"],
    "send_email": ["attachment"],
}


class EntityResolver:
    def __init__(self, world: WorldModel) -> None:
        self.world = world

    def resolve_recipient(
        self, value: str, context: Optional[SessionContext] = None
    ) -> ResolvedEntity:
        value = value.strip()

        contact = self.world.find_contact_by_email(value)
        if contact:
            return ResolvedEntity(
                entity_id=contact.id,
                matched_value=value,
                match_type="exact_email",
                confidence=1.0,
            )

        contacts = self.world.find_contacts_by_name(value)
        if len(contacts) == 1:
            return ResolvedEntity(
                entity_id=contacts[0].id,
                matched_value=value,
                match_type="name_match",
                confidence=0.8,
            )
        if len(contacts) > 1:
            return ResolvedEntity(
                entity_id=contacts[0].id,
                matched_value=value,
                match_type="ambiguous_name",
                confidence=0.4,
            )

        return ResolvedEntity(
            entity_id=None,
            matched_value=value,
            match_type="unresolved",
            confidence=0.0,
        )

    def resolve_file(self, value: str) -> ResolvedEntity:
        value = value.strip()
        doc = self.world.find_document_by_path(value)
        if doc:
            return ResolvedEntity(
                entity_id=doc.id,
                matched_value=value,
                match_type="exact_path",
                confidence=1.0,
            )
        return ResolvedEntity(
            entity_id=None,
            matched_value=value,
            match_type="unresolved",
            confidence=0.0,
        )

    def resolve_tool_recipients(
        self,
        tool_name: str,
        tool_args: dict,
        context: Optional[SessionContext] = None,
    ) -> list[ResolvedEntity]:
        param_names = TOOL_RECIPIENT_PARAMS.get(tool_name, [])
        resolved = []
        for param in param_names:
            value = tool_args.get(param)
            if value:
                resolved.append(self.resolve_recipient(value, context))
        return resolved

    def resolve_tool_files(
        self, tool_name: str, tool_args: dict
    ) -> list[ResolvedEntity]:
        param_names = TOOL_FILE_PARAMS.get(tool_name, [])
        resolved = []
        for param in param_names:
            value = tool_args.get(param)
            if value:
                resolved.append(self.resolve_file(value))
        return resolved
