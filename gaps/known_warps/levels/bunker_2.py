from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="bond cell door",
        walls="0AF611.2 | 0x1dadcc.1",
        status=WARP,
        width_cm=7.417,
        step_cm=78.44,
        objects_forming_gap=[0x1DADCC],
        notes="Room 0x28. A 7 cm slit between the cell door and the wall beside it.",
    ),
    # A pair of doors in room 0x0a, each 27.8 cm from the wall beside it, with identical steps
    KnownWarp(
        name="TAS documents warp in",
        walls="06EE12.1 | 0x1d9bac.0",
        status=WARP,
        width_cm=27.813,
        step_cm=110.77,
        objects_forming_gap=[0x1D9BAC],
    ),
    KnownWarp(
        name="TAS documents warp out",
        walls="06EE11.0 | 0x1d9aac.0",
        status=WARP,
        width_cm=27.813,
        step_cm=110.77,
        objects_forming_gap=[0x1D9AAC],
    ),
]
