"""
NFR тесты надежности и стабильности (Reliability Tests).

Проверяют:
- Стабильность работы под нагрузкой
- Устойчивость к ошибкам
- Восстановление после сбоев
- Consistency данных

NOTE: эти тесты важны для продакшна!
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Клиент для тестов надежности."""
    return TestClient(app)


class TestServiceAvailability:
    """Тесты доступности сервиса."""

    def test_health_check_always_available(self, client):
        """Проверка, что health check всегда доступен."""
        # Выполняем множество запросов подряд
        for _ in range(100):
            response = client.get("/health")
            assert (
                response.status_code == 200
            ), "Health check should always be available"
            assert response.json() == {"status": "ok"}

    @pytest.mark.timeout(10)
    def test_continuous_availability(self, client):
        """Проверка непрерывной доступности."""
        duration = 5  # секунд
        failures = []
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                response = client.get("/health")
                if response.status_code != 200:
                    failures.append(f"Status {response.status_code}")
            except Exception as e:
                failures.append(str(e))

        # Не должно быть отказов
        assert len(failures) == 0, f"Service unavailable: {failures}"


class TestErrorRecovery:
    """Тесты восстановления после ошибок."""

    def test_recovery_after_invalid_request(self, client):
        """Проверка восстановления после некорректного запроса."""
        # Отправляем некорректный запрос
        bad_response = client.post("/items?name=")
        assert bad_response.status_code == 422

        # Следующие запросы должны работать нормально
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

        # Нормальный запрос должен работать
        good_response = client.post("/items?name=ValidItem")
        assert good_response.status_code == 200

    def test_recovery_after_not_found(self, client):
        """Проверка восстановления после 404 ошибки."""
        # Запрашиваем несуществующий item
        not_found_response = client.get("/items/99999")
        assert not_found_response.status_code == 404

        # Сервис должен продолжать работать
        response = client.get("/health")
        assert response.status_code == 200

    def test_multiple_errors_handling(self, client):
        """Проверка обработки множественных ошибок подряд."""
        # Генерируем различные ошибки
        error_requests = [
            lambda: client.post("/items?name="),  # Validation error
            lambda: client.get("/items/99999"),  # Not found
            lambda: client.get("/nonexistent"),  # Invalid endpoint
            lambda: client.post("/items?name=" + "A" * 1000),  # Too long
        ]

        for _ in range(5):
            for error_request in error_requests:
                error_request()

        # После всех ошибок сервис должен работать
        response = client.get("/health")
        assert response.status_code == 200


class TestDataConsistency:
    """Тесты консистентности данных."""

    def test_item_crud_consistency(self, client):
        """Проверка консистентности CRUD операций."""
        # Создаем item
        create_response = client.post("/items?name=TestItem")
        assert create_response.status_code == 200
        item_data = create_response.json()
        item_id = item_data["id"]

        # Читаем созданный item
        read_response = client.get(f"/items/{item_id}")
        assert read_response.status_code == 200
        assert read_response.json()["name"] == "TestItem"

        # Данные должны быть идентичны
        assert read_response.json()["id"] == item_id

    def test_concurrent_reads_consistency(self, client):
        """Проверка консистентности при параллельном чтении."""
        # Создаем item
        create_response = client.post("/items?name=ConcurrentTest")
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Читаем параллельно
        def read_item():
            response = client.get(f"/items/{item_id}")
            return response.json()

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_item) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]

        # Все результаты должны быть идентичны
        first_result = results[0]
        for result in results:
            assert (
                result == first_result
            ), "Inconsistent data in concurrent reads"

    def test_sequential_operations_consistency(self, client):
        """Проверка консистентности последовательных операций."""
        created_items = []

        # Создаем несколько items
        for i in range(10):
            response = client.post(f"/items?name=Item{i}")
            assert response.status_code == 200
            created_items.append(response.json())

        # Проверяем, что все созданы правильно
        for item in created_items:
            response = client.get(f"/items/{item['id']}")
            assert response.status_code == 200
            assert response.json()["id"] == item["id"]


class TestStabilityUnderLoad:
    """Тесты стабильности под нагрузкой."""

    @pytest.mark.timeout(15)
    def test_stability_with_mixed_operations(self, client):
        """Проверка стабильности при смешанных операциях."""
        operations = []
        errors = []

        # Выполняем смешанные операции
        for i in range(100):
            try:
                # Создание
                if i % 3 == 0:
                    response = client.post(f"/items?name=Item{i}")
                    operations.append(("create", response.status_code))

                # Чтение
                elif i % 3 == 1:
                    response = client.get(f"/items/{i % 10 + 1}")
                    operations.append(("read", response.status_code))

                # Health check
                else:
                    response = client.get("/health")
                    operations.append(("health", response.status_code))

            except Exception as e:
                errors.append(str(e))

        # Не должно быть критических ошибок
        assert len(errors) == 0, f"Errors during mixed operations: {errors}"

        # Большинство операций должны быть успешными
        successful = sum(
            1 for op, status in operations if status in [200, 404]
        )
        success_rate = successful / len(operations) * 100
        assert success_rate >= 95, f"Success rate too low: {success_rate:.2f}%"

    @pytest.mark.timeout(20)
    def test_concurrent_write_stability(self, client):
        """Проверка стабильности при параллельной записи."""
        errors = []
        successful_creates = []

        def create_item(index):
            try:
                response = client.post(f"/items?name=ConcurrentItem{index}")
                return response.status_code == 200
            except Exception as e:
                errors.append(str(e))
                return False

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_item, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
            successful_creates = [r for r in results if r]

        # Не должно быть ошибок
        assert len(errors) == 0, f"Errors during concurrent writes: {errors}"

        # Большинство записей должны быть успешными
        success_rate = len(successful_creates) / 50 * 100
        assert (
            success_rate >= 90
        ), f"Too many failed writes: {success_rate:.2f}%"


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_zero_and_negative_ids(self, client):
        """Проверка обработки нулевых и отрицательных ID."""
        test_ids = [0, -1, -100]

        for item_id in test_ids:
            response = client.get(f"/items/{item_id}")
            # Должна быть обработана корректно (404 или 422)
            assert response.status_code in [404, 422]

    def test_very_large_ids(self, client):
        """Проверка обработки очень больших ID."""
        large_ids = [999999, 2**31 - 1, 2**63 - 1]

        for item_id in large_ids:
            response = client.get(f"/items/{item_id}")
            # Должна быть обработана корректно
            assert response.status_code in [404, 422]

    def test_boundary_string_values(self, client):
        """Проверка граничных значений строк."""
        test_cases = [
            ("a", 200),  # Минимальная длина (1 символ)
            ("a" * 100, 200),  # Максимальная длина (100 символов)
            ("", 422),  # Пустая строка (должна отклониться)
            ("a" * 101, 422),  # Превышение максимума
        ]

        for name, expected_status in test_cases:
            response = client.post(f"/items?name={name}")
            assert (
                response.status_code == expected_status
            ), f"Failed for name '{name}' (len={len(name)})"

    def test_special_id_values(self, client):
        """Проверка специальных значений ID."""
        special_values = [
            "abc",  # Буквы
            "1.5",  # Дробное число
            "1e10",  # Научная нотация
        ]

        for value in special_values:
            response = client.get(f"/items/{value}")
            # Должна быть ошибка валидации
            assert response.status_code in [404, 422]


class TestLongRunning:
    """Тесты длительной работы."""

    @pytest.mark.slow
    @pytest.mark.timeout(60)
    def test_extended_operation_stability(self, client):
        """Проверка стабильности при длительной работе."""
        duration = 30  # секунд
        operations = []
        errors = []
        start_time = time.time()

        operation_count = 0

        while time.time() - start_time < duration:
            operation_count += 1
            try:
                # Чередуем операции
                if operation_count % 10 == 0:
                    # Создание
                    response = client.post(
                        f"/items?name=Item{operation_count}"
                    )
                    operations.append(("create", response.status_code))
                elif operation_count % 10 == 5:
                    # Чтение существующего
                    response = client.get(
                        f"/items/{(operation_count % 100) + 1}"
                    )
                    operations.append(("read_existing", response.status_code))
                else:
                    # Health check
                    response = client.get("/health")
                    operations.append(("health", response.status_code))

            except Exception as e:
                errors.append((operation_count, str(e)))

        # Анализ результатов
        total_ops = len(operations)
        successful_ops = sum(
            1 for op, status in operations if status in [200, 404]
        )
        success_rate = successful_ops / total_ops * 100 if total_ops > 0 else 0

        # Требования
        assert (
            len(errors) < total_ops * 0.01
        ), f"Too many errors: {len(errors)}"
        assert (
            success_rate >= 99.0
        ), f"Success rate too low: {success_rate:.2f}%"
        assert total_ops > 100, f"Too few operations completed: {total_ops}"


@pytest.mark.slow
class TestFailureScenarios:
    """Тесты сценариев отказа."""

    @pytest.mark.timeout(15)
    def test_recovery_from_burst_errors(self, client):
        """Проверка восстановления после всплеска ошибок."""
        # Генерируем всплеск ошибок
        for _ in range(50):
            client.post("/items?name=")  # Validation error
            client.get("/items/99999")  # Not found
            client.get("/nonexistent")  # Invalid endpoint

        # Проверяем, что сервис восстановился
        successful_requests = 0
        for _ in range(20):
            response = client.get("/health")
            if response.status_code == 200:
                successful_requests += 1

        # Должны быть успешными все или почти все запросы
        assert (
            successful_requests >= 19
        ), f"Service didn't recover: {successful_requests}/20 successful"

    def test_alternating_success_and_failure(self, client):
        """Проверка чередования успешных и неуспешных запросов."""
        results = []

        for i in range(100):
            if i % 2 == 0:
                # Успешный запрос
                response = client.get("/health")
                results.append(response.status_code == 200)
            else:
                # Неуспешный запрос
                response = client.get("/items/99999")
                results.append(response.status_code == 404)

        # Все запросы должны быть обработаны корректно
        success_rate = sum(results) / len(results) * 100
        assert (
            success_rate == 100
        ), f"Some requests not handled correctly: {success_rate:.2f}%"
