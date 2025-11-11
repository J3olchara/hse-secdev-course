# STRIDE — Угрозы и контроли

## Методология анализа
**STRIDE категории:**
- **S** (Spoofing): Подмена идентичности
- **T** (Tampering): Модификация данных
- **R** (Repudiation): Отрицание действий
- **I** (Information Disclosure): Утечка информации
- **D** (Denial of Service): Отказ в обслуживании
- **E** (Elevation of Privilege): Повышение привилегий

| Поток/Элемент | Угроза (S/T/R/I/D/E) | Описание угрозы | Контроль | Ссылка на NFR | Проверка/Артефакт |
|---------------|-----------------------|------------------|----------|---------------|-------------------|
| **F1: POST /auth/login** | S | Атакующий может подменить легитимного пользователя и войти в систему | MFA, CAPTCHA, rate limiting | **NFR-06** (Rate limiting), **NFR-01** (Пароли) | Интеграционные тесты аутентификации + penetration testing |
| **F1: POST /auth/login** | T | Перехват и модификация учетных данных в транзите | TLS 1.3, HSTS, certificate pinning | **NFR-09** (Security headers) | SSL Labs rating A+, certificate transparency logs |
| **F1: POST /auth/login** | I | Утечка учетных данных при обработке логина | Не логировать пароли, sanitization | **NFR-01** (Пароли), **NFR-02** (Ошибки RFC7807) | Code review, secret scanning в CI, аудит логов |
| **F1: POST /auth/login** | D | DoS атака на эндпоинт аутентификации | Rate limiting, circuit breaker | **NFR-06** (Rate limiting), **NFR-03** (Производительность) | Нагрузочный тест (p95 ≤ 300мс при 50 RPS) |
| **F2: GET /wishes** | S | Несанкционированный доступ к чужим желаниям | JWT validation, session management | **NFR-05** (Ротация секретов) | Интеграционные тесты с невалидными токенами |
| **F2: GET /wishes** | I | Утечка списка желаний других пользователей | Row Level Security (RLS) | **NFR-07** (Шифрование данных) | Логи доступа к БД, аудит приватности |
| **F3: POST /wishes** | T | Внедрение вредоносного контента в желания | Input validation, sanitization, CSP | **NFR-08** (Валидация ввода) | Unit тесты с вредоносными payloads |
| **F3: POST /wishes** | I | Разглашение чувствительной информации в описаниях желаний | Content filtering, PII detection | **NFR-07** (Шифрование данных) | Content scanning, GDPR compliance check |
| **F4: PATCH /wishes/{id}** | E | Пользователь модифицирует чужие желания | Authorization checks, ownership validation | **NFR-05** (Ротация секретов) | Авторизационные unit тесты |
| **F4: PATCH /wishes/{id}** | R | Пользователь отрицает факт изменения желания | Audit logging, digital signatures | **NFR-10** (Аудит действий) | Анализ логов, tamper detection |
| **F5: DELETE /wishes/{id}** | E | Удаление чужих ресурсов | Strict authorization, confirmation dialogs | **NFR-05** (Ротация секретов) | Penetration testing авторизации |
| **F5: DELETE /wishes/{id}** | R | Отрицание факта удаления | Immutable audit trail, soft deletes | **NFR-10** (Аудит действий) | Проверка целостности бэкапов |
| **F6: JWT Manager** | T | Манипуляция JWT токенами | Strong algorithms (RS256), short expiration | **NFR-05** (Ротация секретов) | Анализ безопасности JWT, тесты ротации токенов |
| **F6: JWT Manager** | I | Разглашение секретного ключа JWT | Secure key storage, key rotation | **NFR-05** (Ротация секретов) | Аудит управления секретами, политика ротации ключей |
| **F7: Database** | T | SQL injection в запросах | ORM with parameterization, input validation | **NFR-08** (Валидация ввода) | Сканирование SQL injection, только подготовленные запросы |
| **F7: Database** | I | Несанкционированный доступ к базе данных | Database encryption at rest, access controls | **NFR-07** (Шифрование данных) | Оценка безопасности БД, аудит шифрования |
| **F7: Database** | D | Переполнение базы данных большим количеством желаний | Pagination, rate limiting per user | **NFR-06** (Rate limiting) | Тестирование производительности с большими датасетами |
| **API Gateway** | D | DDoS атака на весь сервис | WAF, rate limiting, geo-blocking | **NFR-06** (Rate limiting) | Симуляционное тестирование DDoS, валидация правил WAF |
| **External Services** | I | Зависимость от внешних сервисов может привести к утечке данных | Vendor assessment, contract clauses | **NFR-04** (Уязвимости зависимостей) | Опросник безопасности вендора, review контрактов |

## Исключения и обоснования
**Не применимо для данного контекста:**
- **Spoofing внешних сервисов (F2)**: В текущей архитектуре нет интеграции с внешними сервисами, требующими аутентификации
- **Elevation of Privilege в базе данных**: Используется один сервисный аккаунт с минимальными правами
