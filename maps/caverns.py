from lib.seperate_tile_groups import seperateGroups
from lib.tiles import prepTiles, drawTiles, getGroupBounds, prepPlot, drawTileHardEdges, getTilePlanes
from lib.object import drawObjects
from lib.circle_related import drawDoorReachability
from lib.stairs import markStairs
from lib.path_finding import prepSets, getPathBetweenPads, drawPathWithinGroup
from lib.set_boundaries import drawSetBoundaries
from lib.misc import *
import matplotlib.pyplot as plt
import os
from math import sqrt, floor, ceil, atan2, atan, pi, cos, sin, acos

# --------------------------------------------------------
# Caverns SPECIFIC

from level_specific.caverns.details import dividingTiles, startTileName, excludeDoorReachPresets
from data.caverns import tiles, guards, objects, pads, level_scale, sets, presets, activatable_objects
from level_specific.caverns.group_names import *
import numpy as np
from lib.path_finding import rotACWS

def clipTileInsideRectangle(tile, x1, x2, z1, z2):
    assert x1 < x2 and z1 < z2
    js = [1,0,1,0]
    es = [0,0,1,1]
    limits = [[x1,x2], [z1,z2]]
    rectPnts = [(x1,z1), (x1,z2), (x2,z2), (x2,z1)]

    pnts = tile['points']
    collisions = []

    x,z = pnts[0]
    inside = (x1 < x < x2 and z1 < z < z2)

    def getK(d,r):
        if r != 0:
            return d / r
        elif d == 0:
            return 0
        else:
            return 2    # inf

    for ti, (p,q) in enumerate(zip(pnts, pnts[1:] + [pnts[0]])):
        px, pz = p
        v = np.subtract(q,p)
        vx, vz = v
        
        ks = [getK(x1-px,vx), getK(z1-pz,vz), getK(x2-px,vx), getK(z2-pz,vz)]
        edgeCollisions = []
        for i in range(4):  # i the edge number in j
            # Check we intersect within this segment
            if ks[i] > 1 or ks[i] < 0:
                continue

            # Find the collision point r
            r = tuple(np.add(p, np.multiply(v, ks[i])))

            # Check that it's within the rectangle's edge segment
            j = js[i]
            rc = r[j]
            l,h = limits[j]
            if rc < l or rc > h:
                continue

            # Add our collision
            entering = (v[1-j] < 0) ^ (es[i] == 0)  # won't cope with touching a corner
            edgeCollisions.append((ti, ks[i], i, entering, r))

        edgeCollisions.sort()
        collisions.extend(edgeCollisions)

        if len(edgeCollisions) > 0:
            inside = edgeCollisions[-1][3]

        if inside:
            collisions.append((ti, 1, 4, None, q))


    if len(collisions) == 0:
        if inside:
            return pnts
        else:
            return []        

    pnts = []
    lastLeave = next(ri for _, _, ri, entering, _ in collisions[::-1] if not entering)
    for ti, k, ri, entering, p in collisions:
        if entering:
            i = ri
            while i != lastLeave:
                pnts.append(rectPnts[i])
                i = (i + 1) % 4
            lastLeave = None
        
        pnts.append(p)
    
        if not entering:
            lastLeave = ri

    return pnts



def debug(plys):
    fig = plt.figure()
    ax = plt.axes()
    ax.set_aspect('equal', 'datalim')

    for plyI, plyPnts in enumerate(plys):
        if len(plyPnts) == 0:
            continue
        xs, ys = zip(*(plyPnts + [plyPnts[0]]))
        plt.plot(xs, ys)
        plt.scatter(xs, ys)
        
        for i,(x,y) in enumerate(plyPnts):
            plt.text(x,y,(plyI,i))

    plt.show()


def caverns_mine_placements(tilePlanes, currentTiles, s_pos, radio_s_pos, plt, axs, GROUP_NO):
    rightConsole = objects[0x1C8FC8]
    c_x, c_z = rightConsole['position']
    cHeight = rightConsole['height']

    # Mine? related constants
    min_damage_radius = 300
    max_damage_radius = 480
    damage_factor = 4
    waves = [0.05, 0.30, 0.55, 0.80]
    exp_radii = [min_damage_radius + (max_damage_radius-min_damage_radius)*w for w in waves]
    # max is 444
    
    # Looking back at this, note that explosions have a separate width (x/z) and height (y)
    # If the object is in the bounding box, it scales this down to a cube 1,1,1.
    # Take dimension that object is furthest on, say x.
    # Compute d = 1-x, so larger the closer it is
    # Damage is d * rand(1.0, 1.5) * damage_factor, and further gets a * 250 later since the health is 1000
    def getWorseCaseDamage(r, target, verbose=False):
        hs = [max(er - r, 0) for er in exp_radii]
        fs = [damage_factor * 250 * h / er for h,er in zip(hs, exp_radii)]
        if verbose:
            print(hs)
        expectedDamage = sum(fs)  # no RNG multiplier (should be 1.0 - 1.5 per)
        return expectedDamage / target['health']

    # For SA, consider whether 1 mine can in fact destroy both the <B> room consoles - nope
    bRoomLeftConsole = objects[0x1C9EA0]
    bRoomRightConsole = objects[0x1C9774]
    l_x, l_z = bRoomLeftConsole["position"]
    r_x, r_z = bRoomRightConsole["position"]
    r = max(abs(l_x - r_x), abs(l_z - r_z)) / 2
    ##print(f"SA r = {r}")
    ##print(f"SA Damage = {getWorseCaseDamage(r-100, bRoomLeftConsole)} aka not possible")

    # Also entertain the idea that only our mine could blow up at the end,
    #   and draw a square around the right scientist in that room
    # It looks impossible because the mine is skidding and needs to go between the boxes?
    for r in exp_radii:
        x, z = radio_s_pos
        xs = [x-r, x-r, x+r, x+r]
        zs = [z-r, z+r, z+r, z-r]
        xs = [-x for x in xs]
        plt.plot(xs, zs, color='r', linewidth=1)

    # If it is stopped by the box on the near side, that will actually explode the barrel
    #   though it needs to be on the left side of that box, and flush to it (may not be possible)
    leftMostBox = objects[0x1CBE60]
    nearBarrel = objects[0x1CB520]
    p = leftMostBox["points"][0]
    q = leftMostBox["points"][-1]
    # Only approximate, we should compute it really, for some probability of boom
    k = 0.2     # 0.2 -> 66.31% , which equates to 0% chance of actual destruction
    r = k*p[1] + (1-k)*q[1] - nearBarrel["position"][1]
    d = getWorseCaseDamage(r, nearBarrel)
    print(f"Line on Obj C box has worst-case damage of {d*100:.2f}%")
    # d < 2/3

    # Considering that it'll be held back by its own thickness, we account for this,
    #   but only for drawing the line
    projectile_width_estimate = 8
    k += projectile_width_estimate/(q[1]-p[1])

    q = (p[0] * k + q[0]*(1-k), p[1] * k + q[1]*(1-k))
    xs, zs = zip(p,q)
    xs = [-x for x in xs]
    plt.plot(xs,zs,color='g',linewidth=2)


    if GROUP_NO != GRP_DOWNSTAIRS:
        return

    # ================== Downstairs only ==================

    # Special mine placement, testing 1m right of the scientist
    z = s_pos[1] - 100
    r = c_z - z
    print(f"1m right of scientist r = {r}")
    c = expectedDamage = getWorseCaseDamage(r, rightConsole, True)
    plt.plot((-s_pos[0], -c_x + r), (z, z), color=(1-c, c, 0), alpha=0.2)
    plt.text(-c_x + r, z - 10, f"{expectedDamage:.3f}")

    # Another special, Icy-like throw
    r = 380     # measured, since we don't have access to the background
    print(f"Icy throw, r = {r}")
    c = expectedDamage = getWorseCaseDamage(r, rightConsole, True)
    plt.plot((-c_x-r,-c_x-r), (c_z-r,c_z+r), color=(1-c, c, 0), alpha=0.7)
    plt.text(-c_x-r+15, c_z+r-55, f"{expectedDamage:.3f}")

    # And the plan for where to put the 3rd one - right on the very edge
    edgeZ = tiles[0x1B1D9C]['points'][0][1]
    r = c_z - edgeZ
    print(f"Edge r = {r}")
    c = expectedDamage = getWorseCaseDamage(r, rightConsole, True)
    plt.plot((-s_pos[0], -c_x + r), (edgeZ, edgeZ), color=(1-c, c, 0), alpha=0.2)
    plt.text(-c_x + r + 100, edgeZ - 12, f"{expectedDamage:.3f}")



    for (consoleAddr, drawLow) in [(0x1C8FC8, False), (0x1C922C, True)]:    #, (0x1C8B00, True)]:
        console = objects[consoleAddr]
        c_x, c_z = console['position']
        cHeight = console['height']

        for (n,a), tileAddrs in tilePlanes.items():
            if n != (0,1,0):
                continue
            y = a - cHeight
            if (y < 0 and not drawLow) or y > exp_radii[-1]:
                continue
            r = abs(y)

            # The actual explosion is slightly clear of the surface
            r += 5.3955
            
            expectedDamage = getWorseCaseDamage(r, console)
            c = min(expectedDamage, 1)
            c = (1-c, c, 0)

            allPnts = []
            for ta in tileAddrs:
                pnts = clipTileInsideRectangle(tiles[ta], c_x - r, c_x + r, c_z - r, c_z + r)

                """
                # debug
                x1, x2, z1, z2 = (c_x - r, c_x + r, c_z - r, c_z + r)
                rectPnts = [(x1,z1), (x1,z2), (x2,z2), (x2,z1)]
                debug([tiles[ta]['points'], rectPnts, pnts,])
                """

                if pnts == []:
                    continue
                allPnts.extend(pnts)
                xs,zs = zip(*pnts)
                plt.fill([-x for x in xs], zs, alpha=0.2, fc=c)

            if allPnts == []:
                continue

            xs,zs = zip(*allPnts)
            x = sum(xs) / len(xs)
            z = sum(zs) / len(zs)
            plt.text(-x,z, f"{expectedDamage:.3f}")


def caverns_specific(tilePlanes, currentTiles, plt, axs, GROUP_NO):
    guardAddrWithId = dict((gd["id"], addr) for addr, gd in guards.items())

    # SA A from above strats
    scientist1 = guards[guardAddrWithId[0x4B]]
    scientist2 = guards[guardAddrWithId[0x49]]
    scientist3 = guards[guardAddrWithId[0x4A]]

    # Alerting prior
    noiseAroundGuardHelper(scientist1, [19.85], tilePlanes, tiles, plt, axs, '#d1512e', base_alpha=1, fill=False)

    # Alerting after
    # -> 7 shots gives < 15.1 noise, seems too little
    # -> 8 shots gives < 16.8, should do nicely
    noiseAroundGuardHelper(scientist1, [15], tilePlanes, tiles, plt, axs, '#d1512e', base_alpha=1, fill=False)

    # Calculations for considering using noise alone for the 2nd & 3rd scientist
    xs, _ = zip(*tiles[0x1B169C]["points"])
    wall_x = min(xs)
    
    ubend_corner = min(tiles[0x1B18BC]["points"])
    pBothRun = 1
    for sci in [scientist2, scientist3]:
        ws_x = sci['position'][0] - wall_x
        v = np.subtract(ubend_corner, sci['position'])
        c = -cos(atan2(*v))
        req_run = 444 - ws_x - (200*c)
        p = 1 - (req_run / (c*200))
        pBothRun *= p

    print(f"#2 & #3 will run far enough {100*pBothRun:.3f}% of the time")
    
    # Mine placements for A from above
    s_pos = scientist1["position"]
    radio_s_pos = guards[guardAddrWithId[0x55]]["position"]
    caverns_mine_placements(tilePlanes, currentTiles, s_pos, radio_s_pos, plt, axs, GROUP_NO)

    STEP = scientist1['radius'] * 1.2

    def drawHeadingLine(heading, mainLen, armLen):
        # Note armLen is signed
        v = (sin(heading), -cos(heading))
        q = np.add(s_pos, np.multiply(v, mainLen))

        xs, zs = zip(s_pos, q)
        plt.plot([-x for x in xs], zs, linewidth=0.5, color='k')

        if armLen != 0:
            p = np.add(s_pos, np.multiply(v, STEP))
            x, z = v
            q = np.add(p, np.multiply((-z, x), armLen))
            xs, zs = zip(p, q)
            plt.plot([-x for x in xs], zs, linewidth=0.5, color=(0.5,0.5,0.5))


    # Draw the line that we have to stay right of
    rightConsole = objects[0x1C8FC8]
    corner = rightConsole["points"][0]
    v = np.subtract(s_pos, corner)
    c = np.linalg.norm(v)
    a = STEP
    ang = atan(a / c)
    x,z = v
    heading = atan2(-x, z) + ang - pi/2
    
    drawHeadingLine(heading, 1400, 400 + STEP)

    #  Also do some computations for the prom
    sAng = pi - scientist1["facing_angle"]  # transformation confirmed with heading
    relativeHeading = heading - sAng
    cmdArg = 128*relativeHeading / pi
    cmdArg = 256 - cmdArg
    ##print(f"Command argument should be (dec) {cmdArg}")
    ##print(f"  rounded = 0x{round(cmdArg):x}")
    # 22.991 so 23 will work just fine

    # And the angle that we want to be at to make him run in a good direction (96% up)
    heading = acos(0.96) + pi/2
    drawHeadingLine(heading, 400, 0)
    relativeHeading = heading - sAng
    cmdArg = 128*relativeHeading / pi
    cmdArg = 256 - cmdArg
    ##print(f"Command argument should be (dec) {cmdArg}")
    ##print(f"  rounded = 0x{round(cmdArg):x}")

    # Make a circle just for consideration of how soon to turn in, 8 seems appropriate
    ##noiseAroundGuardHelper(scientist1, [8], tilePlanes, tiles, plt, axs, '#139163', base_alpha=1, fill=False)

    

    # Likewise draw the line that he'll run along (4m)
    corner = tiles[0x1B291C]['points'][2]
    x,z = np.subtract(corner, s_pos)
    z += 30     # Bond radius
    v = (-z, x)
    k = 400 / np.linalg.norm(v)
    q = np.add(s_pos, np.multiply(v, k))

    xs, zs = zip(s_pos, q)
    plt.plot([-x for x in xs], zs, linewidth=0.5, color='g')

    # Also check he can't try to run the wrong way early on
    c = sqrt(STEP**2 + (200 + STEP)**2)  # 2m, a step to the side and a step forward
    corner1 = tiles[0x1B257C]['points'][1]
    corner2 = tiles[0x1B25BC]['points'][2]
    v = np.subtract(s_pos, corner1)
    w = np.subtract(corner2, corner1)

    a = np.linalg.norm(v)
    len_w = np.linalg.norm(w)
    cos_C = np.dot(v,w) / (a * len_w)
    sin_C = sqrt(1 - cos_C**2)

    sineRuleConst = sin_C / c
    sin_A = a * sineRuleConst
    cos_A = sqrt(1 - sin_A**2)
    A = acos(cos_A)
    C = acos(cos_C)
    B = pi - A - C
    
    x,z = v
    heading = atan2(-x,z) - B + atan((200 + STEP) / STEP)
    drawHeadingLine(heading, 3500, -200-STEP)

    
    # And draw noise for the other guard
    annoyingGuard = guards[guardAddrWithId[0xA]]
    noiseAroundGuardHelper(annoyingGuard, [19.85], tilePlanes, tiles, plt, axs, '#d1512e', base_alpha=1, fill=False)


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
    caverns_specific(tilePlanes, currentTiles, plt, axs, GROUP_NO)

    # Save
    saveFig(plt,fig,os.path.join('output', path))


if __name__ == "__main__":
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_DOWNSTAIRS, "caverns/caverns_main_downstairs")
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_OBJ_A_AREA, "caverns/caverns_objective_a_area")
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_MAIN_UPSTAIRS, "caverns/caverns_main_upstairs")
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_UPSTAIRS_LOWER_CATWALK, "caverns/caverns_upstairs_lower_catwalk")
    main(plt, tiles, dividingTiles, startTileName, objects, level_scale, GRP_SPIRAL_MIDDLE, "caverns/caverns_spiral_middle")
