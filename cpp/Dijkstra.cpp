#include "Dijkstra.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <queue>
#include <stdexcept>
#include <unordered_map>

namespace {
double edgeValue(const Edge& edge, const CostWeights& weights, const std::string& objective) {
    if (objective == "distance") return edge.distanceKm;
    const auto metrics = TrafficModel::calculate(edge, weights);
    return objective == "time" ? metrics.travelTimeMin : metrics.cost;
}
}

SearchResult Dijkstra::find(const Graph& graph, const std::string& source, const std::string& destination,
                            const CostWeights& weights, const std::string& objective) {
    if (!graph.nodes().count(source) || !graph.nodes().count(destination)) throw std::invalid_argument("unknown source or destination");
    using Item = std::pair<double, std::string>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> queue;
    std::unordered_map<std::string, double> distance;
    std::unordered_map<std::string, std::pair<std::string, std::string>> previous;
    for (const auto& item : graph.nodes()) distance[item.first] = std::numeric_limits<double>::infinity();
    distance[source] = 0;
    queue.push({0, source});
    std::size_t explored = 0;
    while (!queue.empty()) {
        const auto [cost, node] = queue.top();
        queue.pop();
        if (cost != distance[node]) continue;
        ++explored;
        if (node == destination) break;
        for (const auto& roadId : graph.adjacent(node)) {
            const auto& edge = graph.edges().at(roadId);
            const auto& next = edge.start == node ? edge.end : edge.start;
            const double candidate = cost + edgeValue(edge, weights, objective);
            if (candidate < distance[next]) {
                distance[next] = candidate;
                previous[next] = {node, roadId};
                queue.push({candidate, next});
            }
        }
    }
    if (!std::isfinite(distance[destination])) return {};
    SearchResult result;
    result.cost = distance[destination];
    result.nodesExplored = explored;
    for (auto cursor = destination; cursor != source;) {
        result.nodes.push_back(cursor);
        const auto& parent = previous.at(cursor);
        result.roads.push_back(parent.second);
        cursor = parent.first;
    }
    result.nodes.push_back(source);
    std::reverse(result.nodes.begin(), result.nodes.end());
    std::reverse(result.roads.begin(), result.roads.end());
    return result;
}
