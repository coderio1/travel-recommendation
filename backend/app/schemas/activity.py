from pydantic import BaseModel, ConfigDict


class ActivityTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class DestinationActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination_id: int
    activity_type_id: int
    start_month: int
    end_month: int
    price_level: int | None = None
    quiet_level: int | None = None
    luxury_level: int | None = None
