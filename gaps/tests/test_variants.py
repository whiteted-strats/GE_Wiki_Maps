import unittest

from gaps.pinch import find_pinches
from gaps.survey import NO_WARP_FOUND, WARP, Gap, _find_best_warp, _group_pinches
from gaps.tests.levels import two_rooms
from gaps.variants import mark_variants


def gaps_of(level) -> list[Gap]:
    pinches, _, _ = find_pinches(level)
    gaps = [
        Gap(id=i, pinches=group, key=str(i))
        for i, group in enumerate(_group_pinches(level, pinches))
    ]
    for gap in gaps:
        _find_best_warp(level, gap)
    return gaps


class Variants(unittest.TestCase):
    def test_a_long_corridor_has_a_gap_at_each_mouth_and_one_between_but_is_one_warp(self):
        level = two_rooms(corridor_width=50, corridor_length=200)
        gaps = gaps_of(level)
        self.assertEqual(len(gaps), 3)

        mark_variants(level, gaps)
        mains = [gap for gap in gaps if not gap.variant_of]
        self.assertEqual(len(mains), 1)
        self.assertEqual(mains[0].witness.step2, min(gap.witness.step2 for gap in gaps))
        self.assertEqual({gap.variant_of for gap in gaps if gap.variant_of}, {mains[0].key})

    def test_a_gap_with_no_warp_of_its_own_is_proved_by_a_step_through_it(self):
        level = two_rooms(corridor_width=50, corridor_length=200)
        gaps = gaps_of(level)
        main = min(gaps, key=lambda gap: gap.witness.step2)
        unlucky = next(gap for gap in gaps if gap is not main)
        unlucky.witness, unlucky.pinch, unlucky.status = None, None, NO_WARP_FOUND  # as if unfound

        mark_variants(level, gaps)
        self.assertEqual(unlucky.variant_of, main.key)
        self.assertIs(unlucky.witness, main.witness)
        self.assertEqual(unlucky.status, WARP)
        self.assertIn(unlucky.pinch, unlucky.pinches)

    def test_two_corridors_far_apart_are_two_warps(self):
        level = two_rooms(corridor_width=50)
        gaps = gaps_of(level)
        mark_variants(level, gaps)
        self.assertEqual([gap.variant_of for gap in gaps], [""] * len(gaps))


if __name__ == "__main__":
    unittest.main()
