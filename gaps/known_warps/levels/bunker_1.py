from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="mainframe meme",
        walls="0x1d13e0.2 | 0x1d1470.0",
        status=WARP,
        width_cm=12.363,
        step_cm=81.65,
        objects_forming_gap=[0x1D13E0, 0x1D1470],
        notes="Room 0x11, between two of the mainframes.",
    ),
]
