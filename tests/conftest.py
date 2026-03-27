import pytest

from sentinel import Sentinel, Scope
from sentinel.models import EntityStatus, Sensitivity


@pytest.fixture
def world():
    """A realistic test world with ambiguous contacts and stale entries."""
    s = Sentinel()

    # --- Contacts ---
    s.add_contact(
        id="david-liu",
        name="David Liu",
        emails=["david.liu@mycompany.com"],
        role="Senior Engineer",
        org="MyCompany",
        scope=Scope.INTERNAL,
    )
    s.add_contact(
        id="david-kim",
        name="David Kim",
        emails=["david.kim@partner-co.com"],
        role="Partnership Manager",
        org="Partner Co",
        scope=Scope.EXTERNAL,
    )
    s.add_contact(
        id="john-old",
        name="John Chen",
        emails=["john@old-lawfirm.com"],
        role="Lawyer",
        org="Old Law Firm",
        scope=Scope.EXTERNAL,
        status=EntityStatus.INACTIVE,
        valid_until="2026-02-01",
    )
    s.add_contact(
        id="john-new",
        name="John Chen",
        emails=["john@new-lawfirm.com"],
        role="Lawyer",
        org="New Law Firm",
        scope=Scope.EXTERNAL,
        status=EntityStatus.ACTIVE,
    )
    s.add_contact(
        id="alice",
        name="Alice Wang",
        emails=["alice@mycompany.com"],
        role="Product Manager",
        org="MyCompany",
        scope=Scope.INTERNAL,
    )
    s.add_contact(
        id="tom-client",
        name="Tom Lee",
        emails=["tom@acme.com"],
        role="Client Contact",
        org="Acme Corp",
        scope=Scope.EXTERNAL,
    )

    # --- Documents ---
    s.add_document(
        id="doc-profit",
        title="Q3 Profit Margins",
        path="/docs/profit-margins.xlsx",
        scope=Scope.INTERNAL,
        sensitivity=Sensitivity.CONFIDENTIAL,
    )
    s.add_document(
        id="doc-contract",
        title="Acme Service Agreement",
        path="/docs/acme-contract.pdf",
        scope=Scope.EXTERNAL,
        sensitivity=Sensitivity.INTERNAL,
    )
    s.add_document(
        id="doc-pricing",
        title="2026 Pricing Strategy",
        path="/docs/pricing-strategy.xlsx",
        scope=Scope.INTERNAL,
        sensitivity=Sensitivity.CONFIDENTIAL,
    )

    # --- Projects ---
    s.add_project(
        id="alpha",
        name="Project Alpha",
        scope=Scope.INTERNAL,
        sensitivity=Sensitivity.CONFIDENTIAL,
    )
    s.add_project(
        id="beta",
        name="Project Beta",
        scope=Scope.EXTERNAL,
    )

    # --- Memberships ---
    s.add_membership("david-liu", "alpha")
    s.add_membership("alice", "alpha")
    s.add_membership("david-kim", "beta")
    s.add_membership("tom-client", "beta")

    return s
