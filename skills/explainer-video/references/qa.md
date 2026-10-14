# Visual QA

`explainer qa` checks audio and video length against the timeline and writes `qa/sheet.png`: one frame near the end of each beat, in beat order. Read the sheet after every low-quality render. Read single frames in `qa/` at full size when a tile is unclear.

The agent sees still frames, not motion. Flicker, a jump between two frames, or an animation that runs too fast can pass this review. Say so when delivering.

## Check every tile for

1. **Overlap.** Text on text, text on boxes, arrows through labels.
2. **Clipping.** Anything past the frame edge. Keep 0.5 units of margin.
3. **Contradiction.** Any label that reads differently from the narration of the same beat, or from the plan. Example from a real render: a summary column showed "kernel sockets → milliseconds" right after the narration said "tens of microseconds". Both were true in context, but the column had no header that said "your edge is in", so it read as a contradiction.
4. **Stale objects.** A cost list, badge, or meter from an earlier band that is still on screen.
5. **Empty frames.** A tile with only the header means the beat's visuals ended early or never started.
6. **Legibility.** Text smaller than font size 18 at 1080p, low contrast on the dark background.
7. **Consistency.** The dial, the cost corner, and the colors stay in the same places across segments.

## Render warnings

- `WARNING beat <id> overran its audio slot`: the animations in that beat take longer than its audio. Shorten run_time fractions, or move a step to the next beat. Do not slow the voice.
- `PROBLEM: video is Xs but timeline is Ys`: a beat overran or a beat was skipped in `scene.py`.
- `word ... is not spoken`: a word cue names a word that is not in the spoken text. Check aliases.
- `LowContrastError`: a text sits on a filled shape in nearly the same color, usually after `set_opacity` on a group. Build the card with `box()`, or give the text a contrasting color.

## Known failure types

Add new types here through the retro process.

- Labels positioned with absolute coordinates collide after a text change. Prefer `next_to` and `arrange`.
- Final beat frames can fall past the last video frame at low frame rates. `explainer qa` clamps this.
