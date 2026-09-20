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
    KnownWarp(
        name="ouro door",
        walls="06D02A.1 | 0x1cc23c.3",
        status=WARP,
        width_cm=0.0,
        step_cm=91.79,
        objects_forming_gap=[0x1CC23C],
        notes="Room 0x33. A hairline: 0.0000034 cm. The door just before the train warp, which a "
        "guard should be opening.",
    ),
    KnownWarp(
        name="this looks curious WHATTT XD",
        walls="031421.0 | 0x1cbf1c.0",
        status=WARP,
        width_cm=0.0,
        step_cm=313.42,
        objects_forming_gap=[0x1CBF1C],
        notes="Room 0x2d. A hairline, 0.0000064 cm, with a step of over three metres.",
    ),
]
