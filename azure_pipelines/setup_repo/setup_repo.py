#!/usr/bin/env python3
"""Module for creating and configuring Azure DevOps repositories and pipelines."""
import argparse
import base64
import os
import subprocess
import sys

import requests

from azure_pipelines.logging_config import get_logger

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# Get configured logger for this module
logger = get_logger(__name__)


class CreateAzureRepo:
    """Handles creation and configuration of Azure DevOps repositories."""

    def __init__(self, pa_token: str, new_repo_name: str) -> None:
        """Initialize the Azure repository creator.

        Args:
            pa_token: Azure DevOps personal access token
            new_repo_name: Name of the repository to be created
        """
        self.new_repo_name = new_repo_name
        self.azure_api_version = "7.0"
        self.parent_project_id = "<PROJECT_ID>"
        self.source_project_name = "<PROJECT_NAME>"
        self.organization = "<ORGANIZATION>"
        self.pipeline_stages = ["development", "pull-request", "release"]
        self.new_repository_id = None
        self.cicd_pull_request_id = None

        # Create authorization header
        auth_string = base64.b64encode(f":{pa_token}".encode("ascii")).decode("ascii")
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {auth_string}",
        }

    def create_pipelines(self) -> None:
        """Create three standard pipelines for this CDK project."""
        if not self.new_repository_id:
            logger.error("Repository ID not set. Create repository first.")
            return

        logger.info(f"Creating new Azure pipelines on repository: {self.new_repo_name}")
        post_url = f"https://dev.azure.com/{self.organization}/{self.parent_project_id}/_apis/pipelines?api-version={self.azure_api_version}"

        for stage in self.pipeline_stages:
            # Determine pipeline path based on stage
            path = (
                "/azure-pipelines.yml"
                if stage == "development"
                else f"/azure-pipelines-{stage}.yml"
            )

            body = {
                "name": f"{self.new_repo_name}-{stage}",
                "configuration": {
                    "path": path,
                    "repository": {
                        "id": self.new_repository_id,
                        "name": self.new_repo_name,
                        "type": "azureReposGit",
                    },
                    "type": "yaml",
                },
                "folder": f"\\{self.new_repo_name}",
            }

            response = requests.post(url=post_url, headers=self.headers, json=body)

            # Handle pull-request pipeline ID retrieval
            if stage == "pull-request":
                self._handle_pull_request_pipeline(response)

            logger.info(
                f"Pipeline creation status: {response.status_code} - {response.reason}"
            )
            if response.status_code == 200:
                logger.info("Pipeline creation succeeded")
            else:
                logger.error("Pipeline creation failed or pipeline already exists")

    def _handle_pull_request_pipeline(self, response: requests.Response) -> None:
        """Extract or find the pull request pipeline ID.

        Args:
            response: The response from creating the pull request pipeline
        """
        try:
            self.cicd_pull_request_id = response.json()["id"]
        except (KeyError, ValueError):
            logger.error(
                f"Pipeline {self.new_repo_name}-pull-request already exists. Searching for its ID..."
            )
            get_url = f"https://dev.azure.com/{self.organization}/{self.source_project_name}/_apis/pipelines?api-version={self.azure_api_version}"

            search_response = requests.get(url=get_url, headers=self.headers)
            if search_response.status_code != 200:
                logger.error(
                    f"Failed to retrieve pipelines: {search_response.status_code}"
                )
                return

            try:
                pipelines = search_response.json().get("value", [])
                for pipeline in pipelines:
                    name = pipeline.get("name", "")
                    if self.new_repo_name in name and "pull-request" in name:
                        self.cicd_pull_request_id = pipeline["id"]
                        logger.info(f"Found ID for {self.new_repo_name}-pull-request")
                        break
            except (KeyError, ValueError) as e:
                logger.error(f"Error parsing pipeline data: {e}")

    def create_azure_devops_repo(self) -> bool:
        """Create a new repository within this Azure DevOps project.

        Returns:
            bool: True if repository was created or found, False otherwise
        """
        logger.info(f"Creating new Azure repository: {self.new_repo_name}")

        body = {"name": self.new_repo_name, "project": {"id": self.parent_project_id}}
        url = f"https://dev.azure.com/{self.organization}/_apis/git/repositories?api-version={self.azure_api_version}"

        response = requests.post(url=url, headers=self.headers, json=body)

        if response.status_code == 201:
            logger.info("Repository created successfully")
            self.new_repository_id = response.json()["id"]
            return True
        elif response.status_code == 409:
            logger.info("Repository already exists, retrieving ID")
            return self._get_existing_repo_id()
        else:
            logger.error(
                f"Failed to create repository: {response.status_code} - {response.reason}"
            )
            return False

    def _get_existing_repo_id(self) -> bool:
        """Retrieve the ID of an existing repository.

        Returns:
            bool: True if repository ID was found, False otherwise
        """
        get_url = f"https://dev.azure.com/{self.organization}/{self.parent_project_id}/_apis/git/repositories/{self.new_repo_name}?api-version={self.azure_api_version}"
        response = requests.get(url=get_url, headers=self.headers)

        if response.status_code == 200:
            try:
                self.new_repository_id = response.json()["id"]
                return True
            except (KeyError, ValueError) as e:
                logger.error(f"Error parsing repository data: {e}")
                return False
        else:
            logger.error(
                f"Failed to retrieve repository: {response.status_code} - {response.reason}"
            )
            return False

    def git_migrate(self) -> bool:
        """Migrate sample repo into this new repository.

        Returns:
            bool: True if migration was successful, False otherwise
        """
        logger.info("Starting git migration")
        try:
            # Set the new remote URL
            subprocess.run(
                [
                    "git",
                    "remote",
                    "set-url",
                    "origin",
                    f"git@ssh.dev.azure.com:v3/{self.organization}/{self.source_project_name}/{self.new_repo_name}",
                ],
                check=True,
            )

            # Push all branches to the new remote
            subprocess.run(["git", "push", "-u", "origin", "--all"], check=True)
            logger.info("Git migration completed successfully")
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Git migration failed: {e}")
            return False

    def create_pull_request_policy(self) -> bool:
        """Create build validation policy for pull requests into master branch.

        Returns:
            bool: True if policy was created successfully, False otherwise
        """
        if not self.cicd_pull_request_id or not self.new_repository_id:
            logger.error("Missing required IDs for policy creation")
            return False

        logger.info("Setting build validation policy for pull requests")

        post_url = f"https://dev.azure.com/{self.organization}/{self.source_project_name}/_apis/policy/configurations?api-version={self.azure_api_version}"

        body = {
            "isEnabled": True,
            "isBlocking": True,
            "isDeleted": False,
            "isEnterpriseManaged": False,
            "type": {"id": "0609b952-1397-4640-95ec-e00a01b2c241"},
            "settings": {
                "buildDefinitionId": self.cicd_pull_request_id,
                "manualQueueOnly": False,
                "queueOnSourceUpdateOnly": True,
                "scope": [
                    {
                        "repositoryId": self.new_repository_id,
                        "refName": "refs/heads/master",
                        "matchKind": "exact",
                    }
                ],
                "validDuration": 720.0,
            },
        }

        response = requests.post(url=post_url, headers=self.headers, json=body)

        if response.status_code == 200:
            logger.info("Build validation policy created successfully")
            return True
        else:
            logger.error(
                f"Failed to create build validation policy: {response.status_code} - {response.reason}"
            )
            return False


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Create and configure Azure DevOps repositories and pipelines"
    )
    parser.add_argument(
        "-pat",
        "--azure-access-token",
        required=True,
        help="Your personal Azure Access Token (PAT)",
    )
    parser.add_argument(
        "-rn",
        "--repository-name",
        required=True,
        help="Your new repository within Azure DevOps Project 'CDK-Projects'",
    )

    return parser.parse_args()


def main() -> None:
    """Orchestrate the creation and configuration of an Azure DevOps repository."""
    args = parse_arguments()

    # Create and configure the repository
    repo = CreateAzureRepo(
        pa_token=args.azure_access_token,
        new_repo_name=args.repository_name,
    )

    # Execute the workflow
    if repo.create_azure_devops_repo():
        repo.create_pipelines()
        repo.git_migrate()
        repo.create_pull_request_policy()
    else:
        logger.error("Failed to create or find repository. Aborting.")


if __name__ == "__main__":
    main()
