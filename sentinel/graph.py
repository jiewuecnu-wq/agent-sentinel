"""Personal World State Graph — typed property graph for organizational world state.

Nodes represent entities (contacts, documents, projects, groups) with
policy-relevant attributes.  Edges represent typed, directed relationships
(MEMBER_OF, BELONGS_TO, SUCCESSOR_OF, CONTEXT_FOR, …).

This is the core knowledge structure that captures "what the agent doesn't
know but the organization does."  Sentinel's verifiers are *consumers* of
this graph; the graph itself is the reusable, extensible knowledge base.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class GraphNode:
    id: str
    node_type: str          # "contact", "document", "project", "group"
    entity: Any = None      # The typed dataclass (Contact, Document, …)


@dataclass(slots=True)
class GraphEdge:
    source: str
    target: str
    edge_type: str          # "MEMBER_OF", "BELONGS_TO", "SUCCESSOR_OF", …


class PersonalWorldStateGraph:
    """Lightweight typed property graph backed by adjacency lists.

    Usage::

        g = PersonalWorldStateGraph()
        g.add_node("alice", "contact", entity=alice_contact)
        g.add_node("proj-x", "project", entity=proj_x)
        g.add_edge("alice", "proj-x", "MEMBER_OF")

        g.neighbors("proj-x", edge_type="MEMBER_OF", direction="in")
        # → ["alice"]

        g.coverage({"alice", "bob", "proj-x"})
        # → 0.667  (bob is missing)
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._out: dict[str, list[GraphEdge]] = {}
        self._in: dict[str, list[GraphEdge]] = {}

    # ── Mutations ──────────────────────────────────────────────

    def add_node(
        self, node_id: str, node_type: str, *, entity: Any = None
    ) -> None:
        self._nodes[node_id] = GraphNode(
            id=node_id, node_type=node_type, entity=entity
        )
        self._out.setdefault(node_id, [])
        self._in.setdefault(node_id, [])

    def add_edge(self, source: str, target: str, edge_type: str) -> None:
        edge = GraphEdge(source=source, target=target, edge_type=edge_type)
        self._out.setdefault(source, []).append(edge)
        self._in.setdefault(target, []).append(edge)

    # ── Node lookups ───────────────────────────────────────────

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def nodes_by_type(self, node_type: str) -> list[GraphNode]:
        return [n for n in self._nodes.values() if n.node_type == node_type]

    # ── Graph traversal ────────────────────────────────────────

    def neighbors(
        self,
        node_id: str,
        edge_type: Optional[str] = None,
        direction: str = "out",
    ) -> list[str]:
        """Return neighbor node IDs.

        direction: "out" (default) | "in" | "both"
        """
        result: list[str] = []

        if direction in ("out", "both"):
            for e in self._out.get(node_id, []):
                if edge_type is None or e.edge_type == edge_type:
                    result.append(e.target)

        if direction in ("in", "both"):
            for e in self._in.get(node_id, []):
                if edge_type is None or e.edge_type == edge_type:
                    result.append(e.source)

        return result

    def edges_of(
        self, node_id: str, direction: str = "out"
    ) -> list[GraphEdge]:
        """Return raw edges for a node."""
        if direction == "out":
            return list(self._out.get(node_id, []))
        if direction == "in":
            return list(self._in.get(node_id, []))
        return list(self._out.get(node_id, [])) + list(
            self._in.get(node_id, [])
        )

    def has_path(
        self,
        source: str,
        target: str,
        via_types: Optional[set[str]] = None,
    ) -> bool:
        """BFS reachability check, optionally restricted to certain edge types."""
        if source not in self._nodes or target not in self._nodes:
            return False
        if source == target:
            return True

        visited: set[str] = set()
        queue: deque[str] = deque([source])

        while queue:
            current = queue.popleft()
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)

            for edge in self._out.get(current, []):
                if via_types and edge.edge_type not in via_types:
                    continue
                if edge.target not in visited:
                    queue.append(edge.target)

        return False

    # ── Coverage measurement ───────────────────────────────────

    def coverage(self, required_ids: set[str]) -> float:
        """Fraction of required entity IDs that exist as nodes in the graph."""
        if not required_ids:
            return 1.0
        present = sum(1 for rid in required_ids if rid in self._nodes)
        return present / len(required_ids)

    # ── Statistics ─────────────────────────────────────────────

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return sum(len(edges) for edges in self._out.values())

    def summary(self) -> dict[str, Any]:
        node_types: dict[str, int] = {}
        for node in self._nodes.values():
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1

        edge_types: dict[str, int] = {}
        for edges in self._out.values():
            for e in edges:
                edge_types[e.edge_type] = edge_types.get(e.edge_type, 0) + 1

        return {
            "nodes": self.node_count,
            "edges": self.edge_count,
            "node_types": node_types,
            "edge_types": edge_types,
        }

    def __repr__(self) -> str:
        s = self.summary()
        return (
            f"PersonalWorldStateGraph("
            f"nodes={s['nodes']}, edges={s['edges']}, "
            f"types={s['node_types']})"
        )
