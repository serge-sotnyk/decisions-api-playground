# Methodology — October 16, 2026 follow-up

## Research questions

1. Does Jev 1.14 improve over Jev 1.13 on the same Ukrainian and English examples? Does Jev still fail on “ледь не запізнився” / “almost late”, and how does Decisions respond?
2. Do controlled wording changes alter the answer?
3. Does correctness persist when each of the three models receives the same passage as a PNG, including Ukrainian text?
4. What are the observed HTTP latencies and costs of these specific requests?

The October 9 methodology is archived in [methodology-20261009.md](methodology-20261009.md). Its results in `results/published/20261009-main/` and original images in `assets/images/` remain unchanged. This follow-up was specified before new API calls. Inputs and answer keys are identical to the first experiment.

## Fixed inputs

`original`: two language adaptations, nine questions each; all nine questions share one request.
`wording`: four openings per language; the rest of the passage is unchanged, and only q1 is sent.
The “almost” variant intentionally repeats the baseline passage with a different question set;
it is analyzed separately from `original`.
`traps`: three new short scenarios per language, each with one question and four choices.

New examples are in `data/traps.json`; their keys are in `data/trap_answers.json`.
Original passages, questions, answer keys, and opening variants are extracted from immutable gist Markdown files.
Every run stores the complete dataset snapshot and its SHA-256. Do not edit the corpus after inspecting
responses for the same experiment; a changed corpus constitutes a new experiment.

The previous 8/9 results are historical observations retained in the source files only.
The original `jev-latest` version was not recorded; we do not assume it was `jev-1.13.0`.

## API inputs and images

Three separately identified model arms are used: `jev13` = `jev-1.13.0`, `jev14` =
`jev-1.14.0`, and `openai` = Decisions `gpt-6-luna`. Requested and returned IDs are
recorded; a mismatch stops the run. Jev aliases are not used. The same TypeSafe API
key serves both Jev versions. The legacy `JEV_MODEL` environment setting is not used
by this matrix; explicit overrides are `JEV13_MODEL` and `JEV14_MODEL`.

All models receive the same questions, choice descriptions, and a–d ordering.
Jev text retains `state: {"text": ...}`; Decisions receives plain-text `input`.
Jev images use a UUID reference in `state.text`, a top-level `assets` entry with
`type=image`, `format=png`, and raw `data_base64`, plus
`TypeSafe-Danger-Zone-Images: true`. The asset is referenced exactly once.
Decisions uses an `input_image` base64 data URL with `detail=auto`.
Both use JSON/base64 over the same HTTP client; the upload time is included.
There is no OCR, source-text duplicate, answer key, or extra hint in image input.
Questions and choices remain textual. Image support in Jev is experimental.

### Shared padded images

The 16 original PNG files and their manifest stay in `assets/images/`.
`prepare` verifies their hashes and creates 16 provider-independent files in
`assets/images-padded/`. It adds centered white padding until both dimensions are
at least 280 px (Jev's documented minimum), with no resizing or rerendering.
Fourteen images gain vertical padding; the full-size original passages are unchanged
in dimensions. All resulting dimensions are at most 1568 px.

The original full-size text was rendered at width 1200 px, font 28 px, margins 48 px,
line height 40 px, with pinned Noto Sans and Pillow BASIC layout. The small source
was downsampled 50% with Lanczos *before* padding. Consequently the letters retain
half size but the padded canvas height need not be half the full canvas height.
The exact same PNG bytes are sent to all three models. Source hashes, dimensions,
padding offsets, output hashes, and Pillow version are stored in the new manifest.
Tests verify unchanged source pixels and white added margins. Visual checks cover
all 16 outputs. The image experiments still concern synthetic rendered text only.

Padding can change tokenization and model behavior. Compare image conditions within
this new run; do not attribute differences from the October 9 unpadded images solely
to a model update. Old results remain a separately labeled historical observation.

## Execution

The default run has **18 warmups + 480 measured requests**, with five repetitions:

| Block | Calculation | Measured requests |
|---|---|---:|
| original | 2 languages × 3 models × 3 inputs × 5 repeats | 90 |
| wording | 2 languages × 3 models × 4 formulations × 5 repeats | 120 |
| traps | 2 languages × 3 models × 3 inputs × 3 examples × 5 repeats | 270 |

Warmups use the original passage once per language/model/input combination. They
verify the API shape, image support and usage, and supply a rough cost forecast.
The run proceeds to measurements after all warmups succeed. Each of five rounds
contains all 96 measured conditions exactly once, shuffled with seed 20261016.
There are 1,200 measured question attempts. Five repeats give less stable latency
estimates than the original ten; sample counts remain visible.

Requests are sequential. One synchronous httpx client reuses connections to both services over HTTP/1.1,
with a 60-second keepalive, no retries, and no redirects. There are no background requests,
local response caches, or environment proxies. The network timeout is 30 seconds per operation,
not an overall deadline for the experiment.

JSON serialization, PNG reading/encoding, and request construction happen before timing.
`perf_counter_ns` covers HTTP transmission and the complete response download; JSON parsing
and disk writes happen afterward. Timing includes network effects, possible connection establishment,
and image upload, so it is not pure inference time.

HTTP 400/401/403/404/405/422 and response schema failures stop the run after the error is recorded.
429, 5xx, and transport failures are recorded without automatic retries.
An unsuccessful warmup prevents measurements from starting. Refusals remain separate outcomes.
Missing usage is unknown, not zero, and does not invalidate an otherwise valid answer.
Ctrl+C retains completed records and marks the run interrupted. An unfinished HTTP request might
still be billed by the provider even if its response was never received.

## Calculations

- **Correct / all question attempts:** correct choice answers divided by the number of questions
  in requests that were actually attempted. Refusals and errors remain in the denominator.
  Unexecuted requests in an interrupted run are listed separately and are not counted as model errors.
- **Accuracy among answers:** `accuracy_answered` excludes refusals and errors. Always interpret it
  alongside their counts so availability problems are not hidden.
- **Stability:** a/b/c/d counts and distinct choices for each question across repetitions.
  Confidence and full probability distributions are retained in JSONL without assuming equivalent
  calibration across models. Confidence summaries separate the two Jev versions. No decision
  threshold is fitted to these diagnostic examples.
- **Latency:** median, minimum, and maximum for valid responses, excluding warmups and errors.
  Refusals are valid responses. Failed-request durations remain available in requests.csv.
  Blocks and languages are analyzed separately: `original` has nine questions; `wording` and `traps` have one.
- **Cost:** `usage.input_tokens / 1_000_000 × rate`. Tariffs were checked on October 16 and frozen in `data/pricing-20261016.json`: Jev 1.13 and 1.14 are both USD 0.042/M input tokens; Decisions is USD 0.10/M. The recorded base input rate applies to all
  reported input tokens; output is free. Image usage is taken from the provider's usage response.
  Token counts are not assumed equivalent across providers. This is an estimate using published rates,
  excluding taxes, credits, and discounts, not an invoice reconciliation.
- **Per 1,000 requests:** mean request cost within a block/language/mode multiplied by 1,000.
  `wording` is an equal mixture of four formulations; `traps` is an equal mixture of three scenarios.
  If any cost is missing, this aggregate is unknown. Known subtotals and unknown-cost request counts
  are reported separately.

## Limitations

A few scenarios cannot establish overall language proficiency or a universal model winner.
Repeated requests are not independent examples; no p95, confidence intervals, or significance tests are used.
Some original questions quote the passage, so the baseline does not fully isolate image reading;
new questions avoid quoting the answer-bearing sentence.

The English passage is an adaptation: Ukrainian case marking is replaced by a passive construction.
Downsampling changes readability, payload size, and potentially image processing/tokenization.
An incorrect answer alone cannot distinguish a reading failure from a reasoning failure.
Server-side caching, provider load, and network routing are not controlled. The new Jev image
interface and limits are experimental. No Box questions, long-context flags or new examples
are added to this follow-up.

## Sources

- [Original gist](https://gist.github.com/serge-sotnyk/d32cc693d7b4ac2867f851c1dee6440d)
- [TypeSafe API](https://docs.typesafe.ai/api), [models and pricing](https://docs.typesafe.ai/models)
- [Decisions guide](https://developers.openai.com/api/docs/guides/decisions), [Python API reference](https://developers.openai.com/api/reference/python/resources/decisions/methods/create)
- [Noto Sans source](https://github.com/notofonts/noto-fonts); pinned revision and OFL license in `assets/fonts`.

- [Jev 1.14 release](https://typesafe.ai/blog/jev-1-14), [image input and limits](https://docs.typesafe.ai/images)
