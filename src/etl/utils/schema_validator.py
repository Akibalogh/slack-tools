#!/usr/bin/env python3
"""
ETL Output Schema Validator

Validates ETL output against the standardized JSON schema.
Provides detailed validation errors and warnings.
"""

import json
import os
from typing import Dict, List, Any, Tuple
from jsonschema import validate, ValidationError, Draft7Validator
from jsonschema.exceptions import SchemaError


class ETLSchemaValidator:
    """Validates ETL output against the standardized schema"""
    
    def __init__(self, schema_path: str = None):
        """Initialize validator with schema file"""
        if schema_path is None:
            schema_path = os.path.join(os.path.dirname(__file__), '..', 'schemas', 'etl_output_schema.json')
        
        self.schema_path = schema_path
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema from file"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON schema: {e}")
    
    def validate_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """Validate ETL output file against schema"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.validate_data(data)
        except FileNotFoundError:
            return False, [f"File not found: {file_path}"]
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate data dictionary against schema"""
        errors = []
        
        try:
            # Validate against schema
            validate(instance=data, schema=self.schema)
            
            # Additional business logic validations
            business_errors = self._validate_business_rules(data)
            errors.extend(business_errors)
            
            return len(errors) == 0, errors
            
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            if hasattr(e, 'path') and e.path:
                errors.append(f"Path: {' -> '.join(str(p) for p in e.path)}")
            return False, errors
        except SchemaError as e:
            errors.append(f"Schema error: {e}")
            return False, errors
    
    def _validate_business_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validate business logic rules beyond JSON schema"""
        errors = []
        
        # Check metadata consistency
        metadata = data.get('metadata', {})
        statistics = data.get('statistics', {})
        
        # Total companies should match between metadata and statistics
        meta_companies = metadata.get('total_companies', 0)
        stats_companies = statistics.get('total_companies', 0)
        if meta_companies != stats_companies:
            errors.append(f"Company count mismatch: metadata={meta_companies}, statistics={stats_companies}")
        
        # Check data source consistency
        data_sources = metadata.get('data_sources', [])
        companies = data.get('companies', {})
        
        # Validate that companies with data have corresponding source flags
        for company_name, company_data in companies.items():
            for source in ['slack', 'telegram', 'calendar', 'hubspot']:
                source_data = company_data.get(source, {})
                has_data = self._has_actual_data(source_data, source)
                
                # Check statistics consistency
                coverage_key = company_name.replace('-', '_')  # Handle naming differences
                coverage = statistics.get('data_coverage', {}).get(coverage_key, {})
                has_flag = coverage.get(f'has_{source}', False)
                
                if has_data and not has_flag:
                    errors.append(f"Company {company_name} has {source} data but coverage flag is False")
                elif not has_data and has_flag:
                    errors.append(f"Company {company_name} has no {source} data but coverage flag is True")
        
        # Validate performance stats
        perf_stats = metadata.get('performance_stats', {})
        total_errors = perf_stats.get('total_errors', 0)
        if total_errors > 0:
            errors.append(f"ETL processing had {total_errors} errors - review logs")
        
        return errors
    
    def _has_actual_data(self, source_data: Dict[str, Any], source: str) -> bool:
        """Check if source data actually contains meaningful content"""
        if source == 'slack':
            channels = source_data.get('channels', [])
            return len(channels) > 0 and any(
                len(channel.get('messages', [])) > 0 
                for channel in channels
            )
        elif source == 'telegram':
            chats = source_data.get('chats', [])
            return len(chats) > 0 and any(
                len(chat.get('messages', [])) > 0 
                for chat in chats
            )
        elif source == 'calendar':
            meetings = source_data.get('meetings', [])
            return len(meetings) > 0
        elif source == 'hubspot':
            deals = source_data.get('deals', [])
            contacts = source_data.get('contacts', [])
            return len(deals) > 0 or len(contacts) > 0
        
        return False
    
    def get_validation_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of validation results"""
        is_valid, errors = self.validate_data(data)
        
        metadata = data.get('metadata', {})
        statistics = data.get('statistics', {})
        companies = data.get('companies', {})
        
        summary = {
            'is_valid': is_valid,
            'error_count': len(errors),
            'errors': errors,
            'data_summary': {
                'total_companies': len(companies),
                'companies_with_slack': statistics.get('companies_with_slack', 0),
                'companies_with_telegram': statistics.get('companies_with_telegram', 0),
                'companies_with_calendar': statistics.get('companies_with_calendar', 0),
                'companies_with_hubspot': statistics.get('companies_with_hubspot', 0),
                'total_errors': metadata.get('performance_stats', {}).get('total_errors', 0)
            },
            'schema_version': metadata.get('etl_version', 'unknown'),
            'generated_at': metadata.get('generated_at', 'unknown')
        }
        
        return summary


def main():
    """CLI interface for schema validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate ETL output against schema')
    parser.add_argument('file', help='ETL output JSON file to validate')
    parser.add_argument('--schema', help='Custom schema file path')
    parser.add_argument('--summary', action='store_true', help='Show validation summary')
    
    args = parser.parse_args()
    
    try:
        validator = ETLSchemaValidator(args.schema)
        is_valid, errors = validator.validate_file(args.file)
        
        if is_valid:
            print("✅ ETL output is valid!")
        else:
            print("❌ ETL output validation failed:")
            for error in errors:
                print(f"  - {error}")
        
        if args.summary:
            with open(args.file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            summary = validator.get_validation_summary(data)
            print(f"\n📊 Validation Summary:")
            print(f"  Valid: {summary['is_valid']}")
            print(f"  Errors: {summary['error_count']}")
            print(f"  Companies: {summary['data_summary']['total_companies']}")
            print(f"  Schema Version: {summary['schema_version']}")
            print(f"  Generated: {summary['generated_at']}")
        
        exit(0 if is_valid else 1)
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        exit(1)


if __name__ == '__main__':
    main()
