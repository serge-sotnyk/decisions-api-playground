import json
from copy import deepcopy
from typing import Any

import httpx
import pytest

from decisions_playground.data import MODEL_IDS, ROOT, Trial, load_dataset, matrix, read_json
from decisions_playground.images import load_images
from decisions_playground.report import confidence_section, generate_report, summarize
from decisions_playground.runner import cost, execute, forecast, run_experiment

MODELS = {**MODEL_IDS, "jev": "jev-1.13.0"}
KEYS = {"jev": "TEST_SECRET_JEV", "openai": "TEST_SECRET_OPENAI"}


def fake_response(request: httpx.Request) -> httpx.Response:
    """Synthetic contract stub, intentionally always chooses a; never benchmark evidence."""
    body = json.loads(request.content)
    is_jev = "state" in body
    if is_jev:
        assert (request.headers.get("TypeSafe-Danger-Zone-Images") == "true") == ("assets" in body)
    names = list(body["questions"]) if is_jev else [q["name"] for q in body["questions"]]
    answers: list[dict[str, Any]] = [
        {
            "type": "choice",
            "choice": "a",
            "confidence": 0.5,
            "probabilities": {"a": 0.7, "b": 0.1, "c": 0.1, "d": 0.1},
            "name": name,
        }
        for name in reversed(names)
    ]
    if is_jev:
        result = {a.pop("name"): a for a in answers}
    else:
        for a in answers:
            a["probabilities"] = [
                {"value": k, "probability": v} for k, v in a["probabilities"].items()
            ]
        result = answers
    return httpx.Response(
        200,
        json={
            "model": body["model"],
            "answers": result,
            "usage": {"input_tokens": 1000, "output_tokens": 10},
        },
    )


@pytest.fixture
def completed_run(tmp_path):
    data = load_dataset()
    warmups, schedule = matrix(data)
    output = tmp_path / "run"
    assert run_experiment(
        ROOT,
        data,
        warmups,
        schedule,
        MODELS,
        KEYS,
        read_json(ROOT / "data/pricing-20261016.json"),
        load_images(data),
        output,
        20261016,
        30,
        transport=httpx.MockTransport(fake_response),
    )
    records = [json.loads(line) for line in (output / "records.jsonl").read_text().splitlines()]
    return output, read_json(output / "manifest.json"), records


def test_full_matrix_offline_run_and_report(completed_run, tmp_path, monkeypatch):
    output, manifest, records = completed_run
    assert len(records) == 498
    assert manifest["status"] == "complete" and manifest["execution"] == "mock"
    text = (output / "records.jsonl").read_text()
    assert all(secret not in text for secret in KEYS.values())
    assert "base64," not in text and "Authorization" not in text
    summary = summarize(manifest, records)
    assert summary["measurement_requests"] == 480
    assert summary["warmup_requests"] == 18
    assert len(summary["groups"]) == 42
    assert sum(g["question_attempts"] for g in summary["groups"]) == 1200
    assert summary["known_total_cost_usd"] == pytest.approx(332 * 0.000042 + 166 * 0.0001)
    for key, model in MODEL_IDS.items():
        selected = [r for r in records if r["mode"].startswith(key + "-")]
        assert len(selected) == 166
        assert {r["requested_model"] for r in selected} == {model}
    # The exact same files, hashes and sizes are used across all three models.
    for example in ("original-uk", "negation-en"):
        for kind in ("png", "png-small"):
            rows = [
                r
                for r in records
                if r["example_id"] == example and r["mode"].split("-", 1)[1] == kind
            ]
            assert len({r["image"]["sha256"] for r in rows}) == 1
    confidence = "\n".join(confidence_section(manifest, records))
    assert "| jev-1.13.0 |" in confidence and "| jev-1.14.0 |" in confidence

    # Reporting must not initialize an HTTP client or read any key.
    def forbid_network(*args, **kwargs):
        raise AssertionError("Offline report made a network call")

    monkeypatch.setattr(httpx.Client, "send", forbid_network)
    for variable in ("TYPESAFE_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(variable, raising=False)
    report = generate_report(output, tmp_path / "published")
    assert (report / "accuracy.png").stat().st_size > 1000
    assert (report / "latency-cost.png").stat().st_size > 1000
    rebuilt = generate_report(report, tmp_path / "rebuilt")
    assert read_json(rebuilt / "summary.json") == read_json(report / "summary.json")
    assert (rebuilt / "report.md").read_bytes() == (report / "report.md").read_bytes()


def test_warmup_excluded_and_unknown_cost_and_failed_questions_visible(completed_run):
    _, manifest, records = completed_run
    # Limit analysis to the first selected condition and inject known outcomes.
    r = next(r for r in records if r["phase"] == "measurement" and r["block"] == "wording")
    r1 = deepcopy(r)
    r1["latency_ms"] = 100
    r2 = deepcopy(r)
    r2["latency_ms"] = 300
    r2["input_tokens"] = r2["cost_usd"] = None
    r2["answers"][0]["choice"] = "c"
    error = deepcopy(r)
    error.update(status="error", answers=[], latency_ms=5000, cost_usd=None)
    refusal = deepcopy(r)
    refusal.update(
        status="refusal",
        latency_ms=500,
        answers=[{"question_id": "q1", "status": "refusal", "choice": None}],
    )
    warmup = deepcopy(r)
    warmup.update(phase="warmup", latency_ms=999999)
    summary = summarize(manifest, [warmup, r1, r2, error, refusal])
    group = summary["groups"][0]
    assert group["median_ms"] == 300
    assert group["min_ms"] == 100 and group["max_ms"] == 500
    assert group["question_attempts"] == 4
    assert group["request_errors"] == 1 and group["refusals"] == 1
    assert group["unstable_questions"] == 1
    assert group["usd_per_1000_requests"] is None
    assert group["unknown_cost_requests"] == 2


def test_confidence_report_uses_only_measured_choices_and_separates_scores():
    manifest = {"dataset": {"answer_keys": {"example": {"q1": "b"}}}}
    record: dict[str, Any] = {
        "phase": "measurement",
        "example_id": "example",
        "mode": "openai-text",
        "provider": "openai",
        "answers": [
            {
                "question_id": "q1",
                "status": "choice",
                "choice": "a",
                "probabilities": {"a": 0.94, "b": 0.04, "c": 0.01, "d": 0.01},
                "confidence": 0.92,
            }
        ],
    }
    correct = deepcopy(record)
    correct["answers"][0].update(
        choice="b",
        confidence=0.25,
        probabilities={"a": 0.41, "b": 0.44, "c": 0.06, "d": 0.09},
    )
    warmup = deepcopy(record)
    warmup["phase"] = "warmup"
    warmup["answers"][0]["confidence"] = 0.01
    refusal = {**record, "answers": [{"status": "refusal", "question_id": "q1"}]}
    error = {**record, "answers": []}
    text = "\n".join(confidence_section(manifest, [record, correct, warmup, refusal, error]))
    assert "| example | openai-text | q1 | 1 | 94.0% | 4.0% | 0.920 |" in text
    assert "| openai | correct | 1 | 0.250 | 0.250–0.250 |" in text
    assert "| openai | incorrect | 1 | 0.920 | 0.920–0.920 |" in text
    assert "confidence 0.250, P(selected) 44.0%" in text
    assert "not a validated error detector" in text


@pytest.mark.parametrize(
    "status,fatal", [(400, True), (401, True), (403, True), (422, True), (429, False), (500, False)]
)
def test_http_failures_no_retries_and_redacted(status, fatal):
    e = next(e for e in load_dataset().examples if e.id == "almost-uk")
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": "TEST_SECRET_JEV"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        record, stopped = execute(
            client,
            Trial(e.id, "jev-text", 1),
            e,
            MODELS["jev"],
            KEYS["jev"],
            0.042,
            ROOT,
            {},
            list(KEYS.values()),
        )
    assert len(calls) == 1 and stopped is fatal
    assert record["status"] == "error" and record["cost_usd"] is None
    assert "TEST_SECRET_JEV" not in json.dumps(record)


def test_timeout_and_schema_failure_are_recorded():
    e = next(e for e in load_dataset().examples if e.id == "almost-uk")

    def timeout(request):
        raise httpx.ReadTimeout("TEST_SECRET_JEV", request=request)

    for handler, fatal, kind in (
        (timeout, False, "ReadTimeout"),
        (
            lambda r: httpx.Response(200, json={"model": "unexpected-model", "answers": {}}),
            True,
            "model_mismatch",
        ),
        (lambda r: httpx.Response(200, json={"answers": []}), True, "response_schema"),
    ):
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            record, stopped = execute(
                client,
                Trial(e.id, "jev-text", 1),
                e,
                MODELS["jev"],
                KEYS["jev"],
                0.042,
                ROOT,
                {},
                list(KEYS.values()),
            )
        assert stopped is fatal and record["error"]["kind"] == kind
        assert "TEST_SECRET_JEV" not in json.dumps(record)


def test_fatal_stops_and_keeps_record(tmp_path):
    data = load_dataset()
    warmups, schedule = matrix(data, provider="jev", repeats=1)
    output = tmp_path / "failed"
    assert not run_experiment(
        ROOT,
        data,
        warmups,
        schedule,
        MODELS,
        KEYS,
        read_json(ROOT / "data/pricing-20261016.json"),
        load_images(data),
        output,
        1,
        30,
        transport=httpx.MockTransport(lambda r: httpx.Response(401, json={"error": "invalid key"})),
    )
    assert len((output / "records.jsonl").read_text().splitlines()) == 1
    assert read_json(output / "manifest.json")["status"] == "stopped_fatal_error"
    report = generate_report(output)
    assert read_json(report / "summary.json")["measurement_requests"] == 0


def test_cost_and_forecast_unknown():
    assert cost(1_000_000, 0.042) == 0.042
    assert cost(1000, 0.1) == 0.0001
    assert cost(0, 0.1) == 0
    assert cost(None, 0.1) is None
    data = load_dataset()
    _, schedule = matrix(data, repeats=1, provider="jev")
    result = forecast([], schedule, {e.id: e for e in data.examples})
    assert result["measurement_cost_usd_proxy"] is None
    assert len(result["unknown_conditions"]) == 12


def test_missing_keys_fails_before_writing(tmp_path):
    data = load_dataset()
    warmups, schedule = matrix(data, provider="jev")
    with pytest.raises(ValueError, match="Missing API key"):
        run_experiment(
            ROOT,
            data,
            warmups,
            schedule,
            MODELS,
            {},
            read_json(ROOT / "data/pricing-20261016.json"),
            {},
            tmp_path / "none",
            1,
            30,
        )
    assert not (tmp_path / "none").exists()
