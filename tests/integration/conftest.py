"""
Integration Tests Configuration - Shared Fixtures and Setup

This module provides shared fixtures and configuration for all
integration tests in the DocAnalyzer application.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import asyncio
import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

from docanalyzer.config import DocAnalyzerConfig
from docanalyzer.services import (
    LockManager,
    DirectoryScanner,
    VectorStoreWrapper,
    DatabaseManager,
    FileProcessor,
    ChunkingManager,
    DirectoryOrchestrator,
    ErrorHandler
)
from docanalyzer.filters.file_filter import FileFilter


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.
    
    This fixture ensures that all async tests use the same event loop
    and prevents issues with loop cleanup between tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_test_directory() -> Path:
    """
    Create a temporary directory for integration tests.
    
    This fixture provides a clean directory for each test and
    ensures proper cleanup after test completion.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="docanalyzer_integration_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def integration_config() -> DocAnalyzerConfig:
    """
    Create a configuration object for integration testing.
    
    This fixture provides a consistent configuration across all
    integration tests with appropriate settings for testing.
    """
    config = Mock(spec=DocAnalyzerConfig)
    
    # Basic configuration
    config.vector_store_url = "http://localhost:8000"
    config.embedding_service_url = "http://localhost:8001"
    config.database_url = "sqlite:///test_integration.db"
    
    # File processing settings
    config.max_file_size = 10 * 1024 * 1024  # 10MB
    config.supported_extensions = [".txt", ".md", ".py", ".js"]
    config.chunk_size = 1000
    config.chunk_overlap = 200
    
    # Concurrency settings
    config.max_concurrent_processes = 4
    config.max_concurrent_files = 8
    config.max_retry_attempts = 3
    config.retry_delay = 1.0
    
    # Performance settings
    config.batch_size = 10
    config.processing_timeout = 300  # 5 minutes
    
    # Logging settings
    config.log_level = "INFO"
    config.log_file = "logs/integration_tests.log"
    
    return config


@pytest.fixture
def mock_vector_store() -> VectorStoreWrapper:
    """
    Create a mock vector store wrapper for integration testing.
    
    This fixture provides a consistent mock implementation that
    simulates vector store behavior without requiring a real service.
    """
    mock_wrapper = Mock(spec=VectorStoreWrapper)
    
    # Health check
    mock_wrapper.health_check.return_value = {"status": "healthy", "version": "1.0.0"}
    
    # Chunk operations
    mock_wrapper.process_file_blocks.return_value = {
        "status": "success",
        "chunk_id": "test-chunk-uuid",
        "embedding_id": "test-embedding-uuid"
    }
    mock_wrapper.update_chunk.return_value = {"status": "success"}
    mock_wrapper.delete_chunk.return_value = {"status": "success"}
    
    # Search operations
    mock_wrapper.search_chunks.return_value = {
        "status": "success",
        "results": [],
        "total_count": 0
    }
    
    return mock_wrapper


@pytest.fixture
def mock_database_manager() -> DatabaseManager:
    """
    Create a mock database manager for integration testing.
    
    This fixture provides a consistent mock implementation that
    simulates database operations without requiring a real database.
    """
    mock_db = Mock(spec=DatabaseManager)
    
    # File record operations
    mock_db.create_file_record.return_value = Mock(
        file_id="test-file-uuid",
        file_path="/test/path",
        file_size=1024,
        last_modified=1234567890,
        status="processed"
    )
    mock_db.get_file_record.return_value = None  # File not found by default
    mock_db.update_file_record.return_value = True
    mock_db.delete_file_record.return_value = True
    
    # Statistics operations
    mock_db.get_processing_statistics.return_value = {
        "total_files": 0,
        "processed_files": 0,
        "failed_files": 0,
        "total_chunks": 0
    }
    
    return mock_db


@pytest.fixture
def integration_services(
    integration_config: DocAnalyzerConfig,
    mock_vector_store: VectorStoreWrapper,
    mock_database_manager: DatabaseManager
) -> Dict[str, Any]:
    """
    Create all service instances for integration testing.
    
    This fixture provides a complete set of service instances
    that can be used together to test the full pipeline.
    """
    services = {}
    
    # Create service instances
    services['lock_manager'] = LockManager()
    services['directory_scanner'] = DirectoryScanner(integration_config)
    services['file_processor'] = FileProcessor(integration_config, mock_vector_store)
    services['chunking_manager'] = ChunkingManager(integration_config, mock_vector_store)
    services['error_handler'] = ErrorHandler()
    
    # Create orchestrator
    services['orchestrator'] = DirectoryOrchestrator(
        config=integration_config,
        lock_manager=services['lock_manager'],
        directory_scanner=services['directory_scanner'],
        file_processor=services['file_processor'],
        chunking_manager=services['chunking_manager'],
        database_manager=mock_database_manager,
        error_handler=services['error_handler']
    )
    
    # Add mocks for verification
    services['mock_vector_store'] = mock_vector_store
    services['mock_database_manager'] = mock_database_manager
    
    return services


@pytest.fixture
def sample_files(temp_test_directory: Path) -> Dict[str, Path]:
    """
    Create sample files for integration testing.
    
    This fixture creates various types of test files that can be
    used across different integration test scenarios.
    """
    files = {}
    
    # Text file
    text_file = temp_test_directory / "sample.txt"
    text_content = """
    This is a sample text file for integration testing.
    
    It contains multiple paragraphs with various content types.
    
    The file should be processed correctly by the text processor.
    
    This paragraph contains technical information about
    the DocAnalyzer system and its capabilities.
    """
    text_file.write_text(text_content.strip())
    files['text'] = text_file
    
    # Markdown file
    md_file = temp_test_directory / "sample.md"
    md_content = """
    # Sample Markdown Document
    
    This is a **markdown** document for integration testing.
    
    ## Features
    
    - Text processing
    - Chunk generation
    - Vector storage
    
    ## Code Example
    
    ```python
    def process_file(file_path: str) -> List[Chunk]:
        return processor.process(file_path)
    ```
    
    ## Conclusion
    
    This document tests markdown processing capabilities.
    """
    md_file.write_text(md_content.strip())
    files['markdown'] = md_file
    
    # Python file
    py_file = temp_test_directory / "sample.py"
    py_content = '''
    """
    Sample Python file for integration testing.
    """
    
    import os
    from typing import List, Dict, Any
    
    
    class SampleProcessor:
        """Sample processor class for testing."""
        
        def __init__(self, config: Dict[str, Any]):
            self.config = config
            self.processed_files = 0
        
        def process_file(self, file_path: str) -> List[str]:
            """Process a single file and return chunks."""
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Simple chunking by lines
            chunks = content.split('\\n')
            self.processed_files += 1
            
            return chunks
        
        def get_statistics(self) -> Dict[str, Any]:
            """Get processing statistics."""
            return {
                "processed_files": self.processed_files,
                "status": "active"
            }
    
    
    def main():
        """Main function for testing."""
        processor = SampleProcessor({"chunk_size": 1000})
        result = processor.process_file("test.txt")
        print(f"Processed {len(result)} chunks")
    
    
    if __name__ == "__main__":
        main()
    '''
    py_file.write_text(py_content.strip())
    files['python'] = py_file
    
    # Large file for performance testing
    large_file = temp_test_directory / "large.txt"
    large_content = "Large file content " * 1000  # ~20KB
    large_file.write_text(large_content)
    files['large'] = large_file
    
    # Empty file
    empty_file = temp_test_directory / "empty.txt"
    empty_file.write_text("")
    files['empty'] = empty_file
    
    return files


@pytest.fixture
def test_directories(temp_test_directory: Path) -> Dict[str, Path]:
    """
    Create test directories for integration testing.
    
    This fixture creates various directory structures that can be
    used to test different processing scenarios.
    """
    directories = {}
    
    # Simple directory with few files
    simple_dir = temp_test_directory / "simple"
    simple_dir.mkdir()
    (simple_dir / "file1.txt").write_text("Simple file 1")
    (simple_dir / "file2.txt").write_text("Simple file 2")
    directories['simple'] = simple_dir
    
    # Nested directory structure
    nested_dir = temp_test_directory / "nested"
    nested_dir.mkdir()
    
    level1 = nested_dir / "level1"
    level1.mkdir()
    (level1 / "file1.txt").write_text("Nested file 1")
    
    level2 = level1 / "level2"
    level2.mkdir()
    (level2 / "file2.txt").write_text("Nested file 2")
    (level2 / "file3.md").write_text("# Nested Markdown")
    
    directories['nested'] = nested_dir
    
    # Directory with mixed file types
    mixed_dir = temp_test_directory / "mixed"
    mixed_dir.mkdir()
    (mixed_dir / "text.txt").write_text("Text file content")
    (mixed_dir / "markdown.md").write_text("# Markdown content")
    (mixed_dir / "python.py").write_text("# Python code")
    (mixed_dir / "ignored.log").write_text("Log file - should be ignored")
    directories['mixed'] = mixed_dir
    
    # Large directory for performance testing
    large_dir = temp_test_directory / "large"
    large_dir.mkdir()
    
    for i in range(20):
        subdir = large_dir / f"subdir_{i}"
        subdir.mkdir()
        
        for j in range(5):
            file_path = subdir / f"file_{i}_{j}.txt"
            content = f"Content for file {i}_{j} in large directory structure."
            file_path.write_text(content)
    
    directories['large'] = large_dir
    
    return directories


@pytest.fixture
def performance_metrics() -> Dict[str, Any]:
    """
    Create performance metrics tracking for integration tests.
    
    This fixture provides utilities for measuring and tracking
    performance metrics during integration testing.
    """
    import time
    import psutil
    import threading
    
    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.start_memory = None
            self.end_memory = None
            self.process = psutil.Process()
        
        def start(self):
            """Start performance tracking."""
            self.start_time = time.time()
            self.start_memory = self.process.memory_info().rss
        
        def stop(self):
            """Stop performance tracking."""
            self.end_time = time.time()
            self.end_memory = self.process.memory_info().rss
        
        def get_metrics(self) -> Dict[str, Any]:
            """Get performance metrics."""
            if not self.start_time or not self.end_time:
                return {}
            
            duration = self.end_time - self.start_time
            memory_used = self.end_memory - self.start_memory if self.start_memory else 0
            
            return {
                "duration": duration,
                "memory_used": memory_used,
                "memory_peak": self.process.memory_info().rss,
                "cpu_percent": self.process.cpu_percent(),
                "thread_count": self.process.num_threads()
            }
    
    return {"tracker": PerformanceTracker()} 