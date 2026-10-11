# Jev: English text comprehension test

The complete English adaptation of a small language-comprehension experiment: one passage, nine questions, and four answer choices per question. The wording is preserved from the original English test, including “Marko was almost late”.

## How to reproduce

In the TypeSafe Playground, paste the JSON from **State** into the **State** field and the JSON from **Questions** into the **Questions** field. The original screenshots show the model name `jev-latest`; an exact model version was not recorded.

**Do not include the answer key, explanations, or recorded results in the model input.** They are provided only for checking the output.

## State

```json
{
  "text": "Marko was almost late for the internal meeting, while Olena arrived twenty minutes after the agreed time. “Olena, you're the very model of punctuality!” he said, glancing at his watch. “I didn't get around to reading the email about the time change yesterday,” she explained. Olena was asked by Marko to revise the conclusions: it wasn't the figures in the report that concerned him, but the overly bold generalizations. “Don't rewrite the whole report: change only the last paragraph,” he clarified. Olena did not consider all of Marko's comments valid, but she did not argue. They decided to put off the meeting with the client until Friday, not cancel it. “The client is unlikely to be pleased,” Olena remarked. They had not yet received his reply."
}
```

## Questions

```json
{
  "q1": {
    "type": "choice",
    "instructions": "Who was late for the internal meeting, according to the text?",
    "criteria": {
      "a": "Both Marko and Olena.",
      "b": "Marko was late, but Olena was not.",
      "c": "Olena was late, but Marko was not.",
      "d": "Neither Marko nor Olena."
    }
  },
  "q2": {
    "type": "choice",
    "instructions": "What did Marko most likely mean by saying “you're the very model of punctuality”?",
    "criteria": {
      "a": "He was ironically criticizing Olena for being late.",
      "b": "He was sincerely praising Olena for arriving on time.",
      "c": "He was thanking Olena for reminding him of the meeting time.",
      "d": "He was holding Olena up as an example for the other attendees to follow."
    }
  },
  "q3": {
    "type": "choice",
    "instructions": "What does Olena mean by saying she “didn't get around to reading the email”?",
    "criteria": {
      "a": "She read the email but disagreed with the change of time.",
      "b": "She could not open the email because of a technical fault.",
      "c": "She had not received the email about the time change.",
      "d": "She had not made time to read the email."
    }
  },
  "q4": {
    "type": "choice",
    "instructions": "Who asked whom to revise the conclusions?",
    "criteria": {
      "a": "Olena asked Marko.",
      "b": "Marko asked Olena.",
      "c": "The client asked Marko.",
      "d": "Olena asked the client."
    }
  },
  "q5": {
    "type": "choice",
    "instructions": "What specifically concerned Marko about the report?",
    "criteria": {
      "a": "Errors in the numerical data.",
      "b": "Conclusions that went too far.",
      "c": "An insufficient amount of numerical data.",
      "d": "Conclusions that were too cautious and tentative."
    }
  },
  "q6": {
    "type": "choice",
    "instructions": "Which action would comply with Marko's clarification about editing the report?",
    "criteria": {
      "a": "Edit only the final paragraph, leaving the rest of the text unchanged.",
      "b": "Rewrite the entire report, starting with the last paragraph.",
      "c": "Correct only the figures without changing the conclusions.",
      "d": "Leave the entire report unchanged."
    }
  },
  "q7": {
    "type": "choice",
    "instructions": "What necessarily follows from the statement “Olena did not consider all of Marko's comments valid”?",
    "criteria": {
      "a": "She considered every comment valid.",
      "b": "She considered none of the comments valid.",
      "c": "There was at least one comment she did not consider valid.",
      "d": "She had not yet formed an opinion about any of the comments."
    }
  },
  "q8": {
    "type": "choice",
    "instructions": "What did they decide to do about the meeting with the client?",
    "criteria": {
      "a": "Cancel the meeting altogether.",
      "b": "Reschedule the meeting for Friday.",
      "c": "Arrange an additional meeting on Friday without changing the original one.",
      "d": "Hold the meeting earlier than originally planned."
    }
  },
  "q9": {
    "type": "choice",
    "instructions": "Which conclusion about the client's reaction is supported by the text?",
    "criteria": {
      "a": "The client has already expressed dissatisfaction with the postponement.",
      "b": "The client will definitely be unhappy about the postponement.",
      "c": "The client has already agreed to the postponement.",
      "d": "The client's response is not yet known; Olena doubts that he will be pleased."
    }
  }
}
```

## Answer key

These are the expected choices for the original passage, not an example of the API response structure.

```json
{
  "q1": "c",
  "q2": "a",
  "q3": "d",
  "q4": "b",
  "q5": "b",
  "q6": "a",
  "q7": "c",
  "q8": "b",
  "q9": "d"
}
```

| Question | Answer | What it tests |
| --- | --- | --- |
| `q1` | `c` | “Almost late” means Marko avoided being late; only Olena was late. |
| `q2` | `a` | An ironic criticism phrased as praise for punctuality. |
| `q3` | `d` | The idiom “didn't get around to”: Olena had not made time to read the email. |
| `q4` | `b` | Agent and recipient roles in a passive construction: Marko asked Olena. |
| `q5` | `b` | Paraphrasing “overly bold generalizations” as conclusions that went too far, and the “not X, but Y” contrast. |
| `q6` | `a` | The restriction “only”, and the equivalence of “last” and “final” in this context. |
| `q7` | `c` | “Not all” does not mean “none”: at least one comment was not considered valid. |
| `q8` | `b` | “Put off” / “reschedule”, as opposed to cancellation. |
| `q9` | `d` | Olena's expectation is not an established fact about the client's reaction. |

## Controlled changes to the first sentence

Replace only the opening below. Keep the continuation “, while Olena arrived…”, the rest of the passage, and all questions unchanged. The answer key for `q2`–`q9` stays the same.

| Opening of the passage | Expected answer to `q1` |
| --- | --- |
| Marko was almost late for the internal meeting | `c` — only Olena |
| Marko was actually late for the internal meeting | `a` — both |
| Marko barely made it to the internal meeting on time | `c` — only Olena |
| Marko was a little late for the internal meeting | `a` — both |

These are expected answers, not a claim that all four variants were run. Recorded observations are listed separately below.

## Recorded results

The results were transcribed from the experiment screenshots; they are not new model runs performed when preparing these files.

For the original passage, the model selected `a, a, d, b, b, a, c, b, d`: **8 out of 9 correct**, with `q1` as the only error.

| Opening variant | Expected | Jev's choice | Percentage displayed next to the selected choice | `Confidence` field |
| --- | --- | --- | --- | --- |
| “Was almost late” | `c` | `a` — incorrect | 73% | 63% |
| “Was a little late” | `a` | `a` — correct | 99% | 98% |
| “Barely made it … on time” | `c` | `c` — correct | 84% | 78% |

In the original run, the correct choice `c` for `q1` was shown at 27%. All choices for `q2`–`q9` were correct; the interface displayed 100% next to each selected choice and `Confidence: 100%`.

The partial screenshots for the “a little late” and “barely made it … on time” variants also show correct choices for `q2 = a` and `q3 = d`. Their answers to `q4`–`q9` are not visible in those screenshots. No result for the “actually late” variant was supplied.

Percentages are reported as displayed by the interface. They are not independently measured correctness rates; a displayed 100% is not a guarantee of correctness.

## Limitations

This is a diagnostic example, not a representative benchmark. The nine questions concern a single passage, and some repeat the relevant wording in the question itself. One such result does not establish overall language proficiency.

The corresponding Ukrainian test also produced 8/9 with an error on `q1`, involving “ледь не запізнився”. This is evidence that the observed failure is not limited to the Ukrainian wording; it does not establish equal overall performance across the two languages. The English version is an adaptation rather than a grammatically identical translation: in particular, the Ukrainian case-marked construction in `q4` is replaced by an English passive.
