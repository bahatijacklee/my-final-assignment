# Ranked issues

The issues below are ranked by their impact on whether a supported question
receives a useful, grounded answer.

| rank | issue | impact |
|---:|---|---|
| 1 | Lexical retrieval misses paraphrases with no word overlap. | A user who asks in their own words can receive a refusal for a question the corpus supports. |
| 2 | The model can make unsupported claims or choose imprecise citations. | Users may receive a fluent answer that is not fully grounded in the cited documents. |
| 3 | Local provider latency can exceed the default request deadline. | A cold or busy model can produce a timeout refusal even when the question is supported. |

## Rank 1, in progress

- The likely fix: add semantic or hybrid retrieval while preserving the
  read-only corpus boundary.
- The regression test: add a paraphrased supported question whose keywords do
  not exactly match the source wording.
- Current evidence: the Ollama practice run scored 5/10; see
  [EVAL_REPORT.md](EVAL_REPORT.md).
