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
from manim import (DOWN, LEFT, ORIGIN, RIGHT, UP, Animation, AnimationGroup, FadeIn, FadeOut, FadeTransform, Line,
                   MarkupText, MovingCameraScene, RoundedRectangle, Scene, SingleStringMathTex, Succession, Text,
                   Transform, Triangle, VGroup, VMobject, color_to_rgb, config)

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
BOX_PAD = 0.2  # space between a box's border and its text
TEXT_INSET = 0.15  # the least space between text and the border of the shape it sits in
EDGE = 0.05  # overlap smaller than this, between texts or past the frame edge, is not reported
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
        problems = transition_problems(args)
        if problems:
            raise LayoutError(f"{self._where()}: this animation shows two texts on top of each other while it runs.\n"
                              + "\n".join(problems))
        super().play(*args, **kwargs)
        self.check_contrast()
        self.check_layout()

    def _where(self) -> str:
        return f"beat {self._beat['id']}" if self._beat else "outside a beat"

    def check_contrast(self) -> None:
        problems = hidden_text(self.mobjects)
        if problems:
            raise LowContrastError(
                f"{self._where()}: text cannot be read on the shape behind it, or a filled shape covers it.\n" + "\n".join(problems) +
                "\nset_opacity on a group also sets the fill of every shape in it. Build cards with box(), whose fill "
                "stays a tint at any opacity, draw the text in a color that contrasts with the fill, and do not put a "
                "filled shape over text that is still on screen.")

    def check_layout(self) -> None:
        frame = getattr(self.camera, "frame", None)
        if frame is not None:
            x, y, _ = frame.get_center()
            bounds = (x - frame.width / 2, y - frame.height / 2, x + frame.width / 2, y + frame.height / 2)
        else:
            bounds = (-config.frame_width / 2, -config.frame_height / 2, config.frame_width / 2, config.frame_height / 2)
        problems = layout_problems(self.mobjects, bounds)
        if problems:
            raise LayoutError(f"{self._where()}: text does not fit where it is placed.\n" + "\n".join(problems))


class LowContrastError(RuntimeError):
    pass


class LayoutError(RuntimeError):
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
    return sorted(out, key=lambda m: m.z_index)


def _contains(m: VMobject, x: float, y: float) -> bool:
    return m.get_left()[0] <= x <= m.get_right()[0] and m.get_bottom()[1] <= y <= m.get_top()[1]


def _name(text) -> str:
    return getattr(text, "original_text", None) or getattr(text, "tex_string", None) or type(text).__name__


def _visible(text) -> bool:
    return _fill(text)[1] > 0.2 and text.width > 0


def hidden_text(mobjects) -> list[str]:
    """One line per visible text whose center lies on a filled shape it does not contrast with.

    Fills drawn under the text set its background; fills drawn over it cover glyphs and background alike."""
    bg = color_to_rgb(BG)
    drawn = _drawn(mobjects)
    problems = []
    for i, text in enumerate(drawn):
        if not isinstance(text, TEXT_TYPES) or not _visible(text):
            continue
        t_color, t_alpha = _fill(text)
        x, y, _ = text.get_center()
        fills = [(j, m) for j, m in enumerate(drawn) if j != i and not isinstance(m, TEXT_TYPES)
                 and m.get_fill_opacity() >= 0.3 and _contains(m, x, y)]
        if not fills:
            continue
        below = [m for j, m in fills if j < i]
        above = [m for j, m in fills if j > i]
        back = bg
        if below:
            f_color, f_alpha = _fill(below[-1])
            back = _over(color_to_rgb(f_color), f_alpha, bg)
        glyph = _over(color_to_rgb(t_color), t_alpha, back)
        for m in above:
            c_color, c_alpha = _fill(m)
            glyph = _over(color_to_rgb(c_color), c_alpha, glyph)
            back = _over(color_to_rgb(c_color), c_alpha, back)
        lum = sorted([_luminance(glyph), _luminance(back)])
        ratio = (lum[1] + 0.05) / (lum[0] + 0.05)
        if ratio < MIN_CONTRAST:
            if above:
                c_color, c_alpha = _fill(above[-1])
                where = f"covered by a {type(above[-1]).__name__} filled {c_color.to_hex()} at {c_alpha:.2f} drawn over it"
            else:
                f_color, f_alpha = _fill(below[-1])
                where = f"on fill {f_color.to_hex()} at {f_alpha:.2f}"
            problems.append(f"  {_name(text)!r}: text {t_color.to_hex()} at {t_alpha:.2f} {where}, "
                            f"contrast {ratio:.2f}:1 (needs {MIN_CONTRAST}:1)")
    return problems


def _box_of(m) -> tuple[float, float, float, float]:
    return m.get_left()[0], m.get_bottom()[1], m.get_right()[0], m.get_top()[1]


def _overlap(a, b) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > EDGE and min(a[3], b[3]) - max(a[1], b[1]) > EDGE


def _shape_visible(m: VMobject) -> bool:
    stroke = m.get_stroke_opacity() if m.get_stroke_width() > 0 else 0.0
    return max(stroke, m.get_fill_opacity()) >= 0.1


def _fit_advice(text, inner_w: float) -> str:
    size = getattr(text, "font_size", None)
    advice = []
    if size and text.width > 0:
        fit = int(size * inner_w / text.width)
        if fit >= 16:
            advice.append(f"shrink the font to {fit} or less")
    advice.append(f"widen the shape to at least {text.width + 2 * BOX_PAD:.2f}")
    advice.append("wrap the text onto two lines")
    return ", ".join(advice[:-1]) + " or " + advice[-1]


def layout_problems(mobjects, frame: tuple[float, float, float, float]) -> list[str]:
    """One line per visible text that leaves the shape it sits in, overlaps other text, or leaves the frame.

    A text sits in the smallest visible closed shape that holds its center and is at least half its area.
    `frame` is (left, bottom, right, top) of what the camera shows."""
    drawn = _drawn(mobjects)
    texts = [m for m in drawn if isinstance(m, TEXT_TYPES) and _visible(m)]
    shapes = [m for m in drawn if not isinstance(m, TEXT_TYPES) and m.is_closed() and _shape_visible(m)]
    problems = []
    for t in texts:
        tb = _box_of(t)
        x, y, _ = t.get_center()
        area = t.width * t.height
        holders = [s for s in shapes if _contains(s, x, y) and s.width * s.height >= 0.5 * area]
        if holders:
            s = min(holders, key=lambda m: m.width * m.height)
            sb = _box_of(s)
            out_x = max(sb[0] + TEXT_INSET - tb[0], tb[2] - (sb[2] - TEXT_INSET), 0)
            out_y = max(sb[1] + TEXT_INSET - tb[1], tb[3] - (sb[3] - TEXT_INSET), 0)
            if out_x > 0 or out_y > 0:
                problems.append(
                    f"  {_name(t)!r} is {t.width:.2f} wide and {t.height:.2f} high but the {type(s).__name__} it sits "
                    f"in at ({s.get_x():.1f}, {s.get_y():.1f}) is {s.width:.2f} x {s.height:.2f}. "
                    f"It needs {TEXT_INSET} of space inside each border. Build the card with box(), which fits it to its "
                    f"text, or {_fit_advice(t, s.width - 2 * BOX_PAD)}.")
        if tb[0] < frame[0] - EDGE or tb[1] < frame[1] - EDGE or tb[2] > frame[2] + EDGE or tb[3] > frame[3] + EDGE:
            if _overlap(tb, frame):
                problems.append(f"  {_name(t)!r} runs off the edge of the frame. Move it inward (keep 0.4 of margin), "
                                f"shrink the font, or wrap the text.")
    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            if _overlap(_box_of(a), _box_of(b)):
                problems.append(
                    f"  {_name(a)!r} at ({a.get_x():.1f}, {a.get_y():.1f}) overlaps {_name(b)!r} at "
                    f"({b.get_x():.1f}, {b.get_y():.1f}). Move one with next_to/arrange, shrink the font, wrap the "
                    f"text, or FadeOut the old text before the new one appears.")
    return problems


def _simultaneous(animations) -> list[Animation]:
    """Animations that run at the same time. A group with lag_ratio 1 (Succession) runs its parts one by one."""
    out = []
    for a in animations:
        if isinstance(a, AnimationGroup) and a.lag_ratio < 1:
            out.extend(_simultaneous(a.animations))
        elif isinstance(a, Animation):
            out.append(a)
    return out


def _texts(m) -> list:
    return [] if m is None else [t for t in _drawn([m]) if isinstance(t, TEXT_TYPES)]


def transition_problems(animations) -> list[str]:
    """One line per animation in a play call that would show two different texts on top of each other mid-way.

    A Transform between texts with different words morphs glyph into glyph and is garbled while it runs;
    a FadeOut and a FadeIn of overlapping texts in the same play cross-fade one over the other."""
    anims = _simultaneous(animations)
    problems = []
    for a in anims:
        if isinstance(a, Transform) and not isinstance(a, (FadeIn, FadeOut, FadeTransform)):
            src = sorted(_name(t) for t in _texts(a.mobject))
            dst = sorted(_name(t) for t in _texts(a.target_mobject))
            if src and dst and src != dst:
                problems.append(f"  {type(a).__name__} morphs {' / '.join(src)!r} into {' / '.join(dst)!r}: the "
                                f"letters scramble while it runs. Use swap(old, new) to fade the old text out "
                                f"and the new one in, in place.")
    outs = [t for a in anims if isinstance(a, FadeOut) for t in _texts(a.mobject)]
    ins = [t for a in anims if isinstance(a, FadeIn) for t in _texts(a.mobject)]
    for o in outs:
        for n in ins:
            if _name(o) != _name(n) and _overlap(_box_of(o), _box_of(n)):
                problems.append(f"  FadeOut {_name(o)!r} and FadeIn {_name(n)!r} in the same play: the two "
                                f"cross-fade on the same spot. Use swap(old, new), or fade the old text out in one "
                                f"play and the new one in with the next.")
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


def _wrap(text: str, size: int, color: str, width: float) -> VGroup:
    """Lines of at most `width`, broken at spaces. A single word wider than `width` gets a line of its own."""
    lines: list[str] = []
    for word in text.split():
        if lines and label(f"{lines[-1]} {word}", size).width <= width:
            lines[-1] += f" {word}"
        else:
            lines.append(word)
    return VGroup(*(label(line, size, color) for line in lines)).arrange(DOWN, buff=0.08)


def box(name: str, sub: str | None, color: str, x: float = 0.0, y: float = 0.0,
        w: float = 2.2, h: float = 1.3) -> VGroup:
    """A component card. Text wraps to fit width w; the card grows past w and h only when the text cannot fit."""
    inner = w - 2 * BOX_PAD
    text = VGroup(_wrap(name, 26, color, inner))
    if sub:
        text.add(_wrap(sub, 16, GREY_, inner))
    text.arrange(DOWN, buff=0.12)
    rect = Panel(width=max(w, text.width + 2 * BOX_PAD), height=max(h, text.height + 2 * BOX_PAD),
                 corner_radius=0.15, color=color, stroke_width=3)
    rect.set_fill(color, opacity=BOX_TINT)
    return VGroup(rect, text).move_to([x, y, 0])


def swap(old: VMobject, new: VMobject, edge=ORIGIN) -> Succession:
    """Replace one box or text with another in place: the old fades out, then the new fades in.

    `edge` keeps that side lined up (RIGHT for a label in the top-right corner). A Transform between different
    words would scramble the letters mid-way."""
    new.move_to(old, aligned_edge=edge)
    return Succession(FadeOut(old), FadeIn(new))


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
