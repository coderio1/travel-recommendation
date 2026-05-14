from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class RecommendationRequest(Base):
    __tablename__ = "recommendation_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    wanted_destination_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("destinations.id"),
        nullable=True,
    )
    wanted_country: Mapped[str | None] = mapped_column(Text, nullable=True)
    wanted_area: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_type_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("activity_types.id"),
        nullable=True,
    )
    vacation_start_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vacation_end_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preference: Mapped[str | None] = mapped_column(Text, nullable=True)  # 'cheap'|'quiet'|'luxury'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="requests")  # type: ignore[name-defined]
    results: Mapped[list["RecommendationResult"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="RecommendationResult.rank_position",
    )


class RecommendationResult(Base):
    __tablename__ = "recommendation_results"
    __table_args__ = (UniqueConstraint("recommendation_request_id", "destination_activity_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    recommendation_request_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("recommendation_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    destination_activity_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("destination_activities.id", ondelete="CASCADE"),
        nullable=False,
    )
    recommended_start_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_end_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    rank_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    request: Mapped["RecommendationRequest"] = relationship(back_populates="results")
    destination_activity: Mapped["DestinationActivity"] = relationship()  # type: ignore[name-defined]
