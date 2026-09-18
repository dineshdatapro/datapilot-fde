# Design decisions

Given the 4–6 hour constraint, the prototype prioritizes **correctness and explainability over breadth**.

## Why the LLM plans instead of calculating

Language models are strong at mapping a question onto columns and operations, and weak at arithmetic over thousands of rows. DataPilot treats the model as a **semantic query planner**. It may only emit a structured `AnalyticalPlan`. Pandas is the only component allowed to produce numbers. That split is the product: answers can be verified, not merely generated.

## Why Pandas is the source of truth

Uploaded files become DataFrames in an in-memory session. Aggregations, filters, joins, rankings, and percentage change all run through explicit Pandas calls. If the plan is valid, the result is deterministic for the same files. If the plan is invalid, we refuse to execute it. The explanation LLM sees **already-formatted numbers** and is instructed not to rewrite them.

## How multi-file analysis works

Each file is profiled independently (types, samples, missingness). Compatible identifier columns are scored for name match and value overlap. The engine concatenates same-shaped sales files (January + February) and **joins only when needed**: the metric lives on one dataset, the group key on another, and a detected relationship (or an explicit join in the plan) connects them. We do not cartesian-join every upload.

## How schema validation reduces hallucination

Before any computation, the plan is checked against real filenames and columns: operations, metrics, group-by fields, filters, numeric vs date usage, and join keys. Missing fields return the available numeric columns. Filter values that do not appear in the data are rejected (`Mumbai` vs `city`). Malformed JSON never reaches Pandas.

## Why this is not a generalized agent

A tool-calling Python agent would expand the demo surface and the failure surface at the same time: arbitrary code, unbounded joins, and answers that cannot be explained as `SUM(revenue)`. The supported operation list is the product contract. Users see files used, rows analyzed, operation, grouping, and a **Verified against uploaded data** badge so the trust layer is visible, not implied.

## What would be built next

Persisted sessions, richer time intelligence, user-confirmed joins, export of the analysis trail, and a local fallback planner when no Ollama Cloud key is configured. Not accounts, RAG, or an enterprise permission model.
