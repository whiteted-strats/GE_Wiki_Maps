from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import (
    has_standard_health,
    is_axis_aligned,
    is_door,
    is_generic,
    is_glass,
    is_lying_flat,
    is_overhead,
    is_rectangle,
)

IGNORE_OBJECTS = [
    ObjectGroup(
        name="table in the trap room",
        reason="The big table which Bond gets 'trapped' at. The chairs round it and the monitors "
        "on it each leave a gap against it, none of any use. (The chairs are doors in the data, as "
        "is the table itself: that is how they were animated.)",
        objects=[0x1E7314],
        expect=Expect(count=1, room=0x22, all=[is_door], footprint_m2=(18.2, 18.3)),
    ),
    ObjectGroup(
        name="room behind glass",
        reason="Everything in the room behind glass, except the glass itself. We call this the "
        "glass, but they are probably actually doors.",
        objects=[0x1E896C, 0x1E8B6C, 0x1E8BFC, 0x1E8C7C],
        expect=Expect(
            count=4,
            room=0x12,
            all=[is_generic, is_rectangle, has_standard_health],
            none=[is_door, is_axis_aligned],
            footprint_m2=(0.0, 1.5),
            max_spread_m=3.6,
        ),
    ),
]

REMOVE_OBJECTS = [
    ObjectGroup(
        name="doors under the rocket",
        reason="The pair of doors between the rocket above and the table room below, which Bond "
        "gets 'trapped' in. Each is a slab 4 m by 9.6 m lying flat, 3 m over his head there.",
        objects=[0x1E7104, 0x1E7204],
        expect=Expect(
            count=2,
            room=0x22,
            all=[is_door, is_overhead, is_lying_flat],
            min_floor_clearance_m=3.0,
            footprint_m2=(38.8, 39.0),
            max_spread_m=4.4,
        ),
    ),
    ObjectGroup(
        name="overhead black room glass",
        reason="The upper pane of the black room's glass, 3.4 m over Bond's head.",
        objects=[0x1E8EDC],
        expect=Expect(
            count=1,
            room=0x3E,
            all=[is_glass, is_overhead],
            min_floor_clearance_m=3.4,
            footprint_m2=(0.1, 0.2),
        ),
    ),
]
