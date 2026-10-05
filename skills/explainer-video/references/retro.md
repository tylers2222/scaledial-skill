# Retro: write each lesson in exactly one place

Run this after a video when the user reports a problem, or when they ask for a retro. The goal is that the next video does not repeat the mistake, and that the skills do not drift toward whatever topic came last.

## 1. Collect

List each problem in one line: what was wrong, in which beat or component, and how it was found (user, QA sheet, fact check).

## 2. Split each lesson into principle and specifics

Most lessons have two parts. Write them in different places.

- **Principle** (no product names): the general rule. Example: "Name the axis that forces the switch. It is often not throughput."
- **Specifics** (product names allowed): the facts behind this instance. Example: "For a replayable event log, replay and retention drove the choice, not message rate."

## 3. File by type

| Lesson type | Principle goes to | Specifics go to |
|---|---|---|
| Wrong component choice or band | `scale-planner` SKILL.md (method steps) | `scale-planner/references/crossovers/<area>.md` |
| Missing or wrong axis | `scale-planner/references/axes.md` | the area catalog |
| Unsupported or wrong number | `explainer-factcheck` SKILL.md | the area catalog, with the source |
| Segment felt repetitive or flat | `references/teaching-template.md` | none |
| Narration hard to follow | `references/script-style.md` | none |
| Mispronounced term | none | `explainer-narration/references/pronunciation.md` |
| Layout, overlap, timing | `explainer-manim/references/layout.md` | `explainer-manim/references/gotchas.md` |
| QA missed it | `references/qa.md` (known failure types) | none |

If an area has no catalog file, create one with the same format as the existing files. Do not put it into an unrelated area's file.

## 4. Check for drift

Run from the skill repository (`explainer where` prints its path):

```
explainer lint-skills
explainer diversity skills/scale-planner/examples/*.plan.json
```

- `lint-skills` fails if a product name reaches a SKILL.md, if a referenced file is missing, or if a SKILL.md grows past its word limit. It warns when a reference file is large enough to split.
- `diversity` flags plans that share one binding axis, one outcome, a fixed option count, or the same picks.

For larger edits to the planner, also re-plan the briefs in `evals/designs/` and run `explainer diversity` over the new plans. Compare with the last run.

## 5. Commit

One commit per retro, message `retro: <video title>: <one-line summary>`. The repository history is then a record of what each video taught the skill.

## Grow or shrink the skill set

- A reference file that gets its own trigger phrases from the user (for example "just re-voice beat 3") may become its own skill.
- A sub-skill that never loads on its own goes back to being a reference of its parent.
- A catalog file above about 5,000 words gets split by job.
