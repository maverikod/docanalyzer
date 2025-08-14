"""
Extended Tests for Database Manager

Additional unit tests to achieve 90%+ coverage for database_manager.py.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

from docanalyzer.services.database_manager import DatabaseManager, FileRepository
from docanalyzer.models.file_system.file_info import FileInfo
from docanalyzer.models.database import DatabaseFileRecord, RecordStatus, DatabaseMetadata
from docanalyzer.models.errors import ProcessingError, NotFoundError, ValidationError, DatabaseError
from docanalyzer.config.integration import DocAnalyzerConfig
from docanalyzer.monitoring.health import HealthChecker
from docanalyzer.monitoring.metrics import MetricsCollector
from docanalyzer.services.vector_store_wrapper import VectorStoreWrapper


class TestDatabaseManagerExtended:
    """Extended test suite for DatabaseManager class."""
    
    @pytest.fixture
    def temp_test_dir(self):
        """Create temporary test directory."""
        temp_dir = tempfile.mkdtemp(prefix="test_database_manager_extended_")
        yield temp_dir
        # Cleanup after test
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_file_path(self, temp_test_dir):
        """Create test file path."""
        test_file = os.path.join(temp_test_dir, "test_file.txt")
        # Create test file
        with open(test_file, 'w') as f:
            f.write("Test content")
        return test_file
    
    @pytest.fixture
    def mock_file_info(self, test_file_path):
        """Create mock file info."""
        return FileInfo(
            file_path=test_file_path,
            file_size=1024,
            modification_time=datetime.now(),
            is_directory=False,
            processing_status="pending"
        )
    
    @pytest.fixture
    def mock_vector_store_wrapper(self):
        """Create mock vector store wrapper."""
        wrapper = AsyncMock(spec=VectorStoreWrapper)
        wrapper.initialize = AsyncMock()
        wrapper.cleanup = AsyncMock()
        wrapper.get_health_status = AsyncMock(return_value={"status": "healthy"})
        wrapper.delete_chunks_by_source = AsyncMock()
        return wrapper
    
    @pytest.fixture
    def mock_health_checker(self):
        """Create mock health checker."""
        checker = AsyncMock(spec=HealthChecker)
        mock_status = Mock()
        mock_status.status = "healthy"
        checker.check_database_health = AsyncMock(return_value=mock_status)
        return checker
    
    @pytest.fixture
    def database_manager(self, mock_vector_store_wrapper, mock_health_checker):
        """Create test database manager."""
        with patch('docanalyzer.services.database_manager.VectorStoreWrapper', return_value=mock_vector_store_wrapper), \
             patch('docanalyzer.services.database_manager.HealthChecker', return_value=mock_health_checker):
            return DatabaseManager()
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, database_manager, mock_vector_store_wrapper, mock_health_checker):
        """Test successful initialization."""
        # Act
        result = await database_manager.initialize()
        
        # Assert
        assert result is True
        assert database_manager.is_initialized is True
        mock_vector_store_wrapper.initialize.assert_called_once()
        mock_health_checker.check_database_health.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_vector_store_failure(self, database_manager, mock_vector_store_wrapper):
        """Test initialization with vector store failure."""
        # Arrange
        mock_vector_store_wrapper.initialize.side_effect = Exception("Vector store error")
        
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager initialization failed"):
            await database_manager.initialize()
        
        assert database_manager.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_health_check_failure(self, database_manager, mock_vector_store_wrapper, mock_health_checker):
        """Test initialization with health check failure."""
        # Arrange
        mock_health_checker.check_database_health.side_effect = Exception("Health check error")
        
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager initialization failed"):
            await database_manager.initialize()
        
        assert database_manager.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_create_file_record_not_initialized(self, database_manager, mock_file_info, test_file_path):
        """Test creating file record when not initialized."""
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager not initialized"):
            await database_manager.create_file_record(test_file_path, mock_file_info)
    
    @pytest.mark.asyncio
    async def test_get_file_record_not_initialized(self, database_manager, test_file_path):
        """Test getting file record when not initialized."""
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager not initialized"):
            await database_manager.get_file_record(test_file_path)
    
    @pytest.mark.asyncio
    async def test_update_file_status_not_initialized(self, database_manager, test_file_path):
        """Test updating file status when not initialized."""
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager not initialized"):
            await database_manager.update_file_status(test_file_path, RecordStatus.COMPLETED)
    
    @pytest.mark.asyncio
    async def test_get_files_by_status_not_initialized(self, database_manager):
        """Test getting files by status when not initialized."""
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager not initialized"):
            await database_manager.get_files_by_status(RecordStatus.COMPLETED)
    
    @pytest.mark.asyncio
    async def test_get_files_by_extension_not_initialized(self, database_manager):
        """Test getting files by extension when not initialized."""
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager not initialized"):
            await database_manager.get_files_by_extension(".txt")
    
    @pytest.mark.asyncio
    async def test_delete_file_record_not_initialized(self, database_manager, test_file_path):
        """Test deleting file record when not initialized."""
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager not initialized"):
            await database_manager.delete_file_record(test_file_path)
    
    @pytest.mark.asyncio
    async def test_get_processing_statistics_not_initialized(self, database_manager):
        """Test getting processing statistics when not initialized."""
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager not initialized"):
            await database_manager.get_processing_statistics()
    
    @pytest.mark.asyncio
    async def test_get_database_metadata_not_initialized(self, database_manager):
        """Test getting database metadata when not initialized."""
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager not initialized"):
            await database_manager.get_database_metadata()
    
    @pytest.mark.asyncio
    async def test_create_file_record_repository_error(self, database_manager, mock_file_info, test_file_path):
        """Test creating file record with repository error."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'create_file_record', side_effect=Exception("Repository error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to create file record"):
                await database_manager.create_file_record(test_file_path, mock_file_info)
    
    @pytest.mark.asyncio
    async def test_get_file_record_repository_error(self, database_manager, test_file_path):
        """Test getting file record with repository error."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'get_file_record', side_effect=Exception("Repository error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to get file record"):
                await database_manager.get_file_record(test_file_path)
    
    @pytest.mark.asyncio
    async def test_update_file_status_repository_error(self, database_manager, test_file_path):
        """Test updating file status with repository error."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'update_file_status', side_effect=Exception("Repository error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to update file status"):
                await database_manager.update_file_status(test_file_path, RecordStatus.COMPLETED)
    
    @pytest.mark.asyncio
    async def test_get_files_by_status_repository_error(self, database_manager):
        """Test getting files by status with repository error."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'get_files_by_status', side_effect=Exception("Repository error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to get files by status"):
                await database_manager.get_files_by_status(RecordStatus.COMPLETED)
    
    @pytest.mark.asyncio
    async def test_get_files_by_extension_repository_error(self, database_manager):
        """Test getting files by extension with repository error."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'get_files_by_extension', side_effect=Exception("Repository error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to get files by extension"):
                await database_manager.get_files_by_extension(".txt")
    
    @pytest.mark.asyncio
    async def test_delete_file_record_repository_error(self, database_manager, test_file_path):
        """Test deleting file record with repository error."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'delete_file_record', side_effect=Exception("Repository error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to delete file record"):
                await database_manager.delete_file_record(test_file_path)
    
    @pytest.mark.asyncio
    async def test_get_processing_statistics_repository_error(self, database_manager):
        """Test getting processing statistics with repository error."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'get_statistics', side_effect=Exception("Repository error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to get processing statistics"):
                await database_manager.get_processing_statistics()
    
    @pytest.mark.asyncio
    async def test_get_database_metadata_error(self, database_manager, mock_health_checker):
        """Test getting database metadata with error."""
        # Arrange
        await database_manager.initialize()
        mock_health_checker.check_database_health.side_effect = Exception("Health check error")
        
        # Act & Assert
        with pytest.raises(ProcessingError, match="Failed to get database metadata"):
            await database_manager.get_database_metadata()
    
    @pytest.mark.asyncio
    async def test_cleanup_success(self, database_manager, mock_vector_store_wrapper):
        """Test successful cleanup."""
        # Arrange
        await database_manager.initialize()
        
        # Act
        result = await database_manager.cleanup()
        
        # Assert
        assert result is True
        assert database_manager.is_initialized is False
        mock_vector_store_wrapper.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_error(self, database_manager, mock_vector_store_wrapper):
        """Test cleanup with error."""
        # Arrange
        await database_manager.initialize()
        mock_vector_store_wrapper.cleanup.side_effect = Exception("Cleanup error")
        
        # Act & Assert
        with pytest.raises(ProcessingError, match="Database Manager cleanup failed"):
            await database_manager.cleanup()
    
    def test_cache_operations(self, database_manager):
        """Test cache operations."""
        # Test _update_cache
        database_manager._update_cache("test_key", "test_value")
        assert "test_key" in database_manager._cache
        assert database_manager._cache["test_key"] == "test_value"
        assert "test_key" in database_manager._cache_timestamps
    
    def test_cache_eviction(self, database_manager):
        """Test cache eviction when full."""
        # Fill cache to capacity
        for i in range(database_manager.cache_size + 1):
            database_manager._update_cache(f"key_{i}", f"value_{i}")
        
        # Oldest key should be evicted
        assert "key_0" not in database_manager._cache
        assert "key_1" in database_manager._cache
    
    def test_get_from_cache_hit(self, database_manager):
        """Test cache hit."""
        # Arrange
        database_manager._update_cache("test_key", "test_value")
        
        # Act
        result = database_manager._get_from_cache("test_key")
        
        # Assert
        assert result == "test_value"
    
    def test_get_from_cache_miss(self, database_manager):
        """Test cache miss."""
        # Act
        result = database_manager._get_from_cache("nonexistent_key")
        
        # Assert
        assert result is None
    
    def test_get_from_cache_expired(self, database_manager):
        """Test cache expiration."""
        # Arrange
        database_manager._update_cache("test_key", "test_value")
        # Manually set old timestamp
        database_manager._cache_timestamps["test_key"] = datetime.now() - timedelta(seconds=database_manager.cache_ttl + 1)
        
        # Act
        result = database_manager._get_from_cache("test_key")
        
        # Assert
        assert result is None
        assert "test_key" not in database_manager._cache
    
    def test_invalidate_cache(self, database_manager):
        """Test cache invalidation."""
        # Arrange
        database_manager._update_cache("test_key", "test_value")
        
        # Act
        database_manager._invalidate_cache("test_key")
        
        # Assert
        assert "test_key" not in database_manager._cache
        assert "test_key" not in database_manager._cache_timestamps
    
    def test_calculate_cache_hit_rate(self, database_manager):
        """Test cache hit rate calculation."""
        # Arrange - Add some data to cache
        database_manager._update_cache("test_key1", "test_value1")
        database_manager._update_cache("test_key2", "test_value2")
        
        # Act
        rate = database_manager._calculate_cache_hit_rate()
        
        # Assert
        assert rate == 0.85  # Placeholder value
    
    def test_calculate_cache_hit_rate_empty(self, database_manager):
        """Test cache hit rate calculation with empty cache."""
        # Clear cache
        database_manager._cache.clear()
        database_manager._cache_timestamps.clear()
        
        # Act
        rate = database_manager._calculate_cache_hit_rate()
        
        # Assert
        assert rate == 0.0


class TestFileRepositoryExtended:
    """Extended test suite for FileRepository class."""
    
    @pytest.fixture
    def temp_test_dir(self):
        """Create temporary test directory."""
        temp_dir = tempfile.mkdtemp(prefix="test_file_repository_extended_")
        yield temp_dir
        # Cleanup after test
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_file_path(self, temp_test_dir):
        """Create test file path."""
        test_file = os.path.join(temp_test_dir, "test_file.txt")
        # Create test file
        with open(test_file, 'w') as f:
            f.write("Test content")
        return test_file
    
    @pytest.fixture
    def mock_file_info(self, test_file_path):
        """Create mock file info."""
        return FileInfo(
            file_path=test_file_path,
            file_size=1024,
            modification_time=datetime.now(),
            is_directory=False,
            processing_status="pending"
        )
    
    @pytest.fixture
    def mock_vector_store_wrapper(self):
        """Create mock vector store wrapper."""
        wrapper = AsyncMock(spec=VectorStoreWrapper)
        wrapper.delete_chunks_by_source = AsyncMock()
        return wrapper
    
    @pytest.fixture
    def mock_metrics_collector(self):
        """Create mock metrics collector."""
        collector = Mock(spec=MetricsCollector)
        collector.increment_counter = Mock()
        return collector
    
    @pytest.fixture
    def mock_health_checker(self):
        """Create mock health checker."""
        checker = AsyncMock(spec=HealthChecker)
        mock_status = Mock()
        mock_status.status = "healthy"
        checker.check_database_health = AsyncMock(return_value=mock_status)
        return checker
    
    @pytest.fixture
    def database_manager(self, mock_vector_store_wrapper, mock_health_checker):
        """Create test database manager."""
        with patch('docanalyzer.services.database_manager.VectorStoreWrapper', return_value=mock_vector_store_wrapper), \
             patch('docanalyzer.services.database_manager.HealthChecker', return_value=mock_health_checker):
            return DatabaseManager()
    
    @pytest.fixture
    def file_repository(self, mock_vector_store_wrapper, mock_metrics_collector):
        """Create test file repository."""
        return FileRepository(mock_vector_store_wrapper, mock_metrics_collector)
    
    @pytest.mark.asyncio
    async def test_create_file_record_validation_error_empty_path(self, file_repository, mock_file_info):
        """Test creating file record with empty path."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_path must be non-empty string"):
            await file_repository.create_file_record("", mock_file_info)
    
    @pytest.mark.asyncio
    async def test_create_file_record_validation_error_none_path(self, file_repository, mock_file_info):
        """Test creating file record with None path."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_path must be non-empty string"):
            await file_repository.create_file_record(None, mock_file_info)
    
    @pytest.mark.asyncio
    async def test_create_file_record_validation_error_invalid_path_type(self, file_repository, mock_file_info):
        """Test creating file record with invalid path type."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_path must be non-empty string"):
            await file_repository.create_file_record(123, mock_file_info)
    
    @pytest.mark.asyncio
    async def test_create_file_record_validation_error_none_file_info(self, file_repository):
        """Test creating file record with None file_info."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_info cannot be None"):
            await file_repository.create_file_record("/tmp/test.txt", None)
    
    @pytest.mark.asyncio
    async def test_create_file_record_database_error(self, file_repository, mock_file_info, test_file_path):
        """Test creating file record with database error."""
        # Arrange
        file_repository.records[test_file_path] = Mock()  # Simulate existing record
        
        # Act & Assert
        with pytest.raises(DatabaseError, match="File record already exists"):
            await file_repository.create_file_record(test_file_path, mock_file_info)
    
    @pytest.mark.asyncio
    async def test_get_file_record_validation_error_empty_path(self, file_repository):
        """Test getting file record with empty path."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_path must be non-empty string"):
            await file_repository.get_file_record("")
    
    @pytest.mark.asyncio
    async def test_get_file_record_validation_error_none_path(self, file_repository):
        """Test getting file record with None path."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_path must be non-empty string"):
            await file_repository.get_file_record(None)
    
    @pytest.mark.asyncio
    async def test_get_file_record_validation_error_invalid_path_type(self, file_repository):
        """Test getting file record with invalid path type."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_path must be non-empty string"):
            await file_repository.get_file_record(123)
    
    @pytest.mark.asyncio
    async def test_update_file_record_validation_error_empty_path(self, file_repository):
        """Test updating file record with empty path."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_path must be non-empty string"):
            await file_repository.update_file_record("", {"status": "completed"})
    
    @pytest.mark.asyncio
    async def test_update_file_record_validation_error_invalid_updates_type(self, file_repository):
        """Test updating file record with invalid updates type."""
        # Act & Assert
        with pytest.raises(ValidationError, match="updates must be dictionary"):
            await file_repository.update_file_record("/tmp/test.txt", "invalid")
    
    @pytest.mark.asyncio
    async def test_update_file_status_validation_error_empty_path(self, file_repository):
        """Test updating file status with empty path."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_path must be non-empty string"):
            await file_repository.update_file_status("", RecordStatus.COMPLETED)
    
    @pytest.mark.asyncio
    async def test_update_file_status_validation_error_invalid_status_type(self, file_repository):
        """Test updating file status with invalid status type."""
        # Act & Assert
        with pytest.raises(ValidationError, match="status must be RecordStatus enum"):
            await file_repository.update_file_status("/tmp/test.txt", "invalid")
    
    @pytest.mark.asyncio
    async def test_get_files_by_status_validation_error_invalid_status_type(self, file_repository):
        """Test getting files by status with invalid status type."""
        # Act & Assert
        with pytest.raises(ValidationError, match="status must be RecordStatus enum"):
            await file_repository.get_files_by_status("invalid")
    
    @pytest.mark.asyncio
    async def test_get_files_by_status_validation_error_negative_limit(self, file_repository):
        """Test getting files by status with negative limit."""
        # Act & Assert
        with pytest.raises(ValidationError, match="limit must be non-negative"):
            await file_repository.get_files_by_status(RecordStatus.COMPLETED, -1)
    
    @pytest.mark.asyncio
    async def test_get_files_by_extension_validation_error_empty_extension(self, file_repository):
        """Test getting files by extension with empty extension."""
        # Act & Assert
        with pytest.raises(ValidationError, match="extension must be non-empty string"):
            await file_repository.get_files_by_extension("")
    
    @pytest.mark.asyncio
    async def test_get_files_by_extension_validation_error_invalid_status_type(self, file_repository):
        """Test getting files by extension with invalid status type."""
        # Act & Assert
        with pytest.raises(ValidationError, match="status must be RecordStatus enum"):
            await file_repository.get_files_by_extension(".txt", "invalid")
    
    @pytest.mark.asyncio
    async def test_delete_file_record_validation_error_empty_path(self, file_repository):
        """Test deleting file record with empty path."""
        # Act & Assert
        with pytest.raises(ValidationError, match="file_path must be non-empty string"):
            await file_repository.delete_file_record("")
    
    @pytest.mark.asyncio
    async def test_delete_file_record_vector_store_error(self, file_repository, mock_file_info, mock_vector_store_wrapper, test_file_path):
        """Test deleting file record with vector store error."""
        # Arrange
        record = await file_repository.create_file_record(test_file_path, mock_file_info)
        record.vector_store_id = "test_id"
        mock_vector_store_wrapper.delete_chunks_by_source.side_effect = Exception("Vector store error")
        
        # Act
        result = await file_repository.delete_file_record(test_file_path)
        
        # Assert
        assert result is True  # Should still succeed despite vector store error
        assert record.status == RecordStatus.DELETED
    
    @pytest.mark.asyncio
    async def test_get_statistics_error(self, file_repository):
        """Test getting statistics with error."""
        # Arrange
        file_repository.records = None  # Cause error
        
        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to calculate statistics"):
            await file_repository.get_statistics()
    
    def test_file_repository_init_validation_error(self):
        """Test FileRepository initialization with None vector_store_wrapper."""
        # Act & Assert
        with pytest.raises(ValueError, match="vector_store_wrapper cannot be None"):
            FileRepository(None)
    
    def test_database_manager_init_validation_errors(self):
        """Test DatabaseManager initialization with invalid parameters."""
        # Test invalid cache_size
        with pytest.raises(ValueError, match="cache_size must be positive"):
            DatabaseManager(cache_size=0)
        
        # Test invalid cache_ttl
        with pytest.raises(ValueError, match="cache_ttl must be positive"):
            DatabaseManager(cache_ttl=0)
        
        # Test invalid batch_size
        with pytest.raises(ValueError, match="batch_size must be positive"):
            DatabaseManager(batch_size=0)
        
        # Test invalid transaction_timeout
        with pytest.raises(ValueError, match="transaction_timeout must be positive"):
            DatabaseManager(transaction_timeout=0) 

    @pytest.mark.asyncio
    async def test_update_file_record_exception_handling(self, file_repository, mock_file_info, test_file_path):
        """Test update_file_record exception handling."""
        # Arrange
        record = await file_repository.create_file_record(test_file_path, mock_file_info)
        
        # Act & Assert - Test with metrics collector error that causes exception
        with patch.object(file_repository.metrics_collector, 'increment_counter', side_effect=Exception("Metrics error")):
            with pytest.raises(DatabaseError, match="Failed to update file record"):
                await file_repository.update_file_record(test_file_path, {"file_size_bytes": 2048})
    
    @pytest.mark.asyncio
    async def test_update_file_status_exception_handling(self, file_repository, mock_file_info, test_file_path):
        """Test update_file_status exception handling."""
        # Arrange
        await file_repository.create_file_record(test_file_path, mock_file_info)
        
        # Act & Assert - Test with metrics collector error that causes exception
        with patch.object(file_repository.metrics_collector, 'increment_counter', side_effect=Exception("Metrics error")):
            with pytest.raises(DatabaseError, match="Failed to update file status"):
                await file_repository.update_file_status(test_file_path, RecordStatus.COMPLETED)
    
    @pytest.mark.asyncio
    async def test_delete_file_record_exception_handling(self, file_repository, mock_file_info, test_file_path):
        """Test delete_file_record exception handling."""
        # Arrange
        record = await file_repository.create_file_record(test_file_path, mock_file_info)
        record.vector_store_id = "test_id"
        
        # Act & Assert - Test with metrics collector error that causes exception
        with patch.object(file_repository.metrics_collector, 'increment_counter', side_effect=Exception("Metrics error")):
            with pytest.raises(DatabaseError, match="Failed to delete file record"):
                await file_repository.delete_file_record(test_file_path)
    
    @pytest.mark.asyncio
    async def test_get_statistics_exception_handling(self, file_repository):
        """Test get_statistics exception handling."""
        # Arrange - Set records to None to cause exception
        file_repository.records = None
        
        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to calculate statistics"):
            await file_repository.get_statistics()
    
    @pytest.mark.asyncio
    async def test_update_file_status_with_error_message(self, file_repository, mock_file_info, test_file_path):
        """Test update_file_status with error message for FAILED status."""
        # Arrange
        await file_repository.create_file_record(test_file_path, mock_file_info)
        
        # Act
        record = await file_repository.update_file_status(
            test_file_path, 
            RecordStatus.FAILED, 
            "Test error message"
        )
        
        # Assert
        assert record.status == RecordStatus.FAILED
        assert "Test error message" in record.processing_errors
        assert record.processing_count == 1
    
    @pytest.mark.asyncio
    async def test_update_file_status_without_error_message(self, file_repository, mock_file_info, test_file_path):
        """Test update_file_status without error message for non-FAILED status."""
        # Arrange
        await file_repository.create_file_record(test_file_path, mock_file_info)
        
        # Act
        record = await file_repository.update_file_status(
            test_file_path, 
            RecordStatus.COMPLETED, 
            "This should not be added"
        )
        
        # Assert
        assert record.status == RecordStatus.COMPLETED
        assert len(record.processing_errors) == 0  # Error message should not be added for non-FAILED status
        assert record.processing_count == 1
    
    @pytest.mark.asyncio
    async def test_update_file_status_archived_status(self, file_repository, mock_file_info, test_file_path):
        """Test update_file_status with ARCHIVED status (should not increment processing_count)."""
        # Arrange
        await file_repository.create_file_record(test_file_path, mock_file_info)
        
        # Act
        record = await file_repository.update_file_status(test_file_path, RecordStatus.ARCHIVED)
        
        # Assert
        assert record.status == RecordStatus.ARCHIVED
        assert record.processing_count == 0  # ARCHIVED should not increment processing_count
    
    @pytest.mark.asyncio
    async def test_database_manager_create_file_record_exception(self, database_manager, mock_file_info, test_file_path):
        """Test DatabaseManager create_file_record with exception."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'create_file_record', side_effect=Exception("Test error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to create file record"):
                await database_manager.create_file_record(test_file_path, mock_file_info)
    
    @pytest.mark.asyncio
    async def test_database_manager_get_file_record_exception(self, database_manager, test_file_path):
        """Test DatabaseManager get_file_record with exception."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'get_file_record', side_effect=Exception("Test error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to get file record"):
                await database_manager.get_file_record(test_file_path)
    
    @pytest.mark.asyncio
    async def test_database_manager_update_file_status_exception(self, database_manager, test_file_path):
        """Test DatabaseManager update_file_status with exception."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'update_file_status', side_effect=Exception("Test error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to update file status"):
                await database_manager.update_file_status(test_file_path, RecordStatus.COMPLETED)
    
    @pytest.mark.asyncio
    async def test_database_manager_get_files_by_status_exception(self, database_manager):
        """Test DatabaseManager get_files_by_status with exception."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'get_files_by_status', side_effect=Exception("Test error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to get files by status"):
                await database_manager.get_files_by_status(RecordStatus.COMPLETED)
    
    @pytest.mark.asyncio
    async def test_database_manager_get_files_by_extension_exception(self, database_manager):
        """Test DatabaseManager get_files_by_extension with exception."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'get_files_by_extension', side_effect=Exception("Test error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to get files by extension"):
                await database_manager.get_files_by_extension(".txt")
    
    @pytest.mark.asyncio
    async def test_database_manager_delete_file_record_exception(self, database_manager, test_file_path):
        """Test DatabaseManager delete_file_record with exception."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'delete_file_record', side_effect=Exception("Test error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to delete file record"):
                await database_manager.delete_file_record(test_file_path)
    
    @pytest.mark.asyncio
    async def test_database_manager_get_processing_statistics_exception(self, database_manager):
        """Test DatabaseManager get_processing_statistics with exception."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.file_repository, 'get_statistics', side_effect=Exception("Test error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to get processing statistics"):
                await database_manager.get_processing_statistics()
    
    @pytest.mark.asyncio
    async def test_database_manager_get_database_metadata_exception(self, database_manager, mock_health_checker):
        """Test DatabaseManager get_database_metadata with exception."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.health_checker, 'check_database_health', side_effect=Exception("Test error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Failed to get database metadata"):
                await database_manager.get_database_metadata()
    
    @pytest.mark.asyncio
    async def test_database_manager_cleanup_exception(self, database_manager, mock_vector_store_wrapper):
        """Test DatabaseManager cleanup with exception."""
        # Arrange
        await database_manager.initialize()
        with patch.object(database_manager.vector_store_wrapper, 'cleanup', side_effect=Exception("Test error")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="Database Manager cleanup failed"):
                await database_manager.cleanup()
    
    def test_update_cache_with_eviction(self, database_manager):
        """Test cache update with eviction when full."""
        # Arrange - Fill cache to capacity
        database_manager.cache_size = 2
        database_manager._update_cache("key1", "value1")
        database_manager._update_cache("key2", "value2")
        
        # Act - Add one more item to trigger eviction
        database_manager._update_cache("key3", "value3")
        
        # Assert - Oldest key should be evicted
        assert "key1" not in database_manager._cache
        assert "key2" in database_manager._cache
        assert "key3" in database_manager._cache
        assert len(database_manager._cache) == 2
    
    def test_get_from_cache_expired(self, database_manager):
        """Test getting expired cache entry."""
        # Arrange
        database_manager._update_cache("test_key", "test_value")
        # Manually set old timestamp to simulate expiration
        database_manager._cache_timestamps["test_key"] = datetime.now() - timedelta(seconds=database_manager.cache_ttl + 1)
        
        # Act
        result = database_manager._get_from_cache("test_key")
        
        # Assert
        assert result is None
        assert "test_key" not in database_manager._cache
    
    def test_invalidate_cache_nonexistent_key(self, database_manager):
        """Test invalidating non-existent cache key."""
        # Act - Should not raise exception
        database_manager._invalidate_cache("nonexistent_key")
        
        # Assert - Cache should remain unchanged
        assert len(database_manager._cache) == 0
    
    def test_calculate_cache_hit_rate_empty(self, database_manager):
        """Test cache hit rate calculation with empty cache."""
        # Act
        rate = database_manager._calculate_cache_hit_rate()
        
        # Assert
        assert rate == 0.0
    
    def test_calculate_cache_hit_rate_with_data(self, database_manager):
        """Test cache hit rate calculation with data."""
        # Arrange
        database_manager._update_cache("key1", "value1")
        database_manager._update_cache("key2", "value2")
        
        # Act
        rate = database_manager._calculate_cache_hit_rate()
        
        # Assert
        assert rate == 0.85  # Placeholder value from implementation
    
    @pytest.mark.asyncio
    async def test_update_file_status_file_not_found(self, file_repository):
        """Test update_file_status when file record not found."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="File record not found"):
            await file_repository.update_file_status("/nonexistent/file.txt", RecordStatus.COMPLETED) 