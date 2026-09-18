# DataPilot

Natural-language Q&A over uploaded CSV/Excel files, with **Pandas as the source of truth** and an LLM used only as a query planner and narrator.

This repository is a **Darwinbox Forward Deployed Engineer (FDE) take-home**. The goal is a scoped, demo-ready prototype that a reviewer can upload data into, ask a question, and immediately see *how* the number was produced — not a general-purpose agent platform.

AI coding tools (**Cursor**) were used to move faster on boilerplate and UI. The work that matters here is **problem scoping, architecture, and the trust boundary between language models and deterministic analytics**.

---

## Project Overview

Spreadsheet “ask the AI” products often send rows (or summaries) to a model and hope the arithmetic is correct. That fails on multi-file questions, large totals, and any check an FDE would do on a customer call.

DataPilot inverts that:

| Role | Component | Responsibility |
| --- | --- | --- |
| Semantic layer | Ollama Cloud (`gpt-oss:120b`) | Map a question onto a structured `AnalyticalPlan` JSON; later, phrase an already-computed result |
| Contract | Pydantic `AnalyticalPlan` | Closed set of operations; malformed JSON never reaches Pandas |
| Gate | `validate_plan()` | Columns, files, joins, numeric vs date usage, filter values against real data |
| Source of truth | `execute_plan()` (Pandas) | Aggregations, filters, concatenations, joins, rankings, percentage change |
| Presentation | Visualization selector + React/Recharts | KPI, bar, horizontal bar, line, pie, or table — only when it adds information |

The planner receives a **schema profile** (column names, semantic types, samples, row counts) and detected relationships — not the raw datasets.

```
Upload CSV / XLSX / XLS
        │
        ▼
Profile + relationship detection  ──►  in-memory session
        │
Question ──► LLM planner ──► JSON plan ──► validator
                                      │
                                      ▼
                              Pandas engine
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              structured         chart spec         LLM explanation
              result             (Recharts)         (numbers already fixed)
                    │
                    ▼
         Answer + verified badge + “how this was calculated”
```

---

## Features

Implemented in this repo (not aspirational):

**Ingestion**
- Multi-file upload in one session (picker, drag-and-drop, add-more)
- `.csv`, `.xlsx`, `.xls`; 10 MB per-file cap; filename sanitization; temp files
- Rejection of empty files, unreadable spreadsheets, and files without headers
- Duplicate filename handling within a session
- **Load demo data** (`POST /api/demo`) for a one-click review path

**Profiling & multi-file reasoning**
- Per-file profile: row/column counts, dtypes, missing/unique counts, sample values
- Semantic types: numeric, categorical, date/datetime, boolean, text, identifier
- Derived calendar columns (`month`, `year`, `month_name`) when a parseable date column exists
- Conservative join candidates: name match + identifier semantics + value overlap (same-shaped sales files are **not** treated as a join; they concatenate)

**Q&A pipeline**
- Natural-language questions → structured plan → validation → Pandas execution
- Closed operations: `total`, `sum`, `average`, `count`, `minimum`, `maximum`, `filter`, `group_by`, `comparison`, `trend`, `top_n`, `bottom_n`, `percentage_change`, `cross_file_join`
- Cross-file example: revenue on sales files + `segment` on `customers.csv` via `customer_id` (explicit plan join or inferred from detected relationships)
- No execution of model-generated Python or shell

**Trust layer (visible in the UI)**
- “Verified against uploaded data”
- Files used, rows analyzed, operation (e.g. `SUM(revenue)`), grouping, filters
- Copy explaining that Pandas computed the numbers; the model planned and narrated

**Visualization & formatting**
- Automatic chart type from operation/result (KPI, bar, horizontal bar, line, pie, table)
- For `top_n` with `limit=1`, the answer uses the top row; the chart can still show the ranked set
- Indian grouping / compact INR (`₹`, L, Cr) when the metric looks like currency

**Product UX**
- Empty state, query loading stages, user-facing errors (no stack traces)
- If Ollama Cloud is unreachable or `OLLAMA_API_KEY` is unset: datasets remain inspectable; asking a question returns a setup message
- Health endpoint reports API + model reachability

---

## Architecture

### Query path


flowchart TD
  Q[User question] --> P[LLM planner]
  P --> J[JSON AnalyticalPlan]
  J --> V[validate_plan]
  V -->|invalid| E[Typed error to UI]
  V -->|valid| X[execute_plan Pandas]
  X --> C[select_visualization]
  X --> A[LLM explanation on formatted numbers]
  C --> UI[Answer + chart + analysis trail]
  A --> UI
```

### Backend layout

| Path | Role |
| --- | --- |
| `backend/app/routes/upload.py` | Upload, demo load, session get/reset, file delete |
| `backend/app/routes/query.py` | Orchestrates plan → validate → execute → viz → explain |
| `backend/app/services/file_processor.py` | Parse CSV/Excel, date enrichment |
| `backend/app/services/schema_profiler.py` | Column semantics for the planner |
| `backend/app/services/relationship_detector.py` | Pairwise join hypotheses |
| `backend/app/services/llm_planner.py` | Official `ollama` Python client against Ollama Cloud (`https://ollama.com`) |
| `backend/app/services/validator.py` | Schema/file/join/filter-value checks |
| `backend/app/services/analytics_engine.py` | Deterministic execution |
| `backend/app/services/visualization.py` | Chart type selection |
| `backend/app/services/answer_generator.py` | Narration + deterministic fallback sentence |
| `backend/app/services/session_store.py` | In-memory sessions and DataFrames |
| `backend/app/models/schemas.py` | Pydantic contracts |
| `backend/app/utils/formatting.py` | Number/currency/filename helpers |

### Session model

Uploads live as Pandas DataFrames in process memory, keyed by `session_id`. There is **no** Postgres, Redis, vector store, or auth. That is intentional for a 4–6 hour prototype: the interesting failure modes are hallucination and bad joins, not session persistence.

### Multi-file strategy

1. Profile each file independently.
2. Detect `customer_id`-style links with overlap ratios (shown in the sidebar as “Potential relationship detected”).
3. Concatenate files that share the metric (e.g. January CSV + February XLSX on `revenue`).
4. Join **only** when the metric and the group key live on different files *and* a relationship (or an explicit `join` on the plan) connects them.

### API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/upload` | Multipart files + optional `session_id` |
| `POST` | `/api/demo` | Load bundled sample datasets |
| `GET` | `/api/session/{session_id}` | Profiles + relationships |
| `DELETE` | `/api/session/{session_id}` | Clear session files |
| `DELETE` | `/api/session/{session_id}/files/{file_id}` | Remove one file |
| `POST` | `/api/query` | `{ session_id, question }` |
| `GET` | `/api/health` | Process + Ollama reachability |

---

## Tech Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | React 18, TypeScript, Vite, Tailwind, Recharts, Lucide | Fast local demo; charts are first-class, not screenshots |
| Backend | FastAPI, Pydantic v2, Pandas, openpyxl, xlrd, httpx | Typed plans, spreadsheet I/O, async LLM calls |
| AI | Ollama Cloud via the official Python client (`gpt-oss:120b`) | Bearer `OLLAMA_API_KEY`; no local daemon |
| Runtime | In-memory sessions; optional Docker Compose | No infrastructure tax for a take-home |

---

## Setup Instructions

### Prerequisites

- Python 3.11+ (developed against 3.12)
- Node 20+
- An [Ollama Cloud](https://ollama.com) API key for Q&A (uploads and profiling work without it)

### Sample data

`sample_data/` is generated by `scripts/generate_sample_data.py` (seeded): ~2,200 January orders (CSV), ~2,400 February orders (XLSX), ~800 customers. `customer_id` overlaps so join questions work.

```bash
cd backend
python ../scripts/generate_sample_data.py
```

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env    # or: cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health: `GET http://localhost:8000/api/health`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: `http://localhost:5173` (Vite proxies `/api` → `localhost:8000`).

### Ollama Cloud

Planning and explanations call **Ollama Cloud**, not a local Ollama process. Create an API key at [ollama.com](https://ollama.com) and put it in `backend/.env`:

```
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL=gpt-oss:120b
OLLAMA_API_KEY=your_key_here
MAX_UPLOAD_BYTES=10485760
```

The backend uses the official client the same way as Ollama’s cloud docs:

```python
from ollama import Client

client = Client(
    host="https://ollama.com",
    headers={"Authorization": "Bearer " + os.environ["OLLAMA_API_KEY"]},
)
client.chat("gpt-oss:120b", messages=messages, stream=True)
```

Plans use `format="json"` so the validator gets a complete object; explanations stream chunks and concatenate them. There is no `ollama pull` and no `localhost:11434`.

If the key is missing or Cloud is unreachable, you can still upload files and inspect profiles. Asking a question returns a setup message pointing at `OLLAMA_API_KEY`.

### Docker

```bash
cp .env.example backend/.env
docker compose up --build
```

UI `http://localhost:8080` · API `http://localhost:8000`. The API container reads `OLLAMA_API_KEY` from `backend/.env` and talks to `https://ollama.com`.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `https://ollama.com` | Ollama Cloud origin |
| `OLLAMA_MODEL` | `gpt-oss:120b` | Cloud planner / explainer |
| `OLLAMA_API_KEY` | empty | Required Bearer token for Cloud |
| `MAX_UPLOAD_BYTES` | `10485760` | Per-file upload limit |
| `VITE_API_URL` | empty | Frontend API origin; empty uses the Vite/nginx proxy |

---

## Demo Questions

Click **Load demo data**, then:

1. What is the total revenue across all files?
2. Which region generated the highest revenue?
3. Compare January and February revenue.
4. What are the top 5 products by revenue?
5. Show the revenue trend by month.
6. Which customer segment generated the most revenue?
7. What is the average order value?
8. Which cities generated more than ₹1 lakh in revenue?

Suggested checks as a reviewer: (1) totals come from Pandas, not the prompt; (2) segment questions join `customers.csv`; (3) missing columns and invented cities are refused with available fields / actual values.

---

## Key Design Decisions

Longer write-up: [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md). Short version:

**LLM plans; it does not calculate.** Models are reliable at mapping “highest region” onto `group_by` + `sum(revenue)` + `limit=1`. They are unreliable at summing thousands of rows. The product contract is a JSON plan, not a Python sandbox.

**Validate before execute.** Invented columns, non-numeric metrics, missing files, and filter values that do not appear in the data (`Mumbai` vs `city`) fail closed. The user gets a useful error instead of a confident wrong chart.

**Joins are conservative.** Over-joining is worse than asking the user to rephrase. The engine concatenates compatible fact tables and joins dimensions only when the plan requires a column that does not live on the metric files.

**Explainability is a feature, not a footer.** Files, row counts, `SUM(revenue)`, grouping, and a verified badge are what make this demoable to a skeptical operator.

**Closed operation set over an agent.** A tool-calling “write Pandas” agent would widen the demo *and* the failure surface. The operation list is the product boundary.

**Given a 4–6 hour constraint, the prototype prioritizes correctness and explainability over breadth.**

---

## Engineering Trade-offs

| Chose | Over | Rationale |
| --- | --- | --- |
| In-memory sessions | Postgres / Redis | Persistence is not the evaluation axis; restart drops uploads (documented) |
| Ollama Cloud (`ollama` Client + Bearer key) | Local Ollama daemon / `ollama pull` | Matches Cloud API usage; no GPU or local model install for reviewers |
| Schema-to-LLM, not rows | RAG / embedding the CSV | Arithmetic must not depend on retrieval chunks |
| Pydantic plan + Pandas | `exec` of model code | Security and auditability |
| Heuristic relationship detection | User-defined join UI | Enough for the demo schema; false-positive joins are filtered by overlap |
| Time derived as month/year | Full grain engine | `time_grain` exists on the plan; execution uses date columns and derived month fields |
| UI loading stages as timed UX | Streaming the four backend phases | Backend is a single `/api/query` call; stages communicate progress without a websocket |
| Fallback narration if explain fails | Blocking the answer | Numbers still show; copy degrades gracefully |

**Known limits (honest):** no auth; sessions die with the process; pie/bar heuristics are rule-based; explanation prose quality depends on the model, **totals do not**.

---

## Future Improvements

If this were a customer deployment, next (in order):

1. **Rule-based fallback planner** when the Cloud key is missing, for the eight demo questions
2. **User-confirmed joins** when overlap is medium
3. **Persisted sessions** and export of the analysis trail (plan + Pandas result)
4. Richer time grains and comparison of arbitrary periods
5. Still not: accounts, RAG, vector DBs, or a generalized coding agent

---

## Author

**Dinesh** — Darwinbox Forward Deployed Engineer take-home.

This project is scoped the way I would scope a short on-site: pick a trust problem customers actually hit (numbers from a model), ship a thin vertical that can be demoed in 30 seconds, and make the engineering boundary visible in the UI.

Cursor was used as an accelerator. Architecture, what *not* to build, and the planner/validator/engine split are the submission.
