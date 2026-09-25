from gaps.known_warps import KnownWarp
from gaps.survey import WARP, WARP_IF_REMOVED

KNOWN_WARPS = [
    KnownWarp(
        name="pipe warp",
        walls="076A19.0 | 076A1A.1",
        status=WARP,
        width_cm=23.033,
        step_cm=90.83,
        notes="Room 0x10, between the end of the thin wall and the pipes. The well known one.",
    ),
    KnownWarp(
        name="harder pipe warp",
        walls="003719.1 | 07691A.2",
        status=WARP,
        width_cm=12.353,
        step_cm=84.78,
    ),
    KnownWarp(
        name="flukey pipe warp",
        walls="076319.1 | 076B18.2",
        status=WARP,
        width_cm=7.34,
        step_cm=190.74,
    ),
    KnownWarp(
        name="balcony door warp",
        walls="021E02.1 | 0x1ec6c0.5",
        status=WARP,
        width_cm=2.234,
        step_cm=84.97,
        objects_forming_gap=[0x1EC6C0],
        notes="The left balcony only. The two balcony doors are exact mirror images, but the wall "
        "beside the left one is one tile unit (2.234 cm) further out than on the right, where the "
        "door touches the wall.",
    ),
    KnownWarp(
        name="helicopter warp",
        walls="06BF3A.4 | 0x1eab04.2",
        status=WARP_IF_REMOVED,
        width_cm=1.999,
        step_cm=146.94,
        objects_forming_gap=[0x1EAB04],
        objects_in_the_way=[0x1EC8D0],
        notes="Between the helicopter and the wall. Only possible with the door 0x1ec8d0 gone, so "
        "not useful to a run, but of interest: a check that nothing cuts warps which need an "
        "object out of the way.",
    ),
    KnownWarp(
        name="potential roller door DLTK TAS warp",
        walls="06BF3A.2 | 0x1ec8d0.0",
        status=WARP,
        width_cm=0.0,
        step_cm=89.05,
        objects_forming_gap=[0x1EC8D0],
        notes="Room 0x25. A hairline: 0.000051 cm. The same door is in the way of the helicopter "
        "warp.",
    ),
]
