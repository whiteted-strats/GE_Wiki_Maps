from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import is_crate, is_door

IGNORE_OBJECTS = [
    ObjectGroup(
        name="huts",
        reason="3 huts which we don't go in. One houses the fence cam, the second is opposite the "
        "first, and the last is in the compound.",
        objects=[
            # room 0x1b
            0x1DB794,
            0x1DB814,
            0x1DB894,
            0x1DB914,
            0x1DB994,
            0x1DBA14,
            0x1DBA94,
            0x1DBD14,
            0x1DBD94,
            # room 0x1c
            0x1DBEC8,
            0x1DBF48,
            0x1DBFC8,
            0x1DC048,
            0x1DC0C8,
            0x1DC148,
            # room 0x1d
            0x1DD0C8,
            0x1DD148,
            0x1DD7C8,
            0x1DD848,
        ],
        expect=Expect(count=19, none=[is_door]),
    ),
    ObjectGroup(
        name="compound crate triplet",
        reason="Three crates together in the compound.",
        objects=[0x1DD348, 0x1DD3C8, 0x1DD448],
        expect=Expect(
            count=3, room=0x10, all=[is_crate], footprint_m2=(0.4, 0.5), max_spread_m=1.4
        ),
    ),
    ObjectGroup(
        name="compound crates, group of 8",
        reason="Eight crates together in the compound.",
        objects=[
            0x1DCAC8,
            0x1DCB48,
            0x1DCBC8,
            0x1DCC48,
            0x1DCEC8,
            0x1DCF48,
            0x1DCFC8,
            0x1DD048,
        ],
        expect=Expect(
            count=8, room=0x10, all=[is_crate], footprint_m2=(0.7, 0.8), max_spread_m=5.0
        ),
    ),
    ObjectGroup(
        name="compound crates, group of 7",
        reason="Seven crates together in the compound.",
        objects=[
            0x1DCCC8,
            0x1DCD48,
            0x1DCDC8,
            0x1DCE48,
            0x1DD1C8,
            0x1DD248,
            0x1DD2C8,
        ],
        expect=Expect(
            count=7, room=0x10, all=[is_crate], footprint_m2=(0.4, 0.8), max_spread_m=3.9
        ),
    ),
    ObjectGroup(
        name="early hut containing crates",
        reason="The early hut containing crates.",
        objects=[0x1DDEE8, 0x1DDF68, 0x1DDFE8, 0x1DE068, 0x1DE0E8, 0x1DE168],
        expect=Expect(
            count=6, room=0x18, all=[is_crate], footprint_m2=(0.9, 1.1), max_spread_m=4.0
        ),
    ),
    ObjectGroup(
        name="observatory crates",
        reason="The three crates in the observatory.",
        objects=[0x1DD648, 0x1DD6C8, 0x1DD748],
        expect=Expect(
            count=3, room=0x07, all=[is_crate], footprint_m2=(0.4, 0.5), max_spread_m=1.4
        ),
    ),
]
