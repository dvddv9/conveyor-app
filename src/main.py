# -*- coding: utf-8 -*-
"""
Conveyor — FastAPI сервер.
"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.config import APP_NAME, PORT
from src.pipeline.orchestrator import run_pipeline
from src.pipeline.batch import run_batch
from src.storage.history import load_history, add_entry


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"=== {APP_NAME} API запускается ===")
    print(f"Открой в браузере: http://localhost:{PORT}/docs")
    yield
    print(f"=== {APP_NAME} API остановлен ===")


app = FastAPI(
    title=f"{APP_NAME} API",
    description="Conveyor V5.7 — 6-стадийный LLM-конвейер для анализа кода",
    version="5.7.0",
    lifespan=lifespan,
)


# === Pydantic-схемы ===

class AnalyzeRequest(BaseModel):
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
        "version": "5.7.0",
        "docs": "/docs",
        "endpoints": ["/analyze", "/history", "/health"],
    }


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """
    Запускает полный pipeline Conveyor V5.7.
    
    Вход: код / spec / logs.
    Выход: финальный Markdown-отчёт + метаданные.
    """
    if not req.material.strip():
        raise HTTPException(status_code=400, detail="material не может быть пустым")

    try:
        result = run_pipeline(
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

    return AnalyzeResponse(
        session_id=result["session_id"],
        filename=result["filename"],
        level=stage0.get("level"),
        route=stage0.get("route"),
        final_markdown=result["final_markdown"],
        timestamp=result["timestamp"],
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )


@app.post("/analyze/batch", response_model=BatchResponse)
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


@app.post("/history/clear")
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


@app.post("/mode", response_model=ModeResponse)
async def set_mode_endpoint(req: ModeRequest):
    """Устанавливает режим LLM (auto / cloud / local)."""
    from src.storage.mode import set_mode, get_mode, VALID_MODES
    if not set_mode(req.mode):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {req.mode}. Valid: {list(VALID_MODES)}",
        )
    return ModeResponse(mode=get_mode(), valid_modes=list(VALID_MODES))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
    )
