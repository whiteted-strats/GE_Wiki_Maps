import importlib
import unittest

from gaps.filters import (
    _ignored_object_verdict,
    apply_filters,
    ignored_groups,
    objects_to_remove,
)
from gaps.filters.generic import anvil_and_hammer
from gaps.filters.groups import (
    Expect,
    FilterFileError,
    ObjectGroup,
    check_group,
    footprint_m2,
)
from gaps.filters.pocket import narrow_pocket
from gaps.filters.predicates import is_crate, is_door, is_lying_flat, is_overhead, is_square
from gaps.mesh import OUTSIDE_WALKABLE_AREA, load_level
from gaps.pinch import find_pinches
from gaps.survey import NO_WARP_FOUND, Gap, survey_level
from gaps.tests.levels import build, crate, notched_room, room_with_a_slot, two_rooms


def pinches_under_the_notch(level):
    """The pinches between the near wall, which lies along z = 0, and the notch above it."""
    pinches, _, _ = find_pinches(level)
    return [pinch for pinch in pinches if 0 in (pinch.a[1], pinch.b[1])]


class AnvilAndHammer(unittest.TestCase):
    """In these rooms the near wall is the anvil. At its right hand end the wall always turns up
    into the room for 4 m: a protrusion far higher than any hammer here. `left_end` says what
    happens at its left hand end."""

    OUTSIDE_CORNER = -300

    def matches(self, level) -> list[bool]:
        pinches = pinches_under_the_notch(level)
        self.assertTrue(pinches)
        return [anvil_and_hammer(level, pinch) is not None for pinch in pinches]

    def test_a_corner_close_over_the_middle_of_a_long_wall(self):
        room = notched_room(1000, 500, 500, clearance=20, left_end=self.OUTSIDE_CORNER)
        self.assertTrue(all(self.matches(room)))

    def test_the_same_corner_near_an_end_with_no_protrusion_is_left_alone(self):
        # Only 1 m of wall to the left, and Bond can stand round the end of it and angle in
        room = notched_room(1000, 100, 100, clearance=20, left_end=self.OUTSIDE_CORNER)
        self.assertFalse(any(self.matches(room)))

    def test_with_a_high_protrusion_at_both_ends_it_is_caught_however_short_the_anvil(self):
        self.assertTrue(all(self.matches(notched_room(1000, 100, 100, clearance=20))))

    def test_a_protrusion_must_rise_at_least_as_far_as_the_hammer(self):
        self.assertTrue(all(self.matches(notched_room(1000, 100, 100, clearance=20, left_end=20))))
        self.assertFalse(any(self.matches(notched_room(1000, 100, 100, clearance=20, left_end=19))))

    def test_near_an_end_with_no_protrusion_it_is_caught_if_a_step_round_it_rises_too_slowly(self):
        # The corner is 1 m from the open end. A step brushing it rises 5 cm in that metre, so
        # takes 6 m to rise Bond's 30 cm: just long enough. At 6 cm it takes only 5 m.
        room = notched_room(1000, 100, 100, clearance=5, left_end=self.OUTSIDE_CORNER)
        self.assertTrue(all(self.matches(room)))
        room = notched_room(1000, 100, 100, clearance=6, left_end=self.OUTSIDE_CORNER)
        self.assertFalse(any(self.matches(room)))

    def test_a_step_under_the_corner_of_a_crate_must_pass_under_the_whole_hammer_head(self):
        # A crate 80 cm square, 8 cm from the near wall, its near corner 1 m from the end with no
        # protrusion. Brushing that corner alone a step would need 1 m x 30 / 8 = 3.75 m. But the
        # crate's long side is a hammer head reaching to 1.8 m, and passing that takes 6.75 m.
        room = notched_room(1000, 500, 500, clearance=200, left_end=self.OUTSIDE_CORNER)
        with_crate = build(
            {"room": room.tiles[0x1000].points}, {0x9000: crate(0x9000, 0x1000, 100, 8, 80)}
        )
        self.assertTrue(all(self.matches(with_crate)))
        # Nudged 35 cm nearer the end, its far end is at 1.45 m: 5.4 m, which isn't enough
        nearer = build(
            {"room": room.tiles[0x1000].points}, {0x9000: crate(0x9000, 0x1000, 65, 8, 80)}
        )
        self.assertFalse(any(self.matches(nearer)))

    def test_a_hammer_at_exactly_bonds_radius_can_be_passed_so_is_left_alone(self):
        self.assertFalse(any(self.matches(notched_room(1000, 500, 500, clearance=30))))
        self.assertTrue(all(self.matches(notched_room(1000, 500, 500, clearance=29))))

    def test_a_wall_in_several_pieces_is_one_anvil_if_they_are_in_line(self):
        # Three pieces of 3.3 m: no single piece has 3 m either side of the corner
        room = notched_room(1000, 500, 500, clearance=20, pieces=3, left_end=self.OUTSIDE_CORNER)
        self.assertTrue(all(self.matches(room)))

    def test_a_parallel_edge_is_measured_from_both_of_its_ends(self):
        # The flat end of the notch runs from 3.5 m to 4.5 m along the wall
        room = notched_room(1000, 350, 450, clearance=20, left_end=self.OUTSIDE_CORNER)
        self.assertTrue(all(self.matches(room)))
        # From 2.5 m to 3.5 m: 3 m of wall to the left of its middle, but only 2.5 m to the left
        # of its near end. The pinch with the flat end doesn't match, and a gap is only filtered
        # if all of its pinches do.
        room = notched_room(1000, 250, 350, clearance=20, left_end=self.OUTSIDE_CORNER)
        self.assertFalse(all(self.matches(room)))


class NarrowPocket(unittest.TestCase):
    def matches(self, level) -> list[bool]:
        pinches, _, _ = find_pinches(level)
        self.assertTrue(pinches)
        return [narrow_pocket(level, pinch) is not None for pinch in pinches]

    def test_a_dead_end_slot_narrower_than_bond(self):
        self.assertTrue(all(self.matches(room_with_a_slot(slot_width=50, slot_length=200))))

    def test_a_corridor_between_two_rooms_is_not_a_pocket(self):
        self.assertFalse(any(self.matches(two_rooms(corridor_width=50))))

    def test_a_slot_which_opens_into_a_chamber_bond_fits_in_is_not_a_pocket(self):
        level = room_with_a_slot(slot_width=50, slot_length=200, widens_to=80)
        self.assertFalse(any(self.matches(level)))

    def test_a_chamber_still_too_narrow_for_bond_is(self):
        level = room_with_a_slot(slot_width=40, slot_length=200, widens_to=58)
        self.assertTrue(all(self.matches(level)))


class IgnoredObjects(unittest.TestCase):
    def setUp(self):
        room = {"room": [(0, 0), (0, 600), (600, 600), (600, 0)]}
        objects = {
            0x9000: crate(0x9000, 0x1000, 100, 100, 80),
            0x9001: crate(0x9001, 0x1000, 220, 100, 80),  # 40 from the first
            0x9002: {**crate(0x9002, 0x1000, 100, 400, 80), "type": "monitor"},
        }
        self.level = build(room, objects)

    def group(self, objects, **expected) -> ObjectGroup:
        return ObjectGroup("test", "because", objects, Expect(**expected))

    def test_a_group_which_matches_its_description_passes(self):
        check_group(
            self.level,
            self.group([0x9000, 0x9001], count=2, room=1, all=[is_crate], max_spread_m=1.5),
        )

    def test_every_kind_of_mismatch_is_caught(self):
        wrong = {
            "2 objects are listed but 3 are expected": self.group([0x9000, 0x9001], count=3),
            "there is no object 0x9009": self.group([0x9000, 0x9009], count=2),
            "is in room 0x01, not 0x02": self.group([0x9000], count=1, room=2),
            "object 0x9002 fails is_crate": self.group([0x9000, 0x9002], count=2, all=[is_crate]),
            "1.20 m apart, more than 1.0 m": self.group(
                [0x9000, 0x9001], count=2, max_spread_m=1.0
            ),
            "listed twice": self.group([0x9000, 0x9000], count=2),
        }
        for message, group in wrong.items():
            with self.assertRaisesRegex(FilterFileError, message):
                check_group(self.level, group)

    def test_a_gap_is_filtered_only_if_an_ignored_object_forms_every_pinch_of_it(self):
        pinches, _, _ = find_pinches(self.level)
        between_crates = [pinch for pinch in pinches if pinch.needs == {0x9000, 0x9001}]
        self.assertTrue(between_crates)
        ignore_first = [self.group([0x9000], count=1)]
        ignore_monitor = [self.group([0x9002], count=1)]

        gap = Gap(id=0, pinches=between_crates, status=NO_WARP_FOUND)
        self.assertIsNotNone(_ignored_object_verdict(gap, ignore_first))
        self.assertIsNone(_ignored_object_verdict(gap, ignore_monitor))


class RemovedObjects(unittest.TestCase):
    """Removing is for objects which aren't really there. Unlike ignoring, it changes the level."""

    def setUp(self):
        self.room = {"room": [(0, 0), (0, 400), (400, 400), (400, 0)]}
        floating = crate(0x9000, 0x1000, 45, 180, 40)
        floating["height_range"] = (350.0, 550.0)  # the floor is at 0
        self.objects = {0x9000: floating}

    def test_an_object_knows_how_far_it_is_above_its_floor(self):
        level = build(self.room, self.objects)
        self.assertEqual(level.objects[0x9000].floor_clearance, 350.0)

    def test_a_removed_object_forms_no_gaps_and_is_recorded(self):
        as_dumped = build(self.room, self.objects)
        self.assertTrue(find_pinches(as_dumped)[0])

        level = build(self.room, self.objects, removed={0x9000: "hangs in the air"})
        self.assertEqual(find_pinches(level)[0], [])
        self.assertEqual(level.skipped_objects, [(0x9000, "generic", "hangs in the air")])

    def test_a_group_can_insist_that_its_objects_are_high_enough(self):
        level = build(self.room, self.objects)
        high_enough = ObjectGroup("x", "y", [0x9000], Expect(count=1, min_floor_clearance_m=3.0))
        too_demanding = ObjectGroup("x", "y", [0x9000], Expect(count=1, min_floor_clearance_m=4.0))
        check_group(level, high_enough)
        with self.assertRaisesRegex(FilterFileError, "3.50 m above its floor, less than 4.0 m"):
            check_group(level, too_demanding)


class ObjectsOutsideTheWalkableArea(unittest.TestCase):
    def test_an_object_beyond_the_wall_is_left_out_and_one_straddling_it_is_kept(self):
        room = {"room": [(0, 0), (0, 400), (400, 400), (400, 0)]}
        objects = {
            0x9000: crate(0x9000, 0x1000, 420, 100, 40),  # 20 beyond the wall
            0x9001: crate(0x9001, 0x1000, 380, 300, 40),  # half in, half out
        }
        level = build(room, objects)
        self.assertEqual(set(level.objects), {0x9001})
        self.assertEqual(level.skipped_objects, [(0x9000, "generic", OUTSIDE_WALKABLE_AREA)])


class RealLevels(unittest.TestCase):
    def test_the_frigate_crates_are_what_the_file_says_they_are(self):
        level = load_level("frigate", importlib.import_module("data.frigate"))
        groups = ignored_groups(level)
        self.assertEqual([len(group.objects) for group in groups], [9])
        for group in groups:
            check_group(level, group)
        self.assertTrue(all(is_square(level.objects[obj]) for obj in groups[0].objects))

    def test_frigates_floating_doors_are_the_only_overhead_doors_on_the_level(self):
        data = importlib.import_module("data.frigate")
        removed = objects_to_remove("frigate", data)  # also checks the group against the level
        level = load_level("frigate", data)
        overhead_doors = {
            a for a, obj in level.objects.items() if is_door(obj) and is_overhead(obj)
        }
        self.assertEqual(set(removed), overhead_doors)
        self.assertEqual(len(removed), 6)

    def test_silos_missile_bay_doors_are_its_only_doors_lying_flat_or_overhead(self):
        data = importlib.import_module("data.silo")
        removed = objects_to_remove("silo", data)  # also checks the group against the level
        level = load_level("silo", data)
        doors = {addr: obj for addr, obj in level.objects.items() if is_door(obj)}
        self.assertEqual(set(removed), {a for a, door in doors.items() if is_lying_flat(door)})
        self.assertEqual(set(removed), {a for a, door in doors.items() if is_overhead(door)})
        others = [footprint_m2(door) for addr, door in doors.items() if addr not in removed]
        self.assertLess(max(others), 1)  # every other door covers under a square metre

    def test_aztecs_doors_under_the_rocket_are_its_only_doors_lying_flat(self):
        data = importlib.import_module("data.aztec")
        removed = objects_to_remove("aztec", data)  # also checks the group against the level
        level = load_level("aztec", data)
        flat_doors = {a for a, obj in level.objects.items() if is_door(obj) and is_lying_flat(obj)}
        self.assertEqual(set(removed), flat_doors)

    def test_controls_overhead_glass_forms_no_gaps(self):
        """A pane lying flat 3 m over room 0x2e, which is at Bond's feet on the storey above. It was
        left in the level on the understanding that no gap involves it. If that changes, decide
        again."""
        level = load_level("control", importlib.import_module("data.control"))
        self.assertTrue(is_overhead(level.objects[0x1D7810]))
        pinches, _, _ = find_pinches(level)
        self.assertFalse([pinch for pinch in pinches if 0x1D7810 in pinch.needs])

    def test_statue(self):
        """The corner 26 cm from a wall 32 m long is filtered, and no filter claims that a gap with
        a warp through it can't be warped through."""
        survey = survey_level("statue")
        contradictions = apply_filters(survey.level, survey.gaps)
        self.assertEqual(contradictions, [])
        filtered = {gap.key: gap.filtered_by.filter_name for gap in survey.gaps if gap.filtered_by}
        self.assertEqual(filtered, {"142310.0 | 142510.1": "anvil and hammer"})


if __name__ == "__main__":
    unittest.main()
