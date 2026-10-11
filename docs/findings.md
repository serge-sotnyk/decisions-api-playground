# Findings from the 2026-10-09 live run

The clearest result is that a stable answer can still be wrong, and the same aggregate
score can hide different errors when text is supplied as an image.

The run completed all **480 measured requests and 8 warmups** with no API errors,
refusals, or missing usage. Requested and returned model names matched:
`jev-1.13.0` and Decisions `gpt-6-luna`. Each condition was repeated ten times.
Every question retained the same selected answer across those ten repetitions;
this does not imply that confidence values or complete responses were identical.

See the [generated report](../results/published/20261009-main/report.md),
[per-question results](../results/published/20261009-main/questions.csv),
[raw records](../results/published/20261009-main/records.jsonl), and
[methodology](methodology.md). These findings describe this saved run only.

## Original nine-question passage

Each score below was reproduced in all ten repetitions.

| Input and provider | English | Ukrainian |
|---|---:|---:|
| Jev text | 8/9 | 8/9 |
| Decisions text | 9/9 | 8/9 |
| Decisions PNG, 1200 px wide | 9/9 | 8/9 |
| Decisions PNG, 600 px wide | 8/9 | 8/9 |

Jev answered q1 incorrectly in both languages: it selected that both people were
late, although Marko almost being late means he was not late. Decisions text
answered this correctly in English but made the same mistake as Jev in Ukrainian.
The pinned Jev run reproduces the historical 8/9 outcome; the earlier
`jev-latest` observation has no known exact model version and is not a controlled
comparison across model versions.

The Ukrainian image modes also scored 8/9, but their mistakes differed:

- At full size, Decisions got q1 wrong by selecting that only Marko was late.
- At half size, Decisions got q1 right but reversed who asked whom in q4.

The English half-size PNG introduced a q1 error: only Marko was selected as late.
Aggregate accuracy alone therefore misses meaningful changes in the answers.

## Wording variants and new traps

In the wording block, Jev answered three of four variants correctly in each language.
Decisions answered all four in English and three of four in Ukrainian. The only
failing variant was the original "almost late" wording; the other three variants
were answered correctly by both models in both languages.

Both text providers and full-size Decisions PNGs answered all three new traps
correctly in both languages. These tested a negated failure to act, an unresolved
condition, and a correction to earlier information.

The exception was the half-size Ukrainian PNG for the negation example:
"Олена не забула надіслати лист перед обідом." Decisions chose that she forgot the
task in all ten repetitions. The text and full-size image conditions chose that
she sent the email. This run demonstrates sensitivity to the image representation;
it does not isolate whether recognition or subsequent interpretation caused the error.

## Confidence on incorrect answers

Both APIs returned choice probabilities and a separate `confidence` field. Jev's
incorrect answers had confidence between **0.40 and 0.65**, compared with **0.80
to 1.00** on correct answers. For q1 in the original Ukrainian passage, the median
probability of the selected wrong answer was 65.5%, while the correct answer
received 31%; median confidence was 0.54. The selected answer stayed unchanged,
but the probability distribution varied across repetitions.

Decisions sometimes made much more confident errors. On the same Ukrainian text
question, both in the original and wording blocks, it assigned **94% to the wrong
answer and 4% to the correct one**, with confidence **0.92**, in every repetition.
The half-size Ukrainian negation PNG received 88% for the incorrect answer,
6% for the correct answer, and confidence 0.84.

Other image errors showed closer competing options: the half-size Ukrainian q4
role reversal received 53% for the wrong answer and 41% for the correct answer,
with confidence 0.37. Conversely, q1 was answered correctly on that same image
with only 44% for the selected correct option versus 41% for its nearest competitor,
and confidence 0.25. Low confidence did not necessarily indicate an error.

The generated report includes all incorrect question/condition combinations and
confidence ranges by outcome. Jev's ranges happened to separate correct and
incorrect answers in this sample, but a threshold chosen after seeing these
results is not a validated detector. Decisions' ranges overlapped. Neither API's
scores should be read as empirically calibrated probabilities of correctness or
directly equated to the other provider's scores.

## Latency and cost

The following numbers refer to an entire request containing the original passage
and all nine questions. Warmups are excluded from latency statistics. Timing includes
the network and image upload, with one sequential HTTP client and reused connections.

| Language | Mode | Median, ms | Min–max, ms | USD per 1,000 identical requests |
|---|---|---:|---:|---:|
| English | Jev text | 275.15 | 251.37–991.25 | 0.061782 |
| English | Decisions text | 235.63 | 135.30–306.02 | 0.158000 |
| English | Decisions PNG | 304.94 | 161.56–802.06 | 0.202700 |
| English | Decisions half-size PNG | 271.10 | 158.42–379.37 | 0.157100 |
| Ukrainian | Jev text | 269.11 | 245.03–421.96 | 0.122556 |
| Ukrainian | Decisions text | 249.31 | 139.47–348.33 | 0.189600 |
| Ukrainian | Decisions PNG | 273.10 | 162.21–524.11 | 0.223200 |
| Ukrainian | Decisions half-size PNG | 250.87 | 155.33–472.30 | 0.181400 |

Decisions text had lower median HTTP latency in this run. These are measurements
from one client and one short session, not server-only inference times or general
latency guarantees. Full distributions and results for the other blocks remain
available in the generated report and individual request records.

The whole run cost **$0.025779678**, including warmups, calculated from reported input
tokens and the frozen tariffs: Jev $0.042 per million and Decisions $0.10 per million;
output was free. This is a usage-based calculation, not an invoice reconciliation.
Tariff sources and verification date are preserved in the manifest.

Jev accounted for $0.005718678 over 162 requests; Decisions accounted for $0.020061
over 326 requests. Those totals cover different workloads because Decisions also
handled the two image modes, so they should not be compared as equal-task costs.

For the original text requests, Decisions cost about 2.56 times as much in English
and 1.55 times as much in Ukrainian. Token counts matter as well as the published
per-token rate: across the three Ukrainian traps, Decisions text averaged
$0.020567 per 1,000 requests versus Jev's $0.022442. For that row, 1,000 requests
means the same equal mixture of the three examples.

The warmup-based forecast was $0.07313104 for the measured portion. It intentionally
used the longer nine-question requests as a proxy; the actual matrix contains many
shorter requests. Use the completed run's usage for reporting actual cost.

## Scope of the conclusions

The experiment contains a few fixed examples, not a representative language benchmark.
Ten repetitions measure observed answer stability and request latency, not ten new
independent examples. Synthetic PNGs contain clean rendered text; these results do
not establish performance on photographs, scans, handwriting, or arbitrary layouts.
Questions and choices stayed textual; only the source passage became an image.

Inputs and keys were frozen before the first live run. No examples were adjusted
in response to these results. Confidence and probability fields are preserved but
are not treated as calibrated or directly comparable between providers.

The useful follow-up is concrete: the original linguistic trap remains a problem
for some conditions, and changing text into an image can change which question is
wrong even when the total score stays the same.
