"""
Extended Tests for Database Models

Comprehensive test suite covering edge cases, validation errors,
and exception handling for database models.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from docanalyzer.models.database import (
    DatabaseFileRecord,
    ProcessingStatistics,
    DatabaseMetadata,
    DatabaseHealth,
    RecordStatus
)


class TestDatabaseFileRecordExtended:
    """Extended test suite for DatabaseFileRecord."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return {
            "file_path": "/tmp/test.txt",
            "file_size_bytes": 1024,
            "modification_time": datetime.now().isoformat(),
            "record_id": "test-id-123",
            "file_name": "test.txt",
            "file_extension": "txt",
            "status": "new",
            "processing_count": 1,
            "last_processed_at": datetime.now().isoformat(),
            "processing_errors": ["error1", "error2"],
            "metadata": {"key": "value"},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "vector_store_id": "vs-123",
            "chunk_count": 5
        }
    
    def test_from_dict_invalid_status(self, sample_data):
        """Test from_dict with invalid status."""
        # Arrange
        sample_data["status"] = "invalid_status"
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid status"):
            DatabaseFileRecord.from_dict(sample_data)
    
    def test_from_dict_missing_datetime_fields(self, sample_data):
        """Test from_dict with missing datetime fields."""
        # Arrange
        del sample_data["modification_time"]
        
        # Act & Assert
        with pytest.raises(ValueError, match="Required field 'modification_time' missing in data"):
            DatabaseFileRecord.from_dict(sample_data)
    
    def test_from_dict_empty_datetime_fields(self, sample_data):
        """Test from_dict with empty datetime fields."""
        # Arrange
        sample_data["modification_time"] = ""
        sample_data["created_at"] = ""
        sample_data["updated_at"] = ""
        sample_data["last_processed_at"] = ""
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid isoformat string"):
            DatabaseFileRecord.from_dict(sample_data)
    
    def test_from_dict_not_dict(self):
        """Test from_dict with non-dict input."""
        # Act & Assert
        with pytest.raises(TypeError, match="data must be dictionary"):
            DatabaseFileRecord.from_dict("not a dict")
    
    def test_mark_processing_completed_negative_chunk_count(self):
        """Test mark_processing_completed with negative chunk_count."""
        # Arrange
        record = DatabaseFileRecord("/tmp/test.txt", 1024, datetime.now())
        
        # Act & Assert
        with pytest.raises(ValueError, match="chunk_count must be non-negative integer"):
            record.mark_processing_completed(chunk_count=-1)
    
    def test_mark_processing_failed_empty_error_message(self):
        """Test mark_processing_failed with empty error message."""
        # Arrange
        record = DatabaseFileRecord("/tmp/test.txt", 1024, datetime.now())
        
        # Act & Assert
        with pytest.raises(ValueError, match="error_message must be non-empty string"):
            record.mark_processing_failed("")
    
    def test_mark_processing_failed_non_string_error_message(self):
        """Test mark_processing_failed with non-string error message."""
        # Arrange
        record = DatabaseFileRecord("/tmp/test.txt", 1024, datetime.now())
        
        # Act & Assert
        with pytest.raises(TypeError, match="error_message must be string"):
            record.mark_processing_failed(123)
    
    def test_equality_with_different_types(self):
        """Test equality comparison with different object types."""
        # Arrange
        record = DatabaseFileRecord("/tmp/test.txt", 1024, datetime.now())
        
        # Act & Assert
        assert record != "not a DatabaseFileRecord"
        assert record != 123
        assert record != {}
    
    def test_equality_with_different_attributes(self):
        """Test equality comparison with different attributes."""
        # Arrange
        record1 = DatabaseFileRecord("/tmp/test.txt", 1024, datetime.now())
        record2 = DatabaseFileRecord("/tmp/test2.txt", 1024, datetime.now())
        
        # Act & Assert
        assert record1 != record2


class TestProcessingStatisticsExtended:
    """Extended test suite for ProcessingStatistics."""
    
    @pytest.fixture
    def valid_params(self):
        """Create valid parameters for ProcessingStatistics."""
        now = datetime.now()
        return {
            "period_start": now,
            "period_end": now + timedelta(hours=1),
            "total_files_processed": 100,
            "total_files_successful": 95,
            "total_files_failed": 3,
            "total_files_skipped": 2,
            "total_processing_time_seconds": 500.0,
            "total_chunks_created": 500,
            "total_characters_processed": 100000
        }
    
    def test_validation_period_start_not_datetime(self, valid_params):
        """Test validation with non-datetime period_start."""
        # Arrange
        valid_params["period_start"] = "not a datetime"
        
        # Act & Assert
        with pytest.raises(TypeError, match="period_start must be datetime object"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_period_end_not_datetime(self, valid_params):
        """Test validation with non-datetime period_end."""
        # Arrange
        valid_params["period_end"] = "not a datetime"
        
        # Act & Assert
        with pytest.raises(TypeError, match="period_end must be datetime object"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_period_end_before_start(self, valid_params):
        """Test validation with period_end before period_start."""
        # Arrange
        valid_params["period_end"] = valid_params["period_start"] - timedelta(hours=1)
        
        # Act & Assert
        with pytest.raises(ValueError, match="period_end must be >= period_start"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_files_processed_negative(self, valid_params):
        """Test validation with negative total_files_processed."""
        # Arrange
        valid_params["total_files_processed"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_files_processed must be non-negative integer"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_files_processed_not_int(self, valid_params):
        """Test validation with non-int total_files_processed."""
        # Arrange
        valid_params["total_files_processed"] = "not an int"
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_files_processed must be non-negative integer"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_files_successful_negative(self, valid_params):
        """Test validation with negative total_files_successful."""
        # Arrange
        valid_params["total_files_successful"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_files_successful must be non-negative integer"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_files_successful_exceeds_processed(self, valid_params):
        """Test validation with total_files_successful exceeding total_files_processed."""
        # Arrange
        valid_params["total_files_successful"] = 101
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_files_successful cannot exceed total_files_processed"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_files_failed_negative(self, valid_params):
        """Test validation with negative total_files_failed."""
        # Arrange
        valid_params["total_files_failed"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_files_failed must be non-negative integer"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_files_skipped_negative(self, valid_params):
        """Test validation with negative total_files_skipped."""
        # Arrange
        valid_params["total_files_skipped"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_files_skipped must be non-negative integer"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_failed_plus_skipped_exceeds_processed(self, valid_params):
        """Test validation with sum of failed and skipped exceeding total processed."""
        # Arrange
        valid_params["total_files_failed"] = 50
        valid_params["total_files_skipped"] = 51
        
        # Act & Assert
        with pytest.raises(ValueError, match="sum of failed and skipped files cannot exceed total files"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_processing_time_negative(self, valid_params):
        """Test validation with negative total_processing_time_seconds."""
        # Arrange
        valid_params["total_processing_time_seconds"] = -1.0
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_processing_time_seconds must be non-negative number"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_processing_time_not_number(self, valid_params):
        """Test validation with non-number total_processing_time_seconds."""
        # Arrange
        valid_params["total_processing_time_seconds"] = "not a number"
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_processing_time_seconds must be non-negative number"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_chunks_created_negative(self, valid_params):
        """Test validation with negative total_chunks_created."""
        # Arrange
        valid_params["total_chunks_created"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_chunks_created must be non-negative integer"):
            ProcessingStatistics(**valid_params)
    
    def test_validation_total_characters_processed_negative(self, valid_params):
        """Test validation with negative total_characters_processed."""
        # Arrange
        valid_params["total_characters_processed"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_characters_processed must be non-negative integer"):
            ProcessingStatistics(**valid_params)
    
    def test_success_rate_zero_files(self, valid_params):
        """Test success_rate calculation with zero files processed."""
        # Arrange
        valid_params["total_files_processed"] = 0
        valid_params["total_files_successful"] = 0
        valid_params["total_files_failed"] = 0
        valid_params["total_files_skipped"] = 0
        stats = ProcessingStatistics(**valid_params)
        
        # Act
        rate = stats.success_rate
        
        # Assert
        assert rate == 0.0
    
    def test_failure_rate_zero_files(self, valid_params):
        """Test failure_rate calculation with zero files processed."""
        # Arrange
        valid_params["total_files_processed"] = 0
        valid_params["total_files_successful"] = 0
        valid_params["total_files_failed"] = 0
        valid_params["total_files_skipped"] = 0
        stats = ProcessingStatistics(**valid_params)
        
        # Act
        rate = stats.failure_rate
        
        # Assert
        assert rate == 0.0
    
    def test_average_processing_time_zero_files(self, valid_params):
        """Test average_processing_time_seconds calculation with zero files processed."""
        # Arrange
        valid_params["total_files_processed"] = 0
        valid_params["total_files_successful"] = 0
        valid_params["total_files_failed"] = 0
        valid_params["total_files_skipped"] = 0
        stats = ProcessingStatistics(**valid_params)
        
        # Act
        avg_time = stats.average_processing_time_seconds
        
        # Assert
        assert avg_time == 0.0


class TestDatabaseMetadataExtended:
    """Extended test suite for DatabaseMetadata."""
    
    @pytest.fixture
    def valid_params(self):
        """Create valid parameters for DatabaseMetadata."""
        return {
            "total_files": 1000,
            "total_chunks": 5000,
            "total_size_bytes": 1024000,
            "health_status": "healthy",
            "vector_store_status": "connected",
            "cache_size": 100,
            "cache_hit_rate": 0.85,
            "last_updated": datetime.now(),
            "configuration": {"key": "value"}
        }
    
    def test_validation_total_files_negative(self, valid_params):
        """Test validation with negative total_files."""
        # Arrange
        valid_params["total_files"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_files must be non-negative"):
            DatabaseMetadata(**valid_params)
    
    def test_validation_total_chunks_negative(self, valid_params):
        """Test validation with negative total_chunks."""
        # Arrange
        valid_params["total_chunks"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_chunks must be non-negative"):
            DatabaseMetadata(**valid_params)
    
    def test_validation_total_size_bytes_negative(self, valid_params):
        """Test validation with negative total_size_bytes."""
        # Arrange
        valid_params["total_size_bytes"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="total_size_bytes must be non-negative"):
            DatabaseMetadata(**valid_params)
    
    def test_validation_cache_size_negative(self, valid_params):
        """Test validation with negative cache_size."""
        # Arrange
        valid_params["cache_size"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="cache_size must be non-negative"):
            DatabaseMetadata(**valid_params)
    
    def test_validation_cache_hit_rate_below_zero(self, valid_params):
        """Test validation with cache_hit_rate below 0.0."""
        # Arrange
        valid_params["cache_hit_rate"] = -0.1
        
        # Act & Assert
        with pytest.raises(ValueError, match="cache_hit_rate must be between 0.0 and 1.0"):
            DatabaseMetadata(**valid_params)
    
    def test_validation_cache_hit_rate_above_one(self, valid_params):
        """Test validation with cache_hit_rate above 1.0."""
        # Arrange
        valid_params["cache_hit_rate"] = 1.1
        
        # Act & Assert
        with pytest.raises(ValueError, match="cache_hit_rate must be between 0.0 and 1.0"):
            DatabaseMetadata(**valid_params)
    
    def test_validation_last_updated_not_datetime(self, valid_params):
        """Test validation with non-datetime last_updated."""
        # Arrange
        valid_params["last_updated"] = "not a datetime"
        
        # Act & Assert
        with pytest.raises(TypeError, match="last_updated must be datetime object"):
            DatabaseMetadata(**valid_params)
    
    def test_from_dict_not_dict(self):
        """Test from_dict with non-dict input."""
        # Act & Assert
        with pytest.raises(TypeError, match="data must be dictionary"):
            DatabaseMetadata.from_dict("not a dict")
    
    def test_from_dict_missing_required_field(self):
        """Test from_dict with missing required field."""
        # Arrange
        data = {
            "total_files": 1000,
            "total_chunks": 5000,
            "total_size_bytes": 1024000,
            "health_status": "healthy"
            # Missing vector_store_status
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Required field 'vector_store_status' missing in data"):
            DatabaseMetadata.from_dict(data)
    
    def test_from_dict_empty_last_updated(self):
        """Test from_dict with empty last_updated."""
        # Arrange
        data = {
            "total_files": 1000,
            "total_chunks": 5000,
            "total_size_bytes": 1024000,
            "health_status": "healthy",
            "vector_store_status": "connected",
            "last_updated": ""
        }
        
        # Act
        metadata = DatabaseMetadata.from_dict(data)
        
        # Assert
        assert metadata.last_updated is not None  # Should be set to current time
    
    def test_equality_with_different_cache_hit_rate(self, valid_params):
        """Test equality comparison with different cache_hit_rate."""
        # Arrange
        metadata1 = DatabaseMetadata(**valid_params)
        valid_params["cache_hit_rate"] = 0.86
        metadata2 = DatabaseMetadata(**valid_params)
        
        # Act & Assert
        assert metadata1 != metadata2
    
    def test_equality_with_similar_cache_hit_rate(self, valid_params):
        """Test equality comparison with similar cache_hit_rate (within tolerance)."""
        # Arrange
        metadata1 = DatabaseMetadata(**valid_params)
        valid_params["cache_hit_rate"] = 0.8501  # Very close to 0.85
        metadata2 = DatabaseMetadata(**valid_params)
        
        # Act & Assert
        assert metadata1 == metadata2


class TestDatabaseHealthExtended:
    """Extended test suite for DatabaseHealth."""
    
    @pytest.fixture
    def valid_params(self):
        """Create valid parameters for DatabaseHealth."""
        return {
            "status": "healthy",
            "connection_status": "connected",
            "performance_metrics": {"response_time": 0.1},
            "error_count": 0,
            "last_error": None,
            "last_check": datetime.now()
        }
    
    def test_validation_error_count_negative(self, valid_params):
        """Test validation with negative error_count."""
        # Arrange
        valid_params["error_count"] = -1
        
        # Act & Assert
        with pytest.raises(ValueError, match="error_count must be non-negative"):
            DatabaseHealth(**valid_params)
    
    def test_validation_last_check_not_datetime(self, valid_params):
        """Test validation with non-datetime last_check."""
        # Arrange
        valid_params["last_check"] = "not a datetime"
        
        # Act & Assert
        with pytest.raises(TypeError, match="last_check must be datetime object"):
            DatabaseHealth(**valid_params)
    
    def test_from_dict_not_dict(self):
        """Test from_dict with non-dict input."""
        # Act & Assert
        with pytest.raises(TypeError, match="data must be dictionary"):
            DatabaseHealth.from_dict("not a dict")
    
    def test_from_dict_missing_required_field(self):
        """Test from_dict with missing required field."""
        # Arrange
        data = {
            "status": "healthy"
            # Missing connection_status
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Required field 'connection_status' missing in data"):
            DatabaseHealth.from_dict(data)
    
    def test_from_dict_empty_last_check(self):
        """Test from_dict with empty last_check."""
        # Arrange
        data = {
            "status": "healthy",
            "connection_status": "connected",
            "last_check": ""
        }
        
        # Act
        health = DatabaseHealth.from_dict(data)
        
        # Assert
        assert health.last_check is not None  # Should be set to current time
    
    def test_equality_with_different_types(self, valid_params):
        """Test equality comparison with different object types."""
        # Arrange
        health = DatabaseHealth(**valid_params)
        
        # Act & Assert
        assert health != "not a DatabaseHealth object"
        assert health != 123
        assert health != {}
    
    def test_equality_with_different_attributes(self, valid_params):
        """Test equality comparison with different attributes."""
        # Arrange
        health1 = DatabaseHealth(**valid_params)
        valid_params["status"] = "unhealthy"
        health2 = DatabaseHealth(**valid_params)
        
        # Act & Assert
        assert health1 != health2
    
    def test_equality_with_different_error_count(self, valid_params):
        """Test equality comparison with different error_count."""
        # Arrange
        health1 = DatabaseHealth(**valid_params)
        valid_params["error_count"] = 1
        health2 = DatabaseHealth(**valid_params)
        
        # Act & Assert
        assert health1 != health2
    
    def test_equality_with_different_last_error(self, valid_params):
        """Test equality comparison with different last_error."""
        # Arrange
        health1 = DatabaseHealth(**valid_params)
        valid_params["last_error"] = "Some error"
        health2 = DatabaseHealth(**valid_params)
        
        # Act & Assert
        assert health1 != health2 
    
    def test_database_metadata_from_dict_not_dict(self):
        """Test DatabaseMetadata.from_dict with non-dict input."""
        # Act & Assert
        with pytest.raises(TypeError, match="data must be dictionary"):
            DatabaseMetadata.from_dict("not a dict")
    
    def test_database_metadata_equality_with_different_types(self):
        """Test DatabaseMetadata equality comparison with different object types."""
        # Arrange
        metadata = DatabaseMetadata(1000, 5000, 1024000, "healthy", "connected")
        
        # Act & Assert
        assert metadata != "not a DatabaseMetadata object"
        assert metadata != 123
        assert metadata != {} 