from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..crud import destination as destination_crud
from ..deps import get_db
from ..schemas.destination import DestinationOut

router = APIRouter(prefix="/api/destinations", tags=["destinations"])


@router.get("", response_model=list[DestinationOut])
def list_destinations(db: Session = Depends(get_db)) -> list:
    """Return all destinations, ordered alphabetically."""
    return destination_crud.list_destinations(db)
