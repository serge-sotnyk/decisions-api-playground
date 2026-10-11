import base64
import json
from dataclasses import replace

import pytest

from decisions_playground.data import ROOT, load_dataset, read_json
from decisions_playground.providers import SchemaError, input_tokens, normalize, payload, redact


@pytest.fixture
def example():
    e = next(e for e in load_dataset().examples if e.id == "original-uk")
    return replace(e, questions=e.questions[:2])


def test_request_adapters_and_no_image_text_leak(example):
    j = payload(example, "jev-text", "jev-1.13.0")
    assert j["state"] == {"text": example.text}
    o = payload(example, "openai-text", "gpt-6-luna")
    assert o["input"] == example.text
    assert o["questions"][0]["choices"] == [
        {"value": k, "description": v} for k, v in example.questions[0].choices.items()
    ]
    for mode in ("openai-png", "openai-png-small"):
        p = payload(example, mode, "gpt-6-luna", b"test-png")
        content = p["input"][0]["content"]
        assert len(content) == 1 and content[0]["type"] == "input_image"
        assert base64.b64decode(content[0]["image_url"].split(",")[1]) == b"test-png"
        assert example.text not in json.dumps(p, ensure_ascii=False)
        assert p["questions"] == o["questions"]
    assert set(j) == {"state", "model", "questions"}
    assert set(o) == {"input", "model", "questions"}


@pytest.mark.parametrize("provider", ["jev", "openai"])
def test_fixture_normalization_matches_names_not_order(provider, example):
    raw = read_json(ROOT / f"tests/fixtures/{provider}.json")
    answers = normalize(raw, provider, example)
    assert [a["question_id"] for a in answers] == ["q1", "q2"]
    assert [a["choice"] for a in answers] == ["c", "a"]
    assert answers[0]["confidence"] == 0.7
    assert answers[0]["probabilities"]["c"] == 0.9
    assert input_tokens(raw) == 1000


def test_mixed_refusal_and_duplicate_missing_invalid_answers(example):
    raw = read_json(ROOT / "tests/fixtures/openai.json")
    raw["answers"][0] = {"type": "refusal", "name": "q2"}
    assert normalize(raw, "openai", example)[1]["status"] == "refusal"
    raw["answers"][0]["name"] = "q1"
    with pytest.raises(SchemaError):
        normalize(raw, "openai", example)
    raw["answers"] = raw["answers"][:1]
    with pytest.raises(SchemaError):
        normalize(raw, "openai", example)
    raw = read_json(ROOT / "tests/fixtures/jev.json")
    raw["answers"]["q1"]["choice"] = []
    with pytest.raises(SchemaError):
        normalize(raw, "jev", example)


@pytest.mark.parametrize("value", [None, -1, True, "10", 1.2])
def test_invalid_usage_is_unknown(value):
    assert input_tokens({"usage": {"input_tokens": value}}) is None


def test_redaction():
    raw = {
        "error": "echo secret-key",
        "authorization": "Bearer secret-key",
        "nested": [{"image_url": "data:image/png;base64,AAAA"}],
    }
    clean = json.dumps(redact(raw, ["secret-key"]))
    assert "secret-key" not in clean and "AAAA" not in clean
