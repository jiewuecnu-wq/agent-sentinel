from __future__ import annotations

from typing import Optional

from sentinel.models import (
    Candidate,
    Decision,
    EntityStatus,
    ResolvedEntity,
    SessionContext,
    VerificationResult,
)
from sentinel.world import WorldModel


class RecipientVerifier:
    def __init__(self, world: WorldModel) -> None:
        self.world = world

    def verify(
        self,
        resolved: ResolvedEntity,
        context: Optional[SessionContext] = None,
    ) -> VerificationResult:
        if resolved.entity_id is None:
            return VerificationResult(
                decision=Decision.ALLOW,
                explanation="Recipient not in world model; no verification possible.",
                target=resolved,
            )

        contact = self.world.get_contact(resolved.entity_id)
        if contact is None:
            return VerificationResult(
                decision=Decision.ALLOW,
                explanation="Entity not found in world model.",
                target=resolved,
            )

        # --- Check 1: Inactive / stale contact ---
        if contact.status == EntityStatus.INACTIVE:
            alternatives = self.world.find_same_name_contacts(contact.name, contact.id)
            active_alts = [a for a in alternatives if a.status == EntityStatus.ACTIVE]

            candidates = [
                Candidate(
                    entity_id=alt.id,
                    name=alt.name,
                    email=alt.emails[0] if alt.emails else "",
                    reason=f"Active contact with same name ({alt.role}, {alt.org})",
                )
                for alt in active_alts
            ]

            explanation = (
                f"Contact '{contact.name}' ({resolved.matched_value}) is inactive"
            )
            if contact.valid_until:
                explanation += f" since {contact.valid_until}"
            explanation += "."
            if candidates:
                explanation += (
                    f" Suggested alternative: "
                    f"{candidates[0].name} ({candidates[0].email})"
                )

            return VerificationResult(
                decision=Decision.BLOCK,
                explanation=explanation,
                target=resolved,
                candidates=candidates,
            )

        # --- Check 2: Context mismatch → possible wrong target ---
        if context and context.current_project:
            if not self.world.is_project_member(contact.id, context.current_project):
                same_name = self.world.find_same_name_contacts(
                    contact.name, contact.id
                )
                in_project = [
                    c
                    for c in same_name
                    if self.world.is_project_member(c.id, context.current_project)
                    and c.status == EntityStatus.ACTIVE
                ]

                if in_project:
                    project = self.world.get_project(context.current_project)
                    project_name = (
                        project.name if project else context.current_project
                    )

                    candidates = [
                        Candidate(
                            entity_id=c.id,
                            name=c.name,
                            email=c.emails[0] if c.emails else "",
                            reason=f"Member of {project_name} ({c.role})",
                        )
                        for c in in_project
                    ]

                    return VerificationResult(
                        decision=Decision.CLARIFY,
                        explanation=(
                            f"'{contact.name}' ({resolved.matched_value}) is not a "
                            f"member of {project_name}. "
                            f"Did you mean {in_project[0].name} "
                            f"({in_project[0].emails[0]})?"
                        ),
                        target=resolved,
                        candidates=candidates,
                    )

        # --- Check 3: Scope boundary violation ---
        if context and context.current_project:
            project = self.world.get_project(context.current_project)
            if project and project.scope > contact.scope:
                return VerificationResult(
                    decision=Decision.BLOCK,
                    explanation=(
                        f"Cannot send to '{contact.name}' "
                        f"(scope={contact.scope.name}): current project "
                        f"'{project.name}' has scope={project.scope.name}."
                    ),
                    target=resolved,
                )

        # --- All checks passed ---
        return VerificationResult(
            decision=Decision.ALLOW,
            explanation=f"Recipient '{contact.name}' verified.",
            target=resolved,
        )


class DataFlowVerifier:
    """Check accumulated session data sources against outbound recipients."""

    def __init__(self, world: WorldModel) -> None:
        self.world = world

    def verify(
        self,
        recipients: list[ResolvedEntity],
        data_sources: set[str],
    ) -> Optional[VerificationResult]:
        if not data_sources or not recipients:
            return None

        for source_id in data_sources:
            doc = self.world.get_document(source_id)
            if doc is None:
                continue

            for recipient in recipients:
                if recipient.entity_id is None:
                    continue
                contact = self.world.get_contact(recipient.entity_id)
                if contact is None:
                    continue

                if doc.scope > contact.scope:
                    return VerificationResult(
                        decision=Decision.BLOCK,
                        explanation=(
                            f"Session data includes '{doc.title}' "
                            f"(scope={doc.scope.name}). "
                            f"Cannot send to '{contact.name}' "
                            f"(scope={contact.scope.name})."
                        ),
                        target=recipient,
                    )

        return None
