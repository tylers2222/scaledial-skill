"""Schema validation plus the cross-field checks JSON Schema cannot express."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from . import SCHEMA_DIR

KINDS = ("plan", "script", "timeline")


def detect_kind(path: Path) -> str:
    name = path.name
    for kind in KINDS:
        if name == f"{kind}.json" or name.endswith(f".{kind}.json"):
            return kind
    raise ValueError(f"cannot tell schema from file name {name!r}; pass --kind")


def schema(kind: str) -> dict:
    return json.loads((SCHEMA_DIR / f"{kind}.schema.json").read_text())


def validate(path: Path, kind: str | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    kind = kind or detect_kind(path)
    data = json.loads(path.read_text())
    errors = [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(Draft202012Validator(schema(kind)).iter_errors(data), key=lambda e: list(e.absolute_path))
    ]
    if errors:
        return errors, []
    warnings: list[str] = []
    if kind == "plan":
        _check_plan(data, errors, warnings)
    elif kind == "script":
        _check_script(data, path, errors, warnings)
    return errors, warnings


def _check_plan(plan: dict, errors: list[str], warnings: list[str]) -> None:
    ids = [c["id"] for c in plan["components"]]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"duplicate component ids: {sorted(dupes)}")
    missing = set(ids) - set(plan["order"])
    unknown = set(plan["order"]) - set(ids)
    if missing:
        errors.append(f"order is missing components: {sorted(missing)}")
    if unknown:
        errors.append(f"order names unknown components: {sorted(unknown)}")
    for c in plan["components"]:
        where = f"components/{c['id']}"
        axis_names = [a["name"] for a in c["axes"]]
        if c["binding_axis"] not in axis_names:
            errors.append(f"{where}: binding_axis {c['binding_axis']!r} is not in axes {axis_names}")
        if c["outcome"] == "keep" and any(o["breaks_when"] for o in c["options"]):
            warnings.append(f"{where}: outcome is keep but an option has breaks_when; is the outcome right?")
        if c["outcome"] in ("substitute_up", "substitute_down", "split") and len(c["options"]) < 2:
            errors.append(f"{where}: outcome {c['outcome']} needs at least 2 options")
        for i, o in enumerate(c["options"]):
            if o["evidence"]["kind"] == "unverified":
                warnings.append(f"{where}/options/{i}: evidence is unverified ({o['pick']}); fact-check before scripting")


def _check_script(script: dict, path: Path, errors: list[str], warnings: list[str]) -> None:
    ids = [b["id"] for b in script["beats"]]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"duplicate beat ids: {sorted(dupes)}")
    plan_path = path.with_name("plan.json")
    if plan_path.exists():
        components = {c["id"] for c in json.loads(plan_path.read_text())["components"]}
        for b in script["beats"]:
            if "component" in b and b["component"] not in components:
                errors.append(f"beat {b['id']}: component {b['component']!r} is not in plan.json")
    for b in script["beats"]:
        for sentence in _sentences(b["text"]):
            words = len(sentence.split())
            if words > 25:
                warnings.append(f"beat {b['id']}: sentence has {words} words (style limit 20-25): {sentence[:60]}...")


def _sentences(text: str) -> list[str]:
    out, cur = [], []
    for token in text.split():
        cur.append(token)
        if token.endswith((".", "?", "!")):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out
