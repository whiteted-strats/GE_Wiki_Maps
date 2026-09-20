"""Brings together gaps which are really the same warp.

A slot with two tight spots in it gives two gaps, since their pinch lines are too far apart to be
grouped, yet one step gets Bond past both. So: two gaps are the same warp if the step found for one
passes through a pinch line of the other. Gaps joined in this way, directly or through others,
form one warp. The gap with the shortest step is the main one and the rest are its variants.

Variants stay in the survey. They are logged in variants.csv, and left off the maps unless asked
for. Filters must be applied first: a filtered gap is neither a main warp nor a variant.
"""

from gaps.exact import bounding_box, contact_interval, grow_box
from gaps.mesh import Level
from gaps.survey import Gap


def mark_variants(level: Level, gaps: list[Gap]) -> None:
    """Sets `variant_of` on every gap which is a variant, to the key of its main gap."""
    warps = [gap for gap in gaps if gap.witness is not None and gap.filtered_by is None]
    group_of = {gap.key: gap.key for gap in warps}

    def find(key: str) -> str:
        while group_of[key] != key:
            key = group_of[key]
        return key

    for i, first in enumerate(warps):
        for second in warps[i + 1 :]:
            if _step_passes_through(level, first, second) or _step_passes_through(
                level, second, first
            ):
                group_of[find(second.key)] = find(first.key)

    groups: dict[str, list[Gap]] = {}
    for gap in warps:
        groups.setdefault(find(gap.key), []).append(gap)
    for gap in gaps:
        gap.variant_of = ""
    for members in groups.values():
        main = min(members, key=lambda gap: (gap.witness.step2, gap.key))
        for gap in members:
            if gap is not main:
                gap.variant_of = main.key


def _step_passes_through(level: Level, stepping: Gap, other: Gap) -> bool:
    """Whether the step found for one gap crosses a pinch line of the other, on the same sheet."""
    p, q = stepping.witness.p, stepping.witness.q
    nearby = level.linked_tiles_within(
        stepping.pinch.start_tile, grow_box(bounding_box([p, q]), level.bond_radius)
    )
    return any(
        pinch.start_tile in nearby and contact_interval(p, q, pinch.a, pinch.b) is not None
        for pinch in other.pinches
    )
