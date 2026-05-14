from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..crud import destination as destination_crud
from ..deps import get_db
from ..schemas.activity import ActivityTypeOut

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("", response_model=list[ActivityTypeOut])
def list_activity_types(db: Session = Depends(get_db)) -> list:
    """Return all activity types, ordered alphabetically."""
    return destination_crud.list_activity_types(db)
