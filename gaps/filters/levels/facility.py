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
        name="room left of the decoder door",
        reason="Only for the one-guard-decoder-door-lure (OGDDL) do we go in here, and the "
        "warps strictly within the room aren't relevant. These are all tables.",
        objects=[0x1CBED0, 0x1CBF50, 0x1CBFD0],
        expect=Expect(
            count=3,
            room=0x3E,
            all=[is_generic, is_rectangle, has_standard_health],
            none=[is_door],
            footprint_m2=(4.4, 4.5),
            max_spread_m=9.1,
        ),
    ),
    ObjectGroup(
        name="bathroom stall doors",
        reason="The doors of the bathroom stalls. We have explicitly excluded the one which we "
        "exit through.",
        objects=[
            0x1C640C,
            0x1C650C,
            0x1C670C,
            0x1C680C,
            0x1C690C,
            0x1C6A0C,
            0x1C6B0C,
            0x1C6C0C,
        ],
        expect=Expect(
            count=8,
            room=0x0C,
            all=[is_door, is_x_axis_aligned],
            footprint_m2=(0.1, 0.2),
            max_spread_m=9.0,
        ),
    ),
    ObjectGroup(
        name="start upstairs crates",
        reason="The pair of crates upstairs at the start.",
        objects=[0x1CB5B4, 0x1CB6BC],
        expect=Expect(
            count=2, room=0x06, all=[is_crate], footprint_m2=(0.7, 1.1), max_spread_m=0.2
        ),
    ),
    ObjectGroup(
        name="crates at the foot of the start stairs",
        reason="We certainly go around these",
        objects=[0x1CB1A0, 0x1CB2A8, 0x1CB3AC],
        expect=Expect(
            count=3, room=0x08, all=[is_crate], footprint_m2=(0.4, 0.9), max_spread_m=1.0
        ),
    ),
    ObjectGroup(
        name="objective A area crates",
        reason="These are beyond the stairs which we of course take",
        objects=[0x1CAA74, 0x1CAB7C, 0x1CAC84, 0x1CAD8C, 0x1CAE90, 0x1CAF94, 0x1CB098],
        expect=Expect(
            count=7, room=0x31, all=[is_crate], footprint_m2=(0.7, 1.1), max_spread_m=3.3
        ),
    ),
    ObjectGroup(
        name="bottling room",
        reason="Everything in the bottling room, which we don't go near even in RTA",
        objects=[
            0x1CB950,
            0x1CB9E0,
            0x1CBA70,
            0x1CBB00,
            0x1CBB90,
            0x1CBC20,
            0x1CBCB0,
            0x1CBD40,
            0x1CBDD0,
            0x1CDF90,
            0x1CE010,
            0x1CE0A0,
            0x1CE1A0,
            0x1CE220,
            0x1CE2A0,
            0x1CE330,
            0x1CE430,
            0x1CE4B0,
            0x1CE540,
            0x1CE640,
            0x1CE6C0,
            0x1CE750,
            0x1CE850,
            0x1CE8D0,
            0x1CE960,
        ],
        expect=Expect(count=25, room={0x2C, 0x2D, 0x2E, 0x2F}, none=[is_door]),
    ),
    ObjectGroup(
        name="objective a door control room",
        reason="This is the room containing the console to open the objective A door. "
        "We lure this door open instead.",
        objects=[0x1C82BC, 0x1C8624, 0x1CC3D0, 0x1CC450, 0x1CC550, 0x1CC5D0],
        expect=Expect(count=6, room=0x28, none=[is_door]),
    ),
    ObjectGroup(
        name="side room downstairs in the start",
        reason="On the right just after we leave the console room and head onwards in the level.",
        objects=[0x1CB7C0, 0x1CB840, 0x1CB8C0, 0x1CC6D0],
        expect=Expect(count=4, room=0x04, all=[is_generic], none=[is_door]),
    ),
]
