# Directory Structure

This document describes the organization of the slack-tools repository.

## Root Directory
- `README.md` - Main project documentation
- `CHANGELOG.md` - Project changelog
- `CURSOR_SETUP.md` - Cursor IDE setup instructions
- `TOOL_INTEGRATION_GUIDE.md` - Tool integration guide
- `.env` - Environment variables (not tracked)
- `.env.example` - Environment variables template
- `.gitignore` - Git ignore rules
- `.cursorrules` - Cursor IDE rules (symlink to global rules)

## Core Directories

### `/analysis/`
Analysis scripts for commission calculations and data processing:
- `company_commission_breakdown.py` - Company-specific commission analysis
- `comprehensive_company_mapping.py` - Company mapping utilities
- `map_activities_to_conversations.py` - Activity mapping
- `pipeline_commission_analysis.py` - Pipeline analysis
- `real_company_commission_breakdown.py` - Real company analysis

### `/scripts/`
Utility and processing scripts:
- `codascan-dl.py` - Codascan data downloader
- `create_clean_table.py` - Database table creation
- `google_calendar_integration.py` - Calendar integration
- `company_mapping_table.py` - Company mapping table management
- Various analysis and processing scripts

### `/src/`
Source code for the main application:
- ORM models and database schemas
- Core business logic
- API integrations

### `/output/`
Generated output files (not tracked in git):
- `analysis/` - Analysis report outputs
- `justifications/` - Commission justification files

### `/config/`
Configuration files and setup scripts:
- Logging configuration
- Cursor extensions setup
- Monitoring dashboard

### `/tests/`
Test files and test data

### `/notebooks/`
Jupyter notebooks for data analysis

### `/logs/`
Application log files

## Data Directories (Not Tracked)
- `/data/` - Raw data files (Slack exports, databases, etc.)
- `/venv/` - Python virtual environment

## Hidden Directories
- `/.cursor/` - Cursor IDE configuration
- `/.git/` - Git repository data
- `/.taskmaster/` - Taskmaster project management
- `/.vscode/` - VS Code configuration
- `/.pytest_cache/` - Pytest cache

## Naming Conventions
- Python files use snake_case
- Directories use lowercase with underscores
- Configuration files start with a dot
- Output files are excluded from git tracking
