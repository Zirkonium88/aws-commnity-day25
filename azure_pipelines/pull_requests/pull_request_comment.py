"""Module for interacting with Azure DevOps Pull Request comments and attachments."""

import os
from pathlib import Path
from typing import Union

import requests

from azure_pipelines.logging_config import get_logger

# Get configured logger for this module
logger = get_logger(__name__)

# API version constant
API_VERSION = "7.1"


class Message:
    """Handles Azure DevOps Pull Request comments and attachments."""

    def __init__(self):
        """Initialize with environment variables for Azure DevOps connection."""
        # Get environment variables
        self.token = os.getenv("SYSTEM_ACCESSTOKEN")
        self.collection_uri = os.getenv("SYSTEM_COLLECTIONURI")
        self.pull_request_id = os.getenv("SYSTEM_PULLREQUEST_PULLREQUESTID")
        self.team_project = os.getenv("SYSTEM_TEAMPROJECT")
        self.repository_id = os.getenv("BUILD_REPOSITORY_ID")

        # Get first 5 characters of commit SHA for attachment naming
        source_version = os.getenv("BUILD_SOURCEVERSION", "")
        self.commit_sha_prefix = source_version[:5] if source_version else ""

        # Construct base URL for API calls
        self.base_url = (
            f"{self.collection_uri}{self.team_project}/_apis/git/repositories/"
            f"{self.repository_id}/pullRequests/{self.pull_request_id}"
        )

    def add_msg(self, comment: str) -> bool:
        """Add a comment to Azure DevOps Pull Request.

        Args:
            comment: The comment text to add

        Returns:
            bool: True if comment was added successfully, False otherwise
        """
        data = {
            "comments": [{"parentCommentId": 1, "content": comment, "commentType": 1}],
            "status": 1,
        }

        msg_url = f"{self.base_url}/threads?api-version={API_VERSION}"
        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        logger.info(f"Sending PR comment to: {msg_url}")
        response = requests.post(url=msg_url, json=data, headers=headers)

        logger.info(
            f"Response Code: {response.status_code}, Response Reason: {response.reason}"
        )
        return response.status_code == 200

    def upload_attachment_and_comment(self, file_path: Union[str, Path]) -> bool:
        """Upload an attachment and add a comment with the attachment link.

        Args:
            file_path: Path to the file to upload

        Returns:
            bool: True if upload and comment were successful, False otherwise
        """
        # Convert to Path object for better path handling
        path = Path(file_path)

        if not path.is_file():
            logger.error(f"File does not exist: {path}")
            return False

        file_name = f"diagram-{self.commit_sha_prefix}.png"
        attachment_url = (
            f"{self.base_url}/attachments/{file_name}?api-version={API_VERSION}"
        )

        headers = {
            "Content-Type": "application/octet-stream",
            "Authorization": f"Bearer {self.token}",
        }

        logger.info(f"Uploading attachment: {file_name} to {attachment_url}")

        with path.open("rb") as file:
            response = requests.post(url=attachment_url, headers=headers, data=file)

        logger.info(
            f"Response Code: {response.status_code}, Response Reason: {response.reason}"
        )

        if response.status_code == 201:
            logger.info("File uploaded successfully")
            attachment_ref = response.json().get("url")

            # Add comments with the attachment
            self.add_msg(f"[Architecture Diagram]({attachment_ref})")
            self.add_msg(f"""<img src="{attachment_ref}" alt="Architecture Diagram">""")
            return True
        else:
            logger.error(f"Failed to upload file. Response: {response.text}")
            return False


if __name__ == "__main__":
    # Example usage
    message = Message()
    # message.add_msg("Example comment")
    # message.upload_attachment_and_comment("path/to/diagram.png")
