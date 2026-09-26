"""Curated IV safehouse parking poses for spawn/edit grouping."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParkingPose:
    x: float
    y: float
    z: float
    rot: tuple[int, int, int]  # uint8 x3


@dataclass(frozen=True)
class Safehouse:
    id: str
    name: str
    spots: tuple[ParkingPose, ...]


# Poses surveyed from CE SGTA4xx Block 4 StoredCars (100% / mid-game samples).
SAFEHOUSES: tuple[Safehouse, ...] = (
    Safehouse(
        "broker",
        "Broker (Hove Beach)",
        (
            ParkingPose(904.31, -500.05, 14.98, (1, 99, 1)),
            ParkingPose(904.00, -493.73, 14.85, (0, 99, 1)),
        ),
    ),
    Safehouse(
        "bohan",
        "South Bohan",
        (
            ParkingPose(589.16, 1397.75, 10.70, (0, 99, 0)),
            ParkingPose(589.99, 1403.38, 10.40, (0, 99, 0)),
        ),
    ),
    Safehouse(
        "mpe",
        "Middle Park East",
        (
            ParkingPose(118.98, 849.03, 14.25, (1, 99, 0)),
            ParkingPose(118.97, 842.28, 14.15, (0, 99, 2)),
        ),
    ),
    Safehouse(
        "playboy",
        "Playboy X Penthouse",
        (
            ParkingPose(-423.77, 1492.89, 18.61, (99, 0, 0)),
            ParkingPose(-418.10, 1492.36, 18.51, (99, 3, 0)),
        ),
    ),
    Safehouse(
        "alderney",
        "Alderney City",
        (
            ParkingPose(-968.68, 900.98, 13.33, (99, 0, 0)),
            ParkingPose(-961.99, 901.62, 12.99, (100, 0, 0)),
        ),
    ),
)

SAFEHOUSE_BY_ID: dict[str, Safehouse] = {s.id: s for s in SAFEHOUSES}

# Match parked cars within this world-unit radius to a curated spot.
SPOT_MATCH_RADIUS = 6.0


def _dist2(ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = ax - bx, ay - by
    return dx * dx + dy * dy


def nearest_safehouse(
    x: float, y: float, *, max_radius: float = SPOT_MATCH_RADIUS
) -> tuple[Safehouse, int] | None:
    """Return (safehouse, spot_index) for the closest curated parking pose."""
    best: tuple[float, Safehouse, int] | None = None
    limit = max_radius * max_radius
    for sh in SAFEHOUSES:
        for i, spot in enumerate(sh.spots):
            d = _dist2(x, y, spot.x, spot.y)
            if d > limit:
                continue
            if best is None or d < best[0]:
                best = (d, sh, i)
    if best is None:
        return None
    return best[1], best[2]


def spot_occupied(
    spot: ParkingPose,
    cars: list[tuple[float, float]],
    *,
    radius: float = SPOT_MATCH_RADIUS,
) -> bool:
    lim = radius * radius
    return any(_dist2(x, y, spot.x, spot.y) <= lim for x, y in cars)
