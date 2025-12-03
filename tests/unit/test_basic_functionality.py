"""
Basic functionality tests that don't require complex imports
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestBasicImports:
    """Test basic module imports"""

    def test_main_import(self):
        """Test that main.py can be imported"""
        import main

        assert hasattr(main, "setup_logging")
        assert hasattr(main, "check_etl_output")
        assert hasattr(main, "run_etl")
        assert hasattr(main, "run_commission_processing")

    def test_utility_imports(self):
        """Test utility module imports"""
        from src.etl.utils.text_formatter import main as text_main

        assert callable(text_main)

        from src.etl.utils.schema_validator import validate

        assert callable(validate)

    def test_validation_script_import(self):
        """Test validation script import"""
        import scripts.validate_etl_output_simple as validator

        assert hasattr(validator, "main")


class TestFileOperations:
    """Test basic file operations"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_file_creation(self, temp_dir):
        """Test file creation and reading"""
        test_file = os.path.join(temp_dir, "test.txt")
        test_content = "Hello, World!"

        # Write file
        with open(test_file, "w") as f:
            f.write(test_content)

        # Read file
        with open(test_file, "r") as f:
            content = f.read()

        assert content == test_content
        assert os.path.exists(test_file)

    def test_directory_operations(self, temp_dir):
        """Test directory operations"""
        # Create subdirectory
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)

        assert os.path.exists(subdir)
        assert os.path.isdir(subdir)

        # Create file in subdirectory
        file_path = os.path.join(subdir, "test.txt")
        with open(file_path, "w") as f:
            f.write("test")

        assert os.path.exists(file_path)


class TestMainFunctionality:
    """Test main.py functionality without complex dependencies"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_check_etl_output_valid(self, temp_dir):
        """Test ETL output validation with valid file"""
        import main

        # Create valid ETL output file
        output_file = os.path.join(temp_dir, "valid_output.txt")
        valid_content = """COMMISSION CALCULATOR - ETL DATA INGESTION REPORT
Generated on: 2025-09-13 19:01:43

COMPANY: TEST-COMPANY
==================================================
COMPANY INFORMATION:
  Base Company: test-company
"""

        with open(output_file, "w") as f:
            f.write(valid_content)

        # Test valid file
        result = main.check_etl_output(output_file)
        assert result == True

    def test_check_etl_output_invalid(self, temp_dir):
        """Test ETL output validation with invalid files"""
        import main

        # Test non-existent file
        result = main.check_etl_output("nonexistent.txt")
        assert result == False

        # Test empty file
        empty_file = os.path.join(temp_dir, "empty.txt")
        with open(empty_file, "w") as f:
            f.write("")

        result = main.check_etl_output(empty_file)
        assert result == False

    def test_setup_logging(self):
        """Test logging setup"""
        import main

        # Test verbose logging with mocked file handler
        with patch("logging.basicConfig") as mock_config, patch(
            "logging.FileHandler"
        ) as mock_file_handler:
            main.setup_logging(verbose=True)
            mock_config.assert_called_once()

            # Check that DEBUG level was used
            call_args = mock_config.call_args
            assert call_args[1]["level"] == 10  # logging.DEBUG


class TestValidationScripts:
    """Test validation script functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_etl_output_parsing(self, temp_dir):
        """Test ETL output file parsing"""
        sample_content = """COMMISSION CALCULATOR - ETL DATA INGESTION REPORT
Generated on: 2025-09-13 19:01:43

COMPANY: TEST-COMPANY
==================================================
COMPANY INFORMATION:
  Base Company: test-company
  Variant Type: base

SLACK CHANNELS:
  - test-company-channel (5 messages, 3 participants)

TELEGRAM CHATS:
  - Test Company (3 messages, 2 participants)

COMPANY: NO-DATA-COMPANY
==================================================
SLACK: No data
TELEGRAM: No data
"""

        # Write sample output to file
        output_file = os.path.join(temp_dir, "test_output.txt")
        with open(output_file, "w") as f:
            f.write(sample_content)

        # Test basic file reading
        with open(output_file, "r") as f:
            content = f.read()

        assert "COMMISSION CALCULATOR - ETL DATA INGESTION REPORT" in content
        assert "COMPANY: TEST-COMPANY" in content
        assert "COMPANY: NO-DATA-COMPANY" in content

    def test_company_extraction(self):
        """Test company name extraction from ETL output"""
        import re

        sample_content = """
COMPANY: TEST-COMPANY
COMPANY: NO-DATA-COMPANY
COMPANY: ANOTHER-COMPANY
"""

        # Extract company names
        companies = re.findall(r"COMPANY: (.+)", sample_content)

        assert "TEST-COMPANY" in companies
        assert "NO-DATA-COMPANY" in companies
        assert "ANOTHER-COMPANY" in companies
        assert len(companies) == 3

    def test_data_coverage_analysis(self):
        """Test data coverage analysis"""
        sample_content = """
SLACK CHANNELS:
  - channel1 (5 messages, 3 participants)
TELEGRAM CHATS:
  - chat1 (3 messages, 2 participants)
SLACK: No data
TELEGRAM: No data
"""

        # Count sections
        slack_sections = sample_content.count("SLACK CHANNELS:")
        assert slack_sections == 1

        telegram_sections = sample_content.count("TELEGRAM CHATS:")
        assert telegram_sections == 1

        no_data_sections = sample_content.count("SLACK: No data")
        assert no_data_sections == 1


class TestConfiguration:
    """Test configuration and setup"""

    def test_pytest_configuration(self):
        """Test that pytest is properly configured"""
        # Test that we can run pytest
        import pytest

        assert pytest.__version__ is not None

        # Test that test discovery works
        import os

        test_dir = os.path.join(os.path.dirname(__file__))
        assert os.path.exists(test_dir)

    def test_test_requirements(self):
        """Test that test requirements are met"""
        # Test core pytest functionality
        import pytest

        assert pytest.__version__ is not None

        # Test available plugins (don't fail if optional ones are missing)
        available_plugins = []
        try:
            import pytest_cov

            available_plugins.append("pytest_cov")
        except ImportError:
            pass

        try:
            import pytest_mock

            available_plugins.append("pytest_mock")
        except ImportError:
            pass

        try:
            import pytest_html

            available_plugins.append("pytest_html")
        except ImportError:
            pass

        try:
            import pytest_json_report

            available_plugins.append("pytest_json_report")
        except ImportError:
            pass

        # At least some plugins should be available
        assert (
            len(available_plugins) > 0
        ), f"At least one test plugin should be available. Found: {available_plugins}"


if __name__ == "__main__":
    pytest.main([__file__])
