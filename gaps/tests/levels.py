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
    heights: dict[str, float] | None = None,
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
            "heights": [(heights or {}).get(name, FLOOR)] * len(points),
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


def two_rooms(corridor_width: int, riser: bool = False, corridor_length: int = 40) -> Level:
    """Two 300 x 300 rooms joined by a corridor, 40 long unless told otherwise. With `riser`, a
    vertical tile (one with no area from above, like the face of a step) sits across the middle of
    the corridor."""
    low, high = 150 - corridor_width // 2, 150 - corridor_width // 2 + corridor_width
    middle, far = 300 + corridor_length // 2, 300 + corridor_length
    tiles = {
        "left room": [(0, 0), (0, 300), (300, 300), (300, high), (300, low), (300, 0)],
        "right room": [
            (far, 0),
            (far, low),
            (far, high),
            (far, 300),
            (far + 300, 300),
            (far + 300, 0),
        ],
    }
    if riser:
        tiles["corridor, near half"] = [(300, low), (300, high), (middle, high), (middle, low)]
        tiles["riser"] = [(middle, low), (middle, high), (middle, high), (middle, low)]
        tiles["corridor, far half"] = [(middle, low), (middle, high), (far, high), (far, low)]
    else:
        tiles["corridor"] = [(300, low), (300, high), (far, high), (far, low)]
    return build(tiles)


def notched_room(
    length: int,
    notch_from: int,
    notch_to: int,
    clearance: int,
    pieces: int = 1,
    left_end: int | None = None,
) -> Level:
    """A room `length` long and 400 deep whose far wall has a notch cut down into it, stopping
    `clearance` short of the near wall, which is straight and lies along z = 0. The notch comes to
    a point if notch_from equals notch_to, and otherwise has a flat end parallel to the near wall.
    With `pieces`, the near wall is made of that many pieces end to end, still in one line.

    Normally both ends of the near wall are corners of the room. With `left_end`, the floor carries
    on for 3 m beyond the left end, and the wall there turns through a right angle for that many
    centimetres first: upwards into the room if positive, so that it juts out, and downwards away
    from it if negative, which makes the end of the near wall an outside corner."""
    near_wall = [(length - i * length // pieces, 0) for i in range(pieces)]
    middle = (notch_from + notch_to) // 2
    notch = [(middle - 50, 400), (notch_from, clearance), (notch_to, clearance), (middle + 50, 400)]
    if notch_from == notch_to:
        notch.pop(1)
    if left_end is None:
        left = [(0, 0), (0, 400)]
    else:
        left = [(0, 0), (0, left_end), (-300, left_end), (-300, 400)]
    return build({"room": [*left, *notch, (length, 400), *near_wall]})


def room_with_a_slot(slot_width: int, slot_length: int, widens_to: int | None = None) -> Level:
    """A 300 x 300 room with a dead-end slot leading off the middle of its right hand wall. With
    `widens_to`, the slot opens out into a chamber of that width at its far end."""
    low, high = 150 - slot_width // 2, 150 - slot_width // 2 + slot_width
    far = 300 + slot_length
    tiles = {
        "room": [(0, 0), (0, 300), (300, 300), (300, high), (300, low), (300, 0)],
        "slot": [(300, low), (300, high), (far, high), (far, low)],
    }
    if widens_to is not None:
        c_low, c_high = 150 - widens_to // 2, 150 + widens_to // 2
        end = far + 100
        tiles["chamber"] = [
            (far, c_low), (far, low), (far, high), (far, c_high), (end, c_high), (end, c_low)
        ]  # fmt: skip
    return build(tiles)
