from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects, markBadDoors
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, getPathTime
from lib.set_boundaries import findBisector, drawSetBoundaries
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil
from lib.fov import drawFOV
from lib.misc import *
import numpy as np

# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customised what's drawn,
#   i.e. drawing something between guards and objects


# --------------------------------------------------------
# DAM SPECIFIC

from level_specific.dam.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.dam import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, opaque_objects
from level_specific.dam.group_names import *

def dam_specific(tilePlanes, currentTiles, plt, axs, GROUP_NO):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())
    tower_guard = guards[guardAddrWithId[0x28]]

    STD_SPEED = 5.4807696015788

    # 0x8F = bottom of the stairs
    # 0x9A = top of stairs
    # 0x91 = far point
    # 0x86 = by the back gate

    # Some paths
    # Get the path to see which way it goes - with the guard starting at this pad

    for sp in [0x9A, 0x91]:
        path = getPathBetweenPads(sp, 0x86, sets, pads)
        print(f"0x{sp:x} -> back gate: [{', '.join(map(hex, path))}]")
        expectedEscapedTime = getPathTime(None, path, pads, STD_SPEED) / 60
        ##drawPathWithinGroup(plt, axs, path, pads, currentTiles, tiles, None)

    LOW_PADS = [0x008F, 0x0091, 0x0090, 0x0094, 0x0093, 0x0092]
    drawPathWithinGroup(plt, axs, LOW_PADS, pads, currentTiles, tiles, None, stdColour='r')

    for padNum in LOW_PADS:
        padPos = list(pads[padNum]["position"])
        x, _, z = padPos
        axs.add_artist(plt.Circle((-x, z), 20, color='b', linewidth=0.5, fill=False))

    # The line - from the tunnel corner to the gate corner
    back_tc = set(tiles[0x1BEC00]["points"]).intersection(set(tiles[0x1BED00]["points"]))
    assert len(back_tc) == 1, back_tc
    back_tc = list(back_tc)[0]
    gc = set(tiles[0x1C1160]["points"]).intersection(set(tiles[0x1C2858]["points"]))
    assert len(gc) == 1
    gc = list(gc)[0]

    # Don't actually draw it now that we draw the racing line to the button

    """
    # Instead draw said racing line
    # And be precise about kicking it out 30 units
    # TODO make this a generic thing - it's easier than we thought
    front_tc = set(tiles[0x1BEC00]["points"]).intersection(set(tiles[0x1BEC40]["points"]))
    assert len(front_tc) == 1, front_tc
    front_tc = list(front_tc)[0]
    v = list(np.subtract(front_tc, back_tc))
    v = np.multiply([v[1], -v[0]], 30 / np.linalg.norm(v))
    bond_pos = np.add(front_tc, v)
    button_pos = objects[0x1E6A40]["position"]
   
    # ALSO we see that it goes over a corner of the wall (at least considering Bond's width)
    wc = set(tiles[0x1C5928]["points"]).intersection(set(tiles[0x1C3918]["points"]))
    assert len(wc) == 1, wc
    wc = list(wc)[0]
    # So work out where the closest point is
    # NOTE that really we should be going around the slightest part of a circle
    # Also we should really have done the dot product in the other direction but oh well
    v = list(np.subtract(button_pos, bond_pos))
    v = np.multiply(v, 1 / np.linalg.norm(v))
    l = np.dot(v,np.subtract(wc, bond_pos))
    p = np.add(bond_pos, np.multiply(v, l))
    w = np.subtract(p, wc)
    l = np.linalg.norm(w)
    assert l < 30       # Too close!
    print(f"The direct line to the button is indeed too close to the corner ({l:.2f}cm)")
    w = np.multiply(w, 30 / l)
    p = list(np.add(w, wc))
    # Despite us not doing any weird scaling, setting the line width to 30 is not 30
    # So we have to draw some shape?
    points = [bond_pos, p, np.subtract(button_pos,np.multiply(v,200))]   # Before the circle
    points += points[::-1]
    points[:3] = [np.add(p,w) for p in points[:3]]
    points[3:] = [np.subtract(p,w) for p in points[3:]]
    points.append(points[0])
    xs,zs = zip(*points)
    xs = [-x for x in xs]
    axs.fill(xs, zs, alpha=0.5, ec=None, fc='k')
    """


    # Left and right guards under the dam between 2nd and 3rd cam towers
    # Top of the dam is all one set, so we test them being lured to the pad approximately above - 0x0112
    lg = guards[guardAddrWithId[0x1A]]
    rg = guards[guardAddrWithId[0x1B]]
    near_pad = lg['near_pad']
    path = getPathBetweenPads(near_pad, 0x0112, sets, pads)

    # Sure enough they go through the 3rd tower :)
    # Truncate and test how long this will take
    assert 0x0101 in path
    i = path.index(0x0101)
    door_path = path[:i+1]
    t = getPathTime(lg, door_path, pads, STD_SPEED) / 60
    
    assert t == 13.75
    
    # And it's not really that long, so we go left guard and we do it after
    # Let's see how much noise we'll need
    noiseAroundGuardHelper(lg, [7,9], tilePlanes, tiles, plt, axs, '#d1512e', base_alpha=0.1)
    noiseAroundGuardHelper(rg, [7,9], tilePlanes, tiles, plt, axs, '#490eb0', base_alpha=0.1)

    # A guard we don't want to lure
    noiseAroundGuardHelper(guards[guardAddrWithId[0x1C]], [7,9], tilePlanes, tiles, plt, axs, '#490eb0', base_alpha=0.1)

    # Draw the path partly for reference
    drawPathWithinGroup(plt, axs, path, pads, currentTiles, tiles, lg)

    # Agh they're all deaf..

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

    # Draw stuff :)
    drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)
    markStairs(tilePlanes, tiles, (0.4,0.2,0), plt) # make generic
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    markBadDoors(objects,"dam")
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets), tiles)
    drawCollectibles(objects, plt, axs, currentTiles)

    # For some reason we need to add the monitors to the activatable objects
    #   I can't remember how they're gathered tbh
    # Also remove the gate doors because they're no good to us
    activatable_objects.append(0x1E6A40)    # Near big gate monitor
    activatable_objects[:] = [objAddr for objAddr in activatable_objects if objects[objAddr]["type"] != "door"]
    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call dam specific code
    dam_specific(tilePlanes, currentTiles, plt, axs, GROUP_NO)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 0, 'dam/pre_dam')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 1, 'dam/on_the_dam')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 2, 'dam/under_the_dam')