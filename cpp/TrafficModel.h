#pragma once

#include "Edge.h"

struct CostWeights {
    double distance{0.2};
    double time{0.5};
    double traffic{0.2};
    double condition{0.1};
};

struct EdgeMetrics {
    double travelTimeMin{};
    double congestionPenalty{};
    double conditionPenalty{};
    double cost{};
};

class TrafficModel {
public:
    static EdgeMetrics calculate(const Edge& edge, const CostWeights& weights);
};
