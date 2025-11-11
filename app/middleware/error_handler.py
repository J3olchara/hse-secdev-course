import logging
import os
import uuid
from datetime import datetime

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.exceptions import ApiError

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware для обработки ошибок в формате RFC7807 с correlation_id (ADR-001)"""

    async def dispatch(self, request: Request, call_next):
        # Генерируем уникальный correlation_id для каждого запроса
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        try:
            response = await call_next(request)
            return response
        except ApiError as e:
            logger.error(
                f"API Error [{correlation_id}]: {e.code} - {e.message}",
                extra={"correlation_id": correlation_id},
            )
            return self._create_rfc7807_response(
                e.status, e.code, e.message, correlation_id
            )
        except HTTPException as e:
            logger.error(
                f"HTTP Exception [{correlation_id}]: {e.status_code} - {e.detail}",
                extra={"correlation_id": correlation_id},
            )
            return self._create_rfc7807_response(
                e.status_code,
                "http_error",
                str(e.detail),
                correlation_id,
                headers=e.headers,
            )
        except Exception as e:
            # В production скрываем технические детали (ADR-001, R10)
            is_production = os.getenv("ENV", "development") == "production"
            detail = "Internal server error" if is_production else str(e)

            logger.error(
                f"Unexpected error [{correlation_id}]: {str(e)}",
                exc_info=True,
                extra={"correlation_id": correlation_id},
            )
            return self._create_rfc7807_response(
                500, "internal_error", detail, correlation_id
            )

    def _create_rfc7807_response(
        self,
        status: int,
        error_code: str,
        message: str,
        correlation_id: str,
        headers: dict = None,
    ) -> JSONResponse:
        """Создает ответ в формате RFC7807 согласно NFR-02 и ADR-001"""
        error_type_base = "https://api.wishlist.com/errors/"

        return JSONResponse(
            status_code=status,
            content={
                "type": f"{error_type_base}{error_code}",
                "title": self._get_title_for_status(status),
                "status": status,
                "detail": message,
                "error": {
                    "code": error_code,
                    "message": message,
                },
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            headers=headers or {},
        )

    def _get_title_for_status(self, status: int) -> str:
        """Возвращает человеко-читаемый заголовок для HTTP статуса"""
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
        return titles.get(status, "Error")
