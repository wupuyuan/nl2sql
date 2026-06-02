from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum


class Aggregation(str, Enum):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    DISTINCT = "distinct"


class Metric(BaseModel):
    name: str
    display_name: str
    expression: str
    description: str
    table: str
    format: Optional[str] = None


class Dimension(BaseModel):
    name: str
    display_name: str
    field: str
    type: str = "string"
    table: str
    is_time: bool = False
    time_format: Optional[str] = None


class Filter(BaseModel):
    name: str
    display_name: str
    field: str
    type: str = "string"
    table: str
    values: Optional[Dict[str, Any]] = None
    description: str = ""


class TimeGranularity(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class CubeConfig(BaseModel):
    name: str
    display_name: str
    description: str
    table: str
    primary_key: str
    metrics: List[Metric] = []
    dimensions: List[Dimension] = []
    filters: List[Filter] = []
    time_dimensions: List[Dimension] = []
    default_limit: int = 100
    cache_ttl: int = 300
