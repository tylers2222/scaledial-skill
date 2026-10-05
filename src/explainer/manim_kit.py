"""Manim helpers for timeline-driven explainer scenes.

    from explainer.manim_kit import *

    class Video(BeatScene):
        def construct(self):
            with self.beat("intro") as s:          # starts the beat's audio, pads to its slot
                self.play(Write(title), run_time=s * 0.3)
                self.wait_until_word("kernel")      # hold until the narrator says "kernel"
                self.play(FadeIn(box), run_time=self.until_word("copies"))

`explainer render` runs Manim inside the project directory, so timeline.json and
plan.json are read from there.
"""

import json
import re
from contextlib import contextmanager
from pathlib import Path

from manim import *  # noqa: F403  (re-exported for scene files)
from manim import (DOWN, LEFT, RIGHT, UP, Line, MovingCameraScene, ReplacementTransform, RoundedRectangle, Scene,
                   Text, Triangle, VGroup)

BG = "#1C1C1C"
BLUE_ = "#58C4DD"
GREEN_ = "#83C167"
YELLOW_ = "#FFFF00"
RED_ = "#FC6255"
PURPLE_ = "#9A72AC"
ORANGE_ = "#FF862F"
GREY_ = "#888888"
WHITE_ = "#FFFFFF"
MONO = "Menlo"  # Pango kerns proportional fonts badly; keep text monospace.


def _norm(word: str) -> str:
    return re.sub(r"[^\w]", "", word.lower())


class BeatMixin:
    timeline_file = "timeline.json"
    plan_file = "plan.json"

    def setup(self):
        super().setup()
        timeline = json.loads(Path(self.timeline_file).read_text())
        self.beats = {b["id"]: b for b in timeline["beats"]}
        plan = Path(self.plan_file)
        self.plan = json.loads(plan.read_text()) if plan.exists() else None
        self._beat = None
        self._beat_start = 0.0
        self._origin: float | None = None
        self.camera.background_color = BG

    def component(self, cid: str) -> dict:
        """Plan entry for a component, so labels come from plan.json instead of being retyped."""
        if not self.plan:
            raise FileNotFoundError("plan.json not found next to timeline.json")
        return next(c for c in self.plan["components"] if c["id"] == cid)

    @contextmanager
    def beat(self, bid: str):
        b = self.beats[bid]
        if self._origin is None:
            self._origin = self.renderer.time - b["start"]
        self._beat, self._beat_start = b, self.renderer.time
        self.add_sound(b["wav"])
        yield b["slot"]
        # Pad to the beat's absolute end on the timeline, so per-animation frame
        # rounding never accumulates into audio/video drift.
        left = self._origin + b["start"] + b["slot"] - self.renderer.time
        if left < -0.05:
            print(f"WARNING beat {bid} overran its audio slot by {-left:.2f}s")
        elif left > 0.01:
            self.wait(left)
        self._beat = None

    def _word_time(self, word: str, occurrence: int) -> float:
        if self._beat is None:
            raise RuntimeError("word cues only work inside `with self.beat(...)`")
        hits = [w for w in self._beat["words"] if _norm(w["word"]) == _norm(word)]
        if len(hits) < occurrence:
            spoken = " ".join(w["word"] for w in self._beat["words"])
            raise KeyError(f"beat {self._beat['id']}: word {word!r} #{occurrence} is not spoken. Spoken: {spoken}")
        return self._beat_start + hits[occurrence - 1]["start"]

    def until_word(self, word: str, occurrence: int = 1, minimum: float = 0.1) -> float:
        """Seconds from now until the word starts; use as a run_time."""
        return max(minimum, self._word_time(word, occurrence) - self.renderer.time)

    def wait_until_word(self, word: str, occurrence: int = 1) -> None:
        gap = self._word_time(word, occurrence) - self.renderer.time
        if gap > 0.01:
            self.wait(gap)


class BeatScene(BeatMixin, Scene):
    pass


class BeatCameraScene(BeatMixin, MovingCameraScene):
    pass


def label(text: str, size: int = 24, color: str = WHITE_, **kw) -> Text:
    return Text(text, font=MONO, font_size=size, color=color, **kw)


def box(name: str, sub: str | None, color: str, x: float = 0.0, y: float = 0.0,
        w: float = 2.2, h: float = 1.3) -> VGroup:
    rect = RoundedRectangle(width=w, height=h, corner_radius=0.15, color=color, stroke_width=3)
    rect.set_fill(color, opacity=0.12)
    text = VGroup(label(name, 26, color))
    if sub:
        text.add(label(sub, 16, GREY_))
    text.arrange(DOWN, buff=0.12)
    return VGroup(rect, text).move_to([x, y, 0])


def swap(old: VGroup, new: VGroup) -> ReplacementTransform:
    """Substitute one component box for another in place."""
    new.move_to(old.get_center())
    return ReplacementTransform(old, new)


class ScaleDial(VGroup):
    """Horizontal scale gauge. `dial.to(i)` animates the marker to band i (floats allowed)."""

    def __init__(self, bands: list[str], width: float = 6.0, color: str = YELLOW_, title: str = "scale"):
        super().__init__()
        self.track = Line(LEFT * width / 2, RIGHT * width / 2, color=GREY_, stroke_width=3)
        self.n = len(bands)
        ticks = VGroup()
        for i, band in enumerate(bands):
            p = self._point(i)
            ticks.add(Line(p + UP * 0.1, p + DOWN * 0.1, color=GREY_, stroke_width=2))
            ticks.add(label(band, 16, GREY_).next_to(p, DOWN, buff=0.2))
        self.marker = Triangle(color=color, fill_opacity=1).scale(0.12).rotate(3.14159).move_to(self._point(0) + UP * 0.22)
        self.title = label(title, 18, color).next_to(self.track, LEFT, buff=0.3)
        self.add(self.track, ticks, self.marker, self.title)

    def _point(self, i: float):
        return self.track.point_from_proportion(i / max(self.n - 1, 1))

    def to(self, i: float):
        return self.marker.animate.move_to(self._point(i) + UP * 0.22)
