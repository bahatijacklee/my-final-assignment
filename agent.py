"""Your capstone agent: the one your README demos and your CI grades.

It starts as the final assignment's starter, unchanged: the same `YourAgent`,
the same `answer_question` pipeline from the course package, the same budget.
Calling it returns a `bootcamp_agent.schema.ResearchAnswer`, the contract the
whole course used, so everything you built in the sessions plugs in here.
`run(question)` returns the whole `AgentResult`, trace included, which is what
`uv run bootcamp capstone trace "<question>"` prints.

As shipped it is honest and insufficient. On the offline `FakeLLM` it refuses
what it should refuse and answers nothing else, and some contract tests in
`tests/test_contract.py` are marked as expected failures on purpose. Making them
pass is the work. What to add, session by session, is in `docs/` (each file
names the session that fills it).

The provider comes from `.env` (`BOOTCAMP_PROVIDER`), and falls back to the
offline `FakeLLM`. Keys live only in `.env`, which git ignores.
"""

from __future__ import annotations

import concurrent.futures
import re
from dataclasses import replace
from pathlib import Path

from bootcamp_agent.agent import AgentResult, TraceEvent, answer_question
from bootcamp_agent.config import load_settings
from bootcamp_agent.documents import Document, load_corpus
from bootcamp_agent.llm import LLMClient, get_client
from bootcamp_agent.schema import ResearchAnswer
from bootcamp_agent.tools import Tool, build_tools

#: The six course documents, copied in by `bootcamp capstone new`. Versioned
#: input: nothing you build writes to it.
CORPUS_DIR = Path(__file__).resolve().parent / "data" / "corpus"


def _flagged_refusal(message: str) -> ResearchAnswer:
    return ResearchAnswer(
        answer=message,
        citations=(),
        confidence=0.0,
        needs_human_review=True,
    )


class GroundingClient:
    """Add local grounding constraints without changing the provider client."""

    _GUIDANCE = (
        "\n\nAdditional grounding requirements: make every factual claim directly "
        "traceable to the context; cite only document IDs that support the answer; "
        "answer every supported part of the question concisely; if any part is not "
        "supported, refuse instead of filling gaps from memory."
    )

    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def complete(self, system: str, user: str) -> str:
        return self.client.complete(system=system + self._GUIDANCE, user=user)


def _apply_grounding_gate(
    result: AgentResult,
    allowed_doc_ids: set[str],
) -> AgentResult:
    """Reject answers that cannot be safely tied to retrieved corpus documents."""
    answer = result.answer
    invalid_citations = set(answer.citations) - allowed_doc_ids
    answer_is_unverifiable = not answer.answer.strip() or (
        not answer.needs_human_review and not answer.citations
    )
    if not invalid_citations and not answer_is_unverifiable:
        return result

    reason = (
        "answer contained an invalid citation"
        if invalid_citations
        else "answer could not be grounded in retrieved sources"
    )
    return AgentResult(
        answer=_flagged_refusal(
            "I could not verify that answer against the available sources."
        ),
        trace=result.trace + (TraceEvent("decision", f"{reason}; flagged refusal"),),
    )


class MemoryStore:
    """Bounded, user-scoped storage for explicit preferences."""

    def __init__(self, max_items_per_user: int = 10) -> None:
        if max_items_per_user < 1:
            raise ValueError("max_items_per_user must be positive")
        self.max_items_per_user = max_items_per_user
        self._values: dict[str, dict[str, str]] = {}

    def remember(self, user_id: str, key: str, value: str) -> None:
        user_values = self._values.setdefault(user_id, {})
        user_values[key] = value
        while len(user_values) > self.max_items_per_user:
            del user_values[next(iter(user_values))]

    def recall(self, user_id: str, key: str) -> str | None:
        return self._values.get(user_id, {}).get(key)

    def reset(self, user_id: str) -> None:
        self._values.pop(user_id, None)


class YourAgent:
    """The agent the tests and the grader run. Make it yours."""

    #: How long one provider call may take before the agent gives up with a
    #: flagged refusal. The local Ollama lane can need more than 30 seconds
    #: for a full retrieval prompt on first load; tests override this value.
    timeout_s: float = 120.0

    def __init__(self, client: LLMClient | None = None) -> None:
        self.documents: list[Document] = load_corpus(CORPUS_DIR)
        self.client: LLMClient = client if client is not None else get_client(load_settings())
        # Every tool the agent can reach. Session 4's registry, read-only by
        # construction; session 12 has you classify each one, and the `tools`
        # contract test refuses anything not classified as a reader.
        self.tools: dict[str, Tool] = build_tools(self.documents, self.client)

    def run(self, question: str) -> AgentResult:
        """One question, answered or refused, with the trace of how."""
        if not question.strip():
            return AgentResult(
                answer=_flagged_refusal("Question cannot be empty."),
                trace=(TraceEvent("decision", "empty question; flagged refusal"),),
            )

        def _execute() -> AgentResult:
            return answer_question(
                question,
                self.documents,
                GroundingClient(self.client),
                max_tool_calls=3,
                top_k=3,
            )

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(_execute)
        try:
            result = future.result(timeout=self.timeout_s)
            result = _apply_grounding_gate(
                result,
                {document.doc_id for document in self.documents},
            )

            injection_pattern = re.compile(r"ignore previous instructions", re.IGNORECASE)
            cited_docs = [doc for doc in self.documents if doc.doc_id in result.answer.citations]
            if any(injection_pattern.search(doc.text) for doc in cited_docs):
                result = AgentResult(
                    answer=replace(
                        result.answer,
                        confidence=0.0,
                        needs_human_review=True,
                    ),
                    trace=result.trace
                    + (
                        TraceEvent(
                            "decision",
                            "instruction-shaped retrieved text; flagged for human review",
                        ),
                    ),
                )

            return result

        except concurrent.futures.TimeoutError:
            return AgentResult(
                answer=_flagged_refusal("Request timed out."),
                trace=(TraceEvent("decision", "provider timeout; flagged refusal"),),
            )
        except ConnectionError:
            return AgentResult(
                answer=_flagged_refusal(
                    "The answer could not be retrieved from the model provider."
                ),
                trace=(TraceEvent("decision", "provider error; flagged refusal"),),
            )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def __call__(self, question: str) -> ResearchAnswer:
        return self.run(question).answer
