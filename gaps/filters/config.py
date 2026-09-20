"""Settings for the generic filters. Distances are in metres.

Anything which depends on Bond's size is not set here: it is worked out from his radius, which is
declared once, in gaps/mesh.py.
"""

# The anvil of "anvil and hammer": how long a straight wall must be. 6 m is ten of Bond's widths.
# Half of this must lie either side of the hammer.
ANVIL_LENGTH_M = 6.0

# Objects whose bottom is at least this far above the floor they are attached to are pointed out for
# review, with a close-up each in output/00_debug/overhead_objects/. Nothing is removed because of
# this: removing an object takes an entry in REMOVE_OBJECTS in the level's file. On the 20 levels
# nothing sits between 1.83 m and 2.68 m, so any value in that range picks out the same objects.
OVERHEAD_REVIEW_CLEARANCE_M = 2.0
