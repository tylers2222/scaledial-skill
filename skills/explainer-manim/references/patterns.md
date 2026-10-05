# Visual patterns per outcome

These match the segment shapes in the explainer-video teaching template. Each pattern uses the fixed zones in `layout.md`.

## Shared pieces

```python
dial = ScaleDial(["1k/s", "10k/s", "100k/s", "1M/s"]).to_corner(DL, buff=0.6)   # bands from plan
self.play(FadeIn(dial), run_time=s * 0.1)
self.play(dial.to(2), run_time=s * 0.2)          # floats allowed: dial.to(1.5)
```

Band labels come from the component's `options[].band` or `axes`, in the binding axis's units.

## Failure on the binding axis

Make the limit visible in the axis's own terms:

| Binding axis | Visual |
|---|---|
| latency | A horizontal budget line and a bar that grows past it. Bar turns red at the crossing. |
| throughput | A queue of dots in front of the box that grows faster than it drains. |
| data_volume | A fill gauge on the box that reaches the top. |
| fan_out | One arrow multiplying into many. The source box pulses under load. |
| consistency | Two readers showing different values for the same key at the same time. |
| durability | A write that disappears when the box blinks off. |
| team_ops_capacity | A small set of people icons against a growing list of pager alerts or run tasks. |
| cost | A running monthly total next to the box that grows while the useful work stays the same. |
| geography | Distance on a map line with a round-trip timer. |

## substitute_up

1. Simple option in place. Dial at the low band.
2. Dial up. The failure visual appears at the `breaks_when` point.
3. `self.play(swap(old_box, new_box))`. Failure visual resolves. Cost corner updates.
4. Dial back down at the end: dim the big option and show its cost list against the small workload.

## substitute_down

1. Show the given (large) option with its cost list already visible.
2. Dial set to the user's scale, low on the track. Show idle capacity (mostly empty gauge, idle people icons, etc.).
3. `swap` to the smaller option. Show the contract properties still checked.
4. Mark the dial position where moving back up pays off.

## keep

1. Simple option. Dial sweeps the whole user range. The binding-axis visual stays inside its limit the whole way.
2. Show the tempting upgrade as a faded box beside it with its cost list. Cross it out or fade it away.

## split

1. One box with two labelled flows through it (for example reads and writes) in two colors.
2. Dial up. One flow's visual hits its limit while the other does not.
3. Transform the box into two boxes, each taking one flow. Name the new coordination cost under the pair.

## remove

1. The component with its original reason as a small label.
2. Show the path working without it: route the arrow around it.
3. Fade it out. Show what took over its job.
