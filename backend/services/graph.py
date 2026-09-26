from __future__ import annotations

from dataclasses import dataclass, field
from math import asin, cos, radians, sin, sqrt


@dataclass
class Node:
    id: str
    name: str
    lat: float
    lon: float


@dataclass
class Edge:
    id: str
    start: str
    end: str
    distance_km: float
    speed_kph: float
    congestion: float
    condition: str
    condition_severity: float


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: dict[str, Edge] = field(default_factory=dict)
    adjacency: dict[str, list[str]] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Duplicate intersection: {node.id}")
        self.nodes[node.id] = node
        self.adjacency[node.id] = []

    def add_edge(self, edge: Edge) -> None:
        if edge.id in self.edges:
            raise ValueError(f"Duplicate road: {edge.id}")
        if edge.start not in self.nodes or edge.end not in self.nodes:
            raise ValueError(f"Road {edge.id} references an unknown intersection")
        if edge.distance_km <= 0 or edge.speed_kph <= 0:
            raise ValueError("Road distance and speed must be positive")
        if not 0 <= edge.congestion <= 1 or not 0 <= edge.condition_severity <= 1:
            raise ValueError("Road traffic and condition severity must be within [0, 1]")
        self.edges[edge.id] = edge
        self.adjacency[edge.start].append(edge.id)
        self.adjacency[edge.end].append(edge.id)


def haversine_km(a: Node, b: Node) -> float:
    radius = 6371.0
    lat1, lat2 = radians(a.lat), radians(b.lat)
    dlat, dlon = lat2 - lat1, radians(b.lon - a.lon)
    value = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(value))
