#include "AStar.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <queue>
#include <stdexcept>
#include <tuple>
#include <unordered_map>

namespace {
double haversine(const Node& a, const Node& b) {
    constexpr double earthKm = 6371.0;
    constexpr double pi = 3.14159265358979323846;
    const double lat1 = a.latitude * pi / 180.0, lat2 = b.latitude * pi / 180.0;
    const double dlat = lat2 - lat1, dlon = (b.longitude - a.longitude) * pi / 180.0;
    const double value = std::pow(std::sin(dlat / 2), 2) +
        std::cos(lat1) * std::cos(lat2) * std::pow(std::sin(dlon / 2), 2);
    return earthKm * 2 * std::asin(std::sqrt(value));
}
}

SearchResult AStar::find(const Graph& graph, const std::string& source, const std::string& destination,
                         const CostWeights& weights) {
    if (!graph.nodes().count(source) || !graph.nodes().count(destination)) throw std::invalid_argument("unknown source or destination");
    double minimumUnitCost = std::numeric_limits<double>::infinity();
    for (const auto& item : graph.edges()) {
        const auto& edge = item.second;
        const double geometricDistance = haversine(graph.nodes().at(edge.start), graph.nodes().at(edge.end));
        if (geometricDistance > 0) {
            minimumUnitCost = std::min(minimumUnitCost,
                TrafficModel::calculate(edge, weights).cost / geometricDistance);
        }
    }
    if (!std::isfinite(minimumUnitCost)) minimumUnitCost = 0;
    auto heuristic = [&](const std::string& id) {
        return haversine(graph.nodes().at(id), graph.nodes().at(destination)) * minimumUnitCost;
    };
    using Item = std::tuple<double, double, std::string>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> queue;
    std::unordered_map<std::string, double> distance;
    std::unordered_map<std::string, std::pair<std::string, std::string>> previous;
    for (const auto& item : graph.nodes()) distance[item.first] = std::numeric_limits<double>::infinity();
    distance[source] = 0;
    queue.push({heuristic(source), 0, source});
    std::size_t explored = 0;
    while (!queue.empty()) {
        const auto [priority, cost, node] = queue.top();
        (void)priority;
        queue.pop();
        if (cost != distance[node]) continue;
        ++explored;
        if (node == destination) break;
        for (const auto& roadId : graph.adjacent(node)) {
            const auto& edge = graph.edges().at(roadId);
            const auto& next = edge.start == node ? edge.end : edge.start;
            const double candidate = cost + TrafficModel::calculate(edge, weights).cost;
            if (candidate < distance[next]) {
                distance[next] = candidate;
                previous[next] = {node, roadId};
                queue.push({candidate + heuristic(next), candidate, next});
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
