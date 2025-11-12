# ADR-005: Улучшение валидации ввода и контроли безопасного кодирования

**Дата:** 2025-01-15  
**Статус:** Принято  
**Контекст:** P06 — Secure Coding  
**Связанные NFR:** NFR-02, NFR-06, NFR-08  
**Связанные угрозы (STRIDE):** T (Tampering), D (Denial of Service)

---

## Контекст и проблема

В процессе аудита безопасности кодовой базы были выявлены несколько уязвимостей и областей для улучшения:

1. **Использование float для денежных значений** — отсутствие поля price в модели Wish и потенциальный риск ошибок округления при работе с деньгами
2. **Отсутствие строгой валидации схем** — возможность передачи дополнительных полей (mass assignment vulnerability)
3. **DoS уязвимость через пагинацию** — отсутствие ограничений на `offset` позволяет атакующему перегрузить базу данных
4. **Wildcard injection в поиске** — использование f-string в LIKE запросах без экранирования спецсимволов
5. **Отсутствие маскирования PII в логах** — чувствительные данные (email, пароли, токены) могут попадать в логи

### Человеческий фактор

Все эти уязвимости возникают из-за типичных ошибок разработчиков:
- Использование `float` вместо `Decimal` для простоты
- Игнорирование возможности передачи дополнительных полей
- Недооценка возможности DoS через легитимные API запросы
- Использование f-string без мысли о спецсимволах
- Отсутствие осознания риска утечки PII через логи

---

## Решение

### 1. Безопасная работа с денежными значениями (Decimal)

**Решение:** Добавить поле `price: Decimal` в модель Wish с валидацией.

**Реализация:**
```python
from decimal import Decimal
from pydantic import Field

class WishBase(BaseModel):
    price: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Wish price (безопасная работа с деньгами, ADR-005)",
    )
```

**Обоснование:**
- `Decimal` предотвращает ошибки округления при работе с деньгами
- `max_digits=12, decimal_places=2` — стандарт для денежных значений (до триллиона с копейками)
- `ge=0` — отрицательные цены не имеют смысла

**Модель БД:**
```python
price = Column(Numeric(precision=12, scale=2), nullable=True)
```

---

### 2. Строгая валидация схем (extra='forbid')

**Решение:** Установить `model_config = ConfigDict(extra='forbid')` во всех Pydantic схемах.

**Реализация:**
```python
class WishBase(BaseModel):
    model_config = ConfigDict(extra='forbid')
    # ... поля
```

**Обоснование:**
- Предотвращает mass assignment атаки
- Явно отклоняет неожиданные поля
- Помогает отловить ошибки в клиентском коде

**Применено к схемам:**
- `WishBase`, `WishCreate`, `WishUpdate`, `WishResponse`, `WishListResponse`
- `UserBase`, `UserLogin`, `UserUpdate`, `UserResponse`
- `Token`, `TokenData`, `RefreshTokenRequest`, `LogoutRequest`

---

### 3. Защита от DoS через пагинацию

**Проблема:** Атакующий может делать запросы с `offset=999999` или `limit=1000`, перегружая базу данных.

**Решение:** Ограничить максимальные значения `skip` и `limit`.

**Реализация:**
```python
@router.get("", response_model=WishListResponse)
async def get_wishes(
    skip: int = Query(0, ge=0, le=10000, description="max 10000 для защиты от DoS"),
    limit: int = Query(10, ge=1, le=50, description="max 50 для защиты от DoS"),
    search: Optional[str] = Query(None, max_length=100, description="max 100 символов"),
    ...
):
```

**Обоснование:**
- `skip <= 10000` — ограничение на максимальный offset (защита от deep pagination DoS)
- `limit <= 50` (было 100) — ограничение размера ответа
- `search <= 100` — ограничение длины поискового запроса

**Связь с NFR-06:** Rate limiting и защита от DoS атак  
**Связь с STRIDE:** D (Denial of Service) — защита от перегрузки через легитимные API вызовы

---

### 4. Защита от wildcard injection в SQL LIKE

**Проблема:** Код `Wish.title.ilike(f"%{title}%")` уязвим к wildcard injection.

**Атака:** Пользователь может передать `%%` или `__` для выполнения дорогих LIKE операций.

**Решение:** Экранирование спецсимволов SQL LIKE.

**Реализация:**
```python
def escape_like_pattern(pattern: str) -> str:
    """Экранирование спецсимволов SQL LIKE для защиты от wildcard injection."""
    pattern = pattern.replace('\\', '\\\\')  # Сначала backslash
    pattern = pattern.replace('%', '\\%')
    pattern = pattern.replace('_', '\\_')
    pattern = pattern.replace('[', '\\[')
    pattern = pattern.replace(']', '\\]')
    return pattern

# Использование
escaped_title = escape_like_pattern(title)
Wish.title.ilike(f"%{escaped_title}%")
```

**Обоснование:**
- Предотвращает злоупотребление wildcard символами
- Backslash экранируется первым, чтобы не экранировать наши escape символы
- Квадратные скобки экранируются для совместимости с некоторыми СУБД

**Связь с NFR-08:** Валидация входных данных  
**Связь с STRIDE:** T (Tampering) — модификация поискового запроса для DoS

---

### 5. Нормализация datetime в UTC

**Проблема:** Inconsistent timezone handling может привести к ошибкам в логике (например, при проверке истечения токенов).

**Решение:** Автоматическая нормализация всех datetime в UTC.

**Реализация:**
```python
@field_validator('created_at', 'updated_at', mode='before')
@classmethod
def normalize_datetime(cls, v: datetime) -> datetime:
    """Нормализация datetime в UTC (ADR-005, NFR-08)"""
    if v is None:
        return v
    if isinstance(v, datetime):
        if v.tzinfo is None:
            # Если naive datetime, считаем его UTC
            return v.replace(tzinfo=timezone.utc)
        # Конвертируем в UTC
        return v.astimezone(timezone.utc)
    return v
```

**Обоснование:**
- Все datetime хранятся в единой timezone (UTC)
- Предотвращает ошибки сравнения datetime
- Соответствует best practices (ISO 8601, RFC 3339)

---

### 6. Маскирование PII в логах и ответах

**Проблема:** Чувствительные данные (email, пароли, токены) могут попадать в логи, нарушая GDPR и другие compliance требования.

**Решение:** Централизованная система маскирования PII.

**Реализация (`app/utils/pii_masking.py`):**
```python
def mask_email(email: str) -> str:
    """test@example.com -> t***@example.com"""
    local, domain = email.split('@', 1)
    return f"{local[0]}***@{domain}"

def mask_password(password: str) -> str:
    """Полностью маскирует пароль"""
    return "***REDACTED***"

def mask_token(token: str) -> str:
    """Показывает только последние 4 символа"""
    return f"***{token[-4:]}"

def mask_pii_in_string(text: str) -> str:
    """Автоматически находит и маскирует PII"""
    # Маскирует email, JWT токены и т.д.
```

**Использование в middleware:**
```python
safe_message = mask_pii_in_string(e.message)
logger.error(f"API Error [{correlation_id}]: {e.code} - {safe_message}")
```

**Обоснование:**
- Соответствует GDPR и compliance требованиям
- Предотвращает утечку чувствительных данных через логи
- Централизованный подход обеспечивает консистентность

**Связь с NFR-02:** Безопасные ошибки с маскированием PII

---

### 7. Централизованная карта ошибок (RFC7807)

**Решение:** Создать централизованную карту кодов ошибок для консистентности.

**Реализация (`app/core/error_codes.py`):**
```python
class ErrorCode:
    VALIDATION_ERROR = "validation_error"
    XSS_DETECTED = "xss_detected"
    SQL_INJECTION_DETECTED = "sql_injection_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    # ... и другие

ERROR_DESCRIPTIONS: Dict[str, str] = {
    ErrorCode.VALIDATION_ERROR: "The request contains invalid data.",
    # ...
}
```

**Использование:**
```python
error_description = get_error_description(error_code)
return JSONResponse({
    "error": {
        "code": error_code,
        "message": message,
        "description": error_description,  # Из карты
    }
})
```

**Обоснование:**
- Консистентные коды ошибок во всем API
- Человеко-читаемые описания для клиентов
- Упрощает документирование API

---

## Последствия

### Положительные

1. **Безопасность:**
   - Защита от DoS атак через пагинацию
   - Защита от wildcard injection
   - Защита от mass assignment
   - Маскирование PII в логах

2. **Надежность:**
   - Точные вычисления с денежными значениями (Decimal)
   - Консистентная обработка timezone (UTC)
   - Строгая валидация предотвращает unexpected inputs

3. **Compliance:**
   - Соответствие GDPR (маскирование PII)
   - Соответствие NFR-02, NFR-06, NFR-08
   - Audit trail с безопасными логами

4. **Удобство разработки:**
   - Централизованная карта ошибок
   - Явные ограничения в схемах
   - Лучшая документация через ADR

### Отрицательные

1. **Производительность:**
   - Дополнительная валидация (минимальный overhead)
   - Экранирование символов в поиске (незначительное влияние)

2. **Ограничения для пользователей:**
   - Меньший максимальный limit (50 вместо 100)
   - Ограничение на максимальный offset (10000)
   - Ограничение длины поискового запроса (100 символов)

3. **Миграция:**
   - Требуется миграция БД для добавления поля `price`
   - Существующий код может сломаться из-за `extra='forbid'`

---

## Связь с предыдущими практиками

| Практика | Связь |
|----------|-------|
| **NFR-02** (P03) | Улучшенный RFC7807 с маскированием PII и картой ошибок |
| **NFR-06** (P03) | Защита от DoS через ограничения пагинации |
| **NFR-08** (P03) | Строгая валидация всех входных данных |
| **STRIDE D** (P04) | Защита от DoS атак через пагинацию |
| **STRIDE T** (P04) | Защита от wildcard injection (tampering поисковых запросов) |

---

## Тестирование

Все контроли покрыты негативными тестами (`tests/unit/test_secure_coding_fixes.py`):

1. ✅ `test_decimal_precision_attack` — попытка передать огромное число
2. ✅ `test_negative_price_rejected` — отрицательная цена
3. ✅ `test_extra_fields_forbidden_*` — дополнительные поля запрещены
4. ✅ `test_search_sql_wildcard_injection_*` — экранирование спецсимволов
5. ✅ `test_mask_email`, `test_mask_password`, `test_mask_token` — маскирование PII
6. ✅ `test_datetime_timezone_normalization_*` — UTC нормализация

**Итого:** 20+ негативных тестов для всех контролей безопасности.

---

## Альтернативы

### Альтернатива 1: Использовать Money объект вместо Decimal
- **Плюсы:** Более явная семантика
- **Минусы:** Дополнительная зависимость, сложнее интеграция с БД
- **Решение:** Decimal достаточно для текущих требований

### Альтернатива 2: Использовать ORM query builder вместо экранирования
- **Плюсы:** Более чистый код
- **Минусы:** SQLAlchemy уже использует параметризацию, но LIKE требует дополнительной защиты
- **Решение:** Экранирование необходимо для wildcard символов

### Альтернатива 3: Cursor-based pagination вместо offset-based
- **Плюсы:** Лучшая производительность для больших offset
- **Минусы:** Более сложная реализация, нельзя jump на произвольную страницу
- **Решение:** Offset-based достаточно с ограничением <= 10000

---

## Дополнительные ссылки

- [RFC 7807 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc7807)
- [OWASP Top 10 — SQL Injection](https://owasp.org/www-project-top-ten/)
- [GDPR — Data Minimization](https://gdpr.eu/data-minimization/)
- [Python Decimal documentation](https://docs.python.org/3/library/decimal.html)
- [Pydantic v2 — Strict Mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)

