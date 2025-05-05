import numpy as np
from math import atan2, pi, sqrt
from matplotlib import patches
from bisect import bisect_left

def roundIfClose(r):
    n = round(r)
    if abs(r-n) < 0.0001:
        return n
    return r

def splitIntoPolygonAndArcs(points, center, radiusSq):
    """
    Breaks the circle down into arcs and the intersection with the given circle. 
    used below but also for door reachability.
    """
    assert len(points) > 1

    def inCircle(p):
        v = np.subtract(p,center)
        return np.dot(v,v) <= radiusSq

    # Init
    inside = inCircle(points[-1])
    polygon = [points[-1]] if inside else []
    arcLeaves = []
    arcEnters = []

    origIndexInInner = []

    for i,currPoint in enumerate(points):
        origIndexInInner.append(len(polygon) - 0.5)

        prevPoint = points[i-1]
        ##print("\nConsidering {} -> {}".format(i-1, i))

        # Find the closest point on (infinite) edge to the circle center
        edge = np.subtract(currPoint, prevPoint)
        ##print("Edge = {}".format(edge))
        w = np.subtract(center, prevPoint)
        edge_length = np.linalg.norm(edge)
        closest_a = np.dot(edge,w) / edge_length
        ##print("Closest a = {}, edge_length = {}".format(closest_a, edge_length))
        closestPoint = np.add(prevPoint, np.multiply(edge, closest_a / edge_length))

        # Find the range on the edge that is inside
        w = np.subtract(closestPoint, center)
        deltaSq = np.dot(w,w)
        if deltaSq < radiusSq:
            delta = sqrt(radiusSq - deltaSq)
            ##print("Infinite line in range, delta = {}".format(delta))
            entry = max(closest_a - delta, 0)
            leave = min(closest_a + delta, edge_length)

            if not inside:
                if leave > entry:
                    ##print("->")
                    # we were outside, we've entered back in
                    pntA = np.add(prevPoint, np.multiply(edge, entry / edge_length))
                    polygon.append(pntA)
                    arcLeaves.append(len(polygon) - 1) # we enter, arc leaves

                    pntB = np.add(prevPoint, np.multiply(edge, leave / edge_length))
                    polygon.append(pntB)    # may be next point, or actual leave
                    inside = (leave == edge_length)
                    if not inside:
                        ##print("<-")
                        arcEnters.append(len(polygon) - 1)
            else:
                if leave > 0:   # don't duplicate the point if we literally leave on it
                    pntB = np.add(prevPoint, np.multiply(edge, leave / edge_length))
                    polygon.append(pntB)

                if leave < edge_length:
                    # we were inside, now we've left
                    inside = False
                    ##print("<-")
                    arcEnters.append(len(polygon) - 1)  # we leave, so arc enters

        else:
            ##print("Infinite line out of range")
            if inside:
                # leave = 0 effectively, don't add previous point but add the arcEnters
                arcEnters.append(len(polygon) - 1)
                ##print("<-")

            inside = False  # infinite line is outside

    # Edge case for if we just enter immediately
    if len(arcLeaves) == len(arcEnters) - 1:
        arcLeaves.append(points[-1])
    assert len(arcLeaves) == len(arcEnters)

    if len(arcLeaves) > 0:
        arcLeaves = arcLeaves[1:] + [arcLeaves[0]]  # shuffle which we think is correct
    arcs = list(zip(arcEnters, arcLeaves))

    return polygon, arcs, origIndexInInner

def getSphereIntersection(plane, tileAddrs, sphere_center, sphere_radius, tiles):
    # Compute distance to the plane. If too far, no intersection
    n,a = plane
    disp = np.dot(n,sphere_center) - a
    if abs(disp) >= sphere_radius:
        return 0, None, None

    # Circle radius and center in the plane
    radiusSq = sphere_radius**2 - disp**2
    radius = sqrt(radiusSq)
    center = np.subtract(sphere_center, np.multiply(n, disp))

    assert radius > 0
    assert roundIfClose(np.dot(center,n) - a) == 0


    polyAndArcs = []

    for tileAddr in tileAddrs:            
        td = tiles[tileAddr]
        tile_points = [[x,y,z] for (x,z), y in zip(td["points"], td["heights"])]

        polygon, arcs, _ = splitIntoPolygonAndArcs(tile_points, center, radiusSq)

        polyAndArcs.append((polygon, arcs))

    # Return the radius and center (for arcs), and the list of polygon and arcs
    return radius, center, polyAndArcs

def colourSphereIntesectionWithTiles(spheres, tilePlanes, tiles, plt, axs, fill=True, HATCH_HACK_FACTOR=13, base_colour='g', base_alpha=0.1, inclTileTest=None, lw=0.5):
    # NOTE that the ellipse code may be a bit off, particularly the angle.
    # In frigate it's nearly all completely flat

    # (1) get circle in each plane
    # (2) 'intersect' to give the circular boundary
    # (3) 'tilt' into ellipse arcs and lines to view from above
    # (4) draw - hatching hack works beautifully

    for sphere_center,sphere_radius in spheres:

        for plane, tileAddrs in tilePlanes.items():
            n, _ = plane
            if inclTileTest is not None:
                tileAddrs = [ta for ta in tileAddrs if inclTileTest(ta, tiles)]

            # Ignore any vertical planes
            if n[1] == 0:
                continue

            # Call main func
            radius, center, polyAndArcs = getSphereIntersection(plane, tileAddrs, sphere_center, sphere_radius, tiles)

            if radius <= 0:
                continue

            cx, _, cz = center
            
            # Determine values needed for any arcs
            # First off, the angle of the ellipse, which we can get from the normal
            nx, cosA, nz = n
            ellipse_angle = 180 * atan2(nx, nz) / pi   # 0,0 -> 0.
            cosA = abs(cosA)    # some tiles do point downward

            # Then the extent of the squashing
            width = 2*radius
            height = width*cosA

            for poly, arcs in polyAndArcs:
                # Note the poly may just be 2 points
                if fill and len(poly) >= 3:
                    xs = [-x for x,y,z in poly]
                    zs = [z for x,y,z in poly]
                    xs.append(xs[0])
                    zs.append(zs[0])
                    plt.fill(xs, zs, alpha=base_alpha, fc=base_colour)

                # arcs :) 
                for arc in arcs:
                    pnts = [poly[i] for i in arc]
                    vectors = [np.subtract(pnt, center) for pnt in pnts]
                    headings = [((180 * atan2(x,z) / pi) + 360 + 90 - ellipse_angle) % 360 for x,y,z in vectors]

                    # Officially .Arc doesn't support filling but we can hack our way to the same result
                    #   with high enough density hatching. This should be only dependent on resolution,
                    #   so the fixed value 13 should always work but it can be tuned.
                    # This does create a bit more work but it saves a lot of painful code.
                    e = patches.Arc((-cx,cz), width, height, alpha=base_alpha, ec=base_colour, linewidth=lw,
                        angle=ellipse_angle, theta1=headings[0], theta2=headings[1], hatch=('-'*HATCH_HACK_FACTOR if fill else None))
                    
                    
                    axs.add_patch(e)


def getIntersectionPolyPoints(tile, door_preset, expansion):
    pos_x, _, pos_z = door_preset["position"]

    # Effectively convert the points into door-space
    pnt_comps = []
    
    for pnt in tile["points"]:
        v_x = pnt[0] - pos_x
        v_z = pnt[1] - pos_z

        comps = []
        pnt_comps.append(comps)

        for axis in ["x","z"]:
            n = door_preset["normal_" + axis]
            comp = v_x*n[0] + v_z*n[2]
            comps.append(comp)
        
    # Determine intersection polygon's points (not necessarily ordered)
    # We really should just be using a generic library for this..
    intersect_pnts = []

    for i in range(len(tile["points"])):
        j = i-1

        r = [0,1]
        for axis in range(2):
            a = pnt_comps[i][axis]
            b = pnt_comps[j][axis]

            l,h = door_preset["xz"[axis] + "_limits"]
            assert l < h
            l -= expansion
            h += expansion

            # It's just simplest to order a and b..
            swap = b < a
            if swap:
                a,b = b,a
            
            length = b-a
            if length != 0:
                # Normalise everyone a -> 0, b -> 1
                l = (l-a) / length
                h = (h-a) / length

                # Update the range
                r[0] = max(r[0], 1-h if swap else l)
                r[1] = min(r[1], 1-l if swap else h)

            elif a < l or a > h:
                # Degenerate case, perpendicular to axis
                # So just test if one of the points is outside, and if so kill the range
                r = [1,0]
                break

        # If some part inside then add the two extreme points
        if r[0] <= r[1]:
            for k in r:
                assert 0 <= k <= 1
                a = tile["points"][i]
                b = tile["points"][j]
                x,z = [a[i] * (1-k) + b[i]*k for i in range(2)]
                # Now is also the time to compute the height
                h = tile["heights"][i] * (1-k) + tile["heights"][j] * k
                intersect_pnts.append([x,h,z])

    return intersect_pnts


def checkDoorCuboidReachableAnywhere(door_tile_addr, door_preset, door_rooms, expansion, currentTiles, tiles, door_preset_no):
    # Check that the door's room list doesn't restrict door reachability through the expanded preset test
    # TODO We should also be checking that height considerations aren't restricting us
    #   .. but we need to resolve some difficult with this as discussed below
    #   so currently we are IGNORING height
    
    # We achieve this by:
    #   - Finding the tiles in the neighbourhood of the door which are within the 2D XZ projection of
    #     the expanded preset (cuboid) test for reachability
    #   - Checking that all these rooms are in the door's (list of) rooms (our parameter may be a set)
    #   - (For height) Testing the highest / lowest points of their intersection with the rectangle, considering
    #     Bond's extra height at fullspeed

    # Height troubles:
    #   - on B2 it thinks the vertical doors are too low for us to get. The map also shows them as low,
    #     but in fact we can still reach them
    #   - and also on B2, the critical door which you can't in fact grab from far away..
    #     this code thinks we should be able to!
    # So something is afoot..


    # Taken from Egypt code (so it's good). -12.6 is the reduction by fullspeed.
    BOND_HEIGHT = 167.3 - 12.6
    
    t_l = t_h = tiles[door_tile_addr]["heights"][0] + BOND_HEIGHT
    seen_rooms = set()

    tile_stack = [door_tile_addr]
    seen_tiles = set()

    while tile_stack:
        tile_addr = tile_stack.pop()
        if tile_addr not in currentTiles:   # includes != 0 surely
            continue
        if tile_addr in seen_tiles:
            continue
        seen_tiles.add(tile_addr)

        tile = tiles[tile_addr]

        # Get the intersection points.
        intersect_pnts = getIntersectionPolyPoints(tile, door_preset, expansion)
        if not intersect_pnts:
            continue

        # Add neighbours to the stack, regardless of height
        tile_stack.extend(tile["links"])

        seen_rooms.add(tile["room"])

        # Extreme heights must occur at the points of these polygons
        heights = [pnt[1] + BOND_HEIGHT for pnt in intersect_pnts]
        t_l = min(heights + [t_l])
        t_h = max(heights + [t_h])
    
    l_l, l_h = door_preset["y_limits"]
    assert l_l < l_h
    l_l -= expansion
    l_h += expansion
    cuboid_trigger_good = l_l <= t_l and t_h <= l_h

    ## if not cuboid_trigger_good:
    ##     # We're having fun with our preset numbers being off... or not??
    ##     print(f"[!] Height is relevant in reachability for door at preset {door_preset_no-1:04X}")
    ##     if t_l < l_l:
    ##         print(f"      {(l_l-t_l)/100:.2f}m too low")
    ##     if t_h > l_h:
    ##         print(f"      {(t_h-l_h)/100:.2f}m too high")

    all_tiles_in_door_rooms = seen_rooms.issubset(door_rooms)
    if not all_tiles_in_door_rooms:
        # This door preset number is definitely right..
        print(f"[!] Door at preset {door_preset_no:04X} 's room list prevents reachability from: " +
        ", ".join(f"0x{room:02x}" for room in seen_rooms.difference(door_rooms)))

    return all_tiles_in_door_rooms


def drawDoorReachability(plt, axs, objects, presets, currentTiles, excludePresets=None, tiles=None):
    for addr, obj in objects.items():
        if obj["type"] != "door":
            continue
        if obj["tile"] not in currentTiles:
            continue
        if obj.get("extreme_clearance"):        # Frigate's crazy doors-in-the-air
            continue
        if excludePresets is not None:
            if obj["preset"] in excludePresets:     # Umm..
                continue
            if obj["preset"] + 10000 in excludePresets:
                continue

        preset_no = 10000 + obj["preset"]
        preset = presets[preset_no]
        if abs(preset["normal_y"][1]) <= 0.99:
            # we assume our doors are upright OR INVERTED, as it gives us a simpler projection
            print(f"[!] Door at {preset_no:04X} is not upright nor inverted! Unable to process reachability..")
            continue

        pos_x, _, pos_z = preset["position"]

        expansion = 150     # 1.5m expansion, hardcoded in the ASM

        js = [1,1,0,0]
        ks = [1,0,0,1]
        change = [-expansion, expansion]  
        xs = []
        zs = []
        pnts = []
        for j,k in zip(js, ks):
            doorX = (preset["x_limits"][j] + change[j])
            doorZ = (preset["z_limits"][k] + change[k])
            pnts.append((
                pos_x + preset["normal_x"][0]*doorX + preset["normal_z"][0]*doorZ, 
                pos_z + preset["normal_x"][2]*doorX + preset["normal_z"][2]*doorZ
            ))


        ## cuboid_trigger_good = checkDoorCuboidReachableAnywhere(obj["tile"], preset, set(obj["room_list"]), expansion, currentTiles, tiles, preset_no)

        ply_colour = arc_colour = (0,0,0,0.25)
        isBadDoor = obj.get("is_bad_door", False)
        if isBadDoor:
            ply_colour = (0.75,0,0,0.25)

        # Circle is centered on the object, not the preset (can differ slightly even when shut)
        # Radius is 2m
        # Prefer the raw object position if we can get it
        # "position" is taken from the position data pointer, but this outputs different (and wrong) data for the depot gates
        # Instead we should be using the raw object position
        # We still fall back on the normal position - TODO go dump all the data again
        object_position = obj.get("object_position", obj["position"])
        cx, cz = object_position
        RADIUS = 200
        innerPly, arcs, origIndexInInner = splitIntoPolygonAndArcs(pnts, object_position, RADIUS**2)

        # the corners of the square are at least 2.25m away, sides 1.5m plus half door thickness
        #   so we will have arcs unless the door is very thick.. which we're assuming it's not
        if len(arcs) == 0:
            print(f"[!] Error drawing reachability for door at {preset_no:04X}")
            continue

        for leave, enter in arcs:
            origIndices = [i for i,newI in enumerate(origIndexInInner)
                if (leave < newI and newI < enter) or               # standard interval
                (enter < leave) and (newI > leave or newI < enter)  # if they wrap around, it's just got to be above the start or before the end
            ]
            # These indices need cycling to have the first 1st
            split = bisect_left([origIndexInInner[i] for i in origIndices], leave)
            origIndices = origIndices[split:] + origIndices[:split]

            segPnts = [innerPly[leave]] + [pnts[i-1] for i in origIndices] + [innerPly[enter]]  # -1 is a hack, may not be right generally..

            xs, zs = zip(*segPnts)
            xs = [-x for x in xs]
            plt.plot(xs, zs, linewidth=0.5, color=ply_colour)


        if isBadDoor:
            print(f"[ ] Drawing bad door at preset {preset_no:04X}")
            # Draw entire circle because it becomes relevant if the preset isn't in fact containing most of it
            axs.add_artist(plt.Circle((-cx, cz), 200, color=arc_colour, linewidth=0.5, fill=False))
        else: 
            leaves, enters = zip(*arcs)
            gaps = zip(enters, leaves[1:] + (leaves[0],))
            for gap in gaps:
                pnts = [innerPly[i] for i in gap]
                vectors = [np.subtract(pnt, object_position) for pnt in pnts]
                headings = [((180 * atan2(x,z) / pi) + 360 + 90) % 360 for x,z in vectors]

                e = patches.Arc((-cx,cz), 2*RADIUS, 2*RADIUS, ec=arc_colour, linewidth=0.5,
                    angle=0, theta1=headings[0], theta2=headings[1])
                axs.add_patch(e)