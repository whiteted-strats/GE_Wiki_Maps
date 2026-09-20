"""Writes a survey out as tables and maps, under output/00_gaps/<level>/.

  gaps.csv        one row per gap which survives the filters, easiest warps first
  variants.csv    gaps which are the same warp as a shorter one in gaps.csv: see gaps/variants.py
  filtered.csv    the gaps which were filtered out, each with the filter and its reason
  suppressed.csv  real warps hidden by the level's file, each with its reason
  filter_contradictions.csv   should be empty, see gaps/filters/generic.py
  decisions.csv   every pair of walls closer than Bond's diameter, and why it was kept or dismissed
  touching.csv    unrelated walls which touch (gaps of width zero)
  vertical_edges_left_out.csv  edges of vertical tiles which no floor leads into, so not walls
  overview_*.svg  each part of the level, with the gaps numbered and the walls involved highlighted
  gap_NNN.svg     a close-up of each gap (NNN_name.svg if it is a known warp), as vector graphics
                  so it can be zoomed without limit.
                  Filtered gaps are only drawn faintly on the overviews. Warps through
                  hairlines are orange

and output/00_gaps/summary.csv, which lists the warps of every surveyed level together.

The maps are deliberately plain: tiles, walls and object outlines only. As on the other maps in
this repo, x is flipped so that they match the game's orientation.
"""

import csv
import importlib
import math
import re
from collections import Counter
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from gaps.filters import Contradiction
from gaps.mesh import BOND_RADIUS_CM, BoundarySegment, Level
from gaps.pinch import describe
from gaps.survey import NO_WARP_FOUND, WARP, WARP_IF_REMOVED, Gap, Survey
from lib.seperate_tile_groups import seperateGroups

matplotlib.rcParams["svg.fonttype"] = "none"  # keep text as text in the close-ups
# With these two, drawing the same thing twice gives the same file, so the images can be committed
matplotlib.rcParams["svg.hashsalt"] = "gaps"
SVG_METADATA = {"Date": None}

# The leading 00 lists these first among the folders of output/, in file managers as well as ls
OUTPUT_ROOT = Path("output/00_gaps")
# Narrower gaps are hairlines: a warp through one is drawn in a colour of its own, and the width
# is written on the close-up.
# They are treated like any other gap otherwise. However narrow, a gap with a warp is a warp.
HAIRLINE_WIDTH_CM = 1
CLOSE_UP_HALF_SIZE_CM = 260  # shows a few metres of surroundings. Nothing depends on the value
# Overviews are vector graphics, so these only set how big the numbers and lines are drawn
# relative to the level: as if it were an image this many pixels along its longer side ...
OVERVIEW_TARGET_PIXELS = 4000
OVERVIEW_PIXELS_PER_UNIT = (0.5, 2.0)  # ... as long as the scale stays within these
OVERVIEW_DPI = 100
STATUS_COLOUR = {WARP: "red", WARP_IF_REMOVED: "darkviolet", NO_WARP_FOUND: "royalblue"}
TILE_COLOUR = (0.86, 0.86, 0.86)
WALL_COLOUR = (0.25, 0.25, 0.25)
HAIRLINE_COLOUR = "orange"
OBJECT_COLOUR = "sienna"  # well away from the orange of hairlines


def write_report(
    survey: Survey,
    contradictions: list[Contradiction],
    draw_variants: bool = False,
    output_root: Path = OUTPUT_ROOT,
) -> Path:
    """Filters must already have been applied to the survey's gaps, and variants marked: see
    gaps.filters and gaps.variants."""
    level = survey.level
    folder = output_root / level.name
    folder.mkdir(parents=True, exist_ok=True)
    for old_image in [*folder.glob("*.png"), *folder.glob("*.svg")]:
        old_image.unlink()

    ranked = sorted(survey.gaps, key=lambda gap: _ranking(level, gap))
    by_key = {gap.key: gap for gap in ranked}
    filtered = [gap for gap in ranked if gap.filtered_by is not None]
    # A suppressed warp takes its variants with it
    suppressed = [
        gap
        for gap in ranked
        if gap.filtered_by is None and by_key[gap.variant_of or gap.key].suppressed_by is not None
    ]
    unsuppressed = [gap for gap in ranked if gap.filtered_by is None and gap not in suppressed]
    variants = [gap for gap in unsuppressed if gap.variant_of]
    kept = [gap for gap in unsuppressed if not gap.variant_of]
    for number, gap in enumerate(kept, start=1):
        gap.id = number  # number them in the order they are listed
    main_of = {gap.key: gap for gap in kept}

    _write_gap_table(level, kept, folder / "gaps.csv")
    _write_variants(level, variants, main_of, folder / "variants.csv")
    _write_filtered(level, filtered, folder / "filtered.csv")
    _write_suppressed(level, suppressed, by_key, folder / "suppressed.csv")
    _write_contradictions(level, contradictions, folder / "filter_contradictions.csv")
    _write_decisions(survey, folder / "decisions.csv")
    _write_touching(survey, folder / "touching.csv")
    _write_objects_left_out(level, folder / "objects_left_out.csv")
    _write_vertical_edges_left_out(level, folder / "vertical_edges_left_out.csv")

    # Filtered and suppressed gaps are drawn faintly and without a number
    faint_keys = {gap.key for gap in [*filtered, *suppressed]}
    shown = [gap for gap in ranked if draw_variants or not gap.variant_of or gap.key in faint_keys]
    _draw_overviews(level, shown, faint_keys, folder)
    for gap in kept:
        draw_close_up(level, gap, folder / f"{file_name_of(gap)}.svg")
    if draw_variants:
        numbers: Counter = Counter()
        for gap in variants:
            main = main_of[gap.variant_of]
            numbers[main.key] += 1
            gap.id = main.id  # so that it is titled and labelled as belonging to its main gap
            gap.name = f"{main.name} variant {numbers[main.key]}".strip()
            draw_close_up(level, gap, folder / f"{file_name_of(gap)}.svg")
    return folder


def file_name_of(gap: Gap) -> str:
    """gap_003, or 003_pipe-warp if it is a known warp."""
    if not gap.name:
        return f"gap_{gap.id:03d}"
    return f"{gap.id:03d}_" + re.sub(r"[^a-z0-9]+", "-", gap.name.lower()).strip("-")


def _ranking(level: Level, gap: Gap) -> tuple:
    """Warps in the level as dumped first, then by the step needed, shortest first."""
    order = [WARP, WARP_IF_REMOVED, NO_WARP_FOUND].index(gap.status)
    step = float(gap.witness.step2) if gap.witness else 0
    return (order, step, _width(level, gap))


def _width(level: Level, gap: Gap) -> float:
    return level.to_cm(float((gap.pinch or gap.narrowest).width2) ** 0.5)


def _width_text(level: Level, gap: Gap) -> str:
    """To a thousandth of a centimetre, except for hairlines, which are given to two significant
    figures: a door in its frame can be a millionth of a centimetre from it."""
    width = _width(level, gap)
    if width >= HAIRLINE_WIDTH_CM:
        return f"{width:.3f}"
    decimal_places = 1 - math.floor(math.log10(width))  # a gap is never of no width at all
    return f"{width:.{decimal_places}f}"


def _is_hairline(level: Level, gap: Gap) -> bool:
    return _width(level, gap) < HAIRLINE_WIDTH_CM


# ---------------------------------------------------------------------------------------------
# Tables


def _write_gap_table(level: Level, gaps: list[Gap], path: Path) -> None:
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(
            ["gap", "name", "status", "width_cm", "step_cm", "walk_round_cm", "x", "z", "room",
             "between", "and", "objects_forming_gap", "objects_in_the_way", "pinches", "key"]
        )  # fmt: skip
        for gap in gaps:
            pinch = gap.pinch or gap.narrowest
            x, z = level.to_cm_point(pinch.midpoint)
            step = level.to_cm(float(gap.witness.step2) ** 0.5) if gap.witness else None
            writer.writerow(
                [
                    gap.id,
                    gap.name,
                    gap.status,
                    _width_text(level, gap),
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
                    gap.key,
                ]
            )


def _describe_walk_round(gap: Gap) -> str:
    if gap.witness is None:
        return ""
    return "none found" if gap.walk_round is None else f"{gap.walk_round:.0f}"


def _write_variants(level: Level, variants: list[Gap], main_of: dict[str, Gap], path: Path) -> None:
    """Gaps which the step of another, shorter warp passes through, so are counted as that warp."""
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(
            ["variant_of_gap", "name", "key", "status", "width_cm", "step_cm", "x", "z", "between",
             "and", "objects_forming_gap", "objects_in_the_way"]
        )  # fmt: skip
        for gap in variants:
            main = main_of[gap.variant_of]
            x, z = level.to_cm_point(gap.pinch.midpoint)
            writer.writerow(
                [
                    main.id,
                    main.name,
                    gap.key,
                    gap.status,
                    _width_text(level, gap),
                    f"{level.to_cm(float(gap.witness.step2) ** 0.5):.2f}",
                    f"{x:.0f}",
                    f"{z:.0f}",
                    describe(level, gap.pinch.first),
                    describe(level, gap.pinch.second),
                    " ".join(f"{obj:#x}" for obj in sorted(gap.needs)),
                    " ".join(f"{obj:#x}" for obj in gap.blockers),
                ]
            )


def _write_filtered(level: Level, filtered: list[Gap], path: Path) -> None:
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(
            ["key", "filter", "reason", "status", "width_cm", "x", "z", "between", "and"]
        )
        for gap in filtered:
            pinch = gap.pinch or gap.narrowest
            x, z = level.to_cm_point(pinch.midpoint)
            writer.writerow(
                [
                    gap.key,
                    gap.filtered_by.filter_name,
                    gap.filtered_by.reason,
                    gap.status,
                    _width_text(level, gap),
                    f"{x:.0f}",
                    f"{z:.0f}",
                    describe(level, pinch.first),
                    describe(level, pinch.second),
                ]
            )


def _write_suppressed(
    level: Level, suppressed: list[Gap], by_key: dict[str, Gap], path: Path
) -> None:
    """Real warps which the level's file says to hide, and why. See gaps/filters/suppressed.py."""
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(
            ["key", "reason", "status", "width_cm", "step_cm", "x", "z", "between", "and"]
        )
        for gap in suppressed:
            main = by_key[gap.variant_of or gap.key]
            x, z = level.to_cm_point(gap.pinch.midpoint)
            writer.writerow(
                [
                    gap.key,
                    main.suppressed_by.reason + (" (a variant of it)" if gap.variant_of else ""),
                    gap.status,
                    _width_text(level, gap),
                    f"{level.to_cm(float(gap.witness.step2) ** 0.5):.2f}",
                    f"{x:.0f}",
                    f"{z:.0f}",
                    describe(level, gap.pinch.first),
                    describe(level, gap.pinch.second),
                ]
            )


def _write_contradictions(level: Level, contradictions: list[Contradiction], path: Path) -> None:
    """Gaps which a generic filter says can't be warped through, but which have a certified warp.
    They are kept in gaps.csv. This file should only ever hold its heading."""
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["key", "filter", "filter_says", "status", "step_cm"])
        for contradiction in contradictions:
            gap = contradiction.gap
            step = level.to_cm(float(gap.witness.step2) ** 0.5)
            writer.writerow(
                [
                    gap.key,
                    contradiction.filter_name,
                    contradiction.reason,
                    gap.status,
                    f"{step:.2f}",
                ]
            )


def _write_objects_left_out(level: Level, path: Path) -> None:
    """Every object which takes no part in the survey, and why. Most are pick-ups, or have no
    outline. Any which a level file asked to have removed are here too, with its reason."""
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["object", "type", "reason"])
        for addr, object_type, reason in sorted(level.skipped_objects, key=lambda entry: entry[2]):
            writer.writerow([f"{addr:#x}", object_type, reason])


def _write_vertical_edges_left_out(level: Level, path: Path) -> None:
    """Unlinked edges of vertical tiles which are not walls, or not all the way along, as no floor
    leads into them there. See gaps.mesh."""
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["edge", "room", "from_x", "from_z", "to_x", "to_z", "still_a_wall_along"])
        for addr, edge_index, stretches in level.vertical_edges_left_out:
            tile = level.tiles[addr]
            (from_x, from_z), (to_x, to_z) = (level.to_cm_point(p) for p in tile.edge(edge_index))
            kept = "; ".join(
                "({:.1f}, {:.1f}) to ({:.1f}, {:.1f})".format(
                    *level.to_cm_point(start), *level.to_cm_point(end)
                )
                for start, end in stretches
            )
            writer.writerow(
                [f"{tile.name:06X}.{edge_index}", f"{tile.room:#04x}"]
                + [f"{value:.1f}" for value in (from_x, from_z, to_x, to_z)]
                + [kept or "none of it"]
            )


def _write_decisions(survey: Survey, path: Path) -> None:
    level = survey.level
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["between", "and", "width", "kept", "reason", "because_of"])
        for decision in survey.decisions:
            blocker = level.segments[decision.blocker] if decision.blocker is not None else None
            writer.writerow(
                [
                    describe(level, level.segments[decision.first]),
                    describe(level, level.segments[decision.second]),
                    f"{decision.width_cm:.3f}",
                    "yes" if decision.kept else "no",
                    decision.reason,
                    describe(level, blocker) if blocker else "",
                ]
            )


def _write_touching(survey: Survey, path: Path) -> None:
    level = survey.level
    with path.open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["x", "z", "between", "and"])
        for touch in survey.touching:
            x, z = level.to_cm_point(touch.at)
            writer.writerow(
                [
                    f"{x:.0f}",
                    f"{z:.0f}",
                    describe(level, touch.first),
                    describe(level, touch.second),
                ]
            )


def write_summary(output_root: Path = OUTPUT_ROOT) -> Path:
    """Gathers the warps from every level's gaps.csv into one table, shortest step first.
    Gaps with no warp found are left to the per-level tables."""
    rows = []
    for table in sorted(output_root.glob("*/gaps.csv")):
        with table.open(newline="") as file:
            for row in csv.DictReader(file):
                if "step_cm" not in row:
                    break  # a table written by an older version of this report
                if row["step_cm"]:
                    rows.append({"level": table.parent.name, **row})
    rows.sort(key=lambda row: (row["status"] != WARP, float(row["step_cm"])))

    path = output_root / "summary.csv"
    with path.open("w", newline="") as file:
        columns = list(dict.fromkeys(column for row in rows for column in row)) or ["level"]
        writer = csv.DictWriter(file, fieldnames=columns, restval="", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


# ---------------------------------------------------------------------------------------------
# Maps


def _draw_overviews(level: Level, gaps: list[Gap], faint_keys: set[str], folder: Path) -> None:
    """One map per part of the level, split up the same way as the level's own maps so that floors
    which overlap from above are drawn separately."""
    for index, tiles in enumerate(_tile_groups(level)):
        group_gaps = [gap for gap in gaps if (gap.pinch or gap.narrowest).start_tile in tiles]
        if not group_gaps:
            continue
        xs = [-level.to_cm(x) for tile in tiles for x, _ in level.tiles[tile].points]
        zs = [level.to_cm(z) for tile in tiles for _, z in level.tiles[tile].points]
        width, height = max(xs) - min(xs) + 200, max(zs) - min(zs) + 200
        # Small levels are drawn larger so that the numbers don't sit on top of each other
        pixels_per_unit = OVERVIEW_TARGET_PIXELS / max(width, height)
        pixels_per_unit = max(
            OVERVIEW_PIXELS_PER_UNIT[0], min(OVERVIEW_PIXELS_PER_UNIT[1], pixels_per_unit)
        )
        inches_per_unit = pixels_per_unit / OVERVIEW_DPI
        fig, ax = plt.subplots(figsize=(width * inches_per_unit, height * inches_per_unit))

        draw_level(ax, level, tiles)
        for gap in group_gaps:
            draw_gap(ax, level, gap, prominent=gap.key not in faint_keys, numbered=True)
        ax.set_xlim(min(xs) - 100, max(xs) + 100)
        ax.set_ylim(min(zs) - 100, max(zs) + 100)
        finish(fig, ax, folder / f"overview_{index}.svg")


def draw_close_up(level: Level, gap: Gap, path: Path) -> None:
    pinch = gap.pinch or gap.narrowest
    x, z = level.to_cm_point(pinch.midpoint)
    half = _close_up_half_size(level, gap)
    region = tuple(v * float(level.scale) for v in (x - half, x + half, z - half, z + half))
    tiles = level.linked_tiles_within(pinch.start_tile, region)

    fig, ax = plt.subplots(figsize=(9, 9))
    draw_level(ax, level, tiles, label_objects=True)
    draw_gap(ax, level, gap, prominent=True, numbered=False)
    if _is_hairline(level, gap):
        ax.annotate(
            f"{_width_text(level, gap)} cm", (-x, z), xytext=(8, 8), textcoords="offset points",
            fontsize=9, color=_colour_of(level, gap), fontweight="bold", zorder=7,
        )  # fmt: skip
    if gap.witness is not None:
        p, q = level.to_cm_point(gap.witness.p), level.to_cm_point(gap.witness.q)
        ax.plot([-p[0], -q[0]], [p[1], q[1]], color="green", linewidth=1.2, zorder=6)
        for centre in (p, q):
            ax.add_patch(
                plt.Circle(
                    (-centre[0], centre[1]), BOND_RADIUS_CM, fill=False, color="green", zorder=6
                )
            )

    step = f"{level.to_cm(float(gap.witness.step2) ** 0.5):.1f}" if gap.witness else "-"
    ax.set_title(
        f"{level.name} {_name_of(gap)}: {gap.status}\n"
        f"width {_width_text(level, gap)}, step {step}, "
        f"walk round {_describe_walk_round(gap) or '-'}\n"
        f"{describe(level, pinch.first)}  /  {describe(level, pinch.second)}",
        fontsize=9,
    )
    ax.set_xlim(-x - half, -x + half)
    ax.set_ylim(z - half, z + half)
    finish(fig, ax, path)


def _close_up_half_size(level: Level, gap: Gap) -> float:
    """Half the width of the square shown, in centimetres. At least the usual size, and more if
    that is what it takes to show both ends of the warp with Bond standing at them."""
    if gap.witness is None:
        return CLOSE_UP_HALF_SIZE_CM
    x, z = level.to_cm_point((gap.pinch or gap.narrowest).midpoint)
    ends = [level.to_cm_point(gap.witness.p), level.to_cm_point(gap.witness.q)]
    furthest = max(max(abs(end_x - x), abs(end_z - z)) for end_x, end_z in ends)
    return max(CLOSE_UP_HALF_SIZE_CM, furthest + 2 * BOND_RADIUS_CM)


def _name_of(gap: Gap) -> str:
    if gap.suppressed_by is not None:
        return f"suppressed warp {gap.key}"
    if gap.filtered_by is None:
        return f"gap {gap.id}" + (f" ({gap.name})" if gap.name else "")
    return f"filtered gap {gap.key} ({gap.filtered_by.filter_name})"


def draw_level(ax: Axes, level: Level, tiles: set[int], label_objects: bool = False) -> None:
    for addr in tiles:
        xs, zs = flipped(level, level.tiles[addr].points)
        ax.fill(xs, zs, facecolor=TILE_COLOUR, edgecolor=TILE_COLOUR, linewidth=0.3, zorder=1)
    for wall in level.walls_of_tiles(tiles):
        _draw_segment(ax, level, wall, WALL_COLOUR, 0.6, zorder=2)
    for obj in level.objects_among_tiles(tiles):
        outline = level.objects[obj].points
        xs, zs = flipped(level, [*outline, outline[0]])
        ax.plot(xs, zs, color=OBJECT_COLOUR, linewidth=0.7, zorder=3)
        if label_objects:
            name = f"{level.objects[obj].type} {obj:#x}"
            ax.text(xs[0], zs[0], name, fontsize=5, zorder=3, clip_on=True)


def _colour_of(level: Level, gap: Gap) -> str:
    """By status, except that a warp through a hairline is set apart from other warps."""
    if gap.status == WARP and _is_hairline(level, gap):
        return HAIRLINE_COLOUR
    return STATUS_COLOUR[gap.status]


def draw_gap(ax: Axes, level: Level, gap: Gap, prominent: bool, numbered: bool) -> None:
    """Highlights the walls which form the gap, and dots the line across its narrowest part.
    See _colour_of."""
    colour = _colour_of(level, gap) if prominent else "grey"
    for pinch in gap.pinches:
        for wall in (pinch.first, pinch.second):
            _draw_segment(ax, level, wall, colour, 2.2 if prominent else 1.0, zorder=4)
        xs, zs = flipped(level, [pinch.a, pinch.b])
        ax.plot(xs, zs, color=colour, linewidth=1.0, linestyle=":", zorder=5)
    if prominent and numbered:
        x, z = level.to_cm_point((gap.pinch or gap.narrowest).midpoint)
        ax.annotate(
            f"{gap.id} {gap.name}".strip(), (-x, z), xytext=(6, 6), textcoords="offset points",
            fontsize=9,
            color=colour, fontweight="bold", zorder=7,
        )  # fmt: skip


def _draw_segment(
    ax: Axes, level: Level, segment: BoundarySegment, colour, linewidth: float, zorder: int
) -> None:
    xs, zs = flipped(level, [segment.a, segment.b])
    ax.plot(xs, zs, color=colour, linewidth=linewidth, zorder=zorder, solid_capstyle="round")


def flipped(level: Level, points: list) -> tuple[list[float], list[float]]:
    in_cm = [level.to_cm_point(point) for point in points]
    return [-x for x, _ in in_cm], [z for _, z in in_cm]


def finish(fig, ax: Axes, path: Path, dpi: int = 100) -> None:
    ax.set_aspect("equal")
    ax.axis("off")
    metadata = SVG_METADATA if path.suffix == ".svg" else None
    fig.savefig(path, dpi=dpi, bbox_inches="tight", metadata=metadata)
    plt.close(fig)
    if path.suffix == ".svg":
        _keep_lines_thin_when_zoomed(path)


def _keep_lines_thin_when_zoomed(svg: Path) -> None:
    """Close-ups are vector graphics so that they can be zoomed into without limit, which matters
    when a gap is a fraction of a centimetre wide. Ordinarily lines get thicker as you zoom and
    would cover such a gap, so this tells the viewer to keep every line the same width on screen."""
    text = svg.read_text()
    style = "<style>path { vector-effect: non-scaling-stroke; }</style>"
    svg.write_text(text.replace("<defs>", f"{style}\n <defs>", 1))


def _tile_groups(level: Level) -> list[set[int]]:
    """The level's tiles split into the same parts as its maps, using level_specific/<level>."""
    details = importlib.import_module(f"level_specific.{level.name}.details")
    raw_tiles = importlib.import_module(f"data.{level.name}").tiles
    groups = seperateGroups(raw_tiles, details.startTileName, details.dividingTiles)
    grouped = [set(group) for group in groups]
    leftover = set(level.tiles) - set().union(*grouped)
    return [*grouped, leftover] if leftover else grouped
