"""
Data validation tests for output files
"""
import pytest
import sys
import os
import csv
import json
import shutil
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from repsplit import RepSplit


class TestOutputValidation:
    """Test output file data validation"""
    
    @pytest.fixture
    def sample_output_files(self):
        """Create sample output files for testing"""
        # Create temporary output directory
        output_dir = Path("tests/data_validation/test_output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample deal_rationale.csv
        deal_rationale_path = output_dir / "deal_rationale.csv"
        with open(deal_rationale_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Full Node Address", "Aki %", "Addie %", "Mayank %", "Amy %",
                "Contestation Level", "Most Likely Owner", "Calendar Meetings",
                "Sourcing/Intro", "Discovery/Qual", "Solution", "Objection",
                "Technical", "Pricing", "Contract", "Scheduling", "Closing", "Rationale"
            ])
            writer.writerow([
                "allnodes::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2",
                "75", "25", "0", "0", "Low", "Aki", "2", "1", "1", "0", "0", "0", "0", "0", "0", "0", "Aki led intro and discovery"
            ])
        
        # Create sample commission_splits.csv
        commission_splits_path = output_dir / "commission_splits.csv"
        with open(commission_splits_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Deal ID", "Aki", "Addie", "Amy", "Mayank", "Prateek", "Will", "Kadeem"])
            writer.writerow(["allnodes", "75", "25", "0", "0", "0", "0", "0"])
        
        yield {
            "deal_rationale": deal_rationale_path,
            "commission_splits": commission_splits_path,
            "output_dir": output_dir
        }
        
        # Cleanup
        shutil.rmtree(output_dir)
    
    def test_deal_rationale_structure(self, sample_output_files):
        """Test deal_rationale.csv file structure"""
        deal_rationale_path = sample_output_files["deal_rationale"]
        
        with open(deal_rationale_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check header structure
        expected_headers = [
            "Full Node Address", "Aki %", "Addie %", "Mayank %", "Amy %",
            "Contestation Level", "Most Likely Owner", "Calendar Meetings",
            "Sourcing/Intro", "Discovery/Qual", "Solution", "Objection",
            "Technical", "Pricing", "Contract", "Scheduling", "Closing", "Rationale"
        ]
        
        assert len(rows) > 0, "Should have at least one data row"
        assert len(rows[0]) == len(expected_headers), "Header count should match expected"
        
        for header in expected_headers:
            assert header in rows[0], f"Header '{header}' should be present"
    
    def test_deal_rationale_data_types(self, sample_output_files):
        """Test deal_rationale.csv data types and validation"""
        deal_rationale_path = sample_output_files["deal_rationale"]
        
        with open(deal_rationale_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        for row in rows:
            # Validate Full Node Address format
            full_node_address = row["Full Node Address"]
            assert "::" in full_node_address, "Full Node Address should contain '::' separator"
            assert len(full_node_address.split("::")[1]) == 68, "Node address should be 68 characters"
            
            # Validate percentage fields are numeric
            for field in ["Aki %", "Addie %", "Mayank %", "Amy %"]:
                value = row[field]
                assert value.isdigit() or value == "0", f"Field {field} should be numeric, got '{value}'"
                percentage = int(value)
                assert 0 <= percentage <= 100, f"Percentage {percentage} should be between 0 and 100"
            
            # Validate contestation level
            contestation = row["Contestation Level"]
            valid_levels = ["Low", "Medium", "High"]
            assert contestation in valid_levels, f"Contestation level '{contestation}' should be one of {valid_levels}"
            
            # Validate stage counts are numeric
            for field in ["Calendar Meetings", "Sourcing/Intro", "Discovery/Qual", "Solution", 
                         "Objection", "Technical", "Pricing", "Contract", "Scheduling", "Closing"]:
                value = row[field]
                assert value.isdigit() or value == "0", f"Field {field} should be numeric, got '{value}'"
                count = int(value)
                assert count >= 0, f"Count {count} should be non-negative"
    
    def test_commission_splits_structure(self, sample_output_files):
        """Test commission_splits.csv file structure"""
        commission_splits_path = sample_output_files["commission_splits"]
        
        with open(commission_splits_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check header structure
        expected_headers = ["Deal ID", "Aki", "Addie", "Amy", "Mayank", "Prateek", "Will", "Kadeem"]
        
        assert len(rows) > 0, "Should have at least one data row"
        assert len(rows[0]) == len(expected_headers), "Header count should match expected"
        
        for header in expected_headers:
            assert header in rows[0], f"Header '{header}' should be present"
    
    def test_commission_splits_data_validation(self, sample_output_files):
        """Test commission_splits.csv data validation"""
        commission_splits_path = sample_output_files["commission_splits"]
        
        with open(commission_splits_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        for row in rows:
            # Validate Deal ID is not empty
            deal_id = row["Deal ID"]
            assert deal_id.strip(), "Deal ID should not be empty"
            
            # Validate commission percentages
            total_percentage = 0
            for field in ["Aki", "Addie", "Amy", "Mayank", "Prateek", "Will", "Kadeem"]:
                value = row[field]
                assert value.isdigit() or value == "0", f"Field {field} should be numeric, got '{value}'"
                percentage = int(value)
                assert 0 <= percentage <= 100, f"Percentage {percentage} should be between 0 and 100"
                total_percentage += percentage
            
            # Total should be 100% or 0% (if no commission)
            assert total_percentage in [0, 100], f"Total percentage {total_percentage} should be 0 or 100"
    
    def test_output_file_consistency(self, sample_output_files):
        """Test consistency between output files"""
        deal_rationale_path = sample_output_files["deal_rationale"]
        commission_splits_path = sample_output_files["commission_splits"]
        
        # Read both files
        with open(deal_rationale_path, 'r') as f:
            deal_reader = csv.DictReader(f)
            deal_rows = list(deal_reader)
        
        with open(commission_splits_path, 'r') as f:
            commission_reader = csv.DictReader(f)
            commission_rows = list(commission_reader)
        
        # Extract company names for comparison
        deal_companies = set()
        for row in deal_rows:
            full_node = row["Full Node Address"]
            company = full_node.split("::")[0]
            deal_companies.add(company)
        
        commission_companies = set()
        for row in commission_rows:
            company = row["Deal ID"]
            commission_companies.add(company)
        
        # Companies should match between files
        assert deal_companies == commission_companies, "Company lists should match between output files"
    
    def test_full_node_address_format(self, sample_output_files):
        """Test full node address format validation"""
        deal_rationale_path = sample_output_files["deal_rationale"]
        
        with open(deal_rationale_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        for row in rows:
            full_node_address = row["Full Node Address"]
            
            # Should have exactly one '::' separator
            parts = full_node_address.split("::")
            assert len(parts) == 2, f"Full Node Address should have exactly one '::' separator, got {len(parts)-1}"
            
            company_name, node_address = parts
            
            # Company name should not be empty
            assert company_name.strip(), "Company name should not be empty"
            
            # Node address should be exactly 68 characters (hex)
            assert len(node_address) == 68, f"Node address should be 68 characters, got {len(node_address)}"
            
            # Node address should be valid hex
            try:
                int(node_address, 16)
            except ValueError:
                pytest.fail(f"Node address '{node_address}' should be valid hexadecimal")


if __name__ == "__main__":
    pytest.main([__file__])
