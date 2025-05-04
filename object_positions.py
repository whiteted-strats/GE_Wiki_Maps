# Lists doors whose raw object position differs from their position data position - this is how the depot gates issue was discovered
from data import *

for level in [
    archives,
    aztec,
    bunker_1,
    bunker_2,
    caverns,
    control,
    cradle,
    dam,
    depot,
    egyptian,
    facility,
    frigate,
    jungle,
    runway,
    silo,
    statue,
    streets,
    surface_1,
    surface_2,
    train,
]:
    objects = level.objects
    for addr, obj in objects.items():
        obj_pos = obj.get("object_position")
        if obj_pos == None:
            continue

        if obj["type"] != "door":
            continue

        pdp_pos = obj.get("position")
        if pdp_pos != obj_pos:
            print(f"{level.__name__[5:]}: 0x{addr:x}")
            print("   ", pdp_pos)
            print("   ", obj_pos)