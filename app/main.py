from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api.v1.router import router as api_router
from .core.database import create_tables
from .core.exceptions import ApiError
from .middleware import (
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    RateLimitingMiddleware,
    setup_cors,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Wishlist API",
    version="0.1.0",
    description="API для управления списком желаний с JWT авторизацией",
    lifespan=lifespan,
)

setup_cors(app)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

app.include_router(api_router)


# Обработчик RequestValidationError для добавления correlation_id
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://tools.ietf.org/html/rfc7807",
            "title": "Unprocessable Entity",
            "status": 422,
            "detail": "Validation error",
            "error": {
                "code": "validation_error",
                "message": str(exc),
            },
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


# Обработчик HTTPException для добавления correlation_id
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    # Определяем заголовок для статуса
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    title = titles.get(exc.status_code, "Error")

    # Собираем заголовки из исключения
    response_headers = dict(exc.headers) if exc.headers else {}

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "https://tools.ietf.org/html/rfc7807",
            "title": title,
            "status": exc.status_code,
            "detail": str(exc.detail),
            "error": {
                "code": "http_error",
                "message": str(exc.detail),
            },
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        headers=response_headers,
    )


# Обработчики исключений теперь находятся в ErrorHandlerMiddleware
# Они возвращают ответы в формате RFC7807 согласно NFR-02


@app.get("/health")
def health():
    return {"status": "ok"}


_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error",
            message="name must be 1..100 chars",
            status=422,
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)
