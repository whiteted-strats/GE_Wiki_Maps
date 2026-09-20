"""Looks for an actual warp through a pinch: two places Bond fits, with line of sight between them.

This is in two halves, and only the second one is trusted.

  1. Propose. Through each of several points on the pinch line, at each of many angles, draw a line
     and slide outwards along it in both directions until Bond fits. This is done in floats with
     numpy, for speed. It is a search, so it can miss: failing to find a warp proves nothing, and a
     pinch is never dismissed because of it.
  2. Certify. The proposed positions are converted to exact fractions and checked with the exact
     `trace` and `fits`. A witness is only reported if it passes.

The step length of a witness is therefore a true length of a possible warp, and an upper bound on
the shortest one.
"""

import math
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from gaps.exact import Point, bounding_box, dist2, grow_box, lerp
from gaps.fast import distance_to_nearest_wall, ray_hits_wall_at, wall_arrays
from gaps.mesh import Level
from gaps.pinch import Pinch
from gaps.sheet import ObjectsPresent, fits, trace, walls_near

SEARCH_RADIUS_WORLD = 300  # how far back from the pinch Bond may stand, either side
SAMPLE_SPACING_WORLD = 2  # distance between the positions tried along each line
CROSSING_POINTS = (0.5, 0.25, 0.75, 0.1, 0.9)  # where on the pinch line to cross it
ANGLES_DEGREES = range(-85, 86, 5)  # measured from straight through the gap
PROPOSALS_TO_CERTIFY = 8
REFINEMENT_STEPS = 12  # halvings of the sample spacing when homing in on where Bond first fits
CLEARANCE_MARGIN = 1e-6  # floats propose positions this much clear of walls, so they certify


@dataclass
class Witness:
    p: Point  # exact positions, scaled units
    q: Point
    step2: Fraction  # squared step length, scaled units
    tile_p: int
    tile_q: int


@dataclass
class _Proposal:
    step: float
    crossing: float  # how far along the pinch line the step crosses it, 0 to 1
    direction: tuple[float, float]
    back: float  # distance from the crossing point to p
    forward: float  # and to q


def find_witness(level: Level, pinch: Pinch, present: ObjectsPresent) -> Witness | None:
    proposals = _propose(level, pinch, present)
    for proposal in proposals[:PROPOSALS_TO_CERTIFY]:
        witness = _certify(level, pinch, present, proposal)
        if witness is not None:
            return witness
    return None


# ---------------------------------------------------------------------------------------------
# 1. Propose, in floats


def _propose(level: Level, pinch: Pinch, present: ObjectsPresent) -> list[_Proposal]:
    scale = float(level.scale)
    radius = float(level.bond_radius) + CLEARANCE_MARGIN
    reach = SEARCH_RADIUS_WORLD * scale
    spacing = SAMPLE_SPACING_WORLD * scale

    region = grow_box(bounding_box([pinch.a, pinch.b]), math.ceil(reach + radius))
    walls = walls_near(level, pinch.start_tile, region, present)
    starts, ends = wall_arrays(walls)

    a = np.array([float(pinch.a[0]), float(pinch.a[1])])
    b = np.array([float(pinch.b[0]), float(pinch.b[1])])
    across = (b - a) / np.linalg.norm(b - a)
    through = np.array([-across[1], across[0]])  # straight through the gap
    distances = np.arange(spacing, reach, spacing)

    proposals = []
    for crossing in CROSSING_POINTS:
        origin = a + crossing * (b - a)
        for degrees in ANGLES_DEGREES:
            angle = math.radians(degrees)
            direction = math.cos(angle) * through + math.sin(angle) * across
            forward = _first_fit_along(origin, direction, distances, starts, ends, radius)
            back = _first_fit_along(origin, -direction, distances, starts, ends, radius)
            if forward is not None and back is not None:
                proposals.append(
                    _Proposal(forward + back, crossing, (direction[0], direction[1]), back, forward)
                )
    return sorted(proposals, key=lambda proposal: proposal.step)


def _first_fit_along(
    origin: np.ndarray,
    direction: np.ndarray,
    distances: np.ndarray,
    starts: np.ndarray,
    ends: np.ndarray,
    radius: float,
) -> float | None:
    """The nearest distance along the ray at which Bond fits, before the ray hits a wall."""
    limit = ray_hits_wall_at(origin, direction, starts, ends)
    usable = distances[distances < limit]
    if len(usable) == 0:
        return None
    positions = origin + usable[:, None] * direction
    clearance = distance_to_nearest_wall(positions, starts, ends)
    fitting = np.nonzero(clearance >= radius)[0]
    if len(fitting) == 0:
        return None

    # Bond fits at `far` but not one sample closer, so home in on where he first fits
    far = float(usable[fitting[0]])
    near = far - float(distances[0])
    for _ in range(REFINEMENT_STEPS):
        middle = (near + far) / 2
        position = (origin + middle * direction)[None, :]
        if distance_to_nearest_wall(position, starts, ends)[0] >= radius:
            far = middle
        else:
            near = middle
    return far


# ---------------------------------------------------------------------------------------------
# 2. Certify, exactly


def _certify(
    level: Level, pinch: Pinch, present: ObjectsPresent, proposal: _Proposal
) -> Witness | None:
    crossing_point = lerp(pinch.a, pinch.b, Fraction(proposal.crossing))
    direction = (Fraction(proposal.direction[0]), Fraction(proposal.direction[1]))
    p = _along(crossing_point, direction, -Fraction(proposal.back))
    q = _along(crossing_point, direction, Fraction(proposal.forward))

    # Find the tile under the crossing point by following the pinch line to it
    to_crossing = trace(
        level, pinch.start_tile, pinch.a, crossing_point, present, may_touch_walls_at_ends=True
    )
    if not to_crossing.clear:
        return None
    crossing_tile = min(to_crossing.end_tiles)

    # p and q are either side of the crossing point on one straight line, so if both halves are
    # clear then so is the whole step
    to_p = trace(level, crossing_tile, crossing_point, p, present)
    to_q = trace(level, crossing_tile, crossing_point, q, present)
    if not (to_p.clear and to_q.clear):
        return None
    tile_p, tile_q = min(to_p.end_tiles), min(to_q.end_tiles)

    if not (fits(level, tile_p, p, present)[0] and fits(level, tile_q, q, present)[0]):
        return None
    return Witness(p, q, dist2(p, q), tile_p, tile_q)


def _along(origin: Point, direction: Point, distance: Fraction) -> Point:
    return (origin[0] + distance * direction[0], origin[1] + distance * direction[1])
