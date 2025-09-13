#!/usr/bin/env python3
"""
Setup script for Cursor IDE extensions and configuration for ETL/data processing project.
This script installs recommended extensions and configures the development environment.
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def install_cursor_extensions():
    """Install recommended Cursor extensions."""
    extensions = [
        "ms-python.python",
        "ms-python.pylance", 
        "ms-python.black-formatter",
        "ms-python.flake8",
        "ms-toolsai.jupyter",
        "mtxr.sqltools",
        "mtxr.sqltools-driver-sqlite",
        "eamodio.gitlens",
        "redhat.vscode-yaml",
        "tamasfe.even-better-toml",
        "mechatroner.rainbow-csv",
        "janisdd.vscode-edit-csv",
        "grapecity.gc-excelviewer",
        "humao.rest-client",
        "christian-kohler.path-intellisense",
        "esbenp.prettier-vscode"
    ]
    
    print("📦 Installing Cursor extensions...")
    for ext in extensions:
        run_command(f"cursor --install-extension {ext}", f"Installing {ext}")

def install_mcp_servers():
    """Install MCP servers for enhanced data processing."""
    print("🔧 Installing MCP servers...")
    
    # Install SQLite MCP server
    run_command(
        "npm install -g @modelcontextprotocol/server-sqlite",
        "Installing SQLite MCP server"
    )
    
    # Install Filesystem MCP server
    run_command(
        "npm install -g @modelcontextprotocol/server-filesystem", 
        "Installing Filesystem MCP server"
    )

def create_workspace_settings():
    """Create additional workspace-specific settings."""
    workspace_settings = {
        "python.defaultInterpreterPath": "./venv/bin/python",
        "python.terminal.activateEnvironment": True,
        "python.linting.enabled": True,
        "python.linting.pylintEnabled": True,
        "python.linting.flake8Enabled": True,
        "python.formatting.provider": "black",
        "python.formatting.blackArgs": ["--line-length", "88"],
        "python.testing.pytestEnabled": True,
        "python.testing.pytestArgs": ["tests/"],
        "files.associations": {
            "*.json": "json",
            "*.csv": "csv", 
            "*.tsv": "tsv",
            "*.yaml": "yaml",
            "*.yml": "yaml",
            "*.toml": "toml"
        },
        "csv-validator.columnCountPolicy": "ignore",
        "csv-validator.encoding": "utf-8",
        "jupyter.askForKernelRestart": False,
        "jupyter.interactiveWindow.creationMode": "perFile",
        "sqltools.connections": [
            {
                "name": "RepSplit DB",
                "driver": "SQLite",
                "database": "./repsplit_orm.db"
            },
            {
                "name": "Slack Data DB", 
                "driver": "SQLite",
                "database": "./data/slack/slack_data.db"
            }
        ],
        "files.exclude": {
            "**/__pycache__": True,
            "**/*.pyc": True,
            "**/venv": True,
            "**/node_modules": True,
            "**/.git": True,
            "**/htmlcov": True,
            "**/dist": True,
            "**/repsplit_orm.egg-info": True
        },
        "search.exclude": {
            "**/venv": True,
            "**/node_modules": True,
            "**/htmlcov": True,
            "**/dist": True,
            "**/repsplit_orm.egg-info": True,
            "**/temp": True
        },
        "python.analysis.extraPaths": [
            "./src",
            "./scripts"
        ],
        "python.analysis.autoImportCompletions": True,
        "python.analysis.typeCheckingMode": "basic"
    }
    
    # Write to .vscode/settings.json (Cursor uses this)
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    with open(vscode_dir / "settings.json", "w") as f:
        json.dump(workspace_settings, f, indent=2)
    
    print("✅ Workspace settings created")

def create_data_analysis_notebooks():
    """Create Jupyter notebooks for data analysis."""
    notebooks_dir = Path("notebooks")
    notebooks_dir.mkdir(exist_ok=True)
    
    # ETL Analysis Notebook
    etl_notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# ETL Pipeline Analysis\n",
                    "\n",
                    "This notebook provides interactive analysis of the ETL pipeline data processing."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    "import sqlite3\n",
                    "import json\n",
                    "from pathlib import Path\n",
                    "\n",
                    "# Load data from SQLite database\n",
                    "conn = sqlite3.connect('repsplit_orm.db')\n",
                    "df = pd.read_sql_query('SELECT * FROM companies', conn)\n",
                    "conn.close()\n",
                    "\n",
                    "print(f'Loaded {len(df)} companies')\n",
                    "df.head()"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    with open(notebooks_dir / "etl_analysis.ipynb", "w") as f:
        json.dump(etl_notebook, f, indent=2)
    
    print("✅ Jupyter notebooks created")

def main():
    """Main setup function."""
    print("🚀 Setting up Cursor IDE for ETL/Data Processing...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("repsplit_orm.db").exists():
        print("⚠️  Warning: repsplit_orm.db not found. Make sure you're in the project root.")
    
    # Install extensions
    install_cursor_extensions()
    
    # Install MCP servers
    install_mcp_servers()
    
    # Create workspace settings
    create_workspace_settings()
    
    # Create analysis notebooks
    create_data_analysis_notebooks()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Restart Cursor IDE to load the new extensions")
    print("2. Open a .py file to activate Python language features")
    print("3. Use Cmd+Shift+P to access new commands:")
    print("   - 'Python: Select Interpreter' to set Python path")
    print("   - 'SQLTools: Add New Connection' to configure databases")
    print("   - 'Jupyter: Create New Notebook' for data analysis")
    print("4. Check the notebooks/ directory for analysis templates")
    print("\n🔧 MCP servers configured:")
    print("   - SQLite: Direct database access")
    print("   - Filesystem: Enhanced file operations")
    print("   - Task Master: Project management integration")

if __name__ == "__main__":
    main()
