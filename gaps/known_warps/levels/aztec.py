from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="black room boxes warp",
        walls="001D2A.1 | 0x1e9f80.0",
        status=WARP,
        width_cm=36.327,
        step_cm=170.14,
        objects_forming_gap=[0x1E9F80],
        notes="The black room, room 0x3d. Two boxes each leave a gap against a wall and one step "
        "passes both. The gap at the other box, 000429.3 | 0x1e9f00.0, is its variant.",
    ),
]
