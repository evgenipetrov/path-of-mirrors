# Path of Mirrors - Backend API

FastAPI backend for Path of Exile economic intelligence platform.

## Quick Start

```bash
# Install dependencies
uv sync

# Copy environment variables
cp .env.example src/.env

# Run development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing

### Run All Tests

```bash
# Run all tests
./scripts/test.sh

# Run tests with coverage report
./scripts/test.sh --cov=src --cov-report=term-missing

# Run tests with HTML coverage report
./scripts/test.sh --cov=src --cov-report=html
# Open htmlcov/index.html to view detailed coverage
```

### Run Specific Tests

```bash
# Run tests for a specific module
./scripts/test.sh tests/contexts/placeholder/test_notes_api.py

# Run tests matching a pattern
./scripts/test.sh -k "test_create"

# Run tests with verbose output
./scripts/test.sh -v
```

### Coverage Status

Current test coverage: **76.39%** (exceeds 70% target)

- Domain models: 100%
- Schemas: 100%
- API routes: 73%
- Services: 62%
- Repository: 68%

## Documentation

See the [main project documentation](../docs/) for architecture, contributing guidelines, and roadmap.
