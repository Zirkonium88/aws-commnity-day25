"""
Tests for the setup_repo.setup_repo module.
"""

import argparse
import base64
from unittest.mock import MagicMock, patch

import pytest
import requests_mock

from azure_pipelines.setup_repo.setup_repo import CreateAzureRepo, main, parse_arguments


@pytest.fixture
def repo_config():
    """Basic repository configuration for testing."""
    return {
        "new_repo_name": "demo",
        "pa_token": "token",
        "azure_api_version": "7.0",
        "parent_project_id": "26546064-040a-41ae-949a-c8f35fa94a9b",
        "source_project_name": "cdk-projects",
        "organization": "mrh-trowe",
    }


@pytest.fixture
def repo_instance(repo_config):
    """Create a CreateAzureRepo instance for testing."""
    return CreateAzureRepo(
        pa_token=repo_config["pa_token"],
        new_repo_name=repo_config["new_repo_name"],
    )


@pytest.fixture
def auth_headers(repo_config):
    """Generate authorization headers for testing."""
    auth_string = base64.b64encode(
        f":{repo_config['pa_token']}".encode("ascii")
    ).decode("ascii")
    return {
        "Accept": "application/json",
        "Authorization": f"Basic {auth_string}",
    }


def test_init(repo_instance, auth_headers, repo_config):
    """Test CreateAzureRepo initialization."""
    assert repo_instance.new_repo_name == repo_config["new_repo_name"]
    assert repo_instance.azure_api_version == repo_config["azure_api_version"]
    assert repo_instance.parent_project_id == repo_config["parent_project_id"]
    assert repo_instance.source_project_name == repo_config["source_project_name"]
    assert repo_instance.organization == repo_config["organization"]
    assert repo_instance.headers == auth_headers
    assert repo_instance.pipeline_stages == ["development", "pull-request", "release"]
    assert repo_instance.new_repository_id is None
    assert repo_instance.cicd_pull_request_id is None


def test_create_pipelines(repo_instance, repo_config):
    """Test create_pipelines method."""
    repo_instance.new_repository_id = "123"
    pipeline_url = f"https://dev.azure.com/{repo_config['organization']}/{repo_config['parent_project_id']}/_apis/pipelines?api-version={repo_config['azure_api_version']}"

    with requests_mock.Mocker() as mock:
        # Mock responses for all three pipeline creations
        mock.post(pipeline_url, json={"id": "1"}, status_code=200)

        repo_instance.create_pipelines()

        # Should have 3 calls for the 3 pipeline stages
        assert mock.call_count == 3

        # Check that the pull-request pipeline ID was set
        assert repo_instance.cicd_pull_request_id == "1"


def test_create_pipelines_no_repo_id(repo_instance):
    """Test create_pipelines method without repository ID."""
    repo_instance.new_repository_id = None

    with requests_mock.Mocker() as mock:
        repo_instance.create_pipelines()

        # Should not make any API calls
        assert mock.call_count == 0


def test_handle_pull_request_pipeline_success(repo_instance):
    """Test _handle_pull_request_pipeline with successful response."""
    response = MagicMock()
    response.json.return_value = {"id": "123"}

    repo_instance._handle_pull_request_pipeline(response)

    assert repo_instance.cicd_pull_request_id == "123"


def test_handle_pull_request_pipeline_error_with_search(repo_instance, repo_config):
    """Test _handle_pull_request_pipeline with error and successful search."""
    response = MagicMock()
    response.json.side_effect = KeyError("No id")

    search_url = f"https://dev.azure.com/{repo_config['organization']}/{repo_config['source_project_name']}/_apis/pipelines?api-version={repo_config['azure_api_version']}"

    with requests_mock.Mocker() as mock:
        mock.get(
            search_url,
            json={
                "value": [
                    {"name": "other-pull-request", "id": "456"},
                    {
                        "name": f"{repo_config['new_repo_name']}-pull-request",
                        "id": "789",
                    },
                ]
            },
            status_code=200,
        )

        repo_instance._handle_pull_request_pipeline(response)

        assert repo_instance.cicd_pull_request_id == "789"


def test_create_azure_devops_repo_success(repo_instance, repo_config):
    """Test create_azure_devops_repo with successful creation."""
    url = f"https://dev.azure.com/{repo_config['organization']}/_apis/git/repositories?api-version={repo_config['azure_api_version']}"

    with requests_mock.Mocker() as mock:
        mock.post(url, json={"id": "123"}, status_code=201)

        result = repo_instance.create_azure_devops_repo()

        assert result is True
        assert repo_instance.new_repository_id == "123"


def test_create_azure_devops_repo_already_exists(repo_instance, repo_config):
    """Test create_azure_devops_repo when repository already exists."""
    create_url = f"https://dev.azure.com/{repo_config['organization']}/_apis/git/repositories?api-version={repo_config['azure_api_version']}"
    get_url = f"https://dev.azure.com/{repo_config['organization']}/{repo_config['parent_project_id']}/_apis/git/repositories/{repo_config['new_repo_name']}?api-version={repo_config['azure_api_version']}"

    with requests_mock.Mocker() as mock:
        mock.post(create_url, status_code=409)
        mock.get(get_url, json={"id": "123"}, status_code=200)

        result = repo_instance.create_azure_devops_repo()

        assert result is True
        assert repo_instance.new_repository_id == "123"


def test_git_migrate_success(repo_instance):
    """Test git_migrate with successful execution."""
    with patch("subprocess.run") as mock_run:
        result = repo_instance.git_migrate()

        assert result is True
        assert mock_run.call_count == 2


def test_create_pull_request_policy_success(repo_instance, repo_config):
    """Test create_pull_request_policy with successful execution."""
    repo_instance.cicd_pull_request_id = "123"
    repo_instance.new_repository_id = "456"

    url = f"https://dev.azure.com/{repo_config['organization']}/{repo_config['source_project_name']}/_apis/policy/configurations?api-version={repo_config['azure_api_version']}"

    with requests_mock.Mocker() as mock:
        mock.post(url, json={}, status_code=200)

        result = repo_instance.create_pull_request_policy()

        assert result is True


def test_create_pull_request_policy_missing_ids(repo_instance):
    """Test create_pull_request_policy with missing IDs."""
    repo_instance.cicd_pull_request_id = None
    repo_instance.new_repository_id = "456"

    result = repo_instance.create_pull_request_policy()

    assert result is False


def test_parse_arguments():
    """Test parse_arguments function."""
    test_args = ["--azure-access-token", "test-token", "--repository-name", "test-repo"]

    with patch("sys.argv", ["setup_repo.py"] + test_args):
        args = parse_arguments()

        assert args.azure_access_token == "test-token"
        assert args.repository_name == "test-repo"


def test_main_success():
    """Test main function with successful execution."""
    with patch("argparse.ArgumentParser.parse_args") as mock_args, patch(
        "azure_pipelines.setup_repo.setup_repo.CreateAzureRepo"
    ) as mock_repo:

        # Configure mock arguments
        mock_args.return_value = argparse.Namespace(
            azure_access_token="test-token", repository_name="test-repo"
        )

        # Configure mock repository
        repo_instance = MagicMock()
        repo_instance.create_azure_devops_repo.return_value = True
        mock_repo.return_value = repo_instance

        main()

        # Verify all methods were called
        repo_instance.create_azure_devops_repo.assert_called_once()
        repo_instance.create_pipelines.assert_called_once()
        repo_instance.git_migrate.assert_called_once()
        repo_instance.create_pull_request_policy.assert_called_once()


def test_main_repo_creation_failure():
    """Test main function with repository creation failure."""
    with patch("argparse.ArgumentParser.parse_args") as mock_args, patch(
        "azure_pipelines.setup_repo.setup_repo.CreateAzureRepo"
    ) as mock_repo:

        # Configure mock arguments
        mock_args.return_value = argparse.Namespace(
            azure_access_token="test-token", repository_name="test-repo"
        )

        # Configure mock repository
        repo_instance = MagicMock()
        repo_instance.create_azure_devops_repo.return_value = False
        mock_repo.return_value = repo_instance

        main()

        # Verify only create_azure_devops_repo was called
        repo_instance.create_azure_devops_repo.assert_called_once()
        repo_instance.create_pipelines.assert_not_called()
        repo_instance.git_migrate.assert_not_called()
        repo_instance.create_pull_request_policy.assert_not_called()
