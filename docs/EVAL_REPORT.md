# Evaluation report

**Filled by:** session 7 (the baseline, and the evaluator's weakness), session 9
(failures named from traces), session 14 (one fix, measured after).

Every number below has the command that produced it, the commit it ran on, and
the model. A number without its command is an impression, and this file holds
none. CI has no keys, so any number CI printed is the offline fake model's.

## Before

- model: not recorded
- commit: not recorded
- command: not recorded
- result: not recorded; no before-run output was provided

### The evaluator's weakness (session 7)

The contract suite verifies safety and refusal behavior, but it does not prove
that supported questions receive useful, grounded answers. The practice grader
exposes this gap because all seven grounded or adversarial cases failed their
citation recall, claim support, and no-review gates.

### Failures, named from traces (session 9)

| Case | Bucket | The trace line that decided it |
|---|---|---|
| fa-01 through fa-07 | citation_recall, claim_support, no_review_flag | `failed: citation_recall, claim_support, no_review_flag` |

## After

The fix for rank 1 of [ISSUES.md](ISSUES.md) (session 14), first measured
with the fake lane and then with the local Ollama lane.

- fake model: commit `84de70d`; `uv run bootcamp capstone grade`; `score: 3/10 (30%) — pass bar 30% — NOT YET`
- Ollama model: `qwen2.5:7b-instruct`; `uv run bootcamp capstone grade`; `score: 5/10 (50%) — pass bar 30% — NOT YET`
- regression test: `test_regression_rank_1_of_the_issue_list`

### What got better (session 7's `improvement`)

The local contract suite passes all 9 tests, and switching from the fake lane
to Ollama improved the practice score from 3/10 (30%) to 5/10 (50%).

### What got worse, or could (session 7's `regression_or_risk`)

The practice grader still fails five grounded or adversarial cases because Qwen
sometimes makes unsupported claims or cites imprecisely; the critical safety
gate remains failed, so the current score is not sufficient for submission.
