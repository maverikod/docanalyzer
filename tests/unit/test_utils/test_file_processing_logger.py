"""
Tests for File Processing Logger

Comprehensive test suite for file processing logging functionality.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
import logging

from docanalyzer.utils.file_processing_logger import FileProcessingLogger, file_processing_logger


class TestFileProcessingLogger:
    """Test suite for FileProcessingLogger class."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def logger_instance(self, temp_log_dir):
        """Create FileProcessingLogger instance with temp directory."""
        with patch('docanalyzer.utils.file_processing_logger.get_unified_config') as mock_config:
            # Create a mock config object
            mock_config_obj = MagicMock()
            mock_config_obj.logging.log_dir = temp_log_dir
            mock_config_obj.logging.file_processing_log = "test_file_processing.log"
            mock_config_obj.logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            mock_config_obj.logging.date_format = "%Y-%m-%d %H:%M:%S"
            mock_config.return_value = mock_config_obj
            
            # Clear any existing loggers to ensure fresh setup
            logging.getLogger("file_processing").handlers.clear()
            
            logger = FileProcessingLogger()
            yield logger
    
    def test_init(self, logger_instance):
        """Test logger initialization."""
        assert logger_instance.logger is not None
        assert logger_instance.logger.name == "file_processing"
        assert logger_instance.logger.level == 20  # INFO level
    
    def test_log_processing_start(self, logger_instance, temp_log_dir):
        """Test logging processing start."""
        file_path = "/test/path/file.txt"
        file_size = 1024
        file_type = "text"
        
        processing_id = logger_instance.log_processing_start(
            file_path=file_path,
            file_size=file_size,
            file_type=file_type
        )
        
        # Check that processing_id is generated
        assert processing_id.startswith("proc_")
        assert len(processing_id) > 10
        
        # Check log file was created
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Check log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "FILE_PROCESSING_START" in log_content
            assert file_path in log_content
            assert str(file_size) in log_content
            assert file_type in log_content
    
    def test_log_processing_end_success(self, logger_instance, temp_log_dir):
        """Test logging processing end with success."""
        processing_id = "test_proc_123"
        file_path = "/test/path/file.txt"
        success = True
        processing_time = 2.5
        chunks_created = 5
        
        logger_instance.log_processing_end(
            processing_id=processing_id,
            file_path=file_path,
            success=success,
            processing_time=processing_time,
            chunks_created=chunks_created
        )
        
        # Check log file was created
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Check log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "FILE_PROCESSING_END" in log_content
            assert processing_id in log_content
            assert file_path in log_content
            assert "true" in log_content.lower()  # success
            assert "2.5" in log_content  # processing_time
            assert "5" in log_content  # chunks_created
    
    def test_log_processing_end_failure(self, logger_instance, temp_log_dir):
        """Test logging processing end with failure."""
        processing_id = "test_proc_123"
        file_path = "/test/path/file.txt"
        success = False
        processing_time = 1.2
        error_message = "Test error message"
        
        logger_instance.log_processing_end(
            processing_id=processing_id,
            file_path=file_path,
            success=success,
            processing_time=processing_time,
            chunks_created=0,
            error_message=error_message
        )
        
        # Check log file was created
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Check log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "FILE_PROCESSING_END" in log_content
            assert processing_id in log_content
            assert file_path in log_content
            assert "false" in log_content.lower()  # success
            assert error_message in log_content
    
    def test_log_processing_error(self, logger_instance, temp_log_dir):
        """Test logging processing error."""
        processing_id = "test_proc_123"
        file_path = "/test/path/file.txt"
        error_type = "ValidationError"
        error_message = "Invalid file format"
        
        logger_instance.log_processing_error(
            processing_id=processing_id,
            file_path=file_path,
            error_type=error_type,
            error_message=error_message
        )
        
        # Check log file was created
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Check log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "FILE_PROCESSING_ERROR" in log_content
            assert processing_id in log_content
            assert file_path in log_content
            assert error_type in log_content
            assert error_message in log_content
    
    def test_log_processing_metrics(self, logger_instance, temp_log_dir):
        """Test logging processing metrics."""
        processing_id = "test_proc_123"
        file_path = "/test/path/file.txt"
        metrics = {
            "blocks_processed": 10,
            "chunks_created": 5,
            "processing_time": 2.5
        }
        
        logger_instance.log_processing_metrics(
            processing_id=processing_id,
            file_path=file_path,
            metrics=metrics
        )
        
        # Check log file was created
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Check log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "FILE_PROCESSING_METRICS" in log_content
            assert processing_id in log_content
            assert file_path in log_content
            assert "10" in log_content  # blocks_processed
            assert "5" in log_content   # chunks_created
    
    def test_log_batch_processing_start(self, logger_instance, temp_log_dir):
        """Test logging batch processing start."""
        batch_id = "test_batch_123"
        file_count = 5
        total_size = 10240
        
        logger_instance.log_batch_processing_start(
            batch_id=batch_id,
            file_count=file_count,
            total_size=total_size
        )
        
        # Check log file was created
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Check log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "BATCH_PROCESSING_START" in log_content
            assert batch_id in log_content
            assert str(file_count) in log_content
            assert str(total_size) in log_content
    
    def test_log_batch_processing_end(self, logger_instance, temp_log_dir):
        """Test logging batch processing end."""
        batch_id = "test_batch_123"
        processed_count = 5
        success_count = 4
        failed_count = 1
        total_processing_time = 10.5
        
        logger_instance.log_batch_processing_end(
            batch_id=batch_id,
            processed_count=processed_count,
            success_count=success_count,
            failed_count=failed_count,
            total_processing_time=total_processing_time
        )
        
        # Check log file was created
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Check log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "BATCH_PROCESSING_END" in log_content
            assert batch_id in log_content
            assert str(processed_count) in log_content
            assert str(success_count) in log_content
            assert str(failed_count) in log_content
            assert "10.5" in log_content  # total_processing_time
            assert "80.0" in log_content  # success_rate (4/5 * 100)
    
    def test_log_processing_end_with_additional_data(self, logger_instance, temp_log_dir):
        """Test logging processing end with additional data."""
        processing_id = "test_proc_123"
        file_path = "/test/path/file.txt"
        additional_data = {
            "custom_field": "custom_value",
            "nested": {"key": "value"}
        }
        
        logger_instance.log_processing_end(
            processing_id=processing_id,
            file_path=file_path,
            success=True,
            processing_time=1.0,
            chunks_created=3,
            additional_data=additional_data
        )
        
        # Check log file was created
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Check log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "FILE_PROCESSING_END" in log_content
            assert "custom_field" in log_content
            assert "custom_value" in log_content
    
    def test_log_processing_error_with_additional_data(self, logger_instance, temp_log_dir):
        """Test logging processing error with additional data."""
        processing_id = "test_proc_123"
        file_path = "/test/path/file.txt"
        additional_data = {
            "error_code": "E001",
            "retry_count": 3
        }
        
        logger_instance.log_processing_error(
            processing_id=processing_id,
            file_path=file_path,
            error_type="NetworkError",
            error_message="Connection timeout",
            additional_data=additional_data
        )
        
        # Check log file was created
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Check log content
        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "FILE_PROCESSING_ERROR" in log_content
            assert "error_code" in log_content
            assert "E001" in log_content
            assert "retry_count" in log_content
            assert "3" in log_content


class TestFileProcessingLoggerIntegration:
    """Integration tests for FileProcessingLogger."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def logger_instance(self, temp_log_dir):
        """Create FileProcessingLogger instance with temp directory."""
        with patch('docanalyzer.utils.file_processing_logger.get_unified_config') as mock_config:
            # Create a mock config object
            mock_config_obj = MagicMock()
            mock_config_obj.logging.log_dir = temp_log_dir
            mock_config_obj.logging.file_processing_log = "test_file_processing.log"
            mock_config_obj.logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            mock_config_obj.logging.date_format = "%Y-%m-%d %H:%M:%S"
            mock_config.return_value = mock_config_obj
            
            # Clear any existing loggers to ensure fresh setup
            logging.getLogger("file_processing").handlers.clear()
            
            logger = FileProcessingLogger()
            yield logger
    
    def test_complete_processing_workflow(self, logger_instance, temp_log_dir):
        """Test complete file processing workflow logging."""
        file_path = "/test/path/document.txt"
        file_size = 2048
        file_type = "text"
        
        # Start processing
        processing_id = logger_instance.log_processing_start(
            file_path=file_path,
            file_size=file_size,
            file_type=file_type
        )
        
        # Log metrics during processing
        logger_instance.log_processing_metrics(
            processing_id=processing_id,
            file_path=file_path,
            metrics={"blocks_extracted": 5, "processing_stage": "chunking"}
        )
        
        # End processing successfully
        logger_instance.log_processing_end(
            processing_id=processing_id,
            file_path=file_path,
            success=True,
            processing_time=3.2,
            chunks_created=8,
            additional_data={"blocks_processed": 5, "chunks_created": 8}
        )
        
        # Check log file
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Read and verify all log entries
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
        
        # Should have 4 log entries (1 initialization + 3 processing)
        assert len(log_lines) == 4
        
        # Check each entry
        start_line = log_lines[1]  # Skip initialization line
        metrics_line = log_lines[2]
        end_line = log_lines[3]
        
        assert "FILE_PROCESSING_START" in start_line
        assert "FILE_PROCESSING_METRICS" in metrics_line
        assert "FILE_PROCESSING_END" in end_line
        
        # Verify processing_id is consistent across all entries
        assert processing_id in start_line
        assert processing_id in metrics_line
        assert processing_id in end_line
    
    def test_error_processing_workflow(self, logger_instance, temp_log_dir):
        """Test file processing workflow with error."""
        file_path = "/test/path/document.txt"
        file_size = 1024
        file_type = "text"
        
        # Start processing
        processing_id = logger_instance.log_processing_start(
            file_path=file_path,
            file_size=file_size,
            file_type=file_type
        )
        
        # Log error
        logger_instance.log_processing_error(
            processing_id=processing_id,
            file_path=file_path,
            error_type="ValidationError",
            error_message="Invalid file format",
            additional_data={"error_code": "E001"}
        )
        
        # End processing with failure
        logger_instance.log_processing_end(
            processing_id=processing_id,
            file_path=file_path,
            success=False,
            processing_time=1.5,
            chunks_created=0,
            error_message="Invalid file format"
        )
        
        # Check log file
        log_file = Path(temp_log_dir) / "test_file_processing.log"
        assert log_file.exists()
        
        # Read and verify log entries
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
        
        # Should have 4 log entries (1 initialization + 3 processing)
        assert len(log_lines) == 4
        
        # Check each entry
        start_line = log_lines[1]  # Skip initialization line
        error_line = log_lines[2]
        end_line = log_lines[3]
        
        assert "FILE_PROCESSING_START" in start_line
        assert "FILE_PROCESSING_ERROR" in error_line
        assert "FILE_PROCESSING_END" in end_line
        
        # Verify error information
        assert "ValidationError" in error_line
        assert "Invalid file format" in error_line
        assert "E001" in error_line


class TestGlobalFileProcessingLogger:
    """Test suite for global file_processing_logger instance."""
    
    def test_global_instance_exists(self):
        """Test that global file_processing_logger instance exists."""
        assert file_processing_logger is not None
        assert isinstance(file_processing_logger, FileProcessingLogger)
    
    def test_global_instance_methods(self):
        """Test that global instance has all required methods."""
        required_methods = [
            'log_processing_start',
            'log_processing_end',
            'log_processing_error',
            'log_processing_metrics',
            'log_batch_processing_start',
            'log_batch_processing_end'
        ]
        
        for method_name in required_methods:
            assert hasattr(file_processing_logger, method_name)
            assert callable(getattr(file_processing_logger, method_name)) 