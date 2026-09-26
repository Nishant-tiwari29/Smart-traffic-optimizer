#include "TrafficModel.h"

EdgeMetrics TrafficModel::calculate(const Edge& edge, const CostWeights& weights) {
    const double freeFlow = edge.distanceKm / edge.speedKph * 60.0;
    const double travelTime = freeFlow * (1.0 + 1.6 * edge.congestion);
    const double trafficPenalty = freeFlow * edge.congestion;
    const double conditionPenalty = freeFlow * edge.conditionSeverity;
    return {travelTime, trafficPenalty, conditionPenalty,
        weights.distance * edge.distanceKm + weights.time * travelTime +
        weights.traffic * trafficPenalty + weights.condition * conditionPenalty};
}
