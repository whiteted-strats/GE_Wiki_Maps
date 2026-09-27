from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import (
    has_standard_health,
    is_crate,
    is_door,
    is_generic,
    is_glass,
    is_rectangle,
)

IGNORE_OBJECTS = [
    ObjectGroup(
        name="dead end crate",
        reason="The crate in a dead end which a guard guards for some unknown reason.",
        objects=[0x1CE7FC],
        expect=Expect(count=1, room=0x18, all=[is_crate], footprint_m2=(0.8, 0.9)),
    ),
    ObjectGroup(
        name="dead end 2, crates 3",
        reason="We never go down here.",
        objects=[0x1CE97C, 0x1CE9FC, 0x1CEA7C],
        expect=Expect(
            count=3,
            room={0x0D, 0x0E},
            all=[is_crate],
            footprint_m2=(0.7, 0.8),
            max_spread_m=5.7,
        ),
    ),
    ObjectGroup(
        name="raised room behind glass",
        reason="These are the contents of the raised room off the main room, excluding the glass."
        "It has a camera in it which we destroy, but we don't enter it.",
        objects=[0x1CE67C, 0x1CE87C, 0x1CE8FC],
        expect=Expect(
            count=3,
            room=0x08,
            all=[is_generic, is_rectangle, has_standard_health],
            none=[is_door, is_glass],
            footprint_m2=(0.7, 1.4),
            max_spread_m=3.2,
        ),
    ),
]
