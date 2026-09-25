import unittest

from gaps.filters.groups import FilterFileError
from gaps.filters.predicates import is_crate, is_door
from gaps.filters.suppressed import NearbyObject, SuppressedWarp, apply_suppressions
from gaps.pinch import find_pinches
from gaps.survey import WARP, WARP_IF_REMOVED, Gap, _find_best_warp, _group_pinches
from gaps.tests.levels import build, crate

CRATE, FAR_CRATE = 0x9000, 0x9001


class SuppressedWarps(unittest.TestCase):
    """A crate 45 cm from the left wall of a big room, and another 3 m away from it."""

    def setUp(self):
        room = {"room": [(0, 0), (0, 800), (800, 800), (800, 0)]}
        objects = {
            CRATE: crate(CRATE, 0x1000, 45, 380, 40),
            FAR_CRATE: crate(FAR_CRATE, 0x1000, 400, 380, 40),
        }
        self.level = build(room, objects)
        pinches, _, _ = find_pinches(self.level)
        groups = _group_pinches(self.level, pinches)
        self.gaps = [Gap(id=i, pinches=group, key=str(i)) for i, group in enumerate(groups)]
        for gap in self.gaps:
            _find_best_warp(self.level, gap)

    def entry(self, **changes) -> SuppressedWarp:
        values = {
            "reason": "obvious",
            "walls": "001000.0 | 0x9000.0",
            "status": WARP,
            "width_cm": 45.0,
            "step_cm": 96.0,
            "nearby": [NearbyObject(CRATE, all=[is_crate])],
        }
        return SuppressedWarp(**{**values, **changes})

    def test_a_warp_which_is_as_described_is_suppressed(self):
        apply_suppressions(self.level, self.gaps, [self.entry()])
        self.assertEqual([gap.suppressed_by is not None for gap in self.gaps], [True])

    def test_every_check_stops_the_run_when_it_fails(self):
        wrong = {
            "its width is 45.000 cm, not 44.000 cm": self.entry(width_cm=44.0),
            "its status is 'warp', not": self.entry(status=WARP_IF_REMOVED),
            "longer than 10.0 cm": self.entry(step_cm=10.0),
            "0 gaps have a pinch between those walls": self.entry(walls="001000.0 | 0x9009.0"),
            "object 0x9000 fails is_door": self.entry(nearby=[NearbyObject(CRATE, all=[is_door])]),
            "near but not listed: 0x9000": self.entry(nearby=[]),
            "listed but not near: 0x9001": self.entry(
                nearby=[NearbyObject(CRATE), NearbyObject(FAR_CRATE)]
            ),
        }
        for message, entry in wrong.items():
            with self.assertRaisesRegex(FilterFileError, message):
                apply_suppressions(self.level, self.gaps, [entry])


if __name__ == "__main__":
    unittest.main()
