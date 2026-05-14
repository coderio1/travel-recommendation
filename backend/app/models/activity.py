from sqlalchemy import BigInteger, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class ActivityType(Base):
    __tablename__ = "activity_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class DestinationActivity(Base):
    __tablename__ = "destination_activities"
    __table_args__ = (UniqueConstraint("destination_id", "activity_type_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    destination_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=False,
    )
    activity_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("activity_types.id"),
        nullable=False,
    )
    start_month: Mapped[int] = mapped_column(Integer, nullable=False)
    end_month: Mapped[int] = mapped_column(Integer, nullable=False)
    price_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quiet_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    luxury_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    destination: Mapped["Destination"] = relationship(back_populates="activities")  # type: ignore[name-defined]
    activity_type: Mapped["ActivityType"] = relationship()
