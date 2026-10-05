# my-final-assignment

This agent answers developer questions about retrieval, agent loops, MCP, prompt
injection, structured outputs, and evaluation using six versioned course
documents. It retrieves relevant passages, asks a model for a structured answer,
checks citations and safety boundaries, and flags a refusal when the corpus does
not support an answer.

## The problem

Developers learning to build reliable AI agents need concise answers grounded in
the course material, but a general-purpose model may invent details, follow
instructions hidden inside retrieved text, or answer questions outside the
available sources. This agent gives learners a source-backed research assistant
for the six course topics, names its supporting documents, and produces a
human-reviewable refusal when evidence is missing or unsafe.

## Demo

Two runs, pasted exactly as the commands printed them. Never an edited one.
`trace` prints every step the agent took, then the answer.

### One supported answer

```bash
uv run bootcamp capstone trace "How does chunking work in RAG?"
```

```text
[retrieve] top_k=3 -> [('rag-basics', 1), ('rag-basics', 2), ('evaluation-basics', 0)]
[llm_call] attempt 1: 280 chars
[decision] answered with citations ['rag-basics']

answer: Chunking in RAG splits documents into passages that are small enough to be individually relevant, respecting paragraph boundaries instead of cutting at a fixed character count mid-sentence.
citations: ['rag-basics']
confidence: 1.0
needs_human_review: False
```

### One refusal

```bash
uv run bootcamp capstone trace "What is the capital city of Mongolia?"
```

```text
[decision] no relevant chunks; refusing without an LLM call

answer: I don't know based on the provided corpus.
citations: []
confidence: 0.0
needs_human_review: True
```

## Architecture

Each run validates the question, retrieves up to three relevant chunks, and
passes the read-only context to a bounded model pipeline. A supported question
normally costs one model call, with the course pipeline allowed a corrective
retry when structured output cannot be parsed. The result passes through
citation, answer-integrity, and prompt-injection checks; empty retrieval,
provider errors, timeouts, invalid answers, and unsafe retrieved instructions
become flagged refusals. The run shape and reversal measurement are documented
in [docs/adr/0001-run-shape.md](docs/adr/0001-run-shape.md).


## Measured results

Every number here comes from a command in this table, run on this commit. Say
which model produced it: CI has no keys, so a CI number is always the offline
fake model's.

| What | Command | Model | Result |
|---|---|---|---|
| Contract tests | `uv run pytest` | fake | `11 passed` |
| Practice grader | `uv run bootcamp capstone grade` | Ollama `qwen2.5:7b-instruct` | `score: 5/10 (50%) — pass bar 30% — NOT YET` |
| Evaluation, before and after | see [docs/EVAL_REPORT.md](docs/EVAL_REPORT.md) | fake → Ollama Qwen | `3/10 (30%) → 5/10 (50%)` |

## The honest limitation

The current limitation is that a local model can still make unsupported claims
or choose imprecise citations on multi-part questions; the next step is to
measure the post-answer grounding gate against the full practice set and
improve refusal calibration without hard-coding evaluation questions.

The full ranked list is in [docs/ISSUES.md](docs/ISSUES.md).

## How to run it

```bash
git clone https://github.com/<your-github-username>/my-final-assignment && cd my-final-assignment && uv sync && uv run pytest
```

No key needed: without a `.env` it runs on the offline fake model. For a real
model, copy `.env.example` to `.env`, fill in your provider, and
`uv sync --extra anthropic` (or `--extra openai`).

To hand in the final assignment, commit and push, then run
`uv run bootcamp capstone submit --github <you>`. It runs the practice set
first, then answers the final questions and opens the pull request.
`--dry-run` shows the bundle without handing anything in.

## Sources

The runtime uses the course-provided `bootcamp_agent` package for document
loading, retrieval, structured-answer parsing, and provider configuration.

## Rollback

If a change lowers the practice score or breaks a contract test, revert the
single implementation commit and rerun `uv run pytest` plus
`uv run bootcamp capstone grade` before proceeding.

---

| Path | What it is |
|---|---|
| `agent.py` | The agent: `YourAgent`, the class the tests, `trace` and the grader run |
| `tests/test_contract.py` | The capstone contract, as tests (`uv run pytest -k refusal`, `-k injection`, ...) |
| `data/corpus/` | The six source documents, versioned; nothing here writes to them |
| `docs/EVAL_REPORT.md` | Numbers you produced, before and after, with the command behind each |
| `docs/SKILL.md` | A skill another assistant can load (session 10) |
| `docs/adr/0001-run-shape.md` | The architecture decision and what would reverse it (session 10) |
| `docs/RETENTION.md` | What a session remembers, and what it refuses to (session 11) |
| `docs/ISSUES.md` | The ranked issue list (session 9, kept until 14) |

Built during the Dev3Pack AI Engineering bootcamp, on the course package at
commit `85ad371e3e6354fc18edb4522b1fd66ac6223f62` of https://github.com/Gecko-Academy/dev3pack-cohort-2026-09.
