from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, getPathTime
from lib.set_boundaries import drawSetBoundaries, drawSets
from lib.near_geoms import computeNearGeoms, drawNearGeoms
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil, atan2, atan, pi, cos, sin, acos
from itertools import chain

# --------------------------------------------------------
# surface_2 SPECIFIC

from level_specific.surface_2.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.surface_2 import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, lone_pads
from level_specific.surface_2.group_names import *
import numpy as np

def s2_spawning():
    padToRoom = dict((i, tiles[p["tile"]]["room"]) for i,p in chain(pads.items(), lone_pads.items()))

    # From script 100A
    bondPadToLabel = {
        0x001e : 0x2f, 0x0044 : 0x30, 0x0048 : 0x31, 0x002a : 0x32, 0x005d : 0x33,
        0x002d : 0x34, 0x0072 : 0x35, 0x008a : 0x36, 0x00d2 : 0x37, 0x0041 : 0x38,
        0x00c9 : 0x39, 0x00b1 : 0x3a, 0x00e2 : 0x3b, 0x00f3 : 0x3c, 0x00e8 : 0x3d,
    }

    # Check none coincide, then move to a map from room to labels
    assert len(bondPadToLabel.keys()) == len(set(padToRoom[p] for p in bondPadToLabel.keys()))
    bondRoomToLabel = {
        padToRoom[p] : l for p,l in bondPadToLabel.items()
    }

    print(", ".join(map(hex, bondRoomToLabel.keys())))
    # Our starting room is 12, then 1 doesn't appear in the list, nor 13
    #    so it's not until the 1st corner (into 2) that we change
    #    .. however actor 01 still targets pad 

    labelToSpawnLocs = {
        0x2f : [0x0027, 0x0039, 0x0048, 0x002a],    # 12, start
        0x30 : [0x001e, 0x0039, 0x002a, 0x0027],    # 02, after 1st corner
        0x31 : [0x0044, 0x005d, 0x002a, 0x0048],    # 03, after concave part starts
        0x32 : [0x002d, 0x0027, 0x005d, 0x0048],
        0x33 : [0x002d, 0x0048, 0x0072, 0x003c],
        0x34 : [0x002f, 0x005d, 0x008a, 0x002a],
        0x35 : [0x008a, 0x003a, 0x00b7, 0x005d],
        0x36 : [0x0072, 0x00e0, 0x002f, 0x0033],
        0x37 : [0x0041, 0x00b7, 0x00b1, 0x003e],
        0x38 : [0x00d2, 0x00c9, 0x003e, 0x00b7],
        0x39 : [0x003e, 0x0086, 0x00b3, 0x00b1],
        0x3a : [0x008a, 0x00e2, 0x00ac, 0x0086],
        0x3b : [0x00b1, 0x00f3, 0x0034, 0x00e8],
        0x3c : [0x00b3, 0x0038, 0x0033, 0x00e8],
        0x3d : [0x00f3, 0x00e2, 0x0034, 0x00b1],
    }

def surface_2_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())

    s2_spawning()

    # Draw the targety line
    pntA = tiles[0x1DA0BC]["points"][0]
    e5_pos = pads[0x00E5]["position"][::2]
    xs, zs = map(list, zip(*[pntA, e5_pos]))
    xs = [-x for x in xs]
    plt.plot(xs, zs, '--', linewidth=5, color=(0.25,0.25,0.25))

    e5_height = pads[0x00E5]["position"][1]
    crossroadsTile = tiles[0x1D8A2C]
    crossroads_height = crossroadsTile["heights"][0]
    BOND_HEIGHT = 167.3 - 12.6
    h = (crossroads_height + BOND_HEIGHT) - e5_height

    r = 20000
    r = sqrt(r*r - h*h)
    x,z = e5_pos
    axs.add_artist(plt.Circle((-x, z), r, color='g', linewidth=5, fill=False))

    towerTile = tiles[0x1CE6E4]
    nearTower_height = max(towerTile["heights"])
    h = (nearTower_height + BOND_HEIGHT) - e5_height

    r = 7500
    r = sqrt(r*r - h*h)
    axs.add_artist(plt.Circle((-x, z), r, color='g', linewidth=5, fill=False))

    pos_2716 = presets[0x2716]["position"][::2]
    height_2716 = presets[0x2716]["position"][1]
    postLeanTile = tiles[0x1C9624]
    postLean_height = sum(postLeanTile["heights"]) / len(postLeanTile["heights"])
    h = (postLean_height + BOND_HEIGHT) - height_2716

    r = 4400
    r = sqrt(r*r - h*h)
    x,z = pos_2716
    axs.add_artist(plt.Circle((-x, z), r, color='g', linewidth=5, fill=False))

    snowEdgeTile = tiles[0x1CBD94]
    snowEdge_height = snowEdgeTile["heights"][0]
    h = (snowEdge_height + BOND_HEIGHT) - height_2716
    r = 1200
    r = sqrt(r*r - h*h)
    axs.add_artist(plt.Circle((-x, z), r, color='g', linewidth=5, fill=False))

    # Add draw the edge of the snow
    rightSlopeTile = tiles[0x1CB834]
    xs,zs = zip(rightSlopeTile["points"][2], rightSlopeTile["points"][0])
    xs = [-x for x in xs]
    plt.plot(xs, zs, linewidth=3, color=(0.35,0.35,0.35))

    xs,zs = zip(*snowEdgeTile["points"][0:2])
    xs = [-x for x in xs]
    plt.plot(xs, zs, linewidth=3, color=(0.35,0.35,0.35))

    # And some text
    x,z = rightSlopeTile["points"][0]
    plt.text(-x -320, z + 30, "Snow edge [3]", size=45)

    x,z = crossroadsTile["points"][0]
    plt.text(-x, z, "X-road [0]", size=45)

    x,z = towerTile["points"][2]
    plt.text(-x + 600, z + 200, "CW tower [1]", size=45)

    x,z = postLeanTile["points"][2]
    plt.text(-x + 700, z + 150, "Post lean [2]", size=45)

    # And mark that peak
    peakTile = tiles[0x1CE564]
    i = max(enumerate(peakTile["heights"]), key=lambda x:x[1])[0]
    x,z = peakTile["points"][i]
    axs.add_artist(plt.Circle((-x, z), 20, color='b', linewidth=1, fill=True))
    plt.text(-x - 200, z + 70, "Peak", size=45)

    # And the higher point that we're thinking might be worth throwing from
    i = max(enumerate(towerTile["heights"]), key=lambda x:x[1])[0]
    x,z = towerTile["points"][i]
    axs.add_artist(plt.Circle((-x, z), 20, color='b', linewidth=1, fill=True))
    plt.text(-x - 200, z + 70, "Alt lean spot?", size=45)


# --------------------------------------------------------
# Generic stuff below 


def saveFig(plt, fig, path, useWikiDpi):
    width, height = fig.get_size_inches()

    # 12.5MP max when rescaling on the wiki.
    wikiDPI = sqrt(12500000 / (width * height))
    stdDPI = 254 # 254 is 1 pixel per cm in GE world
    dpi = wikiDPI if useWikiDpi else stdDPI

    fig.tight_layout(pad=0)
    # (!) reduce the DPI if the map is too large
    plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=dpi)   
            


def main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GROUP_NO, path, useWikiDpi=False):
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
    drawTileHardEdges(currentTiles, tiles, (0.45, 0.45, 0.45), axs, linewidth=10)   # FAT, Darker

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets), tiles)
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call specific code
    surface_2_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path),useWikiDpi)


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 1, "surface_2/surface_2_B")
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 2, "surface_2/surface_2_C")
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 3, "surface_2/surface_2_D")
    print("Making massive main map..")
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 0, "surface_2/surface_2_splits", False)
    print("Done")
