"""Could Bond simply have walked from p to q? An approximate answer, used only to annotate warps.

A warp past a crate which he could stroll around is worth far less than one through a wall. This
floods the positions where Bond fits, on a grid of points around the warp, and measures the walk
from p to q if there is one.

It is approximate, in floats, and says so in the report. Its known weakness is a passage only just
wider than Bond: if no grid point happens to fall in it, the walk through it is missed and the
answer is "no way round" when there is one. It never affects which warps are found.
"""

import heapq
import math

import numpy as np

from gaps.exact import bounding_box, grow_box
from gaps.fast import distance_to_nearest_wall, wall_arrays
from gaps.mesh import Level
from gaps.pinch import Pinch
from gaps.sheet import ObjectsPresent, walls_near
from gaps.witness import Witness

SEARCH_RADIUS_CM = 400  # how far from the warp the walk may stray
GRID_SPACING_CM = 4
ROWS_PER_BATCH = 16  # keeps the numpy arrays to a sensible size


def walking_distance(
    level: Level, pinch: Pinch, witness: Witness, present: ObjectsPresent
) -> float | None:
    """The length in centimetres of a walk from p to q staying near the warp, or None if the flood
    doesn't find one."""
    spacing = float(GRID_SPACING_CM)
    radius = float(level.bond_radius)
    p = np.array([float(witness.p[0]), float(witness.p[1])])
    q = np.array([float(witness.q[0]), float(witness.q[1])])

    region = grow_box(bounding_box([witness.p, witness.q]), SEARCH_RADIUS_CM)
    walls = walls_near(level, pinch.start_tile, region, present)
    starts, ends = wall_arrays(walls)

    xs = np.arange(float(region[0]), float(region[1]), spacing)
    zs = np.arange(float(region[2]), float(region[3]), spacing)
    bond_fits = np.zeros((len(xs), len(zs)), dtype=bool)
    for first_row in range(0, len(xs), ROWS_PER_BATCH):
        rows = xs[first_row : first_row + ROWS_PER_BATCH]
        positions = np.array([[x, z] for x in rows for z in zs])
        clearance = distance_to_nearest_wall(positions, starts, ends)
        bond_fits[first_row : first_row + len(rows), :] = (
            clearance.reshape(len(rows), len(zs)) >= radius
        )

    # Two neighbouring grid points where Bond fits can always be walked between: a wall crossing
    # the short hop between them would be within his radius of both.
    start = _nearest_fitting_node(p, xs, zs, bond_fits)
    goal = _nearest_fitting_node(q, xs, zs, bond_fits)
    if start is None or goal is None:
        return None
    grid_distance = _shortest_path(bond_fits, start, goal)
    return None if grid_distance is None else grid_distance * GRID_SPACING_CM


def _nearest_fitting_node(
    point: np.ndarray, xs: np.ndarray, zs: np.ndarray, bond_fits: np.ndarray
) -> tuple[int, int] | None:
    i, j = int(np.abs(xs - point[0]).argmin()), int(np.abs(zs - point[1]).argmin())
    nearby = [(i + di, j + dj) for di in (-1, 0, 1) for dj in (-1, 0, 1)]
    nearby = [
        (a, b) for a, b in nearby if 0 <= a < len(xs) and 0 <= b < len(zs) and bond_fits[a, b]
    ]
    if not nearby:
        return None
    return min(
        nearby, key=lambda node: (xs[node[0]] - point[0]) ** 2 + (zs[node[1]] - point[1]) ** 2
    )


def _shortest_path(
    bond_fits: np.ndarray, start: tuple[int, int], goal: tuple[int, int]
) -> float | None:
    """Dijkstra over the grid, moving to any of the 8 neighbours. Distance is in grid spacings."""
    moves = [
        (di, dj, math.hypot(di, dj)) for di in (-1, 0, 1) for dj in (-1, 0, 1) if (di, dj) != (0, 0)
    ]
    best = {start: 0.0}
    queue = [(0.0, start)]
    while queue:
        distance, node = heapq.heappop(queue)
        if node == goal:
            return distance
        if distance > best[node]:
            continue
        for di, dj, cost in moves:
            neighbour = (node[0] + di, node[1] + dj)
            if not (
                0 <= neighbour[0] < bond_fits.shape[0] and 0 <= neighbour[1] < bond_fits.shape[1]
            ):
                continue
            if bond_fits[neighbour] and distance + cost < best.get(neighbour, math.inf):
                best[neighbour] = distance + cost
                heapq.heappush(queue, (distance + cost, neighbour))
    return None
