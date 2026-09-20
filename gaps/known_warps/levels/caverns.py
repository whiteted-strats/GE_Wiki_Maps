from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="TAS donut box warp #1",
        walls="00CD08.2 | 0x1c49f0.2",
        status=WARP,
        width_cm=49.701,
        step_cm=96.52,
        objects_forming_gap=[0x1C49F0],
        notes="Room 0x13, between a box and the wall.",
    ),
    KnownWarp(
        name="TAS donut box warp #2",
        walls="00CD08.2 | 0x1c5018.2",
        status=WARP,
        width_cm=51.556,
        step_cm=59.25,
        objects_forming_gap=[0x1C5018],
        notes="Room 0x13, between another box and the same wall.",
    ),
]
