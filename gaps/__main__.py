"""Surveys levels for warp gaps: `python -m gaps train frigate`, or `python -m gaps all`."""

import sys
import time
from collections import Counter

import matplotlib

matplotlib.use("Agg")

import data
from gaps.report import write_report, write_summary
from gaps.survey import survey_level


def main(names: list[str]) -> None:
    if not names:
        sys.exit(__doc__)
    for name in data.__all__ if names == ["all"] else names:
        started = time.time()
        survey = survey_level(name)
        folder = write_report(survey)
        statuses = Counter(gap.status for gap in survey.gaps)
        print(
            f"{name}: {len(survey.decisions)} close pairs of walls, {len(survey.gaps)} gaps "
            f"{dict(statuses)}, {len(survey.touching)} touching, "
            f"{time.time() - started:.0f}s -> {folder}"
        )
    print(f"every level's warps together: {write_summary()}")


if __name__ == "__main__":
    main(sys.argv[1:])
