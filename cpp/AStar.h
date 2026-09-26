#pragma once

#include "Dijkstra.h"

class AStar {
public:
    static SearchResult find(const Graph& graph, const std::string& source,
                             const std::string& destination, const CostWeights& weights);
};
