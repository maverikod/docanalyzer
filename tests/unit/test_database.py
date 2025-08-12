"""
Tests for Database Models

Comprehensive test suite for database models including DatabaseFileRecord
and ProcessingStatistics classes.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from docanalyzer.models.database import (
    DatabaseFileRecord, ProcessingStatistics, RecordStatus
)


class TestDatabaseFileRecord:
    """Test suite for DatabaseFileRecord class."""
    
    @pytest.fixture
    def basic_record(self):
        """Create basic DatabaseFileRecord instance."""
        return DatabaseFileRecord(
            file_path="/path/to/file.txt",
            file_size_bytes=1024,
            modification_time=datetime.now()
        )
    
    def test_init_basic(self, basic_record):
        """Test basic initialization."""
        assert basic_record.file_path == "/path/to/file.txt"
        assert basic_record.file_size_bytes == 1024
        assert isinstance(basic_record.modification_time, datetime)
        assert basic_record.status == RecordStatus.NEW
        assert basic_record.processing_count == 0
        assert basic_record.chunk_count == 0
        assert basic_record.processing_errors == []
        assert basic_record.metadata == {}
        assert isinstance(basic_record.record_id, str)
        assert isinstance(basic_record.created_at, datetime)
        assert isinstance(basic_record.updated_at, datetime)
        assert basic_record.file_name == "file.txt"
        assert basic_record.file_extension == "txt"
    
    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        timestamp = datetime.now()
        record = DatabaseFileRecord(
            file_path="/path/to/document.pdf",
            file_size_bytes=2048,
            modification_time=timestamp,
            record_id="test-id-123",
            file_name="custom_name.pdf",
            file_extension="pdf",
            status=RecordStatus.COMPLETED,
            processing_count=3,
            last_processed_at=timestamp,
            processing_errors=["Error 1", "Error 2"],
            metadata={"category": "documentation"},
            created_at=timestamp,
            updated_at=timestamp,
            vector_store_id="vector_123",
            chunk_count=5
        )
        
        assert record.record_id == "test-id-123"
        assert record.file_name == "custom_name.pdf"
        assert record.file_extension == "pdf"
        assert record.status == RecordStatus.COMPLETED
        assert record.processing_count == 3
        assert record.last_processed_at == timestamp
        assert record.processing_errors == ["Error 1", "Error 2"]
        assert record.metadata == {"category": "documentation"}
        assert record.vector_store_id == "vector_123"
        assert record.chunk_count == 5
    
    def test_init_validation_errors(self):
        """Test initialization validation errors."""
        timestamp = datetime.now()
        
        # Empty file_path
        with pytest.raises(ValueError, match="file_path must be non-empty string"):
            DatabaseFileRecord("", 1024, timestamp)
        
        # Negative file_size_bytes
        with pytest.raises(ValueError, match="file_size_bytes must be non-negative integer"):
            DatabaseFileRecord("/path/file.txt", -1, timestamp)
        
        # Invalid modification_time
        with pytest.raises(TypeError, match="modification_time must be datetime object"):
            DatabaseFileRecord("/path/file.txt", 1024, "not datetime")
        
        # Negative processing_count
        with pytest.raises(ValueError, match="processing_count must be non-negative integer"):
            DatabaseFileRecord("/path/file.txt", 1024, timestamp, processing_count=-1)
        
        # Negative chunk_count
        with pytest.raises(ValueError, match="chunk_count must be non-negative integer"):
            DatabaseFileRecord("/path/file.txt", 1024, timestamp, chunk_count=-1)
    
    def test_file_name_extraction(self):
        """Test automatic file name extraction."""
        record = DatabaseFileRecord("/path/to/document.pdf", 1024, datetime.now())
        assert record.file_name == "document.pdf"
        
        record = DatabaseFileRecord("/path/to/file", 1024, datetime.now())
        assert record.file_name == "file"
    
    def test_file_extension_extraction(self):
        """Test automatic file extension extraction."""
        record = DatabaseFileRecord("/path/to/document.pdf", 1024, datetime.now())
        assert record.file_extension == "pdf"
        
        record = DatabaseFileRecord("/path/to/file", 1024, datetime.now())
        assert record.file_extension == ""
        
        record = DatabaseFileRecord("/path/to/file.TXT", 1024, datetime.now())
        assert record.file_extension == "txt"
    
    def test_mark_processing_started(self, basic_record):
        """Test marking record as processing started."""
        assert basic_record.status == RecordStatus.NEW
        assert basic_record.processing_count == 0
        
        basic_record.mark_processing_started()
        
        assert basic_record.status == RecordStatus.PROCESSING
        assert basic_record.processing_count == 1
        assert basic_record.updated_at > basic_record.created_at
    
    def test_mark_processing_completed(self, basic_record):
        """Test marking record as processing completed."""
        basic_record.mark_processing_completed("vector_123", 5)
        
        assert basic_record.status == RecordStatus.COMPLETED
        assert basic_record.last_processed_at is not None
        assert basic_record.vector_store_id == "vector_123"
        assert basic_record.chunk_count == 5
        assert basic_record.updated_at > basic_record.created_at
    
    def test_mark_processing_completed_validation(self, basic_record):
        """Test mark_processing_completed validation."""
        with pytest.raises(ValueError, match="chunk_count must be non-negative integer"):
            basic_record.mark_processing_completed(chunk_count=-1)
    
    def test_mark_processing_failed(self, basic_record):
        """Test marking record as processing failed."""
        basic_record.mark_processing_failed("File format not supported")
        
        assert basic_record.status == RecordStatus.FAILED
        assert basic_record.last_processed_at is not None
        assert basic_record.processing_errors == ["File format not supported"]
        assert basic_record.updated_at > basic_record.created_at
    
    def test_mark_processing_failed_validation(self, basic_record):
        """Test mark_processing_failed validation."""
        with pytest.raises(TypeError, match="error_message must be string"):
            basic_record.mark_processing_failed(123)
        
        with pytest.raises(ValueError, match="error_message must be non-empty string"):
            basic_record.mark_processing_failed("")
    
    def test_add_processing_error(self, basic_record):
        """Test adding processing error."""
        basic_record.add_processing_error("Permission denied")
        basic_record.add_processing_error("File locked")
        
        assert len(basic_record.processing_errors) == 2
        assert "Permission denied" in basic_record.processing_errors
        assert "File locked" in basic_record.processing_errors
        assert basic_record.updated_at > basic_record.created_at
    
    def test_add_processing_error_validation(self, basic_record):
        """Test add_processing_error validation."""
        with pytest.raises(TypeError, match="error_message must be string"):
            basic_record.add_processing_error(123)
        
        with pytest.raises(ValueError, match="error_message must be non-empty string"):
            basic_record.add_processing_error("")
    
    def test_update_metadata(self, basic_record):
        """Test metadata update."""
        basic_record.update_metadata({"category": "documentation", "priority": "high"})
        
        assert basic_record.metadata == {"category": "documentation", "priority": "high"}
        assert basic_record.updated_at > basic_record.created_at
    
    def test_update_metadata_validation(self, basic_record):
        """Test update_metadata validation."""
        with pytest.raises(TypeError, match="new_metadata must be dictionary"):
            basic_record.update_metadata("not a dict")
    
    def test_to_dict(self, basic_record):
        """Test dictionary conversion."""
        data = basic_record.to_dict()
        
        assert data["file_path"] == "/path/to/file.txt"
        assert data["file_name"] == "file.txt"
        assert data["file_size_bytes"] == 1024
        assert data["file_extension"] == "txt"
        assert data["status"] == "new"
        assert data["processing_count"] == 0
        assert data["chunk_count"] == 0
        assert data["processing_errors"] == []
        assert data["metadata"] == {}
        assert isinstance(data["modification_time"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
        assert data["last_processed_at"] is None
        assert data["vector_store_id"] is None
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        timestamp = datetime.now()
        data = {
            "file_path": "/path/to/file.txt",
            "file_size_bytes": 1024,
            "modification_time": timestamp.isoformat(),
            "record_id": "test-id",
            "status": "completed",
            "processing_count": 2,
            "chunk_count": 3,
            "processing_errors": ["Error 1"],
            "metadata": {"category": "test"},
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "vector_store_id": "vector_123"
        }
        
        record = DatabaseFileRecord.from_dict(data)
        
        assert record.file_path == "/path/to/file.txt"
        assert record.file_size_bytes == 1024
        assert record.record_id == "test-id"
        assert record.status == RecordStatus.COMPLETED
        assert record.processing_count == 2
        assert record.chunk_count == 3
        assert record.processing_errors == ["Error 1"]
        assert record.metadata == {"category": "test"}
        assert record.vector_store_id == "vector_123"
    
    def test_from_dict_validation(self):
        """Test from_dict validation."""
        timestamp = datetime.now()
        
        # Missing required field
        with pytest.raises(ValueError, match="Required field 'file_path' missing"):
            DatabaseFileRecord.from_dict({
                "file_size_bytes": 1024,
                "modification_time": timestamp.isoformat()
            })
        
        # Invalid data type
        with pytest.raises(TypeError, match="data must be dictionary"):
            DatabaseFileRecord.from_dict("not a dict")
        
        # Invalid status
        with pytest.raises(ValueError, match="Invalid status"):
            DatabaseFileRecord.from_dict({
                "file_path": "/path/file.txt",
                "file_size_bytes": 1024,
                "modification_time": timestamp.isoformat(),
                "status": "invalid_status"
            })
    
    def test_equality(self):
        """Test equality comparison."""
        timestamp = datetime.now()
        record1 = DatabaseFileRecord("/path/file.txt", 1024, timestamp)
        record2 = DatabaseFileRecord("/path/file.txt", 1024, timestamp)
        record3 = DatabaseFileRecord("/path/different.txt", 1024, timestamp)
        
        assert record1 == record2
        assert record1 != record3
        assert record1 != "not a record"
    
    def test_repr(self, basic_record):
        """Test string representation."""
        repr_str = repr(basic_record)
        assert "DatabaseFileRecord" in repr_str
        assert "/path/to/file.txt" in repr_str
        assert "1024" in repr_str
        assert "new" in repr_str


class TestProcessingStatistics:
    """Test suite for ProcessingStatistics class."""
    
    @pytest.fixture
    def basic_stats(self):
        """Create basic ProcessingStatistics instance."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        return ProcessingStatistics(
            period_start=start_time,
            period_end=end_time,
            total_files_processed=100,
            total_files_successful=95
        )
    
    def test_init_basic(self, basic_stats):
        """Test basic initialization."""
        assert basic_stats.total_files_processed == 100
        assert basic_stats.total_files_successful == 95
        assert basic_stats.total_files_failed == 0
        assert basic_stats.total_files_skipped == 0
        assert basic_stats.total_processing_time_seconds == 0.0
        assert basic_stats.total_chunks_created == 0
        assert basic_stats.total_characters_processed == 0
        assert basic_stats.file_type_breakdown == {}
        assert basic_stats.error_breakdown == {}
        assert basic_stats.processing_metadata == {}
        assert isinstance(basic_stats.statistics_id, str)
        assert isinstance(basic_stats.created_at, datetime)
    
    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        
        stats = ProcessingStatistics(
            period_start=start_time,
            period_end=end_time,
            total_files_processed=100,
            total_files_successful=90,
            statistics_id="test-id-123",
            total_files_failed=5,
            total_files_skipped=5,
            total_processing_time_seconds=500.0,
            total_chunks_created=1000,
            total_characters_processed=50000,
            file_type_breakdown={"txt": 50, "pdf": 30},
            error_breakdown={"FileNotFoundError": 3},
            processing_metadata={"version": "1.0"},
            created_at=start_time
        )
        
        assert stats.statistics_id == "test-id-123"
        assert stats.total_files_failed == 5
        assert stats.total_files_skipped == 5
        assert stats.total_processing_time_seconds == 500.0
        assert stats.total_chunks_created == 1000
        assert stats.total_characters_processed == 50000
        assert stats.file_type_breakdown == {"txt": 50, "pdf": 30}
        assert stats.error_breakdown == {"FileNotFoundError": 3}
        assert stats.processing_metadata == {"version": "1.0"}
        assert stats.created_at == start_time
    
    def test_init_validation_errors(self):
        """Test initialization validation errors."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        
        # Invalid period_end
        with pytest.raises(ValueError, match="period_end must be >= period_start"):
            ProcessingStatistics(end_time, start_time, 100, 95)
        
        # Invalid total_files_processed
        with pytest.raises(ValueError, match="total_files_processed must be non-negative integer"):
            ProcessingStatistics(start_time, end_time, -1, 95)
        
        # Invalid total_files_successful
        with pytest.raises(ValueError, match="total_files_successful must be non-negative integer"):
            ProcessingStatistics(start_time, end_time, 100, -1)
        
        # total_files_successful exceeds total_files_processed
        with pytest.raises(ValueError, match="total_files_successful cannot exceed total_files_processed"):
            ProcessingStatistics(start_time, end_time, 100, 101)
        
        # Invalid total_files_failed
        with pytest.raises(ValueError, match="total_files_failed must be non-negative integer"):
            ProcessingStatistics(start_time, end_time, 100, 95, total_files_failed=-1)
        
        # Invalid total_files_skipped
        with pytest.raises(ValueError, match="total_files_skipped must be non-negative integer"):
            ProcessingStatistics(start_time, end_time, 100, 95, total_files_skipped=-1)
        
        # Sum exceeds total
        with pytest.raises(ValueError, match="sum of failed and skipped files cannot exceed total files"):
            ProcessingStatistics(start_time, end_time, 100, 95, total_files_failed=50, total_files_skipped=51)
        
        # Invalid processing time
        with pytest.raises(ValueError, match="total_processing_time_seconds must be non-negative number"):
            ProcessingStatistics(start_time, end_time, 100, 95, total_processing_time_seconds=-1.0)
        
        # Invalid chunks created
        with pytest.raises(ValueError, match="total_chunks_created must be non-negative integer"):
            ProcessingStatistics(start_time, end_time, 100, 95, total_chunks_created=-1)
        
        # Invalid characters processed
        with pytest.raises(ValueError, match="total_characters_processed must be non-negative integer"):
            ProcessingStatistics(start_time, end_time, 100, 95, total_characters_processed=-1)
    
    def test_success_rate(self, basic_stats):
        """Test success rate calculation."""
        assert basic_stats.success_rate == 0.95
        
        # Zero files processed
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        stats = ProcessingStatistics(start_time, end_time, 0, 0)
        assert stats.success_rate == 0.0
    
    def test_failure_rate(self, basic_stats):
        """Test failure rate calculation."""
        assert basic_stats.failure_rate == 0.0
        
        # With failed files
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        stats = ProcessingStatistics(start_time, end_time, 100, 95, total_files_failed=3)
        assert stats.failure_rate == 0.03
        
        # Zero files processed
        stats = ProcessingStatistics(start_time, end_time, 0, 0)
        assert stats.failure_rate == 0.0
    
    def test_average_processing_time_seconds(self, basic_stats):
        """Test average processing time calculation."""
        assert basic_stats.average_processing_time_seconds == 0.0
        
        # With processing time
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        stats = ProcessingStatistics(start_time, end_time, 100, 95, total_processing_time_seconds=500.0)
        assert stats.average_processing_time_seconds == 5.0
        
        # Zero files processed
        stats = ProcessingStatistics(start_time, end_time, 0, 0)
        assert stats.average_processing_time_seconds == 0.0
    
    def test_period_duration_seconds(self, basic_stats):
        """Test period duration calculation."""
        duration = basic_stats.period_duration_seconds
        assert duration > 0
        assert abs(duration - 3600.0) < 1.0  # Should be approximately 1 hour
    
    def test_add_file_type_count(self, basic_stats):
        """Test adding file type count."""
        basic_stats.add_file_type_count("txt", 50)
        basic_stats.add_file_type_count("pdf", 30)
        basic_stats.add_file_type_count("txt", 10)  # Add to existing
        
        assert basic_stats.file_type_breakdown["txt"] == 60
        assert basic_stats.file_type_breakdown["pdf"] == 30
    
    def test_add_file_type_count_validation(self, basic_stats):
        """Test add_file_type_count validation."""
        with pytest.raises(TypeError, match="file_extension must be string"):
            basic_stats.add_file_type_count(123, 1)
        
        with pytest.raises(ValueError, match="file_extension must be non-empty string"):
            basic_stats.add_file_type_count("", 1)
        
        with pytest.raises(TypeError, match="count must be integer"):
            basic_stats.add_file_type_count("txt", "1")
        
        with pytest.raises(ValueError, match="count must be positive integer"):
            basic_stats.add_file_type_count("txt", 0)
    
    def test_add_error_count(self, basic_stats):
        """Test adding error count."""
        basic_stats.add_error_count("FileNotFoundError", 3)
        basic_stats.add_error_count("PermissionError", 2)
        basic_stats.add_error_count("FileNotFoundError", 1)  # Add to existing
        
        assert basic_stats.error_breakdown["FileNotFoundError"] == 4
        assert basic_stats.error_breakdown["PermissionError"] == 2
    
    def test_add_error_count_validation(self, basic_stats):
        """Test add_error_count validation."""
        with pytest.raises(TypeError, match="error_type must be string"):
            basic_stats.add_error_count(123, 1)
        
        with pytest.raises(ValueError, match="error_type must be non-empty string"):
            basic_stats.add_error_count("", 1)
        
        with pytest.raises(TypeError, match="count must be integer"):
            basic_stats.add_error_count("Error", "1")
        
        with pytest.raises(ValueError, match="count must be positive integer"):
            basic_stats.add_error_count("Error", 0)
    
    def test_to_dict(self, basic_stats):
        """Test dictionary conversion."""
        data = basic_stats.to_dict()
        
        assert data["total_files_processed"] == 100
        assert data["total_files_successful"] == 95
        assert data["total_files_failed"] == 0
        assert data["total_files_skipped"] == 0
        assert data["total_processing_time_seconds"] == 0.0
        assert data["total_chunks_created"] == 0
        assert data["total_characters_processed"] == 0
        assert data["file_type_breakdown"] == {}
        assert data["error_breakdown"] == {}
        assert data["processing_metadata"] == {}
        assert data["success_rate"] == 0.95
        assert data["failure_rate"] == 0.0
        assert data["average_processing_time_seconds"] == 0.0
        assert data["period_duration_seconds"] > 0
        assert isinstance(data["period_start"], str)
        assert isinstance(data["period_end"], str)
        assert isinstance(data["created_at"], str)
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        
        data = {
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "total_files_processed": 100,
            "total_files_successful": 95,
            "statistics_id": "test-id",
            "total_files_failed": 3,
            "total_files_skipped": 2,
            "total_processing_time_seconds": 500.0,
            "total_chunks_created": 1000,
            "total_characters_processed": 50000,
            "file_type_breakdown": {"txt": 50},
            "error_breakdown": {"FileNotFoundError": 3},
            "processing_metadata": {"version": "1.0"},
            "created_at": start_time.isoformat()
        }
        
        stats = ProcessingStatistics.from_dict(data)
        
        assert stats.total_files_processed == 100
        assert stats.total_files_successful == 95
        assert stats.total_files_failed == 3
        assert stats.total_files_skipped == 2
        assert stats.total_processing_time_seconds == 500.0
        assert stats.total_chunks_created == 1000
        assert stats.total_characters_processed == 50000
        assert stats.file_type_breakdown == {"txt": 50}
        assert stats.error_breakdown == {"FileNotFoundError": 3}
        assert stats.processing_metadata == {"version": "1.0"}
        assert stats.statistics_id == "test-id"
    
    def test_from_dict_validation(self):
        """Test from_dict validation."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        
        # Missing required field
        with pytest.raises(ValueError, match="Required field 'period_start' missing"):
            ProcessingStatistics.from_dict({
                "period_end": end_time.isoformat(),
                "total_files_processed": 100,
                "total_files_successful": 95
            })
        
        # Invalid data type
        with pytest.raises(TypeError, match="data must be dictionary"):
            ProcessingStatistics.from_dict("not a dict")
    
    def test_equality(self):
        """Test equality comparison."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        
        stats1 = ProcessingStatistics(start_time, end_time, 100, 95)
        stats2 = ProcessingStatistics(start_time, end_time, 100, 95)
        stats3 = ProcessingStatistics(start_time, end_time, 200, 190)
        
        assert stats1 == stats2
        assert stats1 != stats3
        assert stats1 != "not stats"
    
    def test_repr(self, basic_stats):
        """Test string representation."""
        repr_str = repr(basic_stats)
        assert "ProcessingStatistics" in repr_str
        assert "100" in repr_str
        assert "95" in repr_str 