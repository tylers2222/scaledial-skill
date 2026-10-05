# Planner evals

Fixed design briefs from different domains. They exist to catch the planner overfitting to recent topics or to the skill's own examples.

## Run

1. In a fresh agent session, for each brief in `designs/`, ask: "Use the scale-planner skill to plan this design. Write plan.json only." Save each result as `runs/<short-commit>/<brief-name>.plan.json`.
2. Validate and compare:

```
explainer validate runs/<short-commit>/*.plan.json
explainer diversity runs/<short-commit>/*.plan.json
```

3. Compare with the previous run. A new flag, or a shift toward one binding axis, outcome, or pick after a skill edit, is a regression to investigate.

## What each brief is designed to test

| Brief | The trap | A good plan |
|---|---|---|
| `trading-system.md` | Treating every component as latency-critical | Only the hot path binds on latency; audit and reporting bind on other axes |
| `bank-ledger.md` | Upgrading to a distributed database for "scale" | Keeps one strongly consistent store in range |
| `photo-app.md` | One storage system for everything | Splits upload storage from delivery |
| `b2b-saas.md` | Ignoring tenancy and compliance | Isolation binds for some components |
| `ml-inference.md` | Planning by request rate only | Cost and accelerator capacity bind |
| `offline-mobile.md` | Server-centric thinking | Sync and conflict handling dominate |
| `internal-tool.md` | Adding components because they exist | Mostly keep, some remove or substitute down |
