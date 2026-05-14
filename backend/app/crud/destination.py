from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.activity import ActivityType
from ..models.destination import Destination


def list_destinations(db: Session) -> list[Destination]:
    """Return all destinations ordered alphabetically by name."""
    return list(
        db.execute(select(Destination).order_by(Destination.name)).scalars()
    )


def list_activity_types(db: Session) -> list[ActivityType]:
    """Return all activity types ordered alphabetically by name."""
    return list(
        db.execute(select(ActivityType).order_by(ActivityType.name)).scalars()
    )
