P12 - IaC & Container Security

## Выполненные критерии на ★★ (расширенный уровень)

### C1. Hadolint — проверка Dockerfile ★★
- Использован конфиг `security/hadolint.yaml` в workflow через флаг `--config`
- Dockerfile соответствует best practices: фиксированные версии пакетов, non-root user, multi-stage build
- Отчёт сохраняется в `EVIDENCE/P12/hadolint_report.json`

### C2. Checkov — проверка IaC ★★
- `security/checkov.yaml` содержит базовую настройку (framework: kubernetes, terraform, dockerfile)
- Отработана находка Checkov: заменён тег `latest` на конкретную версию `wishlist-app:v1.0` в `k8s/deployment.yaml`
- Отчёт сохраняется в `EVIDENCE/P12/checkov_report.json`

### C3. Trivy — проверка образа ★★
- Trivy запускается в CI по собранному образу `app:local`
- Отчёт сохраняется в `EVIDENCE/P12/trivy_report.json`
- После запуска workflow будет добавлен summary по критичным/высоким findings

### C4. Меры харднинга Dockerfile и IaC ★★
- Dockerfile:
  - Не используется `latest` (фиксированные версии: python:3.11-slim, пакеты с версиями)
  - Контейнер переведён на non-root user (appuser, UID 1000)
  - Настроены права доступа (chmod 755 /app, chmod 500 /app/app)
  - Multi-stage build для уменьшения размера образа
- IaC (k8s):
  - Заменён тег `latest` на `v1.0`
  - Настроен pod-level securityContext (runAsNonRoot, runAsUser, fsGroup, seccompProfile)
  - Настроен container-level securityContext (allowPrivilegeEscalation: false, capabilities.drop: ALL)
  - Конфигурация через SecretKeyRef (DATABASE_URL, JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY)
  - Service типа ClusterIP (не экспонируется наружу)
  - Настроены liveness и readiness probes
- Оформлен `EVIDENCE/P12/hardening_summary.md` с описанием до/после

### C5. Интеграция в CI ★★
- Создан `.github/workflows/ci-p12-iac-container.yml`:
  - Настроен `concurrency` с `cancel-in-progress: true` для предотвращения накопления запусков
  - Разумные триггеры: `workflow_dispatch` + `push` по путям `Dockerfile`, `k8s/**`, `security/**`, `iac/**`, `deploy/**`
  - Все три отчёта (hadolint, checkov, trivy) попадают в `EVIDENCE/P12/` и загружаются как артефакт `P12_EVIDENCE`

## Отчёты
- Hadolint: `EVIDENCE/P12/hadolint_report.json`
- Checkov: `EVIDENCE/P12/checkov_report.json`
- Trivy: `EVIDENCE/P12/trivy_report.json`

## Hardening Summary
Детальное описание применённых мер харднинга: `EVIDENCE/P12/hardening_summary.md`
