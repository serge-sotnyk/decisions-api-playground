"""Offline reports use the run's dataset and pricing snapshots, never current inputs."""

import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .data import ROOT, read_json, write_json


def summarize(manifest: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    examples = {e["id"]: e for e in manifest["dataset"]["examples"]}
    keys = manifest["dataset"]["answer_keys"]
    measured = [r for r in records if r["phase"] == "measurement"]
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    questions: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in measured:
        groups[(r["block"], r["language"], r["mode"])].append(r)
        answers = {a["question_id"]: a for a in r["answers"]}
        for q in examples[r["example_id"]]["questions"]:
            a = answers.get(q["id"], {"status": "error", "choice": None})
            questions[(r["example_id"], r["mode"], q["id"])].append(a)
    detail: list[dict[str, Any]] = []
    for (example_id, mode, qid), answers in sorted(questions.items()):
        choices = Counter(a["choice"] for a in answers if a["status"] == "choice")
        expected = keys[example_id][qid]
        detail.append(
            {
                "example_id": example_id,
                "mode": mode,
                "question_id": qid,
                "expected": expected,
                "attempts": len(answers),
                "correct": choices.get(expected, 0),
                "choices": dict(choices),
                "refusals": sum(a["status"] == "refusal" for a in answers),
                "errors": sum(a["status"] == "error" for a in answers),
                "distinct_choices": len(choices),
                "answer_changed": len(choices) > 1,
            }
        )
    summaries = []
    for (block, language, mode), rows in sorted(groups.items()):
        relevant = [
            d
            for d in detail
            if d["mode"] == mode
            and examples[d["example_id"]]["block"] == block
            and examples[d["example_id"]]["language"] == language
        ]
        latencies = [r["latency_ms"] for r in rows if r["status"] in {"ok", "refusal"}]
        known_costs = [r["cost_usd"] for r in rows if r["cost_usd"] is not None]
        tokens = [r["input_tokens"] for r in rows if r["input_tokens"] is not None]
        answered = sum(sum(d["choices"].values()) for d in relevant)
        correct = sum(d["correct"] for d in relevant)
        summaries.append(
            {
                "block": block,
                "language": language,
                "mode": mode,
                "requests": len(rows),
                "question_attempts": sum(d["attempts"] for d in relevant),
                "unique_questions": len(relevant),
                "correct": correct,
                "answered": answered,
                "accuracy_answered": correct / answered if answered else None,
                "refusals": sum(d["refusals"] for d in relevant),
                "request_errors": sum(r["status"] == "error" for r in rows),
                "question_errors": sum(d["errors"] for d in relevant),
                "unstable_questions": sum(d["answer_changed"] for d in relevant),
                "latency_samples": len(latencies),
                "median_ms": statistics.median(latencies) if latencies else None,
                "min_ms": min(latencies) if latencies else None,
                "max_ms": max(latencies) if latencies else None,
                "mean_input_tokens": statistics.mean(tokens) if tokens else None,
                "known_cost_usd": sum(known_costs),
                "unknown_cost_requests": len(rows) - len(known_costs),
                "usd_per_1000_requests": statistics.mean(known_costs) * 1000
                if len(known_costs) == len(rows)
                else None,
                "returned_models": sorted(
                    {r["returned_model"] for r in rows if r["returned_model"]}
                ),
            }
        )
    return {
        "status": manifest["status"],
        "execution": manifest.get("execution", "live"),
        "planned_measurements": sum(t["phase"] == "measurement" for t in manifest["schedule"]),
        "measurement_requests": len(measured),
        "warmup_requests": len(records) - len(measured),
        "known_total_cost_usd": sum(r["cost_usd"] for r in records if r["cost_usd"] is not None),
        "unknown_cost_requests": sum(r["cost_usd"] is None for r in records),
        "groups": summaries,
        "questions": detail,
    }


def csv_file(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                    for k, v in row.items()
                }
            )


def number(value: Any, places: int = 2) -> str:
    return "unknown" if value is None else f"{value:.{places}f}"


def confidence_section(manifest: dict[str, Any], records: list[dict[str, Any]]) -> list[str]:
    """Describe returned scores without assuming calibration or mixing in warmups."""
    keys = manifest["dataset"]["answer_keys"]
    mistakes: dict[tuple[str, str, str], list[tuple[float, float, float]]] = defaultdict(list)
    outcomes: dict[tuple[str, bool], list[float]] = defaultdict(list)
    least_confident: dict[str, tuple[float, str, str, str, float]] = {}
    for r in records:
        if r["phase"] != "measurement":
            continue
        for a in r["answers"]:
            if a["status"] != "choice":
                continue
            expected = keys[r["example_id"]][a["question_id"]]
            correct = a["choice"] == expected
            confidence = a["confidence"]
            selected = a["probabilities"][a["choice"]]
            outcomes[(r["provider"], correct)].append(confidence)
            if correct:
                candidate = (confidence, r["example_id"], r["mode"], a["question_id"], selected)
                previous = least_confident.get(r["provider"])
                if previous is None or candidate < previous:
                    least_confident[r["provider"]] = candidate
            else:
                mistakes[(r["example_id"], r["mode"], a["question_id"])].append(
                    (selected, a["probabilities"][expected], confidence)
                )
    lines = [
        "",
        "## Probabilities and confidence",
        "",
        "Both APIs returned a probability distribution over choices and a separate confidence field. These are API scores, not empirically established probabilities of correctness; equivalent calibration across providers is not assumed. This section includes measured choice answers only, excluding warmups, refusals, and missing answers.",
        "",
        "### Incorrect answers",
        "",
        "Each row summarizes incorrect attempts for one question and condition. P(selected) is the probability assigned to the chosen incorrect option; P(expected) is the probability assigned to the answer key. Medians are computed separately. A stable choice can still have changing probability values.",
        "",
        "| Example | Mode | Question | Incorrect attempts | Median P(selected) | Median P(expected) | Median confidence | Confidence min–max |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for (example, mode, qid), rows in sorted(mistakes.items()):
        chosen, expected_probs, confidences = zip(*rows, strict=True)
        lines.append(
            f"| {example} | {mode} | {qid} | {len(rows)} | {statistics.median(chosen):.1%} | {statistics.median(expected_probs):.1%} | {statistics.median(confidences):.3f} | {min(confidences):.3f}–{max(confidences):.3f} |"
        )
    if not mistakes:
        lines.append("No incorrect choice answers among the measured responses.")
    lines += [
        "",
        "### Confidence by outcome",
        "",
        "Counts are repeated question attempts, not independent examples. Providers have different workloads, including image modes only for Decisions; these aggregates are descriptive, not a ranking.",
        "",
        "| Provider | Outcome | Question attempts | Median confidence | Confidence min–max |",
        "|---|---|---:|---:|---:|",
    ]
    for (provider, correct), values in sorted(outcomes.items()):
        lines.append(
            f"| {provider} | {'correct' if correct else 'incorrect'} | {len(values)} | {statistics.median(values):.3f} | {min(values):.3f}–{max(values):.3f} |"
        )
    lines += ["", "Observed interpretation:", ""]
    for provider in sorted(least_confident):
        correct_values = outcomes[(provider, True)]
        wrong_values = outcomes.get((provider, False), [])
        if wrong_values:
            relation = (
                "overlap in this sample"
                if min(wrong_values) <= max(correct_values)
                and min(correct_values) <= max(wrong_values)
                else "are separate in this sample"
            )
            lines.append(
                f"- {provider}: incorrect-answer confidence was {min(wrong_values):.3f}–{max(wrong_values):.3f}, versus {min(correct_values):.3f}–{max(correct_values):.3f} for correct answers. The ranges {relation}."
            )
        confidence, example, mode, qid, selected = least_confident[provider]
        lines.append(
            f"- {provider}: a correct answer with the lowest observed confidence occurred on {example} / {mode} / {qid}: confidence {confidence:.3f}, P(selected) {selected:.1%}. Low confidence does not itself establish an error."
        )
    lines += [
        "",
        "High probability on a wrong option can coexist with repeated, stable errors. Any threshold suggested by the observed ranges is a post-hoc observation on these fixed examples, not a validated error detector for new tasks.",
    ]
    return lines


def charts(summary: dict[str, Any], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    font_path = ROOT / "assets/fonts/NotoSans-Regular.ttf"
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams["font.family"] = "Noto Sans"
    rows = summary["groups"]
    labels = [f"{r['block']} / {r['language']} / {r['mode']}" for r in rows]
    colors = [
        {
            "jev-text": "#387780",
            "openai-text": "#5369c7",
            "openai-png": "#dc8744",
            "openai-png-small": "#a35e9c",
        }[r["mode"]]
        for r in rows
    ]
    height = max(4, len(rows) * 0.4 + 2)
    fig, ax = plt.subplots(figsize=(12, height), layout="constrained")
    if rows:
        values = [100 * r["correct"] / r["question_attempts"] for r in rows]
        ax.barh(labels, values, color=colors)
        for y, r in enumerate(rows):
            ax.text(102, y, f"{r['correct']}/{r['question_attempts']}", va="center", fontsize=9)
        ax.set_xlim(0, 118)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.invert_yaxis()
    else:
        ax.text(0.5, 0.5, "No measurements yet", ha="center")
    ax.set_xlabel("Correct / all question attempts, % (including errors and refusals)")
    ax.set_title("Correctness on fixed examples; repetitions are not new examples")
    if summary["execution"] == "mock":
        fig.suptitle("SYNTHETIC TEST — NOT MODEL RESULTS", color="red")
    fig.savefig(output / "accuracy.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(15, height), layout="constrained", sharey=True)
    ys = list(range(len(rows)))
    for y, r, color in zip(ys, rows, colors, strict=True):
        if r["median_ms"] is not None:
            axes[0].barh(y, r["median_ms"], color=color)
            axes[0].errorbar(
                r["median_ms"],
                y,
                xerr=[[r["median_ms"] - r["min_ms"]], [r["max_ms"] - r["median_ms"]]],
                color="black",
                capsize=3,
            )
        else:
            axes[0].text(0, y, "no valid responses", va="center")
        if r["usd_per_1000_requests"] is not None:
            axes[1].barh(y, r["usd_per_1000_requests"], color=color)
        else:
            axes[1].text(0, y, "cost unknown", va="center")
    axes[0].set_yticks(ys, labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Median HTTP latency, ms; whiskers = min–max")
    axes[1].set_xlabel("USD / 1,000 requests of this composition")
    fig.suptitle("Latency and cost; original = 9 questions, wording/traps = 1")
    if summary["execution"] == "mock":
        fig.suptitle("SYNTHETIC TEST — NOT MODEL RESULTS", color="red")
    fig.savefig(output / "latency-cost.png", dpi=160)
    plt.close(fig)


def generate_report(run_dir: Path, output: Path | None = None) -> Path:
    manifest = read_json(run_dir / "manifest.json")
    records = [
        json.loads(line)
        for line in (run_dir / "records.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    summary = summarize(manifest, records)
    output = output or run_dir / "report"
    if output.resolve() == run_dir.resolve():
        raise ValueError("Report output must differ from run directory")
    output.mkdir(parents=True, exist_ok=True)
    # Include the sanitized original records and snapshots so the report is independently rebuildable.
    write_json(output / "manifest.json", manifest)
    (output / "records.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8"
    )
    write_json(output / "summary.json", summary)
    csv_file(output / "groups.csv", summary["groups"])
    csv_file(output / "questions.csv", summary["questions"])
    csv_file(
        output / "requests.csv",
        [
            {
                k: r[k]
                for k in (
                    "example_id",
                    "phase",
                    "mode",
                    "repetition",
                    "requested_model",
                    "returned_model",
                    "status",
                    "http_status",
                    "latency_ms",
                    "input_tokens",
                    "cost_usd",
                    "error",
                )
            }
            for r in records
        ],
    )
    lines = [
        "# Jev × OpenAI Decisions: results",
        "",
        f"Run status: **{summary['status']}**. Started: {manifest['created_at']} (UTC).",
        f"Execution: **{summary['execution']}**. mock = synthetic tests, not model results.",
        f"Planned measurements: {summary['planned_measurements']}; not executed: {summary['planned_measurements'] - summary['measurement_requests']}.",
        f"Measured requests: {summary['measurement_requests']}; warmups: {summary['warmup_requests']}.",
        f"Dataset hash: `{manifest['dataset']['fingerprint']}`.",
        f"Pricing checked: {manifest['pricing']['checked_on']}. {manifest['pricing']['scope']}",
        rf"Known subtotal for the entire run, including warmup: \${summary['known_total_cost_usd']:.8f}; requests with unknown cost: {summary['unknown_cost_requests']}.",
        "",
        "## Correctness and stability",
        "",
        "Correct / attempts includes transport errors and refusals in the denominator: it measures successful delivery of a correct answer. The separate accuracy_answered field in JSON/CSV counts only returned choice answers.",
        "",
        "| Block | Language | Mode | Correct / attempts | Unique questions | Request errors | Refusals | Questions with changed choices |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in summary["groups"]:
        lines.append(
            f"| {r['block']} | {r['language']} | {r['mode']} | {r['correct']}/{r['question_attempts']} | {r['unique_questions']} | {r['request_errors']} | {r['refusals']} | {r['unstable_questions']} |"
        )
    lines += ["", "![Correctness](accuracy.png)"]
    lines += confidence_section(manifest, records)
    lines += [
        "",
        "## Latency and cost",
        "",
        "Latency includes valid HTTP responses (including refusals), excluding warmup. Transport/schema errors and their durations remain in requests.csv. Missing usage means unknown cost, not zero.",
        "",
        "| Block | Language | Mode | n | Median, ms | Min–max, ms | USD / 1,000 requests | Returned model |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for r in summary["groups"]:
        lines.append(
            f"| {r['block']} | {r['language']} | {r['mode']} | {r['latency_samples']} | {number(r['median_ms'])} | {number(r['min_ms'])}–{number(r['max_ms'])} | {number(r['usd_per_1000_requests'], 6)} | {', '.join(r['returned_models'])} |"
        )
    lines += [
        "",
        "![Latency and cost](latency-cost.png)",
        "",
        "## Per-question answers",
        "",
        "| Example | Mode | Question | Expected | Correct / attempts | Choices (counts) | Refusals / errors |",
        "|---|---|---|---|---:|---|---|",
    ]
    for q in summary["questions"]:
        lines.append(
            f"| {q['example_id']} | {q['mode']} | {q['question_id']} | {q['expected']} | {q['correct']}/{q['attempts']} | {json.dumps(q['choices'])} | {q['refusals']} / {q['errors']} |"
        )
    failures = [r for r in records if r["status"] != "ok"]
    lines += ["", "## Failed requests and refusals", ""]
    if not failures:
        lines.append("No errors or refusals among executed requests.")
    for r in failures:
        lines.append(
            f"- {r['phase']} / {r['example_id']} / {r['mode']} / repetition {r['repetition']}: {r['status']}, {json.dumps(r['error'], ensure_ascii=False)}."
        )
    lines += [
        "",
        "## Limitations",
        "",
        "These are diagnostic examples, not a representative language benchmark. Repetitions do not add independent examples. Some original questions quote the passage; the new traps avoid this. The English version is an adaptation.",
        "",
        "Synthetic PNGs test reading rendered text, not general image understanding. Downsampling changes readability, payload size, and potentially tokenization. Both image sizes use detail=auto.",
        "",
        "Timing includes network and image upload, not just inference. original returns nine answers; other blocks return one. original latency is not divided by nine. Server caching is uncontrolled; there is no local response cache.",
        "",
        "Confidence and selected-choice probability are different fields; equivalent calibration across providers is not assumed. The historical Jev 8/9 used an unknown exact jev-latest version and is excluded from these measurements.",
        "",
        "## Files",
        "",
        "manifest.json stores the dataset snapshot, schedule, versions, and pricing; records.jsonl stores sanitized responses and usage; questions.csv stores per-question stability; groups.csv and requests.csv contain aggregates and individual requests. Rebuild the report without API keys.",
        "",
    ]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    charts(summary, output)
    return output
