"""Surveys levels for gaps narrower than Bond, filters them, and writes the reports.

python -m gaps train frigate
python -m gaps all --reuse-surveys
"""

import argparse
import importlib
import time
from collections import Counter

import matplotlib

matplotlib.use("Agg")

import data
from gaps.filters import apply_filters, objects_to_remove
from gaps.report import OUTPUT_ROOT, write_report, write_summary
from gaps.review import write_review
from gaps.survey import load_survey, save_survey, survey_level


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("levels", nargs="+", help='level names as in data/, or "all"')
    parser.add_argument(
        "--reuse-surveys",
        action="store_true",
        help="skip the slow survey where one was saved by an earlier run, and only redo the "
        "filtering and the reports. Use this when working on filters.",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="also draw the close-ups for checking our own work, into output/00_debug/: every gap "
        "which a filter removed, and every object which is well above its floor",
    )
    arguments = parser.parse_args()

    for name in data.__all__ if arguments.levels == ["all"] else arguments.levels:
        started = time.time()
        saved = OUTPUT_ROOT / name / "survey.pickle"
        removed = objects_to_remove(name, importlib.import_module(f"data.{name}"))
        survey = load_survey(saved) if arguments.reuse_surveys else None
        if survey is not None and survey.removed != removed:
            print(
                f"{name}: the objects to remove have changed, so the saved survey can't be reused"
            )
            survey = None
        if survey is None:
            survey = survey_level(name, removed)
            save_survey(survey, saved)

        contradictions = apply_filters(survey.level, survey.gaps)
        folder = write_report(survey, contradictions)
        if arguments.review:
            write_review(survey)

        kept = [gap for gap in survey.gaps if gap.filtered_by is None]
        filters_used = Counter(
            gap.filtered_by.filter_name for gap in survey.gaps if gap.filtered_by
        )
        print(
            f"{name}: {len(kept)} gaps {dict(Counter(gap.status for gap in kept))}, "
            f"{len(survey.gaps) - len(kept)} filtered {dict(filters_used)}, "
            f"{time.time() - started:.0f}s -> {folder}"
        )
        for contradiction in contradictions:
            print(
                f"  [!] {contradiction.filter_name} contradicts a warp at {contradiction.gap.key}"
            )
    print(f"every level's warps together: {write_summary()}")


if __name__ == "__main__":
    main()
