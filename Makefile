.PHONY: help install dev fmt lint typecheck test test-unit test-integration test-determinism qualification compose-up compose-down compose-logs migrate frontend-dev frontend-build clean

help:
	@echo "JS-RE-Bench developer Makefile"
	@echo ""
	@echo "  install            install Python deps (editable + dev extras)"
	@echo "  dev                start API + Redis + DB locally via compose"
	@echo "  fmt                format code (ruff format + black)"
	@echo "  lint               lint code (ruff check + black --check)"
	@echo "  typecheck          run mypy on benchmark + apps"
	@echo "  test               run all Python tests"
	@echo "  test-unit          run unit tests only"
	@echo "  test-integration   run integration tests"
	@echo "  test-determinism   run Q2 determinism tests"
	@echo "  qualification      run all enabled qualification challenges"
	@echo "  compose-up         start docker-compose stack (Q1)"
	@echo "  compose-down       stop docker-compose stack"
	@echo "  compose-logs       tail compose logs"
	@echo "  migrate            apply alembic migrations"
	@echo "  frontend-dev       start the frontend dev server"
	@echo "  frontend-build     build the frontend production bundle"
	@echo "  clean              remove caches & build artifacts"

install:
	pip install -e .[dev,sandbox]
	pnpm install --frozen-lockfile
	cd frontend && pnpm install --frozen-lockfile

fmt:
	ruff format .
	black .

lint:
	ruff check .
	black --check .

typecheck:
	mypy benchmark apps --ignore-missing-imports

test:
	pytest -v

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

test-determinism:
	pytest tests/determinism -v

qualification:
	pytest tests/determinism tests/unit/test_d1_challenge.py -v

compose-up:
	docker compose -f infra/compose/docker-compose.yml up --build -d

compose-down:
	docker compose -f infra/compose/docker-compose.yml down -v

compose-logs:
	docker compose -f infra/compose/docker-compose.yml logs -f

migrate:
	alembic upgrade head

frontend-dev:
	cd frontend && pnpm dev

frontend-build:
	cd frontend && pnpm build

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf frontend/dist frontend/.vite frontend/node_modules
