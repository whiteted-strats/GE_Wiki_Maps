"""Exact 2D geometry.

Every function here is exact when given ints or Fractions: there are no tolerances and no epsilons.
The same functions also accept floats, which the witness search uses to propose positions quickly
before they are checked exactly.

All geometry is in the XZ plane, which is how Bond moves in GoldenEye. A point is an (x, z) tuple.
"""

from fractions import Fraction
from itertools import pairwise

Num = int | Fraction | float
Point = tuple[Num, Num]
Interval = tuple[Num, Num]
Box = tuple[Num, Num, Num, Num]  # (min x, max x, min z, max z)


def divide(numerator: Num, denominator: Num) -> Num:
    """Division which stays exact: int / int gives a Fraction rather than a float."""
    if isinstance(numerator, int) and isinstance(denominator, int):
        return Fraction(numerator, denominator)
    return numerator / denominator


def sub(p: Point, q: Point) -> Point:
    return (p[0] - q[0], p[1] - q[1])


def dot(v: Point, w: Point) -> Num:
    return v[0] * w[0] + v[1] * w[1]


def cross(v: Point, w: Point) -> Num:
    return v[0] * w[1] - v[1] * w[0]


def lerp(p: Point, q: Point, t: Num) -> Point:
    """The point a fraction t of the way from p to q."""
    return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))


def dist2(p: Point, q: Point) -> Num:
    """Squared distance. Squared distances are used throughout so that everything stays rational."""
    d = sub(p, q)
    return dot(d, d)


def closest_point_on_segment(p: Point, a: Point, b: Point) -> Point:
    ab = sub(b, a)
    length2 = dot(ab, ab)
    if length2 == 0:
        return a
    t = divide(dot(sub(p, a), ab), length2)
    t = max(0, min(1, t))
    return lerp(a, b, t)


def dist2_point_segment(p: Point, a: Point, b: Point) -> Num:
    return dist2(p, closest_point_on_segment(p, a, b))


def contact_interval(p: Point, q: Point, a: Point, b: Point) -> Interval | None:
    """Where segment ab touches segment pq, as an interval of pq's parameter (0 at p, 1 at q).

    A single crossing or touching point gives (t, t). Collinear overlapping segments give the
    overlap. None means the two segments have no point in common. pq must not be a single point.
    """
    pq = sub(q, p)
    ab = sub(b, a)
    pa = sub(a, p)
    denominator = cross(pq, ab)

    if denominator != 0:
        t = divide(cross(pa, ab), denominator)
        u = divide(cross(pa, pq), denominator)
        if 0 <= t <= 1 and 0 <= u <= 1:
            return (t, t)
        return None

    # Parallel. They can only touch if they are on the same line.
    if cross(pa, pq) != 0:
        return None
    length2 = dot(pq, pq)
    t_a = divide(dot(pa, pq), length2)
    t_b = divide(dot(sub(b, p), pq), length2)
    low, high = max(0, min(t_a, t_b)), min(1, max(t_a, t_b))
    return (low, high) if low <= high else None


def closest_points_between_segments(
    a1: Point, a2: Point, b1: Point, b2: Point
) -> tuple[Num, Point, Point]:
    """(squared distance, point on a, point on b) for the closest approach of two segments."""
    if dist2(a1, a2) != 0:
        contact = contact_interval(a1, a2, b1, b2)
        if contact is not None:
            meeting_point = lerp(a1, a2, contact[0])
            return (0, meeting_point, meeting_point)

    # Parallel walls which run alongside each other are equally close all the way along. Measure
    # across the middle of that stretch: measuring at one end of it would run along whatever wall
    # closes off that end, and the gap would be mistaken for that wall.
    alongside = _middle_of_parallel_stretch(a1, a2, b1, b2)
    if alongside is not None:
        return (dist2(*alongside), *alongside)

    # Otherwise the closest approach involves an endpoint of one of them.
    options = [
        (a1, closest_point_on_segment(a1, b1, b2)),
        (a2, closest_point_on_segment(a2, b1, b2)),
        (closest_point_on_segment(b1, a1, a2), b1),
        (closest_point_on_segment(b2, a1, a2), b2),
    ]
    on_a, on_b = min(options, key=lambda pair: dist2(*pair))
    return (dist2(on_a, on_b), on_a, on_b)


def _middle_of_parallel_stretch(
    a1: Point, a2: Point, b1: Point, b2: Point
) -> tuple[Point, Point] | None:
    """For parallel segments which overlap when projected onto each other: the point on a at the
    middle of the overlap, and the point on b opposite it. None if they aren't like that."""
    a = sub(a2, a1)
    length2 = dot(a, a)
    if length2 == 0 or cross(a, sub(b2, b1)) != 0 or dist2(b1, b2) == 0:
        return None
    t1 = divide(dot(sub(b1, a1), a), length2)
    t2 = divide(dot(sub(b2, a1), a), length2)
    low, high = max(0, min(t1, t2)), min(1, max(t1, t2))
    if low >= high:
        return None
    on_a = lerp(a1, a2, divide(low + high, 2))
    return (on_a, closest_point_on_segment(on_a, b1, b2))


def point_on_segment(p: Point, a: Point, b: Point) -> bool:
    return dist2_point_segment(p, a, b) == 0


def point_in_polygon(p: Point, polygon: list[Point]) -> bool:
    """True if p is inside the polygon or on its edge. Works for either winding and for non-convex
    polygons. A zero-area polygon (a vertical tile seen from above) contains only its own edges."""
    n = len(polygon)
    if any(point_on_segment(p, polygon[i], polygon[(i + 1) % n]) for i in range(n)):
        return True

    # Crossing number: count the edges that a ray from p towards +x passes through.
    inside = False
    for i in range(n):
        a, b = polygon[i], polygon[(i + 1) % n]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x_at_p = a[0] + divide((p[1] - a[1]) * (b[0] - a[0]), b[1] - a[1])
            if x_at_p > p[0]:
                inside = not inside
    return inside


def is_convex(polygon: list[Point]) -> bool:
    """Whether the outline never turns back on itself: every corner turns the same way, or not at
    all. Repeated and in-line corners are allowed."""
    n = len(polygon)
    turns = {
        _sign(cross(sub(polygon[(i + 1) % n], polygon[i]), sub(polygon[(i + 2) % n], polygon[i])))
        for i in range(n)
    }
    return not ({1, -1} <= turns)


def _sign(value: Num) -> int:
    return (value > 0) - (value < 0)


def segment_inside_polygon(p: Point, q: Point, polygon: list[Point]) -> list[Interval]:
    """The parts of segment pq that are inside the polygon (or on its edge), as parameter intervals.

    A convex polygon gives at most one interval, but some tiles are not convex, so this cuts pq at
    every place it meets an edge and tests each piece.
    """
    n = len(polygon)
    cuts: set[Num] = {0, 1}
    for i in range(n):
        contact = contact_interval(p, q, polygon[i], polygon[(i + 1) % n])
        if contact is not None:
            cuts.update(contact)
    ordered = sorted(cuts)

    intervals: list[Interval] = []
    for t in ordered:
        if point_in_polygon(lerp(p, q, t), polygon):
            intervals.append((t, t))
    for low, high in pairwise(ordered):
        if point_in_polygon(lerp(p, q, divide(low + high, 2)), polygon):
            intervals.append((low, high))
    return merge_intervals(intervals)


def merge_intervals(intervals: list[Interval]) -> list[Interval]:
    """Union of closed intervals. Intervals that merely touch are joined."""
    merged: list[Interval] = []
    for low, high in sorted(intervals):
        if merged and low <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return merged


def covers_unit_interval(intervals: list[Interval]) -> bool:
    merged = merge_intervals(intervals)
    return any(low <= 0 and high >= 1 for low, high in merged)


def strictly_inside_polygon(p: Point, polygon: list[Point]) -> bool:
    """Inside, and not on the edge."""
    n = len(polygon)
    on_edge = any(point_on_segment(p, polygon[i], polygon[(i + 1) % n]) for i in range(n))
    return not on_edge and point_in_polygon(p, polygon)


def interior_point(polygon: list[Point]) -> Point | None:
    """Some point strictly inside the polygon. None if it has no area."""
    n = len(polygon)
    for i in range(n):
        a, b, c = polygon[i], polygon[(i + 1) % n], polygon[(i + 2) % n]
        if cross(sub(b, a), sub(c, a)) == 0:
            continue
        centre = (divide(a[0] + b[0] + c[0], 3), divide(a[1] + b[1] + c[1], 3))
        if strictly_inside_polygon(centre, polygon):
            return centre
    return None


def polygons_overlap(first: list[Point], second: list[Point], within: Box | None = None) -> bool:
    return overlap_point(first, second, within) is not None


def overlap_point(
    first: list[Point], second: list[Point], within: Box | None = None
) -> Point | None:
    """A point where the two polygons share area, if they do: touching along an edge or at a corner
    doesn't count. With `within`, only area inside that box counts. The point is inside one of them
    and on the outline of the other, or inside both.

    Any shared area has an outline, made of pieces of the three outlines. A piece of one outline
    which is strictly inside the other two shapes is looked for first. If there is none, the shared
    area must be the whole of one polygon, so a point inside each is tried.
    """
    shapes = [first, second]
    if within is not None:
        x0, x1, z0, z1 = within
        shapes.append([(x0, z0), (x1, z0), (x1, z1), (x0, z1)])

    for shape in shapes:
        others = [other for other in shapes if other is not shape]
        n = len(shape)
        for i in range(n):
            p, q = shape[i], shape[(i + 1) % n]
            if p == q:
                continue
            cuts: set[Num] = {0, 1}
            for other in others:
                for j in range(len(other)):
                    contact = contact_interval(p, q, other[j], other[(j + 1) % len(other)])
                    if contact is not None:
                        cuts.update(contact)
            for low, high in pairwise(sorted(cuts)):
                middle = lerp(p, q, divide(low + high, 2))
                if all(strictly_inside_polygon(middle, other) for other in others):
                    return middle

    for shape in shapes[:2]:
        inside = interior_point(shape)
        if inside is not None and all(
            strictly_inside_polygon(inside, other) for other in shapes if other is not shape
        ):
            return inside
    return None


def bounding_box(points: list[Point]) -> tuple[Num, Num, Num, Num]:
    """(min x, max x, min z, max z)"""
    xs = [p[0] for p in points]
    zs = [p[1] for p in points]
    return (min(xs), max(xs), min(zs), max(zs))


def boxes_overlap(box_a: tuple[Num, Num, Num, Num], box_b: tuple[Num, Num, Num, Num]) -> bool:
    return (
        box_a[0] <= box_b[1]
        and box_b[0] <= box_a[1]
        and box_a[2] <= box_b[3]
        and box_b[2] <= box_a[3]
    )


def grow_box(box: tuple[Num, Num, Num, Num], margin: Num) -> tuple[Num, Num, Num, Num]:
    return (box[0] - margin, box[1] + margin, box[2] - margin, box[3] + margin)
