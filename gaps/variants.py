"""Brings together gaps which are really the same warp.

A slot with two tight spots in it gives two gaps, since their pinch lines are too far apart to be
grouped, yet one step gets Bond past both. So: two gaps are the same warp if the step found for one
passes through a pinch line of the other. Gaps joined in this way, directly or through others,
form one warp. The gap with the shortest step is the main one and the rest are its variants.

A step is also proof for any gap it passes through which found no warp of its own: a slot with
three tight spots along it may only find a step from the middle one, as the search from the end
ones doesn't reach far enough. Such a gap becomes a variant too, and is given the step which proves
it, along with the status that goes with that step.

Variants stay in the survey. They are logged in variants.csv, and left off the maps unless asked
for. Filters must be applied first: a filtered gap is neither a main warp nor a variant.
"""

from gaps.exact import bounding_box, contact_interval, grow_box
from gaps.mesh import Level
from gaps.pinch import Pinch
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

    # Gaps with no warp of their own which some warp's step passes through
    for gap in gaps:
        if gap.witness is not None or gap.filtered_by is not None:
            continue
        for warp in sorted(warps, key=lambda warp: (warp.witness.step2, warp.key)):
            crossed = _pinch_crossed_by(level, warp, gap)
            if crossed is not None:
                _give_the_step(gap, warp, crossed)
                gap.variant_of = warp.variant_of or warp.key
                break


def _give_the_step(gap: Gap, warp: Gap, through: Pinch) -> None:
    """The step found for `warp` passes through `gap` as well, so it is a warp too, by that step."""
    gap.pinch = through
    gap.witness = warp.witness
    gap.status = warp.status
    gap.blockers = list(warp.blockers)
    gap.walk_round = warp.walk_round


def _step_passes_through(level: Level, stepping: Gap, other: Gap) -> bool:
    """Whether the step found for one gap crosses a pinch line of the other, on the same sheet."""
    return _pinch_crossed_by(level, stepping, other) is not None


def _pinch_crossed_by(level: Level, stepping: Gap, other: Gap) -> Pinch | None:
    """The first pinch of `other` whose line the step found for `stepping` crosses, on the same
    sheet. None if the step crosses none of them."""
    p, q = stepping.witness.p, stepping.witness.q
    nearby = level.linked_tiles_within(
        stepping.pinch.start_tile, grow_box(bounding_box([p, q]), level.bond_radius)
    )
    for pinch in other.pinches:
        if pinch.start_tile in nearby and contact_interval(p, q, pinch.a, pinch.b) is not None:
            return pinch
    return None
