"""CLI for preparation, measured runs, and offline reports."""

import argparse
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from .data import ROOT, load_dataset, matrix, read_json
from .images import load_images, prepare
from .report import generate_report
from .runner import run_experiment


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Must be positive")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Jev × OpenAI Decisions: reproducible UA/EN experiment"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "prepare", help="Validate pinned data and render evidence PNGs; no API calls"
    )
    run = commands.add_parser("run", help="Run the fixed experiment matrix")
    run.add_argument("--block", choices=("all", "original", "wording", "traps"), default="all")
    run.add_argument("--provider", choices=("all", "jev", "openai"), default="all")
    run.add_argument("--repeats", type=positive, default=10)
    run.add_argument("--seed", type=int, default=20261009)
    run.add_argument("--timeout", type=positive, default=30)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument(
        "--warmup-only",
        action="store_true",
        help="Run only initial checks and forecast full-run cost",
    )
    run.add_argument("--pricing", type=Path, default=ROOT / "data/pricing.json")
    run.add_argument(
        "--output",
        type=Path,
        help="New run directory; defaults to ignored results/local/<timestamp>",
    )
    report = commands.add_parser("report", help="Rebuild tables and plots offline from a saved run")
    report.add_argument("run_dir", type=Path)
    report.add_argument(
        "--output", type=Path, help="Export a self-contained report, e.g. results/published/<run>"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            print(generate_report(args.run_dir, args.output))
            return 0
        dataset = load_dataset()
        if args.command == "prepare":
            images = prepare(dataset)
            print(
                f"{len(dataset.examples)} examples; {len(images['images'])} PNGs; dataset {dataset.fingerprint}"
            )
            return 0
        warmups, schedule = matrix(dataset, args.repeats, args.seed, args.block, args.provider)
        examples = {e.id: e for e in dataset.examples}
        counts = Counter(examples[t.example_id].block for t in schedule)
        print(
            json.dumps(
                {
                    "blocks": dict(counts),
                    "measurements": len(schedule),
                    "warmup": len(warmups),
                    "requests_to_send": len(warmups) + (0 if args.warmup_only else len(schedule)),
                    "seed": args.seed,
                },
                indent=2,
            )
        )
        if args.dry_run:
            return 0
        load_dotenv(ROOT / ".env", override=False)
        models = {
            "jev": os.getenv("JEV_MODEL", "jev-1.13.0"),
            "openai": os.getenv("OPENAI_MODEL", "gpt-6-luna"),
        }
        keys = {"jev": os.getenv("TYPESAFE_API_KEY", ""), "openai": os.getenv("OPENAI_API_KEY", "")}
        pricing = read_json(args.pricing)
        print(
            f"Pricing ({pricing['checked_on']}): "
            + json.dumps(pricing["providers"], ensure_ascii=False)
        )
        images = load_images(dataset) if any("png" in t.mode for t in warmups) else {}
        output = args.output or ROOT / "results/local" / datetime.now(UTC).strftime(
            "%Y%m%dT%H%M%S.%fZ"
        )
        ok = run_experiment(
            ROOT,
            dataset,
            warmups,
            schedule,
            models,
            keys,
            pricing,
            images,
            output,
            args.seed,
            args.timeout,
            args.warmup_only,
        )
        print(f"Results: {output}")
        print(f"Report: {generate_report(output)}")
        return 0 if ok else 1
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    except KeyboardInterrupt:
        parser.exit(130, "Interrupted. Completed requests are saved; rebuild with report.\n")


if __name__ == "__main__":
    raise SystemExit(main())
