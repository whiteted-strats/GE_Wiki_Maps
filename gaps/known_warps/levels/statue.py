from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="secret area in",
        walls="0C2408.2 | 0C5008.1",
        status=WARP,
        width_cm=28.459,
        step_cm=117.40,
        notes="Room 0x0f, between two tile walls.",
    ),
    KnownWarp(
        name="secret area out",
        walls="0C2608.1 | 0C3408.1",
        status=WARP,
        width_cm=57.370,
        step_cm=146.93,
        notes="Room 0x10, between two tile walls.",
    ),
    KnownWarp(
        name="block warp",
        walls="14A210.0 | 14A510.0",
        status=WARP,
        width_cm=33.442,
        step_cm=86.58,
        notes="Room 0x13, between two tile walls.",
    ),
]
