# Layout

Manim's default frame is about 14.2 units wide and 8 units high, centred on the origin. x runs from about -7.1 to 7.1, y from -4 to 4. Keep 0.4 to 0.5 units of margin on every edge.

## Zones

Use the same zones in every scene so the viewer learns where to look.

| Zone | Position | Holds |
|---|---|---|
| Header | top-left corner, `to_corner(UL, buff=0.4)` | Video or segment title, font 22 |
| Band badge | top-right corner, `to_corner(UR, buff=0.4)` | Current band or level, font 24 |
| Meter | under the badge, right-aligned | The binding-axis value for the current option |
| Diagram row | y about 0.3, x from -6.6 to 6.6 | Up to 4 boxes of width 2.2 in a row, centres about 3.3 apart |
| Below-diagram | y from -1.0 to -2.6, under the box it explains | Cost tags, failure tags, a substituted or added box |
| Cost corner | bottom-right, `to_corner(DR, buff=0.5)` | Trade-off list for the current option. Replace it, do not stack it |
| Footer | `to_edge(DOWN, buff=0.45)` | One-line takeaway |
| Dial | bottom-left or bottom-centre, fixed for the whole video | `ScaleDial` |

When a diagram has more than 4 components in a row, use two rows, or a `BeatCameraScene` that zooms to the current component and keeps the rest at low opacity.

## Sizes

| Role | Font size |
|---|---|
| Title card | 44 |
| Box name | 26 |
| Badge, meter | 24 to 26 |
| Body labels, tags | 20 to 22 |
| Box subtitle, dial labels | 16 |

Nothing below 16. At 1080p, 18 and above reads comfortably.

## Placement

- Position relative to other objects (`next_to`, `arrange`, `move_to(other, aligned_edge=...)`) rather than absolute coordinates, so a longer label does not collide with its neighbour.
- When a label replaces another in the same place, build the new one with `move_to(old, aligned_edge=RIGHT)` (or LEFT) so it does not jump.
- Arrows between boxes use `buff=0.1` so tips do not touch the box border.
