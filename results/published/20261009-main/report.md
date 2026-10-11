# Jev × OpenAI Decisions: results

Run status: **complete**. Started: 2026-10-09T12:18:05.464435+00:00 (UTC).
Execution: **live**. mock = synthetic tests, not model results.
Planned measurements: 480; not executed: 0.
Measured requests: 480; warmups: 8.
Dataset hash: `1db58f724d1aa799899f6433598cc9f7f376675ff9fd54ec61fc6b8dee602351`.
Pricing checked: 2026-10-09. Standard direct API input pricing; no regional premium or long-context multiplier. Output is free. Recheck sources before each live run.
Known subtotal for the entire run, including warmup: $0.02577968; requests with unknown cost: 0.

## Correctness and stability

Correct / attempts includes transport errors and refusals in the denominator: it measures successful delivery of a correct answer. The separate accuracy_answered field in JSON/CSV counts only returned choice answers.

| Block | Language | Mode | Correct / attempts | Unique questions | Request errors | Refusals | Questions with changed choices |
|---|---|---|---:|---:|---:|---:|---:|
| original | en | jev-text | 80/90 | 9 | 0 | 0 | 0 |
| original | en | openai-png | 90/90 | 9 | 0 | 0 | 0 |
| original | en | openai-png-small | 80/90 | 9 | 0 | 0 | 0 |
| original | en | openai-text | 90/90 | 9 | 0 | 0 | 0 |
| original | uk | jev-text | 80/90 | 9 | 0 | 0 | 0 |
| original | uk | openai-png | 80/90 | 9 | 0 | 0 | 0 |
| original | uk | openai-png-small | 80/90 | 9 | 0 | 0 | 0 |
| original | uk | openai-text | 80/90 | 9 | 0 | 0 | 0 |
| traps | en | jev-text | 30/30 | 3 | 0 | 0 | 0 |
| traps | en | openai-png | 30/30 | 3 | 0 | 0 | 0 |
| traps | en | openai-png-small | 30/30 | 3 | 0 | 0 | 0 |
| traps | en | openai-text | 30/30 | 3 | 0 | 0 | 0 |
| traps | uk | jev-text | 30/30 | 3 | 0 | 0 | 0 |
| traps | uk | openai-png | 30/30 | 3 | 0 | 0 | 0 |
| traps | uk | openai-png-small | 20/30 | 3 | 0 | 0 | 0 |
| traps | uk | openai-text | 30/30 | 3 | 0 | 0 | 0 |
| wording | en | jev-text | 30/40 | 4 | 0 | 0 | 0 |
| wording | en | openai-text | 40/40 | 4 | 0 | 0 | 0 |
| wording | uk | jev-text | 30/40 | 4 | 0 | 0 | 0 |
| wording | uk | openai-text | 30/40 | 4 | 0 | 0 | 0 |

![Correctness](accuracy.png)

## Probabilities and confidence

Both APIs returned a probability distribution over choices and a separate confidence field. These are API scores, not empirically established probabilities of correctness; equivalent calibration across providers is not assumed. This section includes measured choice answers only, excluding warmups, refusals, and missing answers.

### Incorrect answers

Each row summarizes incorrect attempts for one question and condition. P(selected) is the probability assigned to the chosen incorrect option; P(expected) is the probability assigned to the answer key. Medians are computed separately. A stable choice can still have changing probability values.

| Example | Mode | Question | Incorrect attempts | Median P(selected) | Median P(expected) | Median confidence | Confidence min–max |
|---|---|---|---:|---:|---:|---:|---:|
| almost-en | jev-text | q1 | 10 | 68.5% | 31.5% | 0.580 | 0.480–0.610 |
| almost-uk | jev-text | q1 | 10 | 64.5% | 32.0% | 0.530 | 0.400–0.630 |
| almost-uk | openai-text | q1 | 10 | 94.0% | 4.0% | 0.920 | 0.920–0.920 |
| negation-uk | openai-png-small | q1 | 10 | 88.0% | 6.0% | 0.840 | 0.840–0.840 |
| original-en | jev-text | q1 | 10 | 68.0% | 32.0% | 0.575 | 0.510–0.650 |
| original-en | openai-png-small | q1 | 10 | 50.0% | 38.0% | 0.330 | 0.330–0.330 |
| original-uk | jev-text | q1 | 10 | 65.5% | 31.0% | 0.540 | 0.440–0.640 |
| original-uk | openai-png | q1 | 10 | 60.0% | 32.0% | 0.470 | 0.470–0.470 |
| original-uk | openai-png-small | q4 | 10 | 53.0% | 41.0% | 0.370 | 0.370–0.370 |
| original-uk | openai-text | q1 | 10 | 94.0% | 4.0% | 0.920 | 0.920–0.920 |

### Confidence by outcome

Counts are repeated question attempts, not independent examples. Providers have different workloads, including image modes only for Decisions; these aggregates are descriptive, not a ranking.

| Provider | Outcome | Question attempts | Median confidence | Confidence min–max |
|---|---|---:|---:|---:|
| jev | incorrect | 40 | 0.555 | 0.400–0.650 |
| jev | correct | 280 | 1.000 | 0.800–1.000 |
| openai | incorrect | 60 | 0.655 | 0.330–0.920 |
| openai | correct | 740 | 1.000 | 0.250–1.000 |

Observed interpretation:

- jev: incorrect-answer confidence was 0.400–0.650, versus 0.800–1.000 for correct answers. The ranges are separate in this sample.
- jev: a correct answer with the lowest observed confidence occurred on barely-en / jev-text / q1: confidence 0.800, P(selected) 85.0%. Low confidence does not itself establish an error.
- openai: incorrect-answer confidence was 0.330–0.920, versus 0.250–1.000 for correct answers. The ranges overlap in this sample.
- openai: a correct answer with the lowest observed confidence occurred on original-uk / openai-png-small / q1: confidence 0.250, P(selected) 44.0%. Low confidence does not itself establish an error.

High probability on a wrong option can coexist with repeated, stable errors. Any threshold suggested by the observed ranges is a post-hoc observation on these fixed examples, not a validated error detector for new tasks.

## Latency and cost

Latency includes valid HTTP responses (including refusals), excluding warmup. Transport/schema errors and their durations remain in requests.csv. Missing usage means unknown cost, not zero.

| Block | Language | Mode | n | Median, ms | Min–max, ms | USD / 1,000 requests | Returned model |
|---|---|---|---:|---:|---:|---:|---|
| original | en | jev-text | 10 | 275.15 | 251.37–991.25 | 0.061782 | jev-1.13.0 |
| original | en | openai-png | 10 | 304.94 | 161.56–802.06 | 0.202700 | gpt-6-luna |
| original | en | openai-png-small | 10 | 271.10 | 158.42–379.37 | 0.157100 | gpt-6-luna |
| original | en | openai-text | 10 | 235.63 | 135.30–306.02 | 0.158000 | gpt-6-luna |
| original | uk | jev-text | 10 | 269.11 | 245.03–421.96 | 0.122556 | jev-1.13.0 |
| original | uk | openai-png | 10 | 273.10 | 162.21–524.11 | 0.223200 | gpt-6-luna |
| original | uk | openai-png-small | 10 | 250.87 | 155.33–472.30 | 0.181400 | gpt-6-luna |
| original | uk | openai-text | 10 | 249.31 | 139.47–348.33 | 0.189600 | gpt-6-luna |
| traps | en | jev-text | 30 | 264.60 | 241.11–370.03 | 0.016646 | jev-1.13.0 |
| traps | en | openai-png | 30 | 223.29 | 128.93–286.16 | 0.039667 | gpt-6-luna |
| traps | en | openai-png-small | 30 | 211.48 | 120.44–623.41 | 0.021300 | gpt-6-luna |
| traps | en | openai-text | 30 | 206.68 | 110.22–246.85 | 0.017767 | gpt-6-luna |
| traps | uk | jev-text | 30 | 268.21 | 238.33–394.05 | 0.022442 | jev-1.13.0 |
| traps | uk | openai-png | 30 | 236.55 | 129.20–552.27 | 0.041267 | gpt-6-luna |
| traps | uk | openai-png-small | 30 | 214.12 | 114.73–714.92 | 0.022900 | gpt-6-luna |
| traps | uk | openai-text | 30 | 201.05 | 106.28–239.09 | 0.020567 | gpt-6-luna |
| wording | en | jev-text | 40 | 271.07 | 241.64–429.60 | 0.023006 | jev-1.13.0 |
| wording | en | openai-text | 40 | 202.06 | 107.15–276.60 | 0.032175 | gpt-6-luna |
| wording | uk | jev-text | 40 | 268.40 | 235.91–399.43 | 0.039953 | jev-1.13.0 |
| wording | uk | openai-text | 40 | 207.28 | 102.98–321.46 | 0.040950 | gpt-6-luna |

![Latency and cost](latency-cost.png)

## Per-question answers

| Example | Mode | Question | Expected | Correct / attempts | Choices (counts) | Refusals / errors |
|---|---|---|---|---:|---|---|
| actually-en | jev-text | q1 | a | 10/10 | {"a": 10} | 0 / 0 |
| actually-en | openai-text | q1 | a | 10/10 | {"a": 10} | 0 / 0 |
| actually-uk | jev-text | q1 | a | 10/10 | {"a": 10} | 0 / 0 |
| actually-uk | openai-text | q1 | a | 10/10 | {"a": 10} | 0 / 0 |
| almost-en | jev-text | q1 | c | 0/10 | {"a": 10} | 0 / 0 |
| almost-en | openai-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| almost-uk | jev-text | q1 | c | 0/10 | {"a": 10} | 0 / 0 |
| almost-uk | openai-text | q1 | c | 0/10 | {"a": 10} | 0 / 0 |
| barely-en | jev-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| barely-en | openai-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| barely-uk | jev-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| barely-uk | openai-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| condition-en | jev-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| condition-en | openai-png | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| condition-en | openai-png-small | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| condition-en | openai-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| condition-uk | jev-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| condition-uk | openai-png | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| condition-uk | openai-png-small | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| condition-uk | openai-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| correction-en | jev-text | q1 | d | 10/10 | {"d": 10} | 0 / 0 |
| correction-en | openai-png | q1 | d | 10/10 | {"d": 10} | 0 / 0 |
| correction-en | openai-png-small | q1 | d | 10/10 | {"d": 10} | 0 / 0 |
| correction-en | openai-text | q1 | d | 10/10 | {"d": 10} | 0 / 0 |
| correction-uk | jev-text | q1 | d | 10/10 | {"d": 10} | 0 / 0 |
| correction-uk | openai-png | q1 | d | 10/10 | {"d": 10} | 0 / 0 |
| correction-uk | openai-png-small | q1 | d | 10/10 | {"d": 10} | 0 / 0 |
| correction-uk | openai-text | q1 | d | 10/10 | {"d": 10} | 0 / 0 |
| little-en | jev-text | q1 | a | 10/10 | {"a": 10} | 0 / 0 |
| little-en | openai-text | q1 | a | 10/10 | {"a": 10} | 0 / 0 |
| little-uk | jev-text | q1 | a | 10/10 | {"a": 10} | 0 / 0 |
| little-uk | openai-text | q1 | a | 10/10 | {"a": 10} | 0 / 0 |
| negation-en | jev-text | q1 | b | 10/10 | {"b": 10} | 0 / 0 |
| negation-en | openai-png | q1 | b | 10/10 | {"b": 10} | 0 / 0 |
| negation-en | openai-png-small | q1 | b | 10/10 | {"b": 10} | 0 / 0 |
| negation-en | openai-text | q1 | b | 10/10 | {"b": 10} | 0 / 0 |
| negation-uk | jev-text | q1 | b | 10/10 | {"b": 10} | 0 / 0 |
| negation-uk | openai-png | q1 | b | 10/10 | {"b": 10} | 0 / 0 |
| negation-uk | openai-png-small | q1 | b | 0/10 | {"a": 10} | 0 / 0 |
| negation-uk | openai-text | q1 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | jev-text | q1 | c | 0/10 | {"a": 10} | 0 / 0 |
| original-en | jev-text | q2 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-en | jev-text | q3 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-en | jev-text | q4 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | jev-text | q5 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | jev-text | q6 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-en | jev-text | q7 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-en | jev-text | q8 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | jev-text | q9 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-en | openai-png | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-en | openai-png | q2 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-en | openai-png | q3 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-en | openai-png | q4 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | openai-png | q5 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | openai-png | q6 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-en | openai-png | q7 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-en | openai-png | q8 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | openai-png | q9 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-en | openai-png-small | q1 | c | 0/10 | {"b": 10} | 0 / 0 |
| original-en | openai-png-small | q2 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-en | openai-png-small | q3 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-en | openai-png-small | q4 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | openai-png-small | q5 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | openai-png-small | q6 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-en | openai-png-small | q7 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-en | openai-png-small | q8 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | openai-png-small | q9 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-en | openai-text | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-en | openai-text | q2 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-en | openai-text | q3 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-en | openai-text | q4 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | openai-text | q5 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | openai-text | q6 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-en | openai-text | q7 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-en | openai-text | q8 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-en | openai-text | q9 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-uk | jev-text | q1 | c | 0/10 | {"a": 10} | 0 / 0 |
| original-uk | jev-text | q2 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-uk | jev-text | q3 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-uk | jev-text | q4 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | jev-text | q5 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | jev-text | q6 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-uk | jev-text | q7 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-uk | jev-text | q8 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | jev-text | q9 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-uk | openai-png | q1 | c | 0/10 | {"b": 10} | 0 / 0 |
| original-uk | openai-png | q2 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-uk | openai-png | q3 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-uk | openai-png | q4 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | openai-png | q5 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | openai-png | q6 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-uk | openai-png | q7 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-uk | openai-png | q8 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | openai-png | q9 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-uk | openai-png-small | q1 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-uk | openai-png-small | q2 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-uk | openai-png-small | q3 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-uk | openai-png-small | q4 | b | 0/10 | {"a": 10} | 0 / 0 |
| original-uk | openai-png-small | q5 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | openai-png-small | q6 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-uk | openai-png-small | q7 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-uk | openai-png-small | q8 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | openai-png-small | q9 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-uk | openai-text | q1 | c | 0/10 | {"a": 10} | 0 / 0 |
| original-uk | openai-text | q2 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-uk | openai-text | q3 | d | 10/10 | {"d": 10} | 0 / 0 |
| original-uk | openai-text | q4 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | openai-text | q5 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | openai-text | q6 | a | 10/10 | {"a": 10} | 0 / 0 |
| original-uk | openai-text | q7 | c | 10/10 | {"c": 10} | 0 / 0 |
| original-uk | openai-text | q8 | b | 10/10 | {"b": 10} | 0 / 0 |
| original-uk | openai-text | q9 | d | 10/10 | {"d": 10} | 0 / 0 |

## Failed requests and refusals

No errors or refusals among executed requests.

## Limitations

These are diagnostic examples, not a representative language benchmark. Repetitions do not add independent examples. Some original questions quote the passage; the new traps avoid this. The English version is an adaptation.

Synthetic PNGs test reading rendered text, not general image understanding. Downsampling changes readability, payload size, and potentially tokenization. Both image sizes use detail=auto.

Timing includes network and image upload, not just inference. original returns nine answers; other blocks return one. original latency is not divided by nine. Server caching is uncontrolled; there is no local response cache.

Confidence and selected-choice probability are different fields; equivalent calibration across providers is not assumed. The historical Jev 8/9 used an unknown exact jev-latest version and is excluded from these measurements.

## Files

manifest.json stores the dataset snapshot, schedule, versions, and pricing; records.jsonl stores sanitized responses and usage; questions.csv stores per-question stability; groups.csv and requests.csv contain aggregates and individual requests. Rebuild the report without API keys.
