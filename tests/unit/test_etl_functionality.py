"""
Unit tests for ETL data ingestion functionality
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Mock logging setup before importing ETL module
with patch("logging.FileHandler") as mock_file_handler, patch(
    "logging.basicConfig"
) as mock_basic_config, patch("os.makedirs") as mock_makedirs:

    from src.etl.etl_data_ingestion import DataETL


class TestETLFunctionality:
    """Test ETL data ingestion functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_etl(self, temp_dir):
        """Create DataETL instance with mocked dependencies"""
        with patch("src.etl.etl_data_ingestion.sqlite3.connect"), patch(
            "src.etl.etl_data_ingestion.os.path.exists", return_value=True
        ):

            etl = DataETL(max_workers=2, batch_size=10, quick_mode=True)
            etl.company_mapping_file = "data/company_mapping.csv"
            etl.output_file = os.path.join(temp_dir, "test_output.txt")
            etl.archive_dir = os.path.join(temp_dir, "archive")
            etl.logs_dir = temp_dir

            return etl

    def test_etl_initialization(self, mock_etl):
        """Test ETL initialization"""
        assert mock_etl.max_workers == 2
        assert mock_etl.batch_size == 10
        assert mock_etl.quick_mode == True
        assert mock_etl.stats is not None
        assert "processing_times" in mock_etl.stats

    def test_timer_functionality(self, mock_etl):
        """Test timer start/end functionality"""
        # Test timer start
        mock_etl._start_timer("test_operation")
        assert "test_operation" in mock_etl.stats["processing_times"]

        # Test timer end - just verify it doesn't crash
        duration = mock_etl._end_timer("test_operation")
        assert isinstance(duration, (int, float))
        assert duration >= 0

    def test_company_mapping_loading(self, mock_etl):
        """Test company mapping loading"""
        # Mock the file path to exist
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open()):
                with patch("csv.DictReader") as mock_reader:
                    mock_reader.return_value = [
                        {
                            "Company Name": "test-company",
                            "Base Company": "test-company",
                            "Variants": "base",
                            "Slack Groups": "test-company-channel",
                            "Telegram Groups": "test-company",
                            "Calendar Search Domain": "test-company.com",
                            "Full Node Address": "test-company::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                        }
                    ]

                    companies = mock_etl.load_company_mapping()
                    assert len(companies) == 1
                    assert "test-company" in companies
                    assert companies["test-company"]["base_company"] == "test-company"

    def test_quick_mode_configuration(self, mock_etl):
        """Test quick mode configuration"""
        assert mock_etl.quick_mode == True

    def test_etl_methods_exist(self, mock_etl):
        """Test that ETL methods exist and are callable"""
        # Test public methods exist
        assert hasattr(mock_etl, "load_company_mapping")
        assert hasattr(mock_etl, "ingest_slack_data")
        assert hasattr(mock_etl, "ingest_telegram_data")
        assert hasattr(mock_etl, "ingest_calendar_data")
        assert hasattr(mock_etl, "ingest_hubspot_data")
        assert hasattr(mock_etl, "match_data_to_companies")
        assert hasattr(mock_etl, "run_etl")

        # Test they are callable
        assert callable(mock_etl.load_company_mapping)
        assert callable(mock_etl.ingest_slack_data)
        assert callable(mock_etl.ingest_telegram_data)
        assert callable(mock_etl.ingest_calendar_data)
        assert callable(mock_etl.ingest_hubspot_data)
        assert callable(mock_etl.match_data_to_companies)
        assert callable(mock_etl.run_etl)

    def test_etl_workflow_mock(self, mock_etl, temp_dir):
        """Test ETL workflow with mocked dependencies"""
        with patch.object(mock_etl, "load_company_mapping") as mock_load, patch.object(
            mock_etl, "ingest_slack_data"
        ) as mock_slack, patch.object(
            mock_etl, "ingest_telegram_data"
        ) as mock_telegram, patch.object(
            mock_etl, "ingest_calendar_data"
        ) as mock_calendar, patch.object(
            mock_etl, "ingest_hubspot_data"
        ) as mock_hubspot, patch.object(
            mock_etl, "match_data_to_companies"
        ) as mock_match, patch.object(
            mock_etl, "generate_summary_stats"
        ) as mock_stats:

            # Setup mocks
            mock_load.return_value = {"test-company": {"company_name": "test-company"}}
            mock_slack.return_value = {"test-company": {"slack_data": "test"}}
            mock_telegram.return_value = {"test-company": {"telegram_data": "test"}}
            mock_calendar.return_value = {}
            mock_hubspot.return_value = {}
            mock_match.return_value = {
                "test-company": {"slack_channels": [], "telegram_chats": []}
            }
            mock_stats.return_value = {"total_companies": 1}

            # Run ETL
            result = mock_etl.run_etl()

            # Verify all methods were called
            mock_load.assert_called_once()
            mock_slack.assert_called_once()
            mock_telegram.assert_called_once()
            mock_calendar.assert_called_once()
            mock_hubspot.assert_called_once()
            mock_match.assert_called_once()

            assert result is None  # run_etl returns None


def mock_open(content=""):
    """Helper function to mock file opening"""
    return MagicMock(return_value=MagicMock(read=MagicMock(return_value=content)))


class TestETLUtilities:
    """Test ETL utility functions"""

    def test_text_formatter_import(self):
        """Test that text formatter can be imported"""
        from src.etl.utils.text_formatter import main

        assert callable(main)

    def test_schema_validator_import(self):
        """Test that schema validator can be imported"""
        from src.etl.utils.schema_validator import validate

        assert callable(validate)


if __name__ == "__main__":
    pytest.main([__file__])
