"""The "narrow pocket" filter: the floor on one side of a pinch is too narrow for Bond to be in.

A warp through a pinch needs somewhere for Bond to stand on each side of it. The *pocket* on one
side is everywhere that can be reached from that side of the pinch line without crossing the pinch
line. If Bond fits nowhere in the pocket, there is no warp.

The test: measure how far the pocket extends in the direction of the pinch line. If that is less
than Bond's diameter, he fits nowhere in it, whatever its shape.

    Put Bond's centre anywhere in the pocket. The pocket is narrower than he is in that direction,
    so to one side or the other his disc reaches beyond it. Walk from his centre in that direction,
    parallel to the pinch line. Within his radius you have left the pocket. The pocket's boundary
    is made of walls and the pinch line, and a walk parallel to the pinch line can't cross it (at
    most it runs along it, to the wall at its end). So you left through a wall, which is therefore
    closer to his centre than his radius.

The direction matters. Measured any other way, his disc could be poking out through the opening,
which is harmless. And the pocket must not be underestimated, or this would claim too much: it is
found by following every tile link, going round corners, and if the pinch ends in mid-floor (at
the corner of an object, say) then the pocket carries on past it.

Objects are left out altogether. They only take floor away, so they can't make Bond fit.
"""

from collections.abc import Iterator
from fractions import Fraction

from gaps.exact import Num, Point, cross, dot, is_convex, lerp, sub
from gaps.mesh import Level, Tile
from gaps.pinch import Pinch
from gaps.sheet import trace

Side = int  # +1 or -1: which side of the pinch line
Piece = tuple[int, Side]  # a tile, or the part of it on that side of the line if the line cuts it


def narrow_pocket(level: Level, pinch: Pinch) -> str | None:
    for side in (1, -1):
        extent2 = _extent_of_pocket2(level, pinch, side)
        if extent2 is not None:
            across_cm = level.to_cm(float(extent2) ** 0.5)
            return (
                f"the floor to one side of it is a pocket only {across_cm:.1f} cm across, measured "
                f"along the pinch line, so Bond fits nowhere in it"
            )
    return None


def _extent_of_pocket2(level: Level, pinch: Pinch, side: Side) -> Num | None:
    """The squared extent of the pocket on this side, measured along the pinch line, in
    units. None as soon as it reaches Bond's diameter, or if the pocket can't be worked out."""
    line = _PinchLine(pinch.a, pinch.b)
    diameter2_times_length2 = (2 * level.bond_radius) ** 2 * line.length2

    over = trace(level, pinch.start_tile, pinch.a, pinch.b, pinch.needs, True).tiles
    to_visit = [(t, side) for t in over if side in line.sides_of(level.tiles[t].points)]
    if not to_visit:
        return None
    visited = set(to_visit)
    low = high = None

    while to_visit:
        tile_addr, on_side = to_visit.pop()
        tile = level.tiles[tile_addr]
        corners = line.part_of(tile, on_side)
        if corners is None:
            return None  # a tile we can't split reliably, so make no claim
        along = [line.along(corner) for corner in corners]
        low = min(along) if low is None else min(low, *along)
        high = max(along) if high is None else max(high, *along)
        if (high - low) ** 2 >= diameter2_times_length2:
            return None

        for piece in _reachable_from(level, line, tile, on_side):
            if piece not in visited:
                visited.add(piece)
                to_visit.append(piece)

    return (high - low) ** 2 / line.length2


def _reachable_from(level: Level, line: "_PinchLine", tile: Tile, on_side: Side) -> Iterator[Piece]:
    """Where the pocket carries on to from this piece of floor."""
    sides_here = line.sides_of(tile.points)

    # Across the line within this tile, but only outside the span of the pinch itself
    if {1, -1} <= sides_here and line.reaches_beyond_pinch(line.cut_through(tile.points)):
        yield (tile.addr, -on_side)

    for i, neighbour in enumerate(tile.links):
        if neighbour == 0 or neighbour not in level.tiles:
            continue
        edge = tile.edge(i)
        edge_sides = line.sides_of(edge)
        if on_side in edge_sides:
            yield (neighbour, on_side)  # the edge is, at least partly, on our side
        elif edge_sides == set() and line.reaches_beyond_pinch(edge):
            # The edge lies along the line. The neighbour is across it, which is allowed only
            # outside the span of the pinch. It is on the far side, unless it is a vertical tile
            # lying along the line too.
            beyond = line.sides_of(level.tiles[neighbour].points)
            yield (neighbour, -on_side if -on_side in beyond else on_side)


class _PinchLine:
    """The infinite line through the pinch's two ends, with positions along it measured so that
    the pinch itself runs from 0 to 1."""

    def __init__(self, a: Point, b: Point) -> None:
        self.a = a
        self.direction = sub(b, a)
        self.length2 = dot(self.direction, self.direction)

    def side_of(self, point: Point) -> int:
        offset = cross(self.direction, sub(point, self.a))
        return (offset > 0) - (offset < 0)

    def sides_of(self, points) -> set[int]:
        """Which sides the points are on, leaving out any which are on the line itself."""
        return {self.side_of(point) for point in points} - {0}

    def along(self, point: Point) -> Num:
        """Position along the line, times the pinch's squared length (to stay in whole numbers)."""
        return dot(self.direction, sub(point, self.a))

    def reaches_beyond_pinch(self, points_on_line) -> bool:
        """Whether these points on the line span anything outside the pinch, which is 0 to 1."""
        positions = [self.along(point) for point in points_on_line]
        return min(positions) < 0 or max(positions) > self.length2

    def cut_through(self, polygon: list[Point]) -> list[Point]:
        """The points at which the line crosses the outline of a polygon."""
        crossings = []
        for i in range(len(polygon)):
            p, q = polygon[i], polygon[(i + 1) % len(polygon)]
            offset_p = cross(self.direction, sub(p, self.a))
            offset_q = cross(self.direction, sub(q, self.a))
            if offset_p == 0:
                crossings.append(p)
            elif offset_p * offset_q < 0:
                crossings.append(lerp(p, q, Fraction(offset_p) / (offset_p - offset_q)))
        return crossings

    def part_of(self, tile: Tile, on_side: Side) -> list[Point] | None:
        """The corners of the part of the tile on this side of the line: all of its corners if the
        line doesn't cut it. None for a tile which is cut but isn't convex, as cutting that could
        leave several parts."""
        if not ({1, -1} <= self.sides_of(tile.points)):
            return tile.points
        if not is_convex(tile.points):
            return None
        kept = [corner for corner in tile.points if self.side_of(corner) == on_side]
        return kept + self.cut_through(tile.points)
