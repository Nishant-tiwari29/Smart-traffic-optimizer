#pragma once

#include "Graph.h"
#include "TrafficModel.h"
#include <string>
#include <vector>

struct SearchResult {
    std::vector<std::string> nodes;
    std::vector<std::string> roads;
    double cost{};
    std::size_t nodesExplored{};
};

class Dijkstra {
public:
    static SearchResult find(const Graph& graph, const std::string& source,
                             const std::string& destination, const CostWeights& weights,
                             const std::string& objective = "cost");
};
