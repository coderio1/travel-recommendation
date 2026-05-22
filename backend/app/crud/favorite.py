from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models.activity import DestinationActivity
from ..models.favorite import UserFavorite


def _load_with_relations(db: Session, *, user_id: int, destination_activity_id: int) -> UserFavorite:
    return db.execute(
        select(UserFavorite)
        .options(
            joinedload(UserFavorite.destination_activity).joinedload(DestinationActivity.destination),
            joinedload(UserFavorite.destination_activity).joinedload(DestinationActivity.activity_type),
        )
        .where(
            UserFavorite.user_id == user_id,
            UserFavorite.destination_activity_id == destination_activity_id,
        )
    ).unique().scalar_one()


def add_favorite(db: Session, *, user_id: int, destination_activity_id: int) -> UserFavorite:
    existing = db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.destination_activity_id == destination_activity_id,
        )
    ).scalar_one_or_none()
    if not existing:
        db.add(UserFavorite(user_id=user_id, destination_activity_id=destination_activity_id))
        db.commit()
    return _load_with_relations(db, user_id=user_id, destination_activity_id=destination_activity_id)


def remove_favorite(db: Session, *, user_id: int, destination_activity_id: int) -> None:
    fav = db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.destination_activity_id == destination_activity_id,
        )
    ).scalar_one_or_none()
    if fav:
        db.delete(fav)
        db.commit()


def list_favorites(db: Session, *, user_id: int) -> list[UserFavorite]:
    stmt = (
        select(UserFavorite)
        .options(
            joinedload(UserFavorite.destination_activity).joinedload(DestinationActivity.destination),
            joinedload(UserFavorite.destination_activity).joinedload(DestinationActivity.activity_type),
        )
        .where(UserFavorite.user_id == user_id)
        .order_by(UserFavorite.created_at.desc())
    )
    return list(db.execute(stmt).scalars().unique())


def get_favorited_ids(db: Session, *, user_id: int) -> set[int]:
    rows = db.execute(
        select(UserFavorite.destination_activity_id).where(UserFavorite.user_id == user_id)
    ).scalars().all()
    return set(rows)