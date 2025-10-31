"""
Tests for the pull_requests.pull_request_comment module.
"""

import os
from unittest.mock import mock_open, patch

import pytest
import requests_mock

from azure_pipelines.pull_requests.pull_request_comment import Message


@pytest.fixture
def message_instance(azure_devops_env):
    """Create a Message instance with mocked environment variables."""
    with patch.dict(os.environ, azure_devops_env):
        return Message()


@pytest.fixture
def api_url(azure_devops_env):
    """Construct the API URL for testing."""
    env = azure_devops_env
    return (
        f"{env['SYSTEM_COLLECTIONURI']}{env['SYSTEM_TEAMPROJECT']}/_apis/git/repositories/"
        f"{env['BUILD_REPOSITORY_ID']}/pullRequests/{env['SYSTEM_PULLREQUEST_PULLREQUESTID']}"
    )


@pytest.fixture
def post_response():
    """Sample response for POST requests."""
    return {
        "id": 2,
        "parentCommentId": 1,
        "author": {
            "id": "d6245f20-2af8-44f4-9451-8107cb2767db",
            "displayName": "Normal Paulk",
            "uniqueName": "fabrikamfiber16@hotmail.com",
            "url": "https://dev.azure.com/fabrikam/_apis/Identities/d6245f20-2af8-44f4-9451-8107cb2767db",
            "imageUrl": "https://dev.azure.com/fabrikam/_api/_common/identityImage?id=d6245f20-2af8-44f4-9451-8107cb2767db",
        },
        "content": "Good idea",
        "publishedDate": "2016-11-01T16:30:51.383Z",
        "lastUpdatedDate": "2016-11-01T16:30:51.383Z",
        "commentType": "text",
    }


def test_init(message_instance, api_url, azure_devops_env):
    """Test Message initialization."""
    assert message_instance.token == azure_devops_env["SYSTEM_ACCESSTOKEN"]
    assert (
        message_instance.pull_request_id
        == azure_devops_env["SYSTEM_PULLREQUEST_PULLREQUESTID"]
    )
    assert message_instance.base_url == api_url
    assert (
        message_instance.commit_sha_prefix
        == azure_devops_env["BUILD_SOURCEVERSION"][:5]
    )


def test_add_msg_success(message_instance, api_url, post_response):
    """Test add_msg method with successful response."""
    comment = "Test comment"

    with requests_mock.Mocker() as mock:
        msg_url = f"{api_url}/threads?api-version=7.1"
        mock.post(msg_url, json=post_response, status_code=200)

        result = message_instance.add_msg(comment=comment)

        assert result is True
        assert mock.last_request.json()["comments"][0]["content"] == comment


def test_add_msg_failure(message_instance, api_url):
    """Test add_msg method with failed response."""
    comment = "Test comment"

    with requests_mock.Mocker() as mock:
        msg_url = f"{api_url}/threads?api-version=7.1"
        mock.post(msg_url, status_code=400)

        result = message_instance.add_msg(comment=comment)

        assert result is False


def test_upload_attachment_and_comment_file_not_exists(message_instance):
    """Test upload_attachment_and_comment with non-existent file."""
    with patch("pathlib.Path.is_file", return_value=False):
        result = message_instance.upload_attachment_and_comment("nonexistent.png")
        assert result is False


def test_upload_attachment_and_comment_success(
    message_instance, api_url, post_response
):
    """Test upload_attachment_and_comment with successful upload."""
    file_path = "diagram.png"
    file_name = f"diagram-{message_instance.commit_sha_prefix}.png"
    attachment_url = f"{api_url}/attachments/{file_name}?api-version=7.1"

    # Mock file operations
    with patch("pathlib.Path.is_file", return_value=True), patch(
        "pathlib.Path.open", mock_open(read_data=b"image data")
    ), requests_mock.Mocker() as mock:

        # Mock attachment upload
        mock.post(
            attachment_url, json={"url": "https://attachment-url"}, status_code=201
        )

        # Mock comment additions
        threads_url = f"{api_url}/threads?api-version=7.1"
        mock.post(threads_url, json=post_response, status_code=200)

        result = message_instance.upload_attachment_and_comment(file_path)

        assert result is True
        assert mock.call_count == 3  # 1 upload + 2 comments


def test_upload_attachment_and_comment_upload_failure(message_instance, api_url):
    """Test upload_attachment_and_comment with failed upload."""
    file_path = "diagram.png"
    file_name = f"diagram-{message_instance.commit_sha_prefix}.png"
    attachment_url = f"{api_url}/attachments/{file_name}?api-version=7.1"

    # Mock file operations
    with patch("pathlib.Path.is_file", return_value=True), patch(
        "pathlib.Path.open", mock_open(read_data=b"image data")
    ), requests_mock.Mocker() as mock:

        # Mock attachment upload failure
        mock.post(attachment_url, status_code=400)

        result = message_instance.upload_attachment_and_comment(file_path)

        assert result is False
