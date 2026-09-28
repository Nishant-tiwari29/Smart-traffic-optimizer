from __future__ import annotations

import os
import subprocess
from pathlib import Path

from services.graph import Graph


class EngineError(RuntimeError):
    pass


def compare_with_native(graph: Graph, source: str, destination: str, weights: dict[str, float]) -> dict | None:
    executable = os.environ.get("ROUTE_ENGINE_PATH")
    if not executable:
        return None

    lines = [
        f"{len(graph.nodes)} {len(graph.edges)} {source} {destination} "
        f"{weights['distance']} {weights['time']} {weights['traffic']} {weights['condition']}"
    ]
    lines.extend(f"{node.id} {node.lat} {node.lon}" for node in graph.nodes.values())
    lines.extend(
        f"{edge.id} {edge.start} {edge.end} {edge.distance_km} {edge.speed_kph} "
        f"{edge.congestion} {edge.condition_severity}"
        for edge in graph.edges.values()
    )
    try:
        result = subprocess.run(
            [str(Path(executable).resolve())],
            input="\n".join(lines) + "\n",
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EngineError(f"Configured C++ route engine could not run: {exc}") from exc
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        raise EngineError(f"Configured C++ route engine failed: {detail}")
    parsed = {}
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) != 5 or fields[0] not in {"DIJKSTRA", "ASTAR"}:
            raise EngineError("Configured C++ route engine returned an invalid response.")
        try:
            parsed[fields[0].lower()] = {
                "cost": float(fields[1]),
                "nodes_explored": int(fields[2]),
                "path": fields[3].split("->"),
                "execution_ms": float(fields[4]),
            }
        except ValueError as exc:
            raise EngineError("Configured C++ route engine returned malformed metrics.") from exc
    if set(parsed) != {"dijkstra", "astar"}:
        raise EngineError("Configured C++ route engine omitted an algorithm result.")
    for algorithm, native in parsed.items():
        if abs(native["cost"] - parsed["dijkstra"]["cost"]) > 0.001:
            raise EngineError(f"C++ {algorithm} cost disagrees with Dijkstra on the same graph.")
    for algorithm, native in parsed.items():
        native["execution_ms"] = round(native["execution_ms"], 4)
        native["complexity"] = "O((V + E) log V)" if algorithm == "dijkstra" else "O((V + E) log V) worst case"
    return parsed
