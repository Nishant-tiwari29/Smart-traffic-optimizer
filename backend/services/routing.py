from __future__ import annotations

from heapq import heappop, heappush
from math import inf
from time import perf_counter

from cpp_engine.bridge import EngineError, compare_with_native
from services.graph import Edge, Graph, haversine_km

CONGESTION_LABELS = ((0.25, "Low"), (0.50, "Moderate"), (0.75, "Heavy"), (1.01, "Severe"))


class RoutingError(ValueError):
    pass


class RouteService:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.history: list[dict] = []

    @staticmethod
    def _edge_metrics(edge: Edge, weights: dict[str, float]) -> dict:
        free_flow = edge.distance_km / edge.speed_kph * 60
        travel_time = free_flow * (1 + 1.6 * edge.congestion)
        congestion_penalty = free_flow * edge.congestion
        condition_penalty = free_flow * edge.condition_severity
        cost = (
            weights["distance"] * edge.distance_km
            + weights["time"] * travel_time
            + weights["traffic"] * congestion_penalty
            + weights["condition"] * condition_penalty
        )
        label = next(label for threshold, label in CONGESTION_LABELS if edge.congestion < threshold)
        return {
            "travel_time_min": travel_time,
            "congestion_penalty": congestion_penalty,
            "condition_penalty": condition_penalty,
            "cost": cost,
            "traffic_level": label,
        }

    def _edge_cost(self, edge: Edge, objective: str, weights: dict[str, float]) -> float:
        metrics = self._edge_metrics(edge, weights)
        if objective == "distance":
            return edge.distance_km
        if objective == "time":
            return metrics["travel_time_min"]
        return metrics["cost"]

    def _search(self, source: str, destination: str, objective: str, weights: dict[str, float], excluded: str | None = None) -> dict:
        if source not in self.graph.nodes or destination not in self.graph.nodes:
            raise RoutingError("Source or destination is not a known intersection.")
        if source == destination:
            return self._make_route([source], [], objective, weights, 0, 0)

        minimum_cost_per_km = min(
            self._edge_cost(edge, objective, weights) / geometric_distance
            for edge in self.graph.edges.values()
            if edge.id != excluded
            for geometric_distance in [
                haversine_km(self.graph.nodes[edge.start], self.graph.nodes[edge.end])
            ]
            if geometric_distance > 0
        ) if len(self.graph.edges) > (1 if excluded else 0) else 0
        if minimum_cost_per_km == inf:
            minimum_cost_per_km = 0

        def heuristic(node_id: str) -> float:
            if objective != "cost":
                return 0
            return haversine_km(self.graph.nodes[node_id], self.graph.nodes[destination]) * minimum_cost_per_km

        distances = {node_id: inf for node_id in self.graph.nodes}
        distances[source] = 0
        previous: dict[str, tuple[str, str]] = {}
        queue = [(heuristic(source), 0.0, source)]
        explored = 0
        while queue:
            _, distance, node_id = heappop(queue)
            if distance != distances[node_id]:
                continue
            explored += 1
            if node_id == destination:
                break
            for edge_id in self.graph.adjacency[node_id]:
                if edge_id == excluded:
                    continue
                edge = self.graph.edges[edge_id]
                neighbor = edge.end if edge.start == node_id else edge.start
                candidate = distance + self._edge_cost(edge, objective, weights)
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    previous[neighbor] = (node_id, edge_id)
                    heappush(queue, (candidate + heuristic(neighbor), candidate, neighbor))
        if distances[destination] == inf:
            return None
        node_path, edge_path = [destination], []
        cursor = destination
        while cursor != source:
            parent, edge_id = previous[cursor]
            node_path.append(parent)
            edge_path.append(edge_id)
            cursor = parent
        route = self._make_route(list(reversed(node_path)), list(reversed(edge_path)), objective, weights, distances[destination], explored)
        return route

    def _make_route(self, nodes: list[str], edges: list[str], objective: str, weights: dict[str, float], search_cost: float, explored: int) -> dict:
        distance = sum(self.graph.edges[e].distance_km for e in edges)
        time = sum(self._edge_metrics(self.graph.edges[e], weights)["travel_time_min"] for e in edges)
        cost = sum(self._edge_metrics(self.graph.edges[e], weights)["cost"] for e in edges)
        traffic = max((self.graph.edges[e].congestion for e in edges), default=0)
        traffic_level = "Low" if traffic < .25 else "Moderate" if traffic < .5 else "Heavy" if traffic < .75 else "Severe"
        return {
            "nodes": nodes,
            "roads": edges,
            "distance_km": round(distance, 2),
            "travel_time_min": round(time, 1),
            "traffic_level": traffic_level,
            "max_congestion": round(traffic, 2),
            "cost": round(cost, 3),
            "objective": objective,
            "search_cost": round(search_cost, 3),
            "nodes_explored": explored,
        }

    def _astar(self, source: str, destination: str, weights: dict[str, float]) -> dict:
        return self._search(source, destination, "cost", weights)

    def _dijkstra(self, source: str, destination: str, weights: dict[str, float]) -> dict:
        return self._search(source, destination, "cost", weights)

    def _constrained_dp(self, source: str, destination: str, weights: dict[str, float], max_hops: int) -> dict | None:
        if source not in self.graph.nodes or destination not in self.graph.nodes:
            raise RoutingError("Source or destination is not a known intersection.")
        # Each layer records the cheapest path using exactly k roads.
        previous = {source: (0.0, [source], [])}
        explored = 0
        best = None
        for _ in range(max_hops):
            current = dict(previous)
            for node_id, (cost, path, roads) in previous.items():
                for edge_id in self.graph.adjacency[node_id]:
                    edge = self.graph.edges[edge_id]
                    neighbor = edge.end if edge.start == node_id else edge.start
                    candidate = cost + self._edge_cost(edge, "cost", weights)
                    explored += 1
                    incumbent = current.get(neighbor)
                    if incumbent is None or candidate < incumbent[0]:
                        current[neighbor] = (candidate, path + [neighbor], roads + [edge_id])
            previous = current
            candidate = previous.get(destination)
            if candidate and (best is None or candidate[0] < best[0]):
                best = candidate
        if best is None:
            return None
        return self._make_route(best[1], best[2], "cost", weights, best[0], explored)

    def optimize(self, source: str, destination: str, weights: dict[str, float], max_hops: int | None = None) -> dict:
        source, destination = source.strip().upper(), destination.strip().upper()
        if source not in self.graph.nodes or destination not in self.graph.nodes:
            raise RoutingError("Source or destination is not a known intersection.")
        if source == destination:
            raise RoutingError("Source and destination must be different.")

        started = perf_counter()
        dijkstra = self._dijkstra(source, destination, weights)
        dijkstra_ms = (perf_counter() - started) * 1000
        started = perf_counter()
        astar = self._astar(source, destination, weights)
        astar_ms = (perf_counter() - started) * 1000
        if dijkstra is None:
            raise RoutingError("No route connects the selected intersections.")
        native_comparison = compare_with_native(self.graph, source, destination, weights)

        shortest = self._search(source, destination, "distance", weights)
        fastest = self._search(source, destination, "time", weights)
        alternatives = []
        for route in (shortest, fastest, dijkstra):
            if route and route["nodes"] not in [r["nodes"] for r in alternatives]:
                alternatives.append(route)
        deviations = [
            self._search(source, destination, "cost", weights, excluded=road_id)
            for road_id in dijkstra["roads"]
        ]
        deviations = [
            route for route in deviations
            if route and route["nodes"] not in [candidate["nodes"] for candidate in alternatives]
        ]
        if deviations:
            alternatives.append(min(deviations, key=lambda route: route["cost"]))
        result = {
            "source": source,
            "destination": destination,
            "optimized": astar,
            "shortest": shortest,
            "fastest": fastest,
            "alternatives": alternatives,
            "comparison": {
                "dijkstra": {"execution_ms": round(dijkstra_ms, 4), "nodes_explored": dijkstra["nodes_explored"], "cost": dijkstra["cost"], "path": dijkstra["nodes"], "complexity": "O((V + E) log V)"},
                "astar": {"execution_ms": round(astar_ms, 4), "nodes_explored": astar["nodes_explored"], "cost": astar["cost"], "path": astar["nodes"], "complexity": "O((V + E) log V) worst case"},
            },
            "network": {"intersections": len(self.graph.nodes), "roads": len(self.graph.edges)},
        }
        if native_comparison:
            result["comparison"] = native_comparison
        if max_hops is not None:
            result["hop_constrained"] = self._constrained_dp(source, destination, weights, max_hops)
        self.history.insert(0, result)
        del self.history[50:]
        return result

    def network(self) -> dict:
        return {
            "nodes": [vars(node) for node in self.graph.nodes.values()],
            "roads": [self._road_data(edge, {"distance": .2, "time": .5, "traffic": .2, "condition": .1}) for edge in self.graph.edges.values()],
        }

    def _road_data(self, edge: Edge, weights: dict[str, float]) -> dict:
        return {
            "id": edge.id,
            "start": edge.start,
            "end": edge.end,
            "distance_km": edge.distance_km,
            "speed_kph": edge.speed_kph,
            "congestion": edge.congestion,
            "condition": edge.condition,
            **self._edge_metrics(edge, weights),
        }

    def traffic(self) -> list[dict]:
        weights = {"distance": .2, "time": .5, "traffic": .2, "condition": .1}
        return [self._road_data(edge, weights) for edge in self.graph.edges.values()]

    def update_traffic(self, road_id: str, congestion: float) -> dict:
        if road_id not in self.graph.edges:
            raise RoutingError(f"Unknown road: {road_id}")
        if not 0 <= congestion <= 1:
            raise RoutingError("Congestion must be between 0 and 1.")
        self.graph.edges[road_id].congestion = congestion
        return next(road for road in self.traffic() if road["id"] == road_id)

    def simulate(self, source: str, destination: str, road_id: str, increase_percent: float, weights: dict[str, float]) -> dict:
        if road_id not in self.graph.edges:
            raise RoutingError(f"Unknown road: {road_id}")
        before = self.optimize(source, destination, weights)
        old_value = self.graph.edges[road_id].congestion
        self.graph.edges[road_id].congestion = min(1.0, old_value * (1 + increase_percent / 100))
        try:
            after = self.optimize(source, destination, weights)
        except (RoutingError, EngineError):
            self.graph.edges[road_id].congestion = old_value
            raise
        return {
            "previous": before["optimized"],
            "current": after["optimized"],
            "change": {
                "travel_time_min": round(after["optimized"]["travel_time_min"] - before["optimized"]["travel_time_min"], 1),
                "distance_km": round(after["optimized"]["distance_km"] - before["optimized"]["distance_km"], 2),
            },
            "reason": (
                f"Congestion on {road_id} increased from {old_value:.0%} to "
                f"{self.graph.edges[road_id].congestion:.0%}; "
                + (
                    f"the optimizer switched from {' → '.join(before['optimized']['nodes'])} "
                    f"to {' → '.join(after['optimized']['nodes'])} because the revised road costs made that path cheaper."
                    if before["optimized"]["nodes"] != after["optimized"]["nodes"]
                    else "the selected path remained the lowest-cost option after recalculation."
                )
            ),
            "traffic": self.traffic(),
        }

    def statistics(self) -> dict:
        levels = {"Low": 0, "Moderate": 0, "Heavy": 0, "Severe": 0}
        traffic = self.traffic()
        for road in traffic:
            levels[road["traffic_level"]] += 1
        average = sum(road["congestion"] for road in traffic) / len(traffic) if traffic else 0
        level = "Low" if average < .25 else "Moderate" if average < .5 else "Heavy" if average < .75 else "Severe"
        last = self.history[0]["optimized"] if self.history else None
        return {
            "roads": len(self.graph.edges),
            "intersections": len(self.graph.nodes),
            "traffic_level": level,
            "average_congestion": round(average, 2),
            "traffic_distribution": levels,
            "latest_route": last,
            "alternatives": len(self.history[0]["alternatives"]) - 1 if self.history else 0,
            "history_count": len(self.history),
        }
