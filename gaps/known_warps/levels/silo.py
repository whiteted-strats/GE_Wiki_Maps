from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="TAS elevator door warp",
        walls="003978.1 | 0x1caf6c.5",
        status=WARP,
        width_cm=0.0,
        step_cm=91.52,
        objects_forming_gap=[0x1CAF6C],
        notes="Room 0x50. A hairline: 0.000012 cm.",
    ),
    KnownWarp(
        name="R-lean'd by Ted FIRST TRY",
        walls="0A4660.0 | 0x1c9d4c.1",
        status=WARP,
        width_cm=2.116,
        step_cm=74.84,
        objects_forming_gap=[0x1C9D4C],
        notes="Room 0x47, between the door and the wall.",
    ),
]
