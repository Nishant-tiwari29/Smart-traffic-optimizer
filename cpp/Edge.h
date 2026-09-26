#pragma once

#include <string>

struct Edge {
    std::string id;
    std::string start;
    std::string end;
    double distanceKm{};
    double speedKph{};
    double congestion{};
    double conditionSeverity{};
};
