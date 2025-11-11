"""
NFR тесты масштабируемости (Scalability Tests).

Проверяют:
- Поведение при увеличении нагрузки
- Эффективность использования ресурсов
- Деградацию производительности
"""

import time
from concurrent.futures import ThreadPoolExecutor

import psutil
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Клиент для тестов масштабируемости."""
    return TestClient(app)


class TestLoadScalability:
    """Тесты масштабируемости нагрузки."""

    @pytest.mark.timeout(20)
    def test_increasing_load_performance(self, client):
        """Проверка производительности при увеличении нагрузки."""
        load_levels = [10, 50, 100, 200]
        results = {}

        for load in load_levels:
            start_time = time.time()
            successful = 0

            for _ in range(load):
                response = client.get("/health")
                if response.status_code == 200:
                    successful += 1

            elapsed = time.time() - start_time
            results[load] = {
                "time": elapsed,
                "success_rate": successful / load * 100,
                "throughput": load / elapsed,
            }

        # Проверяем деградацию производительности
        for i in range(len(load_levels) - 1):
            current_load = load_levels[i]
            next_load = load_levels[i + 1]

            current_throughput = results[current_load]["throughput"]
            next_throughput = results[next_load]["throughput"]

            # Пропускная способность не должна деградировать более чем на 50%
            degradation = (
                (current_throughput - next_throughput)
                / current_throughput
                * 100
            )
            assert (
                degradation < 50
            ), f"Throughput degraded {degradation:.2f}% from {current_load} to {next_load}"

        # Все должны иметь высокий success rate
        for load, result in results.items():
            assert (
                result["success_rate"] >= 95
            ), f"Low success rate at load {load}: {result['success_rate']:.2f}%"

    @pytest.mark.timeout(30)
    def test_concurrent_user_simulation(self, client):
        """Симуляция множества одновременных пользователей."""
        user_counts = [5, 10, 20]
        requests_per_user = 10

        for user_count in user_counts:
            errors = []
            start_time = time.time()

            def simulate_user(user_id):
                user_errors = []
                for req_id in range(requests_per_user):
                    try:
                        # Каждый пользователь делает разные операции
                        if req_id % 3 == 0:
                            response = client.post(
                                f"/items?name=User{user_id}Item{req_id}"
                            )
                        elif req_id % 3 == 1:
                            response = client.get(f"/items/{req_id + 1}")
                        else:
                            response = client.get("/health")

                        if response.status_code not in [200, 404]:
                            user_errors.append(response.status_code)
                    except Exception as e:
                        user_errors.append(str(e))
                return user_errors

            with ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = [
                    executor.submit(simulate_user, i)
                    for i in range(user_count)
                ]
                for future in futures:
                    errors.extend(future.result())

            elapsed = time.time() - start_time
            total_requests = user_count * requests_per_user
            error_rate = len(errors) / total_requests * 100

            # Проверки
            assert (
                error_rate < 5
            ), f"High error rate with {user_count} users: {error_rate:.2f}%"
            assert (
                elapsed < user_count * 2
            ), f"Too slow with {user_count} users: {elapsed:.2f}s"


class TestDataScalability:
    """Тесты масштабируемости данных."""

    @pytest.mark.timeout(30)
    def test_large_dataset_handling(self, client):
        """Проверка работы с большим количеством данных."""
        # Создаем много items
        item_ids = []
        create_times = []

        for i in range(100):
            start = time.time()
            response = client.post(f"/items?name=ScaleItem{i}")
            create_time = time.time() - start
            create_times.append(create_time)

            if response.status_code == 200:
                item_ids.append(response.json()["id"])

        # Проверяем, что время создания не растет линейно
        first_10_avg = sum(create_times[:10]) / 10
        last_10_avg = sum(create_times[-10:]) / 10

        # Последние операции не должны быть существенно медленнее первых
        slowdown = (last_10_avg / first_10_avg - 1) * 100
        assert slowdown < 100, f"Create time increased by {slowdown:.2f}%"

        # Читаем все созданные items
        read_times = []
        for item_id in item_ids[:50]:  # Читаем первые 50
            start = time.time()
            response = client.get(f"/items/{item_id}")
            read_time = time.time() - start
            read_times.append(read_time)
            assert response.status_code == 200

        # Чтение должно оставаться быстрым
        avg_read_time = sum(read_times) / len(read_times)
        assert (
            avg_read_time < 0.1
        ), f"Average read time too slow: {avg_read_time:.4f}s"

    @pytest.mark.timeout(15)
    def test_varying_data_sizes(self, client):
        """Проверка работы с данными разного размера."""
        sizes = [10, 50, 100]  # Длина имени
        results = {}

        for size in sizes:
            name = "A" * size
            start_time = time.time()

            response = client.post(f"/items?name={name}")
            create_time = time.time() - start_time

            if response.status_code == 200:
                item_id = response.json()["id"]

                # Читаем обратно
                read_start = time.time()
                read_response = client.get(f"/items/{item_id}")
                read_time = time.time() - read_start

                results[size] = {
                    "create_time": create_time,
                    "read_time": read_time,
                    "success": read_response.status_code == 200,
                }

        # Все операции должны быть успешными
        for size, result in results.items():
            assert result["success"], f"Failed for size {size}"

            # Время не должно расти пропорционально размеру
            assert (
                result["create_time"] < 0.5
            ), f"Create too slow for size {size}"
            assert result["read_time"] < 0.5, f"Read too slow for size {size}"


class TestResourceEfficiency:
    """Тесты эффективности использования ресурсов."""

    @pytest.mark.timeout(20)
    def test_memory_usage_scaling(self, client):
        """Проверка масштабирования использования памяти."""
        process = psutil.Process()

        # Начальная память
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Создаем много items
        for i in range(500):
            client.post(f"/items?name=MemoryTest{i}")

        # Конечная память
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_increase = final_memory - initial_memory

        # Увеличение памяти должно быть разумным
        assert (
            memory_increase < 100
        ), f"Memory increased too much: {memory_increase:.2f}MB"

        # Проверяем, что сервис все еще работает эффективно
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.timeout(15)
    def test_cpu_usage_under_load(self, client):
        """Проверка использования CPU под нагрузкой."""
        process = psutil.Process()

        # замеряем CPU usage во время нагрузки
        cpu_samples = []

        start_time = time.time()
        request_count = 0

        while time.time() - start_time < 5:
            client.get("/health")
            request_count += 1

            # собираем samples CPU
            if request_count % 10 == 0:
                cpu_percent = process.cpu_percent(interval=0.1)
                cpu_samples.append(cpu_percent)

        # CPU не должен быть перегружен
        if cpu_samples:
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            # средняя загрузка CPU должна быть разумной
            # (это зависит от системы, поэтому берем щадящий лимит)
            # в тестовой среде CPU может быть выше чем в проде
            # TODO: надо проверить на реальной нагрузке
            assert avg_cpu < 150, f"CPU usage too high: {avg_cpu:.2f}%"


@pytest.mark.slow
class TestExtremeCases:
    """Тесты экстремальных случаев."""

    @pytest.mark.timeout(60)
    def test_extended_high_load(self, client):
        """Проверка продолжительной высокой нагрузки."""
        duration = 30  # секунд
        errors = []
        successes = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                response = client.get("/health")
                if response.status_code == 200:
                    successes += 1
                else:
                    errors.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        total_requests = successes + len(errors)
        success_rate = (
            successes / total_requests * 100 if total_requests > 0 else 0
        )

        # Требования
        assert success_rate >= 99, f"Success rate too low: {success_rate:.2f}%"
        assert (
            total_requests > 500
        ), f"Too few requests completed: {total_requests}"

    @pytest.mark.timeout(30)
    def test_burst_load_handling(self, client):
        """Проверка обработки всплесков нагрузки."""

        def burst_requests(count):
            errors = 0
            for _ in range(count):
                try:
                    response = client.get("/health")
                    if response.status_code != 200:
                        errors += 1
                except Exception:
                    errors += 1
            return errors

        # Серия всплесков
        burst_sizes = [50, 100, 50, 100, 50]
        all_errors = []

        for burst_size in burst_sizes:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(burst_requests, burst_size // 10)
                    for _ in range(10)
                ]
                errors = sum(future.result() for future in futures)
                all_errors.append(errors)

            # Небольшая пауза между всплесками
            time.sleep(0.5)

        # Проверяем результаты
        total_errors = sum(all_errors)
        total_requests = sum(burst_sizes)
        error_rate = total_errors / total_requests * 100

        assert (
            error_rate < 5
        ), f"High error rate during bursts: {error_rate:.2f}%"


class TestPerformanceDegradation:
    """Тесты деградации производительности."""

    @pytest.mark.timeout(25)
    def test_performance_consistency(self, client):
        """Проверка консистентности производительности."""
        # Измеряем производительность в разные моменты времени
        measurements = []

        for round_num in range(5):
            start_time = time.time()
            request_count = 0

            # Выполняем запросы в течение 2 секунд
            while time.time() - start_time < 2:
                response = client.get("/health")
                if response.status_code == 200:
                    request_count += 1

            elapsed = time.time() - start_time
            throughput = request_count / elapsed
            measurements.append(throughput)

            # Небольшая пауза между измерениями
            time.sleep(0.5)

        # Проверяем стабильность
        avg_throughput = sum(measurements) / len(measurements)
        for i, throughput in enumerate(measurements):
            deviation = abs(throughput - avg_throughput) / avg_throughput * 100
            assert (
                deviation < 30
            ), f"High deviation in round {i+1}: {deviation:.2f}%"

        # Минимальная пропускная способность
        min_throughput = min(measurements)
        assert (
            min_throughput > 30
        ), f"Throughput too low: {min_throughput:.2f} req/s"
