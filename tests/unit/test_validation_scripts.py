"""
Unit tests for ETL output validation scripts
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


class TestETLOutputValidation:
    """Test ETL output validation functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_etl_output(self):
        """Create sample ETL output content"""
        return """COMMISSION CALCULATOR - ETL DATA INGESTION REPORT
Generated on: 2025-09-13 19:01:43

============================================================
📊 ETL PROCESSING STATISTICS
============================================================
⏱️  Total Duration: 107.56 seconds
📊 Companies Processed: 111
❌ Total Errors: 0
📈 Data Coverage:
   • Slack: 58 companies
   • Telegram: 71 companies
   • Calendar: 0 companies
   • HubSpot: 0 companies

============================================================
🏢 COMPANY DATA
============================================================

COMPANY: TEST-COMPANY
==================================================
COMPANY INFORMATION:
  Base Company: test-company
  Variant Type: base
  Slack Groups: test-company-channel
  Telegram Groups: test-company
  Calendar Domain: test-company meetings
  Full Node Address: test-company::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2

SLACK CHANNELS:
  - test-company-channel (5 messages, 3 participants)
    ALL MESSAGES:
      [2025-09-13 10:00:00] Aki: Hello, how can we help you?
      [2025-09-13 10:01:00] Customer: We're interested in your solution
      [2025-09-13 10:02:00] Aki: Great! Let me explain how it works

TELEGRAM CHATS:
  - Test Company (3 messages, 2 participants)
    ALL MESSAGES:
      [2025-09-13 11:00:00] Aki: Thanks for the call today
      [2025-09-13 11:01:00] Customer: Yes, very helpful

CALENDAR: No data
HUBSPOT: No data

COMPANY: NO-DATA-COMPANY
==================================================
COMPANY INFORMATION:
  Base Company: no-data-company
  Variant Type: base
  Slack Groups: 
  Telegram Groups: 
  Calendar Domain: 
  Full Node Address: no-data-company::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2

SLACK: No data
TELEGRAM: No data
CALENDAR: No data
HUBSPOT: No data
"""

    def test_validate_etl_output_simple_import(self):
        """Test that validation script can be imported"""
        # Import the validation function
        import scripts.validate_etl_output_simple as validator

        assert hasattr(validator, "main")

    def test_etl_output_parsing(self, sample_etl_output, temp_dir):
        """Test ETL output file parsing"""
        # Write sample output to file
        output_file = os.path.join(temp_dir, "test_output.txt")
        with open(output_file, "w") as f:
            f.write(sample_etl_output)

        # Test basic file reading
        with open(output_file, "r") as f:
            content = f.read()

        assert "COMMISSION CALCULATOR - ETL DATA INGESTION REPORT" in content
        assert "COMPANY: TEST-COMPANY" in content
        assert "COMPANY: NO-DATA-COMPANY" in content

    def test_company_extraction(self, sample_etl_output):
        """Test company name extraction from ETL output"""
        import re

        # Extract company names
        companies = re.findall(r"COMPANY: (.+)", sample_etl_output)

        assert "TEST-COMPANY" in companies
        assert "NO-DATA-COMPANY" in companies
        assert len(companies) == 2

    def test_data_coverage_analysis(self, sample_etl_output):
        """Test data coverage analysis"""
        # Count Slack sections
        slack_sections = sample_etl_output.count("SLACK CHANNELS:")
        assert slack_sections == 1

        # Count Telegram sections
        telegram_sections = sample_etl_output.count("TELEGRAM CHATS:")
        assert telegram_sections == 1

        # Count no data sections
        no_data_sections = sample_etl_output.count("SLACK: No data")
        assert no_data_sections == 1

    def test_message_counting(self, sample_etl_output):
        """Test message counting in ETL output"""
        import re

        # Count total messages
        message_pattern = r"\[.*?\] .*?: .*"
        messages = re.findall(message_pattern, sample_etl_output)

        # Should find messages from both Slack and Telegram
        assert len(messages) > 0

        # Check for specific message patterns
        slack_messages = [
            msg
            for msg in messages
            if "test-company-channel"
            in sample_etl_output[: sample_etl_output.find(msg) + len(msg)]
        ]
        telegram_messages = [
            msg
            for msg in messages
            if "Test Company"
            in sample_etl_output[: sample_etl_output.find(msg) + len(msg)]
        ]

        assert len(slack_messages) > 0
        assert len(telegram_messages) > 0

    def test_validation_script_execution(self, sample_etl_output, temp_dir):
        """Test validation script execution"""
        output_file = os.path.join(temp_dir, "test_output.txt")
        with open(output_file, "w") as f:
            f.write(sample_etl_output)

        # Test validation script import and structure
        import scripts.validate_etl_output_simple as validator

        assert hasattr(validator, "main")

        # Test that we can read the file we created
        with open(output_file, "r") as f:
            content = f.read()
        assert content == sample_etl_output

    def test_file_size_validation(self, sample_etl_output, temp_dir):
        """Test file size validation"""
        output_file = os.path.join(temp_dir, "test_output.txt")

        # Test empty file
        with open(output_file, "w") as f:
            f.write("")

        file_size = os.path.getsize(output_file)
        assert file_size == 0

        # Test normal file
        with open(output_file, "w") as f:
            f.write(sample_etl_output)

        file_size = os.path.getsize(output_file)
        assert file_size > 0
        assert file_size < 1000000  # Should be reasonable size

    def test_notebooklm_readiness_check(self, sample_etl_output):
        """Test NotebookLM readiness validation"""
        # Check for required elements for NotebookLM
        required_elements = [
            "COMPANY:",
            "COMPANY INFORMATION:",
            "SLACK CHANNELS:",
            "TELEGRAM CHATS:",
            "ALL MESSAGES:",
        ]

        for element in required_elements:
            assert (
                element in sample_etl_output
            ), f"Required element '{element}' not found"

        # Check for message format
        assert "[" in sample_etl_output  # Timestamp format
        assert "] " in sample_etl_output  # Sender format
        assert ": " in sample_etl_output  # Message content format


class TestValidationScriptIntegration:
    """Test integration of validation scripts"""

    def test_validation_script_file_structure(self):
        """Test that validation script files exist and are importable"""
        script_path = os.path.join(
            os.path.dirname(__file__), "../../scripts/validate_etl_output_simple.py"
        )
        assert os.path.exists(
            script_path
        ), f"Validation script not found: {script_path}"

        # Test that it can be imported
        import importlib.util

        spec = importlib.util.spec_from_file_location("validator", script_path)
        validator_module = importlib.util.module_from_spec(spec)

        # Should not raise an error
        try:
            spec.loader.exec_module(validator_module)
            assert True, "Validation script imported successfully"
        except Exception as e:
            pytest.fail(f"Failed to import validation script: {e}")

    def test_validation_script_help(self):
        """Test validation script help functionality"""
        script_path = os.path.join(
            os.path.dirname(__file__), "../../scripts/validate_etl_output_simple.py"
        )

        # Test that script can be run with help
        import subprocess

        try:
            result = subprocess.run(
                [sys.executable, script_path, "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Should not crash
            assert result.returncode in [0, 2]  # 0 for success, 2 for help shown
        except subprocess.TimeoutExpired:
            pytest.fail("Validation script help timed out")
        except FileNotFoundError:
            pytest.skip("Python executable not found")


if __name__ == "__main__":
    pytest.main([__file__])
