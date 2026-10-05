"""`explainer new` and `explainer doctor`."""

import importlib.util
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from . import CACHE_DIR
from .tts import KOKORO_MODEL, KOKORO_VOICES

KOKORO_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"

SCENE_TEMPLATE = '''"""Scenes for {title}. Labels come from plan.json via self.component(id)."""

from explainer.manim_kit import *


class Video(BeatScene):
    def construct(self):
        header = label("{title}", 22, BLUE_).to_corner(UL, buff=0.4)
        with self.beat("intro") as s:
            self.play(Write(header), run_time=s * 0.3)
'''


def new(target: Path, title: str) -> None:
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"{target} exists and is not empty")
    target.mkdir(parents=True, exist_ok=True)
    (target / "script.json").write_text(json.dumps({
        "title": title,
        "narration": {"provider": "kokoro", "voice": "af_heart", "speed": 1.0, "aliases": {}},
        "beats": [{"id": "intro", "text": f"This video explains {title}."}],
    }, indent=2) + "\n")
    (target / "scene.py").write_text(SCENE_TEMPLATE.format(title=title))
    (target / ".gitignore").write_text("media/\nbeats/\nqa/\nout/\n")
    print(f"created {target}/ with script.json and scene.py")
    print("next: write plan.json (scale-planner skill), then: explainer validate plan.json")


def _download(url: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"downloading {url}")
    with urllib.request.urlopen(url, timeout=600) as resp, open(tmp, "wb") as fh:
        shutil.copyfileobj(resp, fh)
    tmp.rename(dest)


def doctor(fetch: bool) -> int:
    ok = True

    def row(name: str, good: bool, detail: str) -> None:
        nonlocal ok
        ok = ok and good
        print(f"{'ok ' if good else 'BAD'}  {name:<16} {detail}")

    for tool in ("ffmpeg", "ffprobe"):
        path = shutil.which(tool)
        row(tool, bool(path), path or "install with: brew install ffmpeg")
    for lib in ("cairo", "pango"):
        found = subprocess.run(["pkg-config", "--exists", lib], capture_output=True).returncode == 0 \
            if shutil.which("pkg-config") else False
        row(lib, found, "found" if found else f"install with: brew install {lib} pkgconf")
    row("manim", importlib.util.find_spec("manim") is not None, "python package")
    if fetch:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        for f in (KOKORO_MODEL, KOKORO_VOICES):
            if not f.exists():
                _download(KOKORO_BASE + f.name, f)
    have_kokoro = KOKORO_MODEL.exists() and KOKORO_VOICES.exists()
    row("kokoro model", have_kokoro, str(CACHE_DIR) if have_kokoro else "run: explainer doctor --fetch")
    key = os.environ.get("ELEVEN_API_KEY") or os.environ.get("ELEVENLABS_API_KEY")
    print(f"{'ok ' if key else '-- '}  {'elevenlabs key':<16} {'set' if key else 'not set (optional; kokoro is the default)'}")
    return 0 if ok else 1
