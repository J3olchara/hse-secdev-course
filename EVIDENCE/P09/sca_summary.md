# SCA Summary

Generated: Mon Nov 24 18:03:53 UTC 2025

{
  "Critical": 1,
  "High": 6,
  "Medium": 2
}
- High: GHSA-2jv5-9r88-3w3p in python-multipart@0.0.6
- High: GHSA-2jv5-9r88-3w3p in python-multipart@0.0.6
- Critical: GHSA-6c5p-j8vq-pqhj in python-jose@3.3.0
- High: GHSA-wj6h-64fc-37mp in ecdsa@0.19.1
- High: GHSA-59g5-xgcq-4qw3 in python-multipart@0.0.6
- High: GHSA-59g5-xgcq-4qw3 in python-multipart@0.0.6
- High: GHSA-f96h-pmfr-66vw in starlette@0.38.6

## Комментарий

Нашлось довольно много проблем, особенно в python-multipart и python-jose. 
Критичная уязвимость в python-jose связана с обработкой JWT токенов - нужно обновить или сделать waiver.
python-multipart тоже требует внимания, там несколько High severity.

План действий:
1. Обновить python-multipart до последней версии если есть фикс
2. Проверить можем ли обновить python-jose или нужен waiver
3. Остальные уязвимости оценить по реальным рискам для нашего проекта
