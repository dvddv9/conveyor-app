# -*- coding: utf-8 -*-
"""
Vishap — FastAPI сервер.
"""
from contextlib import asynccontextmanager
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import APP_NAME, PORT, DATA_DIR
from src.pipeline.orchestrator import run_pipeline
from src.pipeline.batch import run_batch
from src.storage.history import load_history, add_entry
from src.api.auth import verify_api_key, is_auth_enabled
from src.api.rate_limit import rate_limit_analyze, rate_limit_read
from src.api.jobs import (
    create_job, get_job, update_job, list_jobs,
)
from datetime import datetime, UTC
from src.tools.sarif import to_sarif


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"=== {APP_NAME} API запускается ===")
    print(f"Открой в браузере: http://localhost:{PORT}/docs")
    yield
    print(f"=== {APP_NAME} API остановлен ===")


app = FastAPI(
    title=f"{APP_NAME} API",
    description="Vishap V6.0.0 — 6-стадийный LLM-конвейер для анализа кода",
    version="5.9.6",
    lifespan=lifespan,
)

# CORS: only localhost:8501 (Streamlit UI) by default (dogfood P0 fix)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


# === Pydantic-схемы ===

class AnalyzeRequest(BaseModel):
    force: bool = False
    material: str = Field(..., description="Код, spec, logs — что анализировать")
    filename: str = Field(default="input.txt", description="Имя файла (для контекста)")
    verbose: bool = Field(default=False, description="Подробные логи в ответе")


class AnalyzeResponse(BaseModel):
    session_id: str
    filename: str
    level: str | None = None
    route: list | None = None
    final_markdown: str
    timestamp: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    cached: bool = False
    audit_id: str = ""
    material_hash: str = ""
    material_hash_full: str = ""
    truncated: bool = False
    original_size: int = 0
    verdict: str = ""
    pii_detected: bool = False
    compliance_flags: list = []
    audit: dict = {}
    completeness: dict = {}


class HistoryItem(BaseModel):
    session_id: str
    filename: str
    level: str | None = None
    route: list | None = None
    material_size: int
    timestamp: str
    verdict: str | None = None
    pii_detected: bool | None = None


class BatchItem(BaseModel):
    material: str = Field(..., description="Код / spec / logs")
    filename: str = Field(default="input.txt", description="Имя файла")


class BatchRequest(BaseModel):
    items: list[BatchItem] = Field(..., description="Список материалов")
    max_concurrent: int = Field(default=3, ge=1, le=10,
                                description="Макс. параллельных LLM-вызовов (1..10)")


class BatchResponseItem(BaseModel):
    session_id: str | None = None
    filename: str
    level: str | None = None
    route: list | None = None
    final_markdown: str | None = None
    verdict: str | None = None
    pii_detected: bool | None = None
    error: str | None = None


class BatchResponse(BaseModel):
    results: list[BatchResponseItem]
    count: int
    max_concurrent: int


class ModeRequest(BaseModel):
    mode: str = Field(..., description="auto / cloud / local")


class ModeResponse(BaseModel):
    mode: str
    valid_modes: list[str]


# === Endpoints ===

@app.get("/")
async def root():
    return {
        "app": APP_NAME,
        "version": "5.9.6",
        "docs": "/docs",
        "endpoints": ["/analyze", "/history", "/health"],
    }


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/analyze", response_model=AnalyzeResponse, dependencies=[Depends(verify_api_key), Depends(rate_limit_analyze)])
async def analyze(req: AnalyzeRequest):
    """
    Запускает полный pipeline Vishap V5.9.
    
    Вход: код / spec / logs.
    Выход: финальный Markdown-отчёт + метаданные.
    """
    if not req.material.strip():
        raise HTTPException(status_code=400, detail="material не может быть пустым")

    # === Idempotency: check if same material already analyzed ===
    from src.pipeline.orchestrator import compute_hash
    from src.storage.history import find_done_by_hash, load_history

    material_hash = compute_hash(req.material)
    existing = None if getattr(req, 'force', False) else find_done_by_hash(material_hash)

    if existing:
        cached_session = existing.get("session_id", "")
        result_file = DATA_DIR / f"result_{cached_session}.json"
        if result_file.exists():
            cached = json.loads(result_file.read_text(encoding="utf-8"))
            stage0c = cached.get("stage0", {})
            stage1c = cached.get("stage1", {})
            stage2c = cached.get("stage2", {})
            tokens_in_c = sum(s.get("_meta", {}).get("tokens_in", 0) for s in [stage0c, stage1c, stage2c])
            tokens_out_c = sum(s.get("_meta", {}).get("tokens_out", 0) for s in [stage0c, stage1c, stage2c])
            return AnalyzeResponse(
                session_id=cached.get("session_id", cached_session),
                filename=cached.get("filename", req.filename),
                level=stage0c.get("level"),
                route=stage0c.get("route"),
                final_markdown=cached.get("final_markdown", ""),
                timestamp=cached.get("timestamp", ""),
                tokens_in=tokens_in_c,
                tokens_out=tokens_out_c,
                cost_usd=cached.get("cost_usd", 0.0),
                audit=cached.get("audit", {}),
                completeness=cached.get("completeness", {}),
                material_hash_full=cached.get("audit", {}).get("material_hash_full", cached.get("material_hash", "")),
                truncated=cached.get("audit", {}).get("truncated", False),
                original_size=cached.get("audit", {}).get("original_size", 0),
                cached=True,
                audit_id=cached.get("audit", {}).get("audit_id", ""),
                material_hash=cached.get("audit", {}).get("material_hash", ""),
                verdict=cached.get("audit", {}).get("critique_verdict", ""),
                pii_detected=bool(cached.get("audit", {}).get("pii_detected", False)),
                compliance_flags=cached.get("audit", {}).get("compliance_flags", []),
            )

    try:
        from src.pipeline.orchestrator import run_pipeline_async
        result = await run_pipeline_async(
            material=req.material,
            filename=req.filename,
            verbose=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    stage0 = result.get("stage0", {})
    stage1 = result.get("stage1", {})
    stage2 = result.get("stage2", {})

    tokens_in = sum(
        s.get("_meta", {}).get("tokens_in", 0)
        for s in [stage0, stage1, stage2]
    )
    tokens_out = sum(
        s.get("_meta", {}).get("tokens_out", 0)
        for s in [stage0, stage1, stage2]
    )
    from src.pipeline.cost import sum_stage_costs
    stage3 = result.get("stage3") or {}
    stage4 = result.get("stage4") or {}
    cost_usd = sum_stage_costs([stage0, stage1, stage2, stage3, stage4])

    _audit = result.get("audit", {}) or {}
    return AnalyzeResponse(
        session_id=result["session_id"],
        filename=result["filename"],
        level=stage0.get("level"),
        route=stage0.get("route"),
        final_markdown=result["final_markdown"],
        timestamp=result["timestamp"],
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        audit_id=_audit.get("audit_id", ""),
        material_hash=_audit.get("material_hash", ""),
        verdict=_audit.get("critique_verdict", ""),
        material_hash_full=_audit.get("material_hash_full", ""),
        truncated=_audit.get("truncated", False),
        original_size=_audit.get("original_size", 0),
        pii_detected=bool(_audit.get("pii_detected", False)),
        compliance_flags=_audit.get("compliance_flags", []),
        audit=result.get("audit", {}),
        completeness=result.get("completeness", {}),
    )


@app.post("/analyze/batch", response_model=BatchResponse, dependencies=[Depends(verify_api_key), Depends(rate_limit_analyze)])
async def analyze_batch(req: BatchRequest):
    """
    Параллельный анализ списка материалов.

    Вход: список {material, filename}.
    Выход: список результатов в том же порядке.

    max_concurrent: 1..10 (по умолчанию 3). Больше 10 — риск rate limit DeepSeek.
    """
    if not req.items:
        raise HTTPException(status_code=400, detail="items не может быть пустым")

    for i, item in enumerate(req.items):
        if not item.material.strip():
            raise HTTPException(
                status_code=400,
                detail=f"items[{i}].material не может быть пустым",
            )

    materials = [(item.material, item.filename) for item in req.items]

    try:
        results = run_batch(
            materials,
            max_concurrent=req.max_concurrent,
            verbose=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch error: {str(e)}")

    response_items = []
    for r, item in zip(results, req.items):
        if r is None or "error" in r:
            response_items.append(BatchResponseItem(
                filename=item.filename,
                error=(r or {}).get("error", "unknown"),
            ))
            continue

        stage0 = r.get("stage0", {}) or {}
        audit = r.get("audit", {}) or {}

        response_items.append(BatchResponseItem(
            session_id=r.get("session_id"),
            filename=item.filename,
            level=stage0.get("level"),
            route=stage0.get("route"),
            final_markdown=r.get("final_markdown"),
            verdict=audit.get("critique_verdict"),
            pii_detected=audit.get("pii_detected"),
        ))

    return BatchResponse(
        results=response_items,
        count=len(response_items),
        max_concurrent=req.max_concurrent,
    )


@app.post("/analyze/sarif", dependencies=[Depends(verify_api_key), Depends(rate_limit_analyze)])
async def analyze_sarif(req: AnalyzeRequest):
    """Run analysis and return SARIF 2.1.0 JSON (for GitHub Code Scanning)."""
    result = await analyze(req)

    audit = result.audit.model_dump() if hasattr(result, "audit") else {}

    # Extract SAST/SCA from audit if present (dict)
    sast_result = None
    sca_result = None
    if isinstance(audit, dict):
        sast_tools = audit.get("sast_tools", {})
        if sast_tools:
            sast_result = {
                "total_findings": audit.get("sast_findings", 0),
                "high_priority": audit.get("sast_high_priority", 0),
                "bandit": {"available": True, "summary": sast_tools.get("bandit", {}), "findings": []},
                "semgrep": {"available": True, "summary": sast_tools.get("semgrep", {}), "findings": []},
            }

    sarif = to_sarif(
        audit=audit if isinstance(audit, dict) else {},
        sast_result=sast_result,
        sca_result=sca_result,
        source_file=req.filename,
    )
    return JSONResponse(content=sarif)


@app.get("/history", response_model=list[HistoryItem])
async def history(limit: int = 20):
    """Возвращает последние N записей."""
    items = load_history()
    return [
        HistoryItem(
            session_id=item.get("session_id", ""),
            filename=item.get("filename", ""),
            level=item.get("level"),
            route=item.get("route"),
            material_size=item.get("material_size", 0),
            timestamp=item.get("timestamp", ""),
            verdict=item.get("verdict"),
            pii_detected=item.get("pii_detected"),
        )
        for item in items[-limit:]
    ]


@app.post("/history/clear", dependencies=[Depends(verify_api_key), Depends(rate_limit_read)])
async def history_clear():
    """Очищает историю."""
    from src.storage.history import save_history
    save_history([])
    return {"status": "ok"}


@app.get("/mode", response_model=ModeResponse)
async def get_mode_endpoint():
    """Возвращает текущий режим LLM."""
    from src.storage.mode import get_mode, VALID_MODES
    return ModeResponse(mode=get_mode(), valid_modes=list(VALID_MODES))


@app.post("/mode", response_model=ModeResponse, dependencies=[Depends(verify_api_key), Depends(rate_limit_read)])
async def set_mode_endpoint(req: ModeRequest):
    """Устанавливает режим LLM (auto / cloud / local)."""
    from src.storage.mode import set_mode, get_mode, VALID_MODES
    if not set_mode(req.mode):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {req.mode}. Valid: {list(VALID_MODES)}",
        )
    return ModeResponse(mode=get_mode(), valid_modes=list(VALID_MODES))


# ============================================================
# v6.0: Async API -- job-based analysis
# ============================================================

async def _run_job_async(job_id: str, req: "AnalyzeRequest"):
    """Run pipeline in background, update job store."""
    from src.pipeline.orchestrator import run_pipeline_async
    update_job(job_id, status="running", started_at=datetime.now(UTC).isoformat())
    try:
        result = await run_pipeline_async(
            material=req.material,
            filename=req.filename or "unknown",
            verbose=False,
        )
        update_job(
            job_id,
            status="done",
            result=result,
            finished_at=datetime.now(UTC).isoformat(),
        )
    except Exception as e:
        update_job(
            job_id,
            status="failed",
            error=str(e),
            finished_at=datetime.now(UTC).isoformat(),
        )


@app.post("/analyze/async", dependencies=[Depends(verify_api_key), Depends(rate_limit_analyze)])
async def analyze_async(req: "AnalyzeRequest", background: BackgroundTasks):
    """Create async job -- returns job_id immediately."""
    job_id = create_job(filename=req.filename or "unknown")
    background.add_task(_run_job_async, job_id, req)
    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get job status."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "filename": job["filename"],
        "created_at": job["created_at"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
        "error": job["error"],
    }


@app.get("/report/{job_id}")
async def get_report(job_id: str):
    """Get job result. 409 if not done."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=f"job not done: {job['status']}",
        )
    return job["result"]


if __name__ == "__main__":
    import uvicorn
    # Dogfood P0 fix: if no API key set, bind only to 127.0.0.1.
    host = "0.0.0.0" if is_auth_enabled() else "127.0.0.1"
    print(f"[Auth] API key {'set' if is_auth_enabled() else 'NOT set'} -- binding to {host}")
    uvicorn.run(
        "src.main:app",
        host=host,
        port=PORT,
        reload=False,
    )