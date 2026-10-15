"""FastAPI 应用入口、健康检查和统一异常处理。"""

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.shared.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", description="电商运营助手后端 API")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """为每次请求生成并返回请求 ID。"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """统一处理未预期异常，避免泄漏内部堆栈。"""
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误", "request_id": request.headers.get("X-Request-ID")})


@app.get("/health", tags=["系统"])
async def health() -> dict[str, str]:
    """返回服务健康状态。"""
    return {"status": "ok", "environment": settings.app_env}


app.include_router(router, prefix=settings.api_prefix)


def run() -> None:
    """启动本地开发服务器。"""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
