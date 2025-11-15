.PHONY: run start rebuild test update format lint docker-build docker-test docker-scan docker-lint docker-clean

run:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

start:
	docker compose up app

rebuild:
	docker compose up --build app

test:
	poetry run pytest tests/ -v

update:
	poetry lock
	poetry install --no-root
	poetry run alembic upgrade head
	poetry run alembic revision --autogenerate -m "Auto-generated migration"

format:
	poetry run black .
	poetry run isort .
	poetry run pre-commit run --all-files

lint:
	poetry run ruff check .
	poetry run black --check .
	poetry run isort --check-only .

docker-build:
	docker build -t wishlist-app:latest .
	@echo "Image built successfully"
	@docker images wishlist-app:latest

docker-test:
	@echo "Testing container security..."
	@bash scripts/test_container.sh

docker-scan:
	@echo "Scanning with Trivy..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy:latest image wishlist-app:latest

docker-lint:
	@echo "Linting Dockerfile with hadolint..."
	@docker run --rm -i hadolint/hadolint < Dockerfile

docker-clean:
	docker-compose down -v
	docker rmi wishlist-app:latest || true
