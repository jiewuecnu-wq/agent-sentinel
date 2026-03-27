"""
Three core scenarios that demonstrate why action-time verification matters.

Each test simulates a tool call an agent might make, and asserts
that Sentinel returns the correct allow / clarify / block decision.
"""

from sentinel import Decision, SessionContext


class TestAmbiguousRecipient:
    """
    Two contacts share the first name "David".
    David Liu is an internal engineer on Project Alpha.
    David Kim is an external partner on Project Beta.

    When the agent sends to David Kim while discussing Project Alpha,
    Sentinel should flag the mismatch and suggest David Liu.
    """

    def test_wrong_david_gets_clarify(self, world):
        ctx = SessionContext(current_project="alpha")
        result = world.verify(
            "send_email",
            {"to": "david.kim@partner-co.com", "subject": "Standup", "body": "..."},
            context=ctx,
        )
        assert result.decision == Decision.CLARIFY
        assert len(result.candidates) >= 1
        assert result.candidates[0].entity_id == "david-liu"

    def test_right_david_gets_allow(self, world):
        ctx = SessionContext(current_project="alpha")
        result = world.verify(
            "send_email",
            {"to": "david.liu@mycompany.com", "subject": "Standup", "body": "..."},
            context=ctx,
        )
        assert result.decision == Decision.ALLOW

    def test_no_project_context_allows_either(self, world):
        result = world.verify(
            "send_email",
            {"to": "david.kim@partner-co.com", "subject": "Hello", "body": "..."},
        )
        assert result.decision == Decision.ALLOW

    def test_david_kim_allowed_in_his_own_project(self, world):
        ctx = SessionContext(current_project="beta")
        result = world.verify(
            "send_email",
            {"to": "david.kim@partner-co.com", "subject": "Update", "body": "..."},
            context=ctx,
        )
        assert result.decision == Decision.ALLOW


class TestStaleContact:
    """
    Lawyer John Chen left his old firm in Feb 2026.
    Old entry (john@old-lawfirm.com) is inactive.
    New entry (john@new-lawfirm.com) is active.

    Sending to the old address should be blocked with a suggestion.
    """

    def test_stale_email_gets_blocked(self, world):
        result = world.verify(
            "send_email",
            {"to": "john@old-lawfirm.com", "subject": "Contract", "body": "..."},
        )
        assert result.decision == Decision.BLOCK
        assert "inactive" in result.explanation.lower()
        assert len(result.candidates) >= 1
        assert result.candidates[0].email == "john@new-lawfirm.com"

    def test_current_email_gets_allow(self, world):
        result = world.verify(
            "send_email",
            {"to": "john@new-lawfirm.com", "subject": "Contract", "body": "..."},
        )
        assert result.decision == Decision.ALLOW


class TestScopeBoundary:
    """
    Project Alpha is internal-only (scope=INTERNAL).
    Tom Lee is an external client (scope=EXTERNAL).

    Sending to Tom from the Alpha context violates scope boundaries.
    """

    def test_external_contact_blocked_in_internal_project(self, world):
        ctx = SessionContext(current_project="alpha")
        result = world.verify(
            "send_email",
            {"to": "tom@acme.com", "subject": "Alpha Update", "body": "..."},
            context=ctx,
        )
        assert result.decision == Decision.BLOCK
        assert "scope" in result.explanation.lower()

    def test_external_contact_allowed_in_external_project(self, world):
        ctx = SessionContext(current_project="beta")
        result = world.verify(
            "send_email",
            {"to": "tom@acme.com", "subject": "Beta Update", "body": "..."},
            context=ctx,
        )
        assert result.decision == Decision.ALLOW

    def test_internal_contact_allowed_in_internal_project(self, world):
        ctx = SessionContext(current_project="alpha")
        result = world.verify(
            "send_email",
            {"to": "alice@mycompany.com", "subject": "Sync", "body": "..."},
            context=ctx,
        )
        assert result.decision == Decision.ALLOW


class TestEdgeCases:

    def test_unknown_recipient_allows(self, world):
        result = world.verify(
            "send_email",
            {"to": "stranger@unknown.com", "subject": "Hi", "body": "..."},
        )
        assert result.decision == Decision.ALLOW

    def test_non_recipient_tool_allows(self, world):
        result = world.verify("read_file", {"path": "/some/file.txt"})
        assert result.decision == Decision.ALLOW

    def test_empty_world(self):
        from sentinel import Sentinel

        empty = Sentinel()
        result = empty.verify(
            "send_email",
            {"to": "anyone@example.com", "subject": "Hi", "body": "..."},
        )
        assert result.decision == Decision.ALLOW

    def test_tool_with_no_recipient_param(self, world):
        result = world.verify("send_email", {"subject": "Oops", "body": "no to"})
        assert result.decision == Decision.ALLOW
