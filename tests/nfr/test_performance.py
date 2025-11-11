"""
NFR тесты производительности (Non-Functional Requirements).

Проверяют:
- Время отклика API endpoints
- Пропускную способность
- Использование памяти
- Производительность базы данных

TODO: добавить больше тестов для конкретных эндпоинтов
"""

import time
from concurrent.futures import ThreadPoolExecutor

import psutil
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Клиент для тестирования производительности."""
    return TestClient(app)


class TestResponseTime:
    """Тесты времени отклика."""

    def test_health_endpoint_response_time(self, client, benchmark):
        """Проверка времени отклика /health."""

        def health_check():
            response = client.get("/health")
            assert response.status_code == 200
            return response

        result = benchmark(health_check)
        assert result.status_code == 200

        # TODO: maybe 100ms слишком строго? посмотреть на проде
        # Время отклика должно быть меньше 100ms
        assert (
            benchmark.stats["mean"] < 0.1
        ), f"Response time too slow: {benchmark.stats['mean']:.4f}s"

    @pytest.mark.timeout(5)
    def test_health_endpoint_under_load(self, client):
        """Проверка /health под нагрузкой (100 запросов)."""
        start_time = time.time()
        successful_requests = 0
        total_requests = 100

        for _ in range(total_requests):
            response = client.get("/health")
            if response.status_code == 200:
                successful_requests += 1

        elapsed_time = time.time() - start_time

        # Все запросы должны быть успешными
        assert (
            successful_requests == total_requests
        ), f"Only {successful_requests}/{total_requests} succeeded"

        # Среднее время на запрос должно быть меньше 50ms
        avg_time = elapsed_time / total_requests
        assert (
            avg_time < 0.05
        ), f"Average request time too slow: {avg_time:.4f}s"

        # Общее время должно быть меньше 5 секунд
        assert elapsed_time < 5.0, f"Total time too slow: {elapsed_time:.2f}s"

    @pytest.mark.timeout(10)
    def test_concurrent_requests(self, client):
        """Проверка параллельных запросов."""
        num_requests = 50

        def make_request():
            response = client.get("/health")
            return response.status_code == 200

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(
                executor.map(lambda _: make_request(), range(num_requests))
            )

        elapsed_time = time.time() - start_time

        # Все запросы должны быть успешными
        assert all(results), "Some concurrent requests failed"

        # Должны обработаться быстрее чем последовательно
        assert (
            elapsed_time < num_requests * 0.05
        ), f"Concurrent requests too slow: {elapsed_time:.2f}s"

    def test_items_create_performance(self, client, benchmark):
        """Проверка производительности создания items."""

        def create_item():
            response = client.post("/items?name=TestItem")
            assert response.status_code == 200
            return response

        benchmark(create_item)

        # Создание должно быть быстрым (< 200ms)
        assert (
            benchmark.stats["mean"] < 0.2
        ), f"Item creation too slow: {benchmark.stats['mean']:.4f}s"


class TestMemoryUsage:
    """Тесты использования памяти."""

    def test_memory_leak_detection(self, client):
        """Проверка отсутствия утечек памяти."""
        process = psutil.Process()

        # Начальное использование памяти
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Выполняем 1000 запросов
        for i in range(1000):
            response = client.get("/health")
            assert response.status_code == 200

            # создаем и удаляем items
            if i % 10 == 0:
                client.post(f"/items?name=Item{i}")

        # Конечное использование памяти
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # FIXME: 50MB может быть слишком мало для некоторых систем
        # Рост памяти не должен превышать 50MB
        memory_growth = final_memory - initial_memory
        assert (
            memory_growth < 50
        ), f"Memory leak detected: grew by {memory_growth:.2f}MB"

    @pytest.mark.timeout(5)
    def test_endpoint_memory_efficiency(self, client):
        """Проверка эффективности использования памяти endpoints."""
        process = psutil.Process()

        endpoints = [
            ("/health", "GET"),
            ("/items?name=Test", "POST"),
        ]

        for endpoint, method in endpoints:
            memory_before = process.memory_info().rss / 1024 / 1024

            # Выполняем 100 запросов
            for _ in range(100):
                if method == "GET":
                    client.get(endpoint)
                else:
                    client.post(endpoint)

            memory_after = process.memory_info().rss / 1024 / 1024
            memory_used = memory_after - memory_before

            # На 100 запросов не должно использоваться больше 10MB
            assert (
                memory_used < 10
            ), f"Endpoint {endpoint} uses too much memory: {memory_used:.2f}MB"


class TestThroughput:
    """Тесты пропускной способности."""

    @pytest.mark.timeout(10)
    def test_requests_per_second(self, client):
        """Проверка количества запросов в секунду."""
        duration = 5  # секунд
        request_count = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            response = client.get("/health")
            if response.status_code == 200:
                request_count += 1

        elapsed_time = time.time() - start_time
        rps = request_count / elapsed_time

        # Должно быть минимум 100 запросов в секунду
        assert rps >= 100, f"Throughput too low: {rps:.2f} req/s"

    @pytest.mark.timeout(15)
    def test_sustained_load(self, client):
        """Проверка стабильности под продолжительной нагрузкой."""
        duration = 10  # секунд
        errors = 0
        success = 0
        start_time = time.time()

        response_times = []

        while time.time() - start_time < duration:
            req_start = time.time()
            response = client.get("/health")
            req_time = time.time() - req_start

            response_times.append(req_time)

            if response.status_code == 200:
                success += 1
            else:
                errors += 1

        total_requests = success + errors
        error_rate = errors / total_requests if total_requests > 0 else 0
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        # Количество ошибок должно быть меньше 1%
        assert (
            error_rate < 0.01
        ), f"Error rate too high: {error_rate * 100:.2f}%"

        # Среднее время отклика должно быть стабильным
        assert (
            avg_response_time < 0.1
        ), f"Average response time degraded: {avg_response_time:.4f}s"


class TestDatabasePerformance:
    """Тесты производительности базы данных."""

    @pytest.mark.timeout(5)
    def test_multiple_item_operations(self, client):
        """Проверка производительности множественных операций с items."""
        start_time = time.time()

        # Создаем 100 items
        created_ids = []
        for i in range(100):
            response = client.post(f"/items?name=Item{i}")
            if response.status_code == 200:
                created_ids.append(response.json()["id"])

        create_time = time.time() - start_time

        # Читаем все созданные items
        read_start = time.time()
        for item_id in created_ids:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 200

        read_time = time.time() - read_start

        # Создание 100 записей должно занять меньше 3 секунд
        assert (
            create_time < 3.0
        ), f"Creating 100 items too slow: {create_time:.2f}s"

        # Чтение 100 записей должно занять меньше 2 секунд
        assert read_time < 2.0, f"Reading 100 items too slow: {read_time:.2f}s"


@pytest.mark.slow
class TestStressTests:
    """Стресс-тесты."""

    @pytest.mark.timeout(30)
    def test_high_load_stress(self, client):
        """Стресс-тест с высокой нагрузкой."""
        total_requests = 1000
        failed_requests = 0
        slow_requests = 0
        response_times = []

        start_time = time.time()

        for i in range(total_requests):
            req_start = time.time()
            try:
                response = client.get("/health")
                req_time = time.time() - req_start
                response_times.append(req_time)

                if response.status_code != 200:
                    failed_requests += 1

                if req_time > 0.5:  # 500ms
                    slow_requests += 1

            except Exception:
                failed_requests += 1

        total_time = time.time() - start_time

        # Показатели производительности
        success_rate = (
            (total_requests - failed_requests) / total_requests * 100
        )
        throughput = total_requests / total_time

        # Критерии успеха
        assert (
            success_rate >= 99.0
        ), f"Success rate too low: {success_rate:.2f}%"
        assert (
            slow_requests < total_requests * 0.05
        ), f"Too many slow requests: {slow_requests}"
        assert throughput >= 50, f"Throughput too low: {throughput:.2f} req/s"
