.PHONY: run start rebuild test update format lint

run:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

start:
	docker-compose up app

rebuild:
	docker-compose up --build app

test:
	poetry run pytest tests/ -v

update:
	poetry lock
	poetry install --no-root
	poetry run alembic upgrade head
	poetry run alembic revision --autogenerate -m "Auto-generated migration"

format:
	poetry run black app/ tests/
	poetry run isort app/ tests/

lint:
	poetry run ruff check app/ tests/
	poetry run black --check app/ tests/
	poetry run isort --check-only app/ tests/
	poetry run pre-commit run --all-files

