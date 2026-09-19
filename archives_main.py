from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup
from lib.fov import drawFOV
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt
import numpy as np

# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customised what's drawn,
#   i.e. drawing something between guards and objects

# --------------------------------------------------------
# Archives SPECIFIC

from level_specific.archives.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.archives import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, opaque_objects


# --------------------------------------------------------
# Generic stuff below 

def saveFig(plt, fig, path):
    width, height = fig.get_size_inches()

    # 12.5MP max when rescaling on the wiki.
    # We can just not rescale though ;) 
    wikiDPI = sqrt(12500000 / (width * height))

    dpi = 254

    fig.tight_layout(pad=0)
    # (!) reduce the DPI if the map is too large
    plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=dpi)   # 254 is 1 pixel per cm in GE world
            


def main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GROUP_NO, path):
    # Global (above a specific group) preperations
    prepTiles(tiles)

    tile_groups = seperateGroups(tiles, startTileName, dividingTiles)
    groupBounds = getGroupBounds(tiles, tile_groups)
    prepSets(sets, pads)

    # Group specific preperations
    currentTiles = set(tile_groups[GROUP_NO])
    fig,axs = prepPlot(plt,groupBounds[GROUP_NO])
    tilePlanes = getTilePlanes(currentTiles, tiles, level_scale)

    # Draw stuff :)
    drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)
    markStairs(tilePlanes, tiles, (0.4,0.2,0), plt) # make generic
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets))
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Archives specific testing
    # Ignore the stairs since they overlap
    doorAddr = 0x1D36C8
    def openNatDoor(pnt):
        hinge = objects[doorAddr]["hinges"][0]
        x,z = np.subtract(pnt, hinge)
        pnt = np.add((z,-x), hinge)
        return pnt

    # Object on the boundary isn't really supported, but better to be more accurate
    nat = [g for g in guards.values() if g["id"] == 0x00][0]
    drawFOV(nat, [0x34, 0x3A, 0x39,], tiles, guards, objects, opaque_objects, plt,
        ignoreTileAddrs = [0x1AD70C], objTransforms = {doorAddr:openNatDoor})

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 0, 'archives/archives_upstairs')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 1, 'archives/archives_downstairs')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 2, 'archives/archives_attic')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 3, 'archives/archives_start')
    ##[4] is the ending