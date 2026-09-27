from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import has_standard_health, is_glass

IGNORE_OBJECTS = [
    ObjectGroup(
        name="top floor glass",
        reason="All the glass on the top floor.",
        objects=[
            0x1D8298,
            0x1D832C,
            0x1D83C0,
            0x1D8454,
            0x1D84E8,
            0x1D857C,
            0x1D8610,
            0x1D86A4,
            0x1D8738,
        ],
        expect=Expect(
            count=9,
            room={0x22, 0x36, 0x37, 0x38, 0x3D, 0x3E, 0x42, 0x43, 0x44},
            all=[is_glass, has_standard_health],
            footprint_m2=(0.0, 0.2),
            max_spread_m=26.9,
        ),
    ),
]
