"""Render a project's scene.py with Manim, then QA the result."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

QUALITY = {"l": ("-ql", "480p15"), "m": ("-qm", "720p30"), "h": ("-qh", "1080p60"), "k": ("-qk", "2160p60")}


def scene_names(scene_file: Path) -> list[str]:
    import ast

    tree = ast.parse(scene_file.read_text())
    return [n.name for n in tree.body if isinstance(n, ast.ClassDef)
            and any(getattr(b, "id", "").endswith("Scene") for b in n.bases)]


def render(project: Path, quality: str, scene: str | None) -> Path:
    scene_file = project / "scene.py"
    if not (project / "timeline.json").exists():
        raise SystemExit("timeline.json missing. Run: explainer tts")
    names = [scene] if scene else scene_names(scene_file)
    if len(names) != 1:
        raise SystemExit(f"scene.py defines {names}; pass --scene NAME")
    flag, folder = QUALITY[quality]
    cmd = [sys.executable, "-m", "manim", flag, "--disable_caching", "scene.py", names[0]]
    proc = subprocess.run(cmd, cwd=project, capture_output=True, text=True)
    overruns = [line.strip() for line in (proc.stdout + proc.stderr).splitlines() if "WARNING beat" in line]
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout[-3000:] + proc.stderr[-3000:])
        raise SystemExit(f"manim failed (exit {proc.returncode})")
    src = project / "media" / "videos" / "scene" / folder / f"{names[0]}.mp4"
    out = project / "out"
    out.mkdir(exist_ok=True)
    dest = out / f"{names[0]}-{folder}.mp4"
    shutil.copy2(src, dest)
    for line in overruns:
        print(line)
    print(dest)
    return dest


def latest_video(project: Path) -> Path:
    videos = sorted((project / "out").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not videos:
        raise SystemExit("no video in out/. Run: explainer render")
    return videos[-1]


def probe(video: Path) -> dict[str, float]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout
    return {s["codec_type"]: float(s.get("duration", 0)) for s in json.loads(out)["streams"]}


def qa(project: Path, video: Path | None) -> int:
    video = video or latest_video(project)
    timeline = json.loads((project / "timeline.json").read_text())
    problems = []
    durations = probe(video)
    if "audio" not in durations:
        problems.append("video has no audio stream")
    else:
        drift = abs(durations["video"] - timeline["total"])
        if drift > 0.5:
            problems.append(f"video is {durations['video']:.2f}s but timeline is {timeline['total']:.2f}s "
                            f"(drift {drift:.2f}s): a beat overran or a scene skipped a beat")
    qa_dir = project / "qa"
    if qa_dir.exists():
        shutil.rmtree(qa_dir)
    qa_dir.mkdir()
    end = durations.get("video", timeline["total"])
    for i, b in enumerate(timeline["beats"]):
        t = min(b["start"] + min(b["slot"] - 0.4, b["audio"]), end - 0.25)
        frame = qa_dir / f"{i:03d}-{b['id']}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=854:-1", str(frame)], check=True)
        if not frame.exists():
            problems.append(f"no frame at {t:.2f}s for beat {b['id']}")
    cols = 3
    rows = -(-len(timeline["beats"]) // cols)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", str(qa_dir / "*.png"),
                    "-vf", f"tile={cols}x{rows}:padding=6:color=white", "-frames:v", "1",
                    str(qa_dir / "sheet.png")], check=True)
    print(f"video {durations.get('video', 0):.2f}s, audio {durations.get('audio', 0):.2f}s, "
          f"timeline {timeline['total']:.2f}s")
    print(f"contact sheet: {qa_dir / 'sheet.png'} (one frame at the end of each beat; read it)")
    for p in problems:
        print(f"PROBLEM: {p}")
    return 1 if problems else 0
