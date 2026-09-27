from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import is_axis_aligned, is_crate, is_door

IGNORE_OBJECTS = [
    ObjectGroup(
        name="satellite room crate",
        reason="The crate in the satellite room. It doesn't interfere with the objective.",
        objects=[0x1EB430],
        expect=Expect(count=1, room=0x1F, all=[is_crate], footprint_m2=(0.7, 0.8)),
    ),
    ObjectGroup(
        name="huts",
        reason="3 huts which we don't go in. One houses the fence cam, the second is opposite the "
        "first, and the last is in the compound.",
        objects=[
            # room 0x1b
            0x1EA600,
            0x1EA680,
            0x1EA780,
            0x1EA800,
            0x1EA880,
            # room 0x1c
            0x1EA34C,
            0x1EA3CC,
            0x1EA480,
            0x1EA500,
            0x1EA580,
            # room 0x1d
            0x1EAC10,
            0x1EAF40,
            0x1EAFC0,
            0x1EB4B0,
        ],
        expect=Expect(count=14, none=[is_door]),
    ),
    ObjectGroup(
        name="compound crate pair",
        reason="Two crates side by side in the compound.",
        objects=[0x1EB530, 0x1EB5B0],
        expect=Expect(
            count=2, room=0x10, all=[is_crate], footprint_m2=(0.6, 0.8), max_spread_m=1.2
        ),
    ),
    ObjectGroup(
        name="compound crate triplet",
        reason="Three crates together in the compound.",
        objects=[0x1EB630, 0x1EB6B0, 0x1EB730],
        expect=Expect(
            count=3, room=0x10, all=[is_crate], footprint_m2=(0.6, 0.9), max_spread_m=1.4
        ),
    ),
    ObjectGroup(
        name="cutscene glass door",
        reason="The six pieces of the glass door from the cutscene.",
        objects=[0x1EC5C0, 0x1EC6C0, 0x1EC7C0, 0x1EC8C0, 0x1EC9C0, 0x1ECAC0],
        expect=Expect(
            count=6,
            room=0x24,
            all=[is_door, is_axis_aligned],
            footprint_m2=(0.08, 0.10),
            max_spread_m=2.4,
        ),
    ),
]
