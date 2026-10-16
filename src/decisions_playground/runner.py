"""Sequential runs with durable records and no hidden retries."""

import json
import math
import platform
import subprocess
import time
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path
from typing import Any

import httpx

from .data import Dataset, Example, Trial, digest, write_json
from .providers import ENDPOINTS, SchemaError, input_tokens, normalize, payload, redact

FATAL_HTTP = {400, 401, 403, 404, 405, 422}


def now() -> str:
    return datetime.now(UTC).isoformat()


def cost(tokens: int | None, rate: float) -> float | None:
    if tokens is None:
        return None
    return float(Decimal(tokens) * Decimal(str(rate)) / Decimal(1_000_000))


def validate_pricing(pricing: dict[str, Any], models: dict[str, str], providers: set[str]) -> None:
    if pricing.get("currency") != "USD" or not pricing.get("checked_on"):
        raise ValueError("Pricing must include currency USD and checked_on")
    for provider in providers:
        item = pricing["providers"][provider]
        rate = item["input_per_million"]
        if (
            isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or not math.isfinite(rate)
            or rate < 0
        ):
            raise ValueError("Invalid price")
        if item["model"] != models[provider]:
            raise ValueError(
                f"Pricing model does not match {provider}; supply an updated --pricing file"
            )


def execute(
    client: httpx.Client,
    trial: Trial,
    example: Example,
    model: str,
    key: str,
    rate: float,
    root: Path,
    images: dict[str, Any],
    secrets: list[str],
) -> tuple[dict[str, Any], bool]:
    image = images.get("images", {}).get(f"{example.id}/{trial.input_mode}")
    if image is None:
        image = images.get("images", {}).get(f"{example.id}/{trial.mode}")
    png = (root / image["path"]).read_bytes() if image else None
    body = payload(example, trial.mode, model, png)
    # Serialize and build before timing; only HTTP transport / response download are timed.
    headers = {"Authorization": f"Bearer {key}"}
    if trial.provider == "jev" and trial.input_mode != "text":
        headers["TypeSafe-Danger-Zone-Images"] = "true"
    request = client.build_request("POST", ENDPOINTS[trial.provider], json=body, headers=headers)
    record: dict[str, Any] = {
        **asdict(trial),
        "provider": trial.provider,
        "block": example.block,
        "language": example.language,
        "requested_model": model,
        "returned_model": None,
        "started_at": now(),
        "image": image,
        "status": "error",
        "http_status": None,
        "answers": [],
        "raw_response": None,
        "usage": None,
        "input_tokens": None,
        "cost_usd": None,
        "input_per_million_usd": rate,
        "error": None,
    }
    start = time.perf_counter_ns()
    try:
        response = client.send(request)
    except httpx.HTTPError as exc:
        record["latency_ms"] = (time.perf_counter_ns() - start) / 1_000_000
        # Exception strings may contain credentials or request contents: retain only the class.
        record["error"] = {"kind": type(exc).__name__}
        return record, False
    record["latency_ms"] = (time.perf_counter_ns() - start) / 1_000_000
    record["http_status"] = response.status_code
    try:
        raw = response.json()
    except ValueError:
        record["error"] = {"kind": "non_json_response"}
        return record, response.is_success or response.status_code in FATAL_HTTP
    record["raw_response"] = redact(raw, secrets)
    if not response.is_success:
        record["error"] = {"kind": "http_error", "http_status": response.status_code}
        return record, response.status_code in FATAL_HTTP
    record["returned_model"] = raw.get("model") if isinstance(raw, dict) else None
    record["usage"] = raw.get("usage") if isinstance(raw, dict) else None
    record["input_tokens"] = input_tokens(raw)
    record["cost_usd"] = cost(record["input_tokens"], rate)
    if record["returned_model"] is not None and record["returned_model"] != model:
        record["error"] = {"kind": "model_mismatch", "expected": model}
        return redact(record, secrets), True
    try:
        record["answers"] = normalize(raw, trial.provider, example)
    except SchemaError as exc:
        record["error"] = {"kind": "response_schema", "detail": str(exc)}
        return redact(record, secrets), True
    record["status"] = (
        "refusal" if any(a["status"] == "refusal" for a in record["answers"]) else "ok"
    )
    return redact(record, secrets), False


def forecast(
    warmups: list[dict[str, Any]], schedule: list[Trial], examples: dict[str, Example]
) -> dict[str, Any]:
    # Baseline (9 questions) is only a proxy for smaller requests, not an exact token prediction.
    costs = {(r["language"], r["mode"]): r["cost_usd"] for r in warmups}
    counts = Counter((examples[t.example_id].language, t.mode) for t in schedule)
    unknown = [f"{lang}/{mode}" for (lang, mode) in counts if costs.get((lang, mode)) is None]
    estimated = None if unknown else sum(costs[k] * n for k, n in counts.items())
    return {
        "measurement_cost_usd_proxy": estimated,
        "unknown_conditions": unknown,
        "method": "Baseline request cost × scheduled requests per language/mode. Rough proxy, not an upper bound; wording/traps have fewer questions.",
    }


def run_experiment(
    root: Path,
    dataset: Dataset,
    warmups: list[Trial],
    schedule: list[Trial],
    models: dict[str, str],
    keys: dict[str, str],
    pricing: dict[str, Any],
    images: dict[str, Any],
    output: Path,
    seed: int,
    timeout: float,
    warmup_only: bool = False,
    transport: httpx.BaseTransport | None = None,
) -> bool:
    providers = {t.provider for t in warmups + schedule}
    for provider in providers:
        if not keys.get(provider, "").strip():
            raise ValueError(f"Missing API key for {provider}. Fill .env using .env.example.")
    validate_pricing(pricing, models, {t.model_key for t in warmups + schedule})
    output.mkdir(parents=True, exist_ok=False)
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except OSError, subprocess.CalledProcessError:
        commit = None
    code_files = sorted((root / "src/decisions_playground").glob("*.py"))
    manifest = {
        "schema_version": 2,
        "execution": "mock" if transport is not None else "live",
        "created_at": now(),
        "status": "running",
        "seed": seed,
        "timeout_seconds": timeout,
        "models": models,
        "pricing": pricing,
        "dataset": dataset.snapshot(),
        "images": images,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {p: version(p) for p in ("httpx", "pillow", "matplotlib", "python-dotenv")},
        "git_commit": commit,
        "code_sha256": {p.name: digest(p.read_bytes()) for p in code_files},
        "uv_lock_sha256": digest((root / "uv.lock").read_bytes()),
        "warmup_only": warmup_only,
        "schedule": [asdict(t) for t in warmups + schedule],
        "completed_requests": 0,
        "forecast": None,
    }
    write_json(output / "manifest.json", manifest)
    examples = {e.id: e for e in dataset.examples}
    secrets = [v for v in keys.values() if v]
    warmup_records = []
    trials = warmups if warmup_only else warmups + schedule
    successful = False
    try:
        with (
            httpx.Client(
                transport=transport
                or httpx.HTTPTransport(
                    retries=0, trust_env=False, limits=httpx.Limits(keepalive_expiry=60)
                ),
                timeout=timeout,
                trust_env=False,
                limits=httpx.Limits(keepalive_expiry=60),
            ) as client,
            (output / "records.jsonl").open("x", encoding="utf-8") as log,
        ):
            for index, trial in enumerate(trials, 1):
                e = examples[trial.example_id]
                rate = pricing["providers"][trial.model_key]["input_per_million"]
                record, fatal = execute(
                    client,
                    trial,
                    e,
                    models[trial.model_key],
                    keys[trial.provider],
                    rate,
                    root,
                    images,
                    secrets,
                )
                log.write(json.dumps(record, ensure_ascii=False) + "\n")
                log.flush()
                manifest["completed_requests"] = index
                print(
                    f"[{index}/{len(trials)}] {trial.phase} {e.id} {trial.mode}: "
                    f"{record['status']} {record['latency_ms']:.1f} ms",
                    flush=True,
                )
                if trial.phase == "warmup":
                    warmup_records.append(record)
                if fatal:
                    manifest["status"] = "stopped_fatal_error"
                    return False
                if index == len(warmups):
                    manifest["forecast"] = forecast(warmup_records, schedule, examples)
                    print(
                        "Forecast from warmup requests: "
                        + json.dumps(manifest["forecast"], ensure_ascii=False),
                        flush=True,
                    )
                    if any(r["status"] != "ok" for r in warmup_records):
                        manifest["status"] = "stopped_warmup_failure"
                        return False
                write_json(output / "manifest.json", manifest)
        manifest["status"] = "warmup_complete" if warmup_only else "complete"
        successful = True
        return True
    finally:
        if not successful and manifest["status"] == "running":
            manifest["status"] = "interrupted"
        manifest["finished_at"] = now()
        write_json(output / "manifest.json", manifest)
