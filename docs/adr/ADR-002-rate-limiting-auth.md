# ADR-002: Rate Limiting для защиты от брутфорс атак

Дата: 2025-01-22
Статус: Accepted

## Context

Эндпоинт аутентификации `/auth/login` является критичной точкой входа в систему и подвержен брутфорс атакам где злоумышленник может перебирать пароли для получения доступа к акаунтам пользователей. Без защиты атакующий может сделать тысячи попыток входа за короткое время.

Текущая ситуация:
- Нет ограничений на количество попыток логина
- Злоумышленник может делать 100+ запросов в секунду
- Риск компрометации слабых паролей очень высокий
- Нет механизмов блокировки подозрительной активности

Бизнес требования:
- Защитить пользователей от взлома аккаунтов
- Минимизировать влияние на легитимных пользователей
- Соответствие security best practices

Технические ограничения:
- Приложение может работать в multiple instances (горизонтальное масштабирование)
- Нужен shared state для счетчиков попыток
- Минимальная latency для проверки лимитов (<10мс)

## Decision

Внедряем **Rate Limiting** на основе **Sliding Window** алгоритма с использованием Redis для хранения счетчиков.

### Параметры лимитов:

**Для `/auth/login`:**
- **5 попыток в минуту на IP адрес**
- После превышения — блокировка на 15 минут
- HTTP статус: 429 Too Many Requests
- Response в формате RFC 7807 (согласно ADR-001)

**Для остальных API endpoints:**
- 100 запросов в минуту на аутентифицированого пользователя
- 20 запросов в минуту для не аутентифицированых запросов по IP

### Реализация:

```python
# app/middleware/rate_limiting.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

### Исключения:
- Trusted IPs (monitoring, health checks) — whitelist
- Internal service-to-service calls (по API key)

### Headers в response:
- `X-RateLimit-Limit` — максимальное количество запросов
- `X-RateLimit-Remaining` — оставшееся количество
- `X-RateLimit-Reset` — timestamp когда лимит сбрасывается

## Alternatives

### Альтернатива 1: Fixed Window алгоритм
**Плюсы:**
- Проще в реализации
- Меньше memory overhead

**Минусы:**
- Уязвим к burst атакам на границах окна
- Атакующий может сделать 10 запросов за секунду (5 в конце минуты + 5 в начале следующей)

**Вердикт:** Отвергнута из-за security риска

### Альтернатива 2: Token Bucket алгоритм
**Плюсы:**
- Позволяет краткосрочные bursts
- Более гибкая настройка

**Минусы:**
- Сложнее в понимании для команды
- Больше параметров для настройки

**Вердикт:** Хороший вариант но Sliding Window проще и достаточно для наших нужд

### Альтернатива 3: CAPTCHA после N попыток
**Плюсы:**
- Очень эффективно против ботов
- Не блокирует легитимных пользователей

**Минусы:**
- Плохой UX
- Требует frontend интеграции
- Дополнительные зависимости (reCAPTCHA, hCaptcha)

**Вердикт:** Можем добавить позже как дополнительный слой защиты но не как основой

### Альтернатива 4: Account Lockout после N неудачных попыток
**Плюсы:**
- Прямая защита конкретного аккаунта

**Минусы:**
- DoS vector — атакующий может заблокировать любой аккаунт зная только username
- Сложность unlock механизма

**Вердикт:** Слишком рискованно, оставляем IP-based rate limiting

## Consequences

### Плюсы
- **Защита от брутфорса**: значительно снижает риск **R1** (брутфорс атаки)
- **Защита от DoS**: предотвращает перегрузку сервера лишними запросами (**R5**)
- **Industry standard**: соответствие OWASP рекомендациям
- **Масштабируемость**: Redis позволяет работать с multiple instances

### Минусы
- **False positives**: легитимные пользователи за NAT могут быть заблокированы
- **Dependency на Redis**: дополнительная инфраструктура
- **Bypass через прокси**: атакующий может использовать разные IP (но это дорого)

### Влияние на производительность
- Redis lookup добавляет ~2-5мс latency
- p95 остается в пределах **NFR-03** (≤300мс для /auth/login)
- Minimal memory usage: ~100 bytes на IP адрес
- TTL очищает старые записи автоматически

### Security Impact
- **Снижение риска R1** (брутфорс) с уровня 20 до ~5 (Risk = 2×2.5 = 5)
- **Снижение риска R5** (DDoS) с уровня 12 до ~6
- IP-based tracking не содержит PII
- Rate limit headers помогают клиентам избежать блокировки

### User Experience
- Легитимные пользователи почти никогда не достигнут лимита
- Если достигнут — понятное сообщение об ошибке (RFC 7807)
- Возможность контакта с поддержкой для unban

### Trade-offs
- Жертвуем немного latency ради безопасности
- Добавляем зависимость на Redis (но он уже нужен для сессий)
- Потенциальные false positives vs защита от атак — выбираем защиту

## Rollout Plan

### Pre-requisites
- [ ] Redis instance (используем существующий или создаем новый)
- [ ] Установить библиотеку `slowapi` и `redis-py`

### Фаза 1: Development (Неделя 1)
- [ ] Интегрировать slowapi в FastAPI приложение
- [ ] Настроить Redis connection pool
- [ ] Добавить rate limiting middleware
- [ ] Применить decorators на `/auth/login` и другие endpoints
- [ ] Добавить whitelist для trusted IPs
- [ ] Настроить RFC7807 responses для 429 ошибок

### Фаза 2: Testing (Неделя 1-2)
- [ ] Unit тесты для rate limiting логики
- [ ] Integration тесты с реальным Redis
- [ ] Load testing для проверки производительности
- [ ] Negative тесты: попытки bypass через разные endpoints

### Фаза 3: Мониторинг (Неделя 2)
- [ ] Добавить метрики в Prometheus/Grafana
  - `rate_limit_exceeded_total` counter по endpoint
  - `rate_limit_check_duration` histogram
- [ ] Алерты при аномальном количестве 429 ошибок
- [ ] Dashboard для визуализации blocked IPs

### Фаза 4: Production Rollout (Неделя 3)
- [ ] Deploy на staging с мониторингом
- [ ] Проверка что легитимные пользователи не затронуты
- [ ] Gradual rollout на production: 10% → 50% → 100%
- [ ] Monitoring error rates и latency

### Definition of Done (DoD)
- [x] Rate limiting работает на `/auth/login` (5/min)
- [x] Rate limiting работает на других endpoints (100/min auth, 20/min unauth)
- [x] Redis используется для shared state
- [x] Trusted IPs в whitelist
- [x] Response headers содержат X-RateLimit-*
- [x] 429 ошибки в формате RFC7807
- [x] Тесты покрывают основные сценарии
- [x] Мониторинг и алерты настроены

### Rollback Plan
Если возникнут проблемы:
1. Отключить rate limiting через feature flag `RATE_LIMIT_ENABLED=false`
2. Увеличить лимиты если много false positives
3. Переключиться на in-memory fallback если Redis недоступен

## Links

**NFR (из P03):**
- **NFR-06** — Rate limiting аутентификации (прямое соответствие, порог 5 попыток/мин)
- **NFR-03** — Производительность /auth/login (должны оставаться в пределах p95 ≤300мс)

**STRIDE угрозы (из P04):**
- **F1: POST /auth/login (D)** — защита от DoS атак
- **F1: POST /auth/login (S)** — затрудняет spoofing через брутфорс

**Риски (из P04):**
- **R1** — Брутфорс атаки на /auth/login (КРИТЕРИЙ ЗАКРЫТИЯ: Rate limiting 5/мин + блокировка на 15 мин)
- **R5** — DDoS атаки (КРИТЕРИЙ ЗАКРЫТИЯ: Rate limiting на уровне API + WAF rules)

**Тесты:**
- `tests/nfr/test_security.py::test_rate_limit_auth_endpoint`
- `tests/nfr/test_security.py::test_rate_limit_blocks_after_5_attempts`
- `tests/integration/test_api.py::test_rate_limit_headers_present`
- `test_rate_limiting.py::test_rate_limiting_integration`

**Связанные ADR:**
- ADR-001 (RFC7807) — используется для форматирования 429 ошибок
- ADR-003 (Secrets) — Redis credentials хранятся безопасно
