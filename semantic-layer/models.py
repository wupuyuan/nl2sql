from pydantic import BaseModel
from typing import List, Optional, Any


class Filter(BaseModel):
    field: str
    op: str
    value: Any


class SemanticResponse(BaseModel):
    intent: str
    metrics: List[str]
    dimensions: List[str]
    filters: List[Filter]
    time_range: Optional[Any] = None
    warnings: List[str] = []
    limit: int = 100
