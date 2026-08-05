from typing import Any
from pydantic import BaseModel


class QueryResultResponse(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_time_ms: int


class TableSummary(BaseModel):
    catalog: str
    schema_name: str
    table_name: str
    table_type: str
    comment: str | None = None


class SchemaTree(BaseModel):
    catalog: str
    schemas: list[str]


class KpiCard(BaseModel):
    label: str
    value: str
    unit: str | None = None
    delta: str | None = None
    delta_direction: str | None = None  # "up" | "down" | "neutral"
