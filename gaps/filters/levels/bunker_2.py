from gaps.filters.predicates import is_crate
from gaps.filters.suppressed import NearbyObject, SuppressedWarp
from gaps.survey import WARP

# The four crates in room 0x37. Nothing else is within 2 m of either warp.
CRATES_IN_ROOM_37 = [
    NearbyObject(0x1DEC64, all=[is_crate]),
    NearbyObject(0x1DED6C, all=[is_crate]),
    NearbyObject(0x1DEE74, all=[is_crate]),
    NearbyObject(0x1DEF7C, all=[is_crate]),
]

SUPPRESSED_WARPS = [
    SuppressedWarp(
        reason="Obvious: two crates 52.7 cm apart, 7 cm too close for Bond to walk between.",
        walls="0x1dec64.0 | 0x1def7c.2",
        status=WARP,
        width_cm=52.689,
        step_cm=28.7,
        nearby=CRATES_IN_ROOM_37,
    ),
    SuppressedWarp(
        reason="Obvious: the other two of the same four crates, the same 52.7 cm apart.",
        walls="0x1ded6c.0 | 0x1dee74.2",
        status=WARP,
        width_cm=52.688,
        step_cm=28.71,
        nearby=CRATES_IN_ROOM_37,
    ),
]
