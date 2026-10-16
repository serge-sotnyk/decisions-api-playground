# Results

## October 16: three models and shared padded images

The **2026-10-16** follow-up is complete: 480 measured requests plus 18 warmups,
all successful, with no refusals and no missing usage. Jev 1.13, Jev 1.14, and
Decisions received the same inputs over five repetitions. The usage-based cost
was **\$0.028282918**.

- [Findings and interpretation](../docs/findings-20261016.md)
- [Full report](published/20261016-main/report.md)
- [Sanitized API records](published/20261016-main/records.jsonl)
- [Frozen run manifest](published/20261016-main/manifest.json)
- [Correctness chart](published/20261016-main/accuracy.png)
- [Latency and cost chart](published/20261016-main/latency-cost.png)

## October 9: original experiment, preserved unchanged

The **2026-10-09** live experiment is complete: 480 measured requests plus 8 warmups,
all successful, with no refusals and no missing usage. The usage-based cost was **\$0.025779678**.

- [Findings and interpretation](../docs/findings.md)
- [Full report](published/20261009-main/report.md)
- [Sanitized API records](published/20261009-main/records.jsonl)
- [Frozen run manifest](published/20261009-main/manifest.json)
- [Correctness chart](published/20261009-main/accuracy.png)
- [Latency and cost chart](published/20261009-main/latency-cost.png)

## Offline export

`local/` is ignored by Git. Export a selected run with:

```sh
uv run --locked decisions-playground report results/local/RUN_ID --output results/published/RUN_ID
```

A reviewed `published/RUN_ID` directory can be committed alongside the conclusions.
Exporting does not commit or publish anything. Reports can be rebuilt without API keys.
Synthetic test responses must never be presented as experiment results.
