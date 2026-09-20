from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="theoretical decoder door TAS warp",
        walls="0FE422.1 | 0x1c9794.2",
        status=WARP,
        width_cm=0.001,
        step_cm=192.20,
        objects_forming_gap=[0x1C9794],
        notes=(
            "Room 0x3d. A hairline, 0.00063 cm, so a long step straight along the crack. It was "
            "missed until vertical tiles' edges stopped being walls where no floor leads into them."
        ),
    ),
    KnownWarp(
        name="bathroom door meme warp",
        walls="037F02.1 | 0x1c6d0c.1",
        status=WARP,
        width_cm=0.0,
        step_cm=99.79,
        objects_forming_gap=[0x1C6D0C],
        notes="Room 0x09. A hairline: 0.00000085 cm.",
    ),
    KnownWarp(
        name="Ted waz ere TASing",
        walls="0x1c9484.0 | 10F30A.1",
        status=WARP,
        width_cm=0.0,
        step_cm=121.03,
        objects_forming_gap=[0x1C9484],
        notes="Room 0x1b. A hairline: 0.0000066 cm. Warped in a TAS by Whiteted.",
    ),
]
