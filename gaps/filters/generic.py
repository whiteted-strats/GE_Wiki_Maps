"""Filters which apply to every level: shapes of gap which can never be warped through.

Each filter looks at one pinch and returns a sentence saying why it matches, or None. A gap is only
filtered if every one of its pinches matches. All of them are listed in GENERIC_FILTERS at the
bottom, in the order they are tried.

These filters claim that no warp is possible, so they must never match a gap where one has been
found. `gaps.filters.apply_filters` checks that, and keeps and reports any gap where it happens.
"""

from collections.abc import Callable
from fractions import Fraction

from gaps.exact import Num, Point, bounding_box, cross, divide, dot, grow_box, sub
from gaps.filters.config import ANVIL_LENGTH_M
from gaps.mesh import BoundarySegment, Level
from gaps.pinch import Pinch, describe

PinchFilter = Callable[[Level, Pinch], str | None]


def anvil_and_hammer(level: Level, pinch: Pinch) -> str | None:
    """A long straight wall (the anvil) with a corner or a parallel edge (the hammer) closer to it
    than Bond's radius.

    Bond's centre is at least his radius from the anvil at both ends of a step, so every point of
    the step is too, and it can't pass between the anvil and a hammer which is closer than that.
    A hammer at exactly his radius can be passed, so the test is strictly less than.

    The only other way past is to angle in round the end of the anvil, so the anvil must run
    straight for half of ANVIL_LENGTH_M beyond the hammer in both directions.
    """
    if pinch.width2 >= level.bond_radius**2:
        return None
    half_anvil2 = (level.from_metres(ANVIL_LENGTH_M) / 2) ** 2

    for anvil, hammer, nearest_on_hammer in (
        (pinch.first, pinch.second, pinch.b),
        (pinch.second, pinch.first, pinch.a),
    ):
        if anvil.tile is None:
            continue  # only walls of tiles: no object is anywhere near long enough
        run_low, run_high = _straight_run(level, anvil)
        hammer_low, hammer_high = _extent_along(anvil, hammer, nearest_on_hammer)
        length2 = _squared_length(anvil)
        clear_before2 = (hammer_low - run_low) ** 2 * length2
        clear_after2 = (run_high - hammer_high) ** 2 * length2
        inside_run = run_low <= hammer_low and hammer_high <= run_high
        if inside_run and clear_before2 >= half_anvil2 and clear_after2 >= half_anvil2:
            run_m = level.to_cm(float((run_high - run_low) ** 2 * length2) ** 0.5) / 100
            width_cm = level.to_cm(float(pinch.width2) ** 0.5)
            return (
                f"{describe(level, hammer)} is {width_cm:.1f} cm from a straight wall "
                f"{run_m:.1f} m long, which is closer than Bond's radius"
            )
    return None


def _straight_run(level: Level, wall: BoundarySegment) -> tuple[Num, Num]:
    """How far the straight line of walls through `wall` extends, as (low, high) positions along
    it: 0 is wall.a and 1 is wall.b, so a wall on its own gives (0, 1).

    Walls are added if they share a corner with one already in the run and lie exactly on the same
    line. "Exactly" is meaningful because the corners of tiles are integers. A wall must also be on
    the same sheet: sharing a corner from above is not enough, as it could be on another floor.
    """
    direction = sub(wall.b, wall.a)
    low, high = Fraction(0), Fraction(1)
    in_run = {wall.id}
    to_extend = [wall]

    while to_extend:
        current = to_extend.pop()
        nearby_tiles = level.linked_tiles_within(
            current.tile, grow_box(bounding_box([current.a, current.b]), 1)
        )
        for corner in (current.a, current.b):
            for other in level.walls_meeting_at(corner):
                on_the_line = (
                    cross(direction, sub(other.a, wall.a)) == 0
                    and cross(direction, sub(other.b, wall.a)) == 0
                )
                if other.id in in_run or other.tile not in nearby_tiles or not on_the_line:
                    continue
                in_run.add(other.id)
                to_extend.append(other)
                for end in (other.a, other.b):
                    position = _position_along(wall, end)
                    low, high = min(low, position), max(high, position)
    return (low, high)


def _extent_along(
    anvil: BoundarySegment, hammer: BoundarySegment, nearest_on_hammer: Point
) -> tuple[Num, Num]:
    """The part of the anvil which the hammer is over. A parallel edge is over a stretch of it, and
    anything else comes closest at a single point."""
    is_parallel = cross(sub(anvil.b, anvil.a), sub(hammer.b, hammer.a)) == 0
    if not is_parallel:
        position = _position_along(anvil, nearest_on_hammer)
        return (position, position)
    ends = [_position_along(anvil, hammer.a), _position_along(anvil, hammer.b)]
    return (min(ends), max(ends))


def _position_along(wall: BoundarySegment, point: Point) -> Num:
    direction = sub(wall.b, wall.a)
    return divide(dot(sub(point, wall.a), direction), dot(direction, direction))


def _squared_length(wall: BoundarySegment) -> Num:
    direction = sub(wall.b, wall.a)
    return dot(direction, direction)


GENERIC_FILTERS: dict[str, PinchFilter] = {
    "anvil and hammer": anvil_and_hammer,
}
