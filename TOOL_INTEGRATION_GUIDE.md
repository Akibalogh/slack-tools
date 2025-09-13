# Tool Integration Guide

This guide explains how the ETL and data processing tools are integrated into Cursor IDE and when they activate automatically vs. when you need to call them manually.

## 🔄 **Automatic Integration (No Setup Required)**

### **Extensions** - Load Automatically
- **When**: Cursor IDE starts up
- **What**: All installed extensions become available
- **Examples**: 
  - Open a `.csv` file → Rainbow CSV automatically color-codes columns
  - Open a `.json` file → JSON Tools formatting available
  - Open a `.py` file → Python language features activate

### **MCP Servers** - Load from Configuration
- **When**: Cursor starts (reads `.cursor/mcp.json`)
- **What**: Filesystem access, Task Master AI integration
- **Examples**:
  - File operations in data directories
  - Task management through AI integration

### **Database Connections** - Pre-configured
- **When**: SQLTools extension loads
- **What**: RepSplit DB and Slack Data DB connections ready
- **Access**: Activity Bar → Database icon → Select connection

## 🎯 **Manual Activation (Command Palette)**

### **Command Palette** (`Cmd+Shift+P`)
- **Python: Select Interpreter** - Set Python environment
- **SQLTools: Show** - Open database panel
- **Jupyter: Create New Notebook** - Start data analysis
- **Format Document** - Format JSON/CSV files
- **Tasks: Run Task** - Execute predefined tasks

### **Task Runner** (`Cmd+Shift+P` → `Tasks: Run Task`)
- **Run ETL Pipeline** - Execute `python run_etl.py`
- **Run Slack Ingest** - Execute `python slack_ingest.py`
- **Run Tests** - Execute `python -m pytest tests/`
- **Format Code** - Run Black formatter
- **Lint Code** - Run Flake8 linter

## 🐛 **Debug Configurations** (F5 or Debug Panel)

### **Launch Configurations** (`.cursor/launch.json`)
- **Python: ETL Pipeline** - Debug main ETL process
- **Python: Slack Ingest** - Debug Slack data ingestion
- **Python: Commission Analysis** - Debug sales analysis
- **Python: Pytest** - Debug test execution

## 📊 **Interactive Tools**

### **Jupyter Notebooks** (`.ipynb` files)
- **When**: Open a `.ipynb` file
- **What**: Jupyter features activate automatically
- **Templates**: 
  - `notebooks/slack_data_analysis.ipynb` - Slack data analysis
  - `notebooks/etl_analysis.ipynb` - ETL pipeline analysis

### **SQLTools Panel** (Activity Bar)
- **When**: Click database icon in Activity Bar
- **What**: Database connection management and query execution
- **Pre-configured**: RepSplit DB, Slack Data DB

## ⚙️ **Configuration Files**

### **Automatic Loading**
- **`.cursor/settings.json`** - Python, formatting, database settings
- **`.cursor/mcp.json`** - MCP server configurations
- **`.cursor/extensions.json`** - Recommended extensions list

### **Manual Execution**
- **`.cursor/launch.json`** - Debug configurations (F5)
- **`.cursor/tasks.json`** - Task runner definitions (Command Palette)

## 🚀 **Quick Start Workflow**

1. **Open Cursor** → Extensions load automatically
2. **Open Python file** → Language features activate
3. **Open CSV/JSON** → Data tools activate
4. **Use Command Palette** → Access all tools manually
5. **Press F5** → Run debug configurations
6. **Open Notebook** → Jupyter features activate

## 🔧 **Tool-Specific Activation**

### **Database Tools**
- **SQLTools**: Activity Bar → Database icon
- **SQLite Viewer**: Right-click `.db` files
- **Query Execution**: SQLTools panel → Select connection → Run queries

### **Data Format Tools**
- **Rainbow CSV**: Open `.csv` files
- **JSON Tools**: Open `.json` files → `Cmd+Shift+P` → `Format Document`
- **Excel Viewer**: Open `.xlsx` files

### **Python Development**
- **Black Formatter**: Save Python files (auto) or `Cmd+Shift+P` → `Format Document`
- **Flake8 Linting**: Real-time as you type
- **Pytest**: Task runner or Debug panel

### **File Management**
- **Path Intellisense**: Type file paths in Python imports
- **GitLens**: `Cmd+Shift+P` → `GitLens: Show` commands
- **File Utils**: `Cmd+Shift+P` → `File Utils:` commands

## 📝 **No Additional Configuration Needed**

The tools are designed to work out-of-the-box with your ETL project:

- ✅ **Extensions**: Load automatically on Cursor startup
- ✅ **Database Connections**: Pre-configured in settings
- ✅ **MCP Servers**: Load from configuration files
- ✅ **Python Environment**: Auto-detected from settings
- ✅ **File Associations**: Automatic based on file extensions

## 🎯 **When to Use Each Tool**

- **Data Exploration**: Open Jupyter notebooks
- **Database Analysis**: Use SQLTools panel
- **Code Development**: Use Python extensions + debugging
- **File Operations**: Use Path Intellisense + File Utils
- **Data Formatting**: Use Rainbow CSV + JSON Tools
- **Project Management**: Use Task Master AI integration

The integration is seamless - most tools activate automatically when you need them, and manual tools are easily accessible through the Command Palette.
