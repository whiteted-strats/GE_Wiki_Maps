"""The two questions the game asks about a move, answered exactly and on the right floor.

  `trace`  - is there line of sight from p to q? Bond has no width while he moves.
  `fits`   - does Bond, a disc of radius 30, fit at p?

Both take the tile that p is on. Everything is then found by following links from that tile, so
floors above and below, and unlinked parts of the level which happen to overlap from above, are
never considered.

`present` says which objects exist: None means every object as it was dumped, and a set means only
those objects (an empty set is the bare level). Objects may be destructible, so gaps are examined
with and without them.
"""

from dataclasses import dataclass, field
from fractions import Fraction

from gaps.exact import (
    Point,
    bounding_box,
    boxes_overlap,
    contact_interval,
    covers_unit_interval,
    dist2_point_segment,
    grow_box,
    lerp,
    point_in_polygon,
    segment_inside_polygon,
)
from gaps.mesh import BoundarySegment, Box, Level

ObjectsPresent = frozenset[int] | None


@dataclass
class Trace:
    clear: bool
    reason: str = ""  # why not, when not clear
    blocker: BoundarySegment | None = None  # the wall or object side in the way, if that's why
    tiles: set[int] = field(default_factory=set)  # every tile the line passes over
    end_tiles: set[int] = field(default_factory=set)  # the tiles that q is on


def is_present(obj: int, present: ObjectsPresent) -> bool:
    return present is None or obj in present


def walls_near(
    level: Level, start_tile: int, region: Box, present: ObjectsPresent
) -> list[BoundarySegment]:
    """Walls and object sides in the region, on the sheet that start_tile belongs to."""
    tiles = level.linked_tiles_within(start_tile, region)
    walls = level.walls_of_tiles(tiles)
    for obj in level.objects_among_tiles(tiles):
        if is_present(obj, present):
            walls.extend(level.sides_of_object(obj))
    return [wall for wall in walls if boxes_overlap(wall.box, region)]


def trace(
    level: Level,
    start_tile: int,
    p: Point,
    q: Point,
    present: ObjectsPresent,
    may_touch_walls_at_ends: bool = False,
) -> Trace:
    """Line of sight from p (on start_tile) to q.

    The line is clear if linked tiles cover every part of it and it touches no wall or object on
    the way. `may_touch_walls_at_ends` is for lines drawn from one wall to another, which touch
    walls at p and q by construction; touching anywhere in between still blocks them.
    """
    tiles_over, end_tiles, covered = _tiles_along(level, start_tile, p, q)
    result = Trace(clear=False, tiles=tiles_over, end_tiles=end_tiles)
    if not covered:
        result.reason = "leaves the walkable area"
        return result

    walls = level.walls_of_tiles(tiles_over)
    objects = [obj for obj in level.objects_among_tiles(tiles_over) if is_present(obj, present)]
    for obj in objects:
        walls.extend(level.sides_of_object(obj))

    for wall in walls:
        contact = contact_interval(p, q, wall.a, wall.b)
        if contact is None:
            continue
        only_at_ends = contact[1] <= 0 or contact[0] >= 1
        if not (may_touch_walls_at_ends and only_at_ends):
            result.reason = "touches a wall" if wall.obj is None else "touches an object"
            result.blocker = wall
            return result

    # A line which touches none of an object's sides could still be entirely inside it
    midpoint = lerp(p, q, Fraction(1, 2))
    for obj in objects:
        outline = level.objects[obj].points
        if len(outline) >= 3 and point_in_polygon(midpoint, outline):
            result.reason = "inside an object"
            result.blocker = level.sides_of_object(obj)[0]
            return result

    result.clear = True
    return result


def fits(
    level: Level, tile: int, p: Point, present: ObjectsPresent
) -> tuple[bool, BoundarySegment | None]:
    """Whether Bond fits at p, which is on `tile`. If not, also the wall he overlaps."""
    radius = level.bond_radius
    region = grow_box(bounding_box([p]), radius)
    for wall in walls_near(level, tile, region, present):
        if dist2_point_segment(p, wall.a, wall.b) < radius * radius:
            return (False, wall)
    return (True, None)


def _tiles_along(
    level: Level, start_tile: int, p: Point, q: Point
) -> tuple[set[int], set[int], bool]:
    """Follows the line from start_tile through links, only crossing edges the line touches.

    Returns (tiles the line passes over, tiles that q is on, whether those tiles cover the line).
    Following every touched edge, rather than picking one exit per tile, means a line that passes
    exactly through a corner or along an edge needs no special cases. Vertical tiles, which have no
    area from above, are crossed like any other.
    """
    tiles_over: set[int] = set()
    end_tiles: set[int] = set()
    covered_parts = []
    visited = {start_tile}
    stack = [start_tile]

    while stack:
        tile = level.tiles[stack.pop()]
        inside = segment_inside_polygon(p, q, tile.points)
        if not inside:
            continue
        tiles_over.add(tile.addr)
        covered_parts.extend(inside)
        if any(high >= 1 for _, high in inside):
            end_tiles.add(tile.addr)

        for i, neighbour in enumerate(tile.links):
            if neighbour == 0 or neighbour in visited or neighbour not in level.tiles:
                continue
            if contact_interval(p, q, *tile.edge(i)) is not None:
                visited.add(neighbour)
                stack.append(neighbour)

    return (tiles_over, end_tiles, covers_unit_interval(covered_parts))
