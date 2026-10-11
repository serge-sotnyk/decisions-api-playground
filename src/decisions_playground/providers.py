"""Explicit request allowlists and strict response normalization."""

import base64
import math
from typing import Any

from .data import Example

ENDPOINTS = {
    "jev": "https://api.typesafe.ai/v1/systemone",
    "openai": "https://api.openai.com/v1/decisions",
}


def payload(example: Example, mode: str, model: str, png: bytes | None = None) -> dict[str, Any]:
    # Example deliberately has no expected answers or explanations.
    if mode == "jev-text":
        return {
            "model": model,
            "state": {"text": example.text},
            "questions": {
                q.id: {"type": "choice", "instructions": q.instructions, "criteria": q.choices}
                for q in example.questions
            },
        }
    if mode not in ("openai-text", "openai-png", "openai-png-small"):
        raise ValueError(f"Unknown mode: {mode}")
    evidence: Any = example.text
    if mode != "openai-text":
        if not png:
            raise ValueError("Image mode requires PNG")
        evidence = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": "data:image/png;base64," + base64.b64encode(png).decode(),
                        "detail": "auto",
                    }
                ],
            }
        ]
    return {
        "model": model,
        "input": evidence,
        "questions": [
            {
                "type": "choice",
                "name": q.id,
                "instructions": q.instructions,
                "choices": [{"value": k, "description": v} for k, v in q.choices.items()],
            }
            for q in example.questions
        ],
    }


class SchemaError(ValueError):
    """An API contract failure; stop instead of collecting misleading results."""


def probability(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaError("Invalid probability type")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise SchemaError("Probability outside [0, 1]")
    return float(value)


def normalize(raw: Any, provider: str, example: Example) -> list[dict[str, Any]]:
    if not isinstance(raw, dict) or not isinstance(raw.get("model"), str):
        raise SchemaError("Missing response model")
    answers = raw.get("answers")
    if provider == "openai":
        if not isinstance(answers, list) or any(not isinstance(a, dict) for a in answers):
            raise SchemaError("Expected an answers array")
        names = [a.get("name") for a in answers]
        if any(not isinstance(n, str) for n in names) or len(set(names)) != len(names):
            raise SchemaError("Missing/duplicate question names")
        answers = {a["name"]: a for a in answers}
    if not isinstance(answers, dict) or set(answers) != {q.id for q in example.questions}:
        raise SchemaError("Response question IDs differ from request")
    result = []
    for q in example.questions:
        a = answers[q.id]
        if not isinstance(a, dict):
            raise SchemaError("Invalid answer object")
        if a.get("type") == "refusal":
            result.append(
                {
                    "question_id": q.id,
                    "status": "refusal",
                    "choice": None,
                    "probabilities": None,
                    "confidence": None,
                }
            )
            continue
        if (
            a.get("type") != "choice"
            or not isinstance(a.get("choice"), str)
            or a["choice"] not in q.choices
        ):
            raise SchemaError("Invalid choice answer")
        probs = a.get("probabilities")
        if provider == "openai":
            if not isinstance(probs, list) or any(not isinstance(p, dict) for p in probs):
                raise SchemaError("Invalid probability array")
            values = [p.get("value") for p in probs]
            if any(not isinstance(v, str) for v in values) or len(set(values)) != len(values):
                raise SchemaError("Invalid probability option IDs")
            probs = {p["value"]: p.get("probability") for p in probs}
        if not isinstance(probs, dict) or set(probs) != set(q.choices):
            raise SchemaError("Probability options differ from request")
        probs = {k: probability(v) for k, v in probs.items()}
        if not math.isclose(sum(probs.values()), 1.0, abs_tol=0.025):
            raise SchemaError("Probabilities do not sum to one")
        result.append(
            {
                "question_id": q.id,
                "status": "choice",
                "choice": a["choice"],
                "probabilities": probs,
                "confidence": probability(a.get("confidence")),
            }
        )
    return result


def input_tokens(raw: Any) -> int | None:
    usage = raw.get("usage") if isinstance(raw, dict) else None
    value = usage.get("input_tokens") if isinstance(usage, dict) else None
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def redact(value: Any, secrets: list[str]) -> Any:
    """Keep raw JSON useful without saving keys or accidentally echoed inline images."""
    if isinstance(value, dict):
        return {
            k: (
                "[REDACTED]"
                if k.lower() in {"authorization", "api_key", "image_url"}
                else redact(v, secrets)
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        if "data:image/" in value:
            return "[INLINE IMAGE REDACTED]"
    return value
