---
name: explainer-factcheck
description: This skill should be used when the user asks to "fact check the plan", "is that number right", "source these thresholds", "check the script claims", "where does that limit come from", or when the explainer-video skill reaches its fact-check stage. It checks every crossover point and spoken number in plan.json and script.json against sources, and labels what cannot be sourced.
version: 0.1.0
---

# Fact check

A clean animation makes a wrong claim more convincing, not less. The most dangerous claims in a scale explainer are crossover points ("this option stops working at X"), because they sound precise and depend on hardware, payload, configuration, and team. This skill runs after the plan is approved and before the script is written, and again on the finished script.

## Pass 1: the plan

For every `options[]` entry in `plan.json`:

1. **Read the claim.** `breaks_when`, any number in `why` or `cost`, and the `band`.
2. **Find a source.** Prefer, in order: official documentation, a benchmark that states its hardware and payload, a paper, an engineering blog by the operator of a real system. Avoid unsourced listicles and vendor marketing pages that give no conditions.
3. **Compare conditions.** A source that measured 100-byte messages on a 32-core server does not support a claim about 10 KB messages on a small cloud instance. Write the conditions into `evidence.conditions`.
4. **Label it.**
   - `source` + `ref`: the source supports the claim under stated conditions.
   - `rule_of_thumb` + `conditions`: practitioners agree on an order of magnitude, but no single source fits. Narration must hedge ("roughly", "on typical hardware").
   - `unverified`: nothing found. Remove the number from the band, or keep it only if the user accepts the label.
5. **Fix the plan, not the script.** Corrections go into `plan.json`. The script is regenerated from it.

Run `explainer validate plan.json`. It warns for every `unverified` option.

## Pass 2: the script

After `script.json` exists:

1. List every number, comparison, and absolute word ("always", "never", "only") in the narration.
2. Each one must trace to a plan field. A number that is not in the plan is removed or added to the plan with evidence.
3. Each hedge in the plan's evidence must survive into the narration. "About a microsecond" must not become "one microsecond".
4. Check that product claims are current: features, defaults, and deprecations change. When the source is more than about two years old, look for a newer one.

## Reporting

When delivering, list every claim still labelled `rule_of_thumb` or `unverified`, each with its conditions. The user decides whether the video ships with them.

## What this cannot do

It cannot prove a crossover point for the user's own workload. Only a benchmark on their hardware does that. Say so when a decision depends on a number near a band edge.
