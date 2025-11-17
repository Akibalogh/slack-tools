.PHONY: test test-unit test-integration test-performance test-coverage test-quick lint format clean install

# Default target
all: test

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r tests/requirements-test.txt

# Run all tests
test:
	cd tests && python3 -m pytest unit/ integration/ performance/ -v

# Run unit tests only
test-unit:
	cd tests && python3 -m pytest unit/ -v

# Run integration tests only
test-integration:
	cd tests && python3 -m pytest integration/ -v

# Run performance tests only
test-performance:
	cd tests && python3 -m pytest performance/ -v

# Run tests with coverage
test-coverage:
	cd tests && python3 -m pytest unit/ integration/ performance/ --cov=../src --cov-report=term-missing --cov-report=html

# Run quick tests (unit only, no coverage)
test-quick:
	cd tests && python3 -m pytest unit/ -v --tb=short

# Lint code
lint:
	flake8 src/ tests/ scripts/ --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check src/ tests/ scripts/
	isort --check-only src/ tests/ scripts/

# Format code
format:
	black src/ tests/ scripts/
	isort src/ tests/ scripts/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf tests/htmlcov
	rm -rf tests/.coverage
	rm -rf tests/coverage.xml

# Create necessary directories
setup-dirs:
	mkdir -p logs
	mkdir -p output/notebooklm
	mkdir -p output/analysis
	mkdir -p data/slack
	mkdir -p data/telegram

# Run ETL in quick mode for testing
test-etl-quick:
	python3 main.py etl --quick

# Run ETL in full mode
test-etl-full:
	python3 main.py etl

# Validate ETL output
validate-output:
	python3 scripts/validate_etl_output_simple.py

# Help
help:
	@echo "Available targets:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-performance - Run performance tests only"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  test-quick     - Run quick unit tests"
	@echo "  lint           - Lint code with flake8, black, isort"
	@echo "  format         - Format code with black and isort"
	@echo "  clean          - Clean up cache files"
	@echo "  setup-dirs     - Create necessary directories"
	@echo "  test-etl-quick - Run ETL in quick mode"
	@echo "  test-etl-full  - Run ETL in full mode"
	@echo "  validate-output - Validate ETL output"
	@echo "  install        - Install dependencies"
	@echo "  help           - Show this help"
