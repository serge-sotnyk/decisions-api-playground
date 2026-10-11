# Results

The **2026-10-09** live experiment is complete: 480 measured requests plus 8 warmups,
all successful, with no refusals and no missing usage. The usage-based cost was **\$0.025779678**.

- [Findings and interpretation](../docs/findings.md)
- [Full report](published/20261009-main/report.md)
- [Sanitized API records](published/20261009-main/records.jsonl)
- [Frozen run manifest](published/20261009-main/manifest.json)
- [Correctness chart](published/20261009-main/accuracy.png)
- [Latency and cost chart](published/20261009-main/latency-cost.png)

`local/` is ignored by Git. Export a selected run with:

```sh
uv run --locked decisions-playground report results/local/RUN_ID --output results/published/RUN_ID
```

A reviewed `published/RUN_ID` directory can be committed alongside the conclusions.
Exporting does not commit or publish anything. Reports can be rebuilt without API keys.
Synthetic test responses must never be presented as experiment results.
