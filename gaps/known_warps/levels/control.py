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
    KnownWarp(
        name="Main room locked double door",
        walls="0x1d8c0c.1 | 0x1d8d0c.0",
        status=WARP,
        width_cm=0.00012,
        step_cm=76.04,
        objects_forming_gap=[0x1D8C0C, 0x1D8D0C],
        notes="Room 0x10, the crack down the middle of a pair of doors. Both are exact axis-aligned "
        "rectangles, and their inner edges are exactly one float32 step apart in x (2^-13 cm, "
        "1.22e-4 cm) along their whole 16 cm thickness. Like Facility's objective A door, a step "
        "straight through can only have its line on one door's x or the other's; here both sides "
        "are doors, so the same collision routine decides. Untested in the game.",
    ),
]
