from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import is_crate

IGNORE_OBJECTS = [
    ObjectGroup(
        name="clipboard room crates",
        reason="The eight crates in the clipboard room. The 2 warps among these crates are wide "
        "and apparent.",
        objects=[
            0x1DEA54,
            0x1DEB5C,
            0x1DEC64,
            0x1DED6C,
            0x1DEE74,
            0x1DEF7C,
            0x1DF084,
            0x1DF18C,
        ],
        expect=Expect(
            count=8, room=0x37, all=[is_crate], footprint_m2=(0.7, 0.8), max_spread_m=8.3
        ),
    ),
]
