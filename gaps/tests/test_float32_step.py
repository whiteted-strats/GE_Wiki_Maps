import unittest
from fractions import Fraction

from gaps.mesh import float32_step, nearest_float32
from gaps.pinch import find_pinches
from gaps.tests.levels import build, crate

ROOM = {"room": [(0, 0), (0, 300), (300, 300), (300, 0)]}


def pinches_of(level):
    return find_pinches(level)[0]


class OneFloat32Step(unittest.TestCase):
    def test_the_step_size(self):
        self.assertEqual(float32_step(Fraction(100)), Fraction(2) ** -17)
        self.assertEqual(float32_step(Fraction(1100)), Fraction(2) ** -13)
        self.assertEqual(
            nearest_float32(Fraction(100) + Fraction(2) ** -17), Fraction(100) + Fraction(2) ** -17
        )

    def test_a_crate_one_step_from_the_wall_is_picked_out(self):
        step = float(float32_step(Fraction(300)))
        level = build(ROOM, {0x9000: crate(0x9000, 0x1000, 300 - 50 - step, 100, 50)})
        pinch = min(pinches_of(level), key=lambda pinch: pinch.width2)
        self.assertEqual(pinch.width2, float32_step(Fraction(300)) ** 2)
        self.assertTrue(pinch.one_float32_step)

    def test_two_steps_or_a_rotation_are_not(self):
        step = float(float32_step(Fraction(300)))
        level = build(ROOM, {0x9000: crate(0x9000, 0x1000, 300 - 50 - 2 * step, 100, 50)})
        self.assertFalse(min(pinches_of(level), key=lambda p: p.width2).one_float32_step)
        leaning = crate(0x9000, 0x1000, 300 - 50 - step, 100, 50)
        x0 = (
            300 - 50 - step
        )  # turned a little about its near bottom corner: no edge stays axis-aligned
        leaning["points"] = [
            (x - (z - 100) * 1e-4, z + (x - x0) * 1e-4) for x, z in leaning["points"]
        ]
        level = build(ROOM, {0x9000: leaning})
        self.assertFalse(min(pinches_of(level), key=lambda p: p.width2).one_float32_step)


if __name__ == "__main__":
    unittest.main()
