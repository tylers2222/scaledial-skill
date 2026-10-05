# ElevenLabs

Status in this repository: implemented from the API documentation. Run one beat and check the result before the first full video with a new key.

## Setup

- Export `ELEVEN_API_KEY` (or `ELEVENLABS_API_KEY`).
- In `script.json`: `"narration": {"provider": "elevenlabs", "voice": "<voice_id>", "model_id": "eleven_multilingual_v2"}`. List voice ids with `GET https://api.elevenlabs.io/v1/voices`.

## What the pipeline sends

`POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128`
(docs: https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps)

- Body: `text`, `model_id`, `voice_settings.speed`, optional `pronunciation_dictionary_locators`, and `previous_request_ids`.
- Response: `audio_base64` plus `alignment` with per-character start and end times. The pipeline groups characters into words for `timeline.json`.
- Audio arrives as MP3 and is converted to WAV with ffmpeg. MP3 at 44.1 kHz/128 kbps works on any tier. WAV and PCM at 44.1 kHz need the Pro tier.

## Request stitching

Each beat is a separate request, so prosody can reset between beats. The pipeline passes the request ids of up to 3 earlier beats as `previous_request_ids` so the voice continues naturally. Request ids are stored in each beat's sidecar JSON, so cached beats still chain.

The docs state that stitching is not available for `eleven_v3`. The pipeline skips it for model ids that start with `eleven_v3`.
(docs: https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/request-stitching)

## Pronunciation dictionaries

`.pls` files with alias rules (replace text) or phoneme rules (IPA). Phoneme rules work only with eleven_v4, eleven_v3, and eleven_flash_v2 per the docs. Upload once in the ElevenLabs dashboard or API, then reference by id and version in `narration.pronunciation_dictionaries` (up to 3).

## Cost and licence (check current pricing before quoting it)

- Published API rates in 2026 were about $0.05 to $0.10 per 1,000 characters depending on model. Narration runs about 900 characters per spoken minute, so a 10-minute video is roughly $0.50 to $1.00.
- Free-tier output is non-commercial and must credit ElevenLabs. Published videos need a paid plan.

## Other capabilities not wired into the pipeline

Voice cloning (use the cloned voice id as `voice`), seeded generation, sound effects, and dubbing.
