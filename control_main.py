from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import colourSphereIntesectionWithTiles, drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup, getPathTime
from lib.set_boundaries import drawSetBoundaries, drawNavGraph, drawSets
from lib.near_geoms import computeNearGeoms, drawNearGeoms

from lib.misc import *
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import math
from math import sqrt, floor, ceil

# --------------------------------------------------------
# Control SPECIFIC

from level_specific.control.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.control import tiles, guards, objects, pads, lone_pads, level_scale, sets, presets, activatable_objects
from level_specific.control.group_names import *
import numpy as np
from lib.path_finding import rotACWS

# Whether to generate the beautiful near geoms
DRAW_NEAR_GEOMS = False

# For our new trick
PAD_BEHIND_LEFT_GLASS = 0x007C
BOND_GUARD_SPAWN_PADS = {
    0x26 : [
        0x007e,
        0x0047,
        0x0081,
        0x00ca,
        0x00bd,
        0x003d,
        0x007c,
    ],
    0x27 : [
        0x0056,
        0x00d7,     # Pad by Nat's door
        0x008c,     # Fallback if the above is blocked - Pad by the door in the 'generator' room
        0x00a5,
        0x0095,
        0x00b7,
        0x0052,
    ]
}

NAT_GUARD_SPAWN_PADS = [0x003f, 0x0045]

NAT_TERMINUS_PAIRS = [
    [0x00dc, 0x00e1],
    [0x0070, 0x00e3]
]

# Mine related constants taken from the Caverns code
MINE_EXPLOSION_CONSTANTS = {
    "min_damage_radius" : 300,
    "max_damage_radius" : 480,
    "damage_factor" : 4,
}

def _natsplosion_nonsense():
    # Silly Natsplosion idea - the lift doors probably have to be shut
    # We can reach ok from outside the doors, but the pillar is very awkward
    # We also see problems that we probably can't Nat-splode her from far away
    # Unfortunately, Nat does not "stop moving" while fading out, so this strat is not possible. 
    x, _, z = lone_pads[0x00e0]["position"]
    axs.add_artist(plt.Circle((-x, z), 250-20, color='k', linewidth=2, fill=False))

    nat_final_path = getPathBetweenPads(0xD8, 0xCB, sets, pads)
    assert len(nat_final_path) == 4

    for i in [0,1]:
        t = getPathTime(None, nat_final_path[i:], pads, STD_SPEED)
        print(f"Nat end time from {nat_final_path[i]:04x} is {t/60:.2f}")

def draw_nat_warp(plt, axs):
    # Draw our circles for the Nat warp
    # 2.5m and 1.5m
    NAT_HEIGHT = 105    # Not measured, stolen from Frigate script O:)
    for tps in NAT_TERMINUS_PAIRS:
        for pad,r,colour in zip(tps, [250,150],['#884400', '#990000']):
            pad = pads[pad] if pad in pads else lone_pads[pad]
            x,y,z = pad["position"]
            heights = set(tiles[pad["tile"]]["heights"])
            assert len(heights) == 1
            y -= (next(iter(heights)) + NAT_HEIGHT)

            # Now y is the height of the pad above Nat
            # Adjust radius and draw our circle, plus the center point
            r = math.sqrt(r*r - y*y)
            axs.add_artist(plt.Circle((-x, z), r, color=colour, alpha=0.5, linewidth=1, fill=False))
            axs.add_artist(plt.Circle((-x, z), 2, color=colour, alpha=0.5, linewidth=0, fill=True))

def draw_bond_guard_trappings(currentTiles, plt, axs):
    # Draw the Nat spawn pads too
    for sp in NAT_GUARD_SPAWN_PADS:
        if pads[sp]["tile"] in currentTiles:
            x,_,z = pads[sp]["position"]
            axs.add_artist(plt.Circle((-x, z), 20, color='green', alpha=0.5, linewidth=1, fill=True))

    # Draw the paths..
    # But also build a list of common ones so we can draw them in purple
    # Necessarily they must be in the same direction
    edges_for_each = []

    for sps, colour in zip(BOND_GUARD_SPAWN_PADS.values(), ['r','b']):
        edges = set()
        for sp in sps:
            # Mark the spawn point
            if pads[sp]["tile"] in currentTiles:
                x,_,z = pads[sp]["position"]
                axs.add_artist(plt.Circle((-x, z), 20, color=colour, alpha=0.5, linewidth=1, fill=True))

            spawnPath = getPathBetweenPads(sp, PAD_BEHIND_LEFT_GLASS, sets, pads)
            fullEdges = []
            drawPathWithinGroup(plt, axs, spawnPath, pads, currentTiles, tiles, None, stdColour=colour, fullEdges=fullEdges)
            for i,j in fullEdges:
                edges.add((spawnPath[i], spawnPath[j]))

            # True hacking to cope with partial edges
            if fullEdges:
                i = min(fullEdges)[0] - 1
                if i >= 0:
                    edges.add(tuple(spawnPath[i:i+2]))
                i = max(fullEdges)[1] 
                if i < len(spawnPath) - 1:
                    edges.add(tuple(spawnPath[i:i+2]))

        edges_for_each.append(edges)

    # Draw those purple edges
    common_edges = set.intersection(*edges_for_each)
    for edge in common_edges:
        xs, ys, zs = zip(*[pads[p]["position"] for p in edge])
        xs = [-x for x in xs]
        plt.plot(xs, zs, linewidth=0.5, color='purple')


def draw_clem_glass_strat(currentTiles, plt, axs):
    # Cook up the radius for just the 1st wave
    # We won't care about the 2nd wave, even for the glass explosion
    waves = [0.05, 0.30, 0.55, 0.80]    # We've forgotten but we think these are a global constant
    min_r = MINE_EXPLOSION_CONSTANTS["min_damage_radius"]
    max_r = MINE_EXPLOSION_CONSTANTS["max_damage_radius"]
    exp_radii = [min_r + (max_r-min_r)*w for w in waves]
    w1_r = exp_radii[0]

    MINE_RADIUS = 8     # From GE_MAP.lua, which we remember eyeballing

    # Find the glass so we can put a mine against it
    # !! For some reason our presets are wrong! The setup editor shows 0x27c0..
    #    Our tiles do seem to be right, and there doesn't seem to be any computation to these
    #    Maybe we dumped this from some trash rom??
    mainframe_glass = objects[0x1D8204]
    assert mainframe_glass["preset"] == 0x27C2 and mainframe_glass["type"] == "glass"   # are we going mad?
    xs,zs = zip(*mainframe_glass["points"])
    mfg_x = min(xs) - MINE_RADIUS       # reflected
    mfg_left_z = min(zs)

    # Draw our cute mine, same colour from GE_MAP.lua again
    axs.add_artist(plt.Circle((-mfg_x, mfg_left_z), MINE_RADIUS, color='k', alpha=1, linewidth=0, fill=True))

    # Draw the explosion
    """
    ds = [1,-1,-1,1,1,-1]
    xs = [-(mfg_x + d*w1_r) for d in ds[:5]]
    zs = [mfg_left_z + d*w1_r for d in ds[1:6]]
    plt.plot(xs, zs, linewidth=1, color='r')
    """
    rect = patches.Rectangle((-mfg_x-w1_r, mfg_left_z-w1_r), 2*w1_r, 2*w1_r, linewidth=1, edgecolor='r', alpha=0.5, facecolor='orange')
    axs.add_patch(rect)


def control_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())

    STD_SPEED = 5.4807696015788

    # Nat's final route, from the bottom of the stairs to the lift
    # Note that this full_path includes a wiggle which we skip
    full_path = getPathBetweenPads(0x0067, 0x00CB, sets, pads)   
    assert full_path[4:6] == [0x0055, 0x00D7]
    del full_path[4]
    assert full_path[3:5] == [0x0057, 0x00D7]
    path = full_path[4:7]
    assert path == [0x00D7, 0x00D6, 0x00D0]

    # Time the full path as a sanity check
    # Then time the pieces of the small path
    t = getPathTime(None, full_path, pads, STD_SPEED) / 60
    print(f"[ ] Nat ideal complete time from stair bottom: {t:.2f}s")

    t1 = getPathTime(None, path[:2], pads, STD_SPEED)
    t2 = getPathTime(None, path[1:], pads, STD_SPEED)
    print(f"[ ] {path[0]:04x} -> {path[1]:04x} : {t1}")
    print(f"    {path[1]:04x} -> {path[2]:04x} : {t2}")

    # Do drawings for Clem's new glass strat
    # No longer - we have the modern strats
    ##draw_clem_glass_strat(currentTiles, plt, axs)

    # Check that any guards behind you get to the Nat door / "I'm coming trigger pad" backwards
    # This inspires keeping to one side (probably left) to stop guards blocking Nat's ending
    full_path = getPathBetweenPads(0x80, 0xD7, sets, pads)
    assert full_path[:10] == list(range(0x80,0x8a))
    assert full_path[-2:] == [0xD6, 0xD7]
    assert 0xCE in full_path
    print("[+] Yup pre-glass guards will go back past Nat to get behind Nat's door")

    # Draw a corridor around where Nat might run, to help us decide whether to go left or right:
    # Pads at the top of the stairs, and back of the corridor behind Nat's door
    if pads[0x0057]["tile"] in currentTiles:
        p = pads[0x0057]["position"]
        q = pads[0x00D6]["position"]
        v = np.subtract(q,p)
        n_x, _, n_z = np.multiply(v, 1/np.linalg.norm(v))

        # Nat tends to drift left around the stairs
        # This range represents her being anywhere between middle of the stairs, and far left
        leftmost_shift = 75.0 - 20.0
        rightmost_shift = 0

        for k,shift in [(-1,rightmost_shift),(1,leftmost_shift)]:
            p_shifted = (p[0]+shift*n_z, p[1], p[2]-shift*n_x)
            base_xs,_,base_zs = zip(p_shifted,q)
            # Nat, guard, Bond = 70
            # 40 excluding Bond, which shows where we can actually be
            for width,alpha in [(0,0.3),(40,1),(70,0.3)]:
                xs = [x + width*k*n_z for x in base_xs]
                zs = [z - width*k*n_x for z in base_zs]
                plt.plot([-x for x in xs], zs, linewidth=0.5, color='b', alpha=alpha)

    """
    # Draw our 15m circle around Nat's start point,
    # Considering the new Nat business, we need to see the 15m circle at the start
    nat_pad = lone_pads[0x00e3]
    x, _, z = nat_pad["position"]
    axs.add_artist(plt.Circle((-x, z), 1500, color='k', linewidth=2, fill=False))
    """

    """
    # Consider our teleport blocking!
    # TODO functionalise
    def draw_spawn_spot(x,z,axs,plt,gather=None):
        axs.add_artist(plt.Circle((-x, z), 20, color='b', linewidth=1, fill=False))
        if gather:
            gather.append((-x,z))
    
    spawn_spots = []
    draw_spawn_spot(nat_pad["position"][0], nat_pad["position"][2], axs, plt, spawn_spots)
    angle = math.asin(nat_pad["normal"][0])     # Heading. We happen to get the quadrant right but should have a function..
    for i in range(8):
        x = nat_pad["position"][0] + math.sin(angle)*60
        z = nat_pad["position"][2] + math.cos(angle)*60
        draw_spawn_spot(x,z,axs,plt)
        angle += math.pi / 4
    """

    ##draw_bond_guard_trappings(currentTiles, plt, axs)



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

    # Draw tiles or pretty colours for Nat / Silvereye
    if GROUP_NO in [GRP_CONTROL_MAIN] and DRAW_NEAR_GEOMS:
        computeNearGeoms(pads, tiles)
        drawNearGeoms(pads, axs)
        drawNavGraph(pads, plt, axs, edgeColour='w')

        p = getPathBetweenPads(0x70, 0x57, sets, pads)  # Nat
        ##print(", ".join(map(hex, p)))

        p = getPathBetweenPads(0x84, 0x54, sets, pads)  # Fast Belgium lure, does go around
        assert 0xd2 in p
        i = p.index(0xd2)
        assert p[i+2] == 0xdd    

        STD_SPEED = 5.4807696015788
        t0 = getPathTime(None, p[:i+1], pads, STD_SPEED) / 60
        d = getPathTime(None, p[i:i+3], pads, STD_SPEED) / 60
        t1 = t0 + d
        print(f"Run around window: {t0:.2f} - {t1:.2f}")

        p = getPathBetweenPads(0x84, 0x89, sets, pads)
        tl = getPathTime(None, p, pads, STD_SPEED) / 60
        print(f"Direct lure time: {tl:.2f}")

        # This is silvereye right..
        ## noiseAroundGuardHelper(pads[0x84], [19.70], tilePlanes, tiles, plt, axs, 'r', base_alpha=0.5)

    else:
        drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)
        if GROUP_NO in [GRP_CONTROL_MID_FLOOR]:
            drawSets(sets, pads, lone_pads, currentTiles, tiles, plt, axs, scale=1, add_labels=False)

    # Draw stuff :)
    markStairs(tilePlanes, tiles, (0.4,0.2,0), plt) # make generic
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)
    

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets), tiles)
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call specific code
    control_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))



##print("[!] Drawing the mid-level only")

main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_CONTROL_MAIN, "control/control_main")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_CONTROL_MID_FLOOR, "control/protect_mid_floor")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 2, "control/protect_upper_floor")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 3, "control/protect_left_space")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, 4, "control/protect_right_space")