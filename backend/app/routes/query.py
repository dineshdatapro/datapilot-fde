from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.analytics_engine import AnalyticsError, execute_plan
from app.services.answer_generator import generate_answer
from app.services.llm_planner import LLMPlannerError, LLMUnavailableError, plan_question
from app.services.session_store import store
from app.services.validator import PlanValidationError, available_schema_summary, validate_plan
from app.services.visualization import select_visualization
from app.utils.formatting import format_value, infer_value_kind

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    session_id: str
    question: str


def _analysis_details(plan, result) -> dict:
    agg = result.get("aggregation") or "sum"
    metric = plan.metric or "rows"
    op_label = f"{agg.upper()}({metric})" if metric else agg
    filters = "None"
    if plan.filters:
        filters = "; ".join(f"{f.column} {f.operator} {f.value}" for f in plan.filters)
    grouping = ", ".join(plan.group_by) if plan.group_by else "None"
    return {
        "files_used": result.get("files_used") or [],
        "rows_analyzed": result.get("rows_analyzed") or 0,
        "operation": op_label,
        "grouping": grouping,
        "filters": filters,
        "join": plan.join.model_dump() if plan.join else None,
        "trust": "Numbers were computed with Pandas from the uploaded files. The model only planned the query and wrote the explanation.",
    }


@router.post("/query")
async def query(req: QueryRequest):
    session = store.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Upload files and try again.")
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Ask a question about your uploaded data.")
    if not session.files:
        raise HTTPException(status_code=400, detail="Upload at least one CSV or Excel file before asking a question.")

    schema = available_schema_summary([f.profile for f in session.files.values()])
    relationships = [r.model_dump() for r in session.relationships]

    try:
        plan = await plan_question(question, schema, relationships)
        plan = validate_plan(plan, session)
        result = execute_plan(plan, session)
        visualization = select_visualization(plan, result)
        answer = await generate_answer(question, plan, result)
    except LLMUnavailableError as exc:
        return {
            "question": question,
            "answer": "",
            "verified": False,
            "files_used": [],
            "rows_analyzed": 0,
            "plan": {},
            "result": {},
            "visualization": {"type": "none", "title": "", "data": []},
            "analysis": {},
            "error": exc.message,
        }
    except (LLMPlannerError, PlanValidationError, AnalyticsError) as exc:
        message = getattr(exc, "message", str(exc))
        return {
            "question": question,
            "answer": "",
            "verified": False,
            "files_used": [],
            "rows_analyzed": 0,
            "plan": {},
            "result": {},
            "visualization": {"type": "none", "title": "", "data": []},
            "analysis": {},
            "error": message,
        }
    except Exception:
        return {
            "question": question,
            "answer": "",
            "verified": False,
            "files_used": [],
            "rows_analyzed": 0,
            "plan": {},
            "result": {},
            "visualization": {"type": "none", "title": "", "data": []},
            "analysis": {},
            "error": "Something went wrong while analyzing your question. Please try again.",
        }

    kind = infer_value_kind(plan.metric, result.get("value"))
    public_result = {
        **{k: v for k, v in result.items() if k != "rows" or result.get("kind") != "table"},
        "formatted_value": format_value(result.get("value"), kind),
        "rows": result.get("rows"),
    }
    if result.get("kind") == "table":
        public_result["rows"] = result.get("rows")

    return {
        "question": question,
        "answer": answer,
        "verified": True,
        "files_used": result.get("files_used") or [],
        "rows_analyzed": result.get("rows_analyzed") or 0,
        "plan": plan.model_dump(),
        "result": public_result,
        "visualization": visualization.model_dump(),
        "analysis": _analysis_details(plan, result),
        "error": None,
    }
