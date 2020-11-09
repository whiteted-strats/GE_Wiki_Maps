# Field of view, showing the areas covered by the 0x3C command

# https://github.com/MrMinimal64/extremitypathfinder
# pip install extremitypathfinder
# the visibility in this should be sufficient since our LOS is a straight line, so a shortest path
from extremitypathfinder import PolygonEnvironment
from extremitypathfinder.helper_classes import Vertex
from extremitypathfinder.helper_fcts import find_visible
from math import atan2

def walkClippingBoundary(addr, i, envTileAddrs, tiles, remExtEdges):
    """
    (addr -> tiles[addr]["links"][i]) must be crossing the boundary (out)
    Then we return the complete boundary and remove it from remExtEdges
    """
    boundary = []

    while True:
        # Move acws.
        i = (i + 1) % len(tiles[addr]["points"])
        l = tiles[addr]["links"][i-1]

        ##input(hex(tiles.get(l, {}).get("name", 0)))

        # If boundary, add it
        if l == 0 or l not in envTileAddrs:
            if len(boundary) > 0 and boundary[0] == (addr, i-1):
                break
            ##print("boundary", hex(tiles[addr]["name"]), "->", hex(tiles.get(l, {}).get("name", 0)))
            pr = (addr, i-1)
            assert pr in remExtEdges
            remExtEdges.remove(pr)
            boundary.append(pr)

        # Else, walk across it.
        else:
            i = tiles[l]["links"].index(addr) + 1
            addr = l
    
    # For each edge take 1 end, forms the whole polygon
    # .. but we need to remove duplicates (assumes len(set(-)) > 1)
    addr, j = boundary[-1]
    prev = tiles[addr]["points"][j]
    pnts = []
    for addr, j in boundary:
        curr = tiles[addr]["points"][j]
        if curr != prev:
            pnts.append(curr)
        prev = curr
    
    return pnts

def drawFOV(guardId, rooms, tiles, guards, plt, ignoreTileAddrs = None):
    """
    [!] The rooms you give must be simply linked i.e. project flat. i.e. only 1 floor
    Otherwise this will likely enter an infinite loop looking for the boundary
    """
    
    # 0. Ignore tiles used to ensure our boundary polygon doesn't overlap at all
    ignoreTileAddrs = set() if ignoreTileAddrs is None else set(ignoreTileAddrs)

    # 1. get tiles in our rooms (or use all tiles)
    envTileAddrs = set(
        tiles.keys() if rooms is None
        else [a for a,t in tiles.items() if t["room"] in rooms]
    )
    envTileAddrs.difference_update(ignoreTileAddrs)
    assert len(envTileAddrs) > 0

    externalEdges = set()

    # 2. Find the outside shape:
    # Get a point with max x (and z). Then from those tiles with this point,
    #   get one with a maximal 2nd point
    max_p = max(p for a in envTileAddrs for p in tiles[a]["points"])
    maxTiles = [a for a in envTileAddrs if max_p in tiles[a]["points"]]
    q, addr = max((p, a) for a in maxTiles for p in tiles[a]["points"] if p != max_p)
    pnts = tiles[addr]["points"]
    i = pnts.index(q)
    if pnts[i-1] != max_p:
        i = (i + 1) % len(pnts)
        assert pnts[i] == max_p


    # 3a/4a. Get all external edges.
    remExtEdges = set([
        (addr, ((i+1) % len(tiles[addr]["links"])) - 1)
        for addr in envTileAddrs
        for i,l in enumerate(tiles[addr]["links"])
        if l == 0 or l not in envTileAddrs
    ])

    # Now [i-1], [i] are these two points, and must be an external edge.
    # (note this is only external to the group we're looking at, but that's okay)
    # And this edge is ["links"][i-1]. And they go ACWS
    assert (addr, i-1) in remExtEdges
    
    outerBoundary = walkClippingBoundary(addr, i-1, envTileAddrs, tiles, remExtEdges)

    # 3. Find all clipping holes. Untested.
    holes = []
    while len(remExtEdges) > 0:
        addr, i = next(iter(remExtEdges))
        hole = walkClippingBoundary(addr, i, envTileAddrs, tiles, remExtEdges)
        holes.append(hole)    # CWS

    # 4. Get objs


    # 5. Use library, digging a little into the internals to add the current path
    environment = PolygonEnvironment()
    environment.store(outerBoundary[::-1], holes, validate=True)  # probably don't validate O:) - objects may leak over
    environment.prepare()
    guardPos = [g["position"] for g in guards.values() if g["id"] == guardId][0]

    
    # Testing
    assert environment.within_map(guardPos)
    guardVertex = Vertex(guardPos)
    environment.translate(new_origin=guardVertex)
    candidates = set(filter(lambda n: n.get_angle_representation() is not None, environment.graph.get_all_nodes()))
    visibles = [
        tuple(pnt[0].coordinates)
        for pnt in find_visible(candidates, edges_to_check=set(environment.all_edges))
    ]


    # Debug
    ##targetPos = [g["position"] for g in guards.values() if g["id"] == 0x11][0]
    ##path, _ = environment.find_shortest_path(guardPos, targetPos)

    # 6. Arrange visibles in a (A?)CWS order, draw.
    visibles.sort(key = lambda x : atan2(x[0],x[1]))
    xs, zs = zip(*visibles)
    plt.plot([-x for x in xs], zs, linewidth=0.5, color='r')