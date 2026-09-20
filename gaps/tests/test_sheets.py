import unittest

from gaps.exact import overlap_point, polygons_overlap
from gaps.tests.levels import build

SQUARE = [(0, 0), (10, 0), (10, 10), (0, 10)]

# Five tiles linked in a ring, the last of which comes round over the first
RING = {
    "start": [(0, 0), (10, 0), (10, 9), (0, 9)],
    "east": [(10, 0), (20, 0), (20, 9), (10, 9)],
    "north east": [(10, 9), (20, 9), (20, 20), (10, 20), (10, 10)],
    "north": [(0, 10), (10, 10), (10, 20), (0, 20)],
    "over the start": [(0, 1), (10, 1), (10, 10), (0, 10)],
}
EVERYWHERE = (-100, 100, -100, 100)


class PolygonsOverlap(unittest.TestCase):
    def test_sharing_area(self):
        self.assertTrue(polygons_overlap(SQUARE, [(5, 5), (15, 5), (15, 15), (5, 15)]))
        self.assertTrue(polygons_overlap(SQUARE, SQUARE))
        self.assertTrue(polygons_overlap(SQUARE, [(2, 2), (4, 2), (4, 4)]))  # one inside the other
        self.assertTrue(polygons_overlap(SQUARE, [(5, -5), (15, 5), (5, 15), (-5, 5)]))

    def test_only_touching(self):
        self.assertFalse(polygons_overlap(SQUARE, [(10, 0), (20, 0), (20, 10), (10, 10)]))  # edge
        self.assertFalse(
            polygons_overlap(SQUARE, [(10, 10), (20, 10), (20, 20), (10, 20)])
        )  # corner

    def test_the_notch_of_a_non_convex_polygon_is_not_part_of_it(self):
        l_shape = [(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)]
        self.assertFalse(polygons_overlap(l_shape, [(5, 5), (9, 5), (9, 9), (5, 9)]))

    def test_only_area_inside_the_box_counts(self):
        shifted = [(5, 5), (15, 5), (15, 15), (5, 15)]
        self.assertFalse(polygons_overlap(SQUARE, shifted, within=(0, 4, 0, 4)))
        self.assertTrue(polygons_overlap(SQUARE, shifted, within=(4, 8, 4, 8)))
        self.assertTrue(polygons_overlap(SQUARE, SQUARE, within=(2, 3, 2, 3)))  # box inside both

    def test_the_point_given_is_in_both(self):
        self.assertEqual(overlap_point(SQUARE, [(2, 2), (4, 2), (4, 4)]), (3, 2))


class ASheetDoesNotLieOverItself(unittest.TestCase):
    def nearby(self, heights):
        level = build(RING, heights=heights)
        names = {tile.addr: name for name, tile in zip(RING, level.tiles.values(), strict=True)}
        start = next(addr for addr, name in names.items() if name == "start")
        return {names[addr] for addr in level.linked_tiles_within(start, EVERYWHERE)}

    def test_another_storey_is_left_out(self):
        climbing = {"north east": 100, "north": 200, "over the start": 300}
        self.assertEqual(self.nearby(climbing), set(RING) - {"over the start"})

    def test_the_same_floor_drawn_twice_is_kept(self):
        self.assertEqual(self.nearby({}), set(RING))


if __name__ == "__main__":
    unittest.main()
