#include "Graph.h"
#include <stdexcept>

void Graph::addNode(const Node& node) {
    if (!nodes_.emplace(node.id, node).second) throw std::invalid_argument("duplicate node: " + node.id);
    adjacency_[node.id] = {};
}

void Graph::addEdge(const Edge& edge) {
    if (edges_.count(edge.id)) throw std::invalid_argument("duplicate road: " + edge.id);
    if (!nodes_.count(edge.start) || !nodes_.count(edge.end)) throw std::invalid_argument("unknown road endpoint");
    if (edge.distanceKm <= 0 || edge.speedKph <= 0 || edge.congestion < 0 || edge.congestion > 1 ||
        edge.conditionSeverity < 0 || edge.conditionSeverity > 1) throw std::invalid_argument("invalid road metrics");
    edges_.emplace(edge.id, edge);
    adjacency_[edge.start].push_back(edge.id);
    adjacency_[edge.end].push_back(edge.id);
}

const std::unordered_map<std::string, Node>& Graph::nodes() const { return nodes_; }
const std::unordered_map<std::string, Edge>& Graph::edges() const { return edges_; }

const std::vector<std::string>& Graph::adjacent(const std::string& nodeId) const {
    const auto found = adjacency_.find(nodeId);
    if (found == adjacency_.end()) throw std::invalid_argument("unknown node: " + nodeId);
    return found->second;
}
