from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="depot warp",
        walls="005811.0 | 0x1ee630.2",
        status=WARP,
        width_cm=1.110,
        step_cm=78.38,
        objects_forming_gap=[0x1EE630],
        notes="Room 0x25.",
    ),
    KnownWarp(
        name="far roller door",
        walls="0BD011.1 | 0x1ee530.2",
        status=WARP,
        width_cm=2.047,
        step_cm=69.37,
        objects_forming_gap=[0x1EE530],
        notes="Room 0x26.",
    ),
    KnownWarp(
        name="TAS near roller door",
        walls="0BD111.1 | 0x1ee430.2",
        status=WARP,
        width_cm=0.0,
        step_cm=69.15,
        objects_forming_gap=[0x1EE430],
        notes="Room 0x26. A hairline: 0.000077 cm.",
    ),
    KnownWarp(
        name="right train door",
        walls="04557A.1 | 0x1eed40.2",
        status=WARP,
        width_cm=1.315,
        step_cm=167.86,
        objects_forming_gap=[0x1EED40],
        notes="Room 0x59.",
    ),
    KnownWarp(
        name="left train door",
        walls="045579.0 | 0x1eec40.1",
        status=WARP,
        width_cm=3.881,
        step_cm=80.17,
        objects_forming_gap=[0x1EEC40],
        notes="Room 0x59.",
    ),
]
