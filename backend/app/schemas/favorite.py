from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FavoriteIn(BaseModel):
    destination_activity_id: int
    recommendation_request_id: int | None = None


class FavoriteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination_activity_id: int
    destination_id: int
    destination_name: str
    country: str | None
    area: str | None
    activity_name: str
    travel_start_month: int | None
    travel_end_month: int | None
    created_at: datetime


class FavoritePatch(BaseModel):
    travel_start_month: int | None = Field(default=None, ge=1, le=12)
    travel_end_month: int | None = Field(default=None, ge=1, le=12)