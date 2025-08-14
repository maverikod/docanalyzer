"""
Tests for Directory Scanner Worker

Comprehensive test suite for directory scanner worker functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import os

from docanalyzer.workers.directory_scanner_worker import (
    WorkerConfig,
    WorkerStatus,
    DirectoryScannerWorker
)
from docanalyzer.models.processing import ProcessingResult
from docanalyzer.models.file_system import FileInfo
from docanalyzer.models.errors import ProcessingError, ErrorCategory


class TestWorkerConfig:
    """Test suite for WorkerConfig class."""
    
    def test_init_valid_config(self):
        """Test valid configuration initialization."""
        config = WorkerConfig(
            scan_timeout=300,
            batch_size=25,
            progress_interval=5,
            enable_detailed_logging=False,
            enable_progress_reports=False,
            max_retry_attempts=5
        )
        
        assert config.scan_timeout == 300
        assert config.batch_size == 25
        assert config.progress_interval == 5
        assert config.enable_detailed_logging is False
        assert config.enable_progress_reports is False
        assert config.max_retry_attempts == 5
    
    def test_init_defaults(self):
        """Test configuration initialization with defaults."""
        config = WorkerConfig()
        
        assert config.scan_timeout == 600
        assert config.batch_size == 50
        assert config.progress_interval == 10
        assert config.enable_detailed_logging is True
        assert config.enable_progress_reports is True
        assert config.max_retry_attempts == 3
    
    def test_init_invalid_scan_timeout(self):
        """Test configuration with invalid scan timeout."""
        with pytest.raises(ValueError, match="scan_timeout must be positive"):
            WorkerConfig(scan_timeout=0)
    
    def test_init_invalid_batch_size(self):
        """Test configuration with invalid batch size."""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            WorkerConfig(batch_size=-1)
    
    def test_init_invalid_progress_interval(self):
        """Test configuration with invalid progress interval."""
        with pytest.raises(ValueError, match="progress_interval must be positive"):
            WorkerConfig(progress_interval=0)
    
    def test_init_invalid_max_retry_attempts(self):
        """Test configuration with invalid max retry attempts."""
        with pytest.raises(ValueError, match="max_retry_attempts must be non-negative"):
            WorkerConfig(max_retry_attempts=-1)


class TestWorkerStatus:
    """Test suite for WorkerStatus class."""
    
    def test_init_valid_status(self):
        """Test valid status initialization."""
        start_time = datetime.now()
        status = WorkerStatus(
            worker_id=12345,
            status="scanning",
            directory_path="/test/directory",
            files_found=100,
            files_processed=50,
            files_failed=2,
            start_time=start_time,
            progress_percentage=50.0,
            error_message="Test error"
        )
        
        assert status.worker_id == 12345
        assert status.status == "scanning"
        assert status.directory_path == "/test/directory"
        assert status.files_found == 100
        assert status.files_processed == 50
        assert status.files_failed == 2
        assert status.start_time == start_time
        assert status.progress_percentage == 50.0
        assert status.error_message == "Test error"
    
    def test_init_defaults(self):
        """Test status initialization with defaults."""
        status = WorkerStatus(
            worker_id=12345,
            status="idle",
            directory_path="/test/directory"
        )
        
        assert status.files_found == 0
        assert status.files_processed == 0
        assert status.files_failed == 0
        assert status.progress_percentage == 0.0
        assert status.error_message is None
        assert isinstance(status.start_time, datetime)
        assert isinstance(status.last_activity, datetime)
    
    def test_init_progress_percentage_clamping(self):
        """Test progress percentage clamping."""
        status = WorkerStatus(
            worker_id=12345,
            status="processing",
            directory_path="/test/directory",
            progress_percentage=150.0  # Should be clamped to 100.0
        )
        
        assert status.progress_percentage == 100.0
        
        status2 = WorkerStatus(
            worker_id=12345,
            status="processing",
            directory_path="/test/directory",
            progress_percentage=-10.0  # Should be clamped to 0.0
        )
        
        assert status2.progress_percentage == 0.0
    
    def test_to_dict(self):
        """Test status to dictionary conversion."""
        start_time = datetime.now()
        status = WorkerStatus(
            worker_id=12345,
            status="scanning",
            directory_path="/test/directory",
            files_found=100,
            files_processed=50,
            start_time=start_time
        )
        
        data = status.to_dict()
        
        assert data["worker_id"] == 12345
        assert data["status"] == "scanning"
        assert data["directory_path"] == "/test/directory"
        assert data["files_found"] == 100
        assert data["files_processed"] == 50
        assert data["files_failed"] == 0
        assert data["progress_percentage"] == 0.0
        assert data["error_message"] is None
        assert "start_time" in data
        assert "last_activity" in data
    
    def test_from_dict_valid(self):
        """Test creating status from valid dictionary."""
        start_time = datetime.now()
        data = {
            "worker_id": 12345,
            "status": "scanning",
            "directory_path": "/test/directory",
            "files_found": 100,
            "files_processed": 50,
            "files_failed": 2,
            "start_time": start_time.isoformat(),
            "last_activity": start_time.isoformat(),
            "progress_percentage": 50.0,
            "error_message": "Test error"
        }
        
        status = WorkerStatus.from_dict(data)
        
        assert status.worker_id == 12345
        assert status.status == "scanning"
        assert status.directory_path == "/test/directory"
        assert status.files_found == 100
        assert status.files_processed == 50
        assert status.files_failed == 2
        assert status.progress_percentage == 50.0
        assert status.error_message == "Test error"
    
    def test_from_dict_missing_field(self):
        """Test creating status from dictionary with missing field."""
        data = {
            "worker_id": 12345,
            # Missing status and directory_path
        }
        
        with pytest.raises(ValueError, match="Required field 'status' missing"):
            WorkerStatus.from_dict(data)
    
    def test_from_dict_invalid_type(self):
        """Test creating status from invalid data type."""
        with pytest.raises(ValueError, match="data must be dictionary"):
            WorkerStatus.from_dict("invalid")


class TestDirectoryScannerWorker:
    """Test suite for DirectoryScannerWorker class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return WorkerConfig(
            scan_timeout=60,
            batch_size=10,
            progress_interval=2
        )
    
    @pytest.fixture
    def worker(self, config):
        """Create test worker instance."""
        with patch('docanalyzer.workers.directory_scanner_worker.DirectoryScanner'), \
             patch('docanalyzer.workers.directory_scanner_worker.LockManager'), \
             patch('docanalyzer.workers.directory_scanner_worker.FileProcessor'), \
             patch('docanalyzer.workers.directory_scanner_worker.ChunkingManager'), \
             patch('docanalyzer.workers.directory_scanner_worker.ProcessCommunication') as mock_comm, \
             patch('docanalyzer.workers.directory_scanner_worker.ProcessCommunicationConfig'), \
             patch('docanalyzer.filters.file_filter.FileFilter'):
            
            # Mock async methods in communication
            mock_comm.return_value.start_heartbeat = AsyncMock()
            mock_comm.return_value.stop_heartbeat = AsyncMock()
            mock_comm.return_value.cleanup = AsyncMock()
            mock_comm.return_value.send_result = AsyncMock()
            mock_comm.return_value.send_status_update = AsyncMock()
            
            return DirectoryScannerWorker(config)
    
    def test_init_valid_worker(self, config):
        """Test valid worker initialization."""
        with patch('docanalyzer.workers.directory_scanner_worker.DirectoryScanner'), \
             patch('docanalyzer.workers.directory_scanner_worker.LockManager'), \
             patch('docanalyzer.workers.directory_scanner_worker.FileProcessor'), \
             patch('docanalyzer.workers.directory_scanner_worker.ChunkingManager'), \
             patch('docanalyzer.workers.directory_scanner_worker.ProcessCommunication') as mock_comm, \
             patch('docanalyzer.workers.directory_scanner_worker.ProcessCommunicationConfig'), \
             patch('docanalyzer.filters.file_filter.FileFilter'):
            
            # Mock async methods in communication
            mock_comm.return_value.start_heartbeat = AsyncMock()
            mock_comm.return_value.stop_heartbeat = AsyncMock()
            mock_comm.return_value.cleanup = AsyncMock()
            mock_comm.return_value.send_result = AsyncMock()
            mock_comm.return_value.send_status_update = AsyncMock()
            
            worker = DirectoryScannerWorker(config)
            
            assert worker.config == config
            assert worker.worker_id > 0
            assert worker._scanning is False
            assert worker._paused is False
    
    def test_init_invalid_config(self):
        """Test worker initialization with invalid config."""
        with pytest.raises(ValueError, match="config must be WorkerConfig instance"):
            DirectoryScannerWorker("invalid_config")
    
    @pytest.mark.asyncio
    async def test_start_scanning_success(self, worker, tmp_path):
        """Test successful scanning start."""
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()
        
        # Create some test files
        (test_dir / "test1.txt").write_text("Test content 1")
        (test_dir / "test2.md").write_text("Test content 2")
        
        with patch.object(worker, '_scan_directory') as mock_scan, \
             patch.object(worker, '_process_files') as mock_process, \
             patch.object(worker.communication, 'start_heartbeat', new_callable=AsyncMock) as mock_start_heartbeat, \
             patch.object(worker.communication, 'stop_heartbeat', new_callable=AsyncMock) as mock_stop_heartbeat, \
             patch.object(worker.communication, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
            
            mock_scan.return_value = [
                FileInfo(file_path=str(test_dir / "test1.txt"), file_size=100, modification_time=datetime.now()),
                FileInfo(file_path=str(test_dir / "test2.md"), file_size=200, modification_time=datetime.now())
            ]
            mock_process.return_value = ProcessingResult(
                success=True,
                message="Processing completed successfully",
                data={"processed_files": 2}
            )
            
            result = await worker.start_scanning(str(test_dir))
            
            assert result.success is True
            assert "Processing completed successfully" in result.message
            assert worker.status.status == "completed"
            assert worker.status.files_found == 2
            mock_start_heartbeat.assert_called_once()
            mock_stop_heartbeat.assert_called_once()
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_scanning_directory_not_found(self, worker):
        """Test scanning with non-existent directory."""
        with patch('os.path.exists', return_value=False):
            result = await worker.start_scanning("/nonexistent/directory")
            
            assert result.success is False
            assert "Directory not found" in result.message
            assert worker.status.status == "failed"
    
    @pytest.mark.asyncio
    async def test_start_scanning_already_scanning(self, worker):
        """Test starting scanning when already scanning."""
        worker._scanning = True
        
        result = await worker.start_scanning("/test/directory")
        
        assert result.success is False
        assert "Scanning already in progress" in result.message
    
    @pytest.mark.asyncio
    async def test_start_scanning_cancelled(self, worker, tmp_path):
        """Test scanning cancellation."""
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()
        
        with patch.object(worker, '_scan_directory') as mock_scan, \
             patch.object(worker.communication, 'start_heartbeat', new_callable=AsyncMock), \
             patch.object(worker.communication, 'stop_heartbeat', new_callable=AsyncMock), \
             patch.object(worker.communication, 'cleanup', new_callable=AsyncMock):
            
            # Set shutdown event to simulate cancellation
            worker._shutdown_event.set()
            mock_scan.return_value = []
            
            result = await worker.start_scanning(str(test_dir))
            
            assert result.success is False
            assert "Scanning cancelled" in result.message
    
    @pytest.mark.asyncio
    async def test_stop_scanning_success(self, worker):
        """Test successful scanning stop."""
        worker._scanning = True
        
        with patch.object(worker.communication, 'stop_heartbeat', new_callable=AsyncMock) as mock_stop, \
             patch.object(worker.communication, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
            
            result = await worker.stop_scanning()
            
            assert result is True
            assert worker._scanning is False
            assert worker.status.status == "stopped"
            mock_stop.assert_called_once()
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_scanning_not_scanning(self, worker):
        """Test stopping when not scanning."""
        result = await worker.stop_scanning()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_status(self, worker):
        """Test getting worker status."""
        worker.status.files_found = 100
        worker.status.files_processed = 50
        
        status = await worker.get_status()
        
        assert status.worker_id == worker.worker_id
        assert status.files_found == 100
        assert status.files_processed == 50
        assert status.progress_percentage == 50.0
        assert isinstance(status.last_activity, datetime)
    
    @pytest.mark.asyncio
    async def test_pause_scanning(self, worker):
        """Test pausing scanning."""
        worker._scanning = True
        
        result = await worker.pause_scanning()
        
        assert result is True
        assert worker._paused is True
    
    @pytest.mark.asyncio
    async def test_pause_scanning_not_scanning(self, worker):
        """Test pausing when not scanning."""
        result = await worker.pause_scanning()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_resume_scanning(self, worker):
        """Test resuming scanning."""
        worker._scanning = True
        worker._paused = True
        
        result = await worker.resume_scanning()
        
        assert result is True
        assert worker._paused is False
    
    @pytest.mark.asyncio
    async def test_resume_scanning_not_scanning(self, worker):
        """Test resuming when not scanning."""
        result = await worker.resume_scanning()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_scan_directory_success(self, worker, tmp_path):
        """Test successful directory scanning."""
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()
        (test_dir / "test.txt").write_text("Test content")
        
        with patch.object(worker.directory_scanner, 'scan_directory', new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = type('obj', (object,), {
                'files': [FileInfo(file_path=str(test_dir / "test.txt"), file_size=100, modification_time=datetime.now())]
            })()
            
            files = await worker._scan_directory(str(test_dir))
            
            assert len(files) == 1
            assert files[0].file_path == str(test_dir / "test.txt")
            mock_scan.assert_called_once_with(str(test_dir))
    
    @pytest.mark.asyncio
    async def test_scan_directory_error(self, worker):
        """Test directory scanning error."""
        with patch.object(worker.directory_scanner, 'scan_directory', new_callable=AsyncMock, side_effect=Exception("Scan error")):
            with pytest.raises(ProcessingError):
                await worker._scan_directory("/test/directory")
    
    @pytest.mark.asyncio
    async def test_process_files_success(self, worker):
        """Test successful file processing."""
        with patch('docanalyzer.models.file_system.file_info.os.path.exists', return_value=True):
            files = [
                FileInfo(file_path="/test/file1.txt", file_size=100, modification_time=datetime.now()),
                FileInfo(file_path="/test/file2.md", file_size=200, modification_time=datetime.now())
            ]
        
        with patch.object(worker, '_process_file_batch') as mock_batch, \
             patch.object(worker, '_update_progress', new_callable=AsyncMock) as mock_update, \
             patch.object(worker.communication, 'send_result', new_callable=AsyncMock) as mock_send:
            
            mock_batch.return_value = {"processed": 1, "failed": 0}
            mock_send.return_value = True
            
            result = await worker._process_files(files)
            
            assert result.success is True
            assert mock_batch.call_count == 1  # One batch (2 files, batch_size=10)
            assert mock_update.call_count == 1
            assert mock_send.call_count == 1
    
    @pytest.mark.asyncio
    async def test_process_files_error(self, worker):
        """Test file processing error."""
        with patch('docanalyzer.models.file_system.file_info.os.path.exists', return_value=True):
            files = [FileInfo(file_path="/test/file.txt", file_size=100, modification_time=datetime.now())]
        
        with patch.object(worker, '_process_file_batch', side_effect=Exception("Processing error")):
            with pytest.raises(ProcessingError):
                await worker._process_files(files)
    
    @pytest.mark.asyncio
    async def test_process_file_batch_success(self, worker):
        """Test successful file batch processing."""
        with patch('docanalyzer.models.file_system.file_info.os.path.exists', return_value=True):
            batch = [
                FileInfo(file_path="/test/file1.txt", file_size=100, modification_time=datetime.now()),
                FileInfo(file_path="/test/file2.txt", file_size=200, modification_time=datetime.now())
            ]
        
        with patch.object(worker.file_processor, 'process_file', new_callable=AsyncMock) as mock_process, \
             patch.object(worker.chunking_manager, 'process_blocks', new_callable=AsyncMock) as mock_chunk:
            
            mock_process.return_value = ProcessingResult(success=True, message="Processed", data={"blocks": ["block1", "block2"]})
            mock_chunk.return_value = ProcessingResult(success=True, message="Chunked")
            
            result = await worker._process_file_batch(batch)
            
            assert result["processed"] == 2
            assert result["failed"] == 0
            assert mock_process.call_count == 2
            assert mock_chunk.call_count == 2
    
    @pytest.mark.asyncio
    async def test_process_file_batch_partial_failure(self, worker):
        """Test file batch processing with partial failures."""
        with patch('docanalyzer.models.file_system.file_info.os.path.exists', return_value=True):
            batch = [
                FileInfo(file_path="/test/file1.txt", file_size=100, modification_time=datetime.now()),
                FileInfo(file_path="/test/file2.txt", file_size=200, modification_time=datetime.now())
            ]
        
        with patch.object(worker.file_processor, 'process_file', new_callable=AsyncMock) as mock_process, \
             patch.object(worker.chunking_manager, 'process_blocks', new_callable=AsyncMock) as mock_chunk:
            
            # First file succeeds, second fails
            mock_process.side_effect = [
                ProcessingResult(success=True, message="Processed", data={"blocks": ["block1", "block2"]}),
                ProcessingResult(success=False, message="Failed")
            ]
            mock_chunk.return_value = ProcessingResult(success=True, message="Chunked")
            
            result = await worker._process_file_batch(batch)
            
            assert result["processed"] == 1
            assert result["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_update_progress(self, worker):
        """Test progress update."""
        with patch.object(worker, '_send_status_update', new_callable=AsyncMock) as mock_send:
            await worker._update_progress(50, 100)
            
            assert worker.status.files_processed == 50
            assert worker.status.progress_percentage == 50.0
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_status_update(self, worker):
        """Test sending status update."""
        with patch.object(worker.communication, 'send_status_update', new_callable=AsyncMock) as mock_send:
            await worker._send_status_update()
            
            mock_send.assert_called_once()
            # Verify the status data structure
            call_args = mock_send.call_args[0][0]
            assert "worker_id" in call_args
            assert "status" in call_args
            assert "directory_path" in call_args
    
    @pytest.mark.asyncio
    async def test_handle_signal(self, worker):
        """Test signal handling."""
        with patch.object(worker, 'stop_scanning', new_callable=AsyncMock) as mock_stop, \
             patch.object(worker, '_cleanup_resources', new_callable=AsyncMock) as mock_cleanup, \
             patch('sys.exit'):
            await worker._handle_signal(2, None)  # SIGINT
            
            mock_stop.assert_called_once()
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_resources(self, worker):
        """Test resource cleanup."""
        with patch.object(worker.communication, 'cleanup', new_callable=AsyncMock) as mock_cleanup:
            await worker._cleanup_resources()
            
            mock_cleanup.assert_called_once()


def test_main():
    """Test main entry point."""
    with patch('docanalyzer.workers.directory_scanner_worker.DirectoryScannerWorker'), \
         patch('docanalyzer.workers.directory_scanner_worker.WorkerConfig'), \
         patch('asyncio.run'):
        
        from docanalyzer.workers.directory_scanner_worker import main
        main()  # Should not raise any exceptions 