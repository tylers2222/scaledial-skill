# Script style

Narration is heard once, at the speaker's speed. The viewer cannot re-read a sentence. Write for the ear.

## Beats

- A beat is 1 to 4 sentences that go with one visual change. Each beat becomes one audio clip.
- Beat ids are short and stable (`kernel-cost`, not `beat7`). Scenes refer to them by id, and editing text keeps the id.
- Tag each beat with the plan `component` it explains. Intro and summary beats may have none.
- Budget about 150 spoken words per minute. A 6-component video at 60 seconds per segment is about 900 words.

## Sentences

Use about 80% of ASD-STE100. Full strict mode deletes meaning (one published test lost 22 of 47 facts under the strict rules).

- 20 words or fewer per sentence. `explainer validate` warns above 25.
- Active voice. One idea per sentence. No semicolons.
- Keep hedges that carry meaning: "roughly", "on typical hardware", "often". A hedge in the plan's evidence must survive into the narration.
- Use the same name for the same thing every time. If the plan calls it "the receive path", never call it "the ingest layer" later.
- Name the job before the product. "A durable log that many readers can replay" comes before the product name.

## Numbers and terms

- Speak numbers the way a person says them: "about a microsecond", "a million messages a minute". Avoid "1.0 µs".
- Every spoken number must appear in `plan.json` with its evidence. If it is not in the plan, it does not go in the script.
- Acronyms the voice may misread go in `narration.aliases` (for example `"FPGA": "F P G A"`). The script text keeps the written form for captions.
- Word cues in scenes use the **spoken** form, after aliases.

## Things that read well and sound bad

- Lists of more than three items in one sentence.
- Parentheses and slashes. Say "or".
- Symbols (≈, →, %). Write the words.
