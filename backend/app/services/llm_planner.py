from __future__ import annotations

import json
import re
from typing import Any

from ollama import AsyncClient, ResponseError

from app.config import settings
from app.models.schemas import AnalyticalPlan

CLOUD_SETUP_MESSAGE = (
    "AI planning is temporarily unavailable.\n\n"
    "DataPilot uses Ollama Cloud. Set OLLAMA_API_KEY in backend/.env "
    "(create a key at https://ollama.com) and keep OLLAMA_BASE_URL=https://ollama.com.\n\n"
    "You can still inspect your uploaded datasets."
)


class LLMUnavailableError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class LLMPlannerError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


PLANNER_SYSTEM = """You are DataPilot's semantic query planner.
Convert the user's data question into a JSON analytical plan.
You do NOT calculate numbers. You only produce a plan.

Return JSON only, matching this schema:
{
  "operation": "total|sum|average|count|minimum|maximum|filter|group_by|comparison|trend|top_n|bottom_n|percentage_change|cross_file_join",
  "metric": "column name or null",
  "aggregation": "sum|mean|count|min|max or null",
  "group_by": ["column", ...],
  "sort": "asc|desc or null",
  "limit": number or null,
  "filters": [{"column": "...", "operator": "eq|neq|gt|gte|lt|lte|contains|in", "value": "..."}],
  "having": {"column": "value", "operator": "gt", "value": 100000} or null,
  "files": ["filename", ...] or [],
  "join": {"left_file": "...", "right_file": "...", "left_on": "...", "right_on": "..."} or null,
  "time_column": "column or null",
  "time_grain": "month"
}

Rules:
- Use ONLY column names and filenames from the provided schema.
- Never invent columns, datasets, or values.
- For "total revenue across all files", operation=total, metric=revenue, files=all files that contain revenue.
- For highest/top region, operation=top_n or group_by with sort=desc, limit=1, group_by=["region"].
- For month comparison, operation=comparison, group_by=["month"] or ["month_name"].
- For trend, operation=trend, time_column="month".
- For top N, operation=top_n with limit.
- For average order value, operation=average, metric=revenue.
- For customer segment questions, join sales files to customers on customer_id and group_by=["segment"].
- For "cities generated more than 1 lakh", group_by=["city"], aggregation=sum, having value > 100000.
- 1 lakh = 100000. 1 crore = 10000000.
- month, year, and month_name may exist as derived columns.
- If the question cannot be answered with supported operations, still return the closest valid plan using existing columns.
"""


def cloud_client() -> AsyncClient:
    key = (settings.ollama_api_key or "").strip()
    if not key:
        raise LLMUnavailableError(CLOUD_SETUP_MESSAGE)
    return AsyncClient(
        host=settings.ollama_base_url.rstrip("/"),
        headers={"Authorization": f"Bearer {key}"},
        timeout=90.0,
    )


async def _chat(messages: list[dict[str, str]], json_mode: bool = False) -> str:
    client: AsyncClient | None = None
    try:
        client = cloud_client()
        kwargs: dict[str, Any] = {
            "model": settings.ollama_model,
            "messages": messages,
        }
        if json_mode:
            kwargs["format"] = "json"
            response = await client.chat(**kwargs, stream=False)
            content = (response.message.content if response.message else None) or ""
        else:
            parts: list[str] = []
            stream = await client.chat(**kwargs, stream=True)
            async for part in stream:
                chunk = part.message.content if part.message else None
                if chunk:
                    parts.append(chunk)
            content = "".join(parts)
    except LLMUnavailableError:
        raise
    except ResponseError as exc:
        raise LLMUnavailableError(CLOUD_SETUP_MESSAGE) from exc
    except Exception as exc:
        raise LLMUnavailableError(CLOUD_SETUP_MESSAGE) from exc
    finally:
        if client is not None:
            await client.close()

    if not content.strip():
        raise LLMUnavailableError(CLOUD_SETUP_MESSAGE)
    return content


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise LLMPlannerError("The planner returned malformed JSON. Please try rephrasing the question.")
        return json.loads(match.group(0))


async def plan_question(question: str, schema: dict[str, Any], relationships: list[dict[str, Any]]) -> AnalyticalPlan:
    user = {
        "question": question,
        "schema": schema,
        "relationships": relationships,
    }
    raw = await _chat(
        [
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": json.dumps(user)},
        ],
        json_mode=True,
    )
    try:
        payload = _extract_json(raw)
    except json.JSONDecodeError as exc:
        raise LLMPlannerError("The planner returned malformed JSON. Please try rephrasing the question.") from exc

    if not payload.get("join"):
        payload["join"] = None
    if not payload.get("having"):
        payload["having"] = None
    if payload.get("files") is None:
        payload["files"] = []
    if payload.get("filters") is None:
        payload["filters"] = []
    if payload.get("group_by") is None:
        payload["group_by"] = []

    try:
        return AnalyticalPlan.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        raise LLMPlannerError("The planner returned a plan that does not match the supported schema.") from exc


EXPLAIN_SYSTEM = """You write a short, precise explanation of an already-computed analytics result.
Do NOT change any numbers. Do NOT invent metrics.
Use the provided formatted values exactly as given.
Write 1-3 sentences in a professional tone.
If currency is implied (revenue/amount), you may use ₹ as already formatted.
"""


async def explain_result(question: str, formatted_result: dict[str, Any]) -> str:
    raw = await _chat(
        [
            {"role": "system", "content": EXPLAIN_SYSTEM},
            {
                "role": "user",
                "content": json.dumps({"question": question, "result": formatted_result}),
            },
        ],
        json_mode=False,
    )
    return raw.strip()


async def ollama_cloud_reachable() -> bool:
    if not (settings.ollama_api_key or "").strip():
        return False
    client: AsyncClient | None = None
    try:
        client = AsyncClient(
            host=settings.ollama_base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {settings.ollama_api_key.strip()}"},
            timeout=5.0,
        )
        await client.list()
        return True
    except Exception:
        return False
    finally:
        if client is not None:
            await client.close()
