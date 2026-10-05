# ADR 0001: the shape of one run

**Filled by:** session 10, for the choice measured in session 8.

- Status: accepted
- Date: 2026-10-05

## Context

We needed a deterministic request boundary that balances speed with tool-calling
capabilities. Session 8 measurements showed a strict chain costs exactly one
model call but fails on missing data, while an unconstrained graph can spin
indefinitely. A loop with a strict budget costs one to three calls and provides
a safe fallback.

## Decision (`decision`)

We keep the loop architecture with a strict tool-call budget in `agent.py`.

## Options considered (`options_considered`)

1. A bounded loop with a maximum of three tool calls.
2. A static chain with one fixed retrieval call.

## Why not the other option (`why_not`)

The static chain cannot recover from an empty initial retrieval or adapt to
multi-step requests.

## What would reverse it (`reverses_it`)

When a question needs more than three model calls to fetch sufficient context
in 15 of the golden cases, requiring a budget increase.
