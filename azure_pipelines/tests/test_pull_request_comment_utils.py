"""
Tests for the pull_requests.comment module.
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest

from azure_pipelines.pull_requests import comment


@pytest.fixture
def mock_message():
    """Mock Message instance."""
    return MagicMock()


def test_read_output_file_success(mock_file_content):
    """Test read_output_file with successful file read."""
    file_path = "./output.log"

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        result = comment.read_output_file(file_path)

        assert result == mock_file_content


def test_read_output_file_not_found():
    """Test read_output_file when file is not found."""
    file_path = "./nonexistent.log"

    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = comment.read_output_file(file_path)

        assert result is None


def test_read_output_file_error():
    """Test read_output_file with other errors."""
    file_path = "./error.log"

    with patch("builtins.open", side_effect=PermissionError()), pytest.raises(
        PermissionError
    ):
        comment.read_output_file(file_path)


def test_add_cdk_diff_comment_with_content(mock_message, mock_file_content):
    """Test add_cdk_diff_comment with content."""
    result = comment.add_cdk_diff_comment(mock_message, mock_file_content)

    mock_message.add_msg.assert_called_once_with(comment=mock_file_content)
    assert result == mock_message.add_msg.return_value


def test_add_cdk_diff_comment_without_content(mock_message):
    """Test add_cdk_diff_comment without content."""
    result = comment.add_cdk_diff_comment(mock_message, None)

    mock_message.add_msg.assert_called_once_with(
        comment="CDK Diff found no resource is going to change"
    )
    assert result == mock_message.add_msg.return_value


def test_add_validation_reports_directory_not_found(mock_message):
    """Test add_validation_reports when directory is not found."""
    templates_dir = "./nonexistent/"

    with patch("pathlib.Path.exists", return_value=False):
        comment.add_validation_reports(mock_message, templates_dir)

        mock_message.add_msg.assert_not_called()


def test_add_validation_reports_with_csv_files(mock_message, sample_dataframe):
    """Test add_validation_reports with CSV files."""
    templates_dir = "./synth/templates/"
    csv_files = [
        Path(templates_dir) / "report1.csv",
        Path(templates_dir) / "report2.csv",
    ]

    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.glob", return_value=csv_files
    ), patch("pandas.read_csv", return_value=sample_dataframe):

        comment.add_validation_reports(mock_message, templates_dir)

        # Should be called once for each CSV file
        assert mock_message.add_msg.call_count == 2
        mock_message.add_msg.assert_called_with(comment=sample_dataframe.to_markdown())


def test_add_validation_reports_with_empty_csv(mock_message):
    """Test add_validation_reports with empty CSV files."""
    templates_dir = "./synth/templates/"
    csv_files = [Path(templates_dir) / "empty.csv"]
    empty_df = pd.DataFrame()

    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.glob", return_value=csv_files
    ), patch("pandas.read_csv", return_value=empty_df):

        comment.add_validation_reports(mock_message, templates_dir)

        # Should not be called for empty DataFrames
        mock_message.add_msg.assert_not_called()


def test_add_validation_reports_with_error(mock_message, sample_dataframe):
    """Test add_validation_reports with error during processing."""
    templates_dir = "./synth/templates/"
    csv_files = [Path(templates_dir) / "report1.csv", Path(templates_dir) / "error.csv"]

    def mock_read_csv(file_path):
        if "error.csv" in str(file_path):
            raise Exception("CSV error")
        return sample_dataframe

    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.glob", return_value=csv_files
    ), patch("pandas.read_csv", side_effect=mock_read_csv):

        # Should not raise exception
        comment.add_validation_reports(mock_message, templates_dir)

        # Should be called only for the successful CSV
        assert mock_message.add_msg.call_count == 1


def test_main_success(mock_pull_request_comment, mock_file_content):
    """Test main function with successful execution."""
    with patch(
        "azure_pipelines.pull_requests.comment.read_output_file",
        return_value=mock_file_content,
    ), patch(
        "azure_pipelines.pull_requests.comment.add_cdk_diff_comment", return_value=True
    ), patch(
        "azure_pipelines.pull_requests.comment.add_validation_reports"
    ) as mock_add_reports:

        comment.main()

        mock_add_reports.assert_called_once()


def test_main_comment_failure(mock_pull_request_comment, mock_file_content):
    """Test main function with comment failure."""
    with patch(
        "azure_pipelines.pull_requests.comment.read_output_file",
        return_value=mock_file_content,
    ), patch(
        "azure_pipelines.pull_requests.comment.add_cdk_diff_comment", return_value=False
    ), patch(
        "azure_pipelines.pull_requests.comment.add_validation_reports"
    ) as mock_add_reports:

        comment.main()

        # Should still try to add validation reports even if comment fails
        mock_add_reports.assert_called_once()
