from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Month = int  # 1..12


class RecommendationRequestIn(BaseModel):
    """User-supplied wish for a vacation. Every field is optional
    (an empty request returns broadly-scored suggestions)."""

    wanted_destination_id: int | None = None
    wanted_country: str | None = None
    wanted_area: str | None = None
    activity_type_id: int | None = None
    vacation_start_month: Month | None = Field(default=None, ge=1, le=12)
    vacation_end_month: Month | None = Field(default=None, ge=1, le=12)
    preference: Literal["cheap", "quiet", "luxury"] | None = None

    @model_validator(mode="after")
    def _validate_month_pair(self) -> "RecommendationRequestIn":
        """if only one bound is given, it will be treated as
        a signle month window. If both are given, no further
        validation is needed.
        """
        return self


class RecommendationResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination_activity_id: int
    destination_id: int
    destination_name: str
    country: str | None
    area: str | None
    activity_name: str
    recommended_start_month: int | None
    recommended_end_month: int | None
    match_score: Decimal | None
    rank_position: int | None
    reason: str | None


class RecommendationRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    wanted_destination_id: int | None
    wanted_country: str | None
    wanted_area: str | None
    activity_type_id: int | None
    vacation_start_month: int | None
    vacation_end_month: int | None
    preference: str | None
    created_at: datetime
    results: list[RecommendationResultOut] = []
