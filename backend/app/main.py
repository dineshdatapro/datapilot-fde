from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes.query import router as query_router
from app.routes.upload import router as upload_router
from app.services.llm_planner import ollama_cloud_reachable

app = FastAPI(title="DataPilot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(query_router)


@app.exception_handler(Exception)
async def unhandled_error(_request: Request, exc: Exception):
    if isinstance(exc, (HTTPException, RequestValidationError)):
        raise exc
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


@app.get("/api/health")
async def health():
    key_set = bool((settings.ollama_api_key or "").strip())
    ollama_ok = await ollama_cloud_reachable()
    return {
        "status": "ok",
        "ollama": "reachable" if ollama_ok else "unreachable",
        "ollama_host": settings.ollama_base_url,
        "api_key_configured": key_set,
        "model": settings.ollama_model,
    }
