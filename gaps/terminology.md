# Terminology

The words used in the code, the reports and the filter files. Lengths are in **centimetres** unless
they say otherwise (Bond's radius is 30 cm). The settings of filters are in **metres**.

## The game

**Bond** - a disc of radius 30 cm seen from above, so 60 cm wide. Declared once, as
`BOND_RADIUS_CM` in `mesh.py`. Everything which depends on his size is worked out from that.

**Step** - how far Bond moves in one frame. He doesn't travel: he disappears from one position and
appears at the next, provided there is *line of sight* and he *fits*. The length of the step a warp
needs is the real measure of how hard it is.

**Line of sight** - the straight line from one position to the next touches no wall. Bond has no
width while he moves. (`trace` in `sheet.py`.)

**Fits** - the disc, centred on a position, overlaps no wall. Touching exactly is allowed.
(`fits` in `sheet.py`.)

**Warp** - a step which takes Bond somewhere he could not have walked, because it passes through
a gap narrower than he is.

## The level

**Tile** - a flat polygon of floor, usually a triangle. Its corners are whole numbers in the
game's own units.

**Link** - two tiles which share an edge and are joined across it, so Bond can walk from one to the
other. Links are the only thing which joins the floor together.

**Wall** - anything which stops Bond: an edge of a tile with nothing linked across it (the game's
"void edge"), or a side of an object. In the code a wall is a `BoundarySegment`.

**Corner** - an end of a wall.

**Object** - a crate, door, monitor and so on, with an outline seen from above. The data doesn't say
which can be destroyed, so every object is treated as optional. Doors are as they were when the
level was dumped, which is closed. Pick-ups and guards are left out.

**Storey** - one level of a building, in the everyday sense: Archives has an upstairs and a
downstairs. Storeys overlap seen from above, which is why "near" has to mean near on the *sheet*.

**Floor** - only ever used for the tiles directly beneath something, as in *floor clearance*. It is
not used to mean a storey, and not to mean the whole walkable surface: that is the sheet.

**Walkable area** - the floor seen from above: everywhere that is over a tile. Gaps are made of
walkable area, and objects only ever take away from it.

**Outside the walkable area** - said of an object no part of which, seen from above, is over any
tile at all, on any storey. (It has nothing to do with height: an object hanging in the air
over the floor is *overhead*, not outside.) Such an object can never form a gap, block a line of
sight or stop Bond fitting, so it is left out of the level automatically and listed in
`objects_left_out.csv`. Most are scenery out in the snow on the Surface levels.

**Sheet** - the floor as Bond experiences it: tiles joined by links. Two parts of a level can be in
the same place seen from above and yet have nothing to do with each other, such as the floors of a
building, or Aztec's pipes behind the glass. They are different sheets, or distant parts of one.
So "near" always means *reachable through links without going far*, never just close from above.

Where links lead round to another storey within the distance being looked at, that storey is left
out: a tile isn't taken as near if it lies over or under one which already has been, with a metre
or more between them. Nearer tiles are taken first, measured along the way there, so it is the far
storey which goes. The metre is there because tiles of one floor overlap slightly where a level was
drawn carelessly, and both of those must be kept. Storeys are 2 m apart or more. This is the only
use made of heights. (`Level.linked_tiles_within` in `mesh.py`.)

**Scaled units** - the whole-number units which tiles are stored in. Centimetres multiplied by the
level's scale. All exact arithmetic is done in these; reports convert back to centimetres.

## The survey

**Pinch** - one pair of walls closer together than Bond's width (60 cm), with clear floor between
them. It has a *pinch line*: the shortest line from one wall to the other, whose length is the
*width*. A pinch is the smallest unit the survey deals in. (`pinch.py`.)

**Gap** - one place where the level is too narrow for Bond, which is what a person would point at.
It is usually several pinches, because a wall is made of many short pieces, and outlines of objects
repeat some of their corners. Pinches whose lines come within Bond's radius of each other are
grouped into one gap. Reports are per gap. (`survey.py`.)

**Decision** - the record of one pair of walls closer than 60 cm: kept as a pinch, or dismissed,
and why. All of them are in `decisions.csv`.

**Touching walls** - two unrelated walls at no distance at all: a gap of width zero. Bond can't
pass, but they are listed in `touching.csv`.

**Hairline** - a gap less than 1 cm wide. Nearly all are closed doors which sit a few millionths
of a centimetre from their frames. However narrow, one with a warp through it is a warp: they are
treated like any other gap. A warp through one is drawn in orange rather than red, and their close-ups
have the width written on them. A hairline's width is always given to two significant figures,
written out in full: 0.93, 0.0042, 0.0000066.

**Witness** - an actual warp through a pinch: two positions where Bond fits, with line of sight
between them through it. A witness is proposed by a fast search and then *certified* exactly, so a
reported warp is real. (`witness.py`.)

**Status** of a gap:
- *warp* - a witness exists in the level exactly as dumped. Red on the maps.
- *warp if objects removed* - only once the listed objects are out of the way. Violet.
- *no warp found* - the search found no witness. That is not proof that there is none. Blue.

**Pocket** - the usual reason for *no warp found*: on one side of the gap there is nowhere Bond
fits, so there is nowhere to arrive.

**Objects forming the gap** - the objects whose sides are its walls. Destroy one and the gap is gone.

**Objects in the way** - for *warp if objects removed*: the objects which block the witness.

**Walk round** - how far Bond would have to walk to get from one end of the warp to the other.
*None found* means the warp crosses something he can't otherwise get past, which makes it far more
interesting than a squeeze past a crate. This is approximate. (`detour.py`.)

**Key** - a name for a gap which doesn't change between runs, made from the two walls of its
narrowest pinch, e.g. `142310.0 | 142510.1` (tile name and which edge) or `0x1e990c.2` (object and
which side). Gap *numbers* are friendlier but change whenever the ranking or the filters do.

**Variant** - a gap which is really the same warp as another: the step found for one passes
through a pinch line of the other, as when a slot has two tight spots, or the same squeeze is
measured against two different objects. Gaps joined like this form one warp. The one with the
shortest step is the *main* gap, and is what the tables, maps and names refer to. The rest are its
variants: listed in `variants.csv`, and drawn only with `--variants`. (`variants.py`.)

**Known warp** - a gap which has been given a name, in `known_warps/levels/<level>.py`, together
with what the survey found for it: its status, width, step and objects. It is tied to the two
walls of one of its pinches, not to its number. Every run checks that each is still there, still
unfiltered, still as recorded, and that a warp no longer than the recorded step is still found, which makes them a regression test of the whole tool.
Their close-ups are named after them: `006_pipe-warp.svg`.

## Filters

**Filter** - a rule which marks a gap as being of no interest. Nothing is deleted: the gap gains a
*verdict* (the filter's name and its reason) and moves from `gaps.csv` to `filtered.csv`.

**Generic filter** - code, applying to every level, which claims that no warp is possible through a
certain shape of gap. It may only remove gaps where *no warp found*. (`filters/generic.py`.)

**Contradiction** - a generic filter matching a gap which does have a witness. One of the two is
wrong, so the gap is kept and the clash is reported. There should never be any.

**Anvil and hammer** - the first generic filter. The *anvil* is a long wall in one straight line,
made of one piece or several. The *hammer* is a corner, or an edge parallel to the anvil, less than
Bond's radius from it. No step can pass between them, because Bond's centre stays at least his
radius from the anvil throughout. The only other way past is for an end of the step to be beyond an end of the anvil, angling in
round it. For each end, such a step is ruled out or shown to be impractically long in one of three
ways: the anvil runs on for half its required length; or it ends at a *protrusion*; or, failing
those, the *slow-rise bound* is long enough. A doorway in the wall ends the anvil.

**Hammer point** - a corner closer to the anvil than Bond's radius, over the anvil and on its
walkable side. The hammer of a pinch is always at least one hammer point.

**Hammer head** - an edge both of whose ends are hammer points. A step can't cross an edge, so one
which passes under a hammer head passes under both of its points, and the slow-rise bound is
measured to the further of them. Heads are never joined into anything longer than one edge. If the
pinch's hammer is a side of an object whose outline is convex, every side of that object which is
a hammer head counts, since a straight line which misses a convex shape has all of it to one side:
a step under the corner of a crate passes under the whole crate.

**Protrusion** - a wall at the end of an anvil which turns towards the walkable side and rises at
least as far from the anvil's line as the hammer is. A step from beyond it passes over its tip,
so higher than the hammer, and then has to drop under the hammer. It therefore keeps dropping and
can't end over the anvil, where Bond must be 30 cm up. It can still end beyond the *other* end of
the anvil, so a protrusion only counts if the other end has one too, or is long. Nothing is
assumed about what lies beyond a protrusion, as the wall may bend back again: an end of an anvil
is never called "closed". Depot's gap `04557A.1 | 0x1eed40.2` is the example to remember, a warp
over a protrusion, under a door corner and out past the other end of an anvil under a metre long.

**Slow-rise bound** - a lower limit on the length of a step which comes in round an end of the
anvil: `min(anvil length, distance x 30 / d)`, where `d` is the hammer's distance from the anvil
and `distance` is measured from that end of the anvil to the furthest hammer point which the
step must pass: the far end of the hammer head, if there is one. The step can't
cross the anvil and must pass under the hammer, so it rises no faster than `d` over that distance,
and Bond doesn't fit until it has risen 30 cm. Or it ends beyond the other end of the anvil, having
covered the anvil's whole length. If the bound reaches `ANVIL_LENGTH_M` the step is impractical.

**Pocket** (in the narrow pocket filter) - everywhere that can be reached from one side of a pinch
line without crossing the pinch line itself, following every link and going round corners.

**Narrow pocket** - the second generic filter. If a pocket extends less than Bond's width,
measured in the direction of the pinch line, he fits nowhere in it, so there is no warp through
that pinch. Walking from his centre parallel to the pinch line, you leave the pocket within his
radius, and since you can't cross the pinch line that way, you left through a wall. Measured in any
other direction his disc might only be poking out through the opening. (`filters/pocket.py`.)

There are three ways for a level's file to hide things, from strongest to mildest: *remove* an
object (it isn't really there), *ignore* objects (gaps they form are of no interest), and
*suppress* a single warp (it is real, but not worth telling anyone about).

**Ignored objects** - per level, in `filters/levels/<level>.py`: a named group of objects of no
interest to the speedrun, with a reason. A gap is filtered if every one of its pinches is formed by
an object of the group.

**Removed objects** - per level, in the same file: objects which are not really there, and are
left out of the level before it is surveyed. Far stronger than ignoring, because an object which is
merely ignored still blocks lines of sight and still stops Bond fitting, whereas a removed one does
nothing at all. It therefore changes which gaps and warps are found. Every removed object is listed
with its reason in `objects_left_out.csv`.

**Overhead object** - an object whose bottom is at least 2 m above the floor it is attached to
(`OVERHEAD_REVIEW_CLEARANCE_M`), so Bond would pass underneath. Frigate's *floating doors* are the
known case: doors attached to the room below the one they appear to be in. Being overhead removes
nothing by itself. With `--review`, overhead objects are listed and drawn under `output/00_debug/overhead_objects/`
as an aid to finding them. It takes an entry in the level's file to remove one.

**Floor clearance** - how far the bottom of an object is above the highest point of the tile it is
attached to. Negative if it starts below the floor.

**Suppressed warp** - a real warp which a level's file hides, one at a time, because it is of no
interest: usually a big gap beside a crate which anyone looking at the map would see. Unlike a
generic filter it makes no claim that the warp is impossible. Each entry gives a reason and is
checked: its status, its exact width, a step no longer than recorded, and the complete list of
*nearby objects*. Listed in `suppressed.csv`, drawn faintly. (`filters/suppressed.py`.)

**Nearby objects** - for a suppressed warp, every object any part of which is within 2 m of its
pinch line, on the same sheet, each given by address with the predicates it should pass. If
anything unlisted is near, the run stops: the warp is not as simple as was claimed. Measured from
the pinch line, which is exact, rather than from the ends of the step, which come from a search.

**Expectations** - what a level file says its group should look like: how many objects, which room,
which predicates they all pass, how spread out they may be, and how far above the floor they are. They repeat what the list of objects
implies, deliberately, so that a wrong ID stops the run.

**Predicate** - a named test on one object, such as `is_square` or `is_crate`, for level files to
use. `python -m gaps.filters` lists them. (`filters/predicates.py`.)
