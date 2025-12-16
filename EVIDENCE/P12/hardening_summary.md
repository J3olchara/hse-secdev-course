# Hardening Summary - P12

## Dockerfile Hardening

### До:
- Использовался базовый образ python:3.11-slim без фиксации версий пакетов
- Процесс запускался от root
- Не было явных ограничений на capabilities

### После:
- Фиксированные версии базового образа (python:3.11-slim)
- Фиксированные версии системных пакетов (curl, libpq5, libpq-dev, gcc, libffi-dev)
- Создан non-root пользователь appuser (UID 1000)
- Процесс запускается от appuser
- Настроены права доступа (chmod 755 /app, chmod 500 /app/app)
- Multi-stage build для уменьшения размера образа

## Kubernetes IaC Hardening

### До:
- Использовался тег latest для образа приложения
- Базовые securityContext настройки

### После:
- Заменен тег latest на конкретную версию (wishlist-app:v1.0)
- Настроен pod-level securityContext:
  - runAsNonRoot: true
  - runAsUser: 1000
  - fsGroup: 1000
  - seccompProfile: RuntimeDefault
- Настроен container-level securityContext:
  - allowPrivilegeEscalation: false
  - runAsNonRoot: true
  - runAsUser: 1000
  - capabilities.drop: ALL
- Конфигурация через SecretKeyRef (DATABASE_URL, JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY)
- Настроены liveness и readiness probes
- Ограничены ресурсы (requests/limits)
- Service типа ClusterIP (не экспонируется наружу)

## Security Scanning Integration

- Hadolint: проверка Dockerfile с использованием security/hadolint.yaml
- Checkov: проверка k8s манифестов с использованием security/checkov.yaml
- Trivy: сканирование собранного образа на уязвимости
