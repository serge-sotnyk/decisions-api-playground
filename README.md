# Jev × OpenAI Decisions

A small reproducible experiment comparing Ukrainian and English, plain text and synthetic images of text.
A continuation of the [earlier Jev experiment](https://www.linkedin.com/pulse/jev-та-українська-невеличкий-тест-serge-sotnyk-juxhf/).

**Status:** the October 16 follow-up is complete: 480 measurements plus 18 warmups,
all successful, using Jev 1.13, Jev 1.14, and Decisions with the same padded PNGs
and five repetitions. Total usage-based cost: \$0.028282918.
See the [new findings](docs/findings-20261016.md),
[new report](results/published/20261016-main/report.md), and
[current methodology](docs/methodology.md). The [October 9 findings](docs/findings.md)
and [October 9 report](results/published/20261009-main/report.md) remain unchanged.
The responses in `tests/fixtures` are synthetic contract fixtures, not model performance measurements.

## Experiment matrix

| Block | Ukrainian + English | Modes per model | Requests with 5 repetitions |
|---|---|---|---:|
| `original` | Original passage, all 9 questions together | Text; PNG; small PNG | 90 |
| `wording` | Four opening variants, full passage, q1 only | Text | 120 |
| `traps` | Negated action, condition versus fact, corrected information | Text; PNG; small PNG | 270 |

Models: `jev-1.13.0`, `jev-1.14.0`, and OpenAI Decisions `gpt-6-luna`.
A full run contains **480 measured requests + 18 warmups**, yielding 1,200 measured
question attempts. Repetitions reuse fixed examples, not independent tasks.

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
[Decisions tariff](https://developers.openai.com/api/docs/guides/decisions) with `data/pricing-20261016.json`.
The file records the verification date, model, source, and USD per million input tokens.
The recorded base rates are \$0.042 and \$0.10 respectively; output is free.
For regional premiums, provide the applicable rate in a separate file using `--pricing`.

Optionally run only the 18 initial checks and inspect the rough full-run cost forecast:

```sh
uv run --locked decisions-playground run --warmup-only
```

The full experiment performs its own warmup, prints a forecast, and continues with measurements:

```sh
uv run --locked decisions-playground run
```

A separate `--warmup-only` invocation adds 18 calls in a separate run.
Missing usage makes the forecast unknown, not zero. The forecast uses the nine-question baseline
cost as a proxy for each condition; it is neither an exact estimate nor a guaranteed upper bound.

Run selected blocks or providers, or use fewer repetitions for a smoke test:

```sh
uv run --locked decisions-playground run --block original --repeats 3
uv run --locked decisions-playground run --provider jev --block wording
uv run --locked decisions-playground run --provider openai --block traps
```

Options include `--seed` (default 20261016), `--timeout` (30 seconds per network operation),
`--pricing`, and `--output` (a new directory). Existing run directories are never overwritten.
A single-provider run needs only that provider's key. Use `--model jev13`, `--model jev14`, or `--model openai` to select one arm. `--provider jev` selects both Jev versions. Model names can be changed with `JEV13_MODEL`, `JEV14_MODEL`, and `OPENAI_MODEL` in `.env` (the old `JEV_MODEL` is ignored),
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

The original 16 PNGs remain in `assets/images/`; `prepare` derives 16 shared PNGs in `assets/images-padded/` by adding white margins to meet the 280 px minimum without changing text pixels. Noto Sans, its OFL license,
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
