# Gotchas

Problems already met in real renders, with fixes. Add entries through the retro process.

## Timing

- **Frame rounding drift.** At 15 fps every animation rounds to whole frames. Earlier versions padded each beat by its own elapsed time, so rounding accumulated (0.35 s drift over 9 beats). The kit now pads to each beat's absolute end on the timeline. If drift returns, check that every beat uses `with self.beat(...)`.
- **Overrun after a late word cue.** A word near the end of a sentence (for example "wakes" in "finally wakes up your program") leaves little time. Animations after that cue must fit in the remaining slot. Budget about 0.05 x `s` each, or move them to the next beat.
- **Estimated word times.** With Kokoro, word times are spread by character count. A cue on a short word after a long number can be early or late by a few hundred milliseconds.

## Objects

- **`add_tip` changes path animations.** `ArcBetweenPoints(...).add_tip()` adds the tip as a submobject. `MoveAlongPath` over that object follows the tip too. Keep an untipped copy for the path and show the tipped copy.
- **Animating objects not on screen.** `obj.animate` on an object never added raises or does nothing. Add it (`FadeIn`, `Create`, or `self.add`) first.
- **Text on top of text.** `Write(new)` on the same spot as old text leaves both. Use `ReplacementTransform(old, new)`.
- **Clearing at the end of a segment.** `[m for m in self.mobjects if m is not header]` then `FadeOut` each. Keep the header.

## Fonts

- Proportional fonts render with broken kerning through Pango. Use `MONO` (Menlo).
- Symbols like µ, ≈, →, ✓, ✗ render in Menlo. Test a new symbol in a low-quality render before relying on it.

## Rendering

- `explainer render` runs Manim inside the project directory. `timeline.json` and `plan.json` must be there.
- `-q l` is for layout and timing checks. Colors and thin strokes look different at `-q h`. Check one high-quality frame before delivery.
