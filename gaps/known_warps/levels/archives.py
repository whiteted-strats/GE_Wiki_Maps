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
    KnownWarp(
        name="TAS double door warp",
        walls="06FA19.0 | 0x1d3bc8.0",
        status=WARP,
        width_cm=0.0,
        step_cm=69.87,
        objects_forming_gap=[0x1D3BC8],
        notes="Room 0x3a. A hairline: 0.000057 cm.",
    ),
    KnownWarp(
        name="TAS agent glass warp",
        walls="015E19.0 | 0x1d43c8.1",
        status=WARP,
        width_cm=0.0,
        step_cm=117.54,
        objects_forming_gap=[0x1D43C8],
        notes="Room 0x37, upstairs. A hairline: 0.000080 cm. There is a pane in the same place "
        "downstairs.",
    ),
]
