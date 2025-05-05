from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects, markBadDoors
from lib.circle_related import drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup
from lib.set_boundaries import drawSetBoundaries
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil, atan2, atan, pi, cos, sin, acos

# --------------------------------------------------------
# egyptian SPECIFIC

from level_specific.egyptian.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.egyptian import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects, lone_pads
from level_specific.egyptian.group_names import *
import numpy as np

def get_GG_room_limits(tiles):
    cps = set(tiles[0x1BB494]["points"]).intersection(set(tiles[0x1BB4B4]["points"]))
    assert(len(cps) == 1)
    low_x,_ = cps.pop()
    cps = set(tiles[0x1BB314]["points"]).intersection(set(tiles[0x1BB2D4]["points"]))
    assert(len(cps) == 1)
    high_x,_ = cps.pop()

    cps = set(tiles[0x1BB394]["points"]).intersection(set(tiles[0x1BB3D4]["points"]))
    assert(len(cps) == 1)
    _,low_z = cps.pop()
    cps = set(tiles[0x1BB2D4]["points"]).intersection(set(tiles[0x1BB414]["points"]))
    assert(len(cps) == 1)
    _,high_z = cps.pop()

    return low_x, high_x, low_z, high_z


def egyptian_specific(tilePlanes, currentTiles, plt, axs):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())

    low_x, high_x, low_z, high_z = get_GG_room_limits(tiles)

    tx = (high_x - low_x) / 18
    low_x = low_x + tx * 6  # bring us up to the room
    
    # x looks good, but we're hacking here
    tz = tx * 1.008


    grey = (0.3,0.3,0.3)

    # Draw all the lines
    for x_i in range(0,12):
        x = low_x + x_i * tx
        plt.plot([-x,-x], [low_z, high_z], linewidth=0.5, color=grey)

    for z_i in range(1,6):
        z = low_z + z_i * tz
        plt.plot([-low_x, -high_x], [z,z], linewidth=0.5, color=grey)

liveArtists = []

def gg_room(plt, axs, gg_room_cycle=None):
    # GG room!
    triggerPads = [
        ('k', list(range(0x97, 0x9C))),
        ('r', list(range(0x9C, 0xA1))),
        ('#d67113', list(range(0xA1, 0xA6)) + [0xA7, 0xA8]),    # orange
        ('m', list(range(0xA9, 0xAF))),
    ]

    BOND_HEIGHT = 167.3 - 12.6  # -12.6 is the reduction by fullspeed

    global liveArtists

    INACTIVE_ALPHA = 0.2
    ACTIVE_ALPHA = 1

    for i,(waveColour, pads) in enumerate(triggerPads):
        alpha = ACTIVE_ALPHA if gg_room_cycle in [i, None] else INACTIVE_ALPHA

        for pNum in pads:
            pad = lone_pads[pNum]
            x,y,z = pad["position"]
            hs = set(tiles[pad["tile"]]["heights"])
            assert len(hs) == 1

            # Bond's height above the pad
            h = hs.pop() + BOND_HEIGHT - y
            r = sqrt(90**2 - h**2)
            liveArtists.append(axs.add_artist(plt.Circle((-x, z), r, color=waveColour, linewidth=0.5, fill=False, alpha=alpha)))


    # Special final trigger, effectively a purple
    pad = lone_pads[0xA6]
    x,y,z = pad["position"]
    hs = set(tiles[pad["tile"]]["heights"])
    assert len(hs) == 1
    h = hs.pop() + BOND_HEIGHT - y
    r = sqrt(100**2 - h**2)

    alpha = ACTIVE_ALPHA if gg_room_cycle in [3, None] else INACTIVE_ALPHA
    liveArtists.append(axs.add_artist(plt.Circle((-x, z), r, color='g', linewidth=1, fill=False, alpha=alpha)))


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
    egyptian_specific(tilePlanes, currentTiles, plt, axs)
    gg_room(plt, axs)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


# ==============================================
# Special for making a gif of just the tile warp

from matplotlib.animation import FuncAnimation

axs = None  # global

def gif_update(frame_i):
    # Clear previous
    global liveArtists
    for a in liveArtists:
        a.remove()
    liveArtists = []

    # frame_i pretend 1/60th of a second
    # so we convert this to game frames, considering stable 30fps except where there's the lag spike
    # lag spike is 5 instead of 2, so effectively take off 3

    LAG_SPIKE_START = 20
    LAG_SPIKE_END = 25
    NORMAL_FRAME_WIDTH = 2
    WARPING = False
    if frame_i >= LAG_SPIKE_END:
        frame_i -= (LAG_SPIKE_END - LAG_SPIKE_START - NORMAL_FRAME_WIDTH)
    elif frame_i >= LAG_SPIKE_START:
        WARPING = frame_i >= LAG_SPIKE_START + NORMAL_FRAME_WIDTH
        frame_i = LAG_SPIKE_START
        
    game_frame_i = frame_i // NORMAL_FRAME_WIDTH
    
    # Round either to even or odd as appropriate
    # Relies on the values being 5 and 2?
    shown_frame_i = frame_i - (frame_i % NORMAL_FRAME_WIDTH)
    if frame_i > LAG_SPIKE_START:
        shown_frame_i += (LAG_SPIKE_END - LAG_SPIKE_START - NORMAL_FRAME_WIDTH)


    low_x, high_x, low_z, high_z = get_GG_room_limits(tiles)

    tx = (high_x - low_x) / 18
    low_x = low_x + tx * 6  # bring us up to the room
    tz = tx * 1.008

    # Draw the relevant triggers
    if game_frame_i >= 1:
        gg_room(plt, axs, (game_frame_i-1) % 4)
        wave_no = 1 + ((game_frame_i - 1) // 4)
        x = low_x - tx * 0.25
        z = low_z + tz * 0.25
        liveArtists.append(axs.text(-x, z, f"Wave {wave_no}", fontsize="small"))
    elif game_frame_i == 0:
        gg_room(plt, axs, -1)
        x = low_x - tx * 0.25
        z = low_z + tz * 0.25
        liveArtists.append(axs.text(-x, z, f"Entered GG room", fontsize="small"))


    # Draw Bond
    speed = 13.5   # cm / frame

    p1 = (low_x + 0.1*tx, low_z + 2*tz + 50)
    p2 = (low_x + 1.333*tx, low_z + 3*tz)

    # And place Bond at p1 at time (0), moving with the specified speed
    d = np.linalg.norm(np.subtract(p2,p1))
    f = d / speed

    if shown_frame_i < 0:
        # Entering the tunnel
        x,z = p1
        x += shown_frame_i * speed

    elif shown_frame_i < f:
        # On the diagonal
        x1,z1 = p1
        x2,z2 = p2
        x = (x2 * shown_frame_i + x1 * (f - shown_frame_i)) / f
        z = (z2 * shown_frame_i + z1 * (f - shown_frame_i)) / f

    else:
        # Straight again
        x,z = p2
        x += (shown_frame_i - f) * speed

    liveArtists.append(axs.add_artist(plt.Circle((-x, z), 30, color='g', linewidth=0.5, fill=False)))
    liveArtists.append(axs.add_artist(plt.Circle((-x, z), 5, color='g', linewidth=0.5, fill=True)))

    # If warping, show some text
    if WARPING:
        x,z = p2
        z -= tz*0.42
        x += tx*1.40
        liveArtists.append(axs.text(-x, z, "(lag)", fontsize="small"))


def gif_main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GROUP_NO, fn):

    # Still do the standard prep
    prepTiles(tiles)
    tile_groups = seperateGroups(tiles, startTileName, dividingTiles)
    groupBounds = getGroupBounds(tiles, tile_groups)
    prepSets(sets, pads)

    # First, focus on the entrance
    lx, hx, lz, hz = get_GG_room_limits(tiles)
    sx = (lx*3 + hx) / 4
    ex = (lx + hx*2) / 3
    global axs
    fig, axs = prepPlot(plt, (sx, ex, lz, hz))

    # Group prep
    currentTiles = set(tile_groups[GROUP_NO])
    tilePlanes = getTilePlanes(currentTiles, tiles, level_scale)

    # Draw everything fixed
    drawTiles(currentTiles, tiles, (0.75, 0.75, 0.75), axs)
    markStairs(tilePlanes, tiles, (0.4,0.2,0), plt) # make generic
    drawTileHardEdges(currentTiles, tiles, (0.65, 0.65, 0.65), axs)

    drawGuards(guards, currentTiles, plt, axs)
    drawObjects(plt, axs, objects, tiles, currentTiles)
    markBadDoors(objects, "egypt")
    drawDoorReachability(plt, axs, objects, presets, currentTiles, set(excludeDoorReachPresets))
    drawCollectibles(objects, plt, axs, currentTiles)

    drawActivatables(plt, axs, activatable_objects, objects, currentTiles)

    #  including the GG tile lines
    egyptian_specific(tilePlanes, currentTiles, plt, axs)

    fp = os.path.join("output", "egypt", fn)
    zoomed_fp = os.path.join("output", "egypt", "zoomed_" + fn)
    anim = FuncAnimation(fig, gif_update, frames=np.arange(-8, 36), interval=1000/3)
    anim.save(fp, dpi=200) # still doesn't seem to produce 60 fps

    anim = FuncAnimation(fig, gif_update, frames=np.arange(14, 30), interval=1000)
    anim.save(zoomed_fp, dpi=200) # still doesn't seem to produce 60 fps





gif_main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_MAIN, "gg_room_anim.gif")

main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_MAIN, "egypt/egyptian_main")
main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_LOWER, "egypt/egyptian_lower")