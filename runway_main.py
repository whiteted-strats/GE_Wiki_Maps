from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, getPathTime
from lib.set_boundaries import drawSetBoundaries
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil, atan2, atan, pi, cos, sin, acos

# --------------------------------------------------------
# runway SPECIFIC

from level_specific.runway.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.runway import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, lone_pads
import numpy as np
from matplotlib.patches import Wedge
from itertools import count

def runway_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())
    padToRoom = dict((i, tiles[p["tile"]]["room"]) for i,p in pads.items())

    chargingGuard = guards[guardAddrWithId[0x1D]]
    GUARD_MAX_SIGHT = 50    # Guard-specific but common here on Runway

    # Developing line of sight

    assert (110 - 60) % 15 != 0
    assert GUARD_MAX_SIGHT % 16 != 0
    critAngles = [0] + list(range(60,110,15)) + [110]
    critDists = [100*x/3 for x in range(0,GUARD_MAX_SIGHT*3,16)] + [100*GUARD_MAX_SIGHT]
    
    baseAng = (pi/2 + chargingGuard["facing_angle"]) * 180 / pi
    x,z = chargingGuard["position"]

    for aB,a1,a2 in zip(count(1), critAngles, critAngles[1:]):
        for dB,d1,d2 in zip(count(1), critDists[1:], critDists[2:]):    # Skip the inner sector, 100% chance
            N = aB * dB + 1
            w = d2 - d1
            axs.add_artist(Wedge((-x,z), d2, baseAng+a1, baseAng+a2, width=w, color='r', alpha=1/N))
            axs.add_artist(Wedge((-x,z), d2, baseAng-a2, baseAng-a1, width=w, color='r', alpha=1/N))

    # Line(ish) direct to plane
    hc = set(tiles[0x1C8208]["points"]).intersection(set(tiles[0x1C7EA8]["points"]))
    assert len(hc) == 1
    hc = list(hc)[0]
    x,z = hc
    hc = (x + 40, z)    # Guesstimate for going wide + bond's width

    for objAddr in [0x1DA72C]:  # 0x1DBA3C i.e. battery
        objP = objects[objAddr]["position"]

        xs,zs = zip(hc,objP)
        plt.plot([-x for x in xs], zs, color='k')

    # Better second line
    bc = set(tiles[0x1CAB30]["points"]).intersection(set(tiles[0x1CAB50]["points"]))
    assert len(bc) == 1
    bc = list(bc)[0]
    xs,zs = zip(hc,bc)
    plt.plot([-x for x in xs], zs, color='k')
    
    # Charging area
    noiseAroundGuardHelper(chargingGuard, [10], tilePlanes, tiles, plt, axs, 'b', base_alpha=1, fill=False, lw=2)

# --------------------------------------------------------
# Generic stuff below 


def saveFig(plt, fig, path):
    width, height = fig.get_size_inches()

    # 12.5MP max when rescaling on the wiki.
    wikiDPI = sqrt(12500000 / (width * height))

    fig.tight_layout(pad=0)
    # (!) reduce the DPI if the map is too large
    plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=254)   # 254 is 1 pixel per cm in GE world
            


def main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GROUP_NO, path):
    # Global (above a specific group) preperations
    prepTiles(tiles)
    tile_groups = seperateGroups(tiles, startTileName, dividingTiles)
    groupBounds = getGroupBounds(tiles, tile_groups)
    prepSets(sets, pads)

    
    # Group specific preperations
    currentTiles = set(tile_groups[GROUP_NO])
    tilePlanes = getTilePlanes(currentTiles, tiles, level_scale)
    fig,axs = prepPlot(plt,groupBounds[GROUP_NO])

    # Draw stuff :)
    drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)
    markStairs(tilePlanes, tiles, (0.4,0.2,0), plt) # make generic
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets), tiles)
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call specific code
    runway_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 0, "runway/runway")
