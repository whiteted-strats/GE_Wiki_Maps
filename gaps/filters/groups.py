"""What the level files are written with: a group of objects, and what is expected of it.

A level file can hold two lists of groups:

  IGNORE_OBJECTS  objects of no interest to the speedrun. Gaps they form are filtered out. They are
                  still there, and still get in the way of other warps.
  REMOVE_OBJECTS  objects which are not really there, such as Frigate's doors which hang in the air
                  above the room they are attached to. They are left out of the level before it is
                  surveyed, as if they didn't exist. This is the stronger of the two by far, since
                  it changes what is found, so every one of them is listed in removed_objects.csv.

The expectations repeat what the list of objects already implies, on purpose. If an ID is mistyped,
or the level is dumped again and objects are numbered differently, the checks fail and the run
stops, rather than quietly ignoring the wrong things.
"""

from dataclasses import dataclass, field
from itertools import combinations

from gaps.exact import dist2
from gaps.filters.predicates import Predicate
from gaps.mesh import Level, LevelObject


class FilterFileError(Exception):
    """A level's filter file doesn't match the level."""


@dataclass
class Expect:
    count: int
    room: int | None = None  # every object stands on a tile of this room
    all: list[Predicate] = field(default_factory=list)  # every object passes every one of these
    # no two objects are further apart than this, centre to centre
    max_spread_m: float | None = None
    # the bottom of every object is at least this far above the top of the tile it is attached to
    min_floor_clearance_m: float | None = None
    # the area of every object's outline, seen from above, is within this range: (least, most)
    footprint_m2: tuple[float, float] | None = None


@dataclass
class ObjectGroup:
    """Objects of no interest to the speedrun. Any gap which one of them helps to form is filtered,
    whether it is between two of them or between one of them and something else."""

    name: str
    reason: str
    objects: list[int]
    expect: Expect


def check_group(level: Level, group: ObjectGroup) -> None:
    def fail(problem: str) -> None:
        raise FilterFileError(f'{level.name}, group "{group.name}": {problem}')

    if len(set(group.objects)) != len(group.objects):
        fail("an object is listed twice")
    if len(group.objects) != group.expect.count:
        fail(f"{len(group.objects)} objects are listed but {group.expect.count} are expected")

    for addr in group.objects:
        if addr not in level.objects:
            fail(f"there is no object {addr:#x} (or it has no collision outline)")
        room = level.room_of_object(addr)
        if group.expect.room is not None and room != group.expect.room:
            fail(f"object {addr:#x} is in room {room:#04x}, not {group.expect.room:#04x}")
        for test in group.expect.all:
            if not test(level.objects[addr]):
                fail(f"object {addr:#x} fails {test.__name__}")
        if group.expect.min_floor_clearance_m is not None:
            clearance = level.objects[addr].floor_clearance
            if clearance is None or clearance < group.expect.min_floor_clearance_m * 100:
                found = "unknown" if clearance is None else f"{clearance / 100:.2f} m"
                fail(
                    f"object {addr:#x} is {found} above its floor, "
                    f"less than {group.expect.min_floor_clearance_m} m"
                )

    if group.expect.footprint_m2 is not None:
        least, most = group.expect.footprint_m2
        for addr in group.objects:
            area = footprint_m2(level.objects[addr])
            if not least <= area <= most:
                fail(f"object {addr:#x} covers {area:.2f} m2, which is not from {least} to {most}")

    if group.expect.max_spread_m is not None:
        limit2 = level.from_metres(group.expect.max_spread_m) ** 2
        for first, second in combinations(group.objects, 2):
            apart2 = dist2(_centre(level.objects[first]), _centre(level.objects[second]))
            if apart2 > limit2:
                apart_m = level.to_cm(float(apart2) ** 0.5) / 100
                fail(
                    f"objects {first:#x} and {second:#x} are {apart_m:.2f} m apart, "
                    f"more than {group.expect.max_spread_m} m"
                )


def footprint_m2(obj: LevelObject) -> float:
    """The area of the outline seen from above, in square metres."""
    points = obj.points
    doubled = sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )
    return abs(float(doubled)) / 2 / (obj.scale * 100) ** 2


def _centre(obj: LevelObject) -> tuple:
    count = len(obj.points)
    return (sum(p[0] for p in obj.points) / count, sum(p[1] for p in obj.points) / count)
