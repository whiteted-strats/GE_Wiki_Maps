from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import is_axis_aligned, is_door, is_rectangle

IGNORE_OBJECTS = [
    ObjectGroup(
        name="golden gun room gun walls",
        reason="The walls surrounding the autoguns in the golden gun room.",
        objects=[
            0x1CECB8,
            0x1CEDB8,
            0x1CEEB8,
            0x1CEFB8,
            0x1CF0B8,
            0x1CF1B8,
            0x1CF2B8,
            0x1CF3B8,
            0x1CF4B8,
            0x1CF5B8,
        ],
        expect=Expect(
            count=10,
            room=0x13,
            all=[is_door, is_rectangle, is_axis_aligned],
            footprint_m2=(0.8, 1.1),
            max_spread_m=13.7,
        ),
    ),
]
