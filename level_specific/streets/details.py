
# Include them the first time we reach them, but not again
dividingTiles = [
    # Chop the level up because the image has a fit
    # Start -> Mid
    0x526D12,
    0x527211,
    0x526012,
    0x527412,
    0x527012,

    # Mid -> End (long straight)
    0x544412,
    0x543811,
    0x543e12,
    0x544212,
    0x544512,
]

startTileName = 0x1F7100

# Doors which we don't want reachability drawn for
excludeDoorReachPresets = [
]