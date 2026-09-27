from gaps.filters.groups import Expect, ObjectGroup
from gaps.filters.predicates import has_standard_health, is_door, is_generic, is_rectangle

IGNORE_OBJECTS = [
    ObjectGroup(
        name="ammo dump room objects",
        reason="The desks and boxes in the ammo dump which we don't go through",
        objects=[
            0x1EC278,
            0x1EC2F8,
            0x1EC378,
            0x1EC3F8,
            0x1ECD28,
            0x1ECDB8,
            0x1ECE48,
            0x1ECF60,
            0x1ECFF0,
            0x1ED080,
            0x1ED110,
            0x1ED1A0,
            0x1ED230,
            0x1ED2C0,
            0x1ED350,
            0x1ED3E0,
            0x1ED470,
            0x1ED500,
            0x1ED590,
            0x1ED620,
            0x1ED6B0,
        ],
        expect=Expect(
            count=21,
            room=0x42,
            all=[is_generic, is_rectangle, has_standard_health],
            none=[is_door],
            footprint_m2=(0.6, 1.2),
            max_spread_m=7.3,
        ),
    ),
]
