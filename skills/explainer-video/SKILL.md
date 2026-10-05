---
name: explainer-video
description: This skill should be used when the user asks to "make an explainer video", "explain this design as a video", "create a 3b1b style video", "walk me through this architecture at different scales", "turn this system design into a video", "narrated animation of X", or "run a video retro". It runs the full pipeline: scale plan, approval checkpoint, fact check, narration script, voice, Manim animation, and visual QA, using the `explainer` CLI.
version: 0.1.0
---

# Explainer video pipeline

Turn a system design, document, or topic into a narrated, animated explainer. The core of every video is a **scale plan**: for each component, the job it does, the axis that forces the choice, and the scale bands where a smaller or larger option is correct. The video renders that plan. Pixels are cheap. A wrong plan is expensive, so the plan gets a human checkpoint before anything is voiced or rendered.

The `explainer` CLI is on PATH. Run `explainer --help` for commands and `explainer doctor` if anything fails to run.

## Stage order

Run the stages in this order. Do not skip the checkpoint.

1. **Intake.** Collect the input (design doc, diagram, topic), the audience and what they already know, and the scale range to cover. If the user gives a scale range, use it. If not, propose one in the workload's own units and say so.
2. **Project.** Run `explainer new <dir> --title "<title>"`. All later files live in that directory.
3. **Plan.** Load the `scale-planner` skill and write `plan.json`. Run `explainer validate plan.json` and `explainer diversity plan.json`.
4. **Checkpoint.** Show the user a compact table: component, job, binding axis, outcome, options per band. Ask for approval or edits. Edit `plan.json` until approved. Nothing below this line starts before approval.
5. **Fact check.** Load the `explainer-factcheck` skill. Every `breaks_when` and every number that will be spoken needs evidence or an honest label.
6. **Script.** Write `script.json` from the approved plan, following `references/teaching-template.md` and `references/script-style.md`. Tag each beat with its `component` id. Run `explainer validate script.json`.
7. **Voice.** Load the `explainer-narration` skill. Run `explainer tts`.
8. **Scenes.** Load the `explainer-manim` skill. Write `scene.py`, run `explainer render -q l`, then `explainer qa`.
9. **Review.** Read `qa/sheet.png` and fix every problem in `references/qa.md`. Repeat render and QA until clean, then `explainer render -q h`.
10. **Deliver.** Give the path in `out/`, the duration, the plan table, and every claim still labelled rule of thumb or unverified.
11. **Retro.** When the user reports a problem or asks for a retro, follow `references/retro.md`.

## Rules that apply to every stage

- **The plan is the source of truth.** Script, scenes, and on-screen labels come from `plan.json`. When the user corrects something, correct the plan first, then regenerate the script beats and scenes that depend on it.
- **Read the input, not the examples.** Components come from the user's design. Skill examples and catalogs show format and supply facts. They never decide what the video covers.
- **Visuals follow the narration.** The voice is written first. Animation timing comes from `timeline.json`. Never retime audio to fit an animation.
- **Every on-screen claim must match the narration and the plan.** A label that reads differently from what the voice says is a bug, even when both are true.
- **Cost of change.** Editing one beat re-voices one beat (beats are cached by text). Editing the plan can invalidate many beats. Prefer to catch problems at the checkpoint.

## Output formats other than video

The plan stands alone. If the user wants a table, a diagram, or an HTML page instead of a video, stop after step 5 and render the plan in that format.

## Additional resources

- `references/teaching-template.md`: segment structure per component, one shape per outcome.
- `references/script-style.md`: beat and sentence rules for narration.
- `references/qa.md`: what to look for in the contact sheet, and known failure types.
- `references/retro.md`: where each kind of lesson gets written, and the overfitting checks to run after edits.
