from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..crud import favorite as fav_crud
from ..deps import get_current_user, get_db
from ..models.user import User
from ..schemas.favorite import FavoriteIn, FavoriteOut

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


def _to_out(fav) -> FavoriteOut:
    da = fav.destination_activity
    return FavoriteOut(
        id=fav.id,
        destination_activity_id=fav.destination_activity_id,
        destination_id=da.destination_id,
        destination_name=da.destination.name,
        country=da.destination.country,
        area=da.destination.area,
        activity_name=da.activity_type.name,
        created_at=fav.created_at,
    )


@router.get("", response_model=list[FavoriteOut])
def list_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FavoriteOut]:
    return [_to_out(f) for f in fav_crud.list_favorites(db, user_id=current_user.id)]


@router.post("", response_model=FavoriteOut, status_code=status.HTTP_200_OK)
def add_favorite(
    payload: FavoriteIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteOut:
    fav = fav_crud.add_favorite(
        db,
        user_id=current_user.id,
        destination_activity_id=payload.destination_activity_id,
    )
    return _to_out(fav)


@router.delete("/{destination_activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    destination_activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    fav_crud.remove_favorite(
        db,
        user_id=current_user.id,
        destination_activity_id=destination_activity_id,
    )
