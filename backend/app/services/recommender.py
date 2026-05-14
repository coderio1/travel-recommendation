"""Recommendation scoring service.

Takes already loaded ORM `DestinationActivity` objects plus the
user's request inputs and returns ranked plain dicts ready to be persisted.

Scoring logic breakdown (max 100):
    - Activity season overlap with user's vacation window:  up to 50 points
    - Preference match (cheap / quiet / luxury):            up to 30 points
    - Country / area match (soft, when not used as filter): up to 20 points.
"""

from dataclasses import dataclass
from typing import Iterable, Literal

from ..models.activity import DestinationActivity

Preference = Literal["cheap", "quiet", "luxury"]


@dataclass(frozen=True)
class ScoringInput:
    vacation_start_month: int | None
    vacation_end_month: int | None
    preference: Preference | None
    wanted_country: str | None
    wanted_area: str | None


# -- Helpers -----------------------------------------------------------------

def _months_in_window(start: int, end: int) -> set[int]:
    """Return the set of month numbers covered by [start, end], wrap-around aware.

    Example: (11, 3) -> {11, 12, 1, 2, 3}.
    """
    if start <= end:
        return set(range(start, end + 1))
    return set(range(start, 13)) | set(range(1, end + 1))


def _season_score(
    activity_start: int,
    activity_end: int,
    vac_start: int | None,
    vac_end: int | None,
) -> tuple[float, tuple[int, int] | None]:
    """0..50 points based on overlap; returns (score, recommended_window)."""
    if vac_start is None and vac_end is None:
        # No window given — give a neutral mid-score, recommend the activity's own season.
        return 30.0, (activity_start, activity_end)

    # Allow user to specify only one bound —> treat as a single month window.
    vs = vac_start or vac_end
    ve = vac_end or vac_start
    assert vs is not None and ve is not None  # for type checkers

    user_months = _months_in_window(vs, ve)
    activity_months = _months_in_window(activity_start, activity_end)
    overlap = user_months & activity_months

    if not overlap:
        return 0.0, None

    # Reward overlap proportionally to how much of the user's window is covered.
    coverage = len(overlap) / len(user_months)
    score = 50.0 * coverage

    # pick min/max of the overlap as a simple window.
    rec_start = min(overlap)
    rec_end = max(overlap)
    return score, (rec_start, rec_end)


def _preference_score(da: DestinationActivity, pref: Preference | None) -> float:
    """maping 0-30 points for matching the user's qualitative preference.
    Each level (price/quiet/luxury) is 1-3 in the schema (level=3 is mapped with full points).
    """
    if pref is None:
        return 15.0  # neutral midpoint when not specified

    if pref == "cheap":
        # Lower price_level is better. price_level=1 -> 30, =2 -> 15, =3 -> 0.
        if da.price_level is None:
            return 10.0
        return {1: 30.0, 2: 15.0, 3: 0.0}[da.price_level]

    if pref == "quiet":
        if da.quiet_level is None:
            return 10.0
        return {1: 0.0, 2: 15.0, 3: 30.0}[da.quiet_level]

    if pref == "luxury":
        if da.luxury_level is None:
            return 10.0
        return {1: 0.0, 2: 15.0, 3: 30.0}[da.luxury_level]

    return 0.0  # unreachable thanks to Literal type


def _location_score(da: DestinationActivity, wanted_country: str | None, wanted_area: str | None) -> float:
    """Up to 20 points if country/area preference is matched."""
    score = 0.0
    if wanted_country and da.destination.country and da.destination.country.lower() == wanted_country.lower():
        score += 10.0
    if wanted_area and da.destination.area and da.destination.area.lower() == wanted_area.lower():
        score += 10.0
    if not wanted_country and not wanted_area:
        score = 10.0  # neutral midpoint
    return score


def _build_reason(
    da: DestinationActivity,
    season_pts: float,
    pref_pts: float,
    loc_pts: float,
    pref: Preference | None,
    rec_window: tuple[int, int] | None,
) -> str:
    """Text explanation of the score."""
    parts: list[str] = []
    if rec_window is not None:
        parts.append(f"open months {rec_window[0]}–{rec_window[1]}")
    if pref is not None:
        parts.append(f"{pref} preference scored {pref_pts:.0f}/30")
    parts.append(f"location fit {loc_pts:.0f}/20")
    parts.append(f"season fit {season_pts:.0f}/50")
    return f"{da.destination.name} · {da.activity_type.name}: " + ", ".join(parts)


# -- Public API --------------------------------------------------------------

def score_candidates(
    candidates: Iterable[DestinationActivity],
    inp: ScoringInput,
    *,
    top_k: int = 10,
) -> list[dict]:
    """Score and rank candidate destination_activities (result return as dict)."""
    scored: list[dict] = []
    for da in candidates:
        season_pts, rec_window = _season_score(
            da.start_month, da.end_month, inp.vacation_start_month, inp.vacation_end_month
        )
        pref_pts = _preference_score(da, inp.preference)
        loc_pts = _location_score(da, inp.wanted_country, inp.wanted_area)

        total = season_pts + pref_pts + loc_pts
        if total <= 0:
            continue

        scored.append(
            {
                "destination_activity_id": da.id,
                "destination_id": da.destination_id,
                "match_score": total,
                "recommended_start_month": rec_window[0] if rec_window else None,
                "recommended_end_month": rec_window[1] if rec_window else None,
                "reason": _build_reason(da, season_pts, pref_pts, loc_pts, inp.preference, rec_window),
            }
        )

    # Ranking sort by score desc
    scored.sort(key=lambda d: d["match_score"], reverse=True)
    scored = scored[:top_k]
    for i, item in enumerate(scored, start=1):
        item["rank_position"] = i
    return scored
