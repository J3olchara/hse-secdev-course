"""
RFC 7807 Problem Details utility functions
"""

from typing import Any, Dict
from uuid import uuid4

from starlette.responses import JSONResponse


def problem(
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extras: Dict[str, Any] | None = None,
) -> JSONResponse:
    """
    Create RFC 7807 compliant error response

    Args:
        status: HTTP status code
        title: Short human-readable summary
        detail: Human-readable explanation
        type_: URI identifying the problem type
        extras: Additional fields to include

    Returns:
        JSONResponse with RFC 7807 format
    """
    correlation_id = str(uuid4())

    payload = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "correlation_id": correlation_id,
    }

    if extras:
        payload.update(extras)

    return JSONResponse(
        payload,
        status_code=status,
        headers={"Content-Type": "application/problem+json"},
    )


def validation_problem(
    detail: str, errors: list | None = None
) -> JSONResponse:
    """Helper for validation errors"""
    extras = {"errors": errors} if errors else None
    return problem(
        status=400,
        title="Validation Error",
        detail=detail,
        type_="https://api.wishlist.com/errors/validation-failed",
        extras=extras,
    )


def auth_problem(detail: str = "Authentication required") -> JSONResponse:
    """Helper for authentication errors"""
    return problem(
        status=401,
        title="Authentication Error",
        detail=detail,
        type_="https://api.wishlist.com/errors/auth-failed",
    )


def forbidden_problem(detail: str = "Access denied") -> JSONResponse:
    """Helper for authorization errors"""
    return problem(
        status=403,
        title="Authorization Error",
        detail=detail,
        type_="https://api.wishlist.com/errors/forbidden",
    )


def notfound_problem(detail: str = "Resource not found") -> JSONResponse:
    """Helper for 404 errors"""
    return problem(
        status=404,
        title="Not Found",
        detail=detail,
        type_="https://api.wishlist.com/errors/not-found",
    )


def rate_limit_problem(detail: str = "Too many requests") -> JSONResponse:
    """Helper for rate limiting errors"""
    return problem(
        status=429,
        title="Rate Limit Exceeded",
        detail=detail,
        type_="https://api.wishlist.com/errors/rate-limit",
    )


def server_problem(detail: str = "Internal server error") -> JSONResponse:
    """Helper for 500 errors - masks technical details in production"""
    return problem(
        status=500,
        title="Internal Server Error",
        detail=detail,
        type_="https://api.wishlist.com/errors/internal",
    )
