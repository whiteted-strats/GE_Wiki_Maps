from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes, drawEdgeInsideCornerToTarget
from lib.object import drawObjects
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, getPathTime
from lib.set_boundaries import drawSetBoundaries, drawNavGraph
from lib.near_geoms import computeNearGeoms, drawNearGeoms

from lib.misc import *
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import math
from math import sqrt, floor, ceil

# --------------------------------------------------------
# Statue SPECIFIC

from level_specific.statue.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.statue import tiles, guards, objects, pads, lone_pads, level_scale, sets, presets, activatable_objects
from level_specific.statue.group_names import *
import numpy as np
from lib.path_finding import rotACWS


def statue_specific(tilePlanes, currentTiles, plt, axs):
    # Taken from Egypt code. -12.6 is the reduction by fullspeed
    # The ground is actually quite flat nearby so this should be quite accurate,
    #   but going up / down a slope will affect this figure a touch.
    BOND_HEIGHT = 167.3 - 12.6

    # From script 1000
    # Going outside 1400 sets flag #14, which Trev checks in 0414
    STATUE_PAD = 0x003b
    ENTER_DIST = 800
    LEAVE_DIST = 1400

    trig_pad_pos = list(pads[STATUE_PAD]["position"])
    trig_pad_pos[1] -= BOND_HEIGHT
    trig_pad_pos = tuple(trig_pad_pos)
    spheres = [
        (trig_pad_pos, ENTER_DIST),
        (trig_pad_pos, LEAVE_DIST),        
    ]
    
    # Developed for the Frigate hostages. Seems to be working
    # The two overlap so we need to pick sensible colours so that they show well
    colourSphereIntesectionWithTiles(spheres[1:], tilePlanes, tiles, plt, axs, base_colour='g')
    colourSphereIntesectionWithTiles(spheres[:1], tilePlanes, tiles, plt, axs, base_colour='b')

    # We draw circles just for reference
    # It is indeed just slightly wider which is encouraging
    x,_,z = trig_pad_pos
    for dist in [ENTER_DIST, LEAVE_DIST]:
        axs.add_artist(plt.Circle((-x, z), dist, color='r', linewidth=1, alpha=0.2, fill=False))

    # And we mark the center clearly
    axs.add_artist(plt.Circle((-x, z), 15, color='g', linewidth=1, fill=True))

    # And we make use of our beautiful new library function
    drawEdgeInsideCornerToTarget([0x090E00, 0x088600], trig_pad_pos, tiles, plt)
    

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
    fig,axs = prepPlot(plt,groupBounds[GROUP_NO])
    tilePlanes = getTilePlanes(currentTiles, tiles, level_scale)

    drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)

    # Draw stuff :)
    markStairs(tilePlanes, tiles, (0.4,0.2,0), plt) # make generic
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets), tiles)
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call specific code
    statue_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))



if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 0, "statue/statue_full")
