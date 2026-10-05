# Kokoro (local, free)

- Model: Kokoro-82M, Apache-2.0, run through `kokoro-onnx`. Files live in `~/.cache/explainer-video/` (`kokoro-v1.0.onnx`, about 310 MB, and `voices-v1.0.bin`). `explainer doctor --fetch` downloads them.
- Measured on an M3 Pro CPU: 83 seconds of narration in about 15 seconds.
- Default voice `af_heart` (US English, female). It is the voice the Kokoro voice table grades highest. Other voice names follow the pattern `<lang><gender>_<name>`, for example `am_michael` and `bf_emma`. Set `narration.voice`.
- `narration.speed`: 1.0 is natural. 0.9 to 1.1 stays natural. Outside that range, prosody degrades.
- Language is fixed to `en-us` in the pipeline.
- No word timestamps. The pipeline estimates them. See the narration skill for accuracy.
- No voice cloning.

Arena ranking context (Artificial Analysis speech arena, as reported in October 2026): Kokoro about 1,064 Elo, ElevenLabs v4 about 1,321. Builders who compared both for explainers have published that Kokoro was good enough to ship.
