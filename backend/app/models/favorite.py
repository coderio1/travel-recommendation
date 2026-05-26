from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class UserFavorite(Base):
    __tablename__ = "user_favorites"
    __table_args__ = (UniqueConstraint("user_id", "destination_activity_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    destination_activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("destination_activities.id", ondelete="CASCADE"),
        nullable=False,
    )
    recommendation_request_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("recommendation_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    travel_start_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    travel_end_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    destination_activity: Mapped["DestinationActivity"] = relationship()  # type: ignore[name-defined]
    recommendation_request: Mapped["RecommendationRequest | None"] = relationship()  # type: ignore[name-defined]
