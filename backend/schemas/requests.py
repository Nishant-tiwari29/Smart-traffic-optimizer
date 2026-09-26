from pydantic import BaseModel, Field, field_validator


class Weights(BaseModel):
    distance: float = Field(default=0.2, ge=0)
    time: float = Field(default=0.5, ge=0)
    traffic: float = Field(default=0.2, ge=0)
    condition: float = Field(default=0.1, ge=0)

    @field_validator("condition")
    @classmethod
    def weights_must_sum_to_one(cls, value, info):
        data = info.data
        total = data.get("distance", 0) + data.get("time", 0) + data.get("traffic", 0) + value
        if abs(total - 1.0) > 1e-6:
            raise ValueError("distance, time, traffic, and condition weights must sum to 1")
        return value


class OptimizeRequest(BaseModel):
    source: str = Field(min_length=1, max_length=32)
    destination: str = Field(min_length=1, max_length=32)
    weights: Weights = Field(default_factory=Weights)
    max_hops: int | None = Field(default=None, ge=1, le=100)


class TrafficUpdateRequest(BaseModel):
    road_id: str = Field(min_length=1, max_length=64)
    congestion: float = Field(ge=0, le=1)


class SimulationRequest(BaseModel):
    source: str = Field(min_length=1, max_length=32)
    destination: str = Field(min_length=1, max_length=32)
    road_id: str = Field(min_length=1, max_length=64)
    increase_percent: float = Field(gt=0, le=500)
    weights: Weights = Field(default_factory=Weights)
