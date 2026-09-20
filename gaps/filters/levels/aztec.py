from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import is_door, is_lying_flat, is_overhead

IGNORE_OBJECTS = [
    ObjectGroup(
        name="table in the trap room",
        reason="The big table which Bond gets 'trapped' at. The chairs round it and the monitors "
        "on it each leave a gap against it, none of any use. (The chairs are doors in the data, as "
        "is the table itself: that is how they were animated.)",
        objects=[0x1E7314],
        expect=Expect(count=1, room=0x22, all=[is_door], footprint_m2=(18.2, 18.3)),
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
]
