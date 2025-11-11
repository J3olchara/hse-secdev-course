import time
from collections import defaultdict

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

# Глобальное хранилище состояния rate limiter для всех экземпляров
_global_rate_limiter_state = {
    'login_attempts': defaultdict(list),
    'failed_attempts': defaultdict(int),
    'blocked_ips': set(),
    'blocked_until': {},
}


def clear_rate_limiter_state():
    """Очистка глобального состояния rate limiter (для тестов)."""
    _global_rate_limiter_state['login_attempts'].clear()
    _global_rate_limiter_state['failed_attempts'].clear()
    _global_rate_limiter_state['blocked_ips'].clear()
    _global_rate_limiter_state['blocked_until'].clear()


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для ограничения количества запросов к эндпоинтам аутентификации.

    Ограничивает:
    - 5 попыток входа в минуту с одного IP адреса
    - После 3 неудачных попыток показывает CAPTCHA
    - После 5 неудачных попыток блокирует IP на 15 минут
    """

    def __init__(
        self, app, login_attempts_per_minute: int = 5, max_failures: int = 3
    ):
        super().__init__(app)
        self.login_attempts_per_minute = login_attempts_per_minute
        self.max_failures = max_failures
        # Используем глобальное состояние вместо локальных атрибутов
        self.login_attempts = _global_rate_limiter_state['login_attempts']
        self.failed_attempts = _global_rate_limiter_state['failed_attempts']
        self.blocked_ips = _global_rate_limiter_state['blocked_ips']
        self._blocked_until = _global_rate_limiter_state['blocked_until']

    async def dispatch(self, request: Request, call_next):
        # Проверяем только POST запросы к /api/v1/auth/login или /auth/login
        if request.method == "POST" and (
            request.url.path == "/api/v1/auth/login"
            or request.url.path == "/auth/login"
        ):
            # Проверяем, заблокирован ли IP
            if self._is_ip_blocked(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="IP address is temporarily blocked due to too many failed attempts.",
                    headers={"Retry-After": "60"},
                )

            # Проверяем rate limit и записываем попытку
            client_ip = self._get_client_ip(request)
            current_time = time.time()

            # Очищаем старые попытки
            self._cleanup_old_attempts(client_ip, current_time)

            # Добавляем текущую попытку
            self.login_attempts[client_ip].append(current_time)

            # Проверяем лимит
            attempts_in_window = len(self.login_attempts[client_ip])

            if attempts_in_window >= self.max_failures:
                # Превышен лимит попыток
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too Many Requests",
                    headers={"Retry-After": "60"},
                )

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Если запрос был заблокирован rate limiting'ом, пробрасываем исключение
            if isinstance(e, HTTPException) and e.status_code == 429:
                raise
            # Для других ошибок логируем correlation_id
            correlation_id = getattr(
                request.state, 'correlation_id', 'unknown'
            )
            print(
                f"Rate limiting middleware: Request failed [{correlation_id}] - {str(e)}"
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Получаем IP адрес клиента."""
        # Проверяем X-Forwarded-For header (для прокси)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Проверяем X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback к client host
        return request.client.host if request.client else "unknown"

    def _is_ip_blocked(self, request: Request) -> bool:
        """Проверяем, заблокирован ли IP адрес."""
        client_ip = self._get_client_ip(request)

        if client_ip in self.blocked_ips:
            # Проверяем, истекло ли время блокировки (15 минут)
            if self._blocked_until.get(client_ip, 0) < time.time():
                self.blocked_ips.discard(client_ip)
                self._blocked_until.pop(client_ip, None)
                return False
            return True

        return False

    def _check_rate_limit(self, request: Request):
        """Проверяем лимит запросов."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Очищаем старые попытки (старше 1 минуты)
        self._cleanup_old_attempts(client_ip, current_time)

        # Проверяем лимит
        attempts_in_window = len(self.login_attempts[client_ip])

        if attempts_in_window >= self.login_attempts_per_minute:
            # Превышен лимит запросов в минуту
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много попыток входа. Попробуйте позже.",
                headers={"Retry-After": "60"},
            )

    def _cleanup_old_attempts(
        self, client_ip: str, current_time: float
    ) -> None:
        """Очищаем старые попытки входа."""
        if client_ip in self.login_attempts:
            # Оставляем только попытки за последнюю минуту
            self.login_attempts[client_ip] = [
                timestamp
                for timestamp in self.login_attempts[client_ip]
                if current_time - timestamp < 60
            ]

    def record_failed_attempt(self, request: Request) -> None:
        """Записываем неудачную попытку входа."""
        client_ip = self._get_client_ip(request)

        self.failed_attempts[client_ip] += 1

        # Если слишком много неудач, блокируем IP
        if self.failed_attempts[client_ip] >= 5:  # max_failures + 2
            self.blocked_ips.add(client_ip)
            self._blocked_until[client_ip] = time.time() + 900  # 15 минут

    def record_successful_attempt(self, request: Request) -> None:
        """Записываем успешную попытку входа (сбрасываем счетчик неудач)."""
        client_ip = self._get_client_ip(request)
        self.failed_attempts[client_ip] = 0

        # Разблокируем IP если он был заблокирован
        if client_ip in self.blocked_ips:
            self.blocked_ips.discard(client_ip)
            self._blocked_until.pop(client_ip, None)

    def get_client_status(self, request: Request) -> dict:
        """Получаем статус для клиента (для отображения CAPTCHA и т.д.)."""
        client_ip = self._get_client_ip(request)

        return {
            "attempts_in_window": len(self.login_attempts[client_ip]),
            "failed_attempts": self.failed_attempts[client_ip],
            "is_blocked": client_ip in self.blocked_ips,
            "show_captcha": self.failed_attempts[client_ip]
            >= self.max_failures,
        }
