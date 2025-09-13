"""
Unit tests for company name processing functions
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from repsplit import RepSplit


class TestCompanyNameProcessing:
    """Test company name processing and normalization"""
    
    @pytest.fixture
    def repsplit(self):
        """Create RepSplit instance for testing"""
        return RepSplit()
    
    def test_full_node_address_generation(self, repsplit):
        """Test full node address generation"""
        test_cases = [
            ("allnodes", "allnodes::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"),
            ("bitgo", "bitgo::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"),
            ("nansen", "nansen::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"),
            ("figment", "figment::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"),
        ]
        
        for company_name, expected in test_cases:
            result = repsplit.get_full_node_address(company_name)
            assert result == expected, f"Expected {expected}, got {result} for input '{company_name}'"
    
    def test_full_node_address_edge_cases(self, repsplit):
        """Test edge cases in full node address generation"""
        test_cases = [
            ("", "::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"),
            ("  spaced  company  ", "-spaced-company-::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"),
            ("UPPERCASE", "uppercase::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"),
            ("company-with-bitsafe", "company-with::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"),
        ]
        
        for company_name, expected in test_cases:
            result = repsplit.get_full_node_address(company_name)
            assert result == expected, f"Expected {expected}, got {result} for input '{company_name}'"
    
    def test_stage_detection_workflow(self, repsplit):
        """Test stage detection in messages"""
        # Test message with sourcing keywords
        sourcing_message = "I'll intro you to the team and loop in the right people"
        stages = repsplit.detect_stages_in_message(sourcing_message)
        
        assert len(stages) > 0, "Should detect stages in message"
        sourcing_stages = [stage for stage, _ in stages if "sourcing" in stage]
        assert len(sourcing_stages) > 0, "Should detect sourcing stage"
        
        # Test message with discovery keywords
        discovery_message = "What are your requirements and use case for this solution?"
        stages = repsplit.detect_stages_in_message(discovery_message)
        
        discovery_stages = [stage for stage, _ in stages if "discovery" in stage]
        assert len(discovery_stages) > 0, "Should detect discovery stage"
    
    def test_commission_calculation_logic(self, repsplit):
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
    
    def test_config_loading(self, repsplit):
        """Test configuration loading"""
        assert repsplit.config is not None
        assert "participants" in repsplit.config
        assert "stages" in repsplit.config
        assert len(repsplit.config["participants"]) > 0
        assert len(repsplit.config["stages"]) > 0
    
    def test_database_initialization(self, repsplit):
        """Test database initialization"""
        # Check if database path is set
        assert hasattr(repsplit, 'db_path')
        assert repsplit.db_path is not None
        
        # Check if output directories are set
        assert hasattr(repsplit, 'output_dir')
        assert hasattr(repsplit, 'justifications_dir')


if __name__ == "__main__":
    pytest.main([__file__])
