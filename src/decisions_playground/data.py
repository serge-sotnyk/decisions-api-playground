"""Source loading, answer keys, and the fixed experiment matrix."""

import hashlib
import json
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MODEL_IDS = {"jev13": "jev-1.13.0", "jev14": "jev-1.14.0", "openai": "gpt-6-luna"}
MODES = tuple(f"{model}-{kind}" for model in MODEL_IDS for kind in ("text", "png", "png-small"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class Question:
    id: str
    instructions: str
    choices: dict[str, str]


@dataclass(frozen=True)
class Example:
    id: str
    block: str
    language: str
    text: str
    questions: tuple[Question, ...]


@dataclass
class Dataset:
    examples: list[Example]
    answer_keys: dict[str, dict[str, str]]
    fingerprint: str

    def snapshot(self) -> dict[str, Any]:
        return {
            "examples": [asdict(e) for e in self.examples],
            "answer_keys": self.answer_keys,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True)
class Trial:
    example_id: str
    mode: str
    repetition: int
    phase: str = "measurement"

    @property
    def provider(self) -> str:
        return "jev" if self.model_key.startswith("jev") else self.model_key

    @property
    def model_key(self) -> str:
        return self.mode.split("-", 1)[0]

    @property
    def input_mode(self) -> str:
        return self.mode.split("-", 1)[1]


def verify_files(directory: Path) -> dict[str, Any]:
    provenance = read_json(directory / "provenance.json")
    for name, expected in provenance["sha256"].items():
        if digest((directory / name).read_bytes()) != expected:
            raise ValueError(f"Source checksum mismatch: {directory / name}")
    return provenance


def load_dataset(root: Path = ROOT) -> Dataset:
    verify_files(root / "data/source")
    examples: list[Example] = []
    keys: dict[str, dict[str, str]] = {}
    for language, name in (("uk", "ukrainian"), ("en", "english")):
        source = (root / f"data/source/jev-{name}.md").read_text(encoding="utf-8")
        state, questions, key = [
            json.loads(s) for s in re.findall(r"```json\s*\n(.*?)```", source, re.S)
        ]
        qs = tuple(Question(qid, q["instructions"], q["criteria"]) for qid, q in questions.items())
        example = Example(f"original-{language}", "original", language, state["text"], qs)
        examples.append(example)
        keys[example.id] = key
        # Extract the four source table rows, preserving their exact wording.
        variants = re.findall(r"^\| ((?:Марко|Marko)[^|]+?) \| `([ac])`", source, re.M)
        if len(variants) != 4 or not example.text.startswith(variants[0][0]):
            raise ValueError(f"Unexpected variant table in {name}")
        suffix = example.text[len(variants[0][0]) :]
        for slug, (opening, answer) in zip(
            ("almost", "actually", "barely", "little"), variants, strict=True
        ):
            item = Example(f"{slug}-{language}", "wording", language, opening + suffix, qs[:1])
            examples.append(item)
            keys[item.id] = {"q1": answer}
    traps = read_json(root / "data/traps.json")
    trap_keys = read_json(root / "data/trap_answers.json")
    if set(trap_keys) != {t["id"] for t in traps}:
        raise ValueError("Trap answer IDs do not match inputs")
    for trap in traps:
        examples.append(
            Example(
                trap["id"],
                "traps",
                trap["language"],
                trap["text"],
                (Question("q1", trap["question"], trap["choices"]),),
            )
        )
        keys[trap["id"]] = trap_keys[trap["id"]]
    if len({e.id for e in examples}) != len(examples):
        raise ValueError("Duplicate example ID")
    for e in examples:
        if set(keys[e.id]) != {q.id for q in e.questions}:
            raise ValueError(f"Answer key mismatch: {e.id}")
        for q in e.questions:
            if list(q.choices) != ["a", "b", "c", "d"] or keys[e.id][q.id] not in q.choices:
                raise ValueError(f"Invalid choices/key: {e.id}/{q.id}")
    serialized = json.dumps(
        {"examples": [asdict(e) for e in examples], "keys": keys},
        ensure_ascii=False,
        sort_keys=True,
    ).encode()
    return Dataset(examples, keys, digest(serialized))


def matrix(
    dataset: Dataset,
    repeats: int = 5,
    seed: int = 20261016,
    block: str = "all",
    provider: str = "all",
    model: str = "all",
) -> tuple[list[Trial], list[Trial]]:
    if repeats < 1:
        raise ValueError("Repeats must be positive")
    conditions = [
        (e, mode)
        for e in dataset.examples
        for mode in MODES
        if (block == "all" or e.block == block)
        and (provider == "all" or Trial(e.id, mode, 0).provider == provider)
        and (model == "all" or mode.startswith(model + "-"))
        and (e.block != "wording" or mode.endswith("text"))
    ]
    if not conditions:
        raise ValueError("Empty experiment matrix")
    required = {(e.language, mode) for e, mode in conditions}
    warmups = [Trial(f"original-{lang}", mode, 0, "warmup") for lang, mode in sorted(required)]
    rng = random.Random(seed)
    schedule = []
    # Each repetition contains every selected condition exactly once.
    for repetition in range(1, repeats + 1):
        round_trials = [Trial(e.id, mode, repetition) for e, mode in conditions]
        rng.shuffle(round_trials)
        schedule.extend(round_trials)
    return warmups, schedule
