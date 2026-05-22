from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FavoriteIn(BaseModel):
    destination_activity_id: int


class FavoriteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination_activity_id: int
    destination_id: int
    destination_name: str
    country: str | None
    area: str | None
    activity_name: str
    created_at: datetime