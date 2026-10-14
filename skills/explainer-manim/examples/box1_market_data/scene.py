"""Box 1 of a low-latency trading explainer: one component walked up three scale bands.

Shows the kit patterns: beat slots, fractional run_time budgets, word cues,
dimming a bypassed component, and a closing summary table.
"""

from explainer.manim_kit import *


class MarketDataPath(BeatScene):
    def construct(self):
        # ---- intro ----------------------------------------------------------
        with self.beat("intro") as s:
            title = label("Box 1 · Market-data path", 44, BLUE_, weight=BOLD)
            q = label("How does a packet reach your strategy?", 26, GREY_).next_to(title, DOWN, buff=0.4)
            self.play(Write(title), run_time=s * 0.35)
            self.play(FadeIn(q, shift=UP * 0.2), run_time=s * 0.2)
            self.wait(s * 0.2)
            header = label("Box 1 · Market-data path", 22, BLUE_).to_corner(UL, buff=0.4)
            self.play(ReplacementTransform(title, header), FadeOut(q), run_time=s * 0.2)

        # ---- path: word cues pin each box to the word that names it ---------
        exch = box("Exchange", "matching engine", WHITE_, -5.5, 0.3)
        nic = box("NIC", "network card", BLUE_, -2.2, 0.3)
        kern = box("Kernel", "TCP/IP stack", GREY_, 1.1, 0.3)
        strat = box("Strategy", "your program", GREEN_, 4.6, 0.3)
        a1 = Arrow(exch.get_right(), nic.get_left(), buff=0.1, color=GREY_)
        a2 = Arrow(nic.get_right(), kern.get_left(), buff=0.1, color=GREY_)
        a3 = Arrow(kern.get_right(), strat.get_left(), buff=0.1, color=GREY_)
        with self.beat("path") as s:
            self.play(FadeIn(exch, shift=RIGHT * 0.3), run_time=self.until_word("lands"))
            pkt = Dot(exch.get_right(), color=YELLOW_, radius=0.1)
            self.play(GrowArrow(a1), FadeIn(nic), FadeIn(pkt), run_time=s * 0.08)
            self.play(pkt.animate.move_to(nic.get_center()), run_time=self.until_word("kernel"))
            self.play(GrowArrow(a2), FadeIn(kern), run_time=s * 0.08)
            self.play(pkt.animate.move_to(kern.get_center()), run_time=s * 0.1)
            self.play(Wiggle(kern, scale_value=1.05), run_time=self.until_word("wakes"))
            self.play(GrowArrow(a3), FadeIn(strat), run_time=s * 0.05)
            self.play(pkt.animate.move_to(strat.get_center()), run_time=s * 0.05)
            self.play(Indicate(strat, color=GREEN_), FadeOut(pkt), run_time=s * 0.04)

        # ---- cost -----------------------------------------------------------
        tags = VGroup(*(label(t, 20, RED_) for t in ("interrupt", "syscall", "memory copy")))
        tags.arrange(DOWN, buff=0.18).next_to(kern, DOWN, buff=0.45)
        meter = label("receive ≈ tens of µs", 26, RED_).to_corner(UR, buff=0.4).shift(DOWN * 0.6)
        with self.beat("cost") as s:
            self.play(kern[0].animate.set_color(RED_), run_time=s * 0.1)
            for t in tags:
                self.play(FadeIn(t, shift=UP * 0.2), run_time=s * 0.12)
            self.play(Write(meter), run_time=s * 0.25)

        # ---- why (band 1: keep the simple option) ---------------------------
        badge1 = label("Level 1 · most firms", 24, WHITE_).to_corner(UR, buff=0.4)
        pros = VGroup(*(label(t, 22, GREEN_) for t in ("✓ simple", "✓ safe", "✓ fast enough")))
        pros.arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([4.4, -2.2, 0])
        stop = label("edge measured in ms? stop here.", 22, YELLOW_).to_edge(DOWN, buff=0.45)
        with self.beat("why") as s:
            self.play(FadeOut(tags), FadeIn(badge1), run_time=s * 0.1)
            for p in pros:
                self.play(FadeIn(p, shift=RIGHT * 0.2), run_time=s * 0.1)
            self.wait_until_word("edge")
            self.play(Write(stop), run_time=s * 0.2)

        # ---- bypass (band 2) ------------------------------------------------
        badge2 = label("Level 2 · colocated prop shop", 24, WHITE_).to_corner(UR, buff=0.4)
        arc = ArcBetweenPoints(nic.get_top() + UP * 0.05, strat.get_top() + UP * 0.05, angle=-PI / 2.2,
                               color=GREEN_, stroke_width=5)
        arc_tip = arc.copy().add_tip(tip_length=0.25)
        dma = label("DMA → user memory", 20, GREEN_).move_to([1.2, 1.55, 0])
        spin = Arc(radius=0.35, start_angle=0, angle=1.6 * PI, color=YELLOW_, stroke_width=4).add_tip(tip_length=0.15)
        spin.next_to(strat, DOWN, buff=0.35)
        spin_lbl = label("pinned core polls", 18, YELLOW_).next_to(spin, DOWN, buff=0.15)
        with self.beat("bypass") as s:
            self.play(FadeOut(pros), FadeOut(stop), swap(badge1, badge2, RIGHT), run_time=s * 0.08)
            self.play(Create(arc_tip), FadeIn(dma), run_time=s * 0.18)
            pkt = Dot(nic.get_top(), color=YELLOW_, radius=0.1)
            self.play(MoveAlongPath(pkt, arc), run_time=s * 0.14)
            self.play(FadeOut(pkt), FadeIn(spin), FadeIn(spin_lbl), run_time=s * 0.1)
            self.play(Rotate(spin, -2 * PI), run_time=s * 0.18)
            self.play(VGroup(kern, a2, a3).animate.set_opacity(0.18), run_time=s * 0.15)

        # ---- bypass cost ----------------------------------------------------
        meter2 = label("receive ≈ 1 µs", 26, GREEN_).move_to(meter, aligned_edge=RIGHT)
        cons2 = VGroup(label("✗ one core at 100%, always", 20, ORANGE_),
                       label("✗ special NICs + software", 20, ORANGE_))
        cons2.arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_corner(DR, buff=0.5)
        with self.beat("bypass_cost") as s:
            self.play(swap(meter, meter2, RIGHT), run_time=s * 0.15)
            self.play(Rotate(spin, -2 * PI), FadeIn(cons2[0], shift=UP * 0.2), run_time=s * 0.25)
            self.play(Rotate(spin, -2 * PI), FadeIn(cons2[1], shift=UP * 0.2), run_time=s * 0.25)

        # ---- fpga (band 3) --------------------------------------------------
        badge3 = label("Level 3 · top HFT", 24, WHITE_).to_corner(UR, buff=0.4)
        fpga = box("FPGA", "on the wire", PURPLE_, -2.2, -2.3, w=2.2, h=1.1)
        a_nf = Arrow(nic.get_bottom(), fpga.get_top(), buff=0.08, color=PURPLE_)
        order = CurvedArrow(fpga.get_left(), exch.get_bottom() + DOWN * 0.05, angle=-PI / 3, color=ORANGE_)
        order_lbl = label("order", 20, ORANGE_).next_to(order, DOWN, buff=0.05).shift(LEFT * 0.3)
        meter3 = label("tick-to-trade ≈ 100s of ns", 26, PURPLE_).move_to(meter2, aligned_edge=RIGHT)
        with self.beat("fpga") as s:
            self.play(FadeOut(cons2), FadeOut(spin), FadeOut(spin_lbl), FadeOut(arc_tip), FadeOut(dma),
                      swap(badge2, badge3, RIGHT), run_time=s * 0.08)
            self.play(GrowArrow(a_nf), FadeIn(fpga, shift=UP * 0.2), run_time=s * 0.12)
            pkt = Dot(exch.get_right(), color=YELLOW_, radius=0.1)
            self.add(pkt)
            self.play(pkt.animate.move_to(nic.get_center()), run_time=s * 0.1)
            self.play(pkt.animate.move_to(fpga.get_center()), run_time=self.until_word("order"))
            self.play(Flash(fpga, color=PURPLE_), pkt.animate.set_color(ORANGE_), run_time=s * 0.06)
            self.play(Create(order), FadeIn(order_lbl), run_time=s * 0.1)
            self.play(MoveAlongPath(pkt, order), run_time=s * 0.1)
            self.play(FadeOut(pkt), swap(meter2, meter3, RIGHT), run_time=s * 0.1)

        # ---- fpga cost ------------------------------------------------------
        cons3 = VGroup(label("✗ hardware is slow to change", 20, ORANGE_),
                       label("→ keep only the simplest logic", 20, ORANGE_))
        cons3.arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_corner(DR, buff=0.5)
        with self.beat("fpga_cost") as s:
            self.play(FadeIn(cons3[0], shift=UP * 0.2), run_time=s * 0.18)
            self.play(FadeIn(cons3[1], shift=UP * 0.2), run_time=s * 0.18)
            self.play(Circumscribe(fpga, color=PURPLE_), run_time=s * 0.3)

        # ---- summary: column header says what the middle column means -------
        rows = [("kernel sockets", "milliseconds", "simple", GREY_),
                ("kernel bypass", "microseconds", "burns a core", GREEN_),
                ("FPGA", "nanoseconds", "hardware eng.", PURPLE_)]
        table = VGroup(*(VGroup(label(n, 28, c), label(l, 28, WHITE_), label(p, 24, GREY_)) for n, l, p, c in rows))
        for col_i, x in enumerate((-4.2, 0.4, 4.4)):
            for row in table:
                row[col_i].move_to([x, 0, 0])
        for i, row in enumerate(table):
            row.shift(UP * (1.0 - i * 1.0))
        heads = VGroup(*(label(h, 20, GREY_).move_to([x, 2.0, 0])
                         for h, x in zip(("path", "your edge is in", "price"), (-4.2, 0.4, 4.4))))
        rule = Line([-6.0, 1.65, 0], [6.0, 1.65, 0], color=GREY_, stroke_width=1.5)
        nxt = label("Next box: the order book →", 24, BLUE_).to_edge(DOWN, buff=0.6)
        with self.beat("summary") as s:
            others = [m for m in self.mobjects if m is not header]
            self.play(*(FadeOut(m) for m in others), FadeIn(heads), Create(rule), run_time=s * 0.08)
            for row in table:
                self.play(FadeIn(row, shift=UP * 0.2), run_time=s * 0.14)
            self.wait_until_word("Next")
            self.play(Write(nxt), run_time=s * 0.15)
