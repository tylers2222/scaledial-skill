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
- `box(name, sub, color, x, y)`, `label(text, size, color)`, `swap(old, new)` for in-place substitution, and `ScaleDial(bands)` with `dial.to(i)`.
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
- Opacity shows importance: active 1.0, context about 0.4, bypassed or removed about 0.18.

## Additional resources

- `references/layout.md`: frame coordinates, zones, sizes, margins.
- `references/patterns.md`: visual patterns per outcome (dial up, failure, swap, split, keep, remove).
- `references/gotchas.md`: Manim and kit problems already met, with fixes.
- `examples/box1_market_data/`: a finished segment (`scene.py`, `script.json`) that walks one component up three bands. Copy its structure, not its content.
