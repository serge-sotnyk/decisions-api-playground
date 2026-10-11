# Jev × OpenAI Decisions

A small reproducible experiment comparing Ukrainian and English, plain text and synthetic images of text.
A continuation of the [earlier Jev experiment](https://www.linkedin.com/pulse/jev-та-українська-невеличкий-тест-serge-sotnyk-juxhf/).

**Status:** the 2026-10-09 live run is complete: 480 measured requests and 8 warmups, with no API errors or refusals.
Read the [findings](docs/findings.md) and the [full report](results/published/20261009-main/report.md).
Usage-based cost at the recorded tariffs was **$0.025779678**, including warmups.
The responses in `tests/fixtures` are synthetic contract fixtures, not model performance measurements.

## Experiment matrix

| Block | Ukrainian + English | Modes | Requests with 10 repetitions |
|---|---|---|---:|
| `original` | Original passage, all 9 questions together | Jev text; Decisions text; PNG; PNG × 0.5 | 80 |
| `wording` | Four opening variants, full passage, q1 only | Jev text; Decisions text | 160 |
| `traps` | Negated action, condition versus fact, corrected information | All four modes | 240 |

A full run contains **480 measured requests + 8 warmups**, yielding 1,120 measured question attempts.
Repetitions reuse fixed examples; they are not 1,120 independent tasks.
Models: `jev-1.13.0` and OpenAI Decisions `gpt-6-luna`.

## Quick start

Use Python **3.14** and [uv](https://docs.astral.sh/uv/). Run commands from the repository root.
uv can install Python 3.14. `.python-version` pins the minor version; `uv.lock` pins dependencies.
Each run records the actual Python patch version and library versions.

```sh
uv sync --locked
cp .env.example .env
```

Copy the template once, then fill in `TYPESAFE_API_KEY` and `OPENAI_API_KEY` in `.env`.
Existing environment variables take precedence over `.env`. Keys are not needed for preparation,
dry runs, tests, or offline reports.

```sh
uv run --locked decisions-playground prepare
uv run --locked decisions-playground run --dry-run
```

Before a paid run, compare the [Jev tariff](https://docs.typesafe.ai/models) and
[Decisions tariff](https://developers.openai.com/api/docs/guides/decisions) with `data/pricing.json`.
The file records the verification date, model, source, and USD per million input tokens.
The recorded base rates are $0.042 and $0.10 respectively; output is free.
For regional premiums, provide the applicable rate in a separate file using `--pricing`.

Optionally run only the eight initial checks and inspect the rough full-run cost forecast:

```sh
uv run --locked decisions-playground run --warmup-only
```

The full experiment performs its own warmup, prints a forecast, and continues with measurements:

```sh
uv run --locked decisions-playground run
```

A separate `--warmup-only` invocation adds eight calls in a separate run.
Missing usage makes the forecast unknown, not zero. The forecast uses the nine-question baseline
cost as a proxy for each condition; it is neither an exact estimate nor a guaranteed upper bound.

Run selected blocks or providers, or use fewer repetitions for a smoke test:

```sh
uv run --locked decisions-playground run --block original --repeats 3
uv run --locked decisions-playground run --provider jev --block wording
uv run --locked decisions-playground run --provider openai --block traps
```

Options include `--seed` (default 20261009), `--timeout` (30 seconds per network operation),
`--pricing`, and `--output` (a new directory). Existing run directories are never overwritten.
A single-provider run needs only that provider's key. Model names can be changed in `.env`,
but the pricing file must explicitly match the selected models.

## Results and publication

Local runs are saved to the Git-ignored `results/local/<timestamp>/` directory.
A `report` subdirectory is generated after completion or a controlled failure.
After Ctrl+C, completed responses remain saved; rebuild the report separately:

```sh
uv run --locked decisions-playground report results/local/RUN_ID
uv run --locked decisions-playground report results/local/RUN_ID --output results/published/RUN_ID
```

Replace `RUN_ID` with the directory name printed by `run`.
The second command prepares an export for inclusion in the repository; it does not commit or publish anything.
Reports use **the dataset and pricing snapshots stored with the run**, not the current input files.

| File | Purpose |
|---|---|
| `manifest.json` | Dataset, answer keys, schedule, prices, versions, code/lockfile/PNG hashes, and run status |
| `records.jsonl` | Sanitized API responses, normalized answers, usage, latency, and per-request errors |
| `report.md` | English report with tables and limitations |
| `summary.json`, `groups.csv` | Aggregates by block, language, and mode |
| `questions.csv`, `requests.csv` | Per-question stability and individual requests, including failures |
| `accuracy.png`, `latency-cost.png` | Correctness and latency/cost charts |

Authorization headers are never logged. Keys are redacted from responses; images are represented
by their path and SHA-256 rather than inline base64. The current corpus is public; replacing it
with private material would also place that material in the run snapshot.

LinkedIn post drafts stay outside the repository. Draft the follow-up from actual live measurements
and link to the specific published run.

## Reproducibility and methodology

The original Markdown files are preserved unchanged from the
[gist](https://gist.github.com/serge-sotnyk/d32cc693d7b4ac2867f851c1dee6440d),
revision `2cdd6f213390fe86c9c147c4359fedb4ca90f2a0`.
Checksums are verified when loading data. New traps and their separate answer keys were written before live runs.
Model requests never include the answer key or historical results.

All 16 PNGs are included in the repository; `prepare` rebuilds them. Noto Sans, its OFL license,
and pinned provenance are in `assets/fonts`. Image hashes and dataset consistency are checked before runs.
See the [methodology](docs/methodology.md) for details.

Repository documentation is maintained in English. Bilingual experimental data and immutable source
snapshots retain their original languages, as specified in [AGENTS.md](AGENTS.md).

## Checks

```sh
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked ty check
uv run --locked pytest -q
```

Tests require neither network access nor API keys. They cover exact gist reproduction, the matrix,
absence of a text duplicate in image inputs, answer matching by ID, refusals/errors/timeouts,
cost calculations, warmup exclusion, and a full run through MockTransport.
Integration test artifacts are saved only in temporary directories.
