"""
Performance tests for ETL system
Tests ETL performance, memory usage, and scalability
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import psutil
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Mock logging setup before importing ETL module
with patch("logging.FileHandler") as mock_file_handler, patch(
    "logging.basicConfig"
) as mock_basic_config, patch("os.makedirs") as mock_makedirs:
    from src.etl.etl_data_ingestion import DataETL


class TestETLPerformance:
    """Test ETL performance characteristics"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for performance testing"""
        workspace = tempfile.mkdtemp()

        # Create directory structure
        os.makedirs(os.path.join(workspace, "data", "slack"))
        os.makedirs(os.path.join(workspace, "data", "telegram"))
        os.makedirs(os.path.join(workspace, "output", "notebooklm"))
        os.makedirs(os.path.join(workspace, "logs"))

        yield workspace
        shutil.rmtree(workspace)

    @pytest.fixture
    def large_company_mapping(self, temp_workspace):
        """Create large company mapping file for performance testing"""
        mapping_file = os.path.join(temp_workspace, "data", "company_mapping.csv")

        # Generate 1000 companies for performance testing
        companies = []
        for i in range(1000):
            company_name = f"test-company-{i:04d}"
            companies.append(
                f"{company_name},{company_name}::1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2,{company_name}-channel,{company_name},{company_name}.com,base,{company_name}"
            )

        mapping_content = (
            "Company Name,Full Node Address,Slack Groups,Telegram Groups,Calendar Search Domain,Variants,Base Company\n"
            + "\n".join(companies)
        )

        with open(mapping_file, "w") as f:
            f.write(mapping_content)

        return mapping_file

    @pytest.fixture
    def large_slack_database(self, temp_workspace):
        """Create large Slack database for performance testing"""
        db_path = os.path.join(temp_workspace, "data", "slack", "repsplit.db")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute(
            """
            CREATE TABLE conversations (
                id INTEGER PRIMARY KEY,
                name TEXT,
                type TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                conversation_id INTEGER,
                author TEXT,
                text TEXT,
                timestamp REAL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                real_name TEXT,
                display_name TEXT
            )
        """
        )

        # Insert large dataset
        # 100 conversations
        for i in range(100):
            cursor.execute(
                f"INSERT INTO conversations (id, name, type) VALUES ({i+1}, 'test-company-{i:04d}-channel', 'channel')"
            )

        # 10 users
        for i in range(10):
            cursor.execute(
                f"INSERT INTO users (id, real_name, display_name) VALUES ('U{i:03d}', 'User{i:03d}', 'User{i:03d}')"
            )

        # 1000 messages (10 per conversation)
        message_id = 1
        for conv_id in range(1, 101):
            for msg_num in range(10):
                cursor.execute(
                    f"INSERT INTO messages (id, conversation_id, author, text, timestamp) VALUES ({message_id}, {conv_id}, 'U{msg_num % 10:03d}', 'Test message {msg_num} in conversation {conv_id}', {1640995200 + message_id})"
                )
                message_id += 1

        conn.commit()
        conn.close()

        return db_path

    @pytest.fixture
    def large_telegram_data(self, temp_workspace):
        """Create large Telegram dataset for performance testing"""
        telegram_dir = os.path.join(temp_workspace, "data", "telegram")

        # Create 100 chat directories
        for i in range(100):
            chat_dir = os.path.join(telegram_dir, f"chat_{i:04d}")
            os.makedirs(chat_dir)

            # Create HTML file with 10 messages
            html_content = "<html><body>"
            for msg_num in range(10):
                html_content += f"""
                <div class="message">
                    <div class="message_header">
                        <span class="from_name">User{msg_num % 10:03d}</span>
                        <span class="date">2022-01-01 12:{msg_num:02d}:00</span>
                    </div>
                    <div class="text">Test message {msg_num} in chat {i:04d}</div>
                </div>
                """
            html_content += "</body></html>"

            with open(os.path.join(chat_dir, "messages.html"), "w") as f:
                f.write(html_content)

        return telegram_dir

    def test_etl_quick_mode_performance(
        self,
        temp_workspace,
        large_company_mapping,
        large_slack_database,
        large_telegram_data,
    ):
        """Test ETL quick mode performance with large dataset"""
        # Create ETL instance in quick mode
        etl = DataETL(max_workers=4, batch_size=50, quick_mode=True)

        # Set paths
        etl.company_mapping_file = large_company_mapping
        etl.slack_db_path = large_slack_database
        etl.telegram_chats_dir = large_telegram_data
        etl.output_file = os.path.join(
            temp_workspace, "output", "notebooklm", "etl_output_quick.txt"
        )
        etl.archive_dir = os.path.join(
            temp_workspace, "output", "notebooklm", "archive"
        )
        etl.logs_dir = os.path.join(temp_workspace, "logs")

        # Ensure output directories exist
        os.makedirs(os.path.dirname(etl.output_file), exist_ok=True)
        os.makedirs(etl.archive_dir, exist_ok=True)
        os.makedirs(etl.logs_dir, exist_ok=True)

        # Measure performance
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Run ETL
        etl.run_etl()

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Calculate metrics
        duration = end_time - start_time
        memory_used = end_memory - start_memory

        # Verify performance requirements
        assert duration < 30.0, f"Quick mode took {duration:.2f}s, should be < 30s"
        assert (
            memory_used < 500
        ), f"Memory usage was {memory_used:.2f}MB, should be < 500MB"

        # Verify output was created
        assert os.path.exists(etl.output_file)

        # Verify output size is reasonable
        output_size = os.path.getsize(etl.output_file)
        assert output_size > 0, "Output file should not be empty"
        assert (
            output_size < 100 * 1024 * 1024
        ), f"Output file too large: {output_size / 1024 / 1024:.2f}MB"

    def test_etl_full_mode_performance(
        self,
        temp_workspace,
        large_company_mapping,
        large_slack_database,
        large_telegram_data,
    ):
        """Test ETL full mode performance with large dataset"""
        # Create ETL instance in full mode
        etl = DataETL(max_workers=4, batch_size=50, quick_mode=False)

        # Set paths
        etl.company_mapping_file = large_company_mapping
        etl.slack_db_path = large_slack_database
        etl.telegram_chats_dir = large_telegram_data
        etl.output_file = os.path.join(
            temp_workspace, "output", "notebooklm", "etl_output_full.txt"
        )
        etl.archive_dir = os.path.join(
            temp_workspace, "output", "notebooklm", "archive"
        )
        etl.logs_dir = os.path.join(temp_workspace, "logs")

        # Ensure output directories exist
        os.makedirs(os.path.dirname(etl.output_file), exist_ok=True)
        os.makedirs(etl.archive_dir, exist_ok=True)
        os.makedirs(etl.logs_dir, exist_ok=True)

        # Measure performance
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Run ETL
        etl.run_etl()

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Calculate metrics
        duration = end_time - start_time
        memory_used = end_memory - start_memory

        # Verify performance requirements
        assert duration < 120.0, f"Full mode took {duration:.2f}s, should be < 120s"
        assert (
            memory_used < 1000
        ), f"Memory usage was {memory_used:.2f}MB, should be < 1000MB"

        # Verify output was created
        assert os.path.exists(etl.output_file)

        # Verify output size is reasonable
        output_size = os.path.getsize(etl.output_file)
        assert output_size > 0, "Output file should not be empty"

    def test_etl_memory_usage(
        self,
        temp_workspace,
        large_company_mapping,
        large_slack_database,
        large_telegram_data,
    ):
        """Test ETL memory usage patterns"""
        # Create ETL instance
        etl = DataETL(max_workers=2, batch_size=25, quick_mode=True)

        # Set paths
        etl.company_mapping_file = large_company_mapping
        etl.slack_db_path = large_slack_database
        etl.telegram_chats_dir = large_telegram_data
        etl.output_file = os.path.join(
            temp_workspace, "output", "notebooklm", "etl_output_memory.txt"
        )
        etl.archive_dir = os.path.join(
            temp_workspace, "output", "notebooklm", "archive"
        )
        etl.logs_dir = os.path.join(temp_workspace, "logs")

        # Ensure output directories exist
        os.makedirs(os.path.dirname(etl.output_file), exist_ok=True)
        os.makedirs(etl.archive_dir, exist_ok=True)
        os.makedirs(etl.logs_dir, exist_ok=True)

        # Monitor memory usage during ETL
        memory_samples = []

        def monitor_memory():
            while True:
                memory_samples.append(psutil.Process().memory_info().rss / 1024 / 1024)
                time.sleep(0.1)

        # Start memory monitoring
        monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        monitor_thread.start()

        # Run ETL
        etl.run_etl()

        # Stop monitoring
        time.sleep(0.5)  # Let final sample be taken

        # Analyze memory usage
        max_memory = max(memory_samples)
        avg_memory = sum(memory_samples) / len(memory_samples)

        # Verify memory usage is reasonable
        assert (
            max_memory < 500
        ), f"Peak memory usage was {max_memory:.2f}MB, should be < 500MB"
        assert (
            avg_memory < 300
        ), f"Average memory usage was {avg_memory:.2f}MB, should be < 300MB"

    def test_etl_concurrent_workers(
        self, temp_workspace, large_company_mapping, large_telegram_data
    ):
        """Test ETL with different worker configurations"""
        worker_configs = [1, 2, 4, 8]
        results = {}

        for workers in worker_configs:
            # Create ETL instance
            etl = DataETL(max_workers=workers, batch_size=25, quick_mode=True)

            # Set paths
            etl.company_mapping_file = large_company_mapping
            etl.telegram_chats_dir = large_telegram_data
            etl.output_file = os.path.join(
                temp_workspace, f"output_workers_{workers}.txt"
            )
            etl.archive_dir = os.path.join(temp_workspace, "archive")
            etl.logs_dir = os.path.join(temp_workspace, "logs")

            # Ensure output directories exist
            os.makedirs(os.path.dirname(etl.output_file), exist_ok=True)
            os.makedirs(etl.archive_dir, exist_ok=True)
            os.makedirs(etl.logs_dir, exist_ok=True)

            # Measure performance
            start_time = time.time()
            etl.run_etl()
            duration = time.time() - start_time

            results[workers] = duration

            # Verify output was created
            assert os.path.exists(etl.output_file)

        # Verify that more workers generally improve performance (up to a point)
        # With very small datasets, performance differences may be minimal
        assert (
            results[2] <= results[1] * 1.5
        ), "2 workers should be reasonably faster than 1 worker"
        assert (
            results[4] <= results[2] * 1.2
        ), "4 workers should be faster than 2 workers"

    def test_etl_batch_size_impact(
        self, temp_workspace, large_company_mapping, large_telegram_data
    ):
        """Test ETL with different batch sizes"""
        batch_sizes = [10, 25, 50, 100]
        results = {}

        for batch_size in batch_sizes:
            # Create ETL instance
            etl = DataETL(max_workers=2, batch_size=batch_size, quick_mode=True)

            # Set paths
            etl.company_mapping_file = large_company_mapping
            etl.telegram_chats_dir = large_telegram_data
            etl.output_file = os.path.join(
                temp_workspace, f"output_batch_{batch_size}.txt"
            )
            etl.archive_dir = os.path.join(temp_workspace, "archive")
            etl.logs_dir = os.path.join(temp_workspace, "logs")

            # Ensure output directories exist
            os.makedirs(os.path.dirname(etl.output_file), exist_ok=True)
            os.makedirs(etl.archive_dir, exist_ok=True)
            os.makedirs(etl.logs_dir, exist_ok=True)

            # Measure performance
            start_time = time.time()
            etl.run_etl()
            duration = time.time() - start_time

            results[batch_size] = duration

            # Verify output was created
            assert os.path.exists(etl.output_file)

        # Verify that different batch sizes produce valid results
        for batch_size, duration in results.items():
            assert (
                duration > 0
            ), f"Batch size {batch_size} should complete in reasonable time"
            assert (
                duration < 60
            ), f"Batch size {batch_size} took {duration:.2f}s, should be < 60s"


class TestETLScalability:
    """Test ETL scalability with very large datasets"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        workspace = tempfile.mkdtemp()

        # Create directory structure
        os.makedirs(os.path.join(workspace, "data", "slack"))
        os.makedirs(os.path.join(workspace, "data", "telegram"))
        os.makedirs(os.path.join(workspace, "output", "notebooklm"))
        os.makedirs(os.path.join(workspace, "logs"))

        yield workspace
        shutil.rmtree(workspace)

    @pytest.mark.slow
    def test_etl_with_very_large_dataset(self, temp_workspace):
        """Test ETL with very large dataset (marked as slow)"""
        # This test would use a much larger dataset
        # and verify that ETL can handle it without running out of memory
        pass

    @pytest.mark.slow
    def test_etl_memory_efficiency(self, temp_workspace):
        """Test ETL memory efficiency with large datasets (marked as slow)"""
        # This test would verify that ETL doesn't consume excessive memory
        # even with very large datasets
        pass


if __name__ == "__main__":
    pytest.main([__file__])
