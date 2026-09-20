"""Surveys levels for gaps narrower than Bond, filters them, and writes the reports.

python -m gaps train frigate
python -m gaps all --reuse-surveys
"""

import argparse
import importlib
import sys
import time
from collections import Counter

import matplotlib

matplotlib.use("Agg")

import data
from gaps.filters import apply_filters, objects_to_remove, suppress_warps
from gaps.known_warps import check_known_warps
from gaps.report import OUTPUT_ROOT, write_report, write_summary
from gaps.review import write_review
from gaps.survey import load_survey, save_survey, survey_level
from gaps.variants import mark_variants


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
        "--variants",
        action="store_true",
        help="also draw the variants of each warp: other gaps which the same step passes through. "
        "They are always listed in variants.csv",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="also draw the close-ups for checking our own work, into output/00_debug/: every gap "
        "which a filter removed, and every object which is well above its floor",
    )
    arguments = parser.parse_args()

    anything_wrong = False
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
        mark_variants(survey.level, survey.gaps)
        suppress_warps(survey.level, survey.gaps)
        problems = check_known_warps(survey.level, survey.gaps)
        anything_wrong = anything_wrong or bool(contradictions or problems)
        folder = write_report(survey, contradictions, arguments.variants)
        if arguments.review:
            write_review(survey)

        unfiltered = [gap for gap in survey.gaps if gap.filtered_by is None]
        suppressed = [gap for gap in unfiltered if gap.suppressed_by is not None]
        kept = [gap for gap in unfiltered if not gap.variant_of and gap.suppressed_by is None]
        filters_used = Counter(
            gap.filtered_by.filter_name for gap in survey.gaps if gap.filtered_by
        )
        print(
            f"{name}: {len(kept)} gaps {dict(Counter(gap.status for gap in kept))}, "
            f"{len(suppressed)} suppressed, "
            f"{len(unfiltered) - len(kept) - len(suppressed)} variants, "
            f"{len(survey.gaps) - len(unfiltered)} filtered {dict(filters_used)}, "
            f"{time.time() - started:.0f}s -> {folder}"
        )
        for contradiction in contradictions:
            print(
                f"  [!] {contradiction.filter_name} contradicts a warp at {contradiction.gap.key}"
            )
        for problem in problems:
            print(f'  [!] known warp "{problem.warp.name}": {problem.what}')
    print(f"every level's warps together: {write_summary()}")
    if anything_wrong:
        sys.exit("[!] Something is wrong: see the lines marked [!] above")


if __name__ == "__main__":
    main()
