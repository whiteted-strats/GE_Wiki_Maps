from gaps.known_warps import KnownWarp
from gaps.survey import WARP

KNOWN_WARPS = [
    KnownWarp(
        name="Observatory roof warp",
        walls="30FB00.1 | 31A500.2",
        status=WARP,
        width_cm=36.343,
        step_cm=100.09,
        notes="Room 0x07, between two tile walls. Surface 1 and 2 share a map, so it is on both.",
    ),
    KnownWarp(
        name="King of the crates in",
        walls="0x1dd548.0 | 0x1dd5c8.2",
        status=WARP,
        width_cm=48.326,
        step_cm=106.96,
        objects_forming_gap=[0x1DD548, 0x1DD5C8],
        notes="Room 0x05.",
    ),
    KnownWarp(
        name="King of the crates out",
        walls="0x1dd4c8.0 | 0x1dd5c8.2",
        status=WARP,
        width_cm=48.577,
        step_cm=96.11,
        objects_forming_gap=[0x1DD4C8, 0x1DD5C8],
        notes="Room 0x05.",
    ),
]
