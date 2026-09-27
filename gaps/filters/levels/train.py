from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import (
    has_standard_health,
    is_crate,
    is_door,
    is_generic,
    is_rectangle,
    is_x_axis_aligned,
)

IGNORE_OBJECTS = [
    ObjectGroup(
        name="compartment doors",
        reason="The doors of the small compartments off the two corridors: nine along each, 2.6 m "
        "apart. The compartments only contain guards, and are nothing we want to enter. Each door "
        "sits one float32 step off its frame, or on it.",
        objects=[
            # The first corridor: rooms 0x1a, 0x19 and 0x18, doors 13.3 cm thick
            0x1CA6BC,
            0x1CA7BC,
            0x1CA8CC,
            0x1CA9CC,
            0x1CAACC,
            0x1CABDC,
            0x1CACDC,
            0x1CADDC,
            0x1CAEEC,
            # The second corridor: rooms 0x29, 0x28 and 0x27, doors 6.7 cm thick
            0x1CB1EC,
            0x1CB2FC,
            0x1CB3FC,
            0x1CB4FC,
            0x1CB5FC,
            0x1CB70C,
            0x1CB80C,
            0x1CB90C,
            0x1CBA0C,
        ],
        expect=Expect(
            count=18,
            room={0x18, 0x19, 0x1A, 0x27, 0x28, 0x29},
            all=[is_door, is_x_axis_aligned],
            footprint_m2=(0.05, 0.12),  # 86.6 or 93.2 cm by 6.7 or 13.3 cm
        ),
    ),
    ObjectGroup(
        name="brakes",
        reason="The six brakes, one to a carriage, each a small block against a wall. Nothing is "
        "behind them.",
        objects=[
            0x1C51B0,  # room 0x05
            0x1C5240,  # room 0x0b
            0x1C52D0,  # room 0x17
            0x1C5360,  # room 0x1c
            0x1C53F0,  # room 0x2b
            0x1C5480,  # room 0x31
        ],
        expect=Expect(
            count=6,
            room={0x05, 0x0B, 0x17, 0x1C, 0x2B, 0x31},
            all=[is_generic, is_rectangle, has_standard_health],
            footprint_m2=(0.08, 0.10),  # 20.9 by 41.8 cm
        ),
    ),
    ObjectGroup(
        name="crates outside",
        reason="The nine crates outside, after the train warp. Five are square boxes about 1.2 m "
        "across; the other four are boxes on their sides, whose outlines from above are hexagons.",
        objects=[
            0x1C4D20,
            0x1C4DA0,
            0x1C4E20,
            0x1C4EA0,
            0x1C4F20,
            0x1C4FA0,
            0x1C5020,
            0x1C50A0,
            0x1C5120,
        ],
        expect=Expect(
            count=9,
            room=0x35,
            all=[is_generic, has_standard_health],
            footprint_m2=(1.4, 2.0),
            max_spread_m=14.8,
        ),
    ),
    ObjectGroup(
        name="crates behind the start point",
        reason="Five crates behind where Bond starts, at the far end of the train from everything.",
        objects=[
            0x1C3390,
            0x1C3410,
            0x1C3490,
            0x1C3510,
            0x1C3590,
        ],
        expect=Expect(
            count=5,
            room={0x01, 0x02},
            all=[is_crate],
            footprint_m2=(1.2, 1.6),
            max_spread_m=3.9,
        ),
    ),
]
