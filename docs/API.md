# API reference

FastAPI root: `http://127.0.0.1:8000`; interactive schema and Try-it-out: `/docs`. JSON errors use HTTP 400 for routing/domain errors and HTTP 422 for invalid request shape/ranges.

## `GET /api/roads`

Returns `nodes` (`id`, `name`, `lat`, `lon`) and `roads` with endpoints, distance, speed, congestion fraction, condition, derived cost, travel time and traffic level.

## `GET /api/traffic`

Returns current traffic and derived edge metrics.

## `POST /api/route/optimize`

```json
{
  "source": "A",
  "destination": "H",
  "weights": {"distance": 0.2, "time": 0.5, "traffic": 0.2, "condition": 0.1},
  "max_hops": 4
}
```

`weights` and `max_hops` are optional. Weight values must be non-negative and sum to one; hops, if set, are 1–100. Response includes `optimized`, `shortest`, `fastest`, distinct `alternatives`, `comparison` with real Dijkstra/A* timings and explored-node counts, and an optional `hop_constrained` DP result. Identical or unknown endpoints are rejected.

## `POST /api/traffic/update`

```json
{"road_id": "AB", "congestion": 0.75}
```

Congestion is a fraction in `[0,1]`; updates the in-memory edge.

## `POST /api/simulation`

```json
{
  "source": "A", "destination": "H", "road_id": "AB",
  "increase_percent": 50,
  "weights": {"distance": 0.2, "time": 0.5, "traffic": 0.2, "condition": 0.1}
}
```

Scales selected edge congestion by `1 + increase_percent/100`, capped at one, and returns `previous`, `current`, metric `change`, reason, and updated traffic list.

## `GET /api/routes/history`

Returns at most 50 most recent optimization results in the current server process.

## `GET /api/statistics`

Returns network sizes, average congestion and level, distribution, latest route, alternative count, and history size.

## `GET /api/health`

Returns `{"status":"ok"}`.
