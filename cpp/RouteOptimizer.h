#pragma once

#include "AStar.h"

struct RouteComparison {
    SearchResult dijkstra;
    SearchResult aStar;
};

class RouteOptimizer {
public:
    static RouteComparison compare(const Graph& graph, const std::string& source,
                                   const std::string& destination, const CostWeights& weights);
};
