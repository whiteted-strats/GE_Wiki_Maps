from gaps.known_warps import KnownWarp
from gaps.survey import NO_WARP_FOUND, WARP

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
        status=NO_WARP_FOUND,
        width_cm=0.0,
        step_cm=0.0,  # not checked: there is no step
        objects_forming_gap=[0x1C6D0C],
        notes="Room 0x09. Kept as the example of a gap far below the local float32 step, made by "
        "float32 geometry: the door's back edge is tilted by one float32 step over its length, "
        "and its corner sits 1.5e-5 cm beyond the end of the wall, so the wall's corner is "
        "2e-11 cm "
        "from the tilted edge. The game has no number for that: in its arithmetic they touch. "
        "It was a 0.00000085 cm warp when object outlines were the printed decimals.",
    ),
    KnownWarp(
        name="objective A door",
        walls="0FD722.1 | 0x1c8524.0",
        status=WARP,
        width_cm=0.0,
        step_cm=93.60,
        objects_forming_gap=[0x1C8524],
        notes="Room 0x31. The simplest possible hairline, and so the one to test in the game: the "
        "door and its frame are both axis-aligned, and the door sits exactly one float32 step "
        "(2^-16 cm, 1.53e-5 cm) off the frame's line, uniformly along its whole width. There is "
        "no float32 between the two, so a step straight through can only have its line on the "
        "wall's z or on the door's z: whether the game lets Bond through comes down to the "
        "inequalities in its collision code, which the tool doesn't model. Its exact geometry says "
        "yes, by a crossing point halfway between the two which the game can't represent.",
    ),
]
