from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="Observatory roof warp",
        walls="30FB00.1 | 31A500.2",
        status=WARP,
        width_cm=36.343,
        step_cm=100.09,
        notes="Room 0x07, between two tile walls. Surface 1 and 2 share a map, so it is on both.",
    ),
]
