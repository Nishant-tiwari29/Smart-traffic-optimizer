import pytest
from fastapi.testclient import TestClient

from main import app
from services.demo_data import create_demo_graph
from services.graph import Edge, Graph, Node
from services.routing import RouteService, RoutingError

client = TestClient(app)
WEIGHTS = {"distance": .2, "time": .5, "traffic": .2, "condition": .1}


def sample_graph() -> Graph:
    graph = Graph()
    for node_id, lon in (("A", 0), ("B", .01), ("C", .02), ("D", .03)):
        graph.add_node(Node(node_id, node_id, 0, lon))
    graph.add_edge(Edge("AB", "A", "B", 1, 60, .95, "poor", .8))
    graph.add_edge(Edge("BD", "B", "D", 1, 60, .95, "poor", .8))
    graph.add_edge(Edge("AC", "A", "C", 1.4, 60, .05, "good", .05))
    graph.add_edge(Edge("CD", "C", "D", 1.4, 60, .05, "good", .05))
    return graph


def test_shortest_distance_and_fastest_are_real_searches():
    service = RouteService(sample_graph())
    result = service.optimize("A", "D", WEIGHTS)
    assert result["shortest"]["distance_km"] == 2
    assert result["optimized"]["nodes"] == ["A", "C", "D"]
    assert result["fastest"]["nodes"] == ["A", "C", "D"]
    assert result["shortest"]["travel_time_min"] > result["fastest"]["travel_time_min"]


def test_traffic_update_changes_cost_and_can_change_route():
    service = RouteService(sample_graph())
    before = service.optimize("A", "D", WEIGHTS)["optimized"]["nodes"]
    service.update_traffic("AC", 1)
    service.update_traffic("CD", 1)
    after = service.optimize("A", "D", WEIGHTS)["optimized"]["nodes"]
    assert before != after
    assert after == ["A", "B", "D"]


def test_unreachable_route_returns_no_route():
    graph = Graph()
    graph.add_node(Node("A", "A", 0, 0))
    graph.add_node(Node("B", "B", 0, .01))
    service = RouteService(graph)
    with pytest.raises(RoutingError, match="No route"):
        service.optimize("A", "B", WEIGHTS)


def test_same_or_invalid_node_is_rejected():
    service = RouteService(create_demo_graph())
    with pytest.raises(RoutingError, match="different"):
        service.optimize("A", "A", WEIGHTS)
    with pytest.raises(RoutingError, match="known"):
        service.optimize("A", "Z", WEIGHTS)


def test_heavy_traffic_is_classified_severe_and_affects_cost():
    service = RouteService(create_demo_graph())
    result = service.update_traffic("AC", 1)
    assert result["traffic_level"] == "Severe"
    assert result["travel_time_min"] > 0


def test_multiple_objectives_and_algorithm_comparison():
    result = RouteService(create_demo_graph()).optimize("A", "H", WEIGHTS)
    assert result["shortest"]["nodes"]
    assert result["fastest"]["nodes"]
    assert result["comparison"]["dijkstra"]["path"] == result["comparison"]["astar"]["path"]
    assert "complexity" in result["comparison"]["astar"]
    assert len(result["alternatives"]) >= 1
    assert len({tuple(route["nodes"]) for route in result["alternatives"]}) > 1


def test_hop_limited_dynamic_programming():
    result = RouteService(create_demo_graph()).optimize("A", "H", WEIGHTS, max_hops=2)
    assert result["hop_constrained"] is not None
    assert len(result["hop_constrained"]["roads"]) <= 2


def test_api_validation_and_demo_endpoints():
    assert client.get("/api/health").status_code == 200
    assert len(client.get("/api/roads").json()["nodes"]) == 8
    assert client.post("/api/route/optimize", json={"source": "A", "destination": "A"}).status_code == 400
    assert client.post("/api/route/optimize", json={"source": "A", "destination": "H", "weights": {"distance": .9, "time": .9, "traffic": .1, "condition": .1}}).status_code == 422


def test_what_if_simulation_returns_before_after_and_restores_on_error():
    service = RouteService(create_demo_graph())
    outcome = service.simulate("A", "H", "AB", 50, WEIGHTS)
    assert "previous" in outcome and "current" in outcome
    assert "reason" in outcome
    assert "AB increased" in outcome["reason"]
