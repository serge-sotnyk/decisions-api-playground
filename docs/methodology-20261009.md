# Methodology

## Research questions

1. Does Jev still fail on “ледь не запізнився” / “almost late”, and how does Decisions respond?
2. Do controlled wording changes alter the answer?
3. Does correctness persist when Decisions receives the same passage as a PNG, including Ukrainian text?
4. What are the observed HTTP latencies and costs of these specific requests?

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

Both providers receive the same questions, choice descriptions, and a–d ordering.
Jev retains the original `state: {"text": ...}` wrapper; Decisions receives a plain-text `input`.
This is a minimal adaptation to the two API contracts, not identical HTTP request bytes.

Images are sent only to Decisions, as `input_image` with a base64 data URL and `detail=auto`.
There is no text duplicate, OCR step, or hint in `input`. Questions and choices remain text.
Answer keys are never sent to the model or embedded in PNG metadata.

The PNGs are synthetic text renderings, not screenshots of another application. Rendering uses
Noto Sans Regular at 28 px, a 1200 px canvas width, 48 px margins, 40 px line spacing, black text
on white, and an automatically calculated height. Wrapping occurs between words.
The second image is exactly half the width and height, downsampled using Lanczos.
Pillow BASIC layout is used; Pillow, FreeType, and font provenance are recorded in the image manifest.
Committed PNGs and their hashes are the cross-platform reference; changing FreeType may change rasterization.

## Execution

The default run includes eight warmups followed by ten rounds of 48 conditions.
Warmup uses the original passage for each language/mode pair: two Jev requests and six Decisions requests.
Every round contains each selected condition exactly once, shuffled using a local RNG with seed 20261009.
This limits systematic ordering effects.

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
  calibration across providers.
- **Latency:** median, minimum, and maximum for valid responses, excluding warmups and errors.
  Refusals are valid responses. Failed-request durations remain available in requests.csv.
  Blocks and languages are analyzed separately: `original` has nine questions; `wording` and `traps` have one.
- **Cost:** `usage.input_tokens / 1_000_000 × rate`. The recorded base input rate applies to all
  reported input tokens; output is free. Image usage is taken from the provider's usage response.
  Token counts are not assumed equivalent across providers. This is an estimate using published rates,
  excluding taxes, credits, and discounts, not an invoice reconciliation.
- **Per 1,000 requests:** mean request cost within a block/language/mode multiplied by 1,000.
  `wording` is an equal mixture of four formulations; `traps` is an equal mixture of three scenarios.
  If any cost is missing, this aggregate is unknown. Known subtotals and unknown-cost request counts
  are reported separately.

## Limitations

A few scenarios cannot establish overall language proficiency or a universal model winner.
Ten repetitions are not ten independent examples; no p95, confidence intervals, or significance tests are used.
Some original questions quote the passage, so the baseline does not fully isolate image reading;
new questions avoid quoting the answer-bearing sentence.

The English passage is an adaptation: Ukrainian case marking is replaced by a passive construction.
Downsampling changes readability, payload size, and potentially image processing/tokenization.
An incorrect answer alone cannot distinguish a reading failure from a reasoning failure.
Server-side caching, provider load, and network routing are not controlled.

## Sources

- [Original gist](https://gist.github.com/serge-sotnyk/d32cc693d7b4ac2867f851c1dee6440d)
- [TypeSafe API](https://docs.typesafe.ai/api), [models and pricing](https://docs.typesafe.ai/models)
- [Decisions guide](https://developers.openai.com/api/docs/guides/decisions), [Python API reference](https://developers.openai.com/api/reference/python/resources/decisions/methods/create)
- [Noto Sans source](https://github.com/notofonts/noto-fonts); pinned revision and OFL license in `assets/fonts`.
