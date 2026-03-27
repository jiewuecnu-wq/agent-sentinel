from __future__ import annotations

from typing import Optional

from sentinel.models import (
    Contact,
    Decision,
    Document,
    Group,
    Project,
    SessionContext,
    VerificationResult,
)
from sentinel.resolver import EntityResolver
from sentinel.verification import (
    ContextBoundaryVerifier,
    DataFlowVerifier,
    DeleteThreadVerifier,
    RecipientVerifier,
)
from sentinel.world import WorldModel

RECIPIENT_TOOLS = {
    "send_email",
    "send_message",
    "forward_message",
    "forward_email",
    "share_files",
}
READ_TOOLS = {
    "read_file",
    "read_email",
    "fetch_url",
    "search_mail",
    "search_contacts",
    "list_files",
}
DELETE_TOOLS = {"delete_email_thread"}


class Sentinel:
    """
    Main entry point.

    Usage::

        s = Sentinel()
        s.add_contact(id="alice", name="Alice", emails=["alice@co.com"])
        result = s.verify("send_email", {"to": "alice@co.com", ...})
        # result.decision  →  Decision.ALLOW / CLARIFY / BLOCK
        # result.explanation  →  human-readable reason
    """

    def __init__(self) -> None:
        self.world = WorldModel()
        self.resolver = EntityResolver(self.world)
        self.recipient_verifier = RecipientVerifier(self.world)
        self.flow_verifier = DataFlowVerifier(self.world)
        self.context_verifier = ContextBoundaryVerifier(self.world)
        self.delete_verifier = DeleteThreadVerifier(self.world)

    def verify(
        self,
        tool_name: str,
        tool_args: dict,
        context: Optional[SessionContext] = None,
    ) -> VerificationResult:
        # --- Track file/document references as data sources ---
        file_resolved = self.resolver.resolve_tool_files(tool_name, tool_args)
        if context is not None:
            for r in file_resolved:
                if r.entity_id:
                    context.data_sources.add(r.entity_id)

        # --- Read-only tools: track but don't block ---
        if tool_name in READ_TOOLS:
            return VerificationResult(
                decision=Decision.ALLOW,
                explanation="Read operation recorded.",
            )

        # --- Destructive / high-value thread policies ---
        if tool_name in DELETE_TOOLS:
            dr = self.delete_verifier.verify(tool_name, tool_args)
            return dr

        # --- Non-recipient tools: nothing to verify yet ---
        if tool_name not in RECIPIENT_TOOLS:
            return VerificationResult(
                decision=Decision.ALLOW,
                explanation=f"Tool '{tool_name}' does not require recipient verification.",
            )

        # --- Recipient tools: resolve and verify ---
        resolved_recipients = self.resolver.resolve_tool_recipients(
            tool_name, tool_args, context
        )

        if not resolved_recipients:
            return VerificationResult(
                decision=Decision.ALLOW,
                explanation="No recipient parameters found in tool call.",
            )

        all_results: list[VerificationResult] = []

        # Recipient verification (identity, context, scope)
        for r in resolved_recipients:
            all_results.append(self.recipient_verifier.verify(r, context))

        # Data flow verification (accumulated session data vs recipients)
        data_sources = context.data_sources if context else set()
        flow_result = self.flow_verifier.verify(resolved_recipients, data_sources)
        if flow_result:
            all_results.append(flow_result)

        # Explicit context-boundary verification (conversation/workflow scope)
        context_result = self.context_verifier.verify(resolved_recipients, context)
        if context_result:
            all_results.append(context_result)

        # Return the most severe result
        blocks = [r for r in all_results if r.decision == Decision.BLOCK]
        if blocks:
            return blocks[0]

        clarifies = [r for r in all_results if r.decision == Decision.CLARIFY]
        if clarifies:
            return clarifies[0]

        return all_results[0]

    # --- World model helpers ---

    def add_contact(self, id: str, name: str, emails: list[str], **kwargs) -> None:
        self.world.add_contact(Contact(id=id, name=name, emails=emails, **kwargs))

    def add_project(self, id: str, name: str, **kwargs) -> None:
        self.world.add_project(Project(id=id, name=name, **kwargs))

    def add_group(self, id: str, name: str, **kwargs) -> None:
        self.world.add_group(Group(id=id, name=name, **kwargs))

    def add_document(self, id: str, title: str, **kwargs) -> None:
        self.world.add_document(Document(id=id, title=title, **kwargs))

    def add_membership(self, contact_id: str, project_id: str) -> None:
        self.world.add_membership(contact_id, project_id)
