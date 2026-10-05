# explainer-video

Agent skills plus a CLI that turn a system design into a narrated, animated explainer that is honest about scale: for each component, what job it does, which axis forces the choice, and where a smaller or larger option is the right one.

```
design doc ─▶ scale plan ─▶ you approve ─▶ fact check ─▶ script ─▶ voice ─▶ Manim scenes ─▶ QA ─▶ mp4
             (plan.json)                               (script.json) (timeline.json)
```

## Install

```bash
git clone https://github.com/tylers2222/explainer-video && cd explainer-video
./install.sh            # CLI on PATH (editable), skills linked, voice model fetched
explainer doctor        # check ffmpeg, cairo, pango, manim, voice model, optional ElevenLabs key
```

Needs macOS or Linux with `uv`, `ffmpeg`, `cairo`, `pango`, and `pkgconf` (macOS: `brew install uv ffmpeg cairo pango pkgconf`).

`install.sh` links each `skills/<name>` into `~/.agents/skills/` and `~/.claude/skills/`, so any agent session in any directory can load them. The CLI is an editable install, so edits in this repo take effect immediately. `./install.sh --uninstall` removes both.

## Use

In any directory, ask your agent: *"Make an explainer video of this design: <doc>. Cover 1k to 1M users."* The `explainer-video` skill runs the stages and stops at the plan for your approval.

By hand:

```bash
explainer new my-video --title "Event pipeline at three scales"
cd my-video
# write plan.json (scale-planner skill), then:
explainer validate plan.json && explainer diversity plan.json
# write script.json and scene.py, then:
explainer tts              # Kokoro locally; set provider "elevenlabs" + ELEVEN_API_KEY to switch
explainer render -q l      # fast draft
explainer qa               # sync check + qa/sheet.png contact sheet
explainer render -q h      # 1080p60 into out/
```

Worked example: `skills/explainer-manim/examples/box1_market_data/`.

## Layout

| Path | What |
|---|---|
| `skills/explainer-video/` | Entry skill: stage order, checkpoint, teaching template, script style, QA, retro |
| `skills/scale-planner/` | The core: component → job → contract → axes → binding axis → outcome → options. Catalogs in `references/crossovers/`, example plans in `examples/` |
| `skills/explainer-narration/` | Voice providers, aliases, word timing, pronunciation list |
| `skills/explainer-manim/` | Scene kit usage, layout zones, per-outcome visual patterns, gotchas |
| `skills/explainer-factcheck/` | Evidence rules for crossover points and spoken numbers |
| `src/explainer/` | CLI, schemas, `manim_kit`, linters |
| `evals/` | Fixed design briefs from different domains for overfitting checks |

## Keeping the skills honest

- `explainer lint-skills`: SKILL.md files stay short, product-free, and correctly linked. Product names belong in catalogs and examples, not in the method.
- `explainer diversity <plans>`: flags plans that all share one binding axis, one outcome, a fixed number of options, or the same picks.
- After each video, the retro process (`skills/explainer-video/references/retro.md`) files each lesson in exactly one place.
