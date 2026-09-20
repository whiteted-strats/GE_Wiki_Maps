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

# Currently we're going to have a seperate py file for each level
# Seems sensible since it may want to heavily customised what's drawn,
#   i.e. drawing something between guards and objects


# --------------------------------------------------------
# FRIGATE SPECIFIC

from level_specific.frigate.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.frigate import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, opaque_objects
from level_specific.frigate.group_names import *

def frig_specific(tilePlanes, currentTiles, plt, axs, GROUP_NO):
    # ------ Hostage escape areas ------
    HOSTAGE_HEIGHT = 105    # measured, varies +-9 but mostly + so this is pretty fair
    ESCAPE_PAD_NUMS = [0x91, 0x93, 0xA9, 0x94, 0xA8, 0x8f]  # best to worst (when unloaded at least)
    HOSTAGE_IDS = [0x2c, 0x2d, 0x30, 0x31, 0x34, 0x35]

    spheres = []

    for padNum in ESCAPE_PAD_NUMS:
        padPos = list(pads[padNum]["position"])
        padPos[1] -= HOSTAGE_HEIGHT
        spheres.append((tuple(padPos), 500))
        
        # DEBUG - also draw circles for potential explosive wizardry
        x, _, z = padPos
        axs.add_artist(plt.Circle((-x, z), 500, color='g', linewidth=1, fill=False))

    colourSphereIntesectionWithTiles(spheres, tilePlanes, tiles, plt, axs)
    


    # -----------------------------------

    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())
    STD_SPEED = 5.4807696015788     # from my lua GuardData.get_speed, used to print lengths which are handy
    HOSTAGE_NAME = {
        0x2C : "Bridge",
        0x34 : "SA",
        0x31 : "Slowest",
        0x35 : "Engine room",
        0x30 : "Agent #2",
        0x2D : "Agent #1",
    }

    SHORTCUTTING = False
    if SHORTCUTTING:
        print("[!] Shortcutting to 8f across the front of the boat")

    fastestEscapeTimes = []
    for g_id in HOSTAGE_IDS:
        hostage = guards[guardAddrWithId[g_id]]
        np = hostage["near_pad"]
        escapeTimes = []
        for tp in ESCAPE_PAD_NUMS:

            # Get the path from near pad to potential target
            path = getPathBetweenPads(np, tp, sets, pads)
            if tp == 0x91:  # Even unloaded we'll escape at 8b (between stairs)
                assert path[-2] == 0x8b
                path = path[:-1]

            if g_id == 0x2c and tp == 0x91: # Bridge hostage escapes internally
                tweaked_path = path[:path.index(0x4E)+1]
            else:
                tweaked_path = path

            if SHORTCUTTING and tp == 0x8f: # Shortcut
                assert tweaked_path[-5:-1] == [0x92, 0x93, 0x94, 0x90]
                tweaked_path = tweaked_path[:-4] + tweaked_path[-2:]
                assert tweaked_path[-3:] == [0x92, 0x90, 0x8f]

            expectedEscapedTime = getPathTime(hostage, tweaked_path, pads, STD_SPEED) / 60  # nearly certainly a lower bound
            escapeTimes.append((expectedEscapedTime, tp))

            # `hostage` also has ["position"], ["tile"] so we can pass it as an extra first point
            drawPathWithinGroup(plt, axs, path, pads, currentTiles, tiles, hostage)

        # Old code, printing in order and such
        """
        print(f"{hex(g_id)} : (")
        escapeTimes.sort()
        times, escapePads = zip(*escapeTimes)
        escapePads = ", ".join(map(hex,escapePads))
        print(f"  '{HOSTAGE_NAME[g_id]}',")
        print(f"  {times[0]:.2f},")
        print(f"  [{escapePads}],")
        times = [t - times[0] for t in times]
        times = ", ".join(f"{t:.2f}" for t in times)
        print(f"  [{times}],")
        print("),")
        """

        # Now just dump it!
        print(f"{HOSTAGE_NAME[g_id]} : {escapeTimes}")

        eet, eep = min(escapeTimes)
        assert eep == 0x91  # everyone's best pad

        fastestEscapeTimes.append((eet, g_id))


    fastestEscapeTimes.sort()
    for eet, g_id in fastestEscapeTimes:
        # We could draw these by the hostage or something..
        pass ##print(f"{eet:.2f} : {HOSTAGE_NAME[g_id]}")
    
    if False:
        # Hacky FOV doesn't work too well & it's not too interesting.
        drawFOV(pads[0x003E], [0x07, 0x08, 0x2C], tiles, guards, objects, opaque_objects, plt,
            ignoreTileAddrs = [], objTransforms = {})
        drawFOV(guards[guardAddrWithId[0x10]], [0x09, 0x08, 0x2C], tiles, guards, objects, opaque_objects, plt,
            ignoreTileAddrs = [], objTransforms = {})

    ON_TOP_FLOOR = guards[guardAddrWithId[0x30]]["tile"] in currentTiles
    ON_LOWER_DECK = guards[guardAddrWithId[0x34]]["tile"] in currentTiles
    ON_MID_DECK = guards[guardAddrWithId[0x22]]["tile"] in currentTiles

    rbg = guards[guardAddrWithId[0x00]] # right bridge guard
    lbg = guards[guardAddrWithId[0x02]] # left bridge guard
    bhg = guards[guardAddrWithId[0x04]] # bad hearing guard
    dkg = guards[guardAddrWithId[0x0E]] # double klobb guard

    ucg = guards[guardAddrWithId[0x0A]] # upper corner guard

    hpg = guards[guardAddrWithId[0x20]] # hearing pipe guard

    # Bad guards to hear us surely? (far side)
    fsg1 = guards[guardAddrWithId[0x26]]
    fsg2 = guards[guardAddrWithId[0x28]]

    # The near guard can hear us.. but it's probably just too far for him to get there
    ug0 = guards[guardAddrWithId[0x08]]
    ug1 = guards[guardAddrWithId[0x10]]
    path = getPathBetweenPads(ug0["near_pad"], 0x5D, sets, pads)
    t = getPathTime(ug0, path, pads, STD_SPEED) / 60
    # ug1 = 15.03s, ug0 = 15.73s

    mgg = guards[guardAddrWithId[0x22]] # middle grenade guard

    # [+] d5k easily reaches double klobb guard from the stairs
    #   -> though he'll see us under the door if he's too far back
    # If we are going to avoid him we just need to keep right on the stairs
    noiseAroundGuardHelper(dkg, [6.9125], tilePlanes, tiles, plt, axs, 'k')

    if ON_MID_DECK:
        noiseAroundGuardHelper(ug1, [6.9125], tilePlanes, tiles, plt, axs, '#d1880a')       ## likely pull this guy out - with phantom?

    if ON_TOP_FLOOR:
        # [+] 2 shots isn't enough, < 3 triggers left, < 4 could trigger right after

        noises = [2.9, 4.8, 6.6, 8.4, 10.1, 11.7, 11.86]    # pp7
        
        noiseAroundGuardHelper(lbg, [6.9125], tilePlanes, tiles, plt, axs, 'r')
        noiseAroundGuardHelper(rbg, [6.9125], tilePlanes, tiles, plt, axs, 'b')
        noiseAroundGuardHelper(bhg, [7.5], tilePlanes, tiles, plt, axs, 'k')


        # Upper corner guard could even be pulled out from the outside
        # Max noise will have the guard by the pipes hear us (bad?)
        noiseAroundGuardHelper(ucg, [6.9125], tilePlanes, tiles, plt, axs, 'g')
        noiseAroundGuardHelper(hpg, [6.9125], tilePlanes, tiles, plt, axs, 'r')

        # [+] Our main concern atm is the guard at the bottom of the stairs,
        # who we can't easily kill without alerting the pipe guard

    if ON_LOWER_DECK:

        N = 6.9125 ## 9.45  ## = 4 phantom shots -  

        noiseAroundGuardHelper(fsg1, [N], tilePlanes, tiles, plt, axs, 'r')
        noiseAroundGuardHelper(fsg2, [N], tilePlanes, tiles, plt, axs, 'r')

        # Upper corner guard could still be pulled in.. but we don't think we will
        # Grenade guard is of course a joke
        ##noiseAroundGuardHelper(ucg, [N], tilePlanes, tiles, plt, axs, 'b')
        ##noiseAroundGuardHelper(mgg, [5], tilePlanes, tiles, plt, axs, 'b')

        # We could (will) pull this guy down instead of up **
        noiseAroundGuardHelper(hpg, [N], tilePlanes, tiles, plt, axs, 'b')

        # Slow guards are bad guards
        noiseAroundGuardHelper(ug0, [N], tilePlanes, tiles, plt, axs, 'r')
        noiseAroundGuardHelper(ug1, [N], tilePlanes, tiles, plt, axs, 'r')

        # => very precise, though perhaps we could lure sooner?


    # Further notes
    # Maybe left pipe guard could hear us, then see us crossing the doorway, and so run down like 2 others on that floor
    
    # Maybe this has everyone covered without doing anything too clever. 

    # Also we could keep the phantom lure mebob for the 1 agent area guard, coz he will boost us as we try to kill another guard



    # Frigate SA calculations
    bridge_hostage = guards[guardAddrWithId[0x2c]]
    tp = 0x004e
    path = getPathBetweenPads(bridge_hostage["near_pad"], tp, sets, pads)
    assert path[:2] == [0x0053, 0x0051]
    t1 = getPathTime(bridge_hostage, path, pads, STD_SPEED) / 60
    t2 = getPathTime(bridge_hostage, [tp], pads, STD_SPEED) / 60
    print(f"Shortcutting {t1} -> {t2} saves {t1-t2}")


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
    markBadDoors(objects, "frigate")
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets), tiles)
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call frig specific code
    frig_specific(tilePlanes, currentTiles, plt, axs, GROUP_NO)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_DECK_AND_UPSTAIRS, 'frigate/frigate_deck_and_upstairs')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_MIDSHIPS, 'frigate/frigate_midships')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_ENGINE_ROOM, 'frigate/frigate_engine_room')
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_LOWER_DECK, 'frigate/frigate_lower_deck')
    