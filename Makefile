# Conductor - Agentic Documentation System
# Development and deployment automation

.PHONY: help install install-dev test lint format type-check security clean build docker docs

# Default target
help: ## Show this help message
	@echo "Conductor - Agentic Documentation System"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

setup: ## Complete development setup
	python3 -m venv venv
	. venv/bin/activate && $(MAKE) install-dev
	cp .env.example .env
	@echo "✅ Setup complete! Edit .env with your API keys, then activate venv:"
	@echo "source venv/bin/activate"

# Code quality
format: ## Format code with black and isort
	black src/ tests/ examples/ conductor.py setup.py
	isort src/ tests/ examples/ conductor.py setup.py

lint: ## Run linting checks
	flake8 src/ tests/ examples/ conductor.py setup.py
	black --check src/ tests/ examples/ conductor.py setup.py
	isort --check-only src/ tests/ examples/ conductor.py setup.py

type-check: ## Run type checking
	mypy src/ --ignore-missing-imports

security: ## Run security checks
	bandit -r src/ -f json -o reports/bandit-report.json
	safety check --json --output reports/safety-report.json

pre-commit: ## Run all pre-commit hooks
	pre-commit run --all-files

# Testing
test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v --tb=short

test-coverage: ## Run tests with coverage report
	pytest tests/ --cov=src --cov-report=html --cov-report=xml --cov-report=term

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -- -v

# Documentation
docs: ## Generate documentation
	./conductor.py template --type base --template technical_procedure --output docs/sample_procedure.md
	./conductor.py template --type splunk --template alert_configuration --output docs/sample_alert.md

docs-clean: ## Clean documentation build files
	rm -rf docs/_build/ docs/build/

# Building and packaging
build: ## Build package for distribution
	python -m build

clean: ## Clean up build artifacts and cache files
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
	rm -rf __pycache__/ */__pycache__/ */*/__pycache__/
	rm -rf .mypy_cache/
	rm -rf output/ logs/ workflow_templates/*.json
	rm -rf reports/
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Docker operations
docker-build: ## Build Docker image
	docker build -t conductor:latest .

docker-dev: ## Start development environment with Docker
	docker-compose --profile development up -d

docker-test: ## Run tests in Docker
	docker-compose run --rm conductor-dev pytest tests/ -v

docker-clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

# Application commands
run: ## Run Conductor interactively
	./conductor.py generate --interactive

config: ## Show current configuration
	./conductor.py config

example: ## Run example workflow
	python examples/splunk_example.py --simple

# Development utilities
check: format lint type-check security test ## Run all checks

dev-install: install-dev ## Alias for install-dev

init-reports: ## Create reports directory
	mkdir -p reports

# CI/CD helpers
ci-install: ## Install dependencies for CI
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

ci-test: ## Run tests for CI
	pytest tests/ --cov=src --cov-report=xml --cov-report=term -v

ci-lint: ## Run linting for CI
	black --check src/ tests/ examples/ conductor.py setup.py
	isort --check-only src/ tests/ examples/ conductor.py setup.py
	flake8 src/ tests/ examples/ conductor.py setup.py

ci-security: init-reports security ## Run security checks for CI

# Release helpers
version: ## Show current version
	python setup.py --version

tag: ## Create git tag for current version
	git tag -a v$(shell python setup.py --version) -m "Release v$(shell python setup.py --version)"
	git push origin v$(shell python setup.py --version)

release-test: ## Test release build
	python -m build
	python -m twine check dist/*

# Database and data operations (if needed in future)
migrate: ## Run database migrations (placeholder)
	@echo "No migrations needed yet"

seed: ## Seed database with sample data (placeholder)
	@echo "No seeding needed yet"

# Monitoring and debugging
logs: ## Show application logs
	tail -f logs/*.log 2>/dev/null || echo "No log files found"

debug: ## Run in debug mode
	PYTHONPATH=src python -m pdb conductor.py generate --interactive

profile: ## Run with profiling
	python -m cProfile -o profile.stats conductor.py generate --help

# Utilities
requirements-update: ## Update requirements files
	pip-compile --upgrade requirements.in
	pip-compile --upgrade requirements-dev.in

license-check: ## Check license compliance
	pip-licenses --format=markdown --output-file=reports/licenses.md

size-check: ## Check package size
	du -sh . && echo "Source code size:"
	find src/ -name "*.py" | xargs wc -l | tail -1

# Environment management
env-create: ## Create .env from example
	cp .env.example .env
	@echo "Created .env file - please edit with your API keys"

env-validate: ## Validate environment configuration
	python -c "from config.settings import get_settings; print('✅ Configuration valid')" || echo "❌ Configuration invalid"

# IDE setup helpers
vscode-setup: ## Setup VS Code configuration
	mkdir -p .vscode
	@echo "VS Code settings created - see docs/IDE_INTEGRATION.md"

# Performance testing
perf-test: ## Run performance tests
	pytest tests/performance/ -v --benchmark-only

load-test: ## Run load tests
	python tests/load_test.py

# Cleanup operations
clean-output: ## Clean output files
	rm -rf output/*

clean-logs: ## Clean log files
	rm -rf logs/*

clean-cache: ## Clean Python cache
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

reset: clean env-create ## Reset to clean state
	@echo "🔄 Repository reset to clean state"
	@echo "Edit .env with your configuration"
