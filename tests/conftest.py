"""
Pytest configuration and shared fixtures
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths"""
    for item in items:
        # Add markers based on file paths
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark slow tests
        if (
            "test_etl_with_very_large_dataset" in item.name
            or "test_etl_memory_efficiency" in item.name
        ):
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory"""
    return os.path.join(os.path.dirname(__file__), "..")


@pytest.fixture(scope="session")
def test_data_dir():
    """Get the test data directory"""
    return os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_logging():
    """Mock logging to prevent file creation during tests"""
    import logging
    from unittest.mock import MagicMock, patch

    with patch("logging.FileHandler") as mock_file_handler, patch(
        "logging.basicConfig"
    ) as mock_basic_config, patch("os.makedirs") as mock_makedirs:
        yield {
            "file_handler": mock_file_handler,
            "basic_config": mock_basic_config,
            "makedirs": mock_makedirs,
        }
