# Repository instructions

## Language

- Write and maintain repository documentation in English. This includes Markdown documents, generated reports, chart labels, and explanatory CLI messages.
- In chat, respond in the language the user is using.
- Preserve the original language and exact wording of experimental inputs, questions, answer choices, and immutable source snapshots in `data/source/`. These are research data, not authored documentation; translating them would change the experiment or its provenance.
- Keep LinkedIn post drafts in chat, outside the repository. Their language follows the user's request.

## Experiment integrity

- Keep answer keys separate from model inputs. Never include expected answers or historical results in API requests or PNG metadata.
- Freeze inputs before live runs; retain failed requests, refusals, unknown usage, and incomplete-run status.
- Never log API keys, authorization headers, or inline base64 images. Keep `.env` and local runs out of Git.
- Preserve user edits. Do not change the experiment matrix or substitute models without recording and explaining the change.

## Tooling

Use Python 3.14, uv with the committed lockfile, ruff, ty, and pytest. Before handing off code changes, run:

```sh
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked ty check
uv run --locked pytest -q
```

## Current library documentation

Use Context7 MCP whenever a task asks about a library, framework, SDK, API, CLI tool, or cloud service, including syntax, configuration, migrations, setup, and library-specific debugging. Prefer it over web search for library documentation, even when the answer seems familiar.

1. Start with `resolve-library-id`, providing the library name and the actual question, unless an exact `/org/project` ID was supplied.
2. Select the best match by name, relevance, source reputation, snippet coverage, and benchmark score. Use a version-specific ID when a version was requested; refine the lookup when results are unsuitable.
3. Call `query-docs` with the selected ID and a specific, complete question.
4. Base the implementation or answer on the retrieved documentation.

Context7 is not required for ordinary refactoring, business-logic debugging, code review, scripts written from scratch without library-specific questions, or general programming concepts.
