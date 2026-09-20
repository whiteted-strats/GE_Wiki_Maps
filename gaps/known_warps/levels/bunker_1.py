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
    KnownWarp(
        name="TAS closed end door warp",
        walls="016601.1 | 0x1d24f0.0",
        status=WARP,
        width_cm=0.0,
        step_cm=102.53,
        objects_forming_gap=[0x1D24F0],
        notes="Room 0x04. A hairline: 0.0000031 cm. The roof is linked close by, 2 m above.",
    ),
]
