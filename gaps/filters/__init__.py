"""Filters: deciding which gaps are of no interest, openly.

Nothing is ever deleted. A filtered gap keeps everything that was found out about it, and gains a
`filtered_by` saying which filter caught it and why. The report lists them all in filtered.csv.

  generic.py      rules for every level, in code. They claim a warp is impossible.
  levels/*.py     per level: objects which are of no interest to the speedrun, as plain data
  predicates.py   the named tests which level files use to describe their objects
  config.py       the settings of the generic filters
"""

import importlib
from dataclasses import dataclass
from types import ModuleType

from gaps.filters.generic import GENERIC_FILTERS
from gaps.filters.groups import ObjectGroup, check_group
from gaps.mesh import Level, load_level
from gaps.survey import NO_WARP_FOUND, FilterVerdict, Gap


@dataclass
class Contradiction:
    """A generic filter said no warp is possible through a gap which has a certified warp. One of
    them is wrong, so the gap is kept and this is reported."""

    gap: Gap
    filter_name: str
    reason: str


def apply_filters(level: Level, gaps: list[Gap]) -> list[Contradiction]:
    groups = ignored_groups(level)
    for group in groups:
        check_group(level, group)

    contradictions = []
    for gap in gaps:
        gap.filtered_by = _ignored_object_verdict(gap, groups)
        if gap.filtered_by is not None:
            continue
        for name, pinch_filter in GENERIC_FILTERS.items():
            reasons = [pinch_filter(level, pinch) for pinch in gap.pinches]
            if not all(reasons):
                continue
            if gap.status == NO_WARP_FOUND:
                gap.filtered_by = FilterVerdict(name, reasons[0])
            else:
                contradictions.append(Contradiction(gap, name, reasons[0]))
            break
    return contradictions


def ignored_groups(level: Level) -> list[ObjectGroup]:
    return _groups_in_level_file(level.name, "IGNORE_OBJECTS")


def objects_to_remove(name: str, data: ModuleType) -> dict[int, str]:
    """The objects which gaps/filters/levels/<level>.py says to leave out of the level, each with
    the reason. The groups are checked against the level as dumped, with everything still in it."""
    groups = _groups_in_level_file(name, "REMOVE_OBJECTS")
    if not groups:
        return {}
    level_as_dumped = load_level(name, data)
    removed = {}
    for group in groups:
        check_group(level_as_dumped, group)
        for addr in group.objects:
            removed[addr] = f'removed by filters/levels/{name}.py, "{group.name}": {group.reason}'
    return removed


def _groups_in_level_file(name: str, list_name: str) -> list[ObjectGroup]:
    """One of the lists in gaps/filters/levels/<level>.py. Empty if there is no file or no list."""
    try:
        module = importlib.import_module(f"gaps.filters.levels.{name}")
    except ModuleNotFoundError:
        return []
    return getattr(module, list_name, [])


def _ignored_object_verdict(gap: Gap, groups: list[ObjectGroup]) -> FilterVerdict | None:
    """A gap is filtered if every one of its pinches is formed by at least one object of an ignored
    group. (A future option, say to ignore only gaps between two objects of the group, would be a
    setting on ObjectGroup which is consulted here.)"""
    for group in groups:
        ignored_in_each_pinch = [pinch.needs & set(group.objects) for pinch in gap.pinches]
        if all(ignored_in_each_pinch):
            which = ", ".join(f"{obj:#x}" for obj in sorted(set().union(*ignored_in_each_pinch)))
            return FilterVerdict(f"ignored objects: {group.name}", f"{group.reason} ({which})")
    return None
