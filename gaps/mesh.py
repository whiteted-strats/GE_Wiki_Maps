"""Loads a level from data/<level>.py into exact coordinates.

Units. Everything here is in world coordinates, the ones the game computes in and the data files
hold, treated as centimetres: Bond's radius is 30. Every coordinate is a float32 in the game, and
float32s are rationals, so they are held as Fractions and all the geometry is exact. The data files
print values to 14 digits, enough to say which float32 each was, and that float32 is recovered:
- object outlines and height ranges are float32s read straight from memory, so are just snapped
- tile corners and heights are stored by the game as int16s, which the dumper divided by the
  level's scale in a double. The int16 is recovered, and the float32 the game gets from the same
  division is recomputed from it exactly (a single float32 division is correctly rounded).
`Level.to_cm` is left over from when this package worked in other units, and is now the identity.

Sheets. Bond moves in XZ, but floors that overlap in XZ do not interact: only tile links join the
walkable area together. So nothing here ever asks "which tiles are near this point" globally. The
question is always "which tiles can be reached from this tile, through links, without leaving this
small region", see `Level.linked_tiles_within`.
"""

import heapq
import math
import struct
from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from types import ModuleType

from gaps.exact import (
    Num,
    Point,
    bounding_box,
    boxes_overlap,
    contact_interval,
    cross,
    divide,
    dot,
    grow_box,
    lerp,
    merge_intervals,
    overlap_point,
    point_in_polygon,
    polygons_overlap,
    sub,
)

Box = tuple[Num, Num, Num, Num]

BOND_RADIUS_CM = 30
STOREY_SEPARATION_CM = 100  # see Level.linked_tiles_within. Storeys are 2 m apart or more
FLOODS_REMEMBERED = 20000  # see Level.linked_tiles_within. Only there to save time

# Objects which Bond walks through: pick-ups, and the locks which sit on doors
OUTSIDE_WALKABLE_AREA = (
    "outside the walkable area: seen from above, no part of it is over the floor"
)

NON_BLOCKING_TYPES = {"weapon", "ammo", "body_armour", "key", "lock"}


@dataclass
class Tile:
    addr: int
    name: int
    room: int
    points: list[Point]  # float32s as Fractions, in world coordinates (cm)
    heights: list[float]  # float32s, one per point
    links: list[int]  # links[i] is the tile across the edge points[i] -> points[i+1], 0 for a wall
    box: Box
    is_vertical: bool  # zero area from above: a riser or a ledge

    def edge(self, i: int) -> tuple[Point, Point]:
        return (self.points[i], self.points[(i + 1) % len(self.points)])

    def height_at(self, point: Point) -> float:
        """Centimetres, in floats: the height of the tile's plane above or below this point. Only
        used to tell another storey from the same floor drawn twice, never for geometry."""
        n = len(self.points)
        for i in range(n):
            (ax, az), (bx, bz), (cx, cz) = (
                (float(x), float(z))
                for x, z in (self.points[i - 2], self.points[i - 1], self.points[i])
            )
            doubled_area = (bx - ax) * (cz - az) - (bz - az) * (cx - ax)
            if doubled_area != 0:
                ha, hb, hc = self.heights[i - 2], self.heights[i - 1], self.heights[i]
                x, z = float(point[0]) - ax, float(point[1]) - az
                u = (x * (cz - az) - z * (cx - ax)) / doubled_area
                v = (z * (bx - ax) - x * (bz - az)) / doubled_area
                return ha + u * (hb - ha) + v * (hc - ha)
        return self.heights[0]


@dataclass
class LevelObject:
    addr: int
    type: str
    preset: int
    points: list[Point]  # float32s as Fractions, in world coordinates (cm)
    box: Box
    anchor_tile: int  # the tile the game says it stands on
    health: float
    height_range: tuple[float, float] | None  # centimetres, as dumped
    floor_clearance: float | None  # cm from the top of its tile up to its bottom. See below
    sheet_tiles: frozenset[int] = frozenset()  # the tiles it stands among

    @property
    def is_door(self) -> bool:
        return self.type == "door"


@dataclass(frozen=True)
class BoundarySegment:
    """A piece of wall: a tile edge with nothing linked across it, or the side of an object."""

    id: int
    a: Point
    b: Point
    tile: int | None = None  # the tile this is a wall of ...
    edge_index: int | None = None
    obj: int | None = None  # ... or the object it is a side of

    @property
    def box(self) -> Box:
        return bounding_box([self.a, self.b])


@dataclass
class Level:
    name: str
    scale: Fraction
    tiles: dict[int, Tile]
    objects: dict[int, LevelObject]
    segments: list[BoundarySegment] = field(default_factory=list)
    skipped_objects: list[tuple[int, str, str]] = field(default_factory=list)  # addr, type, why
    # Vertical tiles' edges which aren't walls all the way along: tile, edge, the parts which are
    vertical_edges_left_out: list[tuple[int, int, list[tuple[Point, Point]]]] = field(
        default_factory=list
    )
    _tile_segments: dict[int, list[BoundarySegment]] = field(default_factory=dict)
    _object_segments: dict[int, list[BoundarySegment]] = field(default_factory=dict)
    _objects_on_tile: dict[int, list[int]] = field(default_factory=dict)
    _walls_at_corner: dict[Point, list[BoundarySegment]] = field(default_factory=dict)
    _flood_cache: dict[tuple[int, Box], set[int]] = field(default_factory=dict)
    _overlap_cache: dict[tuple[int, int], bool] = field(default_factory=dict)

    @property
    def bond_radius(self) -> int:
        return BOND_RADIUS_CM

    def from_metres(self, metres: float) -> Fraction:
        """A length in metres, as written in the filter settings, in centimetres."""
        return Fraction(str(metres)) * 100

    def to_cm(self, length: Num) -> float:
        return float(length)

    def to_cm_point(self, p: Point) -> tuple[float, float]:
        return (self.to_cm(p[0]), self.to_cm(p[1]))

    def linked_tiles_within(self, start_tile: int, region: Box) -> set[int]:
        """The tiles reachable from start_tile through links, only passing through tiles whose
        bounding box touches the region. This is what "nearby" means on a sheet.

        A sheet doesn't lie over itself. Where links lead round to another storey within the
        region, a tile is left out if, from above and inside the region, it lies over or under a
        tile already reached, with at least STOREY_SEPARATION_CM between them. Tiles are reached
        nearest first, measured along the way there from the middle of the region, so it is the far
        storey which is left out. Vertical tiles have no area, so they are never left out and never
        cause it.

        The separation is there because tiles of one floor do overlap a little where the level was
        drawn carelessly (Control's 033A08 and 033D08, by up to 1.5 cm). Those must both be kept.
        It is the only use made of heights.
        """
        key = (start_tile, region)
        if key not in self._flood_cache:
            if len(self._flood_cache) >= FLOODS_REMEMBERED:
                self._flood_cache.clear()
            self._flood_cache[key] = self._flood(start_tile, region)
        return self._flood_cache[key]

    def _flood(self, start_tile: int, region: Box) -> set[int]:
        middle = (float(region[0] + region[1]) / 2, float(region[2] + region[3]) / 2)
        reached: set[int] = set()
        with_area: list[Tile] = []  # those reached which aren't vertical
        queued = {start_tile}
        queue: list[tuple[float, int, tuple[float, float]]] = [(0.0, start_tile, middle)]
        while queue:
            distance, addr, position = heapq.heappop(queue)
            tile = self.tiles[addr]
            if not tile.is_vertical:
                if any(self._overlap(tile, other, region) for other in with_area):
                    continue
                with_area.append(tile)
            reached.add(addr)
            for i, neighbour in enumerate(tile.links):
                if neighbour == 0 or neighbour in queued or neighbour not in self.tiles:
                    continue
                if boxes_overlap(self.tiles[neighbour].box, region):
                    queued.add(neighbour)
                    a, b = tile.edge(i)
                    crossing = _nearest_on_edge(position, a, b)
                    step = math.dist(position, crossing)
                    heapq.heappush(queue, (distance + step, neighbour, crossing))
        return reached

    def _overlap(self, tile: Tile, other: Tile, region: Box) -> bool:
        """Whether one is on another storey from the other, over or under it in the region."""
        if not boxes_overlap(tile.box, other.box):
            return False
        # Most pairs don't overlap at all, which holds whatever the region, so is remembered
        pair = (min(tile.addr, other.addr), max(tile.addr, other.addr))
        if pair not in self._overlap_cache:
            self._overlap_cache[pair] = polygons_overlap(tile.points, other.points)
        if not self._overlap_cache[pair]:
            return False
        shared = overlap_point(tile.points, other.points, region)
        if shared is None:
            return False
        return abs(tile.height_at(shared) - other.height_at(shared)) >= STOREY_SEPARATION_CM

    def forget_caches(self) -> None:
        """Before saving: these can be worked out again."""
        self._flood_cache.clear()
        self._overlap_cache.clear()

    def walls_of_tiles(self, tiles: set[int]) -> list[BoundarySegment]:
        return [segment for tile in tiles for segment in self._tile_segments.get(tile, [])]

    def objects_among_tiles(self, tiles: set[int]) -> set[int]:
        return {obj for tile in tiles for obj in self._objects_on_tile.get(tile, [])}

    def sides_of_object(self, obj: int) -> list[BoundarySegment]:
        return self._object_segments[obj]

    def walls_meeting_at(self, corner: Point) -> list[BoundarySegment]:
        """The tile walls which have an end at this corner, on whatever floor."""
        if not self._walls_at_corner:
            for segment in self.segments:
                if segment.tile is not None:
                    for end in (segment.a, segment.b):
                        self._walls_at_corner.setdefault(end, []).append(segment)
        return self._walls_at_corner.get(corner, [])

    def room_of_object(self, obj: int) -> int:
        return self.tiles[self.objects[obj].anchor_tile].room


def snap_to_float32(value: float) -> Fraction:
    """The data files print values to 14 digits. Where the game held a float32, that is enough to
    tell which one, so recover it exactly."""
    return Fraction(struct.unpack("f", struct.pack("f", value))[0])


def nearest_float32(value: Fraction) -> Fraction:
    """The float32 nearest to an exact value, ties to even: what one correctly rounded float32
    operation gives. Done in integers, so no double gets in the way."""
    if value == 0:
        return Fraction(0)
    magnitude = abs(value)
    exponent = magnitude.numerator.bit_length() - magnitude.denominator.bit_length()
    # 2**exponent <= magnitude < 2**(exponent + 2); settle which
    if magnitude < Fraction(2) ** exponent:
        exponent -= 1
    elif magnitude >= Fraction(2) ** (exponent + 1):
        exponent += 1
    unit = Fraction(2) ** (exponent - 23)  # a 24-bit significand
    scaled = magnitude / unit
    whole, remainder = divmod(scaled.numerator, scaled.denominator)
    twice = 2 * remainder
    if twice > scaled.denominator or (twice == scaled.denominator and whole % 2 == 1):
        whole += 1
    result = whole * unit
    return -result if value < 0 else result


def float32_step(value: Fraction) -> Fraction:
    """The distance from a float32 to the next one up in magnitude: one unit in its last place."""
    magnitude = abs(value)
    if magnitude == 0:
        return Fraction(2) ** -149
    exponent = magnitude.numerator.bit_length() - magnitude.denominator.bit_length()
    if magnitude < Fraction(2) ** exponent:
        exponent -= 1
    elif magnitude >= Fraction(2) ** (exponent + 1):
        exponent += 1
    return Fraction(2) ** (exponent - 23)


def _stored_int16(level: Level, tile_addr: int, what: str, printed: float) -> Fraction:
    """A tile coordinate, as the game has it: the int16 it stores, divided by the scale in one
    float32 operation. The dumper did that division in a double, so the int16 is recovered from
    the printed value and the division redone."""
    stored = round(printed * float(level.scale))
    if abs(printed * float(level.scale) - stored) > 1e-6 or not -32768 <= stored <= 32767:
        raise ValueError(f"tile {tile_addr:#x}: {what} {printed!r} is not an int16 / scale")
    return nearest_float32(Fraction(stored) / level.scale)


def _snapped_range(height_range: tuple[float, float] | None) -> tuple[float, float] | None:
    if height_range is None:
        return None
    low, high = height_range
    return (float(snap_to_float32(low)), float(snap_to_float32(high)))


def _nearest_on_edge(position: tuple[float, float], a: Point, b: Point) -> tuple[float, float]:
    """In floats: this only decides the order in which tiles are reached."""
    ax, az, bx, bz = float(a[0]), float(a[1]), float(b[0]), float(b[1])
    length2 = (bx - ax) ** 2 + (bz - az) ** 2
    if length2 == 0:
        return (ax, az)
    t = ((position[0] - ax) * (bx - ax) + (position[1] - az) * (bz - az)) / length2
    t = max(0.0, min(1.0, t))
    return (ax + t * (bx - ax), az + t * (bz - az))


def load_level(name: str, data: ModuleType, removed: dict[int, str] | None = None) -> Level:
    """`data` is a data/<level>.py module, or anything with `tiles`, `objects` and `level_scale`.

    `removed` maps objects which are to be left out of the level altogether to the reason why.
    Only gaps/filters/levels/<level>.py can ask for that, and each one is recorded among the
    skipped objects.
    """
    level = Level(name=name, scale=snap_to_float32(data.level_scale), tiles={}, objects={})
    for addr, raw in data.tiles.items():
        level.tiles[addr] = _load_tile(level, addr, raw)

    _add_tile_walls(level)
    for addr, raw in data.objects.items():
        if removed and addr in removed:
            level.skipped_objects.append((addr, raw["type"], removed[addr]))
        else:
            _add_object(level, addr, raw)
    return level


def _load_tile(level: Level, addr: int, raw: dict) -> Tile:
    points: list[Point] = [
        (_stored_int16(level, addr, "x", x), _stored_int16(level, addr, "z", z))
        for x, z in raw["points"]
    ]
    heights = [float(_stored_int16(level, addr, "y", h)) for h in raw["heights"]]

    n = len(points)
    doubled_area = sum(
        points[i][0] * points[(i + 1) % n][1] - points[(i + 1) % n][0] * points[i][1]
        for i in range(n)
    )
    return Tile(
        addr=addr,
        name=raw["name"],
        room=raw["room"],
        points=points,
        heights=heights,
        links=list(raw["links"]),
        box=bounding_box(points),
        is_vertical=(doubled_area == 0),
    )


def _add_tile_walls(level: Level) -> None:
    """Every edge with no link is a wall. On vertical tiles, only where floor leads into it.

    The game only meets an edge by walking into its tile through links, and then only when trying
    to leave across it (see walkAcrossTiles in lib/path_finding.py). From above a vertical tile is
    a line, so it can only be walked into across a floor tile's edge which is linked to it. Where
    that happens and the vertical tile has no link onwards, the floor has a wall there: the floor
    tile's own edge doesn't show it, being linked. Anywhere else along it, nothing can be stopped
    by the vertical tile's edge. One lies right across a doorway which Bond walks through: the
    skirting of Facility's room 0x3d, by door 0x1c9794. Those stretches are recorded in
    `vertical_edges_left_out`.
    """
    for tile in level.tiles.values():
        for i, neighbour in enumerate(tile.links):
            a, b = tile.edge(i)
            if neighbour != 0 or a == b:
                continue  # a == b is the end of a vertical tile, which has no length from above
            stretches = [(a, b)]
            if tile.is_vertical:
                stretches = _stretches_floor_leads_into(level, tile, a, b)
                if stretches != [(a, b)]:
                    level.vertical_edges_left_out.append((tile.addr, i, stretches))
            for start, end in stretches:
                segment = BoundarySegment(
                    id=len(level.segments), a=start, b=end, tile=tile.addr, edge_index=i
                )
                level.segments.append(segment)
                level._tile_segments.setdefault(tile.addr, []).append(segment)


def _stretches_floor_leads_into(
    level: Level, vertical: Tile, a: Point, b: Point
) -> list[tuple[Point, Point]]:
    """The parts of a vertical tile's edge ab which lie along a floor tile's edge that is linked
    to the vertical tile, or to another vertical tile joined to it in the same line."""
    direction = sub(b, a)
    length2 = dot(direction, direction)

    def in_line(tile: Tile) -> bool:
        return tile.is_vertical and all(cross(direction, sub(p, a)) == 0 for p in tile.points)

    joined = {vertical.addr}
    to_visit = [vertical]
    while to_visit:
        for neighbour in to_visit.pop().links:
            if (
                neighbour in level.tiles
                and neighbour not in joined
                and in_line(level.tiles[neighbour])
            ):
                joined.add(neighbour)
                to_visit.append(level.tiles[neighbour])

    # Every floor tile which leads in is itself a link of one of the joined tiles
    leading_in = []
    for addr in joined:
        for neighbour in level.tiles[addr].links:
            floor = level.tiles.get(neighbour)
            if floor is None or floor.is_vertical:
                continue
            for i, link in enumerate(floor.links):
                if link in joined:
                    along = [divide(dot(sub(p, a), direction), length2) for p in floor.edge(i)]
                    leading_in.append((max(0, min(along)), min(1, max(along))))
    covered = merge_intervals([(low, high) for low, high in leading_in if low < high])
    return [(a, b) if (low, high) == (0, 1) else (lerp(a, b, low), lerp(a, b, high))
            for low, high in covered]  # fmt: skip


def _add_object(level: Level, addr: int, raw: dict) -> None:
    if raw["type"] in NON_BLOCKING_TYPES or raw.get("collectible"):
        level.skipped_objects.append((addr, raw["type"], "Bond walks through it"))
        return
    if not raw.get("points"):
        level.skipped_objects.append((addr, raw["type"], "no collision outline in the data"))
        return

    points: list[Point] = []
    for x, z in raw["points"]:
        # Read from memory by the dumper, so the float32 is what the game has
        point = (snap_to_float32(x), snap_to_float32(z))
        if not points or point != points[-1]:
            points.append(point)
    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    if len(points) < 2:
        level.skipped_objects.append((addr, raw["type"], "collision outline is a single point"))
        return
    if raw.get("tile") not in level.tiles:
        # Without its tile there is no telling which floor it is on, so it can't take part
        level.skipped_objects.append(
            (addr, raw["type"], "the tile it stands on is not in the data")
        )
        return

    # Which tiles it stands among. The game gives one tile per object, and outlines usually spill
    # over that tile's edges, so spread out from it through links as far as the outline (plus
    # Bond's diameter) reaches, so that it only interacts with the part of the sheet it is on. This
    # trusts the tile the game gives, which is wrong for a few doors: see gaps/terminology.md,
    # "overhead object".
    box = bounding_box(points)
    sheet_tiles = frozenset(
        level.linked_tiles_within(raw["tile"], grow_box(box, 2 * level.bond_radius))
    )
    if not _is_over_walkable_area(level, points, box):
        level.skipped_objects.append((addr, raw["type"], OUTSIDE_WALKABLE_AREA))
        return

    level.objects[addr] = LevelObject(
        addr=addr,
        type=raw["type"],
        preset=raw["preset"],
        points=points,
        box=box,
        anchor_tile=raw["tile"],
        health=raw.get("health", 0),
        height_range=_snapped_range(raw.get("height_range")),
        floor_clearance=floor_clearance(level, raw),
        sheet_tiles=sheet_tiles,
    )
    for tile in sheet_tiles:
        level._objects_on_tile.setdefault(tile, []).append(addr)

    sides = []
    for i in range(len(points)):
        a, b = points[i], points[(i + 1) % len(points)]
        if len(points) == 2 and i == 1:
            break  # a two point outline is one side, not two
        segment = BoundarySegment(id=len(level.segments), a=a, b=b, obj=addr)
        level.segments.append(segment)
        sides.append(segment)
    level._object_segments[addr] = sides


def _is_over_walkable_area(level: Level, outline: list[Point], box: Box) -> bool:
    """Whether any part of the outline, seen from above, is over any tile at all.

    An object which isn't can never matter, so it is left out. Gaps are made of walkable area, and
    objects only ever take away from it: a pinch line has to lie over tiles, as does a line of
    sight. And such an object can't stop Bond fitting either, because to reach it from a tile you
    must cross a wall, which is therefore at least as close to him as the object is.

    Every tile of the level is tried, on every storey, rather than only those near the tile which
    the object is attached to. That attachment can't be relied on: Silo and Frigate have doors
    attached to a tile in a different room from the one they are drawn in.
    """
    sides = [(outline[i], outline[(i + 1) % len(outline)]) for i in range(len(outline))]
    for tile in level.tiles.values():
        if not boxes_overlap(tile.box, box):
            continue
        if any(point_in_polygon(corner, tile.points) for corner in outline):
            return True
        if len(outline) >= 3 and any(point_in_polygon(corner, outline) for corner in tile.points):
            return True
        for i in range(len(tile.points)):
            a, b = tile.edge(i)
            if a != b and any(contact_interval(p, q, a, b) is not None for p, q in sides):
                return True
    return False


def floor_clearance(level: Level, raw: dict) -> float | None:
    """How far the bottom of the object is above the highest point of the tile it is attached to,
    in centimetres. Negative if it starts below the floor. None if the data has no heights."""
    height_range = _snapped_range(raw.get("height_range"))
    if not height_range:
        return None
    return min(height_range) - max(level.tiles[raw["tile"]].heights)


class SegmentGrid:
    """Buckets segments by position so that nearby pairs can be found without comparing them all.

    Each segment goes into every cell that its bounding box, grown by `reach`, overlaps. Two
    segments closer than 2 * reach are then guaranteed to share a cell: the midpoint between their
    closest points is within `reach` of both.
    """

    def __init__(self, segments: list[BoundarySegment], reach: Num) -> None:
        self.cell = 2 * reach
        self.cells: dict[tuple[int, int], list[BoundarySegment]] = defaultdict(list)
        for segment in segments:
            for key in self._cells_touching(grow_box(segment.box, reach)):
                self.cells[key].append(segment)

    def _cells_touching(self, box: Box) -> list[tuple[int, int]]:
        x_range = range(math.floor(box[0] / self.cell), math.floor(box[1] / self.cell) + 1)
        z_range = range(math.floor(box[2] / self.cell), math.floor(box[3] / self.cell) + 1)
        return [(i, j) for i in x_range for j in z_range]

    def nearby_pairs(self) -> set[tuple[int, int]]:
        """Pairs of segment ids sharing a cell: a superset of the pairs closer than 2 * reach."""
        pairs: set[tuple[int, int]] = set()
        for bucket in self.cells.values():
            for i, first in enumerate(bucket):
                for second in bucket[i + 1 :]:
                    pairs.add((min(first.id, second.id), max(first.id, second.id)))
        return pairs
