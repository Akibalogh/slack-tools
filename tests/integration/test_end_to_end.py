"""
Integration tests for end-to-end workflow
"""
import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from repsplit import RepSplit


class TestEndToEndWorkflow:
    """Test complete workflow from data import to output generation"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_repsplit(self, temp_dir):
        """Create RepSplit instance with test configuration"""
        # Create test config
        test_config = {
            "slack_token": "test_token",
            "participants": [
                {"name": "Aki", "slack_id": "U123", "display_name": "Aki", "email": "aki@test.com"},
                {"name": "Addie", "slack_id": "U456", "display_name": "Addie", "email": "addie@test.com"},
                {"name": "Mayank", "slack_id": "U789", "display_name": "Mayank", "email": "mayank@test.com"},
                {"name": "Amy", "slack_id": "U101", "display_name": "Amy", "email": "amy@test.com"},
            ],
            "stages": [
                {
                    "name": "sourcing_intro",
                    "weight": 8.0,
                    "keywords": ["intro", "connect", "loop in", "reached out", "waitlist", "referral"]
                },
                {
                    "name": "discovery_qual",
                    "weight": 12.0,
                    "keywords": ["questions", "requirements", "use case", "needs", "challenge", "timeline"]
                }
            ]
        }
        
        # Create test config file
        config_path = Path(temp_dir) / "test_config.json"
        import json
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        return RepSplit(str(config_path))
    
    def test_config_loading(self, test_repsplit):
        """Test that configuration loads correctly"""
        assert test_repsplit.config is not None
        assert "participants" in test_repsplit.config
        assert "stages" in test_repsplit.config
        assert len(test_repsplit.config["participants"]) == 4
        assert len(test_repsplit.config["stages"]) == 2
    
    def test_database_initialization(self, test_repsplit):
        """Test database initialization"""
        # Check if database file exists
        db_path = Path(test_repsplit.db_path)
        assert db_path.exists(), "Database should be created"
        
        # Check if tables exist
        import sqlite3
        conn = sqlite3.connect(test_repsplit.db_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['conversations', 'users', 'messages', 'stage_detections', 'telegram_messages']
        for table in expected_tables:
            assert table in tables, f"Table {table} should exist"
        
        conn.close()
    
    def test_stage_detection_workflow(self, test_repsplit):
        """Test stage detection in messages"""
        # Test message with sourcing keywords
        sourcing_message = "I'll intro you to the team and loop in the right people"
        stages = test_repsplit.detect_stages_in_message(sourcing_message)
        
        assert len(stages) > 0, "Should detect stages in message"
        sourcing_stages = [stage for stage, _ in stages if "sourcing" in stage]
        assert len(sourcing_stages) > 0, "Should detect sourcing stage"
        
        # Test message with discovery keywords
        discovery_message = "What are your requirements and use case for this solution?"
        stages = test_repsplit.detect_stages_in_message(discovery_message)
        
        discovery_stages = [stage for stage, _ in stages if "discovery" in stage]
        assert len(discovery_stages) > 0, "Should detect discovery stage"
    
    def test_commission_calculation_logic(self, test_repsplit):
        """Test commission calculation logic"""
        # Test percentage rounding
        from repsplit import round_to_nearest_25
        
        test_cases = [
            (0, 0.0),
            (12.5, 0.0),
            (25.0, 25.0),
            (37.5, 25.0),
            (50.0, 50.0),
            (62.5, 50.0),
            (75.0, 75.0),
            (87.5, 75.0),
            (100.0, 100.0),
        ]
        
        for input_val, expected in test_cases:
            result = round_to_nearest_25(input_val)
            assert result == expected, f"Expected {expected}, got {result} for input {input_val}"
    
    def test_output_directory_creation(self, test_repsplit):
        """Test output directory creation"""
        output_dir = Path(test_repsplit.output_dir)
        justifications_dir = Path(test_repsplit.justifications_dir)
        
        assert output_dir.exists(), "Output directory should be created"
        assert justifications_dir.exists(), "Justifications directory should be created"
    
    @pytest.mark.slow
    def test_full_analysis_workflow(self, test_repsplit):
        """Test complete analysis workflow (marked as slow)"""
        # This test would run the full analysis if we had test data
        # For now, just verify the method exists and can be called
        assert hasattr(test_repsplit, 'run_analysis'), "run_analysis method should exist"
        assert callable(test_repsplit.run_analysis), "run_analysis should be callable"


if __name__ == "__main__":
    pytest.main([__file__])
