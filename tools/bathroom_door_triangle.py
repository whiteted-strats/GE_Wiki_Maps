"""Draws notes/warp_survey/bathroom_door_triangle.svg: why the gap survey reports a 2e-11 cm gap
beside Facility's bathroom door (door 0x1c6d0c against the wall of tile 037F02, "bathroom door
meme warp" in gaps/known_warps/levels/facility.py).

The figures come from the survey, in world coordinates, with every coordinate the float32 the
game holds:
- the door's back edge runs from (-198.92581, W) to (-187.32181, W + one float32 step), so it is
  tilted by one step, 1.53e-5 cm, over its 11.6 cm: a slope of 1.3e-6. The door's stored matrix
  is rotated by a few 1e-7 radians (float32 sine and cosine of a right angle) and its two corners
  rounded to different float32 z values
- the wall lies along z = W exactly, and its end corner is 1.5e-5 cm along from the door's corner
- so the pinch is the short leg of a right-angled triangle: 1.5e-5 cm x 1.3e-6 = 2e-11 cm, from
  the wall's corner straight up to a point of the tilted edge which is not itself a float32

Not part of the survey. Run from the repo root: python -m tools.bathroom_door_triangle
"""

import math
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams["svg.fonttype"] = "none"  # keep the text as text
BROWN, GREY, GREEN = "#8b5a2b", "0.35", "#2ca02c"
OUT = Path("notes/warp_survey/bathroom_door_triangle.svg")

# Drawn, not to scale: the long leg is 1.5e-5 cm and the short leg 2e-11 cm
LONG_LEG = 6.0
SLOPE = 0.55
ANGLE = math.atan(SLOPE)


def main() -> None:
    fig, ax = plt.subplots(figsize=(11, 7.6), dpi=100)
    door_corner, wall_corner = (0.0, 0.0), (LONG_LEG, 0.0)
    on_door_edge = (LONG_LEG, LONG_LEG * SLOPE)

    # The wall: along z = W from its end corner, and its other edge at a right angle, fading
    ax.plot([LONG_LEG, LONG_LEG + 6.5], [0, 0], color=GREY, lw=6, solid_capstyle="butt", zorder=2)
    ax.plot([LONG_LEG, LONG_LEG], [0, -3.0], color=GREY, lw=6, alpha=0.18, zorder=1,
            solid_capstyle="butt")  # fmt: skip
    ax.plot(*wall_corner, "s", color=GREY, ms=13, zorder=5)
    ax.text(LONG_LEG + 3.6, -1.2, "wall", ha="center", va="center", color=GREY, fontsize=16,
            fontweight="bold", alpha=0.8)  # fmt: skip

    # The door: its tilted back edge, and its side edge at a right angle to it, fading
    ax.plot([0, 12.5], [0, 12.5 * SLOPE], color=BROWN, lw=3.5, zorder=3)
    side = 3.2
    ax.plot([0, -math.sin(ANGLE) * side], [0, math.cos(ANGLE) * side], color=BROWN, lw=3.5,
            alpha=0.18, zorder=1)  # fmt: skip
    ax.plot(*door_corner, "o", color=BROWN, ms=12, zorder=5)
    ax.text(1.3, 2.6, "door", ha="center", va="center", color=BROWN, fontsize=16,
            fontweight="bold", alpha=0.8, rotation=math.degrees(ANGLE))  # fmt: skip

    # The triangle
    ax.plot([0, LONG_LEG], [0, 0], color="k", lw=1, ls=":", zorder=4)
    ax.plot([LONG_LEG, LONG_LEG], [0, on_door_edge[1]], color=GREEN, lw=2.5, zorder=4)
    ax.plot(*on_door_edge, "o", color=GREEN, ms=11, zorder=6)

    ax.text(0, -0.35, "door corner\n(-198.92581, W)", ha="center", va="top", color=BROWN,
            fontsize=11)  # fmt: skip
    ax.text(LONG_LEG + 0.3, 0.3, "wall's end corner\n(-198.92580, W)", ha="left", va="bottom",
            color=GREY, fontsize=11)  # fmt: skip
    ax.annotate("", xy=(LONG_LEG, -1.3), xytext=(0, -1.3),
                arrowprops=dict(arrowstyle="<->", color="k", lw=1.3))  # fmt: skip
    ax.text(LONG_LEG / 2, -1.5, "1.5e-5 cm  (door corner to wall corner)", ha="center", va="top",
            fontsize=10.5)  # fmt: skip
    ax.text(9.2, 9.2 * SLOPE + 0.4, "door's back edge\nslope = 1 float32 step / 11.6 cm = 1.3e-6",
            ha="center", va="bottom", color=BROWN, fontsize=11, rotation=math.degrees(ANGLE),
            rotation_mode="anchor")  # fmt: skip
    ax.annotate(
        "the pinch (the short leg):\n1.5e-5 cm x 1.3e-6 = 2e-11 cm,\n"
        "from the wall's corner straight up to the door's edge.\n"
        "This point on the door's edge is not a float32.",
        xy=(LONG_LEG, on_door_edge[1] / 2), xytext=(7.4, 2.3), color=GREEN, fontsize=11,
        va="center",
        arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.3, connectionstyle="arc3,rad=-0.2"),
    )  # fmt: skip

    ax.set_xlim(-4.3, 13.2)
    ax.set_ylim(-3.4, 9.2)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.suptitle(
        "Facility gap 028: the triangle behind the 2e-11 cm pinch between door 0x1c6d0c and the "
        "wall of tile 037F02\n"
        "Not to scale: the triangle is really 1.5e-5 cm long and 2e-11 cm high",
        fontsize=11.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
