(() => {
  const form = document.getElementById("route-form");
  const error = document.getElementById("route-error");
  let lastResult;
  const weights = () => ({
    distance: Number(document.getElementById("w-distance").value),
    time: Number(document.getElementById("w-time").value),
    traffic: Number(document.getElementById("w-traffic").value),
    condition: Number(document.getElementById("w-condition").value)
  });
  const routeName = route => route.nodes.join(" → ");
  const showRoute = result => {
    lastResult = result;
    document.getElementById("route-result").innerHTML = `<div class="result-highlight">
      <div><small>BEST ROUTE</small><strong>${routeName(result.optimized)}</strong></div>
      <div><small>DISTANCE</small><strong>${result.optimized.distance_km} km</strong></div>
      <div><small>EST. TIME</small><strong>${result.optimized.travel_time_min} min</strong></div>
    </div><p class="result-reason">Minimum generalized cost <b>${result.optimized.cost}</b> · ${result.optimized.traffic_level} peak traffic · A* explored ${result.comparison.astar.nodes_explored} intersections. ${result.hop_constrained ? `Hop-constrained DP: ${result.hop_constrained.nodes.join(" → ")}.` : ""}</p>`;
    const cards = [
      ["Shortest distance", "DISTANCE OPTIMUM", result.shortest],
      ["Fastest time", "TIME OPTIMUM", result.fastest],
      ["Traffic optimized", "LOWEST GENERALIZED COST", result.optimized]
    ];
    document.getElementById("route-options").innerHTML = cards.map(([title, sub, route], i) => `<div class="route-option ${i === 2 ? "selected" : ""}">
      <div class="option-title">${title}</div><div class="option-caption">${sub}</div>
      <div class="option-metrics"><span><strong>${route.distance_km}</strong> km</span><span><strong>${route.travel_time_min}</strong> min</span></div>
      <div class="option-caption">${route.nodes.join(" → ")}</div></div>`).join("");
    const entries = ["dijkstra", "astar"].map(key => {
      const value = result.comparison[key];
      return `<div class="comparison-row"><strong>${key === "astar" ? "A* Search" : "Dijkstra"}</strong><span>${value.nodes_explored}</span><span>${value.execution_ms} ms</span><span>${value.cost}</span></div>`;
    }).join("");
    document.getElementById("comparison-rows").innerHTML = entries;
    window.TrafficMap.drawRoutes(result);
    window.TrafficDashboard.refresh();
    return result;
  };
  async function optimize() {
    error.textContent = "";
    const source = document.getElementById("source").value;
    const destination = document.getElementById("destination").value;
    if (source === destination) {
      error.textContent = "Choose two different intersections.";
      return;
    }
    const costWeights = weights();
    if (Object.values(costWeights).some(value => !Number.isFinite(value) || value < 0) || Math.abs(Object.values(costWeights).reduce((a, b) => a + b, 0) - 1) > .001) {
      error.textContent = "Cost weights must be non-negative and sum to 1.";
      return;
    }
    const body = { source, destination, weights: costWeights };
    if (document.getElementById("hop-enabled").checked) body.max_hops = Number(document.getElementById("max-hops").value);
    try {
      const response = await fetch("/api/route/optimize", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Unable to find a route.");
      showRoute(payload);
      await window.TrafficDashboard.refreshHistory();
    } catch (exception) { error.textContent = exception.message; }
  }
  form.addEventListener("submit", event => { event.preventDefault(); optimize(); });
  document.getElementById("hop-enabled").addEventListener("change", event => {
    document.getElementById("max-hops").hidden = !event.target.checked;
  });
  window.TrafficRoutes = { optimize, showRoute, getLast: () => lastResult };
})();
