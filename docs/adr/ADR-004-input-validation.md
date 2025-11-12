# ADR-004: Строгая валидация входных данных

Дата: 2025-01-22
Статус: Accepted

## Context

Наш API принимает пользовательские данные через различные эндпоинты (создание/обновление желаний, регистрация пользователей и тд). Без должной валидации мы подвергаемя рискам:
- **SQL Injection** — внедрение вредоносных SQL команд через поля ввода
- **XSS (Cross-Site Scripting)** — внедрение JavaScript в описания желаний
- **Path Traversal** — попытки доступа к файлам вне разрешенной директории
- **NoSQL Injection** — если в будущем будем использовать MongoDB
- **Command Injection** — если будем запускать внешние команды
- **Buffer Overflow** — слишком длинные строки

Текущие проблемы:
- Частичная валидация через Pydantic schemas
- Нет проверки максимальной длины для некоторых полей
- Нет sanitization HTML/JS контента
- Отсутствует валидация специальных символов

Примеры уязвимого кода:
```python
# Плохо - нет валидации длины
class WishCreate(BaseModel):
    title: str  # может быть 10MB строка!
    description: str
```

Бизнес требования:
- Защита от инъекций любого типа
- Защита производительности от слишком больших payload
- User-friendly error messages когда валидация не проходит

## Decision

Внедряем **многоуровневую валидацию** с использованием Pydantic, custom validators и ORM parameterization.

### Уровень 1: Schema Validation (Pydantic)

Все входные данные должны проходить через Pydantic модели с явными ограничениями:

```python
from pydantic import BaseModel, Field, constr, validator

class WishCreate(BaseModel):
    title: constr(min_length=1, max_length=200, strip_whitespace=True)
    description: constr(max_length=5000, strip_whitespace=True) | None = None

    @validator('title', 'description')
    def sanitize_html(cls, v):
        if v and ('<script' in v.lower() or 'javascript:' in v.lower()):
            raise ValueError('HTML/JS content not allowed')
        return v
```

**Правила для всех полей:**
- `title`: 1-200 символов, обязательное
- `description`: 0-5000 символов, опциональное
- `username`: 3-50 символов, только буквы/цифры/дефис/underscore
- `email`: валидация через `EmailStr`
- `password`: минимум 8 символов, требует буквы+цифры

### Уровень 2: Business Logic Validation

Дополнительная валидация в use cases:
```python
async def create_wish(user_id: int, wish_data: WishCreate):
    # Проверка лимита желаний на пользователя
    count = await repo.count_user_wishes(user_id)
    if count >= 100:
        raise TooManyWishesError("Maximum 100 wishes per user")

    # Проверка на дубликаты
    existing = await repo.find_by_title(user_id, wish_data.title)
    if existing:
        raise DuplicateWishError("Wish with same title exists")
```

### Уровень 3: Database Protection (ORM)

Всегда использовать parameterized queries через SQLAlchemy:
```python
# Правильно - защищено от SQL injection
stmt = select(Wish).where(Wish.user_id == user_id, Wish.title == title)

# НИКОГДА так не делать:
# query = f"SELECT * FROM wishes WHERE title = '{title}'"  # ОПАСНО!
```

### Уровень 4: Output Encoding

При возврате данных клиенту экранировать HTML:
```python
from html import escape

def to_response(wish: Wish) -> WishResponse:
    return WishResponse(
        title=escape(wish.title),
        description=escape(wish.description) if wish.description else None
    )
```

### Лимиты и пороги:

| Поле | Min | Max | Regex/Pattern |
|------|-----|-----|---------------|
| username | 3 | 50 | `^[a-zA-Z0-9_-]+$` |
| email | - | 100 | RFC 5322 email |
| password | 8 | 128 | Минимум 1 буква + 1 цифра |
| wish.title | 1 | 200 | Любые символы (но экранировать) |
| wish.description | 0 | 5000 | Любые символы (но экранировать) |
| request body size | - | 1MB | Content-Length header |

### Специальные символы:

Запрещаем в определенных полях:
- `<script>`, `javascript:`, `onerror=` — в любых текстовых полях
- `../`, `..\\` — в путях к файлам
- `'; DROP TABLE` — классическая SQL инъекция (защищены через ORM)
- Null bytes `\0` — могут ломать строки в некоторых языках

## Alternatives

### Альтернатива 1: Только client-side валидация
**Плюсы:**
- Быстрая обратная связь пользователю
- Меньше нагрузки на сервер

**Минусы:**
- НЕБЕЗОПАСНО — легко обойти через curl/Postman
- Client-side код может быть модифицирован

**Вердикт:** Client-side валидация это UX фича но не security контроль. Отвергнута как единстенный метод.

### Альтернатива 2: Whitelist vs Blacklist подход
**Whitelist (наш выбор):**
- Разрешаем только известные безопасные символы/паттерны
- Более безопасный но менее гибкий

**Blacklist:**
- Запрещаем известные плохие паттерны
- Невозможно предусмотреть все варианты атак

**Вердикт:** Используем whitelist где возможно (username), blacklist как дополнительный слой (script tags)

### Альтернатива 3: Библиотеки sanitization (bleach, DOMPurify)
**Плюсы:**
- Профессиональная очистка HTML
- Поддержка safe subset of HTML (если нужен rich text)

**Минусы:**
- Дополнительная зависимость
- Мы не планируем поддерживать HTML в описаниях

**Вердикт:** Пока не нужно но можем добавить если разрешим rich text editor

### Альтернатива 4: Schema validation на уровне БД (CHECK constraints)
**Плюсы:**
- Последняя линия защиты
- Гарантирует целостность даже при прямом доступе к БД

**Минусы:**
- Менее понятные error messages
- Сложнее поддерживать (дублирование логики)

**Вердикт:** Хороший дополнительный слой, добавим в миграциях Alembic

## Consequences

### Плюсы
- **Защита от инъекций**: практически исключает **R2** (SQL injection)
- **Защита от XSS**: снижает **R7** (вредоносный контент)
- **Predictable API**: клиенты сразу знают какие данные валидны
- **Better UX**: понятные error messages в формате RFC7807

### Минусы
- **Больше кода**: нужно писать validators для каждого поля
- **Возможные false positives**: легитимные данные могут не пройти валидацию
- **Maintenance**: при изменении требований нужно обновлять validators

### Влияние на производительность
- Pydantic валидация добавляет ~0.5-2мс на request
- Regex проверки очень быстрые для коротких строк
- Sanitization добавляет negligible overhead
- Итого p95 остается в пределах **NFR-03**

### Security Impact
- **Устранение риска R2** (SQL injection) — снижается с уровня 15 до ~2 (Risk = 1×2)
  - ORM + parameterized queries делают практически невозможным
  - Likelihood падает с 3 до 1
- **Снижение риска R7** (XSS) — с уровня 9 до ~3 (Risk = 1×3)
  - HTML sanitization блокирует основные векторы атак
- **Защита от R9** (переполнение БД) — лимиты предотвращают создание огромных записей

### Связь с STRIDE:
- **F3,F7 (T) — Tampering**: строгая валидация предотвращает модификацию данных через инъекции
- **F3 (I) — Information Disclosure**: лимиты на размер полей защищают от извлечения чувствительных данных

### User Experience
- Быстрая валидация (до обращения к БД)
- Понятные сообщения об ошибках (благодаря ADR-001)
- Пример error response:
  ```json
  {
    "type": "https://api.wishlist.com/errors/validation-failed",
    "title": "Validation Error",
    "status": 400,
    "detail": "title: must be between 1 and 200 characters",
    "correlation_id": "..."
  }
  ```

### Trade-offs
- Жертвуем немного гибкостью (строгие лимиты) ради безопасности
- Потенциальные false positives vs риск инъекций — выбираем безопасность
- Больше кода но значительно безопаснее

## Rollout Plan

### Фаза 1: Schema Updates (Неделя 1)
- [ ] Обновить все Pydantic schemas в `app/schemas/`:
  - Добавить `constr` constraints на строковые поля
  - Добавить validators для sanitization
  - Добавить max limits на все поля
- [ ] Создать общие validators в `app/validators/common.py`:
  - `sanitize_html()` — удаление/экранирование HTML
  - `validate_username()` — regex для username
  - `check_length()` — generic length validator

### Фаза 2: Business Logic Validation (Неделя 1-2)
- [ ] Добавить лимиты в use cases:
  - Максимум 100 wishes per user
  - Проверка на дубликаты title
- [ ] Обновить error handling для validation errors
  - Использовать RFC7807 format (ADR-001)

### Фаза 3: Database Constraints (Неделя 2)
- [ ] Создать Alembic миграции:
  - CHECK constraints на длину полей
  - NOT NULL constraints где нужно
  - UNIQUE constraints для username/email

### Фаза 4: Testing (Неделя 2)
- [ ] Unit тесты для каждого validator:
  - Positive tests (валидные данные)
  - Negative tests (SQL injection, XSS, too long strings)
  - Edge cases (пустые строки, unicode, emoji)
- [ ] Integration тесты:
  - Попытка создать wish с `<script>alert(1)</script>` в title
  - Попытка создать wish с очень длинным description (10MB)
  - Попытка SQL injection в различные поля

### Фаза 5: Security Review (Неделя 2-3)
- [ ] Code review фокус на безопасности
- [ ] Проверка что все endpoints используют validated schemas
- [ ] Проверка что нет raw SQL queries
- [ ] Audit логов на предмет blocked attempts

### Фаза 6: Deployment (Неделя 3)
- [ ] Deploy на staging с monitoring
- [ ] Мониторинг validation errors rate
- [ ] Проверка что легитимные пользователи не блокируются
- [ ] Gradual rollout на production

### Definition of Done (DoD)
- [x] Все schemas имеют explicit constraints
- [x] Все текстовые поля имеют max length
- [x] HTML/JS sanitization работает
- [x] Username проходит regex валидацию
- [x] Database constraints синхронизированы с Pydantic models
- [x] 100% endpoints используют validated schemas
- [x] Negative тесты покрывают основные векторы атак
- [x] Documentation обновлена

### Мониторинг
Метрики для отслеживания:
- `validation_errors_total` counter по полю и типу ошибки
- `blocked_injection_attempts_total` counter для потенциальных атак
- Алерты при резком росте validation errors (возможно атака)

## Links

**NFR (из P03):**
- **NFR-08** — Валидация входных данных (прямое соответствие, 100% параметров валидированы)
- **NFR-03** — Производительность (валидация не должна влиять на p95 latency)

**STRIDE угрозы (из P04):**
- **F3: POST /wishes (T)** — предотвращение tampering через валидацию
- **F7: Database (T)** — защита от SQL injection
- **F3: POST /wishes (I)** — защита от information disclosure через XSS

**Риски (из P04):**
- **R2** — SQL injection (КРИТЕРИЙ ЗАКРЫТИЯ: 100% parameterized queries + input sanitization)
- **R7** — Внедрение вредоносного контента (КРИТЕРИЙ ЗАКРЫТИЯ: CSP + sanitization)
- **R9** — Переполнение базы данных (КРИТЕРИЙ ЗАКРЫТИЯ: Pagination + rate limiting + max field lengths)

**Тесты:**
- `tests/unit/test_validators.py::test_sanitize_html`
- `tests/unit/test_validators.py::test_username_validation`
- `tests/integration/test_api.py::test_sql_injection_blocked`
- `tests/integration/test_api.py::test_xss_blocked`
- `tests/nfr/test_security.py::test_input_validation`

**Связанные ADR:**
- ADR-001 (RFC7807) — validation errors возвращаются в RFC7807 формате
- ADR-002 (Rate Limiting) — дополнительная защита от mass injection attempts
