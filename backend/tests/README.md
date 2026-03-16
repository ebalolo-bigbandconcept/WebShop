# WebShop Backend Tests

Comprehensive automated test suite for the WebShop quotation management system.

## Directory Structure

```
tests/
├── README.md                    # This file
├── __init__.py                  # Tests package init
├── conftest.py                  # Global pytest fixtures
├── fixtures/                    # Test configurations and data
├── unit/                        # Unit tests (models, utils, services)
├── integration/                 # Integration tests (API endpoints)
└── e2e/                         # End-to-end workflow tests
```

## Running Tests

### Run All Tests
```bash
# Inside Docker container
docker compose exec backend pytest
```

### Run Specific Test Suites
```bash
# Unit tests only
docker compose exec backend pytest tests/unit/

# Integration tests only
docker compose exec backend pytest tests/integration/

# Specific test file
docker compose exec backend pytest tests/unit/test_devis_calculations.py

# Specific test class
docker compose exec backend pytest tests/unit/test_devis_calculations.py::TestArticleLineCalculations

# Specific test function
docker compose exec backend pytest tests/unit/test_devis_calculations.py::TestArticleLineCalculations::test_montant_ht_calculation_basic
```

### Run with Coverage
```bash
# Generate coverage report
docker compose exec backend pytest --cov=. --cov-report=term

# View HTML report (opens in browser)
open backend/htmlcov/index.html
```

### Run with Verbose Output
```bash
# Show detailed test output
docker compose exec backend pytest -v

# Show print statements
docker compose exec backend pytest -s

# Show failed tests details
docker compose exec backend pytest -vv
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-flask documentation](https://pytest-flask.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
