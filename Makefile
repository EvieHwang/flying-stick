.PHONY: install install-backend install-frontend lint lint-backend test build deploy dev clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install          - Install all dependencies (backend + frontend)"
	@echo "  make install-backend  - Install Python dependencies"
	@echo "  make install-frontend - Install npm dependencies"
	@echo "  make lint             - Run all linters"
	@echo "  make lint-backend     - Run Python linter (ruff)"
	@echo "  make test             - Run all tests"
	@echo "  make build            - Build SAM and frontend"
	@echo "  make deploy           - Deploy to AWS"
	@echo "  make dev              - Start frontend dev server"
	@echo "  make clean            - Remove build artifacts"

# Installation
install: install-backend install-frontend

install-backend:
	pip install -r backend/requirements.txt
	pip install ruff pytest pytest-cov

install-frontend:
	cd frontend && npm install

# Linting
lint: lint-backend
	@echo "All linting complete"

lint-backend:
	ruff check backend/src/ --config pyproject.toml

# Testing
test:
	cd backend && pytest tests/ -v --cov=src --cov-report=term-missing

# Building
build:
	sam build
	@if [ -d "frontend" ]; then cd frontend && npm run build; fi

# Deployment
deploy: build
	sam deploy --no-confirm-changeset --no-fail-on-empty-changeset

# Development
dev:
	cd frontend && npm run dev

# Local SAM testing
local:
	sam local start-api

# Cleanup
clean:
	rm -rf .aws-sam/
	rm -rf backend/__pycache__/
	rm -rf backend/src/__pycache__/
	rm -rf backend/src/utils/__pycache__/
	rm -rf backend/tests/__pycache__/
	rm -rf backend/.pytest_cache/
	rm -rf frontend/dist/
	rm -rf frontend/node_modules/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
