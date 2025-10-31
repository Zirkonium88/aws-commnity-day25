"""Module for creating Pull Request comments with CDK diff and validation reports."""

from pathlib import Path
from typing import Optional

import pandas as pd

from azure_pipelines.logging_config import get_logger
from azure_pipelines.pull_requests import pull_request_comment

# Get configured logger for this module
logger = get_logger(__name__)


def read_output_file(file_path: str = "./output.log") -> Optional[str]:
    """Read the content of the output file.

    Args:
        file_path: Path to the output file

    Returns:
        The content of the file or None if file doesn't exist
    """
    try:
        with open(file_path, "r") as output_file:
            return output_file.read()
    except FileNotFoundError:
        logger.exception(f"Output file not found: {file_path}")
        return None
    except Exception as e:
        logger.exception(f"Error reading output file: {e}")
        raise


def add_cdk_diff_comment(
    msg: pull_request_comment.Message, output_content: Optional[str]
) -> bool:
    """Add CDK diff comment to the pull request.

    Args:
        msg: Message object to add comments
        output_content: Content to add as comment

    Returns:
        True if comment was added successfully, False otherwise
    """
    if not output_content:
        comment = "CDK Diff found no resource is going to change"
    else:
        comment = output_content

    logger.info("Adding CDK diff comment")
    return msg.add_msg(comment=comment)


def add_validation_reports(
    msg: pull_request_comment.Message, templates_dir: str = "./synth/templates/"
) -> None:
    """Add validation reports from CSV files to the pull request.

    Args:
        msg: Message object to add comments
        templates_dir: Directory containing CSV template files
    """
    templates_path = Path(templates_dir)

    if not templates_path.exists():
        logger.warning(f"Templates directory not found: {templates_dir}")
        return

    for csv_file in templates_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            if not df.empty:
                logger.info(f"Adding CDK Validation report from {csv_file.name}")
                if not msg.add_msg(comment=df.to_markdown()):
                    logger.error(
                        f"Failed to add validation report from {csv_file.name}"
                    )
        except Exception as e:
            logger.exception(f"Error processing CSV file {csv_file}: {e}")


def main():
    """Create Pull Request comments within azure-pipelines-pr.yml."""
    msg = pull_request_comment.Message()

    # Add CDK diff comment
    output_content = read_output_file()
    if not add_cdk_diff_comment(msg, output_content):
        logger.error("Failed to add CDK diff comment")

    # Add validation reports
    add_validation_reports(msg)


if __name__ == "__main__":
    main()
