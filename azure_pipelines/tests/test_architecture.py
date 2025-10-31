"""
Tests for the pull_requests.architecture module.
"""

from unittest.mock import MagicMock, patch

import pytest

from azure_pipelines.pull_requests import architecture


@pytest.fixture
def mock_message():
    """Mock Message instance."""
    message = MagicMock()
    message.upload_attachment_and_comment.return_value = True
    return message


def test_main_success(mock_message):
    """Test main function with successful execution."""
    with patch(
        "azure_pipelines.pull_requests.pull_request_comment.Message",
        return_value=mock_message,
    ):
        architecture.main()

        mock_message.upload_attachment_and_comment.assert_called_once_with(
            file_path="./cdk.out/cdkgraph/diagram.png"
        )


def test_main_exception(mock_message):
    """Test main function with exception."""
    mock_message.upload_attachment_and_comment.side_effect = Exception("Upload failed")

    with patch(
        "azure_pipelines.pull_requests.pull_request_comment.Message",
        return_value=mock_message,
    ), pytest.raises(Exception, match="Upload failed"):
        architecture.main()
