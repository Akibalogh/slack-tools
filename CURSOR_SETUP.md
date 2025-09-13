# Cursor IDE Setup for ETL/Data Processing

This document outlines the Cursor IDE configuration and extensions set up for the Slack Tools ETL project.

## 🚀 Installed Extensions

### Core Python Development
- **Python** (ms-python.python) - Core Python language support
- **Black Formatter** (ms-python.black-formatter) - Code formatting
- **Flake8** (ms-python.flake8) - Linting and code quality
- **Jupyter** (ms-toolsai.jupyter) - Interactive notebooks for data analysis

### Database & SQL
- **SQLTools** (mtxr.sqltools) - Database connection and query management
- **SQLite Driver** (mtxr.sqltools-driver-sqlite) - SQLite database support

### Data Processing
- **Rainbow CSV** (mechatroner.rainbow-csv) - Color-coded CSV viewing
- **Edit CSV** (janisdd.vscode-edit-csv) - CSV editing capabilities
- **Excel Viewer** (grapecity.gc-excelviewer) - Excel file preview
- **JSON Tools** - JSON formatting and validation

### File Management
- **GitLens** (eamodio.gitlens) - Enhanced Git capabilities
- **Path Intellisense** (christian-kohler.path-intellisense) - File path autocomplete
- **YAML** (redhat.vscode-yaml) - YAML file support
- **TOML** (tamasfe.even-better-toml) - TOML configuration files

### Development Tools
- **REST Client** (humao.rest-client) - API testing
- **Prettier** (esbenp.prettier-vscode) - Code formatting

## 🔧 Configuration Files

### `.cursor/settings.json`
- Python interpreter path: `./venv/bin/python`
- Code formatting with Black (88 character line length)
- Linting with Flake8
- Pytest testing configuration
- File associations for data formats (JSON, CSV, YAML, TOML)
- Database connections for RepSplit and Slack data
- Excluded directories for better performance

### `.cursor/mcp.json`
- **Task Master AI** - Project management integration
- **Filesystem MCP** - Enhanced file operations for data directories

### `.cursor/launch.json`
- **ETL Pipeline** - Debug the main ETL process
- **Slack Ingest** - Debug Slack data ingestion
- **Commission Analysis** - Debug sales process analysis
- **Python Tests** - Run pytest with proper configuration

### `.cursor/tasks.json`
- **Run ETL Pipeline** - Execute the main ETL process
- **Run Slack Ingest** - Execute Slack data ingestion
- **Run Tests** - Execute test suite
- **Format Code** - Format code with Black
- **Lint Code** - Run Flake8 linting
- **Install Dependencies** - Install Python packages

## 📊 Data Analysis Notebooks

### `notebooks/etl_analysis.ipynb`
Interactive Jupyter notebook for ETL pipeline analysis with:
- Database connection setup
- Data loading from SQLite
- Basic data exploration templates

## 🎯 Key Features for ETL Work

### 1. **Database Integration**
- Direct SQLite database connections
- Query execution and result viewing
- Database schema exploration

### 2. **Data Format Support**
- JSON validation and formatting
- CSV color-coding and editing
- Excel file preview
- YAML/TOML configuration files

### 3. **Python Development**
- Advanced IntelliSense with Pylance
- Integrated testing with pytest
- Code formatting and linting
- Interactive Jupyter notebooks

### 4. **File Management**
- Enhanced Git capabilities
- Path autocomplete
- Excluded directories for performance
- REST API testing

## 🚀 Quick Start

1. **Restart Cursor** to load all extensions
2. **Open a Python file** to activate language features
3. **Use Command Palette** (`Cmd+Shift+P`):
   - `Python: Select Interpreter` - Set Python path
   - `SQLTools: Add New Connection` - Configure databases
   - `Jupyter: Create New Notebook` - Start data analysis
4. **Use Tasks** (`Cmd+Shift+P` → `Tasks: Run Task`):
   - Run ETL Pipeline
   - Run Tests
   - Format Code

## 📁 Project Structure Integration

The configuration is optimized for this project structure:
```
slack-tools/
├── data/           # Data files (CSV, JSON)
├── output/         # ETL outputs
├── analysis/       # Analysis scripts
├── notebooks/      # Jupyter notebooks
├── src/           # Source code
├── scripts/       # Utility scripts
└── tests/         # Test files
```

## 🔍 Database Connections

Pre-configured SQLite connections:
- **RepSplit DB**: `./repsplit_orm.db` - Main application database
- **Slack Data DB**: `./data/slack/slack_data.db` - Slack export data

## 🎨 Code Quality

- **Black formatting** with 88-character line length
- **Flake8 linting** for code quality
- **Pytest testing** with proper Python path configuration
- **Type checking** with Pylance

## 📝 Usage Tips

1. **CSV Files**: Open CSV files to see color-coded columns
2. **JSON Files**: Use `Cmd+Shift+P` → `Format Document` for JSON
3. **Database**: Use SQLTools panel to explore database structure
4. **Notebooks**: Create `.ipynb` files for interactive analysis
5. **Testing**: Use the test explorer or run tasks for testing

## 🔄 MCP Integration

The Model Context Protocol (MCP) integration provides:
- **Filesystem access** to data directories
- **Task management** with Task Master AI
- **Enhanced file operations** for ETL workflows

This setup provides a comprehensive development environment optimized for ETL, data processing, and analysis workflows.
