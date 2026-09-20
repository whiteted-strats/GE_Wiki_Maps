"""Aids for checking our own work. None of this takes part in the survey or decides anything.

`python -m gaps <levels> --review` writes, for every level together, under output/00_debug/:

  filter_review/      a close-up of every gap which a filter removed, to check the filters
  overhead_objects/   a close-up of every object which is well above the tile it is attached to,
                      and a table of them per level. This is how Frigate's floating doors were
                      found. It only points objects out: leaving one out of a level takes an entry
                      in REMOVE_OBJECTS in gaps/filters/levels/<level>.py
"""

import csv
import importlib
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt

from gaps import report
from gaps.filters.predicates import is_overhead
from gaps.mesh import Level, LevelObject, load_level
from gaps.survey import Gap, Survey

DEBUG_ROOT = Path("output/00_debug")


def write_review(survey: Survey) -> None:
    """Filters must already have been applied to the survey's gaps."""
    filtered = [gap for gap in survey.gaps if gap.filtered_by is not None]
    _draw_filtered_for_review(survey.level, filtered, DEBUG_ROOT / "filter_review")

    overhead = _overhead_objects(survey)
    folder = DEBUG_ROOT / "overhead_objects"
    folder.mkdir(parents=True, exist_ok=True)
    _write_overhead_objects(overhead, folder / f"{survey.level.name}.csv")
    _draw_overhead_for_review(survey, overhead, folder)


def _draw_filtered_for_review(level: Level, filtered: list[Gap], folder: Path) -> None:
    """Close-ups of the gaps which filters removed, for checking that a filter does what was meant.
    Every level's go into the one folder, named by level and then filter so that they sort into
    a filter's work on each level: frigate_anvil-and-hammer_003.svg."""
    folder.mkdir(parents=True, exist_ok=True)
    for old_image in folder.glob(f"{level.name}_*.svg"):
        old_image.unlink()
    numbers: Counter = Counter()
    for gap in filtered:
        filter_name = re.sub(r"[^a-z0-9]+", "-", gap.filtered_by.filter_name.lower()).strip("-")
        numbers[filter_name] += 1
        name = f"{level.name}_{filter_name}_{numbers[filter_name]:03d}.svg"
        report.draw_close_up(level, gap, folder / name)


@dataclass
class OverheadObject:
    """An object which passes the is_overhead predicate, with what is worth knowing about it."""

    obj: LevelObject  # as it is in the level as dumped, whether or not it was then removed
    room: int
    removed: bool
    gaps: list[Gap]  # the gaps which it helps to form, if it is still in the level


def _overhead_objects(survey: Survey) -> list[OverheadObject]:
    name = survey.level.name
    as_dumped = load_level(name, importlib.import_module(f"data.{name}"))
    overhead = []
    for obj in as_dumped.objects.values():
        if not is_overhead(obj):
            continue
        forms = [
            gap for gap in survey.gaps if any(obj.addr in pinch.needs for pinch in gap.pinches)
        ]
        room = as_dumped.room_of_object(obj.addr)
        overhead.append(OverheadObject(obj, room, obj.addr in survey.removed, forms))
    return sorted(overhead, key=lambda entry: -entry.obj.floor_clearance)


def _write_overhead_objects(overhead: list[OverheadObject], path: Path) -> None:
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["object", "type", "room", "bottom_above_floor_m", "height_m", "in_the_level", "forms"]
        )
        for entry in overhead:
            low, high = min(entry.obj.height_range), max(entry.obj.height_range)
            writer.writerow(
                [
                    f"{entry.obj.addr:#x}",
                    entry.obj.type,
                    f"{entry.room:#04x}",
                    f"{entry.obj.floor_clearance / 100:.2f}",
                    f"{(high - low) / 100:.2f}",
                    "removed" if entry.removed else "yes, as a wall",
                    " ; ".join(gap.key for gap in entry.gaps),
                ]
            )


def _draw_overhead_for_review(survey: Survey, overhead: list[OverheadObject], folder: Path) -> None:
    """A close-up of each object which is well above its floor, for deciding whether it really is
    out of Bond's way and should be listed in REMOVE_OBJECTS. The object is drawn in magenta, on
    the level as it was surveyed, with any gaps it forms. Named by level, type, address and how
    high it is: frigate_door_0x1ebdc0_3.42m.svg."""
    level = survey.level
    folder.mkdir(parents=True, exist_ok=True)
    for old_image in folder.glob(f"{level.name}_*.svg"):
        old_image.unlink()

    for entry in overhead:
        obj = entry.obj
        x = level.to_cm((obj.box[0] + obj.box[1]) / 2)
        z = level.to_cm((obj.box[2] + obj.box[3]) / 2)
        half = report.CLOSE_UP_HALF_SIZE_CM
        region = tuple(v * float(level.scale) for v in (x - half, x + half, z - half, z + half))

        fig, ax = plt.subplots(figsize=(9, 9))
        report.draw_level(ax, level, level.linked_tiles_within(obj.anchor_tile, region), True)
        for gap in entry.gaps:
            report.draw_gap(ax, level, gap, prominent=True, numbered=True)
        xs, zs = report.flipped(level, [*obj.points, obj.points[0]])
        ax.plot(xs, zs, color="magenta", linewidth=2.0, zorder=8)

        clearance_m = obj.floor_clearance / 100
        low, high = min(obj.height_range), max(obj.height_range)
        state = "REMOVED from the level" if entry.removed else "in the level, as a wall"
        ax.set_title(
            f"{level.name} {obj.type} {obj.addr:#x} in room {entry.room:#04x}: {state}\n"
            f"its bottom is {clearance_m:.2f} m above the top of the tile it is attached to "
            f"(it spans {low:.0f} to {high:.0f} cm)\n"
            f"gaps it forms: {', '.join(gap.key for gap in entry.gaps) or 'none'}",
            fontsize=9,
        )
        ax.set_xlim(-x - half, -x + half)
        ax.set_ylim(z - half, z + half)
        name = f"{level.name}_{obj.type}_{obj.addr:#x}_{clearance_m:.2f}m.svg"
        report.finish(fig, ax, folder / name)
