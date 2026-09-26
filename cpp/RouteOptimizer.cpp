#include "RouteOptimizer.h"

RouteComparison RouteOptimizer::compare(const Graph& graph, const std::string& source,
                                        const std::string& destination, const CostWeights& weights) {
    return {Dijkstra::find(graph, source, destination, weights), AStar::find(graph, source, destination, weights)};
}
