import json
from typing import Any, Dict, Optional

from azure_pipelines.logging_config import get_logger

# Get configured logger for this module
logger = get_logger(__name__)


class CDKConfig:
    """Generate CDK config object for multi environment deployments."""

    def __init__(self, environment: str) -> None:
        """Initialize config object.

        Args:
            environment: Name of the environment. Must match the name of a JSON config file.
        """
        self._environment = environment
        self.data: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load the config from the environment-specific JSON file.

        Returns:
            The loaded configuration as a dictionary.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            json.JSONDecodeError: If the config file contains invalid JSON.
        """
        try:
            with open(f"config/{self._environment}.json") as json_file:
                self.data = json.load(json_file)
            return self.data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load config file: {e}")
            raise

    def get_value(self, key: str, default: Any = None) -> Optional[Any]:
        """Get value from config object.

        Args:
            key: Name of the key to retrieve.
            default: Value to return if key is not found (defaults to None).

        Returns:
            The value associated with the key or the default value if not found.
        """
        try:
            return self.data[key]
        except KeyError:
            logger.error(
                f"Key '{key}' not found in configuration for environment '{self._environment}'"
            )
            logger.debug(f"Available keys: {list(self.data.keys())}")
            return default
