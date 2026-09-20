"""Tiny hand-made levels for the tests, in the same format as data/<level>.py.

They use a scale of 1, so that coordinates are centimetres and Bond's radius is 30.
"""

from types import SimpleNamespace

from gaps.exact import Point
from gaps.mesh import Level, load_level

FLOOR = 0.0


def build(
    tiles: dict[str, list[Point]],
    objects: dict[int, dict] | None = None,
    removed: dict[int, str] | None = None,
) -> Level:
    """Tiles are named, and are linked automatically wherever two of them share a whole edge.
    Listing a tile's name in `UNLINKED` style is not needed: give unlinked tiles different edges."""
    addresses = {name: 0x1000 + 0x100 * i for i, name in enumerate(tiles)}
    edge_owners: dict[frozenset, list[str]] = {}
    for name, points in tiles.items():
        for i in range(len(points)):
            edge = frozenset((points[i], points[(i + 1) % len(points)]))
            edge_owners.setdefault(edge, []).append(name)

    raw_tiles = {}
    for name, points in tiles.items():
        links = []
        for i in range(len(points)):
            owners = edge_owners[frozenset((points[i], points[(i + 1) % len(points)]))]
            others = [owner for owner in owners if owner != name]
            links.append(addresses[others[0]] if others else 0)
        raw_tiles[addresses[name]] = {
            "points": [(float(x), float(z)) for x, z in points],
            "heights": [FLOOR] * len(points),
            "room": 1,
            "links": links,
            "name": addresses[name],
        }

    data = SimpleNamespace(tiles=raw_tiles, objects=objects or {}, level_scale=1.0)
    return load_level("test", data, removed)


def crate(addr: int, tile_addr: int, x: float, z: float, size: float) -> dict:
    """A square object with its corner at (x, z), standing on the given tile."""
    outline = [(x, z), (x + size, z), (x + size, z + size), (x, z + size)]
    return {
        "type": "generic",
        "preset": addr,
        "points": outline,
        "collectible": False,
        "tile": tile_addr,
        "height_range": (FLOOR, FLOOR + 100),
        "health": 1000,
    }


def two_rooms(corridor_width: int, riser: bool = False) -> Level:
    """Two 300 x 300 rooms joined by a corridor 40 long. With `riser`, a vertical tile (one with no
    area from above, like the face of a step) sits across the middle of the corridor."""
    low, high = 150 - corridor_width // 2, 150 - corridor_width // 2 + corridor_width
    tiles = {
        "left room": [(0, 0), (0, 300), (300, 300), (300, high), (300, low), (300, 0)],
        "right room": [(340, 0), (340, low), (340, high), (340, 300), (640, 300), (640, 0)],
    }
    if riser:
        tiles["corridor, near half"] = [(300, low), (300, high), (320, high), (320, low)]
        tiles["riser"] = [(320, low), (320, high), (320, high), (320, low)]
        tiles["corridor, far half"] = [(320, low), (320, high), (340, high), (340, low)]
    else:
        tiles["corridor"] = [(300, low), (300, high), (340, high), (340, low)]
    return build(tiles)


def notched_room(
    length: int, notch_from: int, notch_to: int, clearance: int, pieces: int = 1
) -> Level:
    """A room `length` long and 400 deep whose far wall has a notch cut down into it, stopping
    `clearance` short of the near wall, which is straight. The notch comes to a point if notch_from
    equals notch_to, and otherwise has a flat end parallel to the near wall. With `pieces`, the
    near wall is made of that many pieces end to end, still in one straight line."""
    near_wall = [(length - i * length // pieces, 0) for i in range(pieces)] + [(0, 0)]
    middle = (notch_from + notch_to) // 2
    notch = [(middle - 50, 400), (notch_from, clearance), (notch_to, clearance), (middle + 50, 400)]
    if notch_from == notch_to:
        notch.pop(1)
    return build({"room": [(0, 0), (0, 400), *notch, (length, 400), *near_wall[:-1]]})
