"""Named warps: gaps we know about and want to keep an eye on.

Each level can have a file, gaps/known_warps/levels/<level>.py, listing warps by name together with
what the survey found for them. Every run checks them, so that they act as a regression test of
the whole tool: if a change to the survey or to a filter loses one, hides one, or alters what was
found, the run says so loudly. Names are also used in the outputs: gap 3 of Frigate is drawn as
003_pipe-warp.svg rather than gap_003.svg.

A named warp is tied to the two walls of a pinch, by their keys (the tile's name and which edge,
or the object's address and which side), not to its number, which changes whenever the ranking or
the filters do.

The step recorded is an upper bound. The survey reports the step of the best warp its search
found, which is a real warp but not a proven minimum, so a better search may find a shorter one
and that is no problem. Finding only a longer one is: something has been lost.
"""

import importlib
import re
from dataclasses import dataclass, field

from gaps.mesh import Level
from gaps.pinch import feature_key
from gaps.survey import Gap

WIDTH_TOLERANCE_CM = 0.0015  # see _same


@dataclass
class KnownWarp:
    name: str
    walls: str  # the keys of the two walls of one of its pinches, as in the key column of gaps.csv
    status: str  # one of the statuses in gaps/survey.py
    width_cm: float
    step_cm: float  # an upper bound: the survey must find a warp at most this long
    objects_forming_gap: list[int] = field(default_factory=list)
    objects_in_the_way: list[int] = field(default_factory=list)
    notes: str = ""

    @property
    def file_name(self) -> str:
        return re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")


@dataclass
class Problem:
    warp: KnownWarp
    what: str


def known_warps(level_name: str) -> list[KnownWarp]:
    try:
        module = importlib.import_module(f"gaps.known_warps.levels.{level_name}")
    except ModuleNotFoundError:
        return []
    return module.KNOWN_WARPS


def check_known_warps(level: Level, gaps: list[Gap]) -> list[Problem]:
    """Names the gaps which are known warps, and reports anything about them which has changed.
    Filters and suppressions must already have been applied, and variants marked."""
    problems = []
    by_key = {gap.key: gap for gap in gaps}
    for gap in gaps:
        gap.name = ""
    for warp in known_warps(level.name):
        wanted = normalise_walls(warp.walls)
        matches = [gap for gap in gaps if wanted in pinch_keys(level, gap)]
        if len(matches) != 1:
            problems.append(Problem(warp, f"{len(matches)} gaps have a pinch between {warp.walls}"))
            continue
        # The walls may be those of a variant, in which case it is the main gap which is meant
        gap = by_key[matches[0].variant_of or matches[0].key]
        if gap.suppressed_by is not None:
            problems.append(Problem(warp, "it is a suppressed warp: it can't be both"))
            continue
        if gap.name and gap.name != warp.name:
            problems.append(Problem(warp, f'it is the same warp as "{gap.name}"'))
            continue
        gap.name = warp.name
        problems += [Problem(warp, what) for what in _differences(level, warp, gap)]
    return problems


def _same(expected, found) -> bool:
    """Widths are recorded to a thousandth of a centimetre, and the last digit depends on float32
    rounding, so a difference of one there is allowed. Everything else must match exactly."""
    if isinstance(expected, float):
        return abs(expected - found) <= WIDTH_TOLERANCE_CM
    return expected == found


def _differences(level: Level, warp: KnownWarp, gap: Gap) -> list[str]:
    pinch = gap.pinch or gap.narrowest
    found = {
        "status": gap.status,
        "width_cm": round(level.to_cm(float(pinch.width2) ** 0.5), 3),
        "objects_forming_gap": sorted(gap.needs),
        "objects_in_the_way": sorted(gap.blockers),
    }
    expected = {
        "status": warp.status,
        "width_cm": warp.width_cm,
        "objects_forming_gap": sorted(warp.objects_forming_gap),
        "objects_in_the_way": sorted(warp.objects_in_the_way),
    }
    differences = [
        f"{what} was {expected[what]!r} and is now {found[what]!r}"
        for what in expected
        if not _same(expected[what], found[what])
    ]
    if gap.witness is not None:
        step_cm = round(level.to_cm(float(gap.witness.step2) ** 0.5), 2)
        if step_cm > warp.step_cm:
            differences.append(
                f"the shortest step found is now {step_cm} cm, "
                f"longer than the {warp.step_cm} cm recorded"
            )
    if gap.filtered_by is not None:
        differences.append(f'it is now filtered out by "{gap.filtered_by.filter_name}"')
    return differences


def pinch_keys(level: Level, gap: Gap) -> set[str]:
    return {
        normalise_walls(f"{feature_key(level, pinch.first)} | {feature_key(level, pinch.second)}")
        for pinch in gap.pinches
    }


def normalise_walls(walls: str) -> str:
    """The two wall keys in a fixed order, so that it doesn't matter which is written first."""
    return " | ".join(sorted(part.strip() for part in walls.split("|")))
