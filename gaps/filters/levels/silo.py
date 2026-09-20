from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import is_door, is_lying_flat, is_overhead

REMOVE_OBJECTS = [
    ObjectGroup(
        name="missile bay doors",
        reason="The doors of the missile bays, high above the level: an easter egg. Each is a slab "
        "4.2 m by 8.4 m and 25 cm thick, lying flat between 6 m and 10.5 m over Bond's head.",
        objects=[
            0x1CB09C,  # room 0x06, 5.95 m above its floor. One half of a pair with the next
            0x1CB19C,
            0x1CB2AC,  # room 0x0c, 10.47 m
            0x1CB3AC,
            0x1CB6CC,  # room 0x1e, 5.95 m
            0x1CB7CC,
            # The fourth pair, 0x1CB4BC and 0x1CB5BC, is attached to a tile which is not in the
            # data, so it is already left out of the level: see objects_left_out.csv
        ],
        expect=Expect(
            count=6,
            all=[is_door, is_overhead, is_lying_flat],
            min_floor_clearance_m=5.9,
            footprint_m2=(35.1, 35.5),
        ),
    ),
]
