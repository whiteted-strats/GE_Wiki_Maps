"""Touching gaps: walls at no distance, surveyed as gaps of width zero on request."""

import math
import unittest

from gaps.exact import bounding_box, grow_box
from gaps.pinch import find_pinches
from gaps.sheet import trace, walls_near
from gaps.survey import WARP, Gap, _find_best_warp, _group_pinches
from gaps.tests.levels import build, crate, two_rooms
from gaps.witness import _propose

ROOM = 0x1000  # the first tile built
L_ROOM = {"room": [(0, 0), (0, 200), (100, 200), (100, 100), (200, 100), (200, 0)]}
SQUARE_ROOM = {"room": [(0, 0), (0, 300), (300, 300), (300, 0)]}


class LineOfSightAlongWalls(unittest.TestCase):
    """The relaxed rule used for a step through a touching gap, against the usual one."""

    def test_along_a_wall(self):
        level = build(L_ROOM)
        self.assertTrue(trace(level, ROOM, (0, 20), (0, 180), None, along_walls=True).clear)
        self.assertFalse(trace(level, ROOM, (0, 20), (0, 180), None).clear)

    def test_past_a_corner(self):
        level = build(L_ROOM)
        self.assertTrue(trace(level, ROOM, (50, 150), (150, 50), None, along_walls=True).clear)
        self.assertFalse(trace(level, ROOM, (50, 150), (150, 50), None).clear)

    def test_cutting_a_corner_into_the_void_still_fails(self):
        level = build(L_ROOM)
        line = trace(level, ROOM, (50, 190), (190, 50), None, along_walls=True)
        self.assertFalse(line.clear)
        self.assertEqual(line.reason, "leaves the walkable area")

    def test_objects(self):
        level = build(SQUARE_ROOM, {0x9000: crate(0x9000, ROOM, 100, 100, 100)})
        crossing = trace(level, ROOM, (50, 150), (150, 150), None, along_walls=True)
        self.assertEqual(crossing.reason, "touches an object")
        self.assertTrue(trace(level, ROOM, (50, 100), (250, 100), None, along_walls=True).clear)
        self.assertFalse(trace(level, ROOM, (50, 100), (250, 100), None).clear)
        diagonal = trace(level, ROOM, (50, 50), (250, 250), None, along_walls=True)
        self.assertEqual(diagonal.reason, "inside an object")

    def test_a_point(self):
        level = build(L_ROOM)
        self.assertTrue(trace(level, ROOM, (50, 50), (50, 50), None).clear)
        self.assertEqual(trace(level, ROOM, (50, 50), (50, 50), None).end_tiles, {ROOM})
        self.assertFalse(trace(level, ROOM, (150, 150), (150, 150), None).clear)


class TouchingPinches(unittest.TestCase):
    def test_a_crate_against_the_wall(self):
        level = build(SQUARE_ROOM, {0x9000: crate(0x9000, ROOM, 0, 100, 40)})
        pinches, touching, decisions = find_pinches(level)
        self.assertEqual([pinch for pinch in pinches if pinch.touching], [])
        self.assertEqual(len(touching), 3)  # along the crate's side, and at its two corners

        pinches, touching_too, decisions = find_pinches(level, include_touching=True)
        self.assertEqual(touching_too, touching)
        found = [pinch for pinch in pinches if pinch.touching]
        self.assertEqual({pinch.a for pinch in found}, {(0, 100), (0, 120), (0, 140)})
        for pinch in found:
            self.assertEqual(pinch.a, pinch.b)
            self.assertEqual(pinch.width2, 0)
            self.assertEqual(pinch.start_tile, ROOM)
            self.assertEqual(pinch.needs, {0x9000})
        self.assertEqual(sum(1 for d in decisions if d.width_cm == 0 and d.kept), 3)

    def test_touching_pinches_group_only_with_each_other(self):
        level = two_rooms(40, objects={0x9000: crate(0x9000, 0x1200, 300, 130, 40)})
        pinches, _, _ = find_pinches(level, include_touching=True)
        self.assertTrue(any(pinch.touching for pinch in pinches))
        self.assertTrue(any(not pinch.touching for pinch in pinches))
        for group in _group_pinches(level, pinches):
            self.assertEqual(len({pinch.touching for pinch in group}), 1)


class AWarpAlongASeam(unittest.TestCase):
    """A crate fills the mouth of a 40 cm corridor, its sides lying along the corridor's walls.
    Bond can step from room to room along either seam: 30 cm short of the crate at each end."""

    def setUp(self):
        self.level = two_rooms(40, objects={0x9000: crate(0x9000, 0x1200, 300, 130, 40)})
        pinches, _, _ = find_pinches(self.level, include_touching=True)
        self.seams = [
            Gap(id=i, pinches=group)
            for i, group in enumerate(_group_pinches(self.level, pinches))
            if group[0].touching
        ]

    def test_the_step(self):
        for gap in self.seams:
            _find_best_warp(self.level, gap)
            self.assertEqual(gap.status, WARP)
            self.assertAlmostEqual(float(gap.witness.step2) ** 0.5, 100.0, delta=0.01)

    def test_the_proposals_are_finite(self):
        pinch = next(pinch for gap in self.seams for pinch in gap.pinches if pinch.a == (320, 130))
        region = grow_box(bounding_box([pinch.a]), 330)
        walls = walls_near(self.level, pinch.start_tile, region, None)
        proposals = _propose(self.level, pinch, walls, 300.0)
        self.assertTrue(proposals)
        for proposal in proposals:
            for value in (proposal.step, proposal.back, proposal.forward, *proposal.direction):
                self.assertTrue(math.isfinite(value))


if __name__ == "__main__":
    unittest.main()
