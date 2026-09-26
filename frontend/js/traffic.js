(() => {
  const form = document.getElementById("simulation-form");
  const slider = document.getElementById("increase-percent");
  slider.addEventListener("input", () => { document.getElementById("increase-value").textContent = `${slider.value}%`; });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const source = document.getElementById("source").value;
    const destination = document.getElementById("destination").value;
    if (!source || !destination || source === destination) {
      document.getElementById("simulation-result").textContent = "Select a valid source and destination before simulating.";
      return;
    }
    try {
      const response = await fetch("/api/simulation", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source, destination, road_id: document.getElementById("sim-road").value,
          increase_percent: Number(slider.value),
          weights: {
            distance: Number(document.getElementById("w-distance").value),
            time: Number(document.getElementById("w-time").value),
            traffic: Number(document.getElementById("w-traffic").value),
            condition: Number(document.getElementById("w-condition").value)
          }
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Simulation failed.");
      const changed = data.previous.nodes.join(",") !== data.current.nodes.join(",");
      document.getElementById("simulation-result").innerHTML = `${changed ? `<b>Route changed:</b> ${data.previous.nodes.join(" → ")} → ${data.current.nodes.join(" → ")}` : `<b>Route unchanged:</b> ${data.current.nodes.join(" → ")}`} · ${data.change.travel_time_min > 0 ? "+" : ""}${data.change.travel_time_min} min · ${data.change.distance_km > 0 ? "+" : ""}${data.change.distance_km} km. ${data.reason}`;
      const refreshed = await fetch("/api/roads");
      window.TrafficMap.drawNetwork(await refreshed.json());
      await window.TrafficRoutes.optimize();
      window.TrafficDashboard.refreshHistory();
    } catch (exception) {
      document.getElementById("simulation-result").textContent = exception.message;
    }
  });
})();
