"""explainer: command-line pipeline for scale-aware explainer videos.

Project layout (one directory per video):
  plan.json      scale plan (scale-planner skill writes it, you approve it)
  script.json    narration beats
  scene.py       Manim scenes built on explainer.manim_kit
  timeline.json  written by `explainer tts`
  out/, qa/      renders and contact sheets
"""

import argparse
import sys
from pathlib import Path

from . import SCHEMA_DIR


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="explainer", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("doctor", help="check dependencies; --fetch downloads the Kokoro voice model")
    s.add_argument("--fetch", action="store_true")

    s = sub.add_parser("new", help="create a video project directory")
    s.add_argument("dir", type=Path)
    s.add_argument("--title", required=True)

    s = sub.add_parser("schema", help="print a JSON schema (plan, script, timeline)")
    s.add_argument("kind", choices=["plan", "script", "timeline"])

    s = sub.add_parser("validate", help="validate plan.json / script.json / timeline.json")
    s.add_argument("files", type=Path, nargs="+")
    s.add_argument("--kind", choices=["plan", "script", "timeline"])

    s = sub.add_parser("tts", help="synthesize narration and write timeline.json")
    s.add_argument("project", type=Path, nargs="?", default=Path("."))

    s = sub.add_parser("render", help="render scene.py with Manim into out/")
    s.add_argument("project", type=Path, nargs="?", default=Path("."))
    s.add_argument("-q", "--quality", choices=["l", "m", "h", "k"], default="l")
    s.add_argument("--scene")

    s = sub.add_parser("qa", help="check audio/video sync and build a contact sheet")
    s.add_argument("project", type=Path, nargs="?", default=Path("."))
    s.add_argument("--video", type=Path)

    s = sub.add_parser("diversity", help="overfitting check over plan files")
    s.add_argument("plans", type=Path, nargs="+")

    s = sub.add_parser("lint-skills", help="lint the skills directory")
    s.add_argument("--root", type=Path)

    sub.add_parser("where", help="print install locations (repo, skills, schemas)")

    a = p.parse_args(argv)

    if a.cmd == "doctor":
        from .scaffold import doctor
        return doctor(a.fetch)
    if a.cmd == "new":
        from .scaffold import new
        new(a.dir, a.title)
        return 0
    if a.cmd == "schema":
        print((SCHEMA_DIR / f"{a.kind}.schema.json").read_text())
        return 0
    if a.cmd == "validate":
        from .validate import validate
        failed = False
        for f in a.files:
            errors, warnings = validate(f, a.kind)
            for w in warnings:
                print(f"{f}: warning: {w}")
            for e in errors:
                print(f"{f}: ERROR: {e}")
            print(f"{f}: {'invalid' if errors else 'valid'}")
            failed |= bool(errors)
        return 1 if failed else 0
    if a.cmd == "tts":
        from .tts import synthesize
        synthesize(a.project.resolve())
        return 0
    if a.cmd == "render":
        from .media import render
        render(a.project.resolve(), a.quality, a.scene)
        return 0
    if a.cmd == "qa":
        from .media import qa
        return qa(a.project.resolve(), a.video)
    if a.cmd == "diversity":
        from .diversity import report
        return report(a.plans)
    if a.cmd == "lint-skills":
        from .lint_skills import default_root, lint
        return lint(a.root or default_root())
    if a.cmd == "where":
        from .lint_skills import default_root
        root = default_root()
        print(f"repo    {root.parent}")
        print(f"skills  {root}")
        print(f"schemas {SCHEMA_DIR}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
