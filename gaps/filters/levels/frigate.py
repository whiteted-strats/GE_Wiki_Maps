from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import is_crate, is_door, is_overhead

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
