"""
Common Schemas
==============
Pydantic models for tool argument validation (mirrors osmos-reporting-mcp).
"""
from typing import Literal

from pydantic import BaseModel, Field


class FilterItem(BaseModel):
    """A single row-level filter condition passed through to KAM.

    Prefer IN / NOT IN over = / != for string-type ID columns
    (BigQuery STRING vs numeric quirk).
    """
    column: str = Field(description="Column name to filter on.")
    operator: Literal[
        "IN", "NOT IN",
        "=", "!=", "<", "<=", ">", ">=",
        "LIKE", "NOT LIKE", "LIKES",
        "STARTS WITH", "ENDS WITH",
    ] = Field(description="Filter operator.")
    values: list = Field(description="Filter values.")


class OrderByItem(BaseModel):
    """A single ordering directive."""
    column: str = Field(description="Column name to order by.")
    order: Literal["ASC", "DESC"] = Field(default="DESC", description="Sort direction.")


class DateRange(BaseModel):
    """A single analysis window. Two of these (current + baseline) enable comparison mode."""
    startDate: str = Field(description="Start date YYYY-MM-DD.")
    endDate: str = Field(description="End date YYYY-MM-DD.")
