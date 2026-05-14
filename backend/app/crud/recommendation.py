"""CRUD for recommendation requests, results, and the candidate query."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models.activity import DestinationActivity
from ..models.destination import Destination
from ..models.recommendation import RecommendationRequest, RecommendationResult


def load_candidates(
    db: Session,
    *,
    wanted_destination_id: int | None,
    wanted_country: str | None,
    wanted_area: str | None,
    activity_type_id: int | None,
) -> list[DestinationActivity]:
    """Pull all `destination_activities` matching the user's hard filters."""
    stmt = (
        select(DestinationActivity)
        .options(
            joinedload(DestinationActivity.destination),
            joinedload(DestinationActivity.activity_type),
        )
        .join(DestinationActivity.destination)
    )

    if wanted_destination_id is not None:
        stmt = stmt.where(DestinationActivity.destination_id == wanted_destination_id)
    if wanted_country:
        stmt = stmt.where(Destination.country.ilike(wanted_country))
    if wanted_area:
        stmt = stmt.where(Destination.area.ilike(wanted_area))
    if activity_type_id is not None:
        stmt = stmt.where(DestinationActivity.activity_type_id == activity_type_id)

    return list(db.execute(stmt).scalars().unique())


def create_request(
    db: Session,
    *,
    user_id: int,
    wanted_destination_id: int | None,
    wanted_country: str | None,
    wanted_area: str | None,
    activity_type_id: int | None,
    vacation_start_month: int | None,
    vacation_end_month: int | None,
    preference: str | None,
) -> RecommendationRequest:
    """Insert a new recommendation request row and flush to obtain its id."""
    req = RecommendationRequest(
        user_id=user_id,
        wanted_destination_id=wanted_destination_id,
        wanted_country=wanted_country,
        wanted_area=wanted_area,
        activity_type_id=activity_type_id,
        vacation_start_month=vacation_start_month,
        vacation_end_month=vacation_end_month,
        preference=preference,
    )
    db.add(req)
    db.flush()  # populate req.id without committing yet
    return req


def persist_results(
    db: Session,
    *,
    request_id: int,
    scored: list[dict],
) -> list[RecommendationResult]:
    """Insert scored result rows in one batch."""
    rows: list[RecommendationResult] = []
    for item in scored:
        rows.append(
            RecommendationResult(
                recommendation_request_id=request_id,
                destination_activity_id=item["destination_activity_id"],
                recommended_start_month=item["recommended_start_month"],
                recommended_end_month=item["recommended_end_month"],
                match_score=Decimal(str(round(item["match_score"], 2))),
                rank_position=item["rank_position"],
                reason=item["reason"],
            )
        )
    db.add_all(rows)
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows


def get_request(db: Session, *, request_id: int, user_id: int) -> RecommendationRequest | None:
    """Fetch a request belonging to the given user. Loading results."""
    stmt = (
        select(RecommendationRequest)
        .options(
            joinedload(RecommendationRequest.results)
            .joinedload(RecommendationResult.destination_activity)
            .joinedload(DestinationActivity.destination),
            joinedload(RecommendationRequest.results)
            .joinedload(RecommendationResult.destination_activity)
            .joinedload(DestinationActivity.activity_type),
        )
        .where(
            RecommendationRequest.id == request_id,
            RecommendationRequest.user_id == user_id,
        )
    )
    return db.execute(stmt).scalars().unique().one_or_none()


def list_user_requests(db: Session, *, user_id: int, limit: int = 20) -> list[RecommendationRequest]:
    """Return the most recent recommendation requests for a user, newest first."""
    stmt = (
        select(RecommendationRequest)
        .where(RecommendationRequest.user_id == user_id)
        .order_by(RecommendationRequest.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars())
