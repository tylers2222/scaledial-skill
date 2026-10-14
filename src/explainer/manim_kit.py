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
from manim import (DOWN, LEFT, RIGHT, UP, Line, MarkupText, MovingCameraScene, ReplacementTransform, RoundedRectangle,
                   Scene, SingleStringMathTex, Text, Triangle, VGroup, VMobject, color_to_rgb)

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
BOX_TINT = 0.12  # the fill opacity of a box, whatever opacity the box is set to
MIN_CONTRAST = 1.5  # WCAG contrast ratio below which text on a filled shape counts as hidden
TEXT_TYPES = (Text, MarkupText, SingleStringMathTex)


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
        self.check_contrast()
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

    def play(self, *args, **kwargs):
        super().play(*args, **kwargs)
        self.check_contrast()

    def check_contrast(self) -> None:
        problems = hidden_text(self.mobjects)
        if problems:
            where = f"beat {self._beat['id']}" if self._beat else "outside a beat"
            raise LowContrastError(
                f"{where}: text cannot be read on the shape behind it.\n" + "\n".join(problems) +
                "\nset_opacity on a group also sets the fill of every shape in it. Build cards with box(), whose fill "
                "stays a tint at any opacity, or draw the text in a color that contrasts with the fill.")


class LowContrastError(RuntimeError):
    pass


def _luminance(rgb) -> float:
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _over(rgb, alpha: float, under):
    return [alpha * a + (1 - alpha) * b for a, b in zip(rgb, under)]


def _fill(m: VMobject):
    """Fill color and opacity as drawn: a Text's own style is unused; its glyphs carry it."""
    part = next(iter(m.family_members_with_points()), m)
    return part.get_fill_color(), float(part.get_fill_opacity())


def _drawn(mobjects) -> list[VMobject]:
    """VMobjects in draw order. A text is one entry; its glyphs are not shapes behind it."""
    out = []

    def walk(m):
        if isinstance(m, TEXT_TYPES):
            out.append(m)
            return
        if isinstance(m, VMobject) and m.has_points():
            out.append(m)
        for sm in m.submobjects:
            walk(sm)

    for m in mobjects:
        walk(m)
    return out


def hidden_text(mobjects) -> list[str]:
    """One line per visible text whose center lies on a filled shape it does not contrast with."""
    bg = color_to_rgb(BG)
    drawn = _drawn(mobjects)
    problems = []
    for i, text in enumerate(drawn):
        if not isinstance(text, TEXT_TYPES):
            continue
        t_color, t_alpha = _fill(text)
        if t_alpha <= 0.2:
            continue
        x, y, _ = text.get_center()
        under = [m for m in drawn[:i] if not isinstance(m, TEXT_TYPES) and m.get_fill_opacity() >= 0.3
                 and m.get_left()[0] <= x <= m.get_right()[0] and m.get_bottom()[1] <= y <= m.get_top()[1]]
        if not under:
            continue
        f_color, f_alpha = _fill(under[-1])
        back = _over(color_to_rgb(f_color), f_alpha, bg)
        lum = sorted([_luminance(_over(color_to_rgb(t_color), t_alpha, back)), _luminance(back)])
        ratio = (lum[1] + 0.05) / (lum[0] + 0.05)
        if ratio < MIN_CONTRAST:
            name = getattr(text, "original_text", type(text).__name__)
            problems.append(f"  {name!r}: text {t_color.to_hex()} at {t_alpha:.2f} on fill {f_color.to_hex()} "
                            f"at {f_alpha:.2f}, contrast {ratio:.2f}:1 (needs {MIN_CONTRAST}:1)")
    return problems


class BeatScene(BeatMixin, Scene):
    pass


class BeatCameraScene(BeatMixin, MovingCameraScene):
    pass


def label(text: str, size: int = 24, color: str = WHITE_, **kw) -> Text:
    return Text(text, font=MONO, font_size=size, color=color, **kw)


class Panel(RoundedRectangle):
    """A box outline whose fill never exceeds BOX_TINT, so set_opacity(1.0) cannot turn it into a solid block."""

    def set_fill(self, color=None, opacity=None, family=True):
        return super().set_fill(color, None if opacity is None else min(opacity, BOX_TINT), family)


def box(name: str, sub: str | None, color: str, x: float = 0.0, y: float = 0.0,
        w: float = 2.2, h: float = 1.3) -> VGroup:
    rect = Panel(width=w, height=h, corner_radius=0.15, color=color, stroke_width=3)
    rect.set_fill(color, opacity=BOX_TINT)
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
