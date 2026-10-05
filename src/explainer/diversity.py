"""Overfitting check over one or more plan.json files.

Flags the patterns that show the planner copying a template instead of reading
the input: one binding axis everywhere, one outcome everywhere, a fixed number
of options, and the same pick showing up across unrelated designs.
"""

import json
from collections import Counter
from pathlib import Path

AXIS_SHARE_LIMIT = 0.4


def report(paths: list[Path]) -> int:
    plans = [(p, json.loads(p.read_text())) for p in paths]
    comps = [(p, c) for p, plan in plans for c in plan["components"]]
    n = len(comps)
    flags: list[str] = []

    axes = Counter(c["binding_axis"] for _, c in comps)
    outcomes = Counter(c["outcome"] for _, c in comps)
    tiers = Counter(len(c["options"]) for _, c in comps)
    uncatalogued = sum(1 for _, c in comps if c["catalog"] == "uncatalogued")

    print(f"{len(plans)} plan(s), {n} component(s)")
    print("binding axes:  " + ", ".join(f"{k}={v}" for k, v in axes.most_common()))
    print("outcomes:      " + ", ".join(f"{k}={v}" for k, v in outcomes.most_common()))
    print("option counts: " + ", ".join(f"{k}={v}" for k, v in sorted(tiers.items())))
    print(f"uncatalogued:  {uncatalogued}/{n}")

    top_axis, top_count = axes.most_common(1)[0]
    if n >= 5 and top_count / n > AXIS_SHARE_LIMIT:
        flags.append(f"binding axis {top_axis!r} decides {top_count}/{n} components (> {AXIS_SHARE_LIMIT:.0%}). "
                     "Re-check whether it is really the axis that forces each choice.")
    if n >= 4 and len(outcomes) == 1:
        flags.append(f"every component has outcome {next(iter(outcomes))!r}.")
    if n >= 4 and not ({"keep", "substitute_down"} & outcomes.keys()):
        flags.append("no component is keep or substitute_down. Most real designs have parts that should stay simple.")
    if n >= 4 and len(tiers) == 1:
        flags.append(f"every component has exactly {next(iter(tiers))} options. Use the number each component needs.")
    if len(plans) >= 3:
        picks: Counter[str] = Counter()
        for _, plan in plans:
            picks.update({o["pick"].strip().lower() for c in plan["components"] for o in c["options"]})
        common = [pick for pick, k in picks.items() if k / len(plans) >= 0.5]
        if common:
            flags.append(f"these picks appear in at least half of unrelated plans: {common}")

    for f in flags:
        print(f"FLAG: {f}")
    if not flags:
        print("no overfitting flags")
    return 1 if flags else 0
