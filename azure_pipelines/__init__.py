"""Azure Pipelines package for CDK project automation.

This package contains modules for automating CDK project workflows in Azure Pipelines.
"""

from azure_pipelines.logging_config import configure_logging, get_logger

__all__ = ["get_logger", "configure_logging"]
