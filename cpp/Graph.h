#pragma once

#include "Edge.h"
#include "Node.h"
#include <string>
#include <unordered_map>
#include <vector>

class Graph {
public:
    void addNode(const Node& node);
    void addEdge(const Edge& edge);
    const std::unordered_map<std::string, Node>& nodes() const;
    const std::unordered_map<std::string, Edge>& edges() const;
    const std::vector<std::string>& adjacent(const std::string& nodeId) const;

private:
    std::unordered_map<std::string, Node> nodes_;
    std::unordered_map<std::string, Edge> edges_;
    std::unordered_map<std::string, std::vector<std::string>> adjacency_;
};
