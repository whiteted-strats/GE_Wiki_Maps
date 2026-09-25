"""Runs the whole survey of one level: pinches, grouped into gaps, each with its best warp.

A gap usually shows up as several pinches (a corridor is bounded by many short wall pieces, and
object outlines contain tiny near-duplicate sides), so pinches whose lines are within Bond's radius
of each other are grouped. Each gap is then reported once, by its easiest warp.
"""

import importlib
import pickle
from dataclasses import dataclass, field
from pathlib import Path

from gaps.detour import walking_distance
from gaps.exact import bounding_box, contact_interval, dist2_point_segment, grow_box
from gaps.mesh import Level, load_level
from gaps.pinch import Decision, Pinch, TouchingWalls, feature_key, find_pinches
from gaps.sheet import ObjectsPresent, walls_near
from gaps.witness import Witness, find_witness

# Saved surveys are only reused if they were made with this format. Add one whenever a change to
# the code means that old surveys would be wrong or would no longer load.
SURVEY_FORMAT = 10

# What was found at a gap
WARP = "warp"  # a warp exists with the level exactly as dumped
WARP_IF_REMOVED = "warp if objects removed"  # only once the `blockers` are destroyed or moved
NO_WARP_FOUND = "no warp found"  # the search found none. This is not proof that there is none.


@dataclass
class FilterVerdict:
    """Which filter decided that a gap is of no interest, and why. See gaps/filters."""

    filter_name: str
    reason: str


@dataclass
class Gap:
    id: int  # its number in the report. This changes whenever the ranking does.
    pinches: list[Pinch]
    key: str = ""  # names the two walls of its narrowest pinch, so it stays the same between runs
    name: str = ""  # if it is a known warp, see gaps/known_warps
    variant_of: str = ""  # the key of its main gap, if it is a variant: see gaps/variants.py
    status: str = NO_WARP_FOUND
    pinch: Pinch | None = None  # the pinch which the reported warp goes through
    witness: Witness | None = None
    blockers: list[int] = field(default_factory=list)  # objects in the way, as dumped
    walk_round: float | None = None  # centimetres. None: no walk found nearby (approximate)
    filtered_by: FilterVerdict | None = None
    suppressed_by: FilterVerdict | None = None  # a real warp, hidden: see filters/suppressed.py

    @property
    def narrowest(self) -> Pinch:
        return min(self.pinches, key=lambda pinch: pinch.width2)

    @property
    def needs(self) -> frozenset[int]:
        """The objects which form the gap. Destroying one of them removes the gap."""
        return (self.pinch or self.narrowest).needs


@dataclass
class Survey:
    level: Level
    gaps: list[Gap]
    touching: list[TouchingWalls]
    decisions: list[Decision]
    removed: dict[int, str] = field(default_factory=dict)  # objects left out, and why
    format: int = SURVEY_FORMAT


def survey_level(name: str, removed: dict[int, str] | None = None) -> Survey:
    """`removed`: objects to leave out of the level, see gaps.filters.objects_to_remove."""
    removed = removed or {}
    level = load_level(name, importlib.import_module(f"data.{name}"), removed)
    pinches, touching, decisions = find_pinches(level)
    gaps = [Gap(id=i, pinches=group) for i, group in enumerate(_group_pinches(level, pinches))]
    for gap in gaps:
        narrowest = gap.narrowest
        gap.key = " | ".join(
            sorted(feature_key(level, wall) for wall in (narrowest.first, narrowest.second))
        )
        _find_best_warp(level, gap)
    return Survey(level, gaps, touching, decisions, removed)


def save_survey(survey: Survey, path: Path) -> None:
    """Surveying takes a minute or so per level, and filtering and drawing don't need it redone."""
    path.parent.mkdir(parents=True, exist_ok=True)
    survey.level.forget_caches()
    with path.open("wb") as file:
        pickle.dump(survey, file)


def load_survey(path: Path) -> Survey | None:
    """None if there is no saved survey, or it was saved by an older version of this code."""
    if not path.exists():
        return None
    with path.open("rb") as file:
        survey = pickle.load(file)
    # Looked up on the object itself: a survey saved before there were formats has no such entry,
    # and would otherwise pick up the default from the class
    return survey if vars(survey).get("format") == SURVEY_FORMAT else None


def _group_pinches(level: Level, pinches: list[Pinch]) -> list[list[Pinch]]:
    """Pinches belong to the same gap if their lines come within Bond's radius of each other, on
    the same sheet. Groups are built by joining up any two pinches which do."""
    radius2 = level.bond_radius**2
    group_of = list(range(len(pinches)))

    def find(i: int) -> int:
        while group_of[i] != i:
            i = group_of[i]
        return i

    for i, first in enumerate(pinches):
        nearby_tiles = level.linked_tiles_within(
            first.start_tile, grow_box(bounding_box([first.a, first.b]), level.bond_radius)
        )
        for j in range(i + 1, len(pinches)):
            second = pinches[j]
            if second.start_tile not in nearby_tiles:
                continue
            if dist2_point_segment(second.midpoint, first.a, first.b) < radius2:
                group_of[find(j)] = find(i)

    groups: dict[int, list[Pinch]] = {}
    for i, pinch in enumerate(pinches):
        groups.setdefault(find(i), []).append(pinch)
    return sorted(groups.values(), key=lambda group: min(pinch.width2 for pinch in group))


def _find_best_warp(level: Level, gap: Gap) -> None:
    """Tries the level as dumped first. Failing that, tries with every object removed except those
    which form the gap, and works out which objects were in the way."""
    for status, everything_present in ((WARP, True), (WARP_IF_REMOVED, False)):
        found = []
        for pinch in gap.pinches:
            present: ObjectsPresent = None if everything_present else pinch.needs
            witness = find_witness(level, pinch, present)
            if witness is not None:
                found.append((witness.step2, pinch, witness, present))
        if found:
            _, gap.pinch, gap.witness, present = min(found, key=lambda entry: entry[0])
            gap.status = status
            gap.walk_round = walking_distance(level, gap.pinch, gap.witness, present)
            if not everything_present:
                gap.blockers = _objects_in_the_way(level, gap.pinch, gap.witness)
            return


def _objects_in_the_way(level: Level, pinch: Pinch, witness: Witness) -> list[int]:
    """The objects which stop this warp working in the level as dumped: those which Bond would
    overlap at either end, or which the step passes through."""
    radius = level.bond_radius
    region = grow_box(bounding_box([witness.p, witness.q]), radius)
    in_the_way = set()
    for wall in walls_near(level, pinch.start_tile, region, present=None):
        if wall.obj is None or wall.obj in pinch.needs:
            continue
        overlaps_bond = any(
            dist2_point_segment(end, wall.a, wall.b) < radius * radius
            for end in (witness.p, witness.q)
        )
        crosses_step = contact_interval(witness.p, witness.q, wall.a, wall.b) is not None
        if overlaps_bond or crosses_step:
            in_the_way.add(wall.obj)
    return sorted(in_the_way)
