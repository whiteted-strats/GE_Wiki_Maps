# Adapted from the general (SA / 00A) one

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
# Streets SPECIFIC

from level_specific.streets.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.streets import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, lone_pads
from level_specific.streets.group_names import *
import numpy as np

def padRoomAnalysis():
    padsMentionedInRoom = {}
    for p in bondPadToLabel:
        r = padToRoom[p]
        l = padsMentionedInRoom[r] = padsMentionedInRoom.get(r, [])
        l.append(p)
    
    for r, ps in padsMentionedInRoom.items():
        if len(ps) == 1:
            continue

        labels = set(bondPadToLabel[p] for p in ps)
        if len(labels) == 1:
            continue

        print(f"Room {r:x}")
        for p in ps:
            print(f"  {p:x} : {bondPadToLabel[p]:x}")


def streets_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())
    padToRoom = dict((i, tiles[p["tile"]]["room"]) for i,p in pads.items())

    # -- Val LOS --
    
    doorway_tiles = [0x1BA398, 0x1BA3B8]
    wall_tile = 0x1B9ED8
    if doorway_tiles[0] in currentTiles:
        ta, tb = doorway_tiles
        doorway_extremes = [tiles[tb]["points"][1], tiles[ta]["points"][2]]   # Left, Right from Val's POV

        # Just use the intercept rather than walking across tiles
        xs, _, zs = tiles[wall_tile]["points"]
        intercept_x = max(xs)

        val_pos = guards[guardAddrWithId[0x1F]]["position"]
        
        target = []
        for p in doorway_extremes:
            v = np.subtract(p, val_pos)

            line = [val_pos]
            x_diff = intercept_x - val_pos[0]
            w = np.multiply(v, x_diff / v[0])
            line.append(np.add(val_pos, w))

            x_diff -= 30
            w = np.multiply(v, x_diff / v[0])
            q = np.add(val_pos, w)
            q[0] += 30
            target.append(q)

            xs, zs = zip(*line)
            plt.plot([-x for x in xs], zs, linewidth=0.5, color='k')

        xs, zs = zip(*target)
        plt.plot([-x for x in xs], zs, linewidth=0.5, color='g')

        xs = [x-30 for x in xs]
        plt.plot([-x for x in xs], zs, linewidth=0.5, color='b')


        x,z = val_pos
        axs.add_artist(plt.Circle((-x, z), 800, color='r', linewidth=1, fill=False))
    
    # -------------

    # Path from Val to the end, does go the same way we do (though snakes all over the place)
    # Use it to get the order of the rooms we go through
    padNearVal = 0x000A
    bondPath = getPathBetweenPads(padNearVal, 0x00AC, sets, pads)
    rooms = [padToRoom[p] for p in bondPath]
    currentRoom = None
    roomPath = []
    for room in rooms:
        if room != currentRoom:
            roomPath.append(room)
            currentRoom = room
    # Room path verified, could potentially add 1C with some timeloss drifting right
    #   though we rule this out below

    # Processed from the 1001 script:
    bondPadToLabel = {
        0x002c : 0x41, 0x002e : 0x41, 0x0031 : 0x41,
        0x0034 : 0x42, 0x0037 : 0x42, 0x0043 : 0x42,
        0x0049 : 0x43, 0x004c : 0x43, 0x004f : 0x43,
        0x003b : 0x44, 0x0046 : 0x44, 0x005e : 0x44,
        0x005c : 0x45, 0x0064 : 0x45, 0x0052 : 0x46,
        0x0055 : 0x46, 0x0058 : 0x46, 0x006a : 0x47,
        0x006d : 0x47, 0x0070 : 0x47, 0x0073 : 0x48,
        0x0076 : 0x48, 0x007c : 0x49, 0x0082 : 0x49,
        0x0091 : 0x4a, 0x008f : 0x4a, 0x0094 : 0x4a,
        0x0089 : 0x4b, 0x0084 : 0x4b, 0x008a : 0x4b,
        0x0097 : 0x4c, 0x009a : 0x4c, 0x009d : 0x4c,
        0x00a3 : 0x4d, 0x00a7 : 0x4d, 0x00ac : 0x4d,
        # Don't forget the defaults!
    }

    # 00A3 and 00A7 are the only two pads in the same room,
    #   and both have the same target label of 0x4D, so we can move to a map of room to label
    bondRoomToLabel = {
        padToRoom[p] : l for p,l in bondPadToLabel.items()
    }

    # Civilians are 2B and 2D
    labelToSpawnLocs = {
        0x41 : {0x2a : 0x0036, 0x2b : 0x0037, 0x2c : 0x0038, 0x2d : 0x0043, 0x2e : 0x003e, 0x2f : 0x0049, 0x30 : 0x003b, }, # IN1
        0x42 : {0x2a : 0x004c, 0x2b : 0x004b, 0x2c : 0x004d, 0x2d : 0x0045, 0x2e : 0x0046, 0x2f : 0x0047, 0x30 : 0x005e, }, # IN2
        0x43 : {0x2a : 0x0054, 0x2b : 0x0055, 0x2c : 0x0056, 0x2d : 0x0063, 0x2e : 0x0064, 0x2f : 0x0065, 0x30 : 0x003b, }, # IN3
        0x44 : {0x2a : 0x0069, 0x2b : 0x006a, 0x2c : 0x006b, 0x2d : 0x006c, 0x2e : 0x006d, 0x2f : 0x006e, 0x30 : 0x0070, }, # IN4
        0x45 : {0x2a : 0x006c, 0x2b : 0x006d, 0x2c : 0x006e, 0x2d : 0x0055, 0x2e : 0x0072, 0x2f : 0x0073, 0x30 : 0x0074, }, # IN5
        0x46 : {0x2a : 0x0069, 0x2b : 0x006a, 0x2c : 0x006b, 0x2d : 0x006f, 0x2e : 0x0070, 0x2f : 0x0071, 0x30 : 0x0073, }, # IN6
        0x47 : {0x2a : 0x0076, 0x2b : 0x0079, 0x2c : 0x007c, 0x2d : 0x007f, 0x2e : 0x0082, 0x2f : 0x0091, 0x30 : 0x0063, }, # IN7
        0x48 : {0x2a : 0x0082, 0x2b : 0x0089, 0x2c : 0x0088, 0x2d : 0x008e, 0x2e : 0x008f, 0x2f : 0x0093, 0x30 : 0x0097, }, # IN8
        0x49 : {0x2a : 0x0085, 0x2b : 0x0086, 0x2c : 0x0084, 0x2d : 0x0093, 0x2e : 0x0094, 0x2f : 0x008e, 0x30 : 0x008f, }, # IN9
        0x4a : {0x2a : 0x0099, 0x2b : 0x009c, 0x2c : 0x009d, 0x2d : 0x00a0, 0x2e : 0x00a6, 0x2f : 0x0081, 0x30 : 0x0082, }, # IN10
        0x4b : {0x2a : 0x00a8, 0x2b : 0x00a9, 0x2c : 0x00aa, 0x2d : 0x009c, 0x2e : 0x009d, 0x2f : 0x007f, 0x30 : 0x007c, }, # IN11
        0x4c : {0x2a : 0x008b, 0x2b : 0x00ac, 0x2c : 0x00a8, 0x2d : 0x00a9, 0x2e : 0x008f, 0x2f : 0x008e, 0x30 : 0x0085, }, # IN12
        0x4d : {0x2a : 0x0085, 0x2b : 0x0089, 0x2c : 0x0087, 0x2d : 0x0088, 0x2e : 0x009a, 0x2f : 0x0099, 0x30 : 0x0096, }, # IN13

        # Default values
        None : {0x2a : 0x002d, 0x2b : 0x002e, 0x2c : 0x002f, 0x2d : 0x0030, 0x2e : 0x0031, 0x2f : 0x0032, 0x30 : 0x0034, }, # DEFAULTS
    }

    # Note that the default target_pad values are relevant since our earlier rooms in the roomPath aren't mapped
    #   indeed until the left turn after the red car
    # We're mainly concerned about the civilians here
    #   2B (civilian 1) picks 2E i.e. the next pad for RED so he's likely going to cause us problems
    #     We're after the RED spawn at 35, so this guy will be a second later at 36.
    #     Ideally lets make that a low 36 and a high 35, then he'll get out of the way quickly. 
    #   2D (civilian 2) picks 30, i.e. nearer us than RED on 31. But he'll head to RED's 31 coz routing.
    #     Presumably our BLUE spawn is at 27 (RED is at 30 right)? So 24.. and we may not quite be in range!
    #     So keep this timer running as cleanly as possible too.
    # =>
    #   - 9s timer, dunno what we're doing with it
    #   - 8s timer, keep low
    #   - 6s timer, keep low
    #   - 5s timer, keep high
    # And probably still instacut though keeping the 5s timer high we're effectively cutting a bit more cinema?

    # So finally make a mapping from our rooms to the RED spawner (2A)'s spawn location
    # Note that room 0x1C maps to label 0x43, so RED spawning at 0x0054, which is near the end of the right fork there
    # But this guard will always head back down the path, so this spawn is useless
    spawnPath = getPathBetweenPads(0x0054, 0x003E, sets, pads)
    
    allSpawnLocs = set()

    # RED!
    for r in roomPath:
        redSpawnPad = labelToSpawnLocs[bondRoomToLabel.get(r)][0x2A]
        allSpawnLocs.add(redSpawnPad)
        ##print(f"{r:02x} : {redSpawnPad:04x}")
    ##print("")

    """
    RED (standing guard, ID 0x20, 5s timer):
    0b,13,12,06,05,04,03 : 002d (outside of 2nd left corner)
        => can't get these, we're too early
    14,15,16 : 0036 (outside of the corner before kf7 guards. Can't spawn until some way into 14)
        => stop this by looking at him? Blue will be 1s into his segment within his own room so this won't be an issue
        => also can get a slow death anim if that's what we need. Flexible :)
        => * yes this is what we need
    17,18,19 : 004c (after between-the-cars -> well into the right branch) (very bad)
        => prevent using the death animation of the previous
        get one of these, surely the first
    1a,1b,24 : 0069 (pre 1st set -> right side, early on long straight) (*)
        => pathing looks like he'll head straight in ASAP, should at least make 6A
        => so we want to get this early on 1a (TODO timing (pray basically coz the below is more important))
    23,22 : 006c  (pre long straight -> right side of longstraight)
        => similar pathing, but the room is so much later, surely the above one will be better
        either of these would be fine:
    25,26,27 : 0076 (long straight -> just BEFORE the corner) (very start of 25 isn't in range) (*)
    28,29 : 0082 (very end of long straight -> 111 position)
        => common with BLUE! Could be problematic. But the one above is an obvious choice.
    2a,2b : 0085 (on approach to final set -> just past that set, very nice) (~*)
        => may be tricky to get! Calle is in there for ~3s, and we'll have a death animation at the start of it.
        => if we do get it, it's boosts to the END
        I think we'll have too many grenades anyway lol!
    2c,2d,2e : 00a8 (rightmost guard before the ending - should still spawn fine, check routing)
    35, : 0085  (just behind us, could give boost)
    36 : 002d   (default, right back at the beginning)
    37 : 0085   (too late)
    """

    # BLUE!
    for r in roomPath:
        blueSpawnPad = labelToSpawnLocs[bondRoomToLabel.get(r)][0x2e]
        allSpawnLocs.add(blueSpawnPad)
        ##print(f"{r:02x} : {blueSpawnPad:04x}")
    ##print("")

    """
    BLUE (running guard, ID 0x22, 9s timer)
    0b,13,12,06,05,04,03 : 0031 (behind left corner)
        => can't get these, we're too early
    14,15,16 : 003e (111 1st boost) (*)
        => pretty flexible, though be aware we can't be too early or we won't be in 16 anymore
    17,18,19 : 0046 (outside of next corner) (bad but we'll avoid it easy)
    1a,1b,24 : 006d (mid of long straight, bad on console on agent..) (X)
        => he's not far away from the wall, we can just drift outward a touch
        => ! We're unlikely to make the jump in 9s, so it'll have to be 18 instead.
            But that's being slow on console, and we'll be boosting like mad..
        .. so maybe we do try to make it in 9..
        .. yeah I'm making it on console with 1 boost?
        TODO TIMING this will be what we'll go for. Considering the below I think we want to make it as tight as possible.
        !!! FIXME but although we'll make the room we're not in range of the spawn point..
        And 18s will just mean sandbagging i.e. leaving us no time to boost
        And we can't move a cycle, else we won't make the 1st spawn.
    23,22 : 0072 (outside corner at the end of long straight, probably not unless he can make enough unloaded progress)
        => Too far, he'll despawn.. always?
    25,26,27 : 0082 (common with RED, but it works nicely for us to take it) (*)
        => should work easy, we'll trigger it sometime in the middle of the long straight
        This is the 2nd GL on console.. we're gonna get it.

    All of these are bad:
    28,29 : 008f (right fork at the end) (BAD)
    2a,2b : 0094 (right fork) (BAD)
    2c,2d,2e : 009d (end of the right fork, too late) (BAD)
    35 : 009a (near end of right fork) (BAD)
    36 : 0031 (default, back at the start) (BAD)
    37 : 009a (too late!)
    """

    chosenSpawnLocs = [
        ([0x003e, 0x0082], 'b'),    # BLUE      # RIP 0x006d, we're just doing the normal ones
        ([0x0069, 0x0076, 0x0085], 'r'),     # RED. 69 may be a bit sus, we need to keep him unloaded to pull him over.
                # So will definitely want FULL if we're looking vaguely upwards.
    ]
    # No way are we getting through 3 GLs in the ending though, so it's gonna be 4
    
    # Finally I think we want to do the timing so that we spawn RED asap at his first pad i.e. 0069
    # So this is just after the 1st BA
    # Calle makes it about 1s early. My run could cut maybe 2s early and still get 1st spawn
    # But we're asking ourselves to cover a mad amount of ground in 11s so I think we'll just have to watch the entire cinema.

    # It's no use timing for the end of the run because we don't know what'll happen
    # QED

    for sps, colour in chosenSpawnLocs:
        for sp in sps:
            x,_,z = pads[sp]["position"]
            axs.add_artist(plt.Circle((-x, z), 8000, color=colour, alpha=0.5, linewidth=1, fill=False))
            axs.add_artist(plt.Circle((-x, z), 100, color=colour, linewidth=1, fill=False))

            spawnPath = getPathBetweenPads(padNearVal, sp, sets, pads)
            # Entire path atm so we can check
            drawPathWithinGroup(plt, axs, spawnPath[-4:], pads, currentTiles, tiles, None)


    # Further analysis of the unloaded paths that guards start taking
    padAndPathLens = [
        ##(0x0072, 3),    # BLUE, end of long straight
        ##(0x006c, 2),   # RED, alternative that we're confident is worse
    ]
    for p,l in padAndPathLens:
        spawnPath = getPathBetweenPads(padNearVal, p, sets, pads)
        drawPathWithinGroup(plt, axs, spawnPath[-(l+1):], pads, currentTiles, tiles, None)
    
    # Some lengths of paths that we're worried about, and final notes
    STD_SPEED = 5.4807696015788
    spawnPath = getPathBetweenPads(0x002D, padNearVal, sets, pads)[:3]
    t = getPathTime(None, spawnPath, pads, STD_SPEED) / 60
    
    # The 5s to get the 1st RED to move looks pretty tight, we're going to have to hope that this cinema timing works out
    ##print(", ".join(map(hex, spawnPath)))
    ##print(t)

    # TODO : consider the civilian spawns, since they may block where we are relying on guards moving unloaded.


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
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets))
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    # Call specific code
    streets_specific(tilePlanes, currentTiles, plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_STREETS_START, "streets/streets_start")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_STREETS_MID, "streets/streets_mid")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_STREETS_END, "streets/streets_end")