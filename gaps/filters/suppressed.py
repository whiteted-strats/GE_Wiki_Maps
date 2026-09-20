"""Suppressed warps: real warps which aren't worth telling anyone about, hidden one at a time.

This is a different thing from the generic filters, which claim that no warp is possible and may
only remove gaps where none was found. A suppressed warp exists. It is hidden because someone has
decided it is of no interest, usually because it is obvious: a big gap beside a crate which anyone
looking at the map would see. So each one is an entry in the level's file with a reason, and with
checks that it is the simple thing it is said to be:

  - its status, its width (exact) and its step (an upper bound, as for known warps)
  - the complete list of objects within NEARBY_M of its pinch line, each by address and with the
    predicates it is expected to pass. If anything else is near, it isn't as simple as claimed.

"Near" is measured from the pinch line rather than from the ends of the step, because the pinch is
exact geometry while the step comes from a search. Any failed check stops the run.

Suppressed warps are listed in suppressed.csv with their reasons, drawn faintly on the overviews,
and given close-ups by --review.
"""

from dataclasses import dataclass, field

from gaps.exact import bounding_box, closest_points_between_segments, grow_box
from gaps.filters.groups import FilterFileError
from gaps.filters.predicates import Predicate
from gaps.known_warps import normalise_walls, pinch_keys
from gaps.mesh import Level
from gaps.pinch import Pinch
from gaps.survey import FilterVerdict, Gap

NEARBY_M = 2.0


@dataclass
class NearbyObject:
    addr: int
    all: list[Predicate] = field(default_factory=list)  # it passes every one of these


@dataclass
class SuppressedWarp:
    reason: str
    walls: str  # the keys of the two walls of one of its pinches, as in the key column of gaps.csv
    status: str
    width_cm: float
    step_cm: float  # an upper bound: a warp at most this long must still be found
    nearby: list[NearbyObject]  # every object within NEARBY_M of its pinch line, and no others


def apply_suppressions(level: Level, gaps: list[Gap], wanted: list[SuppressedWarp]) -> None:
    """Sets `suppressed_by` on each warp listed. Filters must already have been applied and
    variants marked: an entry which names a variant suppresses the main warp it belongs to."""
    by_key = {gap.key: gap for gap in gaps}
    for gap in gaps:
        gap.suppressed_by = None

    for entry in wanted:

        def fail(problem: str, entry: SuppressedWarp = entry) -> None:
            raise FilterFileError(f"{level.name}, suppressed warp {entry.walls}: {problem}")

        matches = [gap for gap in gaps if normalise_walls(entry.walls) in pinch_keys(level, gap)]
        if len(matches) != 1:
            fail(f"{len(matches)} gaps have a pinch between those walls")
        gap = by_key[matches[0].variant_of or matches[0].key]
        if gap.filtered_by is not None:
            fail(f'it is already filtered out by "{gap.filtered_by.filter_name}"')
        if gap.witness is None or gap.status != entry.status:
            fail(f"its status is {gap.status!r}, not {entry.status!r}")

        width_cm = round(level.to_cm(float(gap.pinch.width2) ** 0.5), 3)
        if width_cm != entry.width_cm:
            fail(f"its width is {width_cm} cm, not {entry.width_cm} cm")
        step_cm = round(level.to_cm(float(gap.witness.step2) ** 0.5), 2)
        if step_cm > entry.step_cm:
            fail(f"the shortest step found is {step_cm} cm, longer than {entry.step_cm} cm")

        near = objects_near(level, gap.pinch)
        listed = {nearby.addr for nearby in entry.nearby}
        if near != listed:
            unlisted = ", ".join(f"{addr:#x}" for addr in sorted(near - listed)) or "none"
            absent = ", ".join(f"{addr:#x}" for addr in sorted(listed - near)) or "none"
            fail(
                f"the objects within {NEARBY_M} m are not those listed "
                f"(near but not listed: {unlisted}; listed but not near: {absent})"
            )
        for nearby in entry.nearby:
            for test in nearby.all:
                if not test(level.objects[nearby.addr]):
                    fail(f"object {nearby.addr:#x} fails {test.__name__}")

        gap.suppressed_by = FilterVerdict("suppressed", entry.reason)


def objects_near(level: Level, pinch: Pinch) -> set[int]:
    """The objects any part of whose outline is within NEARBY_M of the pinch line, on its sheet."""
    reach = level.from_metres(NEARBY_M)
    region = grow_box(bounding_box([pinch.a, pinch.b]), reach)
    tiles = level.linked_tiles_within(pinch.start_tile, region)
    near = set()
    for obj in level.objects_among_tiles(tiles):
        for side in level.sides_of_object(obj):
            apart2, _, _ = closest_points_between_segments(pinch.a, pinch.b, side.a, side.b)
            if apart2 <= reach * reach:
                near.add(obj)
                break
    return near
