from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="left tiny glass gap",
        walls="01A64A.1 | 0x1d7d44.3",
        status=WARP,
        width_cm=1.064,
        step_cm=88.79,
        objects_forming_gap=[0x1D7D44],
        notes="Room 0x27, between a pane of glass and the wall. The mirror image of the right one.",
    ),
    KnownWarp(
        name="right tiny glass gap",
        walls="021448.0 | 0x1d7cb0.3",
        status=WARP,
        width_cm=1.062,
        step_cm=89.10,
        objects_forming_gap=[0x1D7CB0],
        notes="Room 0x47, between a pane of glass and the wall. The mirror image of the left one.",
    ),
]
