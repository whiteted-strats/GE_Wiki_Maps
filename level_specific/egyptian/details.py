
# Include them the first time we reach them, but not again
dividingTiles = [
    0x165A01,   # Near ramp down
    0x1E3A01,   # Far ramp down
]

startTileName = 0x1DA300

# Doors which we don't want reachability drawn for
excludeDoorReachPresets = [
]

excludeDoorReachPresets.extend(range(0x273B, 0x2749))