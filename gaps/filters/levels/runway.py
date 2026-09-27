from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import is_crate

IGNORE_OBJECTS = [
    ObjectGroup(
        name="crate by the wall",
        reason="A crate against the wall of the first room.",
        objects=[0x1DAF9C],
        expect=Expect(count=1, room=0x01, all=[is_crate], footprint_m2=(1.3, 1.4)),
    ),
]
