# gaps: every gap narrower than Bond, and the warps through them

Bond moves by teleporting each frame. He needs **line of sight** to where he is going, and he needs
to **fit** when he gets there, but on the way he has no width. He is 60 wide (radius 30), so any gap
narrower than 60 cm is one he can't walk through but might cross in a single step: a warp.

    python -m gaps train frigate        # or: python -m gaps all
    python -m gaps all --reuse-surveys  # only redo the filtering and the reports: seconds, not minutes
    python -m gaps.filters              # lists the filters and the predicates
    python -m unittest discover -s gaps/tests -t .
    ruff check gaps && ruff format gaps  # pip install -r requirements-dev.txt

The words used here are defined in [terminology.md](terminology.md).

Results go to `output/00_gaps/<level>/`: `gaps.csv` (one row per gap, best first), `overview_*.svg`
(each part of the level with the gaps numbered), `gap_NNN.svg` (a close-up of each, as vector
graphics so it can be zoomed into without limit), `decisions.csv`
(every pair of walls that was looked at, and why it was kept or dismissed), `touching.csv`, and
`filtered.csv` (the gaps which a filter removed, each with the filter and its reason).

## How it works, and what is trusted

Read the modules in this order. Each starts with an explanation.

1. `exact.py` - geometry on integers and fractions. No tolerances anywhere, and no shapely.
2. `mesh.py` - loads a level. Tile corners are exact integers once multiplied by the level's scale,
   and object outlines are exact fractions. Walls are tile edges with nothing linked across them,
   plus the sides of objects.
3. `sheet.py` - the two questions the game asks: is there line of sight, and does Bond fit. Both
   work outwards from a tile **through links**. Floors which overlap from above, and places like
   Aztec's pipes behind the glass, never interact because they are not linked nearby.
4. `pinch.py` - measures every pair of walls closer than 60. Each pair is kept as a *pinch* or
   dismissed by one of four exact rules, and the reason is written to `decisions.csv`. Every warp
   must pass through a pinch, so this stage decides what can possibly be found. It is exact.
5. `witness.py` - looks for an actual warp through each pinch: two positions where Bond fits which
   can see each other through it. A fast search in floats proposes positions, which are then
   **certified exactly** with `sheet.py`. A reported warp is therefore real geometry. The search can
   miss, so "no warp found" is never proof, and such gaps are still listed and drawn.
6. `detour.py` - an approximate note of how far Bond would have to walk to get from one end of the
   warp to the other. "none found" means the warp crosses something he can't otherwise get past.
7. `survey.py`, `report.py` - groups pinches into gaps, ranks them, writes the tables and maps.

`fast.py` holds the numpy helpers used by the two searches. Nothing in it is trusted.

## Filters

`filters/` marks gaps which are of no interest, without deleting anything. Generic filters are code
(`filters/generic.py`) and may only remove gaps where no warp was found. Each level can also have a
plain Python file, `filters/levels/<level>.py`, listing groups of objects to ignore along with what
is expected of them, so that a wrong ID stops the run. Settings are in `filters/config.py`, in
metres.

A level file can also list objects to **remove**: ones which are not really there, such as Frigate's
doors which hang in the air above the room they are attached to. Those are left out of the level
before it is surveyed, which changes what is found, so it is never done automatically. Removing one takes an entry in the
level's file, and everything left out of a level is listed in `objects_left_out.csv` with the reason.

To check this work, `python -m gaps all --reuse-surveys --review` draws close-ups into
`output/00_debug/`: `filter_review/` has every gap a filter removed, named by level and filter, and
`overhead_objects/` has every object well above its floor, named by level, type and height, with a
table of them per level. That is how the floating doors were found. It is only an aid (`review.py`):
nothing in the survey depends on it.

## Reading the results

- **status** `warp`: works in the level exactly as dumped. `warp if objects removed`: works once the
  objects listed under `objects_in_the_way` are gone. `no warp found`: a pinch, but the search found
  no pair of positions (often Bond doesn't fit anywhere on one side: a pocket).
- **width** of the gap and **step**: the distance Bond has to cover in one frame, which is the real
  measure of how hard the warp is. The step is that of the best warp found, so the true minimum
  could be slightly lower.
- **objects_forming_gap**: every object is treated as optional, as the data doesn't say which are
  destructible. If one of these is destroyed the gap is gone.
- Gaps under 1 cm wide are *hairlines*, nearly all of them closed doors sitting a few thousandths
  of a centimetre from their frames. They are listed last and drawn in grey without a number.
- Doors are as they were when the level was dumped, i.e. closed. Guards are ignored.

## Known limits

- The collision rules are the geometric ones described above, not yet checked against the game's
  own routine in the decompilation.
- A step may not start further than 3 m from the pinch (`SEARCH_RADIUS_CM` in witness.py).
- The walk round is searched within 4 m on a grid of 4 cm, so a passage only a little wider than
  Bond can be missed, giving "none found" when there is a way.
