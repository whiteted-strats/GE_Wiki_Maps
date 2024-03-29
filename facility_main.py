from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup
import matplotlib.pyplot as plt
import os
from math import sqrt

# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customised what's drawn,
#   i.e. drawing something between guards and objects

# --------------------------------------------------------
# Facility SPECIFIC

from level_specific.facility.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.facility import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects


# --------------------------------------------------------
# Generic stuff below 

def drawGuards(guards, currentTiles, axs):
    # Too simple for it's own module atm
    for addr, gd in guards.items():
        if gd["tile"] not in currentTiles:
            continue
        x,z = gd["position"]
        nadeOdds = gd["grenade_odds"]
        axs.add_artist(plt.Circle((-x, z), gd["radius"], color=('g' if nadeOdds == 0 else 'r'), linewidth=1, fill=False))

def drawCollectibles(objects, axs, currentTiles):
    # Also currently very simple, though we may add more detail to each type,
    # i.e. draw the ammo box / BA / a key shape.

    # ---- How we should be doing it ----
    # Is going to need to go in a lib though - we're drawing for all groups atm
    # So we need some bounds on Bond's height (crouching -> max)

    # Shift source down by Bond's minimum height, then be generous with max.
    # Cylinder not a sphere don't forget. Could be slightly tricky with sloping tiles.
    # Maybe first clip the tile between these heights. Won't be so hard since convex and flat.

    # For the extra check, get all current tiles within the specified radius which are reachable (not usable in the sphere code)

    # Can borrow the actual 'draw circle intersect tiles' from 
    # Just flatten the tiles.. after clipping using above code.

    # ---- How we're actually doing it.. just draw a circle :) ----

    colours = {
        "key" : (1,0.45,0),  # orange
        "body_armour" : (0,0.1,0.3), # blue
    }
    default_colour = (0,0,0)    # black : ammo_box, ammo, weapon

    for od in objects.values():
        if not od["collectible"]:
            continue
        if od["tile"] not in currentTiles:  # oversimplification - fixme eventually
            continue

        x,z = od["position"]
        colour = colours.get(od["type"], default_colour)
        # 1m radius hardcoded. Also needs to have LOS iirc.
        axs.add_artist(plt.Circle((-x, z), 100, color=colour, linewidth=1, fill=False))


def drawActivatables(axs, activatable_objects, objects, currentTiles):
    for objAddr in activatable_objects:
        od = objects[objAddr]
        if od["tile"] not in currentTiles:
            continue
        
        radius = 200    ## & 22.5 degrees
        if od["type"] == "aircraft":
            radius = 400    ## & 120 degrees

        x,z = od["position"]
        axs.add_artist(plt.Circle((-x, z), radius, color='g', linewidth=1, fill=False))



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

    drawGuards(guards, currentTiles, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets))
    drawCollectibles(objects, axs, currentTiles)

    drawActivatables(axs, activatable_objects, objects, currentTiles)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 1, 'facility/facility_start')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 0, 'facility/facility_downstairs')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 2, 'facility/facility_upstairs')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 3, 'facility/facility_ending')
    ##main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 4, 'facility_E')
    ##main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 5, 'facility_F')