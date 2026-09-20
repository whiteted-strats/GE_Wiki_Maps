# GE Wiki Maps

Top-down maps of GoldenEye 007 (N64) levels, generated from data dumped out of the running game.
They are made for the speedrunning wiki at https://wiki.the-elite.net, and for investigating strats.

As well as the floor itself (tiles), the maps draw guards, objects, collectibles, doors and the areas
you can open them from, stairs, and things specific to a level such as how far a noise carries,
guard paths, lines of sight and trigger zones.

*This README was written during a clean-up of the repository, from reading the code rather than from
full knowledge of it. Treat it as a rough guide.*

## How it fits together

1. `dump_map_data.lua` runs in the BizHawk emulator with the level loaded. It depends on the `Data\GE` and
   `Utilities\GE` Lua modules from a GoldenEye BizHawk scripts collection, which are not part of this
   repository. It writes the level's tiles, objects, guards, pads, sets and presets to `data/<level>.py`
   as plain Python dictionaries.
2. `lib/` holds the shared geometry and drawing code.
3. `level_specific/<level>/` holds small per-level settings: where to split the level into separate maps,
   names for those groups, and doors to skip.
4. `maps/<level>.py` draws the maps for a level, including any investigation specific to it,
   and saves them as PNGs under `output/<level>/`.

## Running

    pip install -r requirements.txt
    python -m maps.facility

Run from the repository root, as a module so that `lib`, `data` and `level_specific` can be imported.

## Notes

- The data was dumped from the NTSC-U version. Guards and objects are wherever they were at the moment
  of the dump, and some objects only exist on certain difficulties.
- Some levels are plain maps with nothing level specific drawn: silo, train, jungle, cradle and the
  simple bunker 1.
- `notes/bad_doors/` has notes on doors which can't be opened from everywhere you'd expect, and
  `notes/notable_doors/` has example images. See `data/relevant_bad_doors.py` for the ones drawn in red.
- The `guard_can_open` field is missing from the data until the levels are dumped again,
  and `height_range` is unreliable for some doors. See the comments in `dump_map_data.lua`.
