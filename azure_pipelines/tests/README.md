# Azure Pipelines Tests

This directory contains tests for the Azure Pipelines package.

## Running Tests

To run the tests, use the following command from the project root:

```bash
# Run all tests in the project
pytest

# Run only azure_pipelines tests
pytest azure_pipelines/tests
```

To run tests with coverage:

```bash
pytest --cov=azure_pipelines --cov-report=term-missing azure_pipelines/tests
```

## Test Structure

The tests are organized by module:

- `test_logging_config.py`: Tests for the logging configuration module
- `test_load_env_config.py`: Tests for the environment configuration module
- `test_pull_request_comment.py`: Tests for the pull request comment module
- `test_pull_request_comment_utils.py`: Tests for the pull request comment utilities
- `test_architecture.py`: Tests for the architecture module
- `test_setup_repo.py`: Tests for the repository setup module

## Test Fixtures

Common test fixtures are defined in `conftest.py` and can be used across all test modules.

## Best Practices

1. Use pytest fixtures for common setup and teardown
2. Mock external dependencies (files, APIs, etc.)
3. Test both success and failure paths
4. Keep tests isolated and independent
5. Use descriptive test names that explain what is being tested