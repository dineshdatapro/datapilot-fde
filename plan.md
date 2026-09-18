Build a polished, production-style prototype called "DataPilot" — an AI-powered Data Q&A web application.

IMPORTANT CONTEXT:
This is a Forward Deployed Engineer take-home assignment.

The goal is NOT to build a huge AI agent or enterprise platform.

The goal is to demonstrate:
1. Good product scoping
2. Multi-file CSV/Excel analysis
3. Cross-file analytical reasoning
4. Natural-language data Q&A
5. Deterministic and trustworthy calculations
6. Useful visualizations
7. Clear explainability
8. Thoughtful engineering decisions
9. A meaningful "delta solution" beyond simply asking an LLM for an answer

The application should feel polished and demo-ready.

==================================================
PRODUCT
==================================================

Product name:
DataPilot

Tagline:
"Ask questions. Understand your data."

Description:
A simple AI-powered data analysis assistant where users upload multiple CSV or Excel files and ask analytical questions in plain English.

Example questions:

- What is the total revenue across all files?
- Which region generated the highest revenue?
- Compare January and February revenue.
- What are the top 5 products by revenue?
- Show me the revenue trend by month.
- Which customer segment generated the most revenue?
- What is the average order value?
- How many orders came from Hyderabad?
- Show revenue by region.
- Which product had the largest increase between January and February?

==================================================
CORE PRODUCT PRINCIPLE
==================================================

DO NOT let the LLM directly calculate numerical answers.

The LLM is a semantic query planner.

The deterministic analytics engine is the source of truth.

Architecture:

User question
    ↓
LLM Planner
    ↓
Structured analytical plan
    ↓
Plan validation
    ↓
Deterministic analytics engine
    ↓
Exact result
    ↓
Visualization selection
    ↓
LLM explanation
    ↓
Answer + chart + analysis details

This principle should be clearly reflected in the code and UI.

==================================================
TECH STACK
==================================================

Frontend:
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts
- Lucide icons

Backend:
- Python
- FastAPI
- Pandas
- openpyxl
- python-multipart

AI:
- Open-source LLM through Ollama
- Make the model configurable using environment variables
- Default model: gpt-oss:120b-cloud 

Storage:
- For the prototype, use in-memory session storage and temporary uploaded files.
- Do NOT add PostgreSQL, MongoDB, Redis, vector databases, authentication, or other unnecessary infrastructure.

Development:
- Include Docker support if practical.
- Include .env.example.
- Include clear local run instructions.

==================================================
UI DESIGN
==================================================

Create a clean modern SaaS-style interface.

Design principles:
- Minimal
- Professional
- Excellent typography
- Spacious layout
- Responsive
- Light mode first
- Subtle borders
- Rounded cards
- No unnecessary animations
- Avoid overly colorful gradients
- Avoid generic AI-dashboard styling

Main layout:

--------------------------------------------------
HEADER
--------------------------------------------------

DataPilot

"Ask questions. Understand your data."

Right side:
- Files indicator
- New session button

--------------------------------------------------
EMPTY STATE
--------------------------------------------------

Centered:

DataPilot

Turn your spreadsheets into answers.

Upload CSV or Excel files and ask questions about them
in plain English.

[ Upload files ]

Supported:
CSV, XLSX, XLS

Example questions:

"What was our total revenue?"
"Which region performed best?"
"Show revenue by month."

--------------------------------------------------
AFTER FILE UPLOAD
--------------------------------------------------

Use a two-column layout.

LEFT SIDEBAR:
"Data sources"

Show uploaded files:

✓ sales_january.csv
  12,482 rows
  8 columns

✓ sales_february.xlsx
  14,921 rows
  8 columns

✓ customers.csv
  8,231 rows
  5 columns

Each file should have:
- filename
- file type
- row count
- column count
- remove button

Below files:

"Data overview"

Show:
- Total rows
- Total columns
- Number of files
- Detected relationships

--------------------------------------------------
MAIN AREA
--------------------------------------------------

Top:

Ask your data

Large question input:

"Ask a question about your uploaded data..."

[ Ask ]

Below input:

Suggested questions:

[ Total revenue ]
[ Top products ]
[ Compare months ]
[ Revenue trend ]

--------------------------------------------------
ANSWER AREA
--------------------------------------------------

When a question is submitted, show:

Question

"What was the total revenue across January and February?"

Then:

Answer

"Total revenue across January and February was
₹48.6M."

Show a small badge:

✓ Verified against uploaded data

Then display visualization if appropriate.

Example:

Revenue by Month

[LINE CHART]

January       ₹21.4M
February      ₹27.2M

--------------------------------------------------
ANALYSIS DETAILS
--------------------------------------------------

Provide an expandable section:

"How this answer was calculated"

Show:

Files used:
- sales_january.csv
- sales_february.xlsx

Rows analyzed:
27,403

Operation:
SUM(revenue)

Grouping:
month

Filters:
None

This is important because it demonstrates explainability.

==================================================
FILE UPLOAD
==================================================

Support multiple files in one session.

Accepted:
- .csv
- .xlsx
- .xls

Allow:
- drag and drop
- file picker
- multiple selection

Display upload progress.

Reject unsupported file types with a clear message.

Handle:
- empty files
- malformed CSV
- invalid Excel
- files without headers
- duplicate filenames

After successful upload, automatically profile each dataset.

==================================================
SCHEMA PROFILING
==================================================

For every uploaded dataset calculate:

- filename
- row count
- column count
- column names
- data types
- missing-value counts
- unique-value counts
- sample values

Detect likely semantic types:

- numeric
- categorical
- date
- datetime
- boolean
- text
- identifier

Example:

sales_january.csv

order_id      identifier
order_date    date
customer_id   identifier
product       categorical
category      categorical
region        categorical
quantity      numeric
revenue       numeric

The schema profile is passed to the LLM instead of sending the full dataset.

==================================================
CROSS-FILE ANALYSIS
==================================================

Support multiple files.

When datasets contain compatible columns, detect potential relationships.

Example:

sales.customer_id
customers.customer_id

Display:

"Potential relationship detected"

sales.customer_id → customers.customer_id

Do NOT blindly join every file.

Only join when:
- column names strongly match, OR
- values overlap significantly, OR
- the analytical plan explicitly requires it.

The user should be able to ask:

"What is revenue by customer segment?"

The system should:
1. Identify revenue in sales
2. Identify customer_id
3. Join with customers
4. Group by segment
5. Calculate revenue

==================================================
SUPPORTED ANALYTICAL OPERATIONS
==================================================

Initially support these operations:

1. total
2. sum
3. average
4. count
5. minimum
6. maximum
7. filter
8. group_by
9. comparison
10. trend
11. top_n
12. bottom_n
13. percentage_change
14. cross_file_join

Do NOT attempt arbitrary natural-language Python execution.

==================================================
LLM PLANNER
==================================================

The LLM must convert the user's question into a structured JSON analytical plan.

Example question:

"Which region generated the highest revenue?"

Expected plan:

{
  "operation": "group_by",
  "metric": "revenue",
  "aggregation": "sum",
  "group_by": ["region"],
  "sort": "desc",
  "limit": 1,
  "filters": []
}

Example:

"Compare January and February revenue."

{
  "operation": "comparison",
  "metric": "revenue",
  "aggregation": "sum",
  "group_by": ["month"],
  "filters": []
}

Example:

"What is the average order value?"

{
  "operation": "average",
  "metric": "revenue",
  "aggregation": "mean",
  "group_by": [],
  "filters": []
}

The planner must ONLY use columns that actually exist in the schema.

Never invent:
- columns
- datasets
- values
- calculations

Return structured JSON only.

==================================================
PLAN VALIDATION
==================================================

This is a critical part of the project.

Before executing an LLM-generated plan:

Validate:

- operation exists
- metric exists
- group_by columns exist
- filter columns exist
- filter values are valid
- numeric operations use numeric columns
- date operations use date columns
- referenced files exist
- joins use valid columns

If invalid, DO NOT execute the plan.

Return a useful error.

Example:

User:
"What is the average salary?"

If salary doesn't exist:

"I couldn't answer this because no uploaded dataset contains a salary field.

Available numeric fields:
• revenue
• quantity
• discount"

Another example:

User:
"Show revenue for Mumbai."

If city exists but Mumbai doesn't:

"I found the city field, but Mumbai does not appear in the uploaded data."

==================================================
DETERMINISTIC ANALYTICS ENGINE
==================================================

Create a clean service:

analytics_engine.py

Implement functions such as:

execute_plan(plan, datasets)

aggregate()
filter_data()
group_by()
compare()
trend()
top_n()
percentage_change()
join_datasets()

All actual numerical computation must happen here using Pandas.

Never ask the LLM to calculate totals.

Example:

LLM:
SUM(revenue) GROUP BY region

Python:
df.groupby("region")["revenue"].sum()

Return structured results.

==================================================
VISUALIZATION ENGINE
==================================================

Automatically determine whether the answer should have a chart.

Rules:

TOTAL / SINGLE KPI:
KPI card

GROUP_BY:
Bar chart

TREND:
Line chart

COMPARISON:
Grouped bar chart

TOP_N:
Horizontal bar chart

PERCENTAGE:
Donut/pie where appropriate

RAW FILTERED DATA:
Table

Do not show a chart when it does not improve understanding.

Charts should use Recharts.

Charts must have:
- labels
- tooltips
- readable axes
- responsive dimensions
- proper number formatting

==================================================
ANSWER GENERATION
==================================================

After deterministic computation, send only the structured result to the LLM.

The LLM's second job is to explain the result naturally.

Example:

Raw result:

{
  "region": "South India",
  "revenue": 24800000
}

LLM explanation:

"South India generated ₹24.8M in revenue, making it the
highest-revenue region in the uploaded data."

The LLM must NOT alter the numerical result.

The UI should display:

✓ Verified against uploaded data

==================================================
DATA FORMATTING
==================================================

Format large numbers intelligently.

Examples:

1000 → 1,000

1000000 → 1,000,000

10000000 → 10,000,000

Use Indian number formatting where appropriate:

₹24,80,000

Support:
- integers
- decimals
- percentages
- currency
- dates

Attempt to infer currency from column names where reasonable,
but do not invent currency.

==================================================
SAMPLE DATA
==================================================

Create a sample_data directory.

Generate realistic demo datasets:

1. sales_january.csv
2. sales_february.xlsx
3. customers.csv

Use approximately:

sales_january:
1000–3000 rows

sales_february:
1000–3000 rows

customers:
500–1000 rows

Columns:

sales:

order_id
order_date
customer_id
product
category
region
city
quantity
revenue
discount

customers:

customer_id
customer_name
city
state
segment
signup_date

Make the data internally consistent.

customer_id values should overlap between sales and customers.

Include realistic regions:
North
South
East
West

Include realistic Indian cities:
Hyderabad
Vijayawada
Visakhapatnam
Bengaluru
Chennai
Mumbai
Delhi
Pune
Kolkata

==================================================
DEMO QUESTIONS
==================================================

Include these as clickable example questions:

1.
"What is the total revenue across all files?"

2.
"Which region generated the highest revenue?"

3.
"Compare January and February revenue."

4.
"What are the top 5 products by revenue?"

5.
"Show the revenue trend by month."

6.
"Which customer segment generated the most revenue?"

7.
"What is the average order value?"

8.
"Which cities generated more than ₹1 lakh in revenue?"

==================================================
ERROR STATES
==================================================

Design polished error handling.

Examples:

No files:

"Upload at least one CSV or Excel file before asking a question."

Invalid file:

"This file couldn't be processed. Please verify that it is a valid CSV or Excel file."

Missing column:

"The requested field wasn't found in your uploaded data."

Unsupported analysis:

"I can currently answer questions involving totals, averages,
filters, comparisons, trends, grouping, and top/bottom results."

LLM unavailable:

"AI planning is temporarily unavailable.

You can still inspect your uploaded datasets."

Never show raw stack traces to users.

==================================================
LOADING STATES
==================================================

Question processing should show stages:

Understanding your question...
↓
Checking your datasets...
↓
Running analysis...
↓
Preparing your answer...

Make this feel fast and professional.

==================================================
API DESIGN
==================================================

Create endpoints similar to:

POST /api/upload

POST /api/query

GET /api/session/{session_id}

DELETE /api/session/{session_id}/files/{file_id}

GET /api/health

Upload response:

{
  "session_id": "...",
  "files": [...]
}

Query response:

{
  "question": "...",
  "answer": "...",
  "verified": true,
  "files_used": [...],
  "rows_analyzed": 12345,
  "plan": {...},
  "result": {...},
  "visualization": {
      "type": "bar",
      "data": [...]
  }
}

==================================================
SECURITY / RELIABILITY
==================================================

For this prototype:

- Limit upload file size
- Validate extensions
- Never execute arbitrary Python generated by the LLM
- Never execute shell commands generated by the LLM
- Sanitize filenames
- Use temporary upload directories
- Never expose server stack traces
- Validate all LLM output against a schema
- Reject malformed JSON
- Use Pydantic models for plans

==================================================
DELTA SOLUTION
==================================================

Make the following visible in the application:

1. Schema profiling
2. Cross-file relationship detection
3. Structured LLM planning
4. Plan validation
5. Deterministic computation
6. Automatic visualization selection
7. Explainable analysis details
8. Verified answer badge

Add a small "Trust layer" concept.

For every answer show:

Verified against uploaded data

Files:
sales_january.csv
sales_february.xlsx

Operation:
SUM(revenue)

This is a core differentiator.

==================================================
PROJECT STRUCTURE
==================================================

Use a clean structure:

backend/

app/
    main.py

    routes/
        upload.py
        query.py

    services/
        file_processor.py
        schema_profiler.py
        relationship_detector.py
        llm_planner.py
        analytics_engine.py
        validator.py
        visualization.py
        answer_generator.py

    models/
        schemas.py

    utils/
        formatting.py

frontend/

src/
    components/
    pages/
    services/
    types/
    hooks/

sample_data/

README.md
.env.example
docker-compose.yml

==================================================
README
==================================================

Create a professional README.

Include:

# DataPilot

## Overview

## Problem

## Solution

## Architecture

## Tech Stack

## AI Architecture

Explain:

LLM = planner

Pandas = source of truth

## Supported Operations

## Cross-file Analysis

## Reliability Strategy

## Delta Solution

## Local Setup

Example:

git clone ...
cd datapilot

Backend:

cd backend
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload

Frontend:

cd frontend
npm install
npm run dev

Ollama:

ollama cloud gpt-oss:120b-cloud , api key support style

## Environment Variables

Provide .env.example.

## Demo Questions

## Limitations

## Future Improvements

==================================================
ONE-PAGE DESIGN WRITE-UP
==================================================

Create a file:

DESIGN_DECISIONS.md

Keep it approximately one page.

Explain:

1. Why the LLM is used for planning rather than computation
2. Why Pandas is the source of truth
3. How multi-file analysis works
4. How schema validation reduces hallucination
5. Why the scope intentionally excludes a generalized agent
6. What would be built next

Include this key idea:

"Given the 4–6 hour constraint, the prototype prioritizes
correctness and explainability over breadth."

==================================================
DEMO MODE
==================================================

Add a "Load demo data" button.

When clicked:
automatically load:

sales_january.csv
sales_february.xlsx
customers.csv

This makes the application easy to demonstrate.

==================================================
IMPORTANT IMPLEMENTATION PRIORITIES
==================================================

Prioritize in this order:

P0:
- Multi-file upload
- CSV/XLSX parsing
- Schema profiling
- Natural language question
- LLM structured plan
- Plan validation
- Pandas deterministic execution
- Answer rendering

P1:
- Cross-file joins
- Charts
- Explainability

P2:
- Polished empty/loading/error states
- Demo mode
- README
- Docker

Do NOT spend time on:
- Authentication
- User accounts
- Payments
- Vector databases
- RAG
- Complex agent frameworks
- Admin panels
- Cloud infrastructure
- Enterprise permissions

==================================================
QUALITY BAR
==================================================

The finished product should feel like a real small SaaS prototype,
not a coding exercise.

The first 30 seconds of the demo should clearly communicate:

1. Upload files
2. Ask a question
3. Receive an exact answer
4. See a useful visualization
5. Understand how the answer was calculated

Use clean code and meaningful names.

Do not create placeholder buttons that do nothing.

Do not create fake AI responses.

If an external Ollama model is unavailable, show a clear setup message.

Make the application fully runnable locally.

At the end, ensure the repository contains:

- working application
- sample datasets
- README
- DESIGN_DECISIONS.md
- .env.example
- Docker configuration if implemented

Build the application now.