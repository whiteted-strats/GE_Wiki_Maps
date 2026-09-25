"""Named tests on a single object, for the level files to describe the objects they list.

They are deliberately simple, and each says exactly what it checks. List them all with
`python -m gaps.filters`.
"""

from collections.abc import Callable

from gaps.exact import dist2
from gaps.filters.config import OVERHEAD_REVIEW_CLEARANCE_M
from gaps.mesh import LevelObject

Predicate = Callable[[LevelObject], bool]

STANDARD_HEALTH = 1000
SQUARE_TOLERANCE = 0.10  # the shorter sides may be up to this much shorter than the longer ones
FLAT_RATIO = 0.2  # how thin, from top to bottom, counts as lying flat
NEGLIGIBLE_SIDE = 0.01  # outlines repeat some corners, giving sides of almost no length

PREDICATES: dict[str, Predicate] = {}


def predicate(test: Predicate) -> Predicate:
    PREDICATES[test.__name__] = test
    return test


@predicate
def is_generic(obj: LevelObject) -> bool:
    """Its type is "generic": scenery, as opposed to a door, monitor, glass, vehicle and so on."""
    return obj.type == "generic"


@predicate
def is_door(obj: LevelObject) -> bool:
    """Its type is "door"."""
    return obj.type == "door"


@predicate
def is_lying_flat(obj: LevelObject) -> bool:
    """It is a slab lying on its side: from top to bottom it measures less than a fifth of the
    shorter side of its outline. Silo's bay doors are 25 cm by 4.2 m and Aztec's 48 cm by 4 m. A
    standing door is the opposite, about 2 m tall and 17 cm thick: twelve times its shorter side."""
    if obj.height_range is None:
        return False
    top_to_bottom = max(obj.height_range) - min(obj.height_range)
    return top_to_bottom < FLAT_RATIO * min(_side_lengths(obj))


@predicate
def is_overhead(obj: LevelObject) -> bool:
    """Its bottom is at least OVERHEAD_REVIEW_CLEARANCE_M (2 m) above the top of the tile it is
    attached to, so Bond would pass underneath. The same test which picks objects out for review
    in overhead_objects.csv."""
    clearance = obj.floor_clearance
    return clearance is not None and clearance >= OVERHEAD_REVIEW_CLEARANCE_M * 100


@predicate
def has_standard_health(obj: LevelObject) -> bool:
    """Its health is 1000, which is what nearly every object has."""
    return obj.health == STANDARD_HEALTH


@predicate
def is_rectangle(obj: LevelObject) -> bool:
    """Its outline has four sides, the opposite ones equal in length (to within 1%)."""
    sides = _side_lengths(obj)
    if len(sides) != 4:
        return False
    return _nearly_equal(sides[0], sides[2], 0.01) and _nearly_equal(sides[1], sides[3], 0.01)


@predicate
def is_square(obj: LevelObject) -> bool:
    """A rectangle whose shorter sides are within 10% of its longer ones. Crates are rarely quite
    square: those on Frigate are 78 by 83 cm."""
    sides = _side_lengths(obj)
    return is_rectangle(obj) and _nearly_equal(min(sides), max(sides), SQUARE_TOLERANCE)


@predicate
def is_crate(obj: LevelObject) -> bool:
    """Generic, square, and with standard health. The data has nothing more specific to go on."""
    return is_generic(obj) and is_square(obj) and has_standard_health(obj)


def _side_lengths(obj: LevelObject) -> list[float]:
    """The lengths of the outline's sides, leaving out the negligible ones between repeated
    corners."""
    points = obj.points
    lengths = [
        float(dist2(points[i], points[(i + 1) % len(points)])) ** 0.5 for i in range(len(points))
    ]
    longest = max(lengths)
    return [length for length in lengths if length > NEGLIGIBLE_SIDE * longest]


def _nearly_equal(smaller: float, larger: float, tolerance: float) -> bool:
    smaller, larger = sorted((smaller, larger))
    return larger - smaller <= tolerance * larger
