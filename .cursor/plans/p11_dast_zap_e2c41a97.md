---
name: P11 DAST ZAP
overview: Добавить DAST-сканирование с OWASP ZAP baseline в CI/CD pipeline для автоматической проверки безопасности веб-приложения
todos:
  - id: create-workflow
    content: Создать .github/workflows/ci-p11-dast.yml с адаптированной конфигурацией
    status: completed
  - id: commit-workflow
    content: Закоммитить workflow и запушить в ветку p11-dast-zap
    status: in_progress
  - id: run-actions
    content: Запустить workflow в GitHub Actions и дождаться завершения
    status: pending
  - id: download-reports
    content: Скачать артефакты и добавить отчёты в EVIDENCE/P11/
    status: pending
  - id: create-pr
    content: Создать PR с резюме результатов сканирования
    status: pending
---

# План выполнения P11 - DAST (OWASP ZAP baseline)

## Цель

Встроить автоматическое сканирование безопасности веб-приложения с помощью OWASP ZAP baseline в GitHub Actions CI/CD процесс.

## Что будет сделано

### 1. Создание workflow файла

Создать [`.github/workflows/ci-p11-dast.yml`](.github/workflows/ci-p11-dast.yml) на основе шаблона из `docs/homework_tasks/P11/06_templates/` с адаптацией под текущий проект:

**Ключевые изменения:**

- Health endpoint: `/health` (вместо `/healthz` в шаблоне)
- Target: `http://localhost:8080`
- Entry point: `uvicorn app.main:app --host 0.0.0.0 --port 8080`

### 2. Workflow структура

```yaml
- Checkout репозитория
- Создание директории EVIDENCE/P11
- Установка Python 3.11 и зависимостей
- Запуск FastAPI приложения в фоне
- Health check с таймаутом 30 секунд
- Запуск ZAP baseline против localhost:8080
- Перемещение отчётов в EVIDENCE/P11/
- Upload артефактов (всегда выполняется)
```

### 3. ZAP baseline параметры

```bash
docker run owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8080 \
  -r zap_baseline.html \
  -J zap_baseline.json \
  -d
```

### 4. Результаты сканирования

После выполнения workflow:

- Скачать артефакты из GitHub Actions
- Добавить файлы в репозиторий: `EVIDENCE/P11/zap_baseline.*`
- Проанализировать отчёты и подготовить резюме

### 5. Описание PR

Шаблон для описания:

```text
P11 - DAST (ZAP baseline)

Target: http://localhost:8080/
Reports: EVIDENCE/P11/zap_baseline.html, zap_baseline.json
Result: N alerts (High=X, Medium=Y, Low=Z).

План действий:
- исправить реальные проблемы (если есть)
- задокументировать принятые риски/FP
```

## Файлы для изменения

- [`.github/workflows/ci-p11-dast.yml`](.github/workflows/ci-p11-dast.yml) - создать новый workflow
- [`EVIDENCE/P11/`](EVIDENCE/P11/) - добавить отчёты после запуска

## Ожидаемый результат

- ✅ Workflow успешно выполняется в Actions (зелёный статус)
- ✅ Генерируются отчёты HTML и JSON
- ✅ Отчёты сохранены в `EVIDENCE/P11/`
- ✅ PR содержит резюме с результатами сканирования и планом действий
