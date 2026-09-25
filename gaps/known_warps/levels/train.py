from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="train warp",
        walls="0E7028.1 | 0x1cd0ec.2",
        status=WARP,
        width_cm=0.004,
        step_cm=84.85,
        objects_forming_gap=[0x1CD0EC],
        notes="Room 0x35. A hairline, 0.0037 cm, and done on console.",
    ),
]
