from __future__ import annotations

from typing import Optional

from sentinel.graph import PersonalWorldStateGraph
from sentinel.models import Contact, Document, Group, Project


class WorldModel:
    """Organizational world model backed by a PersonalWorldStateGraph.

    Provides domain-typed accessors (get_contact, find_document_by_path, …)
    while storing all entities and relationships in a single typed graph.
    """

    def __init__(self) -> None:
        self.graph = PersonalWorldStateGraph()

        # Fast-lookup indexes derived from node attributes.
        self._email_index: dict[str, str] = {}
        self._name_index: dict[str, list[str]] = {}
        self._path_index: dict[str, str] = {}

    # ── Mutations ──────────────────────────────────────────────

    def add_contact(self, contact: Contact) -> None:
        self.graph.add_node(contact.id, "contact", entity=contact)
        for email in contact.emails:
            self._email_index[email.lower()] = contact.id
        name_key = contact.name.lower()
        self._name_index.setdefault(name_key, []).append(contact.id)

    def add_project(self, project: Project) -> None:
        self.graph.add_node(project.id, "project", entity=project)

    def add_group(self, group: Group) -> None:
        self.graph.add_node(group.id, "group", entity=group)

    def add_document(self, document: Document) -> None:
        self.graph.add_node(document.id, "document", entity=document)
        if document.path:
            self._path_index[document.path] = document.id

    def add_membership(self, contact_id: str, project_id: str) -> None:
        self.graph.add_edge(contact_id, project_id, "MEMBER_OF")

    def add_group_membership(self, contact_id: str, group_id: str) -> None:
        self.graph.add_edge(contact_id, group_id, "GROUP_MEMBER_OF")

    def add_relation(self, source: str, target: str, edge_type: str) -> None:
        """Add an arbitrary typed edge (BELONGS_TO, SUCCESSOR_OF, …)."""
        self.graph.add_edge(source, target, edge_type)

    # ── Entity lookups ─────────────────────────────────────────

    def get_contact(self, contact_id: str) -> Optional[Contact]:
        node = self.graph.get_node(contact_id)
        if node and node.node_type == "contact":
            return node.entity
        return None

    def get_project(self, project_id: str) -> Optional[Project]:
        node = self.graph.get_node(project_id)
        if node and node.node_type == "project":
            return node.entity
        return None

    def get_group(self, group_id: str) -> Optional[Group]:
        node = self.graph.get_node(group_id)
        if node and node.node_type == "group":
            return node.entity
        return None

    def get_document(self, doc_id: str) -> Optional[Document]:
        node = self.graph.get_node(doc_id)
        if node and node.node_type == "document":
            return node.entity
        return None

    def find_document_by_path(self, path: str) -> Optional[Document]:
        doc_id = self._path_index.get(path)
        if doc_id:
            return self.get_document(doc_id)
        return None

    def find_contact_by_email(self, email: str) -> Optional[Contact]:
        contact_id = self._email_index.get(email.lower())
        if contact_id:
            return self.get_contact(contact_id)
        return None

    def find_contacts_by_name(self, name: str) -> list[Contact]:
        contact_ids = self._name_index.get(name.lower(), [])
        return [
            c
            for cid in contact_ids
            if (c := self.get_contact(cid)) is not None
        ]

    # ── Relationship queries ───────────────────────────────────

    def get_project_members(self, project_id: str) -> set[str]:
        return set(
            self.graph.neighbors(project_id, edge_type="MEMBER_OF", direction="in")
        )

    def is_project_member(self, contact_id: str, project_id: str) -> bool:
        return contact_id in self.get_project_members(project_id)

    def find_same_name_contacts(self, name: str, exclude_id: str) -> list[Contact]:
        """Find contacts sharing a first name, excluding one by id."""
        target_first = name.split()[0].lower()
        results = []
        for node in self.graph.nodes_by_type("contact"):
            contact: Contact = node.entity
            if contact.id == exclude_id:
                continue
            first = contact.name.split()[0].lower()
            if first == target_first or contact.name.lower() == name.lower():
                results.append(contact)
        return results

    # ── Collection accessors ───────────────────────────────────

    def all_contacts(self) -> list[Contact]:
        return [n.entity for n in self.graph.nodes_by_type("contact")]

    def all_documents(self) -> list[Document]:
        return [n.entity for n in self.graph.nodes_by_type("document")]

    def all_projects(self) -> list[Project]:
        return [n.entity for n in self.graph.nodes_by_type("project")]

    # ── Graph-level queries ────────────────────────────────────

    def coverage(self, required_ids: set[str]) -> float:
        """Fraction of required entity IDs present in the world model."""
        return self.graph.coverage(required_ids)

    def has_path(
        self,
        source: str,
        target: str,
        via_types: Optional[set[str]] = None,
    ) -> bool:
        """Check reachability between two entities in the graph."""
        return self.graph.has_path(source, target, via_types)

    def summary(self) -> dict:
        return self.graph.summary()


# Alias — conceptual rename without breaking existing imports.
PersonalWorldState = WorldModel
