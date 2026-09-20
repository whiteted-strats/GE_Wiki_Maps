"""Loads a level from data/<level>.py into exact coordinates.

Units. The game stores tile corners as integers, and the dumper divided them by the level's scale.
Multiplying by the scale again recovers those integers exactly, so everything in this package works
in that integer space ("scaled units"). Object outlines have been rotated by the game so they are
not integers, but they are exact float32 values and so convert to Fractions without any loss.
`Level.to_world` converts a scaled length back to the units used everywhere else in this repo,
where Bond's radius is 30.

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

from gaps.exact import Num, Point, bounding_box, boxes_overlap, grow_box

Box = tuple[Num, Num, Num, Num]

BOND_RADIUS_WORLD = 30
BOND_HEIGHT_WORLD = Fraction(1673, 10)  # as lib/misc.py

# Objects which Bond walks through: pick-ups, and the locks which sit on doors
NON_BLOCKING_TYPES = {"weapon", "ammo", "body_armour", "key", "lock"}


@dataclass
class Tile:
    addr: int
    name: int
    room: int
    points: list[Point]  # integers, in scaled units
    heights: list[float]  # world units, one per point
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
    box: Box
    anchor_tile: int  # the tile the game says it stands on
    sheet_tiles: frozenset[int] = frozenset()  # the tiles it stands among, see Level._place_objects
    height_suspect: bool = False  # its height range doesn't overlap Bond standing on its tile

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
    skipped_objects: list[tuple[int, str]] = field(default_factory=list)  # (addr, reason)
    _tile_segments: dict[int, list[BoundarySegment]] = field(default_factory=dict)
    _object_segments: dict[int, list[BoundarySegment]] = field(default_factory=dict)
    _objects_on_tile: dict[int, list[int]] = field(default_factory=dict)

    @property
    def bond_radius(self) -> Fraction:
        return BOND_RADIUS_WORLD * self.scale

    def to_world(self, scaled_length: Num) -> float:
        return float(scaled_length / self.scale)

    def to_world_point(self, p: Point) -> tuple[float, float]:
        return (self.to_world(p[0]), self.to_world(p[1]))

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


def snap_to_float32(value: float) -> Fraction:
    """The data files print the scale to 14 digits. The game held a float32, so recover that."""
    return Fraction(struct.unpack("f", struct.pack("f", value))[0])


def load_level(name: str, data: ModuleType) -> Level:
    """`data` is a data/<level>.py module, or anything with `tiles`, `objects` and `level_scale`."""
    scale = snap_to_float32(data.level_scale)
    tiles = {addr: _load_tile(addr, raw, scale) for addr, raw in data.tiles.items()}
    level = Level(name=name, scale=scale, tiles=tiles, objects={})

    _add_tile_walls(level)
    for addr, raw in data.objects.items():
        _add_object(level, addr, raw)
    _place_objects(level, data.objects)
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
        level.skipped_objects.append((addr, "Bond walks through it"))
        return
    if not raw.get("points"):
        level.skipped_objects.append((addr, "no collision outline in the data"))
        return

    points: list[Point] = []
    for x, z in raw["points"]:
        point = (Fraction(x) * level.scale, Fraction(z) * level.scale)
        if not points or point != points[-1]:
            points.append(point)
    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    if len(points) < 2:
        level.skipped_objects.append((addr, "collision outline is a single point"))
        return
    if raw.get("tile") not in level.tiles:
        # Without its tile there is no telling which floor it is on, so it can't take part
        level.skipped_objects.append((addr, "the tile it stands on is not in the data"))
        return

    level.objects[addr] = LevelObject(
        addr=addr,
        type=raw["type"],
        preset=raw["preset"],
        points=points,
        box=bounding_box(points),
        anchor_tile=raw["tile"],
    )
    sides = []
    for i in range(len(points)):
        a, b = points[i], points[(i + 1) % len(points)]
        if len(points) == 2 and i == 1:
            break  # a two point outline is one side, not two
        segment = BoundarySegment(id=len(level.segments), a=a, b=b, obj=addr)
        level.segments.append(segment)
        sides.append(segment)
    level._object_segments[addr] = sides


def _place_objects(level: Level, raw_objects: dict) -> None:
    """Works out which tiles each object stands among.

    The game gives one tile per object. Outlines usually spill over that tile's edges, so we spread
    out from it through links, as far as the object's outline (plus Bond's diameter) reaches. That
    keeps an object on its own floor.
    """
    reach = 2 * level.bond_radius
    for obj in level.objects.values():
        obj.sheet_tiles = frozenset(
            level.linked_tiles_within(obj.anchor_tile, grow_box(obj.box, reach))
        )
        for tile in obj.sheet_tiles:
            level._objects_on_tile.setdefault(tile, []).append(obj.addr)
        obj.height_suspect = _height_is_suspect(level, obj, raw_objects[obj.addr])


def _height_is_suspect(level: Level, obj: LevelObject, raw: dict) -> bool:
    """The dumped height range is known to be nonsense for some doors, so this is only a flag."""
    height_range = raw.get("height_range")
    if not height_range:
        return False
    floor = level.tiles[obj.anchor_tile].heights
    bond_low, bond_high = min(floor), max(floor) + float(BOND_HEIGHT_WORLD)
    return not (min(height_range) <= bond_high and max(height_range) >= bond_low)


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
