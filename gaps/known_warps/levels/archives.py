from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="some sterling warp no doubt",
        walls="01A711.0 | 0x1d31c8.1",
        status=WARP,
        width_cm=33.506,
        step_cm=195.07,
        objects_forming_gap=[0x1CABEC],
        notes="Downstairs, room 0x2b. Its shortest step is between a wall and object 0x1cabec.",
    ),
    KnownWarp(
        name="attic warp",
        walls="04B221.1 | 04B421.1",
        status=WARP,
        width_cm=35.518,
        step_cm=266.77,
        notes="The attic, room 0x3d. There are three gaps a metre apart along one wall, with the "
        "same width, and one step passes through all three. The other two are its variants.",
    ),
]
