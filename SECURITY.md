# Security Policy

## Reporting Security Issues

- Пожалуйста, **не** создавайте публичные issues для уязвимостей
- Сообщайте об уязвимостях преподавателю/ТА через приватный канал
- Используйте email или личные сообщения для сообщений о критических багах

## Security Practices (согласно ADR)

### Управление секретами (ADR-003)
- **НЕ** храните ключи/секреты в репозитории
- Используйте переменные окружения для всех чувствительных данных
- SECRET_KEY должен быть минимум 32 символа
- Ротируйте JWT ключи каждые 30 дней (NFR-05)
- Генерируйте секреты с помощью `scripts/generate_secrets.py`

### Валидация данных (ADR-004)
- Все входные данные проходят строгую валидацию
- Защита от SQL Injection через ORM
- Защита от XSS через sanitization HTML/JS
- Лимиты на длину полей:
  - username: 3-50 символов
  - wish title: 1-200 символов
  - wish description: до 5000 символов

### Обработка ошибок (ADR-001)
- Все ошибки в формате RFC 7807
- Технические детали скрыты в production
- Каждая ошибка имеет correlation_id для отладки
- Секреты не попадают в error messages

### Rate Limiting (ADR-002)
- /auth/login: максимум 5 попыток в минуту на IP
- Защита от брутфорс атак
- Автоматическая блокировка при превышении лимитов

## Best Practices

- Во время курса используйте **синтетические** данные (без ПДн/платежей)
- Всегда используйте HTTPS в production
- Регулярно обновляйте зависимости (проверка на уязвимости)
- Проводите code review с фокусом на безопасность

## Compliance

Проект следует следующим стандартам:
- OWASP Top 10 (защита от основных уязвимостей)
- RFC 7807 (Problem Details for HTTP APIs)
- GDPR best practices (защита персональных данных)

## References

См. также:
- [ADR-001](docs/adr/ADR-001-rfc7807-error-handling.md) - Обработка ошибок
- [ADR-002](docs/adr/ADR-002-rate-limiting-auth.md) - Rate Limiting
- [ADR-003](docs/adr/ADR-003-secrets-management.md) - Управление секретами
- [ADR-004](docs/adr/ADR-004-input-validation.md) - Валидация входных данных
- [NFR.md](P03/NFR.md) - Нефункциональные требования
- [STRIDE.md](P04/STRIDE.md) - Threat Model
- [RISKS.md](P04/RISKS.md) - Реестр рисков
