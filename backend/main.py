from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from schemas.requests import OptimizeRequest, SimulationRequest, TrafficUpdateRequest
from cpp_engine.bridge import EngineError
from database.store import DatabaseError, MySQLStore
from services.demo_data import create_demo_graph
from services.routing import RouteService, RoutingError

ROOT = Path(__file__).resolve().parents[1]
graph = create_demo_graph()
database = MySQLStore.from_environment()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if database:
        database.verify_and_load(graph)
    yield


app = FastAPI(title="Smart Traffic Route Optimizer", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

service = RouteService(graph)


def route_or_400(request: OptimizeRequest) -> dict:
    try:
        result = service.optimize(
            request.source,
            request.destination,
            request.weights.model_dump(),
            request.max_hops,
        )
        if database:
            database.save_route(result)
        return result
    except RoutingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EngineError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/roads")
def roads() -> dict:
    return service.network()


@app.get("/api/traffic")
def traffic() -> dict:
    return {"traffic": service.traffic()}


@app.post("/api/route/optimize")
def optimize(request: OptimizeRequest) -> dict:
    return route_or_400(request)


@app.post("/api/traffic/update")
def update_traffic(request: TrafficUpdateRequest) -> dict:
    old_congestion = service.graph.edges.get(request.road_id)
    previous_value = old_congestion.congestion if old_congestion else None
    try:
        road = service.update_traffic(request.road_id, request.congestion)
        if database:
            try:
                database.save_traffic(request.road_id, request.congestion)
            except DatabaseError:
                service.graph.edges[request.road_id].congestion = previous_value
                raise
        return {"road": road}
    except RoutingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/simulation")
def simulate(request: SimulationRequest) -> dict:
    prior_congestion = service.graph.edges.get(request.road_id)
    previous_value = prior_congestion.congestion if prior_congestion else None
    previous_history = list(service.history)
    try:
        outcome = service.simulate(
            request.source,
            request.destination,
            request.road_id,
            request.increase_percent,
            request.weights.model_dump(),
        )
        if database:
            database.save_simulation(
                request.road_id,
                service.graph.edges[request.road_id].congestion,
                {
                **service.history[1],
                "optimized": outcome["current"],
                },
            )
        return outcome
    except RoutingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EngineError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except DatabaseError as exc:
        if previous_value is not None:
            service.graph.edges[request.road_id].congestion = previous_value
            service.history[:] = previous_history
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/routes/history")
def history() -> dict:
    try:
        return {"history": database.route_history() if database else service.history}
    except DatabaseError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/statistics")
def statistics() -> dict:
    return service.statistics()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
