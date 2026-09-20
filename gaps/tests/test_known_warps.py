import unittest
from unittest import mock

from gaps import known_warps
from gaps.known_warps import KnownWarp, check_known_warps
from gaps.pinch import find_pinches
from gaps.survey import NO_WARP_FOUND, WARP, FilterVerdict, Gap
from gaps.tests.levels import two_rooms
from gaps.witness import find_witness

CORRIDOR = KnownWarp(
    name="corridor warp", walls="001200.1 | 001200.3", status=WARP, width_cm=50.0, step_cm=73.17
)


class KnownWarps(unittest.TestCase):
    def setUp(self):
        self.level = two_rooms(corridor_width=50)
        pinches, _, _ = find_pinches(self.level)
        found = [(find_witness(self.level, p, None), p) for p in pinches]
        witness, pinch = min(((w, p) for w, p in found if w), key=lambda wp: wp[0].step2)
        self.gap = Gap(id=1, pinches=pinches, status=WARP, pinch=pinch, witness=witness)

    def check(self, warp: KnownWarp) -> list[str]:
        with mock.patch.object(known_warps, "known_warps", return_value=[warp]):
            return [problem.what for problem in check_known_warps(self.level, [self.gap])]

    def test_a_warp_which_is_as_recorded_is_named_and_raises_nothing(self):
        self.assertEqual(self.check(CORRIDOR), [])
        self.assertEqual(self.gap.name, "corridor warp")

    def test_the_walls_may_be_written_in_either_order(self):
        self.assertEqual(
            self.check(KnownWarp(**{**vars(CORRIDOR), "walls": "001200.3 | 001200.1"})), []
        )

    def test_the_step_recorded_is_an_upper_bound(self):
        # Finding a shorter step than was recorded is fine
        self.assertEqual(self.check(KnownWarp(**{**vars(CORRIDOR), "step_cm": 80.0})), [])
        # Only finding a longer one is not
        self.assertEqual(
            self.check(KnownWarp(**{**vars(CORRIDOR), "step_cm": 73.16})),
            ["the shortest step found is now 73.17 cm, longer than the 73.16 cm recorded"],
        )

    def test_a_change_of_status_is_reported(self):
        self.gap.status = NO_WARP_FOUND
        self.assertIn("status was 'warp' and is now 'no warp found'", self.check(CORRIDOR))

    def test_being_filtered_out_is_reported(self):
        self.gap.filtered_by = FilterVerdict("some filter", "some reason")
        self.assertEqual(self.check(CORRIDOR), ['it is now filtered out by "some filter"'])

    def test_a_warp_which_has_gone_is_reported(self):
        gone = KnownWarp(**{**vars(CORRIDOR), "walls": "001200.1 | 009999.9"})
        self.assertEqual(self.check(gone), ["0 gaps have a pinch between 001200.1 | 009999.9"])


if __name__ == "__main__":
    unittest.main()
