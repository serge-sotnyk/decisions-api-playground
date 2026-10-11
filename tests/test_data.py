import json
import re
from collections import Counter
from dataclasses import asdict

from decisions_playground.data import ROOT, load_dataset, matrix


def test_originals_match_pinned_gist_exactly():
    data = load_dataset()
    for language, filename in (("uk", "ukrainian"), ("en", "english")):
        source = (ROOT / f"data/source/jev-{filename}.md").read_text()
        state, questions, key = [
            json.loads(b) for b in re.findall(r"```json\s*\n(.*?)```", source, re.S)
        ]
        original = next(e for e in data.examples if e.id == f"original-{language}")
        assert original.text == state["text"]
        assert {
            q.id: {"type": "choice", "instructions": q.instructions, "criteria": q.choices}
            for q in original.questions
        } == questions
        assert data.answer_keys[original.id] == key
        assert len(original.questions) == 9
        for slug, answer in (("almost", "c"), ("actually", "a"), ("barely", "c"), ("little", "a")):
            example = next(e for e in data.examples if e.id == f"{slug}-{language}")
            assert example.text.split(",", 1)[1] == original.text.split(",", 1)[1]
            assert example.questions == original.questions[:1]
            assert data.answer_keys[example.id] == {"q1": answer}


def test_matrix_counts_and_balanced_reproducible_rounds():
    data = load_dataset()
    warmups, schedule = matrix(data)
    assert len(warmups) == 8
    assert len(schedule) == 480
    blocks = {e.id: e.block for e in data.examples}
    assert Counter(blocks[t.example_id] for t in schedule) == {
        "original": 80,
        "wording": 160,
        "traps": 240,
    }
    assert all("png" not in t.mode for t in schedule if blocks[t.example_id] == "wording")
    assert len(set((t.example_id, t.mode) for t in schedule[:48])) == 48
    assert Counter(t.repetition for t in schedule) == dict.fromkeys(range(1, 11), 48)
    assert schedule == matrix(data)[1]
    assert schedule != matrix(data, seed=1)[1]
    assert len(matrix(data, provider="jev")[1]) == 160
    assert len(matrix(data, provider="openai")[1]) == 320
    assert len(matrix(data, block="wording")[0]) == 4


def test_gold_answers_are_separate_from_inputs():
    data = load_dataset()
    for example in data.examples:
        assert "expected" not in asdict(example)
        assert "answer_keys" not in asdict(example)
    assert len([e for e in data.examples if e.block == "traps"]) == 6
