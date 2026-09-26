(() => {
  const map = L.map("map", { zoomControl: false }).setView([37.782, -122.409], 13);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);
  const roadsLayer = L.layerGroup().addTo(map);
  const routesLayer = L.layerGroup().addTo(map);
  const markersLayer = L.layerGroup().addTo(map);
  const colors = { Low: "#43c9ae", Moderate: "#edc75a", Heavy: "#ff9d62", Severe: "#ff6577" };
  let network;

  function drawNetwork(data) {
    network = data;
    roadsLayer.clearLayers();
    data.roads.forEach(road => {
      const from = data.nodes.find(node => node.id === road.start);
      const to = data.nodes.find(node => node.id === road.end);
      const line = L.polyline([[from.lat, from.lon], [to.lat, to.lon]], {
        color: colors[road.traffic_level], weight: 4, opacity: .72
      }).addTo(roadsLayer);
      line.bindTooltip(`${road.id} · ${road.traffic_level} traffic · ${Math.round(road.congestion * 100)}%`);
    });
    data.nodes.forEach(node => {
      L.circleMarker([node.lat, node.lon], { radius: 4, color: "#b9c7d9", weight: 1, fillColor: "#18283a", fillOpacity: 1 })
        .bindTooltip(`${node.id} · ${node.name}`).addTo(roadsLayer);
    });
  }

  function drawRoutes(result) {
    routesLayer.clearLayers();
    markersLayer.clearLayers();
    if (!network || !result) return;
    (result.alternatives || []).filter(route => route.nodes.join(",") !== result.optimized.nodes.join(",")).forEach(route => {
      const points = route.nodes.map(id => network.nodes.find(node => node.id === id)).map(node => [node.lat, node.lon]);
      L.polyline(points, { color: "#91a2ba", weight: 4, opacity: .78, dashArray: "5 7" }).addTo(routesLayer);
    });
    const best = result.optimized.nodes.map(id => network.nodes.find(node => node.id === id));
    L.polyline(best.map(node => [node.lat, node.lon]), { color: "#50d6bb", weight: 6, opacity: .96 }).addTo(routesLayer);
    [best[0], best[best.length - 1]].forEach((node, index) => {
      L.circleMarker([node.lat, node.lon], { radius: 8, color: index ? "#ff7582" : "#50d6bb", weight: 3, fillColor: "#102032", fillOpacity: 1 })
        .bindTooltip(index ? `Destination · ${node.name}` : `Origin · ${node.name}`).addTo(markersLayer);
    });
    map.fitBounds(L.latLngBounds(best.map(node => [node.lat, node.lon])).pad(.25));
  }

  window.TrafficMap = { drawNetwork, drawRoutes, map };
})();
