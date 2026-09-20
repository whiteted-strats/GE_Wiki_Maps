"""Checks against real levels that nothing slips through the first stage of the survey."""

import importlib
import unittest

from gaps.exact import closest_points_between_segments, dist2
from gaps.mesh import Level, SegmentGrid, load_level
from gaps.pinch import _are_neighbours, find_pinches


def load(name: str) -> Level:
    return load_level(name, importlib.import_module(f"data.{name}"))


class NothingIsMissed(unittest.TestCase):
    def test_the_grid_finds_every_close_pair_of_walls(self):
        """Compares the grid's shortlist against simply measuring every pair of walls."""
        level = load("runway")
        diameter2 = (2 * level.bond_radius) ** 2
        shortlisted = SegmentGrid(level.segments, level.bond_radius).nearby_pairs()

        for i, first in enumerate(level.segments):
            for second in level.segments[i + 1 :]:
                gap2, _, _ = closest_points_between_segments(first.a, first.b, second.a, second.b)
                if gap2 < diameter2:
                    self.assertIn((first.id, second.id), shortlisted)

    def test_every_narrow_doorway_is_examined(self):
        """A quite separate way of spotting gaps: an edge which two tiles are linked across, which
        is shorter than Bond is wide and has a wall corner at each end. The survey must have
        looked at the walls either side of every one, whatever it then decided."""
        level = load("train")
        _, _, decisions = find_pinches(level)
        examined = {frozenset((decision.first, decision.second)) for decision in decisions}
        diameter2 = (2 * level.bond_radius) ** 2

        walls_at_corner: dict = {}
        for wall in level.segments:
            if wall.tile is not None:
                for corner in (wall.a, wall.b):
                    walls_at_corner.setdefault(corner, []).append(wall)

        doorways = 0
        for tile in level.tiles.values():
            for i, neighbour in enumerate(tile.links):
                a, b = tile.edge(i)
                is_doorway = neighbour != 0 and 0 < dist2(a, b) < diameter2
                if not (is_doorway and a in walls_at_corner and b in walls_at_corner):
                    continue
                doorways += 1
                pairs = [
                    (first, second)
                    for first in walls_at_corner[a]
                    for second in walls_at_corner[b]
                    if first.id != second.id and not _are_neighbours(first, second)
                ]
                self.assertTrue(
                    any(frozenset((first.id, second.id)) in examined for first, second in pairs),
                    f"the doorway {a} - {b} of tile {tile.name:06X} was never examined",
                )
        self.assertGreater(doorways, 0)


if __name__ == "__main__":
    unittest.main()
