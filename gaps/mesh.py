"""Loads a level from data/<level>.py into exact coordinates.

Units. The game stores tile corners as integers, and the dumper divided them by the level's scale.
Multiplying by the scale again recovers those integers exactly, so everything in this package works
in that integer space ("scaled units"). Object outlines have been rotated by the game so they are
not integers, but they are exact float32 values and so convert to Fractions without any loss.
`Level.to_cm` converts a scaled length back to the units used everywhere else in this repo, which
are centimetres: Bond's radius is 30 cm.

Sheets. Bond moves in XZ, but floors that overlap in XZ do not interact: only tile links join the
walkable area together. So nothing here ever asks "which tiles are near this point" globally. The
question is always "which tiles can be reached from this tile, through links, without leaving this
small region", see `Level.linked_tiles_within`.
"""

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
    grow_box,
    point_in_polygon,
)

Box = tuple[Num, Num, Num, Num]

BOND_RADIUS_CM = 30

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
    points: list[Point]  # integers, in scaled units
    heights: list[float]  # centimetres, one per point
    links: list[int]  # links[i] is the tile across the edge points[i] -> points[i+1], 0 for a wall
    box: Box
    is_vertical: bool  # zero area from above: a riser or a ledge

    def edge(self, i: int) -> tuple[Point, Point]:
        return (self.points[i], self.points[(i + 1) % len(self.points)])


@dataclass
class LevelObject:
    addr: int
    type: str
    preset: int
    points: list[Point]  # Fractions, in scaled units
    scale: float  # scaled units per centimetre, as the level's
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
    _tile_segments: dict[int, list[BoundarySegment]] = field(default_factory=dict)
    _object_segments: dict[int, list[BoundarySegment]] = field(default_factory=dict)
    _objects_on_tile: dict[int, list[int]] = field(default_factory=dict)
    _walls_at_corner: dict[Point, list[BoundarySegment]] = field(default_factory=dict)

    @property
    def bond_radius(self) -> Fraction:
        return BOND_RADIUS_CM * self.scale

    def from_metres(self, metres: float) -> Fraction:
        """A length in metres, as written in the filter settings, in scaled units."""
        return Fraction(str(metres)) * 100 * self.scale

    def to_cm(self, scaled_length: Num) -> float:
        return float(scaled_length / self.scale)

    def to_cm_point(self, p: Point) -> tuple[float, float]:
        return (self.to_cm(p[0]), self.to_cm(p[1]))

    def linked_tiles_within(self, start_tile: int, region: Box) -> set[int]:
        """The tiles reachable from start_tile through links, only passing through tiles whose
        bounding box touches the region. This is what "nearby" means on a sheet."""
        reached = {start_tile}
        stack = [start_tile]
        while stack:
            for neighbour in self.tiles[stack.pop()].links:
                if neighbour == 0 or neighbour in reached or neighbour not in self.tiles:
                    continue
                if boxes_overlap(self.tiles[neighbour].box, region):
                    reached.add(neighbour)
                    stack.append(neighbour)
        return reached

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
    """The data files print the scale to 14 digits. The game held a float32, so recover that."""
    return Fraction(struct.unpack("f", struct.pack("f", value))[0])


def load_level(name: str, data: ModuleType, removed: dict[int, str] | None = None) -> Level:
    """`data` is a data/<level>.py module, or anything with `tiles`, `objects` and `level_scale`.

    `removed` maps objects which are to be left out of the level altogether to the reason why.
    Only gaps/filters/levels/<level>.py can ask for that, and each one is recorded among the
    skipped objects.
    """
    scale = snap_to_float32(data.level_scale)
    tiles = {addr: _load_tile(addr, raw, scale) for addr, raw in data.tiles.items()}
    level = Level(name=name, scale=scale, tiles=tiles, objects={})

    _add_tile_walls(level)
    for addr, raw in data.objects.items():
        if removed and addr in removed:
            level.skipped_objects.append((addr, raw["type"], removed[addr]))
        else:
            _add_object(level, addr, raw)
    return level


def _load_tile(addr: int, raw: dict, scale: Fraction) -> Tile:
    points: list[Point] = []
    for x, z in raw["points"]:
        scaled = (x * float(scale), z * float(scale))
        rounded = (round(scaled[0]), round(scaled[1]))
        if max(abs(scaled[0] - rounded[0]), abs(scaled[1] - rounded[1])) > 1e-6:
            raise ValueError(f"tile {addr:#x} has a corner which is not an integer once scaled")
        points.append(rounded)

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
        heights=list(raw["heights"]),
        links=list(raw["links"]),
        box=bounding_box(points),
        is_vertical=(doubled_area == 0),
    )


def _add_tile_walls(level: Level) -> None:
    for tile in level.tiles.values():
        for i, neighbour in enumerate(tile.links):
            a, b = tile.edge(i)
            if neighbour != 0 or a == b:
                continue  # a == b is the end of a vertical tile, which has no length from above
            segment = BoundarySegment(
                id=len(level.segments),
                a=a,
                b=b,
                tile=tile.addr,
                edge_index=i,
            )
            level.segments.append(segment)
            level._tile_segments.setdefault(tile.addr, []).append(segment)


def _add_object(level: Level, addr: int, raw: dict) -> None:
    if raw["type"] in NON_BLOCKING_TYPES or raw.get("collectible"):
        level.skipped_objects.append((addr, raw["type"], "Bond walks through it"))
        return
    if not raw.get("points"):
        level.skipped_objects.append((addr, raw["type"], "no collision outline in the data"))
        return

    points: list[Point] = []
    for x, z in raw["points"]:
        point = (Fraction(x) * level.scale, Fraction(z) * level.scale)
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
        scale=float(level.scale),
        box=box,
        anchor_tile=raw["tile"],
        health=raw.get("health", 0),
        height_range=raw.get("height_range"),
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
    height_range = raw.get("height_range")
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
