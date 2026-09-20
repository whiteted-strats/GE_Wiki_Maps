from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="Window A",
        walls="2F8020.2 | 2F8020.4",
        status=WARP,
        width_cm=51.361,
        step_cm=42.17,
        notes="Room 0x6f, between two walls of the same tile.",
    ),
    KnownWarp(
        name="Window B",
        walls="2FE621.1 | 2FF520.3",
        status=WARP,
        width_cm=55.301,
        step_cm=66.22,
        notes="Room 0x6f.",
    ),
    KnownWarp(
        name="Window C",
        walls="0x1e19d0.0 | 309621.0",
        status=WARP,
        width_cm=51.450,
        step_cm=49.24,
        notes=(
            "Room 0x7a. The gap is named by its narrowest pinch, a pane of glass against the wall, "
            "but the warp goes between the walls of tiles 309B22 and 309A22."
        ),
    ),
    KnownWarp(
        name="Window D",
        walls="2FE821.0 | 300120.1",
        status=WARP,
        width_cm=52.381,
        step_cm=74.77,
        notes="Room 0x6f.",
    ),
    KnownWarp(
        name="tunnel gate warp",
        walls="0x1e7c50.2 | 0x1e7d50.0",
        status=WARP,
        width_cm=3.970,
        step_cm=73.58,
        objects_forming_gap=[0x1E7C50, 0x1E7D50],
        notes="Room 0x62, between the two doors of the gate.",
    ),
]
