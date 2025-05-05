import numpy as np
from functools import reduce

def prepTiles(tiles):
    # Create shapes only
    # Shapely may be less relevant for us now?
    for _, td in tiles.items():
        xs, zs = zip(*td["points"])
        td["bounding_box"] = (min(xs), max(xs), min(zs), max(zs))

        degenerate = (
            (len(set(xs)) <= 1 or len(set(zs)) <= 1) or
            (len(set(td["points"])) < 3)
        )

        td["degenerate"] = degenerate   # area 0 essentially


def getGroupBounds(tiles, groups):
    groupBounds = []

    for tileGrp in groups:
        bnds = [f(l) for f,l in zip([min, max, min, max], zip(*[ (tiles[tileAddr]["bounding_box"]) for tileAddr in tileGrp]))]
        groupBounds.append(bnds)
    
    return groupBounds


def prepPlot(plt, currGroupBounds):
    # Fit all tiles and a 1 metre in-game border

    # 1m GE world = 100 units = 1 cm (= 1/2.54 inches)
    PAD_UNITS = 100
    min_x, max_x, min_z, max_z = [(v+c) for v,c in zip(currGroupBounds, [-PAD_UNITS, PAD_UNITS, -PAD_UNITS, PAD_UNITS])]

    # Init global plot
    fig, axs = plt.subplots(figsize = ((max_x - min_x) / 254, (max_z - min_z) / 254))
    plt.axis('off')
    axs.set_aspect('equal')

    # Finally we have defeated pyplot
    axs.set_xlim(-max_x, -min_x)  # flipped remember
    axs.set_ylim(min_z, max_z)

    return fig,axs

def drawTile(td, colour, axs, alpha):
    xs, zs = zip(*td["points"])
    xs += (xs[0],)
    zs += (zs[0],)
    xs = [-x for x in xs]   # flip
    axs.fill(xs, zs, alpha=alpha, ec=colour, fc=colour)


def drawTiles(currentTiles, tiles, colour, axs, alpha=1):
    for tileAddr in currentTiles:
        drawTile(tiles[tileAddr], colour, axs, alpha) # light grey


def drawTileHardEdges(currentTiles, tiles, colour, axs, linewidth=1):
    for tileAddr in currentTiles:
        td = tiles[tileAddr]
        xs, zs = zip(*td["points"])
        xs += (xs[0],)
        zs += (zs[0],)
        xs = [-x for x in xs]
        for i,l in enumerate(td["links"]):
            if l != 0:
                continue

            axs.plot(xs[i:i+2], zs[i:i+2], color=colour, linewidth=linewidth)


# -------------- Tile planes ---------------

def roundIfClose(r):
    n = round(r)
    if abs(r-n) < 0.0001:
        return n
    return r

def getUnscaledEnclosingPlane(td, level_scale):
    ps = [[roundIfClose(x * level_scale) for x in p] for p in td["points"]]
    hs = [roundIfClose(h * level_scale) for h in td["heights"]]
    ps = [[x,y,z] for y, (x,z) in zip(hs, ps)]
    assert len(ps) >= 3

    # Some straight lines are split in 2, so their cross product is 0
    # Walk around the tile to find one which isn't
    succ = False
    for i in range(len(ps)):
        v = np.subtract(ps[i-1], ps[i])
        w = np.subtract(ps[(i+1) % len(ps)], ps[i])
        n = tuple(np.cross(w,v))   # normal
        if n != (0,0,0):
            succ = True
            break

    assert succ

    p_as = [np.dot(n, p) for p in ps]
    if len(set(p_as)) != 1:
        print("[!] tile with name {:x} is not flat. Selecting most popular a value with given n".format(td["name"]))
        a = max([(p_as.count(x),x) for x in set(p_as)])[1]
    else:
        a = p_as[0]

    # ! Need a standard form, remove gcd
    assert all(x == int(x) for x in n) and a == int(a)
    gcd = reduce(np.gcd, n + (a,))
    a //= gcd
    n = tuple(x // gcd for x in n)

    return n,a


# Scale the tile planes back into the level, and make the normals unit vectors
def rescalePlane(n, a, level_scale):
    # a = v.n for some v in the tile, so scale as we imagine scaling v
    a = a / level_scale
    # then n and a we need to scale down as we make n a unit vector
    n_mag = np.linalg.norm(n)
    assert n_mag >= 1    # not small
    a = a / n_mag
    n = tuple(x / n_mag for x in n)
    return (n,a)

def getTilePlanes(currentTiles, tiles, level_scale):
    # Get all planes, even those which are vertical
    tilePlanes = dict()
        
    for tileAddr in currentTiles:
        td = tiles[tileAddr]
        plane = getUnscaledEnclosingPlane(td, level_scale)
        n,a = plane

        # Some (bad) tiles do point slightly downward
        #assert n[1] >= 0, "{:x} : {}".format(tileAddr, n)

        if plane in tilePlanes:
            tilePlanes[plane].append(tileAddr)
        else:
            tilePlanes[plane] = [tileAddr]

    # Rescale now that we've matched them
    tilePlanes = dict([(rescalePlane(n,a,level_scale), tileAddrs) for (n,a), tileAddrs in tilePlanes.items()])

    return tilePlanes


# -------------- Tile planes ---------------

def getCommonVoidCornerWithInwardVector(tile_names, tiles):
    # On each tile, identify any points which are on a void edge, i.e. an unlinked edge.
    # We then look for a unique common such point between all (both of) the provided tiles.
    # NOTE that this is can miss void points - the true test would be to attempt to walk around
    #   the point in a complete loop. But this is simpler and sufficient for this function's purpose:
    #   Be sure to pass tiles which *witness* that the point you are trying to identify is void.

    assert len(tile_names) == 2     # 3 or more doesn't actually make any sense

    # Slightly inefficiently search for these names
    named_tiles = []
    tile_names = set(tile_names)
    for tile_addr, tile in tiles.items():
        if tile["name"] in tile_names:
            named_tiles.append(tile)
    assert len(named_tiles) == len(tile_names), "Bad tile name - at least one wasn't found"

    # Determine which points are on a void edge of each tile
    # Note them against their indices
    void_point_maps = [
        {
            pnt : i for i,pnt in enumerate(tile["points"])
            if tile["links"][i] == 0 or tile["links"][i-1] == 0
        }
        for tile in named_tiles
    ]

    # Get the unique common void point, and its indices on the two tiles
    common_void_pnt = set.intersection(*[set(d.keys()) for d in void_point_maps])
    assert len(common_void_pnt) == 1
    common_void_pnt = next(iter(common_void_pnt))
    pnt_indices = [m[common_void_pnt] for m in void_point_maps]

    # Debug
    ##print("Common point: ", common_void_pnt)
    ##print("Indices: ", pnt_indices)
    ##for tile in named_tiles:
    ##    print("Tile:")
    ##    print("  points: ", tile["points"])
    ##    print("  links: ", tile["links"])

    # Then we need to work out which way is "inwards"
    # Essentially we are working out how to orientate the two void edges so that they are both going
    #   clockwise around the void, with our common point in the middle.
    # We also make some checks. These boil down to the two tiles sharing a common edge..
    assert all((tile["links"][i] == 0) ^ (tile["links"][i-1] == 0) for (i,tile) in zip(pnt_indices, named_tiles))
    t_a, t_b = named_tiles
    i_a, i_b = pnt_indices
    assert (t_a["links"][i_a] == 0) ^ (t_b["links"][i_b] == 0)
    cws = t_a["links"][i_a-1] == 0

    if (cws):
        void_pnts = [t_a["points"][i_a-1], common_void_pnt, t_b["points"][i_b+1]]
    else:
        void_pnts = [t_b["points"][i_b-1], common_void_pnt, t_a["points"][i_a+1]]

    # Then we can get the normals (inwards) from these void edges
    void_vs = [np.subtract(p,q) for p,q in zip(void_pnts, void_pnts[1:])]
    norms = [np.linalg.norm(v) for v in void_vs]
    assert 0 not in norms
    void_vs = [np.multiply(v, 1/n) for v,n in zip(void_vs, norms)]
    void_vs = [(-z, x) for x,z in void_vs]

    # We just add these to give us an inward edge at the corner
    # It is a little bit sus geometrically but it should do the job?
    # If we are returning a single edge then surely there's not a better choice
    inward_v = np.add(*void_vs)

    return common_void_pnt, inward_v

def drawEdgeInsideCornerToTarget(tile_names, target_pnt, tiles, plt, linewidth=0.5, color='k'):
    if len(target_pnt) == 3:
        target_pnt = target_pnt[::2]    # ditch y

    common_void_pnt, inward_v = getCommonVoidCornerWithInwardVector(tile_names, tiles)

    # Construct a vector out from this void point at a right angle to the vector to the target
    # It is length 30 i.e. Bond's radius
    v = tuple(np.subtract(target_pnt, common_void_pnt))
    v = np.multiply([-v[1], v[0]], 30 / np.linalg.norm(v))

    # Flip this if necessary so that it points inwards
    if np.dot(v, inward_v) < 0:
        v = np.multiply(v, -1)

    # Add to the corner to give our bond point
    # Assuming that the void point is 'convex' rather than concave (which would make no sense)
    #   and that we haven't crossed some other edge into void, then this is in-bounds,
    # and our line away is avoiding the corner (and both the edges)
    bond_pos = np.add(common_void_pnt, v)

    # Draw the line
    xs, zs = zip(bond_pos, target_pnt)
    plt.plot([-x for x in xs], zs, linewidth=linewidth, color=color)