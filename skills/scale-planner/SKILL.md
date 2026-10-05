---
name: scale-planner
description: This skill should be used when the user asks "is X overkill for us", "what should we use at this scale", "what would this look like at 10x or 1000x", "plan this design for a small team", "which parts of this architecture do we actually need", "scale substitution", or when the explainer-video skill reaches its plan stage. It reads a system design and writes plan.json: per component, the job, the contract, the binding axis, the outcome, and the option per scale band, with evidence.
version: 0.1.0
---

# Scale planner

Decide, per component of a design, which option is correct at each scale band, and why. The output is `plan.json` (schema: `explainer schema plan`). It is useful on its own as a table, and it is the source of truth for the explainer video.

## The main risk: copying a template

A planner that has seen one example tends to produce that example again: the same component types, the same three bands, the same upgrade path, the same axis. The method below is ordered to prevent that. Follow the order.

## Method

1. **List components from the input only.** Read the user's design and write down every component it contains, in the user's words. Do this before opening any catalog file or example. Record this list. It becomes `components` and `order`. Do not add components the input does not have, except to name a missing one the contract requires (and say that it is missing).
2. **Write the job.** For each component, one sentence that says what it must do, with no product names.
3. **Write the contract.** The properties any substitute must keep: ordering, durability, consistency, latency budget, isolation, recovery time, and so on. A smaller option that breaks the contract is not a valid substitute, however much cheaper it is.
4. **Measure the axes.** Fill `axes` with every axis that could matter, using values from the input in the workload's own units. Load `references/axes.md` for the list and for how to estimate missing values. Write the assumption when the input gives no value.
5. **Find the binding axis.** Pick the one axis that actually forces the choice in the user's range. Name it even when it is surprising. Volume is often not the binding axis. Replay needs, team size, compliance, or geography often are.
6. **Pick the outcome.** One of `keep`, `substitute_up`, `substitute_down`, `split`, `remove`. Load `references/outcomes.md` for when each applies. `keep` is a strong answer, not a failure to find an upgrade.
7. **Fill the options.** One option per band that the component needs, and no more. One option is normal for `keep`. For each option: why it fits, what it costs, and the condition on the binding axis where it stops meeting the contract.
8. **Look up facts.** Now open the catalog file for the component's area, if one exists, under `references/crossovers/`. Use it for bands, costs, traps, and sources. If no file fits, set `catalog` to `uncatalogued` and work from the method. That is normal.
9. **Label evidence.** Each option gets `source` (with a URL), `rule_of_thumb` (with the conditions behind it), or `unverified`. Never invent a number to fill a band.
10. **Write the teaching moment.** One sentence: the insight this component teaches. If it reads like a generic fact, the component may not deserve its own segment.
11. **Check the plan against itself.** Run `explainer validate plan.json` and `explainer diversity plan.json`. If every component shares one binding axis or one outcome, re-check each one against the input before accepting it.

## Using examples and catalogs

- `examples/*.plan.json` show the format and the level of detail. They come from deliberately different domains. Do not reuse their components, bands, or picks unless the user's input independently calls for them.
- `references/crossovers/*.md` are fact sheets. They answer "where does this option stop working, and what is the source". They do not answer "what should this video talk about".

## Presenting the plan

Show a compact table before anything else uses the plan: component, job, binding axis, outcome, and one cell per band. Under it, list every option whose evidence is `rule_of_thumb` or `unverified`. Ask the user to approve or correct. Their corrections go into `plan.json` first.

## Additional resources

- `references/axes.md`: the axis list, units, and estimation methods.
- `references/outcomes.md`: how to choose an outcome, with failure signs for each.
- `references/crossovers/`: one fact sheet per area (`latency-path.md`, `consistency.md`, `platform-ops.md`, `storage-delivery.md`). Add an area when a retro needs one.
- `examples/`: finished plans with different binding axes and outcomes.
