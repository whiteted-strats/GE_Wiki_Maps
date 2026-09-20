"""Writes a survey out as tables and maps, under output/gaps/<level>/.

  gaps.csv        one row per gap, easiest warps first
  decisions.csv   every pair of walls closer than Bond's diameter, and why it was kept or dismissed
  touching.csv    unrelated walls which touch (gaps of width zero)
  overview_*.png  each part of the level, with the gaps numbered and the walls involved highlighted
  gap_NNN.png     a close-up of each gap

and output/gaps/summary.csv, which lists the warps of every surveyed level together.

The maps are deliberately plain: tiles, walls and object outlines only. As on the other maps in
this repo, x is flipped so that they match the game's orientation.
"""

import csv
import importlib
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from gaps.mesh import BoundarySegment, Level
from gaps.pinch import describe
from gaps.survey import NO_WARP_FOUND, WARP, WARP_IF_REMOVED, Gap, Survey
from lib.seperate_tile_groups import seperateGroups

HAIRLINE_WIDTH_WORLD = 1  # narrower gaps (closed doors in their frames) get no number or close-up
CLOSE_UP_HALF_SIZE_WORLD = 260
OVERVIEW_TARGET_PIXELS = 4000  # along the longer side, as long as the scale stays within ...
OVERVIEW_PIXELS_PER_UNIT = (0.5, 2.0)
OVERVIEW_DPI = 100
STATUS_COLOUR = {WARP: "red", WARP_IF_REMOVED: "darkviolet", NO_WARP_FOUND: "royalblue"}
TILE_COLOUR = (0.86, 0.86, 0.86)
WALL_COLOUR = (0.25, 0.25, 0.25)
OBJECT_COLOUR = "darkorange"


def write_report(survey: Survey, output_root: Path = Path("output/gaps")) -> Path:
    folder = output_root / survey.level.name
    folder.mkdir(parents=True, exist_ok=True)
    for old_image in folder.glob("*.png"):
        old_image.unlink()

    gaps = sorted(survey.gaps, key=lambda gap: _ranking(survey.level, gap))
    for number, gap in enumerate(gaps, start=1):
        gap.id = number  # number them in the order they are listed

    _write_gap_table(survey.level, gaps, folder / "gaps.csv")
    _write_decisions(survey, folder / "decisions.csv")
    _write_touching(survey, folder / "touching.csv")
    _draw_overviews(survey.level, gaps, folder)
    for gap in gaps:
        if not _is_hairline(survey.level, gap):
            _draw_close_up(survey.level, gap, folder / f"gap_{gap.id:03d}.png")
    return folder


def _ranking(level: Level, gap: Gap) -> tuple:
    """Warps in the level as dumped first, then by the step needed, shortest first. Hairline gaps
    go to the very end whatever their status: there are many, and they are the least practical."""
    order = [WARP, WARP_IF_REMOVED, NO_WARP_FOUND].index(gap.status)
    step = float(gap.witness.step2) if gap.witness else 0
    return (_is_hairline(level, gap), order, step, _width(level, gap))


def _width(level: Level, gap: Gap) -> float:
    return level.to_world(float((gap.pinch or gap.narrowest).width2) ** 0.5)


def _is_hairline(level: Level, gap: Gap) -> bool:
    return _width(level, gap) < HAIRLINE_WIDTH_WORLD


# ---------------------------------------------------------------------------------------------
# Tables


def _write_gap_table(level: Level, gaps: list[Gap], path: Path) -> None:
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["gap", "status", "width", "step", "walk_round", "x", "z", "room", "between", "and",
             "objects_forming_gap", "objects_in_the_way", "pinches"]
        )  # fmt: skip
        for gap in gaps:
            pinch = gap.pinch or gap.narrowest
            x, z = level.to_world_point(pinch.midpoint)
            step = level.to_world(float(gap.witness.step2) ** 0.5) if gap.witness else None
            writer.writerow(
                [
                    gap.id,
                    gap.status,
                    f"{_width(level, gap):.3f}",
                    f"{step:.2f}" if step is not None else "",
                    _describe_walk_round(gap),
                    f"{x:.0f}",
                    f"{z:.0f}",
                    f"{level.tiles[pinch.start_tile].room:#04x}",
                    describe(level, pinch.first),
                    describe(level, pinch.second),
                    " ".join(f"{obj:#x}" for obj in sorted(gap.needs)),
                    " ".join(f"{obj:#x}" for obj in gap.blockers),
                    len(gap.pinches),
                ]
            )


def _describe_walk_round(gap: Gap) -> str:
    if gap.witness is None:
        return ""
    return "none found" if gap.walk_round is None else f"{gap.walk_round:.0f}"


def _write_decisions(survey: Survey, path: Path) -> None:
    level = survey.level
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["between", "and", "width", "kept", "reason", "because_of"])
        for decision in survey.decisions:
            blocker = level.segments[decision.blocker] if decision.blocker is not None else None
            writer.writerow(
                [
                    describe(level, level.segments[decision.first]),
                    describe(level, level.segments[decision.second]),
                    f"{decision.width_world:.3f}",
                    "yes" if decision.kept else "no",
                    decision.reason,
                    describe(level, blocker) if blocker else "",
                ]
            )


def _write_touching(survey: Survey, path: Path) -> None:
    level = survey.level
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["x", "z", "between", "and"])
        for touch in survey.touching:
            x, z = level.to_world_point(touch.at)
            writer.writerow(
                [
                    f"{x:.0f}",
                    f"{z:.0f}",
                    describe(level, touch.first),
                    describe(level, touch.second),
                ]
            )


def write_summary(output_root: Path = Path("output/gaps")) -> Path:
    """Gathers the warps from every level's gaps.csv into one table, shortest step first.
    Hairlines and gaps with no warp found are left to the per-level tables."""
    rows = []
    for table in sorted(output_root.glob("*/gaps.csv")):
        with table.open(newline="") as file:
            for row in csv.DictReader(file):
                if row["step"] and float(row["width"]) >= HAIRLINE_WIDTH_WORLD:
                    rows.append({"level": table.parent.name, **row})
    rows.sort(key=lambda row: (row["status"] != WARP, float(row["step"])))

    path = output_root / "summary.csv"
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]) if rows else ["level"])
        writer.writeheader()
        writer.writerows(rows)
    return path


# ---------------------------------------------------------------------------------------------
# Maps


def _draw_overviews(level: Level, gaps: list[Gap], folder: Path) -> None:
    """One map per part of the level, split up the same way as the level's own maps so that floors
    which overlap from above are drawn separately."""
    for index, tiles in enumerate(_tile_groups(level)):
        group_gaps = [gap for gap in gaps if (gap.pinch or gap.narrowest).start_tile in tiles]
        if not group_gaps:
            continue
        xs = [-level.to_world(x) for tile in tiles for x, _ in level.tiles[tile].points]
        zs = [level.to_world(z) for tile in tiles for _, z in level.tiles[tile].points]
        width, height = max(xs) - min(xs) + 200, max(zs) - min(zs) + 200
        # Small levels are drawn larger so that the numbers don't sit on top of each other
        pixels_per_unit = OVERVIEW_TARGET_PIXELS / max(width, height)
        pixels_per_unit = max(
            OVERVIEW_PIXELS_PER_UNIT[0], min(OVERVIEW_PIXELS_PER_UNIT[1], pixels_per_unit)
        )
        inches_per_unit = pixels_per_unit / OVERVIEW_DPI
        fig, ax = plt.subplots(figsize=(width * inches_per_unit, height * inches_per_unit))

        _draw_level(ax, level, tiles)
        for gap in group_gaps:
            _draw_gap(ax, level, gap, prominent=not _is_hairline(level, gap), numbered=True)
        ax.set_xlim(min(xs) - 100, max(xs) + 100)
        ax.set_ylim(min(zs) - 100, max(zs) + 100)
        _finish(fig, ax, folder / f"overview_{index}.png", dpi=OVERVIEW_DPI)


def _draw_close_up(level: Level, gap: Gap, path: Path) -> None:
    pinch = gap.pinch or gap.narrowest
    x, z = level.to_world_point(pinch.midpoint)
    half = CLOSE_UP_HALF_SIZE_WORLD
    region = tuple(v * float(level.scale) for v in (x - half, x + half, z - half, z + half))
    tiles = level.linked_tiles_within(pinch.start_tile, region)

    fig, ax = plt.subplots(figsize=(9, 9))
    _draw_level(ax, level, tiles, label_objects=True)
    _draw_gap(ax, level, gap, prominent=True, numbered=False)
    if gap.witness is not None:
        p, q = level.to_world_point(gap.witness.p), level.to_world_point(gap.witness.q)
        ax.plot([-p[0], -q[0]], [p[1], q[1]], color="green", linewidth=1.2, zorder=6)
        for centre in (p, q):
            ax.add_patch(
                plt.Circle((-centre[0], centre[1]), 30, fill=False, color="green", zorder=6)
            )

    step = f"{level.to_world(float(gap.witness.step2) ** 0.5):.1f}" if gap.witness else "-"
    ax.set_title(
        f"{level.name} gap {gap.id}: {gap.status}\n"
        f"width {_width(level, gap):.2f}, step {step}, "
        f"walk round {_describe_walk_round(gap) or '-'}\n"
        f"{describe(level, pinch.first)}  /  {describe(level, pinch.second)}",
        fontsize=9,
    )
    ax.set_xlim(-x - half, -x + half)
    ax.set_ylim(z - half, z + half)
    _finish(fig, ax, path, dpi=100)


def _draw_level(ax: Axes, level: Level, tiles: set[int], label_objects: bool = False) -> None:
    for addr in tiles:
        xs, zs = _flipped(level, level.tiles[addr].points)
        ax.fill(xs, zs, facecolor=TILE_COLOUR, edgecolor=TILE_COLOUR, linewidth=0.3, zorder=1)
    for wall in level.walls_of_tiles(tiles):
        _draw_segment(ax, level, wall, WALL_COLOUR, 0.6, zorder=2)
    for obj in level.objects_among_tiles(tiles):
        outline = level.objects[obj].points
        xs, zs = _flipped(level, [*outline, outline[0]])
        ax.plot(xs, zs, color=OBJECT_COLOUR, linewidth=0.7, zorder=3)
        if label_objects:
            name = f"{level.objects[obj].type} {obj:#x}"
            ax.text(xs[0], zs[0], name, fontsize=5, zorder=3, clip_on=True)


def _draw_gap(ax: Axes, level: Level, gap: Gap, prominent: bool, numbered: bool) -> None:
    """Highlights the walls which form the gap, and dots the line across its narrowest part.
    Hairline gaps are drawn faintly and without a number."""
    colour = STATUS_COLOUR[gap.status] if prominent else "grey"
    for pinch in gap.pinches:
        for wall in (pinch.first, pinch.second):
            _draw_segment(ax, level, wall, colour, 2.2 if prominent else 1.0, zorder=4)
        xs, zs = _flipped(level, [pinch.a, pinch.b])
        ax.plot(xs, zs, color=colour, linewidth=1.0, linestyle=":", zorder=5)
    if prominent and numbered:
        x, z = level.to_world_point((gap.pinch or gap.narrowest).midpoint)
        ax.annotate(
            str(gap.id), (-x, z), xytext=(6, 6), textcoords="offset points", fontsize=9,
            color=colour, fontweight="bold", zorder=7,
        )  # fmt: skip


def _draw_segment(
    ax: Axes, level: Level, segment: BoundarySegment, colour, linewidth: float, zorder: int
) -> None:
    xs, zs = _flipped(level, [segment.a, segment.b])
    ax.plot(xs, zs, color=colour, linewidth=linewidth, zorder=zorder, solid_capstyle="round")


def _flipped(level: Level, points: list) -> tuple[list[float], list[float]]:
    world = [level.to_world_point(point) for point in points]
    return [-x for x, _ in world], [z for _, z in world]


def _finish(fig, ax: Axes, path: Path, dpi: int) -> None:
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def _tile_groups(level: Level) -> list[set[int]]:
    """The level's tiles split into the same parts as its maps, using level_specific/<level>."""
    details = importlib.import_module(f"level_specific.{level.name}.details")
    raw_tiles = importlib.import_module(f"data.{level.name}").tiles
    groups = seperateGroups(raw_tiles, details.startTileName, details.dividingTiles)
    grouped = [set(group) for group in groups]
    leftover = set(level.tiles) - set().union(*grouped)
    return [*grouped, leftover] if leftover else grouped
