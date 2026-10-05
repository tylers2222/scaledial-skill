---
name: explainer-narration
description: This skill should be used when the user asks to "voice the script", "re-voice a beat", "change the narrator voice", "use ElevenLabs", "use a free local voice", "fix a mispronounced word", "sync animation to a word", or when the explainer-video skill reaches its voice stage. It covers `explainer tts`, providers (Kokoro local, ElevenLabs API), spoken-form aliases, word timing, and caching.
version: 0.1.0
---

# Narration

`explainer tts` turns `script.json` into one WAV per beat under `beats/` and writes `timeline.json`. Scenes read only `timeline.json`, so switching provider never changes scene code.

## Providers

Set `narration.provider` in `script.json`.

| Provider | Cost | Word timing | Needs |
|---|---|---|---|
| `kokoro` (default) | free, local, about 5x faster than real time on an M-series CPU | estimated: clip length spread over words by character count | model files: `explainer doctor --fetch` |
| `elevenlabs` | paid per character | exact, from the API's character alignment | `ELEVEN_API_KEY` in the environment |

Use Kokoro for drafts and for most finished videos. Use ElevenLabs when the user asks for it, when word-exact sync matters, or when a cloned voice is wanted. Details and limits: `references/kokoro.md`, `references/elevenlabs.md`.

## Procedure

1. Check `narration` settings in `script.json`: provider, voice, speed, aliases.
2. Run `explainer tts` in the project directory. It validates the script first.
3. Read the output line: beats synthesized vs cached, and total duration. Total length is about 150 words per minute.
4. Listen-check is not possible for the agent. Instead, check every term in `references/pronunciation.md` that appears in the script, and add aliases for new acronyms before synthesis.

## Spoken form vs written form

- `narration.aliases` maps written text to spoken text, for example `{"SQL": "sequel"}`. Aliases change only the audio. Captions and on-screen text keep the written form.
- For ElevenLabs, a pronunciation dictionary (`narration.pronunciation_dictionaries`, up to 3) is the cleaner choice for phonetic fixes, because the text sent stays unchanged.
- Word cues in scenes (`wait_until_word`, `until_word`) match the **spoken** form.

## Caching and edits

Each beat is cached by a hash of provider, voice settings, and spoken text. Editing one beat re-synthesizes one beat. Changing voice or speed re-synthesizes all. Delete `beats/` to force a full rebuild.

## Word timing quality

- `words_source: elevenlabs` is exact to the API's alignment.
- `words_source: estimated` drifts within a sentence, typically by a few hundred milliseconds, more around numbers and pauses. Use word cues for coarse sync (a box appears when its name is said) and fractional run_time budgets for the rest.

## Additional resources

- `references/kokoro.md`: voices, speed, model files.
- `references/elevenlabs.md`: endpoint, request stitching, dictionaries, pricing, and licence terms.
- `references/pronunciation.md`: terms that need aliases, grown through retros.
