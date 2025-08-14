"""
Tests for Directory Processing Orchestrator

Comprehensive test suite for directory processing orchestration functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import os
from typing import List, Dict, Any

from docanalyzer.services.directory_orchestrator import (
    DirectoryOrchestrator,
    OrchestratorConfig,
    DirectoryProcessingStatus,
    OrchestrationResult
)
from docanalyzer.models.file_system import FileInfo
from docanalyzer.models.processing import ProcessingResult
from docanalyzer.models.errors import ProcessingError, ErrorCategory


class TestOrchestratorConfig:
    """Test suite for OrchestratorConfig class."""
    
    def test_init_valid_config(self):
        """Test valid configuration initialization."""
        config = OrchestratorConfig(
            max_concurrent_directories=3,
            processing_timeout=1800,
            retry_attempts=2,
            enable_parallel_processing=False,
            enable_progress_tracking=False,
            enable_error_recovery=False,
            enable_cleanup_on_failure=False
        )
        
        assert config.max_concurrent_directories == 3
        assert config.processing_timeout == 1800
        assert config.retry_attempts == 2
        assert config.enable_parallel_processing is False
        assert config.enable_progress_tracking is False
        assert config.enable_error_recovery is False
        assert config.enable_cleanup_on_failure is False
    
    def test_init_defaults(self):
        """Test configuration initialization with defaults."""
        config = OrchestratorConfig()
        
        assert config.max_concurrent_directories == 5
        assert config.processing_timeout == 3600
        assert config.retry_attempts == 3
        assert config.enable_parallel_processing is True
        assert config.enable_progress_tracking is True
        assert config.enable_error_recovery is True
        assert config.enable_cleanup_on_failure is True
    
    def test_init_invalid_max_concurrent_directories(self):
        """Test initialization with invalid max_concurrent_directories."""
        with pytest.raises(ValueError, match="max_concurrent_directories must be positive"):
            OrchestratorConfig(max_concurrent_directories=0)
    
    def test_init_invalid_processing_timeout(self):
        """Test initialization with invalid processing_timeout."""
        with pytest.raises(ValueError, match="processing_timeout must be positive"):
            OrchestratorConfig(processing_timeout=0)
    
    def test_init_invalid_retry_attempts(self):
        """Test initialization with invalid retry_attempts."""
        with pytest.raises(ValueError, match="retry_attempts must be non-negative"):
            OrchestratorConfig(retry_attempts=-1)


class TestDirectoryProcessingStatus:
    """Test suite for DirectoryProcessingStatus class."""
    
    def test_init_valid_status(self):
        """Test valid status initialization."""
        start_time = datetime.now()
        status = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="scanning",
            files_found=100,
            files_processed=50,
            files_failed=2,
            chunks_created=25,
            start_time=start_time,
            progress_percentage=50.0,
            error_message="Test error",
            processing_time=30.5
        )
        
        assert status.directory_path == "/test/directory"
        assert status.status == "scanning"
        assert status.files_found == 100
        assert status.files_processed == 50
        assert status.files_failed == 2
        assert status.chunks_created == 25
        assert status.start_time == start_time
        assert status.progress_percentage == 50.0
        assert status.error_message == "Test error"
        assert status.processing_time == 30.5
    
    def test_init_defaults(self):
        """Test status initialization with defaults."""
        status = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="pending"
        )
        
        assert status.files_found == 0
        assert status.files_processed == 0
        assert status.files_failed == 0
        assert status.chunks_created == 0
        assert status.progress_percentage == 0.0
        assert status.error_message is None
        assert status.processing_time == 0.0
        assert isinstance(status.start_time, datetime)
        assert isinstance(status.last_activity, datetime)
    
    def test_init_progress_percentage_clamping(self):
        """Test progress percentage clamping."""
        status = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="processing",
            progress_percentage=150.0  # Should be clamped to 100.0
        )
        
        assert status.progress_percentage == 100.0
        
        status2 = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="processing",
            progress_percentage=-10.0  # Should be clamped to 0.0
        )
        
        assert status2.progress_percentage == 0.0
    
    def test_to_dict(self):
        """Test status to dictionary conversion."""
        start_time = datetime.now()
        status = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="scanning",
            files_found=100,
            files_processed=50,
            start_time=start_time
        )
        
        data = status.to_dict()
        
        assert data["directory_path"] == "/test/directory"
        assert data["status"] == "scanning"
        assert data["files_found"] == 100
        assert data["files_processed"] == 50
        assert data["files_failed"] == 0
        assert data["chunks_created"] == 0
        assert data["progress_percentage"] == 0.0
        assert data["error_message"] is None
        assert data["processing_time"] == 0.0
        assert "start_time" in data
        assert "last_activity" in data
    
    def test_from_dict_valid(self):
        """Test creating status from valid dictionary."""
        start_time = datetime.now()
        data = {
            "directory_path": "/test/directory",
            "status": "scanning",
            "files_found": 100,
            "files_processed": 50,
            "files_failed": 2,
            "chunks_created": 25,
            "start_time": start_time.isoformat(),
            "last_activity": start_time.isoformat(),
            "progress_percentage": 50.0,
            "error_message": "Test error",
            "processing_time": 30.5
        }
        
        status = DirectoryProcessingStatus.from_dict(data)
        
        assert status.directory_path == "/test/directory"
        assert status.status == "scanning"
        assert status.files_found == 100
        assert status.files_processed == 50
        assert status.files_failed == 2
        assert status.chunks_created == 25
        assert status.progress_percentage == 50.0
        assert status.error_message == "Test error"
        assert status.processing_time == 30.5
    
    def test_from_dict_missing_field(self):
        """Test creating status from dictionary with missing field."""
        data = {
            "directory_path": "/test/directory",
            # Missing status
        }
        
        with pytest.raises(ValueError, match="Required field 'status' missing"):
            DirectoryProcessingStatus.from_dict(data)
    
    def test_from_dict_invalid_type(self):
        """Test creating status from invalid data type."""
        with pytest.raises(ValueError, match="data must be dictionary"):
            DirectoryProcessingStatus.from_dict("invalid")


class TestOrchestrationResult:
    """Test suite for OrchestrationResult class."""
    
    def test_init_valid_result(self):
        """Test valid result initialization."""
        status_updates = [
            DirectoryProcessingStatus("/test/dir", "pending"),
            DirectoryProcessingStatus("/test/dir", "completed")
        ]
        
        result = OrchestrationResult(
            success=True,
            directory_path="/test/directory",
            files_processed=50,
            files_failed=2,
            chunks_created=25,
            processing_time=30.5,
            error_message=None,
            status_updates=status_updates,
            metadata={"test": "data"}
        )
        
        assert result.success is True
        assert result.directory_path == "/test/directory"
        assert result.files_processed == 50
        assert result.files_failed == 2
        assert result.chunks_created == 25
        assert result.processing_time == 30.5
        assert result.error_message is None
        assert len(result.status_updates) == 2
        assert result.metadata["test"] == "data"
    
    def test_init_defaults(self):
        """Test result initialization with defaults."""
        result = OrchestrationResult(
            success=False,
            directory_path="/test/directory"
        )
        
        assert result.files_processed == 0
        assert result.files_failed == 0
        assert result.chunks_created == 0
        assert result.processing_time == 0.0
        assert result.error_message is None
        assert len(result.status_updates) == 0
        assert len(result.metadata) == 0
    
    def test_to_dict(self):
        """Test result to dictionary conversion."""
        status_updates = [DirectoryProcessingStatus("/test/dir", "completed")]
        
        result = OrchestrationResult(
            success=True,
            directory_path="/test/directory",
            files_processed=50,
            files_failed=2,
            chunks_created=25,
            processing_time=30.5,
            status_updates=status_updates,
            metadata={"test": "data"}
        )
        
        data = result.to_dict()
        
        assert data["success"] is True
        assert data["directory_path"] == "/test/directory"
        assert data["files_processed"] == 50
        assert data["files_failed"] == 2
        assert data["chunks_created"] == 25
        assert data["processing_time"] == 30.5
        assert data["error_message"] is None
        assert len(data["status_updates"]) == 1
        assert data["metadata"]["test"] == "data"


class TestDirectoryOrchestrator:
    """Test suite for DirectoryOrchestrator class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return OrchestratorConfig(
            max_concurrent_directories=2,
            processing_timeout=300,
            retry_attempts=1
        )
    
    @pytest.fixture
    def orchestrator(self, config):
        """Create test orchestrator instance."""
        with patch('docanalyzer.services.directory_orchestrator.LockManager'), \
             patch('docanalyzer.services.directory_orchestrator.DirectoryScanner'), \
             patch('docanalyzer.services.directory_orchestrator.FileProcessor'), \
             patch('docanalyzer.services.directory_orchestrator.ChunkingManager'), \
             patch('docanalyzer.services.directory_orchestrator.DatabaseManager'), \
             patch('docanalyzer.services.directory_orchestrator.VectorStoreWrapper'), \
             patch('docanalyzer.services.directory_orchestrator.MainProcessManager'), \
             patch('docanalyzer.services.directory_orchestrator.ChildProcessManager'):
            
            return DirectoryOrchestrator(config)
    
    def test_init_valid_orchestrator(self, config):
        """Test valid orchestrator initialization."""
        with patch('docanalyzer.services.directory_orchestrator.LockManager'), \
             patch('docanalyzer.services.directory_orchestrator.DirectoryScanner'), \
             patch('docanalyzer.services.directory_orchestrator.FileProcessor'), \
             patch('docanalyzer.services.directory_orchestrator.ChunkingManager'), \
             patch('docanalyzer.services.directory_orchestrator.DatabaseManager'), \
             patch('docanalyzer.services.directory_orchestrator.VectorStoreWrapper'), \
             patch('docanalyzer.services.directory_orchestrator.MainProcessManager'), \
             patch('docanalyzer.services.directory_orchestrator.ChildProcessManager'):
            
            orchestrator = DirectoryOrchestrator(config)
            
            assert orchestrator.config == config
            assert len(orchestrator.active_directories) == 0
            assert orchestrator._processing is False
    
    def test_init_invalid_config(self):
        """Test orchestrator initialization with invalid config."""
        with pytest.raises(ValueError, match="config must be OrchestratorConfig instance"):
            DirectoryOrchestrator("invalid")
    
    @pytest.mark.asyncio
    async def test_process_directory_success(self, orchestrator, tmp_path):
        """Test successful directory processing."""
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()
        
        # Create some test files
        (test_dir / "test1.txt").write_text("Test content 1")
        (test_dir / "test2.md").write_text("Test content 2")
        
        with patch.object(orchestrator, '_scan_directory') as mock_scan, \
             patch.object(orchestrator, '_process_files') as mock_process, \
             patch.object(orchestrator, '_create_chunks') as mock_chunk, \
             patch.object(orchestrator, '_store_results') as mock_store, \
             patch.object(orchestrator, '_update_status') as mock_update:
            
            mock_scan.return_value = [
                FileInfo(file_path=str(test_dir / "test1.txt"), file_size=100, modification_time=datetime.now()),
                FileInfo(file_path=str(test_dir / "test2.md"), file_size=200, modification_time=datetime.now())
            ]
            def mock_process_files(files, directory_path):
                # Update status with processed files
                if directory_path in orchestrator.active_directories:
                    orchestrator.active_directories[directory_path].files_processed = 2
                    orchestrator.active_directories[directory_path].files_failed = 0
                return ProcessingResult(
                    success=True,
                    message="Processing completed successfully",
                    data={"processed_files": 2}
                )
            
            mock_process.side_effect = mock_process_files
            mock_chunk.return_value = ProcessingResult(
                success=True,
                message="Chunking completed successfully",
                data={"chunks_created": 4}
            )
            def mock_store_results(chunking_result, directory_path):
                # Update status with chunks created
                if directory_path in orchestrator.active_directories:
                    orchestrator.active_directories[directory_path].chunks_created = 4
                return True
            
            mock_store.side_effect = mock_store_results
            
            # Mock _update_status to actually update the status
            def mock_update_status(directory_path, status, **kwargs):
                if directory_path in orchestrator.active_directories:
                    orchestrator.active_directories[directory_path].status = status
                    for key, value in kwargs.items():
                        setattr(orchestrator.active_directories[directory_path], key, value)
            
            mock_update.side_effect = mock_update_status
            
            result = await orchestrator.process_directory(str(test_dir))
            
            assert result.success is True
            assert result.directory_path == str(test_dir)
            assert result.files_processed == 2  # Updated by _process_files
            assert result.chunks_created == 4
            assert len(result.status_updates) > 0
            mock_scan.assert_called_once_with(str(test_dir))
            mock_process.assert_called_once()
            mock_chunk.assert_called_once()
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_directory_not_found(self, orchestrator):
        """Test processing non-existent directory."""
        with patch('os.path.exists', return_value=False):
            result = await orchestrator.process_directory("/nonexistent/directory")
            
            assert result.success is False
            assert "Directory not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_process_directory_already_processing(self, orchestrator, tmp_path):
        """Test processing directory that is already being processed."""
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()
        
        # Add directory to active directories
        orchestrator.active_directories[str(test_dir)] = DirectoryProcessingStatus(
            directory_path=str(test_dir),
            status="scanning"
        )
        
        with patch('os.path.exists', return_value=True):
            result = await orchestrator.process_directory(str(test_dir))
            
            assert result.success is False
            assert "already being processed" in result.error_message
    
    @pytest.mark.asyncio
    async def test_process_directory_no_files(self, orchestrator, tmp_path):
        """Test processing directory with no files."""
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()
        
        with patch.object(orchestrator, '_scan_directory', return_value=[]), \
             patch.object(orchestrator, '_update_status') as mock_update:
            
            result = await orchestrator.process_directory(str(test_dir))
            
            assert result.success is True
            assert result.directory_path == str(test_dir)
            assert result.files_processed == 0
            assert result.chunks_created == 0
    
    @pytest.mark.asyncio
    async def test_process_multiple_directories(self, orchestrator, tmp_path):
        """Test processing multiple directories."""
        test_dir1 = tmp_path / "test_directory1"
        test_dir2 = tmp_path / "test_directory2"
        test_dir1.mkdir()
        test_dir2.mkdir()
        
        with patch.object(orchestrator, 'process_directory') as mock_process:
            mock_process.return_value = OrchestrationResult(
                success=True,
                directory_path="test",
                files_processed=10
            )
            
            results = await orchestrator.process_multiple_directories([
                str(test_dir1),
                str(test_dir2)
            ])
            
            assert len(results) == 2
            assert all(result.success for result in results)
            assert mock_process.call_count == 2
    
    @pytest.mark.asyncio
    async def test_process_multiple_directories_empty_list(self, orchestrator):
        """Test processing empty directory list."""
        with pytest.raises(ValueError, match="directory_paths cannot be empty"):
            await orchestrator.process_multiple_directories([])
    
    @pytest.mark.asyncio
    async def test_process_multiple_directories_invalid_type(self, orchestrator):
        """Test processing invalid directory list type."""
        with pytest.raises(ValueError, match="directory_paths must be a list"):
            await orchestrator.process_multiple_directories("invalid")
    
    @pytest.mark.asyncio
    async def test_get_processing_status(self, orchestrator):
        """Test getting processing status."""
        status = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="scanning"
        )
        orchestrator.active_directories["/test/directory"] = status
        
        result = await orchestrator.get_processing_status("/test/directory")
        
        assert result == status
    
    @pytest.mark.asyncio
    async def test_get_processing_status_not_found(self, orchestrator):
        """Test getting status for non-existent directory."""
        result = await orchestrator.get_processing_status("/nonexistent/directory")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_processing_status_invalid_path(self, orchestrator):
        """Test getting status with invalid path."""
        with pytest.raises(ValueError, match="directory_path cannot be empty"):
            await orchestrator.get_processing_status("")
    
    @pytest.mark.asyncio
    async def test_get_all_processing_status(self, orchestrator):
        """Test getting all processing statuses."""
        status1 = DirectoryProcessingStatus("/test/dir1", "scanning")
        status2 = DirectoryProcessingStatus("/test/dir2", "processing")
        
        orchestrator.active_directories["/test/dir1"] = status1
        orchestrator.active_directories["/test/dir2"] = status2
        
        results = await orchestrator.get_all_processing_status()
        
        assert len(results) == 2
        assert status1 in results
        assert status2 in results
    
    @pytest.mark.asyncio
    async def test_cancel_processing(self, orchestrator):
        """Test cancelling processing."""
        status = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="scanning"
        )
        orchestrator.active_directories["/test/directory"] = status
        
        with patch.object(orchestrator, '_update_status') as mock_update, \
             patch.object(orchestrator, '_cleanup_resources') as mock_cleanup:
            
            result = await orchestrator.cancel_processing("/test/directory")
            
            assert result is True
            assert "/test/directory" not in orchestrator.active_directories
            mock_update.assert_called_once_with("/test/directory", "cancelled")
            mock_cleanup.assert_called_once_with("/test/directory")
    
    @pytest.mark.asyncio
    async def test_cancel_processing_not_found(self, orchestrator):
        """Test cancelling processing for non-existent directory."""
        result = await orchestrator.cancel_processing("/nonexistent/directory")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cancel_processing_invalid_path(self, orchestrator):
        """Test cancelling processing with invalid path."""
        with pytest.raises(ValueError, match="directory_path cannot be empty"):
            await orchestrator.cancel_processing("")
    
    @pytest.mark.asyncio
    async def test_stop_all_processing(self, orchestrator):
        """Test stopping all processing."""
        status1 = DirectoryProcessingStatus("/test/dir1", "scanning")
        status2 = DirectoryProcessingStatus("/test/dir2", "processing")
        
        orchestrator.active_directories["/test/dir1"] = status1
        orchestrator.active_directories["/test/dir2"] = status2
        
        with patch.object(orchestrator, 'cancel_processing', return_value=True) as mock_cancel:
            result = await orchestrator.stop_all_processing()
            
            assert result is True
            assert mock_cancel.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_failed_processing(self, orchestrator):
        """Test retrying failed processing."""
        with patch.object(orchestrator, 'process_directory') as mock_process:
            mock_process.return_value = OrchestrationResult(
                success=True,
                directory_path="/test/directory",
                files_processed=10
            )
            
            result = await orchestrator.retry_failed_processing("/test/directory")
            
            assert result.success is True
            mock_process.assert_called_once_with("/test/directory")
    
    @pytest.mark.asyncio
    async def test_retry_failed_processing_invalid_path(self, orchestrator):
        """Test retrying processing with invalid path."""
        with pytest.raises(ValueError, match="directory_path cannot be empty"):
            await orchestrator.retry_failed_processing("")
    
    @pytest.mark.asyncio
    async def test_retry_failed_processing_in_progress(self, orchestrator):
        """Test retrying processing that is in progress."""
        status = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="scanning"
        )
        orchestrator.active_directories["/test/directory"] = status
        
        with pytest.raises(ProcessingError, match="currently being processed"):
            await orchestrator.retry_failed_processing("/test/directory")
    
    @pytest.mark.asyncio
    async def test_cleanup_processed_directory(self, orchestrator):
        """Test cleaning up processed directory."""
        status = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="completed"
        )
        orchestrator.active_directories["/test/directory"] = status
        
        with patch.object(orchestrator, '_cleanup_resources') as mock_cleanup:
            result = await orchestrator.cleanup_processed_directory("/test/directory")
            
            assert result is True
            assert "/test/directory" not in orchestrator.active_directories
            mock_cleanup.assert_called_once_with("/test/directory")
    
    @pytest.mark.asyncio
    async def test_cleanup_processed_directory_invalid_path(self, orchestrator):
        """Test cleaning up directory with invalid path."""
        with pytest.raises(ValueError, match="directory_path cannot be empty"):
            await orchestrator.cleanup_processed_directory("")
    
    @pytest.mark.asyncio
    async def test_scan_directory(self, orchestrator, tmp_path):
        """Test directory scanning."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("Test content")
        
        with patch.object(orchestrator.directory_scanner, 'scan_directory', new_callable=AsyncMock) as mock_scan:
            # Create list of FileInfo objects
            file_list = [FileInfo(file_path=str(test_file), file_size=100, modification_time=datetime.now())]
            
            # Set up mock to return the list directly
            mock_scan.return_value = file_list
            
            files = await orchestrator._scan_directory("/test/directory")
            
            assert len(files) == 1
            assert files[0].file_path == str(test_file)
            mock_scan.assert_called_once_with("/test/directory")
    
    @pytest.mark.asyncio
    async def test_scan_directory_error(self, orchestrator):
        """Test directory scanning error."""
        with patch.object(orchestrator.directory_scanner, 'scan_directory', side_effect=Exception("Scan error")):
            with pytest.raises(ProcessingError, match="Directory scanning failed"):
                await orchestrator._scan_directory("/test/directory")
    
    @pytest.mark.asyncio
    async def test_process_files(self, orchestrator, tmp_path):
        """Test file processing."""
        test_file1 = tmp_path / "test_file1.txt"
        test_file2 = tmp_path / "test_file2.txt"
        test_file1.write_text("Test content 1")
        test_file2.write_text("Test content 2")
        
        files = [
            FileInfo(file_path=str(test_file1), file_size=100, modification_time=datetime.now()),
            FileInfo(file_path=str(test_file2), file_size=200, modification_time=datetime.now())
        ]
        
        with patch.object(orchestrator.file_processor, 'process_file') as mock_process, \
             patch.object(orchestrator, '_update_status') as mock_update:
            
            async def mock_process_file(file_path):
                from docanalyzer.models.processing import FileProcessingResult, ProcessingStatus
                return FileProcessingResult(
                    file_path=file_path,
                    blocks=[],
                    processing_status=ProcessingStatus.COMPLETED,
                    processing_time_seconds=1.0,
                    error_message=None
                )
            
            mock_process.side_effect = mock_process_file
            
            # Add directory to active directories
            orchestrator.active_directories["/test/directory"] = DirectoryProcessingStatus(
                directory_path="/test/directory",
                status="processing"
            )
            
            result = await orchestrator._process_files(files, "/test/directory")
            
            assert result.success is True
            assert "Processed 2/2 files successfully" in result.message
            assert mock_process.call_count == 2
    
    @pytest.mark.asyncio
    async def test_create_chunks(self, orchestrator):
        """Test chunk creation."""
        processing_result = ProcessingResult(
            success=True,
            message="Processing completed",
            data={"processed_files": 5}
        )
        
        result = await orchestrator._create_chunks(processing_result)
        
        assert result.success is True
        assert "Created 10 chunks" in result.message
        assert result.data["chunks_created"] == 10
    
    @pytest.mark.asyncio
    async def test_store_results(self, orchestrator):
        """Test result storage."""
        chunking_result = ProcessingResult(
            success=True,
            message="Chunking completed",
            data={"chunks_created": 10}
        )
        
        # Add directory to active directories
        orchestrator.active_directories["/test/directory"] = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="processing"
        )
        
        result = await orchestrator._store_results(chunking_result, "/test/directory")
        
        assert result is True
        assert orchestrator.active_directories["/test/directory"].chunks_created == 10
    
    @pytest.mark.asyncio
    async def test_update_status(self, orchestrator):
        """Test status update."""
        status = DirectoryProcessingStatus(
            directory_path="/test/directory",
            status="pending"
        )
        orchestrator.active_directories["/test/directory"] = status
        
        await orchestrator._update_status("/test/directory", "scanning", files_found=10)
        
        updated_status = orchestrator.active_directories["/test/directory"]
        assert updated_status.status == "scanning"
        assert updated_status.files_found == 10
        assert updated_status.last_activity is not None
    
    @pytest.mark.asyncio
    async def test_handle_processing_error(self, orchestrator):
        """Test processing error handling."""
        with patch.object(orchestrator, '_update_status') as mock_update:
            error = FileNotFoundError("Directory not found")
            
            await orchestrator._handle_processing_error("/test/directory", error)
            
            mock_update.assert_called_once_with("/test/directory", "failed", error_message="Directory not found")
    
    @pytest.mark.asyncio
    async def test_cleanup_resources(self, orchestrator):
        """Test resource cleanup."""
        with patch.object(orchestrator.lock_manager, 'remove_lock_by_directory') as mock_remove:
            await orchestrator._cleanup_resources("/test/directory")
            
            mock_remove.assert_called_once_with("/test/directory") 