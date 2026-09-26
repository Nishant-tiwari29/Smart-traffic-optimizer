(() => {
  async function refresh() {
    const response = await fetch("/api/statistics");
    if (!response.ok) throw new Error("Could not load network statistics.");
    const stats = await response.json();
    document.getElementById("intersection-count").textContent = stats.intersections;
    document.getElementById("road-count").textContent = stats.roads;
    document.getElementById("traffic-level").textContent = stats.traffic_level;
    document.getElementById("traffic-average").textContent = `${Math.round(stats.average_congestion * 100)}%`;
    document.getElementById("alternatives-count").textContent = stats.alternatives;
    const dot = document.getElementById("traffic-dot");
    dot.style.background = ({ Low: "#50d6bb", Moderate: "#edc75a", Heavy: "#ff9d62", Severe: "#ff6577" })[stats.traffic_level];
  }
  async function refreshHistory() {
    const response = await fetch("/api/routes/history");
    if (!response.ok) throw new Error("Could not load route history.");
    const { history } = await response.json();
    document.getElementById("history-list").innerHTML = history.length ? history.slice(0, 4).map(item => `<div class="history-item"><strong>${item.source} → ${item.destination}</strong><span>${item.optimized.distance_km} km · ${item.optimized.travel_time_min} min</span></div>`).join("") : '<div class="placeholder">Your recent routes will appear here.</div>';
  }
  async function initialize() {
    try {
      const response = await fetch("/api/roads");
      if (!response.ok) throw new Error("Could not load the road network.");
      const network = await response.json();
      window.TrafficMap.drawNetwork(network);
      const source = document.getElementById("source");
      const destination = document.getElementById("destination");
      network.nodes.forEach(node => {
        const option = new Option(`${node.id} · ${node.name}`, node.id);
        source.add(option.cloneNode(true));
        destination.add(option);
      });
      source.value = "A";
      destination.value = "H";
      const roadSelect = document.getElementById("sim-road");
      network.roads.forEach(road => roadSelect.add(new Option(`${road.id} · ${road.start} → ${road.end} · ${road.traffic_level}`, road.id)));
      await refresh();
      await refreshHistory();
      await window.TrafficRoutes.optimize();
    } catch (error) {
      document.getElementById("route-error").textContent = error.message;
    }
  }
  document.getElementById("refresh-history").addEventListener("click", refreshHistory);
  window.TrafficDashboard = { refresh, refreshHistory };
  initialize();
})();
