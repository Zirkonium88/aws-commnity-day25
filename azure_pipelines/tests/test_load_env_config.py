"""
Tests for the load_env.config module.
"""

import json
from unittest.mock import mock_open, patch

import pytest

from azure_pipelines.load_env.config import CDKConfig


@pytest.fixture
def sample_config():
    """Sample configuration data for testing."""
    return {
        "AccountId": "947429061527",
        "AWSRegion": "eu-central-1",
        "QueueName": "my-sample-dev-queue",
    }


def test_init(sample_config):
    """Test CDKConfig initialization."""
    environment = "developer"
    config = CDKConfig(environment=environment)

    assert config._environment == environment
    assert isinstance(config.data, dict)
    assert config.load_config() == sample_config


def test_load_config(sample_config):
    """Test load_config method."""
    environment = "developer"
    config = CDKConfig(environment=environment)
    result = config.load_config()
    assert result == sample_config


def test_load_config_file_not_found():
    """Test load_config method when file is not found."""
    environment = "nonexistent"

    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            CDKConfig(environment=environment)


def test_load_config_invalid_json():
    """Test load_config method with invalid JSON."""
    environment = "invalid"

    with patch("builtins.open", mock_open(read_data="invalid json")):
        with pytest.raises(json.JSONDecodeError):
            CDKConfig(environment=environment)


def test_get_value(sample_config):
    """Test get_value method."""
    environment = "developer"

    config = CDKConfig(environment=environment)

    # Test existing key
    assert config.get_value("AccountId") == sample_config["AccountId"]

    # Test non-existing key with default
    assert config.get_value("NonExistentKey", "default") == "default"

    # Test non-existing key without default
    assert config.get_value("NonExistentKey") is None
