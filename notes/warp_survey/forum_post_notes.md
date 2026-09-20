# Warp survey: notes for a forum post

Rough notes, to be worked up into a post later. Gaps are referred to by name, never by number, as
the numbers shift whenever the survey changes.

## Intro

The tool reads the floor and the collision outlines of the objects out of each level, finds every
place where two walls are closer together than Bond is wide (60 cm), and then looks for a real warp
through it: two spots where he fits, with a clear line between them. The geometry is done exactly,
with no rounding, so when it says there is a warp, there is one, and the distance it gives is one
you can actually do it in (a shorter one may exist).

Its limitations:

- It only sees each level as it loads: doors shut, nothing destroyed or moved, no guards. Warps
  which need a door open are missed.
- It works from above, in 2D. It knows nothing of squeezing under things, or of any trick which
  relies on a change in height.
- "No warp found" means just that. It searches, and the search can miss.
- It has no idea of routes, so it can't tell you whether a warp is any use.
- It is built on my understanding of how movement works, not on the game's code.

## High level comments

- Hairline crack warps around doors are startlingly common. I've used a couple in TAS, in
  particular on Facility and the end of B2 'recently', and I recall Henrik saying that there were a
  fair few of them on Facility, but there are loads everywhere.
- These cracks are tiny. The tool finds 151 warps through gaps under 1 cm, and all but two of those
  are doors or glass sitting in their frames, under 0.01 cm. Those 149 average 0.00017 cm (the
  mean; the median is 0.00006 cm), so a couple of thousandths of a millimetre. The ones mentioned
  below range from 0.0000031 cm (the B1 and B2 end door) to 0.0037 cm (the train warp).
- Reading the images. You probably want to open the overviews for each level of interest and trace
  the racing line, then open the close-up of any gap near it. The colours:
  - Red: a warp, in the level as it loads.
  - Orange: the same, but through a hairline crack, under 1 cm. The width is written on the
    close-up.
  - Violet: a warp only if some object is removed first. The objects in the way are listed.
  - Blue: the tool hasn't found a warp. This does NOT mean that it has ruled one out.
  - Faint grey, overviews only: gaps which have been ruled out by geometric logic, and many are.
    I largely guided that logic (I did contribute something alongside Fable).
  - Green, close-ups only: the step, with Bond drawn at each end of it.
- The tool flattens the world to 2D, which is how Bond's movement works, and makes very little use
  of height. It does have some understanding of objects far above us, like those floating Frigate
  ghost doors: it measures how far an object is above the floor, which is how they were spotted,
  and they are taken out so that they don't block the warps underneath them. It also uses height
  to tell one storey from another. Beyond that an object is simply in the way or it isn't.

## Archives

- The door near the start which we lure open can be warped by TAS either side, but the Henrik door
  on the alternate path cannot.
- A good example of a warp "missed" by this tool is the double door corner warp on Agent, because
  it requires the doors to be open, and here we only look at the level in a single state.
- The double doors after Nat on SA/00A can also be warped, and a TAS will probably use this. I
  *think* I knew about this one but maybe not. ("TAS double door warp")
- The door immediately before Miskin's room door can also be warped, which may be useful to a TAS.
  I seem to remember an idea that used a 'ghost door' to open Miskin's door.
- The single closed door between you and the ending once the safe is open can also be warped while
  shut in a TAS. ("TAS final door warp")
- The glass upstairs can be warped through a hairline crack beside it, so the TAS won't need to
  break it on Agent. ("TAS agent glass warp")

## Aztec

- There still aren't any glass warps.
- Here we can observe another restriction of the tool: it doesn't consider the possibility of
  squeezing under obstacles in order to warp. See the point about height in the high level
  comments.

## B1 & B2

- A TAS can warp the end door on both. The B2 TAS does this I believe, but not B1. ("TAS closed end
  door warp")
- On B2 the document room warps from my TAS are present. ("TAS documents warp in" and "TAS
  documents warp out")
- On B2 the double doors by the documents, which need to be opened by a patroller on SA, can be
  warped if necessary in a full run TAS.

## Caverns

- The end elevator door can actually be warped while closed in TAS. Iirc my SA TAS did actually
  open it, but people will have to check it to see if it wiggles. ("closed elevator door warp")
- The 00A door of course remains unwarpable, even a small gap wouldn't change that. (For the
  technically curious: this is the "anvil and hammer" reasoning, `anvil_and_hammer` in
  `gaps/filters/generic.py`, and explained in `gaps/terminology.md`.)

## Control

- To reassure: there is still no Nat door warp, nor the other door out of the first room.
- The first small door has a hairline crack so could be warped by TAS, and this is useful in left
  strafe as you don't get a chance to open the door if you turn hard.
- Likewise the next door, though I can't quite remember how a TAS tackles this with my modern glass
  strats.
- Coming into the main room there are small but not hairline gaps next to the two 'corner glasses'
  ("left tiny glass gap" and "right tiny glass gap"), but the gap is to the right of the one we
  break, so it isn't on a good racing line for the stairs and isn't useful.
- All around the glass of the main room are hairline gaps, and the glass has no thickness, so this
  probably explains why guards sometimes see you through them.
- The locked double doors nearest Nat's stairs have a hairline crack down the middle, which means
  my meme idea is actually TAS viable. Unfortunately this is not the Natsplosion strat, but it
  means that a TAS can use the dead time of the protect to kill Trev without the alarm going off,
  which would be delightful. It would be an epic showdown because he has a lot of health but isn't
  invincible afaik. Effectively each shot will have to be a "trev shot" which doesn't go past him,
  so he isn't triggered to close the doors. (A bit of an aside, but I do get sidetracked often.)

## Dam

- The first automatic gate certainly has a hairline crack, but even for TAS this isn't useful.
- There's no lockshot gate warp, so for the shotless method you'll still need to pull off my silly
  lure.
- On the dam itself, the close-ups of the first and final tower doors don't actually rule out a
  warp, but it probably isn't viable and adding some further logic should show that.
- The tunnel gate warp that Sean used in the 00A TAS is still there ("tunnel gate warp"), but there
  aren't any others down in the tunnels.

## Depot

- The drone room has a hairline crack, but on the left (far) side, so it's not even useful for TAS.
- The ammo dump door has cracks both sides ("left ammo dump door crack" and "right ammo dump door
  crack"), which would be a TAS saving, but I forget, maybe it can do a rocket shot from outside?
- Now things really get interesting. Of course it finds *the* depot warp ("depot warp") and you
  know about the 2nd roller door ("far roller door"), *but* there is also a near roller door warp!
  ("TAS near roller door") It is 0.000077 cm wide and will probably save between 1 and 2 seconds
  in TAS, so is fun.

## Egypt

- The warp out of the golden gun room (TODO: what is it called?) is not found. I still assume that
  this is because the change in height is necessary to pull it off, but more understanding about
  how it works could be fed back into the tool.

## Facility

- It is absolutely littered with hairline door gaps. I used one when I TASed Facility 00A way back
  ("Ted waz ere TASing"), and there is another notable one: the gap next to the decoder door, which
  is all of 0.00063 cm wide! ("theoretical decoder door TAS warp") This would replace the
  beautiful one guard decoder door lure (OGDDL?) which I TAS'd, except that because of the
  geometry you have to warp a spectacular distance, which probably isn't fair anyway (I'm sure you
  can do it, as surely even AI hasn't fixed the crappy emulator).

## Frigate

- The 3 gaps through the pipes are of course found, and I've named them appropriately ("pipe warp",
  "harder pipe warp" and "flukey pipe warp").
- Two surprises were in store for me near the helicopter. One is potentially useful for TASing
  DLTK, as there is a hairline gap that saves you having to wait for the roller door ("potential
  roller door DLTK TAS warp"). But who would make such a TAS, and if you did you'd probably pause or
  something.
- You can warp past the other side of the helicopter provided the roller door is open
  ("helicopter warp"). <3
- It was already known, but you can get out onto one of the balconies of the bridge (left side
  looking forwards) without unlocking it. It should be very feasible. ("balcony door warp")

## Jungle

- A quick scroll across the map shows that only the elevator warps are of any note ("elevator door
  warp (left)" and "elevator door warp (right)"). Yes there is one each side, but you already knew
  that.

## Runway

- There is a hairline gap into the hut, but even a TAS won't want it.

## Silo

- Silo again has lots of hairline gaps to the side of doors, but many of them can't be warped:
  the wall beyond the door comes in so close that there is nowhere for Bond to fit on the far side.
- I also struggle to follow the map since I barely know how to play the level. Where's the start?
- I don't think any of the other hairline cracks are actually useful to a TAS, but who knows. The
  exception is the elevator door, which is a teeny timesaver for TAS. ("TAS elevator door warp")
- One which is less hairline was known before, and there is a funny clip from a certain hoard when
  I hit it first try after saying I wouldn't. ("R-lean'd by Ted FIRST TRY")
- Otherwise I guess I haven't looked at it closely, but it doesn't look exciting (it's Silo) (soz).

## Statue

- Statue was funny, and useful for examples in development.
- Of note for speedrunning is only the block warp. ("block warp")
- But there is a fun (perhaps I'm overusing the word) secret area among the flight recorder spawns
  which isn't too far to warp in and out of: 117 cm to get in. Turbo mode might help. ("secret
  area in" and "secret area out") All I can really think is that some troll rom should hide the FR in here >:)

## Streets

- There is just the one warp, and it is the wrong side of a barrier. ("half-a-frame barrier warp")
  I think I remember someone suggesting it at some point, and no doubt someone has at multiple
  points. It might technically save a hair, but why.

## S1 & S2

- On S1 there is still no warp into the OOK hut :(
- On S1 there is a cute trio of crates that you can get in the middle of.
- On S1 there is no warp in the main building.
- There is nothing of note on S2.

## Train

- This is the fun one. Slightly concerningly the tool didn't find the train warp initially, but
  without me directly bringing it up Claude just slipped into conversation that all gaps under
  1 cm were quietly being left without a close-up because they were too small... it had found it
  after all :) ("train warp")
- And indeed this really is just another example of a door (which is what the trap*door* is) being
  misaligned a touch.
- The "ouro door" just before it can be warped through a hairline crack ("ouro door"), which a TAS
  may find useful as reassurance, but a guard should be opening it of course.
- There is also a fun superwarp which Claude found unprompted, which I leave as a little easter
  egg.

