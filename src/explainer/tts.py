"""script.json -> one WAV per beat + timeline.json.

Beats are cached by a hash of everything that changes the audio, so editing one
sentence re-synthesizes only that beat. Each WAV has a JSON sidecar holding word
timings and (for ElevenLabs) the request id used for request stitching.
"""

import base64
import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import soundfile as sf

from . import CACHE_DIR
from .validate import validate

KOKORO_MODEL = CACHE_DIR / "kokoro-v1.0.onnx"
KOKORO_VOICES = CACHE_DIR / "voices-v1.0.bin"
ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps"
DEFAULTS = {
    "kokoro": {"voice": "af_heart", "speed": 1.0},
    "elevenlabs": {"voice": "21m00Tcm4TlvDq8ikWAM", "model_id": "eleven_multilingual_v2", "speed": 1.0},
}


def spoken_text(text: str, aliases: dict[str, str]) -> str:
    for written, spoken in aliases.items():
        text = re.sub(rf"(?<!\w){re.escape(written)}(?!\w)", spoken, text)
    return text


def estimate_words(text: str, duration: float) -> list[dict]:
    """Spread the clip duration over words in proportion to their length."""
    words = text.split()
    weights = [len(w) + 1 for w in words]
    total = sum(weights) or 1
    out, t = [], 0.0
    for w, weight in zip(words, weights):
        span = duration * weight / total
        out.append({"word": w, "start": round(t, 3), "end": round(t + span, 3)})
        t += span
    return out


def words_from_alignment(alignment: dict) -> list[dict]:
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    out, cur, cur_start, cur_end = [], [], 0.0, 0.0
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                out.append({"word": "".join(cur), "start": round(cur_start, 3), "end": round(cur_end, 3)})
                cur = []
            continue
        if not cur:
            cur_start = s
        cur.append(ch)
        cur_end = e
    if cur:
        out.append({"word": "".join(cur), "start": round(cur_start, 3), "end": round(cur_end, 3)})
    return out


class Kokoro:
    def __init__(self, cfg: dict):
        if not KOKORO_MODEL.exists() or not KOKORO_VOICES.exists():
            raise SystemExit(f"Kokoro model files missing in {CACHE_DIR}. Run: explainer doctor --fetch")
        from kokoro_onnx import Kokoro as Engine

        self.engine = Engine(str(KOKORO_MODEL), str(KOKORO_VOICES))
        self.cfg = cfg

    def synth(self, text: str, wav: Path, previous_ids: list[str]) -> dict:
        samples, sr = self.engine.create(text, voice=self.cfg["voice"], speed=self.cfg["speed"], lang="en-us")
        sf.write(wav, samples, sr)
        return {"words_source": "estimated", "words": estimate_words(text, len(samples) / sr), "request_id": None}


class ElevenLabs:
    def __init__(self, cfg: dict):
        self.key = os.environ.get("ELEVEN_API_KEY") or os.environ.get("ELEVENLABS_API_KEY")
        if not self.key:
            raise SystemExit("Set ELEVEN_API_KEY (or ELEVENLABS_API_KEY) to use the elevenlabs provider.")
        self.cfg = cfg
        # The ElevenLabs docs state request stitching is not available for eleven_v3.
        self.stitch = not cfg["model_id"].startswith("eleven_v3")

    def synth(self, text: str, wav: Path, previous_ids: list[str]) -> dict:
        body = {
            "text": text,
            "model_id": self.cfg["model_id"],
            "voice_settings": {"speed": self.cfg["speed"]},
        }
        if self.cfg.get("pronunciation_dictionaries"):
            body["pronunciation_dictionary_locators"] = self.cfg["pronunciation_dictionaries"]
        if self.stitch and previous_ids:
            body["previous_request_ids"] = previous_ids[-3:]
        req = urllib.request.Request(
            ELEVEN_URL.format(voice=self.cfg["voice"]) + "?output_format=mp3_44100_128",
            data=json.dumps(body).encode(),
            headers={"xi-api-key": self.key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                request_id = resp.headers.get("request-id")
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise SystemExit(f"ElevenLabs HTTP {e.code}: {e.read().decode(errors='replace')[:500]}") from e
        with tempfile.NamedTemporaryFile(suffix=".mp3") as mp3:
            mp3.write(base64.b64decode(payload["audio_base64"]))
            mp3.flush()
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp3.name, str(wav)], check=True)
        alignment = payload.get("alignment")
        if alignment:
            words, source = words_from_alignment(alignment), "elevenlabs"
        else:
            info = sf.info(wav)
            words, source = estimate_words(text, info.frames / info.samplerate), "estimated"
        return {"words_source": source, "words": words, "request_id": request_id}


PROVIDERS = {"kokoro": Kokoro, "elevenlabs": ElevenLabs}


def synthesize(project: Path) -> dict:
    script_path = project / "script.json"
    errors, warnings = validate(script_path, "script")
    if errors:
        raise SystemExit("script.json is invalid:\n  " + "\n  ".join(errors))
    for w in warnings:
        print(f"warning: {w}")
    script = json.loads(script_path.read_text())
    narration = script["narration"]
    provider = narration["provider"]
    cfg = {**DEFAULTS[provider], **{k: v for k, v in narration.items() if k not in ("provider", "aliases", "tail_pad")}}
    aliases = narration.get("aliases", {})
    tail_pad = narration.get("tail_pad", 0.35)

    out = project / "beats"
    out.mkdir(exist_ok=True)
    engine = None
    previous_ids: list[str] = []
    beats, t, made = [], 0.0, 0
    for beat in script["beats"]:
        text = spoken_text(beat["text"], aliases)
        key = hashlib.sha256(json.dumps([provider, cfg, text], sort_keys=True).encode()).hexdigest()[:12]
        wav = out / f"{beat['id']}-{key}.wav"
        sidecar = wav.with_suffix(".json")
        if not (wav.exists() and sidecar.exists()):
            engine = engine or PROVIDERS[provider](cfg)
            sidecar.write_text(json.dumps(engine.synth(text, wav, previous_ids)))
            made += 1
        meta = json.loads(sidecar.read_text())
        if meta.get("request_id"):
            previous_ids.append(meta["request_id"])
        info = sf.info(wav)
        audio = info.frames / info.samplerate
        entry = {
            "id": beat["id"],
            "wav": str(wav.resolve()),
            "start": round(t, 3),
            "audio": round(audio, 3),
            "slot": round(audio + tail_pad, 3),
            "words_source": meta["words_source"],
            "words": meta["words"],
        }
        if "component" in beat:
            entry["component"] = beat["component"]
        beats.append(entry)
        t += audio + tail_pad
    timeline = {"total": round(t, 3), "beats": beats}
    (project / "timeline.json").write_text(json.dumps(timeline, indent=2))
    print(f"{len(beats)} beats ({made} synthesized, {len(beats) - made} cached), {t:.1f}s -> timeline.json")
    return timeline
