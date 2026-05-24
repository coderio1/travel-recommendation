from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..crud import favorite as fav_crud
from ..crud import recommendation as rec_crud
from ..deps import get_current_user, get_db
from ..models.user import User
from ..schemas.recommendation import (
    RecommendationRequestIn,
    RecommendationRequestOut,
    RecommendationResultOut,
)
from ..services.recommender import ScoringInput, score_candidates

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def _build_response(req, favorited_ids: set[int] | None = None) -> RecommendationRequestOut:
    """Flatten ORM relationships into the response shape."""
    favorited_ids = favorited_ids or set()
    results: list[RecommendationResultOut] = []
    for r in sorted(req.results, key=lambda x: (x.rank_position or 0)):
        da = r.destination_activity
        results.append(
            RecommendationResultOut(
                id=r.id,
                destination_activity_id=r.destination_activity_id,
                destination_id=da.destination_id,
                destination_name=da.destination.name,
                country=da.destination.country,
                area=da.destination.area,
                activity_name=da.activity_type.name,
                recommended_start_month=r.recommended_start_month,
                recommended_end_month=r.recommended_end_month,
                match_score=r.match_score,
                rank_position=r.rank_position,
                reason=r.reason,
                is_favorited=r.destination_activity_id in favorited_ids,
            )
        )
    return RecommendationRequestOut(
        id=req.id,
        user_id=req.user_id,
        wanted_destination_id=req.wanted_destination_id,
        wanted_country=req.wanted_country,
        wanted_area=req.wanted_area,
        activity_type_id=req.activity_type_id,
        vacation_start_month=req.vacation_start_month,
        vacation_end_month=req.vacation_end_month,
        preference=req.preference,
        created_at=req.created_at,
        results=results,
    )


@router.post("", response_model=RecommendationRequestOut, status_code=status.HTTP_201_CREATED)
def create_recommendation(
    payload: RecommendationRequestIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationRequestOut:
    """Run the recommender for the current user and persist the request + results."""
    # 1) Hard-filter the candidate pool in SQL
    candidates = rec_crud.load_candidates(
        db,
        wanted_destination_id=payload.wanted_destination_id,
        wanted_country=payload.wanted_country,
        wanted_area=payload.wanted_area,
        activity_type_id=payload.activity_type_id,
    )

    # 2) Persist the request (gives us request.id for the FK)
    request = rec_crud.create_request(
        db,
        user_id=current_user.id,
        wanted_destination_id=payload.wanted_destination_id,
        wanted_country=payload.wanted_country,
        wanted_area=payload.wanted_area,
        activity_type_id=payload.activity_type_id,
        vacation_start_month=payload.vacation_start_month,
        vacation_end_month=payload.vacation_end_month,
        preference=payload.preference,
    )

    # 3) Score in pure Python
    scored = score_candidates(
        candidates,
        ScoringInput(
            vacation_start_month=payload.vacation_start_month,
            vacation_end_month=payload.vacation_end_month,
            preference=payload.preference,
            wanted_country=payload.wanted_country,
            wanted_area=payload.wanted_area,
        ),
        top_k=30,
    )

    # 4) Persist results (commits the transaction)
    rec_crud.persist_results(db, request_id=request.id, scored=scored)

    # 5) Reload with all relationships so the response is complete
    fresh = rec_crud.get_request(db, request_id=request.id, user_id=current_user.id)
    assert fresh is not None
    favorited_ids = fav_crud.get_favorited_ids(db, user_id=current_user.id)
    return _build_response(fresh, favorited_ids)


@router.get("/{request_id}", response_model=RecommendationRequestOut)
def get_recommendation(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationRequestOut:
    """Return a single recommendation request with its ranked results; 404 if not found."""
    req = rec_crud.get_request(db, request_id=request_id, user_id=current_user.id)
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    favorited_ids = fav_crud.get_favorited_ids(db, user_id=current_user.id)
    return _build_response(req, favorited_ids)


@router.get("", response_model=list[RecommendationRequestOut])
def list_my_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RecommendationRequestOut]:
    """List the current user's recent recommendation requests (without their results,
    for the result objects use GET /api/recommendations/{id})."""
    requests = rec_crud.list_user_requests(db, user_id=current_user.id)
    return [
        RecommendationRequestOut(
            id=r.id,
            user_id=r.user_id,
            wanted_destination_id=r.wanted_destination_id,
            wanted_country=r.wanted_country,
            wanted_area=r.wanted_area,
            activity_type_id=r.activity_type_id,
            vacation_start_month=r.vacation_start_month,
            vacation_end_month=r.vacation_end_month,
            preference=r.preference,
            created_at=r.created_at,
            results=[],
        )
        for r in requests
    ]
