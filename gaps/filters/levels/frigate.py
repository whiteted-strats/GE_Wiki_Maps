from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import (
    has_standard_health,
    is_axis_aligned,
    is_crate,
    is_door,
    is_generic,
    is_overhead,
    is_rectangle,
    is_z_axis_aligned,
)

IGNORE_OBJECTS = [
    ObjectGroup(
        name="pipes room crates",
        reason="Nine crates stacked together by the pipes. Squeezing between them leads nowhere.",
        objects=[
            0x1E990C,
            0x1E998C,  # underneath 0x1E9F34
            0x1E9A94,
            0x1E9B9C,
            0x1E9CA4,
            0x1E9DAC,  # underneath 0x1EA03C
            0x1E9E2C,
            0x1E9F34,
            0x1EA03C,  # the rotated one
        ],
        expect=Expect(count=9, room=0x10, all=[is_crate], max_spread_m=2.8),
    ),
    ObjectGroup(
        name="room 0x05",
        reason="Everything in the room off of the bridge",
        objects=[
            0x1E978C,
            0x1E980C,
            0x1E988C,
            0x1EA144,
            0x1EA1C4,
            0x1EA444,
            0x1EA4C4,
            0x1EA544,
            0x1EA5C4,
            0x1EA644,
            0x1EA6C4,
        ],
        expect=Expect(count=11, room=0x05, none=[is_door]),
    ),
    ObjectGroup(
        name="agent area irrelevant chairs",
        reason="Three of the four chairs in the agent area. The one we pass has been left, since "
        "we do come close to it in runs.",
        objects=[0x1EA244, 0x1EA344, 0x1EA3C4],
        expect=Expect(
            count=3,
            room={0x09, 0x0A},
            all=[is_generic, is_rectangle, has_standard_health],
            none=[is_axis_aligned],
            footprint_m2=(0.5, 0.6),
            max_spread_m=10.3,
        ),
    ),
    ObjectGroup(
        name="back row agent area consoles",
        reason="The four consoles in the back row of the agent area.",
        objects=[0x1E8B0C, 0x1E8B8C, 0x1E908C, 0x1E910C],
        expect=Expect(
            count=4,
            room=0x0A,
            all=[is_generic, is_rectangle, is_z_axis_aligned, has_standard_health],
            footprint_m2=(0.7, 0.8),
            max_spread_m=2.4,
        ),
    ),
]

REMOVE_OBJECTS = [
    ObjectGroup(
        name="floating doors",
        reason="Doors attached to the room below the one they are drawn in, so they hang in the "
        "air well above Bond's head. The theory is that they were taken out late in development.",
        objects=[
            0x1EACC0,  # 4.05 m above its floor
            0x1EADC0,  # 4.05 m
            0x1EB0C0,  # 4.05 m
            0x1EBBC0,  # 6.53 m
            0x1EBCC0,  # 4.05 m
            0x1EBDC0,  # 3.42 m
        ],
        expect=Expect(count=6, all=[is_door, is_overhead], min_floor_clearance_m=3.4),
    ),
]
