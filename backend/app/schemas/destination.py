from pydantic import BaseModel, ConfigDict


class DestinationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str | None = None
    area: str | None = None
