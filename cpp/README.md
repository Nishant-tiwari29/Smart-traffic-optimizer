# C++17 route engine

The C++ modules implement graph storage, dynamic edge costs, Dijkstra, admissible A*, and an optimizer that compares the two results. The FastAPI service can call the compiled engine through `backend/cpp_engine/bridge.py`. Set `ROUTE_ENGINE_PATH` to the executable path before starting the API. The native engine's path, cost, and explored-node data populate the algorithm comparison. If the variable is absent, the service runs its equivalent Python graph searches.

Compile from the repository root:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra cpp/main.cpp cpp/Graph.cpp cpp/TrafficModel.cpp cpp/Dijkstra.cpp cpp/AStar.cpp cpp/RouteOptimizer.cpp -o cpp/route_engine
```

Set `ROUTE_ENGINE_PATH` to the resulting binary (for example, in PowerShell `$env:ROUTE_ENGINE_PATH = (Resolve-Path .\cpp\route_engine).Path`) before starting Uvicorn.

Input is whitespace separated, one record per line:

```text
node_count edge_count source destination distance_weight time_weight traffic_weight condition_weight
node_id latitude longitude
... one row per node
road_id start_id end_id distance_km speed_kph congestion_fraction condition_severity
... one row per road
```

Example graph:

```text
4 4 A D 0.2 0.5 0.2 0.1
A 0 0
B 0 0.01
C 0 0.02
D 0 0.03
AB A B 1 60 0.95 0.8
BD B D 1 60 0.95 0.8
AC A C 1.4 60 0.05 0.05
CD C D 1.4 60 0.05 0.05
```

Output is `DIJKSTRA` and `ASTAR` rows containing generalized cost, explored nodes, and reconstructed path. Invalid input is reported on stderr and exits non-zero. Complexity is `O((V+E)log V)` time and `O(V+E)` space for each search.
