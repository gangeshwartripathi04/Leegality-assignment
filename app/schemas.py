from pydantic import BaseModel, ConfigDict, Field


class NodeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class EdgeCreate(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)
    latency: float = Field(gt=0, allow_inf_nan=False)


class EdgeResponse(BaseModel):
    id: int
    source: str
    destination: str
    latency: float


from datetime import datetime
from pydantic import ConfigDict


class RouteRequest(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)


class RouteResponse(BaseModel):
    total_latency: float
    path: list[str]


class RouteHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    destination: str
    total_latency: float
    path: list[str]
    created_at: datetime
