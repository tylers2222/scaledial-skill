import json
import wave

import pytest

from explainer.manim_kit import (BLUE_, BOX_TINT, DOWN, GREEN_, RED_, WHITE_, BeatScene, Circle, FadeIn, FadeOut,
                                 LayoutError, Rectangle, ReplacementTransform, RoundedRectangle, Square,
                                 TransformFromCopy, VGroup, box, hidden_text, label, layout_problems, swap,
                                 tempconfig, transition_problems)

FRAME = (-7.1, -4.0, 7.1, 4.0)


def test_box_fill_stays_a_tint_when_the_group_goes_fully_opaque():
    card = box("Cache", "hot keys", GREEN_)
    card.set_opacity(1.0)
    assert card[0].get_fill_opacity() == pytest.approx(BOX_TINT)
    assert hidden_text([card]) == []


def test_text_in_the_fill_color_of_a_solid_card_is_hidden():
    rect = RoundedRectangle(width=3, height=1.2, color=GREEN_, fill_opacity=1.0)
    title = label("Cache", 26, GREEN_)
    [problem] = hidden_text([VGroup(rect, title)])
    assert "'Cache'" in problem


def test_solid_shape_drawn_over_text_hides_it():
    title = label("Cache", 26, WHITE_)
    cover = Square(2, color=BLUE_, fill_opacity=1.0)
    [problem] = hidden_text([title, cover])
    assert "covered by" in problem


def test_tinted_box_drawn_over_text_does_not_hide_it():
    title = label("Cache", 26, WHITE_)
    assert hidden_text([title, box("Overlay", None, BLUE_)]) == []


def test_box_wraps_a_long_name_inside_the_requested_width():
    card = box("Token bucket check", "one counter per client", GREEN_, w=3.2, h=1.1)
    assert card[0].width == pytest.approx(3.2)
    assert card[1].width <= 3.2 - 0.3
    assert layout_problems([card], FRAME) == []


def test_box_grows_when_one_word_is_wider_than_the_box():
    card = box("Authoritative", None, BLUE_, w=1.5)
    assert card[0].width > 1.5
    assert layout_problems([card], FRAME) == []


def test_label_wider_than_a_hand_made_card_is_reported_with_a_fix():
    card = VGroup(RoundedRectangle(width=2.2, height=1.3), label("Primary database", 26))
    [problem] = layout_problems([card], FRAME)
    assert "'Primary database'" in problem
    assert "widen the shape to at least" in problem and "wrap" in problem


def test_label_touching_the_border_is_reported():
    card = VGroup(Rectangle(width=2.6, height=0.9), label("API server 1", 26))
    assert len(layout_problems([card], FRAME)) == 1


def test_label_inside_a_circle_with_room_is_accepted():
    assert layout_problems([VGroup(Circle(radius=1.0), label("DB", 26))], FRAME) == []


def test_small_marker_under_a_label_is_not_its_container():
    marker = Square(0.2, fill_opacity=1).move_to([0, 0, 0])
    assert layout_problems([marker, label("scale", 26)], FRAME) == []


def test_overlapping_texts_are_reported():
    a = label("Token bucket check", 26)
    b = label("Shared check", 26).move_to(a.get_right())
    [problem] = layout_problems([a, b], FRAME)
    assert "overlaps" in problem


def test_stacked_texts_with_a_gap_are_accepted():
    lines = VGroup(label("one", 22), label("two", 22)).arrange(DOWN, buff=0.12)
    assert layout_problems([lines], FRAME) == []


def test_text_past_the_frame_edge_is_reported():
    t = label("Environment block passed at exec", 26).move_to([6.5, 3.5, 0])
    [problem] = layout_problems([t], FRAME)
    assert "edge of the frame" in problem


def test_faded_text_is_ignored():
    a = label("old caption", 26)
    b = label("new caption", 26).set_opacity(0.1)
    assert layout_problems([a, b], FRAME) == []


def test_morph_between_different_texts_is_reported():
    old, new = label("Retries can charge twice.", 22), label("One key per request.", 22)
    for anim in (ReplacementTransform(old, new), TransformFromCopy(old, new)):
        [problem] = transition_problems([anim])
        assert "swap(old, new)" in problem


def test_morph_of_the_same_text_and_swap_are_accepted():
    title, header = label("Rate limiting", 44), label("Rate limiting", 22)
    assert transition_problems([ReplacementTransform(title, header)]) == []
    assert transition_problems([swap(label("old caption", 22), label("new caption", 22))]) == []


def test_cross_fade_on_the_same_spot_is_reported_and_apart_is_accepted():
    old, new = label("same commit order", 22), label("can lag: seconds", 22)
    assert len(transition_problems([FadeOut(old), FadeIn(new)])) == 1
    far = label("can lag: seconds", 22).shift(DOWN * 2)
    assert transition_problems([FadeOut(old), FadeIn(far)]) == []


def test_swap_keeps_the_named_edge():
    old = label("receive ≈ tens of µs", 26).move_to([4, 3, 0])
    new = label("receive ≈ 1 µs", 26)
    swap(old, new, edge=[1, 0, 0])
    assert new.get_right()[0] == pytest.approx(old.get_right()[0])


def _project(tmp_path):
    wav = tmp_path / "a.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\0\0" * 8000)
    beat = {"id": "a", "wav": str(wav), "start": 0, "audio": 1, "slot": 1, "words_source": "estimated", "words": []}
    (tmp_path / "timeline.json").write_text(json.dumps({"total": 1, "beats": [beat]}))


def test_scene_fails_on_the_play_that_overflows_a_card(tmp_path, monkeypatch):
    _project(tmp_path)
    monkeypatch.chdir(tmp_path)

    class Overflow(BeatScene):
        def construct(self):
            with self.beat("a") as s:
                self.play(FadeIn(box("Cache", None, RED_, x=-4)), run_time=s * 0.2)
                card = VGroup(RoundedRectangle(width=2.2, height=1.0), label("Primary database", 26))
                self.play(FadeIn(card), run_time=s * 0.2)

    with tempconfig({"dry_run": True, "media_dir": str(tmp_path / "media"), "disable_caching": True}):
        with pytest.raises(LayoutError, match=r"(?s)beat a: .*'Primary database'"):
            Overflow().render()
