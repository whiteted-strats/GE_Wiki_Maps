"""Float and numpy versions of a few geometric questions, for searching quickly.

Nothing in here is trusted. Whatever a search built on these proposes is checked again exactly, by
`gaps.sheet`, before it is reported.
"""

import math

import numpy as np

from gaps.mesh import BoundarySegment


def wall_arrays(walls: list[BoundarySegment]) -> tuple[np.ndarray, np.ndarray]:
    """(start points, end points) of the walls, each an array of shape (walls, 2)."""
    starts = np.array([[float(wall.a[0]), float(wall.a[1])] for wall in walls]).reshape(-1, 2)
    ends = np.array([[float(wall.b[0]), float(wall.b[1])] for wall in walls]).reshape(-1, 2)
    return starts, ends


END_MARGIN = 1e-9  # how far along a wall counts as its end, as a fraction of its length


def ray_hits_wall_at(
    origin: np.ndarray,
    direction: np.ndarray,
    starts: np.ndarray,
    ends: np.ndarray,
    glancing_allowed: bool = False,
) -> float:
    """How far along the ray the first wall is hit. With `glancing_allowed`, passing through the
    end of a wall is not a hit, as in `gaps.sheet.trace` with `along_walls`."""
    wall = ends - starts
    to_start = starts - origin
    denominator = direction[0] * wall[:, 1] - direction[1] * wall[:, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        along_ray = (to_start[:, 0] * wall[:, 1] - to_start[:, 1] * wall[:, 0]) / denominator
        along_wall = (to_start[:, 0] * direction[1] - to_start[:, 1] * direction[0]) / denominator
    if glancing_allowed:
        on_the_wall = (along_wall > END_MARGIN) & (along_wall < 1 - END_MARGIN)
    else:
        on_the_wall = (along_wall >= 0) & (along_wall <= 1)
    hits = (denominator != 0) & (along_ray > 1e-9) & on_the_wall
    return float(along_ray[hits].min()) if hits.any() else math.inf


def distance_to_nearest_wall(
    positions: np.ndarray, starts: np.ndarray, ends: np.ndarray
) -> np.ndarray:
    wall = ends - starts  # (walls, 2)
    length2 = np.maximum((wall**2).sum(axis=1), 1e-30)
    offset = positions[:, None, :] - starts[None, :, :]  # (positions, walls, 2)
    along = np.clip((offset * wall[None, :, :]).sum(axis=2) / length2, 0, 1)
    nearest = starts[None, :, :] + along[:, :, None] * wall[None, :, :]
    return np.sqrt(((positions[:, None, :] - nearest) ** 2).sum(axis=2)).min(axis=1)
