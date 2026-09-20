import unittest
from fractions import Fraction

from gaps.exact import (
    closest_points_between_segments,
    contact_interval,
    is_convex,
    point_in_polygon,
    segment_inside_polygon,
)

SQUARE = [(0, 0), (0, 10), (10, 10), (10, 0)]
L_SHAPE = [(0, 0), (0, 10), (4, 10), (4, 4), (10, 4), (10, 0)]  # not convex
VERTICAL_TILE = [(0, 0), (10, 0), (10, 0), (0, 0)]  # no area from above


class ContactInterval(unittest.TestCase):
    def test_crossing(self):
        self.assertEqual(contact_interval((0, 0), (10, 0), (5, -5), (5, 5)), (Fraction(1, 2),) * 2)

    def test_touching_at_an_end(self):
        self.assertEqual(contact_interval((0, 0), (10, 0), (10, 0), (10, 5)), (1, 1))

    def test_missing(self):
        self.assertIsNone(contact_interval((0, 0), (10, 0), (11, -5), (11, 5)))

    def test_parallel_but_apart(self):
        self.assertIsNone(contact_interval((0, 0), (10, 0), (0, 1), (10, 1)))

    def test_overlapping_on_the_same_line(self):
        self.assertEqual(contact_interval((0, 0), (10, 0), (5, 0), (20, 0)), (Fraction(1, 2), 1))


class ClosestPoints(unittest.TestCase):
    def test_parallel_walls(self):
        width2, _, _ = closest_points_between_segments((0, 0), (10, 0), (0, 7), (10, 7))
        self.assertEqual(width2, 49)

    def test_parallel_walls_are_measured_across_the_middle_of_where_they_overlap(self):
        _, on_a, on_b = closest_points_between_segments((0, 0), (10, 0), (4, 7), (30, 7))
        self.assertEqual((on_a, on_b), ((7, 0), (7, 7)))

    def test_corner_to_wall(self):
        width2, on_a, on_b = closest_points_between_segments((0, 0), (10, 0), (5, 3), (5, 9))
        self.assertEqual((width2, on_a, on_b), (9, (5, 0), (5, 3)))

    def test_crossing_walls_touch(self):
        self.assertEqual(closest_points_between_segments((0, 0), (10, 10), (0, 10), (10, 0))[0], 0)


class Convex(unittest.TestCase):
    def test_a_square_is_and_an_l_shape_is_not(self):
        self.assertTrue(is_convex(SQUARE))
        self.assertFalse(is_convex(L_SHAPE))

    def test_repeated_and_in_line_corners_are_allowed(self):
        self.assertTrue(is_convex([(0, 0), (0, 0), (0, 5), (0, 10), (10, 10), (10, 0)]))


class InsidePolygon(unittest.TestCase):
    def test_edges_count_as_inside(self):
        self.assertTrue(point_in_polygon((0, 5), SQUARE))
        self.assertTrue(point_in_polygon((5, 5), SQUARE))
        self.assertFalse(point_in_polygon((11, 5), SQUARE))

    def test_notch_of_a_non_convex_tile_is_outside(self):
        self.assertFalse(point_in_polygon((7, 7), L_SHAPE))
        self.assertTrue(point_in_polygon((2, 7), L_SHAPE))

    def test_a_vertical_tile_contains_only_its_own_line(self):
        self.assertTrue(point_in_polygon((5, 0), VERTICAL_TILE))
        self.assertFalse(point_in_polygon((5, 1), VERTICAL_TILE))

    def test_segment_leaving_and_reentering_a_non_convex_tile(self):
        # Runs along z = 7: inside until x = 4, then in the notch
        self.assertEqual(segment_inside_polygon((0, 7), (10, 7), L_SHAPE), [(0, Fraction(2, 5))])

    def test_segment_crossing_a_vertical_tile_touches_it_at_one_point(self):
        self.assertEqual(
            segment_inside_polygon((5, -5), (5, 5), VERTICAL_TILE), [(Fraction(1, 2),) * 2]
        )


if __name__ == "__main__":
    unittest.main()
