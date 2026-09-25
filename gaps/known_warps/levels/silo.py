from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="R-lean'd by Ted FIRST TRY",
        walls="0A4660.0 | 0x1c9d4c.1",
        status=WARP,
        width_cm=2.116,
        step_cm=74.84,
        objects_forming_gap=[0x1C9D4C],
        notes="Room 0x47, between the door and the wall.",
    ),
    KnownWarp(
        name="TAS elevator door warp",
        walls="001271.2 | 0x1cae6c.0",
        status=WARP,
        width_cm=0.00012,
        step_cm=93.39,
        objects_forming_gap=[0x1CAE6C],
        notes="Room 0x50. One float32 step off its frame. Untested in the game.",
    ),
]
