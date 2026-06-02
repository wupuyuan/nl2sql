from pydantic import BaseModel
from typing import List, Optional, Any


class Filter(BaseModel):
    field: str
    op: str
    value: Any


class TimeRange(BaseModel):
    field: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


class SemanticRequest(BaseModel):
    query: str


class SemanticResponse(BaseModel):
    intent: str
    metrics: List[str] = []
    dimensions: List[str] = []
    filters: List[Filter] = []
    time_range: Optional[TimeRange] = None
    warnings: List[str] = []
    limit: int = 100
