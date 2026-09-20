from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="half-a-frame barrier warp",
        walls="0x1c9448.0 | 530911.0",
        status=WARP,
        width_cm=51.641,
        step_cm=87.73,
        objects_forming_gap=[0x1C9448],
        notes="Room 0x1a, between the barrier and the wall. The only gap on Streets.",
    ),
]
