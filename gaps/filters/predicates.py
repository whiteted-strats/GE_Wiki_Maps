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
RECTANGLE_TOLERANCE = 0.01  # opposite sides of a rectangle may differ by this much
SQUARE_TOLERANCE = 0.10  # the shorter sides may be up to this much shorter than the longer ones
FLAT_RATIO = 0.2  # how thin, from top to bottom, counts as lying flat
# Most outlines have six points, not four: the game holds two of the corners twice, computed by
# two routes, a float32 step or so apart. So a door is really a hexagon with two sides of about
# 5e-4 cm. The predicates count sides as a person would, leaving out any shorter than this fraction
# of the longest. The geometry does no such thing: pinches, lines of sight and warps are all
# computed on every point as the game stores it, tiny sides included.
NEGLIGIBLE_SIDE = 0.01
# A side counts as running along an axis if it strays from it by less than this, in centimetres.
# The game rotates objects into place in float32, so an axis-aligned door's long sides are tilted
# by a float32 step or two (3e-5 cm over 87 cm on Train). A door at 45 degrees is off by metres.
AXIS_TOLERANCE_CM = 0.001

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
def is_glass(obj: LevelObject) -> bool:
    """Its type is "glass"."""
    return obj.type == "glass"


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
def is_axis_aligned(obj: LevelObject) -> bool:
    """Every side of its outline runs along x or along z, to within AXIS_TOLERANCE_CM. The tiny
    sides between repeated corners are left out, as in the other predicates."""
    return _axis_of_longest_side(obj) is not None


@predicate
def is_x_axis_aligned(obj: LevelObject) -> bool:
    """Axis-aligned, with its longest side running along x."""
    return _axis_of_longest_side(obj) == "x"


@predicate
def is_z_axis_aligned(obj: LevelObject) -> bool:
    """Axis-aligned, with its longest side running along z."""
    return _axis_of_longest_side(obj) == "z"


def _axis_of_longest_side(obj: LevelObject) -> str | None:
    """ "x" or "z" if every side runs along an axis, naming the axis of the longest side. None if
    any side runs along neither."""
    points = obj.points
    negligible = NEGLIGIBLE_SIDE * max(_side_lengths(obj))
    longest, axis_of_longest = 0.0, None
    for i in range(len(points)):
        p, q = points[i], points[(i + 1) % len(points)]
        along_x, along_z = abs(float(q[0] - p[0])), abs(float(q[1] - p[1]))
        if max(along_x, along_z) <= negligible:
            continue
        if min(along_x, along_z) >= AXIS_TOLERANCE_CM:
            return None
        if max(along_x, along_z) > longest:
            longest, axis_of_longest = max(along_x, along_z), "x" if along_x > along_z else "z"
    return axis_of_longest


@predicate
def is_rectangle(obj: LevelObject) -> bool:
    """Its outline has four sides, the opposite ones equal in length (to within 1%)."""
    sides = _side_lengths(obj)
    if len(sides) != 4:
        return False
    return _nearly_equal(sides[0], sides[2], RECTANGLE_TOLERANCE) and _nearly_equal(
        sides[1], sides[3], RECTANGLE_TOLERANCE
    )


@predicate
def is_square(obj: LevelObject) -> bool:
    """A rectangle whose shorter sides are within 10% of its longer ones.

    That is loose for "square" because crates aren't: Frigate's pipes room crates, the only use
    so far, are 78 by 83 cm, 6% off. This only ever checks objects listed by address in a level
    file, it never picks objects out."""
    sides = _side_lengths(obj)
    return is_rectangle(obj) and _nearly_equal(min(sides), max(sides), SQUARE_TOLERANCE)


@predicate
def is_crate(obj: LevelObject) -> bool:
    """Generic, square, and with standard health. The data has nothing more specific to go on."""
    return is_generic(obj) and is_square(obj) and has_standard_health(obj)


def _side_lengths(obj: LevelObject) -> list[float]:
    """The lengths of the outline's sides, leaving out the negligible ones between repeated
    corners. See NEGLIGIBLE_SIDE: this is for counting sides, not for geometry."""
    points = obj.points
    lengths = [
        float(dist2(points[i], points[(i + 1) % len(points)])) ** 0.5 for i in range(len(points))
    ]
    longest = max(lengths)
    return [length for length in lengths if length > NEGLIGIBLE_SIDE * longest]


def _nearly_equal(smaller: float, larger: float, tolerance: float) -> bool:
    smaller, larger = sorted((smaller, larger))
    return larger - smaller <= tolerance * larger
