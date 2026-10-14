# Gotchas

Problems already met in real renders, with fixes. Add entries through the retro process.

## Timing

- **Frame rounding drift.** At 15 fps every animation rounds to whole frames. Earlier versions padded each beat by its own elapsed time, so rounding accumulated (0.35 s drift over 9 beats). The kit now pads to each beat's absolute end on the timeline. If drift returns, check that every beat uses `with self.beat(...)`.
- **Overrun after a late word cue.** A word near the end of a sentence (for example "wakes" in "finally wakes up your program") leaves little time. Animations after that cue must fit in the remaining slot. Budget about 0.05 x `s` each, or move them to the next beat.
- **Estimated word times.** With Kokoro, word times are spread by character count. A cue on a short word after a long number can be early or late by a few hundred milliseconds.

## Objects

- **`add_tip` changes path animations.** `ArcBetweenPoints(...).add_tip()` adds the tip as a submobject. `MoveAlongPath` over that object follows the tip too. Keep an untipped copy for the path and show the tipped copy.
- **Animating objects not on screen.** `obj.animate` on an object never added raises or does nothing. Add it (`FadeIn`, `Create`, or `self.add`) first.
- **Title hidden by its own card.** A hand-made card drew its title in the card color. `card.animate.set_opacity(1.0)` set the rectangle fill to 1.0 too, and the title vanished into the fill while it was narrated. Use `box()`. The kit now raises `LowContrastError` after each animation when text and the fill behind it have a contrast below 1.5:1.
- **Text on top of text.** `Write(new)` on the same spot as old text leaves both. `ReplacementTransform(old, new)` between different words scrambles the letters while it runs (gauntlet D9: text morphs in 4 of the 5 flawed videos, and in this skill's own example). `FadeOut(old), FadeIn(new)` in one play cross-fades both on the same spot. Use `swap(old, new)`. The kit raises `LayoutError` before any of these runs.
- **Label wider than its box.** A scene sized boxes before their labels: "Token bucket check" at font 26 is 3.9 wide in a `w=3.2` box, and "Primary database" (3.4 wide) overran a hand-sized card. `box()` now wraps its text to fit `w` and grows when it must. The kit raises `LayoutError` when text comes closer than 0.08 to the border of the shape it sits in, overlaps other text, or leaves the frame. A grown box can reach its neighbour: give long names fewer boxes per row.
- **A copy slid off its original.** `strings.copy().animate.move_to(...)` passes the copy over the original, which reads as garbled text for the first frames. The kit does not check text in motion. Fade the copy in at its destination, or move it first in a direction away from the other text.
- **Clearing at the end of a segment.** `[m for m in self.mobjects if m is not header]` then `FadeOut` each. Keep the header.

## Fonts

- Proportional fonts render with broken kerning through Pango. Use `MONO` (Menlo).
- Symbols like µ, ≈, →, ✓, ✗ render in Menlo. Test a new symbol in a low-quality render before relying on it.

## Rendering

- `explainer render` runs Manim inside the project directory. `timeline.json` and `plan.json` must be there.
- `-q l` is for layout and timing checks. Colors and thin strokes look different at `-q h`. Check one high-quality frame before delivery.
