"""
Tests for Database Models

Comprehensive test suite for database models including DatabaseFileRecord
and ProcessingStatistics classes.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from docanalyzer.models.database import (
    RecordStatus, DatabaseFileRecord, ProcessingStatistics
)


class TestRecordStatus:
    """Test suite for RecordStatus enum."""
    
    def test_record_status_values(self):
        """Test that RecordStatus has expected values."""
        assert RecordStatus.NEW.value == "new"
        assert RecordStatus.PROCESSING.value == "processing"
        assert RecordStatus.COMPLETED.value == "completed"
        assert RecordStatus.FAILED.value == "failed"
        assert RecordStatus.DELETED.value == "deleted"
        assert RecordStatus.ARCHIVED.value == "archived"


class TestDatabaseFileRecord:
    """Test suite for DatabaseFileRecord class."""
    
    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def file_record(self, temp_file):
        """Create DatabaseFileRecord instance for testing."""
        stat = os.stat(temp_file)
        return DatabaseFileRecord(
            file_path=temp_file,
            file_size_bytes=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime)
        )
    
    def test_database_file_record_creation_success(self, temp_file):
        """Test successful DatabaseFileRecord creation."""
        # Arrange
        stat = os.stat(temp_file)
        
        # Act
        record = DatabaseFileRecord(
            file_path=temp_file,
            file_size_bytes=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime)
        )
        
        # Assert
        assert record.file_path == temp_file
        assert record.file_size_bytes == stat.st_size
        assert record.status == RecordStatus.NEW
        assert record.processing_count == 0
        assert record.chunk_count == 0
        assert record.processing_errors == []
        assert record.metadata == {}
    
    def test_database_file_record_creation_with_optional_params(self, temp_file):
        """Test DatabaseFileRecord creation with optional parameters."""
        # Arrange
        stat = os.stat(temp_file)
        last_processed = datetime.now()
        metadata = {"category": "test", "priority": "high"}
        
        # Act
        record = DatabaseFileRecord(
            file_path=temp_file,
            file_size_bytes=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime),
            status=RecordStatus.COMPLETED,
            processing_count=5,
            last_processed_at=last_processed,
            metadata=metadata,
            vector_store_id="vector_123",
            chunk_count=10
        )
        
        # Assert
        assert record.status == RecordStatus.COMPLETED
        assert record.processing_count == 5
        assert record.last_processed_at == last_processed
        assert record.metadata == metadata
        assert record.vector_store_id == "vector_123"
        assert record.chunk_count == 10
    
    def test_database_file_record_creation_empty_path(self):
        """Test DatabaseFileRecord creation with empty file path."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_path must be non-empty string"):
            DatabaseFileRecord("", 1024, datetime.now())
    
    def test_database_file_record_creation_negative_size(self, temp_file):
        """Test DatabaseFileRecord creation with negative file size."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_size_bytes must be non-negative integer"):
            DatabaseFileRecord(temp_file, -1024, datetime.now())
    
    def test_database_file_record_creation_invalid_modification_time(self, temp_file):
        """Test DatabaseFileRecord creation with invalid modification time."""
        # Act & Assert
        with pytest.raises(TypeError, match="modification_time must be datetime object"):
            DatabaseFileRecord(temp_file, 1024, "invalid_time")
    
    def test_database_file_record_creation_nonexistent_file(self):
        """Test DatabaseFileRecord creation with non-existent file."""
        # Act - should not raise FileNotFoundError as we don't validate file existence
        record = DatabaseFileRecord("/nonexistent/file.txt", 1024, datetime.now())
        
        # Assert
        assert record.file_path == "/nonexistent/file.txt"
        assert record.file_size_bytes == 1024
    
    def test_file_name_property(self, file_record):
        """Test file_name property."""
        # Act
        file_name = file_record.file_name
        
        # Assert
        assert file_name.endswith(".txt")
        assert len(file_name) > 0
    
    def test_file_extension_property(self, file_record):
        """Test file_extension property."""
        # Act
        extension = file_record.file_extension
        
        # Assert
        assert extension == "txt"
    
    def test_mark_processing_started(self, file_record):
        """Test mark_processing_started method."""
        # Act
        file_record.mark_processing_started()
        
        # Assert
        assert file_record.status == RecordStatus.PROCESSING
        assert file_record.processing_count == 1
    
    def test_mark_processing_completed(self, file_record):
        """Test mark_processing_completed method."""
        # Act
        file_record.mark_processing_completed("vector_123", 5)
        
        # Assert
        assert file_record.status == RecordStatus.COMPLETED
        assert file_record.vector_store_id == "vector_123"
        assert file_record.chunk_count == 5
    
    def test_mark_processing_completed_without_params(self, file_record):
        """Test mark_processing_completed method without optional parameters."""
        # Act
        file_record.mark_processing_completed()
        
        # Assert
        assert file_record.status == RecordStatus.COMPLETED
        assert file_record.vector_store_id is None
        assert file_record.chunk_count == 0
    
    def test_mark_processing_completed_negative_chunk_count(self, file_record):
        """Test mark_processing_completed with negative chunk count."""
        # Act & Assert
        with pytest.raises(ValueError, match="chunk_count must be non-negative integer"):
            file_record.mark_processing_completed(chunk_count=-1)
    
    def test_mark_processing_failed(self, file_record):
        """Test mark_processing_failed method."""
        # Act
        file_record.mark_processing_failed("File format not supported")
        
        # Assert
        assert file_record.status == RecordStatus.FAILED
        assert "File format not supported" in file_record.processing_errors
    
    def test_mark_processing_failed_empty_message(self, file_record):
        """Test mark_processing_failed with empty error message."""
        # Act & Assert
        with pytest.raises(ValueError, match="error_message must be non-empty string"):
            file_record.mark_processing_failed("")
    
    def test_mark_processing_failed_invalid_type(self, file_record):
        """Test mark_processing_failed with invalid error message type."""
        # Act & Assert
        with pytest.raises(TypeError, match="error_message must be string"):
            file_record.mark_processing_failed(123)
    
    def test_add_processing_error(self, file_record):
        """Test add_processing_error method."""
        # Act
        file_record.add_processing_error("Permission denied")
        
        # Assert
        assert len(file_record.processing_errors) == 1
        assert file_record.processing_errors[0] == "Permission denied"
    
    def test_add_processing_error_empty_message(self, file_record):
        """Test add_processing_error with empty error message."""
        # Act & Assert
        with pytest.raises(ValueError, match="error_message must be non-empty string"):
            file_record.add_processing_error("")
    
    def test_add_processing_error_invalid_type(self, file_record):
        """Test add_processing_error with invalid error message type."""
        # Act & Assert
        with pytest.raises(TypeError, match="error_message must be string"):
            file_record.add_processing_error(123)
    
    def test_update_metadata(self, file_record):
        """Test update_metadata method."""
        # Arrange
        new_metadata = {"category": "documentation", "priority": "high"}
        
        # Act
        file_record.update_metadata(new_metadata)
        
        # Assert
        assert file_record.metadata == new_metadata
    
    def test_update_metadata_invalid_type(self, file_record):
        """Test update_metadata with invalid type."""
        # Act & Assert
        with pytest.raises(TypeError, match="new_metadata must be dictionary"):
            file_record.update_metadata("not a dict")
    
    def test_to_dict(self, file_record):
        """Test to_dict method."""
        # Act
        data = file_record.to_dict()
        
        # Assert
        assert data["file_path"] == file_record.file_path
        assert data["file_size_bytes"] == file_record.file_size_bytes
        assert data["status"] == file_record.status.value
        assert data["processing_count"] == file_record.processing_count
        assert data["chunk_count"] == file_record.chunk_count
        assert "modification_time" in data
        assert data["last_processed_at"] is None
        assert data["processing_errors"] == []
        assert data["metadata"] == {}
    
    def test_to_dict_with_optional_fields(self, temp_file):
        """Test to_dict method with optional fields."""
        # Arrange
        stat = os.stat(temp_file)
        last_processed = datetime.now()
        metadata = {"test": "value"}
        
        record = DatabaseFileRecord(
            file_path=temp_file,
            file_size_bytes=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime),
            last_processed_at=last_processed,
            metadata=metadata,
            vector_store_id="vector_123",
            chunk_count=5
        )
        
        # Act
        data = record.to_dict()
        
        # Assert
        assert data["last_processed_at"] is not None
        assert data["metadata"] == metadata
        assert data["vector_store_id"] == "vector_123"
        assert data["chunk_count"] == 5
    
    def test_from_dict(self, file_record):
        """Test from_dict method."""
        # Arrange
        data = file_record.to_dict()
        
        # Act
        new_record = DatabaseFileRecord.from_dict(data)
        
        # Assert
        assert new_record.file_path == file_record.file_path
        assert new_record.file_size_bytes == file_record.file_size_bytes
        assert new_record.status == file_record.status
    
    def test_from_dict_missing_required_fields(self):
        """Test from_dict method with missing required fields."""
        # Arrange
        data = {"file_path": "/test/file.txt"}  # Missing file_size_bytes and modification_time
        
        # Act & Assert
        with pytest.raises(ValueError, match="Required field 'file_size_bytes' missing in data"):
            DatabaseFileRecord.from_dict(data)
    
    def test_equality(self, file_record):
        """Test equality comparison."""
        # Arrange
        same_record = DatabaseFileRecord(
            file_path=file_record.file_path,
            file_size_bytes=file_record.file_size_bytes,
            modification_time=file_record.modification_time
        )
        
        # Act & Assert
        assert file_record == same_record
    
    def test_inequality(self, file_record):
        """Test inequality comparison."""
        # Arrange - create a different record with same size but different path
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Different content")
            different_path = f.name
        
        try:
            stat = os.stat(different_path)
            different_record = DatabaseFileRecord(
                file_path=different_path,
                file_size_bytes=stat.st_size,
                modification_time=datetime.fromtimestamp(stat.st_mtime)
            )
            
            # Act & Assert
            assert file_record != different_record
        finally:
            if os.path.exists(different_path):
                os.unlink(different_path)
    
    def test_equality_different_type(self, file_record):
        """Test equality with different type."""
        # Act & Assert
        assert file_record != "not a DatabaseFileRecord"
    
    def test_repr(self, file_record):
        """Test string representation."""
        # Act
        repr_str = repr(file_record)
        
        # Assert
        assert "DatabaseFileRecord" in repr_str
        assert file_record.file_path in repr_str
        assert str(file_record.file_size_bytes) in repr_str
        assert file_record.status.value in repr_str


class TestProcessingStatistics:
    """Test suite for ProcessingStatistics class."""
    
    @pytest.fixture
    def statistics(self):
        """Create ProcessingStatistics instance for testing."""
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        return ProcessingStatistics(
            period_start=period_start,
            period_end=period_end,
            total_files_processed=100,
            total_files_successful=95
        )
    
    def test_processing_statistics_creation_success(self):
        """Test successful ProcessingStatistics creation."""
        # Arrange
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        
        # Act
        stats = ProcessingStatistics(
            period_start=period_start,
            period_end=period_end,
            total_files_processed=100,
            total_files_successful=95
        )
        
        # Assert
        assert stats.period_start == period_start
        assert stats.period_end == period_end
        assert stats.total_files_processed == 100
        assert stats.total_files_successful == 95
        assert stats.total_files_failed == 0
        assert stats.total_files_skipped == 0
        assert stats.total_processing_time_seconds == 0.0
        assert stats.total_chunks_created == 0
        assert stats.total_characters_processed == 0
        assert stats.file_type_breakdown == {}
        assert stats.error_breakdown == {}
        assert stats.processing_metadata == {}
    
    def test_processing_statistics_creation_with_optional_params(self):
        """Test ProcessingStatistics creation with optional parameters."""
        # Arrange
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        metadata = {"config": "test", "version": "1.0"}
        
        # Act
        stats = ProcessingStatistics(
            period_start=period_start,
            period_end=period_end,
            total_files_processed=100,
            total_files_successful=90,
            total_files_failed=5,
            total_files_skipped=5,
            total_processing_time_seconds=500.0,
            total_chunks_created=1000,
            total_characters_processed=50000,
            processing_metadata=metadata
        )
        
        # Assert
        assert stats.total_files_failed == 5
        assert stats.total_files_skipped == 5
        assert stats.total_processing_time_seconds == 500.0
        assert stats.total_chunks_created == 1000
        assert stats.total_characters_processed == 50000
        assert stats.processing_metadata == metadata
    
    def test_processing_statistics_creation_invalid_period(self):
        """Test ProcessingStatistics creation with invalid period."""
        # Arrange
        period_start = datetime.now()
        period_end = datetime.now() - timedelta(hours=1)  # End before start
        
        # Act & Assert
        with pytest.raises(ValueError, match="period_end must be >= period_start"):
            ProcessingStatistics(
                period_start=period_start,
                period_end=period_end,
                total_files_processed=100,
                total_files_successful=95
            )
    
    def test_processing_statistics_creation_negative_counts(self):
        """Test ProcessingStatistics creation with negative counts."""
        # Arrange
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_files_processed must be non-negative integer"):
            ProcessingStatistics(
                period_start=period_start,
                period_end=period_end,
                total_files_processed=-1,
                total_files_successful=95
            )
    
    def test_processing_statistics_creation_invalid_successful_count(self):
        """Test ProcessingStatistics creation with invalid successful count."""
        # Arrange
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_files_successful cannot exceed total_files_processed"):
            ProcessingStatistics(
                period_start=period_start,
                period_end=period_end,
                total_files_processed=100,
                total_files_successful=150  # More successful than processed
            )
    
    def test_processing_statistics_creation_invalid_datetime(self):
        """Test ProcessingStatistics creation with invalid datetime."""
        # Act & Assert
        with pytest.raises(TypeError, match="period_start must be datetime object"):
            ProcessingStatistics(
                period_start="invalid_time",
                period_end=datetime.now(),
                total_files_processed=100,
                total_files_successful=95
            )
    
    def test_success_rate(self, statistics):
        """Test success_rate property."""
        # Act
        success_rate = statistics.success_rate
        
        # Assert
        assert success_rate == 0.95  # 95/100
    
    def test_success_rate_no_files(self):
        """Test success_rate when no files processed."""
        # Arrange
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        stats = ProcessingStatistics(
            period_start=period_start,
            period_end=period_end,
            total_files_processed=0,
            total_files_successful=0
        )
        
        # Act
        success_rate = stats.success_rate
        
        # Assert
        assert success_rate == 0.0
    
    def test_failure_rate(self, statistics):
        """Test failure_rate property."""
        # Act
        failure_rate = statistics.failure_rate
        
        # Assert
        assert failure_rate == 0.0  # No failed files
    
    def test_failure_rate_with_failures(self):
        """Test failure_rate with failed files."""
        # Arrange
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        stats = ProcessingStatistics(
            period_start=period_start,
            period_end=period_end,
            total_files_processed=100,
            total_files_successful=90,
            total_files_failed=5
        )
        
        # Act
        failure_rate = stats.failure_rate
        
        # Assert
        assert failure_rate == 0.05  # 5/100
    
    def test_average_processing_time_seconds(self, statistics):
        """Test average_processing_time_seconds property."""
        # Arrange
        statistics.total_processing_time_seconds = 500.0
        
        # Act
        avg_time = statistics.average_processing_time_seconds
        
        # Assert
        assert avg_time == 5.0  # 500/100
    
    def test_average_processing_time_seconds_no_files(self):
        """Test average_processing_time_seconds when no files processed."""
        # Arrange
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        stats = ProcessingStatistics(
            period_start=period_start,
            period_end=period_end,
            total_files_processed=0,
            total_files_successful=0
        )
        
        # Act
        avg_time = stats.average_processing_time_seconds
        
        # Assert
        assert avg_time == 0.0
    
    def test_period_duration_seconds(self, statistics):
        """Test period_duration_seconds property."""
        # Act
        duration = statistics.period_duration_seconds
        
        # Assert
        assert duration > 0
        assert isinstance(duration, float)
    
    def test_add_file_type_count(self, statistics):
        """Test add_file_type_count method."""
        # Act
        statistics.add_file_type_count("txt", 50)
        
        # Assert
        assert statistics.file_type_breakdown["txt"] == 50
    
    def test_add_file_type_count_multiple(self, statistics):
        """Test add_file_type_count method multiple times."""
        # Act
        statistics.add_file_type_count("txt", 30)
        statistics.add_file_type_count("txt", 20)
        
        # Assert
        assert statistics.file_type_breakdown["txt"] == 50
    
    def test_add_file_type_count_empty_extension(self, statistics):
        """Test add_file_type_count with empty extension."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_extension must be non-empty string"):
            statistics.add_file_type_count("", 50)
    
    def test_add_file_type_count_negative_count(self, statistics):
        """Test add_file_type_count with negative count."""
        # Act & Assert
        with pytest.raises(ValueError, match="count must be positive integer"):
            statistics.add_file_type_count("txt", -1)
    
    def test_add_file_type_count_invalid_type(self, statistics):
        """Test add_file_type_count with invalid count type."""
        # Act & Assert
        with pytest.raises(TypeError, match="count must be integer"):
            statistics.add_file_type_count("txt", "not an int")
    
    def test_add_error_count(self, statistics):
        """Test add_error_count method."""
        # Act
        statistics.add_error_count("FileNotFoundError", 3)
        
        # Assert
        assert statistics.error_breakdown["FileNotFoundError"] == 3
    
    def test_add_error_count_multiple(self, statistics):
        """Test add_error_count method multiple times."""
        # Act
        statistics.add_error_count("FileNotFoundError", 2)
        statistics.add_error_count("FileNotFoundError", 1)
        
        # Assert
        assert statistics.error_breakdown["FileNotFoundError"] == 3
    
    def test_add_error_count_empty_type(self, statistics):
        """Test add_error_count with empty error type."""
        # Act & Assert
        with pytest.raises(ValueError, match="error_type must be non-empty string"):
            statistics.add_error_count("", 3)
    
    def test_add_error_count_negative_count(self, statistics):
        """Test add_error_count with negative count."""
        # Act & Assert
        with pytest.raises(ValueError, match="count must be positive integer"):
            statistics.add_error_count("FileNotFoundError", -1)
    
    def test_add_error_count_invalid_type(self, statistics):
        """Test add_error_count with invalid count type."""
        # Act & Assert
        with pytest.raises(TypeError, match="count must be integer"):
            statistics.add_error_count("FileNotFoundError", "not an int")
    
    def test_to_dict(self, statistics):
        """Test to_dict method."""
        # Act
        data = statistics.to_dict()
        
        # Assert
        assert data["total_files_processed"] == 100
        assert data["total_files_successful"] == 95
        assert data["success_rate"] == 0.95
        assert data["failure_rate"] == 0.0
        assert data["average_processing_time_seconds"] == 0.0
        assert "period_start" in data
        assert "period_end" in data
        assert data["file_type_breakdown"] == {}
        assert data["error_breakdown"] == {}
    
    def test_from_dict(self, statistics):
        """Test from_dict method."""
        # Arrange
        data = statistics.to_dict()
        
        # Act
        new_stats = ProcessingStatistics.from_dict(data)
        
        # Assert
        assert new_stats.total_files_processed == statistics.total_files_processed
        assert new_stats.total_files_successful == statistics.total_files_successful
        assert new_stats.success_rate == statistics.success_rate
    
    def test_from_dict_missing_required_fields(self):
        """Test from_dict method with missing required fields."""
        # Arrange
        data = {"total_files_processed": 100}  # Missing other required fields
        
        # Act & Assert
        with pytest.raises(ValueError, match="Required field 'period_start' missing in data"):
            ProcessingStatistics.from_dict(data)
    
    def test_equality(self, statistics):
        """Test equality comparison."""
        # Arrange
        same_stats = ProcessingStatistics(
            period_start=statistics.period_start,
            period_end=statistics.period_end,
            total_files_processed=statistics.total_files_processed,
            total_files_successful=statistics.total_files_successful
        )
        
        # Act & Assert
        assert statistics == same_stats
    
    def test_inequality(self, statistics):
        """Test inequality comparison."""
        # Arrange
        different_stats = ProcessingStatistics(
            period_start=statistics.period_start,
            period_end=statistics.period_end,
            total_files_processed=200,  # Different count
            total_files_successful=190
        )
        
        # Act & Assert
        assert statistics != different_stats
    
    def test_equality_different_type(self, statistics):
        """Test equality with different type."""
        # Act & Assert
        assert statistics != "not a ProcessingStatistics"
    
    def test_repr(self, statistics):
        """Test string representation."""
        # Act
        repr_str = repr(statistics)
        
        # Assert
        assert "ProcessingStatistics" in repr_str
        assert str(statistics.total_files_processed) in repr_str
        assert str(statistics.total_files_successful) in repr_str 