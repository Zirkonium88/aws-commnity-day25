# Azure Pipelines Package

This package provides utilities for automating CDK project workflows in Azure Pipelines.

## Logging Configuration

The package includes a centralized logging configuration system that provides consistent logging across all modules.

### Usage

```python
from azure_pipelines.logging_config import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Use the logger
logger.info("This is an info message")
logger.error("This is an error message")
```

### Configuration Options

You can customize the logging behavior by setting environment variables:

- `AZURE_PIPELINES_LOG_LEVEL`: Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Advanced Usage

For more advanced configuration, you can use the `configure_logging` function directly:

```python
from azure_pipelines.logging_config import configure_logging

logger = configure_logging(
    logger_name="my_custom_logger",
    log_level=logging.DEBUG,
    log_file="custom.log",
    console_output=True,
    file_output=True
)
```

## Modules

- `pull_requests`: Utilities for working with Azure DevOps pull requests
- `load_env`: Utilities for loading environment configurations
- `setup_repo`: Utilities for setting up Azure DevOps repositories