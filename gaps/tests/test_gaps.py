"""End to end tests on tiny levels, one per situation the survey has to get right."""

import unittest

from gaps.detour import walking_distance
from gaps.pinch import BLOCKED, NOT_LINKED, find_pinches
from gaps.sheet import fits, trace
from gaps.tests.levels import build, crate, two_rooms
from gaps.witness import find_witness


def widths(level, pinches) -> list[float]:
    return sorted(round(level.to_world(float(pinch.width2) ** 0.5), 3) for pinch in pinches)


class NarrowCorridor(unittest.TestCase):
    def test_a_corridor_narrower_than_bond_is_a_warp(self):
        level = two_rooms(corridor_width=50)
        pinches, _, _ = find_pinches(level)
        self.assertEqual(sorted(set(widths(level, pinches))), [50.0])

        witnesses = [(find_witness(level, pinch, present=None), pinch) for pinch in pinches]
        witness, pinch = min(
            ((w, p) for w, p in witnesses if w is not None), key=lambda found: found[0].step2
        )
        # The corridor is 40 long. At each end Bond stands in the mouth of it, as far in as the two
        # corners 50 apart allow: sqrt(30^2 - 25^2) = 16.58 back from the opening.
        self.assertAlmostEqual(level.to_world(float(witness.step2) ** 0.5), 73.17, delta=0.05)
        self.assertIsNone(walking_distance(level, pinch, witness, present=None))

    def test_a_corridor_exactly_as_wide_as_bond_is_not(self):
        pinches, _, _ = find_pinches(two_rooms(corridor_width=60))
        self.assertEqual(pinches, [])

    def test_a_vertical_tile_across_the_corridor_changes_nothing(self):
        level = two_rooms(corridor_width=50, riser=True)
        pinches, _, _ = find_pinches(level)
        self.assertEqual(sorted(set(widths(level, pinches))), [50.0])
        self.assertTrue(any(find_witness(level, pinch, present=None) for pinch in pinches))


class ThingsWhichAreNotGaps(unittest.TestCase):
    def test_the_thickness_of_a_wall(self):
        # Two rooms 10 apart with nothing joining them
        level = build(
            {
                "left": [(0, 0), (0, 100), (100, 100), (100, 0)],
                "right": [(110, 0), (110, 100), (210, 100), (210, 0)],
            }
        )
        pinches, _, decisions = find_pinches(level)
        self.assertEqual(pinches, [])
        self.assertEqual({decision.reason for decision in decisions}, {NOT_LINKED})

    def test_a_floor_directly_above_another(self):
        # The same narrow tile twice. Nothing links them, so their walls never meet.
        level = build(
            {
                "downstairs": [(0, 0), (0, 200), (200, 200), (200, 0)],
                "upstairs": [(90, 0), (90, 201), (110, 201), (110, 0)],
            }
        )
        pinches, _, _ = find_pinches(level)
        # Only upstairs' own two long walls, which are 20 apart. Downstairs' walls are 90 from
        # them when seen from above, but they are not in the same place as far as the game goes.
        self.assertEqual(widths(level, pinches), [20.0])

    def test_walls_converging_on_a_short_end_wall(self):
        # The two long walls are 20 apart at the narrow end, but that is the end wall itself
        level = build({"wedge": [(0, 0), (0, 300), (400, 160), (400, 140)]})
        pinches, _, decisions = find_pinches(level)
        self.assertEqual(pinches, [])
        self.assertIn(BLOCKED, {decision.reason for decision in decisions})


class Objects(unittest.TestCase):
    def setUp(self):
        room = {"room": [(0, 0), (0, 400), (400, 400), (400, 0)]}
        self.crate = 0x9000
        # 45 from the left wall, in the middle of it
        self.level = build(room, {self.crate: crate(self.crate, 0x1000, 45, 180, 40)})

    def test_a_crate_near_a_wall_forms_a_gap_which_depends_on_the_crate(self):
        pinches, _, _ = find_pinches(self.level)
        self.assertEqual(sorted(set(widths(self.level, pinches))), [45.0])
        self.assertTrue(all(pinch.needs == {self.crate} for pinch in pinches))

    def test_bond_can_warp_past_it_but_could_also_walk_round(self):
        pinches, _, _ = find_pinches(self.level)
        found = [(p, find_witness(self.level, p, present=None)) for p in pinches]
        pinch, witness = next((p, w) for p, w in found if w is not None)
        self.assertIsNotNone(walking_distance(self.level, pinch, witness, present=None))

    def test_objects_only_exist_when_present(self):
        tile = 0x1000
        beside_crate = (20, 200)
        self.assertFalse(fits(self.level, tile, beside_crate, present=None)[0])
        self.assertFalse(fits(self.level, tile, beside_crate, present=frozenset())[0])  # the wall
        in_crate = (65, 200)
        self.assertTrue(fits(self.level, tile, in_crate, present=frozenset())[0])
        through_crate = trace(self.level, tile, (40, 200), (120, 200), present=None)
        self.assertEqual(through_crate.reason, "touches an object")
        self.assertTrue(trace(self.level, tile, (40, 200), (120, 200), present=frozenset()).clear)


if __name__ == "__main__":
    unittest.main()
