from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="elevator door warp (left)",
        walls="09B72A.2 | 0x1b5718.3",
        status=WARP,
        width_cm=21.124,
        step_cm=65.70,
        objects_forming_gap=[0x1B5718],
        notes="Room 0x2c, between the door and the wall.",
    ),
    KnownWarp(
        name="elevator door warp (right)",
        walls="09BD2A.2 | 0x1b5818.1",
        status=WARP,
        width_cm=21.127,
        step_cm=66.16,
        objects_forming_gap=[0x1B5818],
        notes="Room 0x2c, between the door and the wall.",
    ),
]
