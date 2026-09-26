#include "RouteOptimizer.h"
#include <chrono>
#include <iomanip>
#include <iostream>
#include <stdexcept>

int main() {
    try {
        Graph graph;
        std::size_t nodeCount = 0, edgeCount = 0;
        CostWeights weights;
        std::string source, destination;
        if (!(std::cin >> nodeCount >> edgeCount >> source >> destination
              >> weights.distance >> weights.time >> weights.traffic >> weights.condition))
            throw std::runtime_error("expected header: node_count edge_count source destination wd wt wc wr");
        for (std::size_t i = 0; i < nodeCount; ++i) {
            Node node;
            if (!(std::cin >> node.id >> node.latitude >> node.longitude)) throw std::runtime_error("invalid node row");
            graph.addNode(node);
        }
        for (std::size_t i = 0; i < edgeCount; ++i) {
            Edge edge;
            if (!(std::cin >> edge.id >> edge.start >> edge.end >> edge.distanceKm >> edge.speedKph
                  >> edge.congestion >> edge.conditionSeverity)) throw std::runtime_error("invalid road row");
            graph.addEdge(edge);
        }
        const auto dijkstraStart = std::chrono::steady_clock::now();
        const auto dijkstra = Dijkstra::find(graph, source, destination, weights);
        const auto dijkstraEnd = std::chrono::steady_clock::now();
        const auto aStarStart = std::chrono::steady_clock::now();
        const auto aStar = AStar::find(graph, source, destination, weights);
        const auto aStarEnd = std::chrono::steady_clock::now();
        if (dijkstra.nodes.empty() || aStar.nodes.empty()) {
            std::cout << "NO_ROUTE\n";
            return 2;
        }
        const double dijkstraMs = std::chrono::duration<double, std::milli>(dijkstraEnd - dijkstraStart).count();
        const double aStarMs = std::chrono::duration<double, std::milli>(aStarEnd - aStarStart).count();
        auto print = [](const char* name, const SearchResult& route, double elapsedMs) {
            std::cout << name << '\t' << std::fixed << std::setprecision(3) << route.cost << '\t'
                      << route.nodesExplored << '\t';
            for (std::size_t i = 0; i < route.nodes.size(); ++i) std::cout << (i ? "->" : "") << route.nodes[i];
            std::cout << '\t' << std::setprecision(6) << elapsedMs << '\n';
        };
        print("DIJKSTRA", dijkstra, dijkstraMs);
        print("ASTAR", aStar, aStarMs);
    } catch (const std::exception& error) {
        std::cerr << "route_engine: " << error.what() << '\n';
        return 1;
    }
}
