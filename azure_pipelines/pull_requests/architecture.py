#!/usr/bin/env python3
"""Module for creating Pull Request comments with architecture diagrams."""

from azure_pipelines.logging_config import get_logger
from azure_pipelines.pull_requests import pull_request_comment

# Get configured logger for this module
logger = get_logger(__name__)


def main():
    """Create a Pull Request comment with architecture diagram from CDK output."""
    diagram_path = "./cdk.out/cdkgraph/diagram.png"

    logger.info(f"Uploading architecture diagram from {diagram_path}")

    try:
        msg = pull_request_comment.Message()
        msg.upload_attachment_and_comment(file_path=diagram_path)
        logger.info("Successfully uploaded architecture diagram to PR comment")
    except Exception as exc:
        logger.exception("Failed to upload architecture diagram: %s", exc)
        raise


if __name__ == "__main__":
    main()
