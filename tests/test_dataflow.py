"""
Data flow tracking: detect when an operation chain leaks sensitive data.

The key insight is that individual operations may each look safe,
but the *chain* creates a violation. Reading a confidential report
then emailing an external client means confidential data can leak
into the email — even if the email body itself looks harmless.
"""

from sentinel import Decision, SessionContext


class TestOperationChainLeak:
    """
    Agent reads an internal profit report, then sends email to external client.
    Each step alone is fine; the combination should be blocked.
    """

    def test_read_confidential_then_send_external_blocked(self, world):
        ctx = SessionContext(current_project="alpha")

        r1 = world.verify(
            "read_file", {"path": "/docs/profit-margins.xlsx"}, context=ctx
        )
        assert r1.decision == Decision.ALLOW
        assert "doc-profit" in ctx.data_sources

        r2 = world.verify(
            "send_email",
            {"to": "tom@acme.com", "subject": "Summary", "body": "..."},
            context=ctx,
        )
        assert r2.decision == Decision.BLOCK
        assert "profit" in r2.explanation.lower() or "scope" in r2.explanation.lower()

    def test_multiple_reads_accumulate(self, world):
        ctx = SessionContext()

        world.verify(
            "read_file", {"path": "/docs/profit-margins.xlsx"}, context=ctx
        )
        world.verify(
            "read_file", {"path": "/docs/pricing-strategy.xlsx"}, context=ctx
        )
        assert ctx.data_sources == {"doc-profit", "doc-pricing"}

        result = world.verify(
            "send_email",
            {"to": "tom@acme.com", "subject": "Info", "body": "..."},
            context=ctx,
        )
        assert result.decision == Decision.BLOCK


class TestSafeDataFlows:
    """Operations that should be allowed despite data flow tracking."""

    def test_read_external_doc_then_send_external_allows(self, world):
        ctx = SessionContext()

        world.verify(
            "read_file", {"path": "/docs/acme-contract.pdf"}, context=ctx
        )
        assert "doc-contract" in ctx.data_sources

        result = world.verify(
            "send_email",
            {"to": "tom@acme.com", "subject": "Contract", "body": "..."},
            context=ctx,
        )
        assert result.decision == Decision.ALLOW

    def test_read_internal_then_send_internal_allows(self, world):
        ctx = SessionContext(current_project="alpha")

        world.verify(
            "read_file", {"path": "/docs/profit-margins.xlsx"}, context=ctx
        )

        result = world.verify(
            "send_email",
            {"to": "alice@mycompany.com", "subject": "Report", "body": "..."},
            context=ctx,
        )
        assert result.decision == Decision.ALLOW

    def test_no_context_means_no_tracking(self, world):
        world.verify("read_file", {"path": "/docs/profit-margins.xlsx"})

        result = world.verify(
            "send_email",
            {"to": "tom@acme.com", "subject": "Hi", "body": "..."},
        )
        assert result.decision == Decision.ALLOW


class TestAttachmentCheck:
    """Attaching a file to an email is treated as a data source."""

    def test_confidential_attachment_to_external_blocked(self, world):
        ctx = SessionContext()

        result = world.verify(
            "send_email",
            {
                "to": "tom@acme.com",
                "subject": "Report",
                "body": "See attached.",
                "attachment": "/docs/profit-margins.xlsx",
            },
            context=ctx,
        )
        assert result.decision == Decision.BLOCK

    def test_safe_attachment_to_external_allows(self, world):
        ctx = SessionContext()

        result = world.verify(
            "send_email",
            {
                "to": "tom@acme.com",
                "subject": "Contract",
                "body": "See attached.",
                "attachment": "/docs/acme-contract.pdf",
            },
            context=ctx,
        )
        assert result.decision == Decision.ALLOW

    def test_unknown_attachment_allows(self, world):
        ctx = SessionContext()

        result = world.verify(
            "send_email",
            {
                "to": "tom@acme.com",
                "subject": "File",
                "body": "...",
                "attachment": "/tmp/random-file.txt",
            },
            context=ctx,
        )
        assert result.decision == Decision.ALLOW
