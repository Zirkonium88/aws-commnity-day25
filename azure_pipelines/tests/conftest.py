"""Pytest configuration for azure_pipelines tests.

This module contains shared fixtures and configuration for all tests.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_env():
    """Fixture to create a context manager for mocking environment variables."""

    def _mock_env(**kwargs):
        return patch.dict(os.environ, kwargs)

    return _mock_env


@pytest.fixture
def azure_devops_env():
    """Fixture with common Azure DevOps environment variables."""
    return {
        "SYSTEM_COLLECTIONURI": "https://dev.azure.com/",
        "SYSTEM_PULLREQUEST_PULLREQUESTID": "22",
        "SYSTEM_TEAMPROJECT": "fabrikam",
        "BUILD_REPOSITORY_ID": "3411ebc1-d5aa-464f-9615-0b527bc66719",
        "SYSTEM_ACCESSTOKEN": "SYSTEM_ACCESSTOKEN",
        "BUILD_SOURCEVERSION": "ahkjs213687213",
    }


@pytest.fixture
def mock_pull_request_comment(mocker):
    """Fixture to mock the pull_request_comment.Message class."""
    mock_msg = MagicMock()
    mocker.patch(
        "azure_pipelines.pull_requests.pull_request_comment.Message",
        return_value=mock_msg,
    )
    return mock_msg


@pytest.fixture
def sample_dataframe():
    """Fixture to create a sample pandas DataFrame for testing."""
    import pandas as pd

    return pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})


@pytest.fixture
def mock_file_content():
    """Fixture to provide sample file content for testing."""
    return "Some CDK diff output"
