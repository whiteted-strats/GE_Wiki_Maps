"""Filters which apply to every level: shapes of gap which can never be warped through.

Each filter looks at one pinch and returns a sentence saying why it matches, or None. A gap is only
filtered if every one of its pinches matches. All of them are listed in GENERIC_FILTERS at the
bottom, in the order they are tried.

These filters claim that no warp is possible, so they must never match a gap where one has been
found. `gaps.filters.apply_filters` checks that, and keeps and reports any gap where it happens.
"""

from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

from gaps.exact import Num, Point, bounding_box, cross, divide, dot, grow_box, is_convex, sub
from gaps.filters.config import ANVIL_LENGTH_M
from gaps.filters.pocket import narrow_pocket
from gaps.mesh import BoundarySegment, Level
from gaps.pinch import Pinch, describe

PinchFilter = Callable[[Level, Pinch], str | None]

MOST_WALLS_IN_A_PROTRUSION = 8  # how many walls to follow from the end of an anvil


def anvil_and_hammer(level: Level, pinch: Pinch) -> str | None:
    """A long straight wall (the anvil) with a corner or a parallel edge (the hammer) closer to it
    than Bond's radius.

    Bond's centre is at least his radius from the anvil at both ends of a step, so every point of
    the step is too, and it can't pass between the anvil and a hammer which is closer than that.
    A hammer at exactly his radius can be passed, so the test is strictly less than.

    The only other way past is for an end of the step to be beyond an end of the anvil, angling in
    round it. For each end of the anvil, such a step is ruled out, or shown to be impractically
    long, in one of three ways:

      - the anvil runs for half of ANVIL_LENGTH_M beyond the hammer, or
      - the anvil ends at a protrusion: a wall which turns towards the walkable side and rises at
        least as far from the anvil as the hammer is. A step from beyond it passes over its tip, so
        higher than the hammer, and must then drop under the hammer. So it carries on dropping, and
        can't end over the anvil, where Bond must be 30 cm up. It can still end beyond the other
        end of the anvil, so this only counts if that end has a protrusion too (no straight line
        is above the hammer's height at both ends and below it between) or is long. Nothing is
        assumed about what lies beyond a protrusion: the wall may well bend back again.
      - failing those, a step round this end rises too slowly to be short: see
        `_shortest_step_round_the_end2`.
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
        run = _straight_run(level, anvil)
        hammer_low, hammer_high = _extent_along(anvil, hammer, nearest_on_hammer)
        if not (run.low <= hammer_low and hammer_high <= run.high):
            continue
        length2 = _squared_length(anvil)
        anvil_length2 = (run.high - run.low) ** 2 * length2
        # For each side: how much anvil lies beyond the hammer, how far the end of the anvil is
        # from the far end of the hammer, and the corner at which the anvil ends
        beyond = [hammer_low - run.low, run.high - hammer_high]
        # The slow-rise bound measures to the furthest hammer point which the step must pass
        points = _hammer_points_the_step_must_pass(level, anvil, run, hammer, nearest_on_hammer)
        to_far_end_of_hammer = [max(points) - run.low, run.high - min(points)]
        corners = [run.low_corner, run.high_corner]

        is_long = [amount**2 * length2 >= half_anvil2 for amount in beyond]
        has_protrusion = [
            _protrusion_as_high_as_hammer(
                level, anvil, run, corner, nearest_on_hammer, pinch.width2
            )
            for corner in corners
        ]

        why_no_step_round_each_end = []
        for side in (0, 1):
            clear2 = beyond[side] ** 2 * length2
            clear = f"{_metres(level, clear2):.1f} m of it"
            if is_long[side]:
                why_no_step_round_each_end.append(clear)
            elif has_protrusion[side] and (has_protrusion[1 - side] or is_long[1 - side]):
                why_no_step_round_each_end.append(f"{clear} ending at a protrusion")
            else:
                shortest2 = _shortest_step_round_the_end2(
                    level, to_far_end_of_hammer[side] ** 2 * length2, pinch.width2, anvil_length2
                )
                if shortest2 >= level.from_metres(ANVIL_LENGTH_M) ** 2:
                    why_no_step_round_each_end.append(
                        f"{clear}, so little that a step round its end would be at least "
                        f"{_metres(level, shortest2):.1f} m long"
                    )
        if len(why_no_step_round_each_end) == 2:
            width_cm = level.to_cm(float(pinch.width2) ** 0.5)
            one_side, other_side = why_no_step_round_each_end
            return (
                f"{describe(level, hammer)} is {width_cm:.1f} cm from a straight wall, closer than "
                f"Bond's radius, with {one_side} to one side and {other_side} to the other"
            )
    return None


def _shortest_step_round_the_end2(
    level: Level, to_far_end_of_hammer2: Num, hammer_distance2: Num, anvil_length2: Num
) -> Num:
    """A lower bound on the length of a step which comes in round an end of the anvil, squared and
    in scaled units: min(anvil length, distance x 30 / d).

    Picture the anvil as a floor with that end at the left. The step can't cross the anvil, so at
    the end of it the step is at height 0 or more, wherever Bond is actually standing. It has to
    pass under the far end of the hammer, at the hammer's distance `d`. So it rises no faster than
    `d` over the distance from the end of the anvil to there. Over the anvil Bond must be 30 cm up,
    and rising that slowly the step does not get that high until `distance x 30 / d` along the
    anvil. (The generous case is a Bond of no width standing on the very end of the anvil, with the
    step brushing the hammer.)

    Or the step ends beyond the other end of the anvil, where nothing requires Bond to be 30 cm
    up. Then it has covered the whole length of the anvil. This is possible whatever is at that
    other end, protrusion or not: Depot has a warp which passes over a protrusion at one end of a
    short anvil, under a door corner, and out past the other end.
    """
    before_bond_fits2 = to_far_end_of_hammer2 * level.bond_radius**2 / hammer_distance2
    return min(before_bond_fits2, anvil_length2)


@dataclass
class StraightRun:
    """A line of walls end to end. Positions along it are measured from the wall it was built
    from: 0 is that wall's `a` and 1 is its `b`, so a wall on its own runs from 0 to 1."""

    low: Num
    high: Num
    low_corner: Point
    high_corner: Point
    walls: set[int]  # segment ids


def _straight_run(level: Level, wall: BoundarySegment) -> StraightRun:
    """The straight line of walls through `wall`.

    Walls are added if they share a corner with one already in the run and lie exactly on the same
    line. "Exactly" is meaningful because the corners of tiles are integers. A wall must also be on
    the same sheet: sharing a corner from above is not enough, as it could be on another storey.
    """
    direction = sub(wall.b, wall.a)
    run = StraightRun(Fraction(0), Fraction(1), wall.a, wall.b, {wall.id})
    to_extend = [wall]

    while to_extend:
        current = to_extend.pop()
        for corner in (current.a, current.b):
            for other in _walls_continuing_from(level, current, corner):
                on_the_line = (
                    cross(direction, sub(other.a, wall.a)) == 0
                    and cross(direction, sub(other.b, wall.a)) == 0
                )
                if other.id in run.walls or not on_the_line:
                    continue
                run.walls.add(other.id)
                to_extend.append(other)
                for end in (other.a, other.b):
                    position = _position_along(wall, end)
                    if position < run.low:
                        run.low, run.low_corner = position, end
                    if position > run.high:
                        run.high, run.high_corner = position, end
    return run


def _walls_continuing_from(
    level: Level, wall: BoundarySegment, corner: Point
) -> list[BoundarySegment]:
    """The other tile walls which meet `wall` at this corner, on the same sheet."""
    nearby_tiles = level.linked_tiles_within(wall.tile, grow_box(bounding_box([corner]), 1))
    return [
        other
        for other in level.walls_meeting_at(corner)
        if other.id != wall.id and other.tile in nearby_tiles
    ]


def _protrusion_as_high_as_hammer(
    level: Level,
    anvil: BoundarySegment,
    run: StraightRun,
    corner: Point,
    walkable_side: Point,
    hammer_distance2: Num,
) -> bool:
    """Whether the wall at this end of the anvil turns towards the walkable side and rises at
    least as far from the anvil's line as the hammer is: a protrusion as high as the hammer.

    The walkable side is the side the hammer is on, given here by any point on the hammer. Walls
    are followed from the corner for as long as each one rises further from the anvil's line. What
    the wall does after that doesn't matter. A wall which turns the other way is no protrusion.
    """
    direction = sub(anvil.b, anvil.a)
    length2 = dot(direction, direction)
    towards_walkable = 1 if cross(direction, sub(walkable_side, anvil.a)) > 0 else -1

    def rise(point: Point) -> Num:
        """How far the point is from the anvil's line on the walkable side, times the anvil's
        length. Negative on the other side."""
        return towards_walkable * cross(direction, sub(point, anvil.a))

    previous = next(w for w in level.segments if w.id in run.walls and corner in (w.a, w.b))
    reached = 0
    for _ in range(MOST_WALLS_IN_A_PROTRUSION):
        rising = [
            (rise(far_end), other, far_end)
            for other in _walls_continuing_from(level, previous, corner)
            for far_end in (other.a, other.b)
            if far_end != corner and other.id not in run.walls and rise(far_end) > reached
        ]
        if not rising:
            return False
        reached, previous, corner = max(rising, key=lambda entry: entry[0])
        if reached * reached >= hammer_distance2 * length2:
            return True
    return False


def _metres(level: Level, squared_scaled_length: Num) -> float:
    return level.to_cm(float(squared_scaled_length) ** 0.5) / 100


def _hammer_points_the_step_must_pass(
    level: Level,
    anvil: BoundarySegment,
    run: StraightRun,
    hammer: BoundarySegment,
    nearest_on_hammer: Point,
) -> list[Num]:
    """Positions along the anvil of the hammer points which a step through this pinch has to pass
    under. Always the pinch's own hammer point, and both ends of any hammer head.

    A hammer point is a corner closer to the anvil than Bond's radius, over the anvil and on its
    walkable side. A hammer head is an edge both of whose ends are hammer points: a step can't
    cross an edge, so it passes under both. Heads are never joined up into anything longer.

    The pinch's own edge is a head if its ends qualify. If it is a side of an object whose outline
    is convex, every other side of that object which is a head counts too, because a straight line
    which misses a convex shape has the whole of it to one side. So a step which passes under the
    corner of a crate passes under the whole crate.
    """
    direction = sub(anvil.b, anvil.a)
    length2 = dot(direction, direction)
    walkable = _sign_of(cross(direction, sub(nearest_on_hammer, anvil.a)))
    radius2 = level.bond_radius**2

    def is_hammer_point(corner: Point) -> bool:
        offset = cross(direction, sub(corner, anvil.a))  # distance from the anvil's line x length
        over_the_anvil = run.low <= _position_along(anvil, corner) <= run.high
        return over_the_anvil and _sign_of(offset) == walkable and offset**2 < radius2 * length2

    edges = [hammer]
    if hammer.obj is not None and is_convex(level.objects[hammer.obj].points):
        edges = level.sides_of_object(hammer.obj)

    positions = [_position_along(anvil, nearest_on_hammer)]
    for edge in edges:
        if is_hammer_point(edge.a) and is_hammer_point(edge.b):
            positions += [_position_along(anvil, edge.a), _position_along(anvil, edge.b)]
    return positions


def _sign_of(value: Num) -> int:
    return (value > 0) - (value < 0)


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
    "narrow pocket": narrow_pocket,
}
