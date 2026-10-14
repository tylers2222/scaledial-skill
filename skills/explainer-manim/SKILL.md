---
name: explainer-manim
description: This skill should be used when the user asks to "animate the plan", "write the scenes", "fix the layout", "the label overlaps", "make the animation match the narration", "render the video", or when the explainer-video skill reaches its scenes stage. It covers scene.py on top of explainer.manim_kit (beat slots, word cues, scale dial, in-place substitution), rendering with `explainer render`, and layout rules.
version: 0.1.0
---

# Manim scenes

Scenes are Python files built on `explainer.manim_kit`, rendered by `explainer render`. Narration timing drives everything: a scene never decides how long a beat lasts.

## The kit

```python
from explainer.manim_kit import *        # also re-exports all of manim

class Video(BeatScene):                  # BeatCameraScene for zoom and pan
    def construct(self):
        with self.beat("intro") as s:    # starts the beat's audio; s = slot seconds
            self.play(Write(title), run_time=s * 0.3)
            self.wait_until_word("contract")              # hold until that word is spoken
            self.play(FadeIn(box), run_time=self.until_word("cost"))
```

- `with self.beat(id) as s`: adds the beat's audio and pads to the beat's end on the timeline. It prints `WARNING beat <id> overran` when the animations are longer than the audio.
- Budget run_times as fractions of `s`. Keep the sum of fractions at or below about 0.85 so word cues and frame rounding have room.
- `wait_until_word(word, occurrence=1)` and `until_word(word)` use the spoken form. They raise an error that lists the spoken words if the cue is wrong.
- `self.component(id)` returns the plan entry. Take labels (`pick`, `band`, `cost`) from it so the screen cannot disagree with the plan.
- `box(name, sub, color, x, y, w, h)` for every component card, `label(text, size, color)`, `swap(old, new, edge=ORIGIN)` to replace a box or a text in place, and `ScaleDial(bands)` with `dial.to(i)`. A box wraps its text to fit width `w` and grows only when a single word or the stacked lines do not fit. It keeps its fill a faint tint at any opacity, so its title stays readable. Do not write your own card helper.
- Replace text with `swap(old, new)`: the old text fades out, then the new one fades in. Use `edge=RIGHT` for a label in the top-right corner so its right side stays lined up. `ReplacementTransform` between two different texts scrambles the letters mid-way. Keep it for the same text moving or resizing, such as the title becoming the header.
- Palette constants: `BG`, `BLUE_`, `GREEN_`, `YELLOW_`, `RED_`, `PURPLE_`, `ORANGE_`, `GREY_`, `WHITE_`. Font: `MONO` (monospace, because Pango kerns proportional fonts badly).

## Procedure

1. Read `plan.json`, `script.json`, and `timeline.json`. Map each beat to one visual change.
2. Lay out the persistent diagram first, using the zones in `references/layout.md`.
3. Write one `with self.beat(...)` block per beat, in script order. Every beat id in the script needs a block.
4. Use the patterns in `references/patterns.md` for each outcome's segment.
5. `explainer render -q l` (480p15, seconds). Fix any overrun warning.
6. `explainer qa`, then read `qa/sheet.png`. Fix and repeat.
7. `explainer render -q h` (1080p60) for delivery.

## Rules

- One idea moves at a time. The viewer's eye goes to motion.
- Remove or replace what the narration has moved past. Stale labels are the most common QA failure.
- Never animate the audio to fit. If a beat needs more visual time, split the beat in the script.
- Opacity shows importance: active 1.0, context about 0.4, bypassed or removed about 0.18. `set_opacity` sets the fill too, so it turns a hand-made outline into a solid block. The render fails with `LowContrastError` when text sits on a fill it cannot be read on, or a filled shape covers text that is still on screen.
- The render fails with `LayoutError` after an animation that leaves text outside the shape it sits in, text on top of other text, or text past the frame edge. It also fails before an animation that morphs one text into a different text, or fades one text out while another fades in on the same spot. The message names the text and what to change: shrink the font, widen the shape, wrap the text, move it, or use `swap`. Fix the layout. Do not catch the error.

## Additional resources

- `references/layout.md`: frame coordinates, zones, sizes, margins.
- `references/patterns.md`: visual patterns per outcome (dial up, failure, swap, split, keep, remove).
- `references/gotchas.md`: Manim and kit problems already met, with fixes.
- `examples/box1_market_data/`: a finished segment (`scene.py`, `script.json`) that walks one component up three bands. Copy its structure, not its content.
