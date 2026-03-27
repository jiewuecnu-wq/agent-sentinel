from __future__ import annotations

from typing import Optional

from sentinel.models import Contact, Document, Group, Project


class WorldModel:
    """Lightweight personal world model backed by in-memory dicts."""

    def __init__(self) -> None:
        self._contacts: dict[str, Contact] = {}
        self._projects: dict[str, Project] = {}
        self._groups: dict[str, Group] = {}
        self._documents: dict[str, Document] = {}

        self._project_members: dict[str, set[str]] = {}
        self._contact_projects: dict[str, set[str]] = {}
        self._group_members: dict[str, set[str]] = {}

        self._email_index: dict[str, str] = {}
        self._name_index: dict[str, list[str]] = {}
        self._path_index: dict[str, str] = {}

    # --- Mutations ---

    def add_contact(self, contact: Contact) -> None:
        self._contacts[contact.id] = contact
        for email in contact.emails:
            self._email_index[email.lower()] = contact.id
        name_key = contact.name.lower()
        self._name_index.setdefault(name_key, []).append(contact.id)

    def add_project(self, project: Project) -> None:
        self._projects[project.id] = project
        self._project_members.setdefault(project.id, set())

    def add_group(self, group: Group) -> None:
        self._groups[group.id] = group
        self._group_members.setdefault(group.id, set())

    def add_document(self, document: Document) -> None:
        self._documents[document.id] = document
        if document.path:
            self._path_index[document.path] = document.id

    def add_membership(self, contact_id: str, project_id: str) -> None:
        self._project_members.setdefault(project_id, set()).add(contact_id)
        self._contact_projects.setdefault(contact_id, set()).add(project_id)

    def add_group_membership(self, contact_id: str, group_id: str) -> None:
        self._group_members.setdefault(group_id, set()).add(contact_id)

    # --- Lookups ---

    def get_contact(self, contact_id: str) -> Optional[Contact]:
        return self._contacts.get(contact_id)

    def get_project(self, project_id: str) -> Optional[Project]:
        return self._projects.get(project_id)

    def get_group(self, group_id: str) -> Optional[Group]:
        return self._groups.get(group_id)

    def get_document(self, doc_id: str) -> Optional[Document]:
        return self._documents.get(doc_id)

    def find_document_by_path(self, path: str) -> Optional[Document]:
        doc_id = self._path_index.get(path)
        if doc_id:
            return self._documents.get(doc_id)
        return None

    def find_contact_by_email(self, email: str) -> Optional[Contact]:
        contact_id = self._email_index.get(email.lower())
        if contact_id:
            return self._contacts.get(contact_id)
        return None

    def find_contacts_by_name(self, name: str) -> list[Contact]:
        contact_ids = self._name_index.get(name.lower(), [])
        return [self._contacts[cid] for cid in contact_ids if cid in self._contacts]

    # --- Relationship queries ---

    def get_project_members(self, project_id: str) -> set[str]:
        return self._project_members.get(project_id, set())

    def is_project_member(self, contact_id: str, project_id: str) -> bool:
        return contact_id in self._project_members.get(project_id, set())

    def find_same_name_contacts(self, name: str, exclude_id: str) -> list[Contact]:
        """Find contacts sharing a first name, excluding one by id."""
        target_first = name.split()[0].lower()
        results = []
        for contact in self._contacts.values():
            if contact.id == exclude_id:
                continue
            first = contact.name.split()[0].lower()
            if first == target_first or contact.name.lower() == name.lower():
                results.append(contact)
        return results
