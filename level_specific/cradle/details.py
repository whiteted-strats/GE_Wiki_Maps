
dividingTiles = [
    # Stair down off the top level
    0x021B09,

    # End of ramps down
    0x00A901,
    0x00AE01,

    # Stairs to the final room
    0x021202,
    
    # Ladder down (this excludes the bottom plinth but make our life easier)
    0x020500,
]

startTileName = 0x006D09

# Doors which we don't want reachability drawn for
excludeDoorReachPresets = [
]