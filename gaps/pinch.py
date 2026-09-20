"""Finds every pinch: a pair of walls closer together than Bond's diameter, with floor in between.

Any warp has to pass through one. If Bond fits at two places that can see each other but can't be
walked between, then somewhere between them the walkable area is narrower than he is, and the
narrowest part of that is a pair of wall features with nothing else between them.

So every pair of walls closer than 60 is examined, and each is either kept as a pinch or dismissed
by one of a small number of exact rules. Nothing is dismissed silently: every decision is recorded
with its reason, see `Decision`.
"""

from dataclasses import dataclass
from fractions import Fraction

from gaps.exact import (
    Num,
    Point,
    bounding_box,
    closest_points_between_segments,
    dist2_point_segment,
    grow_box,
    lerp,
    point_in_polygon,
)
from gaps.mesh import BoundarySegment, Level, SegmentGrid
from gaps.sheet import trace, walls_near

# Reasons for dismissing a pair of walls. Each is an exact test.
NOT_LINKED = "the line between them leaves the walkable area (a wall's thickness, or another floor)"
BLOCKED = "the line between them touches another wall"
WRONG_SIDE = "the far wall faces the other way (it belongs to floor which isn't linked here)"
TIGHTER_NEARBY = "another wall pokes into the space between them, so a tighter pair covers this gap"
NOT_OVER_FLOOR = "neither wall could be placed on a tile"


@dataclass
class Pinch:
    """Two walls closer than Bond's diameter, with clear floor between them."""

    first: BoundarySegment
    second: BoundarySegment
    a: Point  # the closest point on `first` ...
    b: Point  # ... and on `second`. The line a -> b is the narrowest part of the gap.
    width2: Num  # squared width, scaled units
    start_tile: int  # a tile that `a` is on, from which the gap can be reached through links
    needs: frozenset[int]  # objects which form this gap. Without them it isn't there.

    @property
    def midpoint(self) -> Point:
        return lerp(self.a, self.b, Fraction(1, 2))


@dataclass
class Decision:
    """The record of one pair of walls which was closer than Bond's diameter."""

    first: int  # segment ids
    second: int
    width_cm: float
    kept: bool
    reason: str = ""
    blocker: int | None = None  # the segment id of the wall responsible, where one is


@dataclass
class TouchingWalls:
    """Two unrelated walls which touch: a gap of width zero. Bond can't pass, but it is reported."""

    first: BoundarySegment
    second: BoundarySegment
    at: Point


def find_pinches(level: Level) -> tuple[list[Pinch], list[TouchingWalls], list[Decision]]:
    diameter2 = (2 * level.bond_radius) ** 2
    segments = level.segments
    pinches: list[Pinch] = []
    touching: list[TouchingWalls] = []
    decisions: list[Decision] = []

    for first_id, second_id in sorted(SegmentGrid(segments, level.bond_radius).nearby_pairs()):
        first, second = segments[first_id], segments[second_id]
        if _are_neighbours(first, second):
            continue  # consecutive pieces of one wall meet at a corner, which is not a gap

        width2, a, b = closest_points_between_segments(first.a, first.b, second.a, second.b)
        if width2 >= diameter2:
            continue
        if width2 == 0:
            if _on_same_sheet(level, first, second, a):
                touching.append(TouchingWalls(first, second, a))
            continue

        pinch, decision = _examine(level, first, second, a, b, width2)
        decisions.append(decision)
        if pinch is not None:
            pinches.append(pinch)

    return pinches, touching, decisions


def _examine(
    level: Level, first: BoundarySegment, second: BoundarySegment, a: Point, b: Point, width2: Num
) -> tuple[Pinch | None, Decision]:
    # Start from a tile wall if there is one, since it says which tile to start from
    if first.tile is None and second.tile is not None:
        first, second, a, b = second, first, b, a

    decision = Decision(first.id, second.id, _width_in_cm(level, width2), kept=False)
    needs = frozenset(seg.obj for seg in (first, second) if seg.obj is not None)

    start_tile = first.tile if first.tile is not None else _tile_under(level, first.obj, a)
    if start_tile is None:
        decision.reason = NOT_OVER_FLOOR
        return None, decision

    # Rule 1: there must be floor all the way across, and nothing else in the way
    line = trace(level, start_tile, a, b, present=needs, may_touch_walls_at_ends=True)
    if not line.clear:
        decision.reason = NOT_LINKED if line.blocker is None else BLOCKED
        decision.blocker = line.blocker.id if line.blocker else None
        return None, decision

    # Rule 2: the far wall must be a wall of the floor we arrived on, not the back of some other
    if second.tile is not None and second.tile not in line.tiles:
        decision.reason = WRONG_SIDE
        return None, decision
    if second.obj is not None and not (level.objects[second.obj].sheet_tiles & line.tiles):
        decision.reason = WRONG_SIDE
        return None, decision

    # Rule 3: nothing else may reach into the circle drawn on the line a -> b. If something does,
    # it forms a tighter gap with one of these walls, and that pair is examined in its own right.
    centre = lerp(a, b, Fraction(1, 2))
    circle_radius2 = width2 / 4
    region = grow_box(bounding_box([a, b]), _ceil_sqrt(circle_radius2))
    for wall in walls_near(level, start_tile, region, present=needs):
        if wall.id in (first.id, second.id):
            continue
        if dist2_point_segment(centre, wall.a, wall.b) < circle_radius2:
            decision.reason = TIGHTER_NEARBY
            decision.blocker = wall.id
            return None, decision

    decision.kept = True
    return Pinch(first, second, a, b, width2, start_tile, needs), decision


def _are_neighbours(first: BoundarySegment, second: BoundarySegment) -> bool:
    """Whether two segments are consecutive pieces of the same wall."""
    share_a_corner = bool({first.a, first.b} & {second.a, second.b})
    if first.obj is not None or second.obj is not None:
        return share_a_corner and first.obj == second.obj
    return share_a_corner


def _on_same_sheet(
    level: Level, first: BoundarySegment, second: BoundarySegment, at: Point
) -> bool:
    """For two touching walls: are they really in the same place, or on different floors?"""
    start_tile = first.tile if first.tile is not None else second.tile
    if start_tile is None:
        return level.objects[first.obj].sheet_tiles == level.objects[second.obj].sheet_tiles
    nearby = level.linked_tiles_within(start_tile, grow_box(bounding_box([at]), level.bond_radius))
    other = second if first.tile is not None else first
    if other.tile is not None:
        return other.tile in nearby
    return bool(level.objects[other.obj].sheet_tiles & nearby)


def _tile_under(level: Level, obj: int | None, p: Point) -> int | None:
    """A tile, among those the object stands on, which contains p."""
    if obj is None:
        return None
    for tile in sorted(level.objects[obj].sheet_tiles):
        if point_in_polygon(p, level.tiles[tile].points):
            return tile
    return None


def _width_in_cm(level: Level, width2: Num) -> float:
    return level.to_cm(float(width2) ** 0.5)


def _ceil_sqrt(value: Num) -> int:
    """An integer at least as big as the square root. Only used to size a search box generously."""
    return int(float(value) ** 0.5) + 2


def describe(level: Level, segment: BoundarySegment) -> str:
    if segment.tile is not None:
        tile = level.tiles[segment.tile]
        return f"wall of tile {tile.name:06X} (room {tile.room:#04x})"
    obj = level.objects[segment.obj]
    return f"{obj.type} {obj.addr:#x} (preset {obj.preset:#06x})"


def feature_key(level: Level, segment: BoundarySegment) -> str:
    """A short name for a wall which doesn't change between runs: the tile's name and which of its
    edges, or the object's address and which of its sides."""
    if segment.tile is not None:
        return f"{level.tiles[segment.tile].name:06X}.{segment.edge_index}"
    side = level.sides_of_object(segment.obj).index(segment)
    return f"{segment.obj:#x}.{side}"
