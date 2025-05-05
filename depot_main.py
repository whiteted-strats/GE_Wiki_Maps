from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects, markBadDoors
from lib.circle_related import drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, getPathTime
from lib.set_boundaries import drawSetBoundaries
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil, atan2, atan, pi, cos, sin, acos
from queue import Queue

# --------------------------------------------------------
# depot SPECIFIC

from level_specific.depot.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.depot import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, lone_pads
import numpy as np

def _get_dist(obj1, obj2):
    x1, z1 = obj1["position"]
    x2, z2 = obj2["position"]
    dx = abs(x2 - x1)
    dy = abs(z2 - z1)
    d = max(dx, dy)     # Furthest
    return d

def depot_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())
    padToRoom = dict((i, tiles[p["tile"]]["room"]) for i,p in pads.items())

    # Exploding ammo crate data, read out with the GE_Map
    damage_factor = 2
    min_damage_radius = 150
    max_damage_radius = 260
    animation_length = 180

    # Now computing the waves more precisely
    wave_0 = 8 / animation_length
    waves = [wave_0 + i / 4 for i in range(4)]
    exp_radii = [min_damage_radius + (max_damage_radius-min_damage_radius)*w for w in waves]

    # Focusing only on x-z, so explosion width (not height) matters - if they are different anyway
    
    # Unfortunately we haven't extracted tags, so we just have to get the ammo boxes by preset
    objectAddrByPreset = dict((obj['preset'], addr) for addr, obj in objects.items())
    ammo_dump_presets = [0x014C, 0x014D, 0x014E, 0x0145, 0x0144, 0x0143, 0x014B, 0x014A, 0x0149, 0x0154, 0x0153, 0x0152,
        0x014F, 0x0150, 0x0151, 0x0148, 0x0147]
    ammo_dumps = [objects[objectAddrByPreset[preset]] for preset in ammo_dump_presets]
    assert all(ad['health'] == 1000 for ad in ammo_dumps)

    def getWorseCaseDamage(r):
        hs = [max(er - r, 0) for er in exp_radii]
        # Note no RNG multiplier applied - should be 1.0 - 1.5 for each
        fs = [damage_factor * 250 * h / er for h,er in zip(hs, exp_radii)]
        expectedDamage = sum(fs) 
        return expectedDamage

    # Since damage_factor = 2, and 4 waves based a 250
    assert getWorseCaseDamage(0) == 2000
    # And since it is right on the edge,
    assert getWorseCaseDamage(exp_radii[-1]) == 0

    # Binary search for minimum guaranteed destruction distance
    l = 0
    h = exp_radii[-1]
    m = h
    i = 0
    while True:
        i += 1
        m = (l + h) / 2
        if m in [l,h]:
            break
        d = getWorseCaseDamage(m)
        if d >= 1000:
            l = m
        else:
            h = m

    sure_destroy_dist = l
    print(f"Guaranteed destroy distance = {sure_destroy_dist}")
    max_damage_dist = exp_radii[-1]

    links = []
    for i, dmp_i in enumerate(ammo_dumps):
        effected = []
        for j,dmp_j in enumerate(ammo_dumps):
            if i == j:
                continue

            d = _get_dist(dmp_i, dmp_j)
            if d >= max_damage_dist:
                continue
            effected.append((j, d))
        links.append(effected)
        
    # Tricky to just find all chains of destruction,
    # Instead lets simulate starting by exploding #1
    health = [1000] * len(ammo_dumps)
    to_explode = Queue()
    
    # Normal strat:
    ## health[0] = 0   # exploded
    ## health[1] = 0   # to explode
    ## to_explode.put(1)

    # Rocket shot - quite sure it's going to blow up both side boxes
    for preset in [0x0151, 0x0147]:
        i = ammo_dump_presets.index(preset)
        health[i] = 0
        to_explode.put(i)

    # Testing - nullifying some
    ## health[ammo_dump_presets.index(0x0154)] = 0
    


    while not to_explode.empty():
        i = to_explode.get()
        print(f"0x{ammo_dumps[i]['preset']:04x} explodes!")
        assert health[i] <= 0
        for j,dst in links[i]:
            h = health[j]
            if h <= 0:
                continue    # don't re-explode
            dmg = getWorseCaseDamage(dst)

            # Testing - average luck
            ## dmg *= 1.25

            h -= dmg
            print(f"  0x{ammo_dumps[j]['preset']:04x} (distance {dst}) takes {int(dmg)} damage -> {int(h)} health")
            if h <= 0:
                print(f"  -> queued to explode")
                to_explode.put(j)
            health[j] = h

    assert all(h <= 0 for h in health)
    print("[+] That's all of them..")

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
    markBadDoors(objects, "depot")
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets), tiles)
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call specific code
    depot_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 0, "depot/depot_main")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 1, "depot/depot_ending")