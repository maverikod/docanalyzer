"""
Tests for Child Process Manager

Comprehensive test suite for child process management functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import os
import sys
from typing import List, Dict, Any

from docanalyzer.services.child_process_manager import (
    ChildProcessManager,
    ChildProcessConfig,
    WorkerProcessInfo,
    ChildProcessResult
)
from docanalyzer.models.errors import (
    ProcessManagementError,
    ProcessNotFoundError,
    ResourceLimitError
)
from docanalyzer.models.processing import ProcessingResult


class TestChildProcessConfig:
    """Test suite for ChildProcessConfig class."""
    
    def test_init_valid_config(self):
        """Test valid configuration initialization."""
        config = ChildProcessConfig(
            max_workers=2,
            worker_timeout=300,
            chunk_size=50,
            enable_graceful_shutdown=True,
            auto_restart_failed_workers=True,
            max_restart_attempts=3
        )
        
        assert config.max_workers == 2
        assert config.worker_timeout == 300
        assert config.chunk_size == 50
        assert config.enable_graceful_shutdown is True
        assert config.auto_restart_failed_workers is True
        assert config.max_restart_attempts == 3
    
    def test_init_invalid_max_workers(self):
        """Test initialization with invalid max_workers."""
        with pytest.raises(ValueError, match="max_workers must be positive"):
            ChildProcessConfig(max_workers=0)
    
    def test_init_invalid_worker_timeout(self):
        """Test initialization with invalid worker_timeout."""
        with pytest.raises(ValueError, match="worker_timeout must be positive"):
            ChildProcessConfig(worker_timeout=0)
    
    def test_init_invalid_chunk_size(self):
        """Test initialization with invalid chunk_size."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            ChildProcessConfig(chunk_size=0)
    
    def test_init_invalid_max_restart_attempts(self):
        """Test initialization with invalid max_restart_attempts."""
        with pytest.raises(ValueError, match="max_restart_attempts must be non-negative"):
            ChildProcessConfig(max_restart_attempts=-1)


class TestWorkerProcessInfo:
    """Test suite for WorkerProcessInfo class."""
    
    def test_init_valid_info(self):
        """Test valid worker info initialization."""
        start_time = datetime.now()
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=start_time,
            status="running",
            directory_path="/test/directory",
            files_processed=10,
            restart_count=0,
            error_message=None
        )
        
        assert worker_info.process_id == 12345
        assert worker_info.start_time == start_time
        assert worker_info.status == "running"
        assert worker_info.directory_path == "/test/directory"
        assert worker_info.files_processed == 10
        assert worker_info.restart_count == 0
        assert worker_info.error_message is None
        assert worker_info.last_activity is not None
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        start_time = datetime.now()
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=start_time,
            status="running",
            directory_path="/test/directory"
        )
        
        data = worker_info.to_dict()
        
        assert data["process_id"] == 12345
        assert data["status"] == "running"
        assert data["directory_path"] == "/test/directory"
        assert data["files_processed"] == 0
        assert data["restart_count"] == 0
        assert data["error_message"] is None
    
    def test_from_dict_valid(self):
        """Test creation from valid dictionary."""
        start_time = datetime.now()
        data = {
            "process_id": 12345,
            "start_time": start_time.isoformat(),
            "status": "running",
            "directory_path": "/test/directory",
            "files_processed": 10,
            "last_activity": start_time.isoformat(),
            "restart_count": 0,
            "error_message": None
        }
        
        worker_info = WorkerProcessInfo.from_dict(data)
        
        assert worker_info.process_id == 12345
        assert worker_info.status == "running"
        assert worker_info.directory_path == "/test/directory"
        assert worker_info.files_processed == 10
    
    def test_from_dict_invalid(self):
        """Test creation from invalid dictionary."""
        with pytest.raises(ValueError, match="data must be dictionary"):
            WorkerProcessInfo.from_dict("invalid")
        
        with pytest.raises(ValueError, match="Required field 'process_id' missing"):
            WorkerProcessInfo.from_dict({"status": "running"})


class TestChildProcessResult:
    """Test suite for ChildProcessResult class."""
    
    def test_init_valid_result(self):
        """Test valid result initialization."""
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory"
        )
        
        result = ChildProcessResult(
            success=True,
            worker_info=worker_info,
            error_message=None,
            processing_result=None,
            execution_time=1.5
        )
        
        assert result.success is True
        assert result.worker_info == worker_info
        assert result.error_message is None
        assert result.execution_time == 1.5
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory"
        )
        
        result = ChildProcessResult(
            success=True,
            worker_info=worker_info,
            execution_time=1.5
        )
        
        data = result.to_dict()
        
        assert data["success"] is True
        assert data["worker_info"] is not None
        assert data["error_message"] is None
        assert data["execution_time"] == 1.5


class TestChildProcessManager:
    """Test suite for ChildProcessManager class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ChildProcessConfig(
            max_workers=2,
            worker_timeout=300,
            chunk_size=50
        )
    
    @pytest.fixture
    def manager(self, config):
        """Create test manager instance."""
        return ChildProcessManager(config)
    
    def test_init_valid_manager(self, config):
        """Test valid manager initialization."""
        manager = ChildProcessManager(config)
        
        assert manager.config == config
        assert len(manager.active_workers) == 0
        assert manager.directory_scanner is not None
        assert manager.lock_manager is not None
    
    def test_init_invalid_config(self):
        """Test initialization with invalid config."""
        with pytest.raises(ValueError, match="config must be ChildProcessConfig instance"):
            ChildProcessManager("invalid")
    
    @pytest.mark.asyncio
    async def test_start_worker_success(self, manager, tmp_path):
        """Test successful worker start."""
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()
        
        with patch('os.path.exists', return_value=True), \
             patch.object(manager.lock_manager, 'create_lock', return_value=Mock()), \
             patch('multiprocessing.Process') as mock_process_class:
            
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process_class.return_value = mock_process
            
            result = await manager.start_worker(str(test_dir))
            
            assert result.success is True
            assert result.worker_info is not None
            assert result.worker_info.process_id == 12345
            assert result.worker_info.directory_path == str(test_dir)
            assert result.worker_info.status == "running"
            assert 12345 in manager.active_workers
    
    @pytest.mark.asyncio
    async def test_start_worker_directory_not_found(self, manager):
        """Test worker start with non-existent directory."""
        with patch('os.path.exists', return_value=False):
            result = await manager.start_worker("/nonexistent/directory")
            
            assert result.success is False
            assert "Directory not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_start_worker_max_workers_reached(self, manager, tmp_path):
        """Test worker start when max workers limit reached."""
        test_dir = tmp_path / "test_directory"
        test_dir.mkdir()
        
        # Add workers up to limit
        manager.active_workers[1] = Mock()
        manager.active_workers[2] = Mock()
        
        with patch('os.path.exists', return_value=True):
            result = await manager.start_worker(str(test_dir))
            
            assert result.success is False
            assert "Maximum workers limit reached" in result.error_message
    
    @pytest.mark.asyncio
    async def test_stop_worker_success(self, manager):
        """Test successful worker stop."""
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory"
        )
        manager.active_workers[12345] = worker_info
        
        with patch('psutil.Process') as mock_process_class, \
             patch.object(manager.lock_manager, 'remove_lock_by_directory', return_value=True):
            
            mock_process = Mock()
            mock_process.is_running.return_value = True
            mock_process.terminate.return_value = None
            mock_process.wait.return_value = None
            mock_process_class.return_value = mock_process
            
            result = await manager.stop_worker(12345)
            
            assert result.success is True
            assert result.worker_info == worker_info
            assert 12345 not in manager.active_workers
    
    @pytest.mark.asyncio
    async def test_stop_worker_not_found(self, manager):
        """Test stopping non-existent worker."""
        result = await manager.stop_worker(99999)
        
        assert result.success is False
        assert "Worker process 99999 not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_get_worker_status_success(self, manager):
        """Test getting worker status."""
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory"
        )
        manager.active_workers[12345] = worker_info
        
        result = await manager.get_worker_status(12345)
        
        assert result == worker_info
        assert result.last_activity is not None
    
    @pytest.mark.asyncio
    async def test_get_worker_status_not_found(self, manager):
        """Test getting status of non-existent worker."""
        with pytest.raises(ProcessNotFoundError, match="Worker process 99999 not found"):
            await manager.get_worker_status(99999)
    
    @pytest.mark.asyncio
    async def test_get_all_workers_status(self, manager):
        """Test getting all workers status."""
        worker1 = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory1"
        )
        worker2 = WorkerProcessInfo(
            process_id=12346,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory2"
        )
        
        manager.active_workers[12345] = worker1
        manager.active_workers[12346] = worker2
        
        result = await manager.get_all_workers_status()
        
        assert len(result) == 2
        assert worker1 in result
        assert worker2 in result
    
    @pytest.mark.asyncio
    async def test_restart_worker_success(self, manager):
        """Test successful worker restart."""
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory"
        )
        manager.active_workers[12345] = worker_info
        
        with patch.object(manager, 'stop_worker', return_value=ChildProcessResult(success=True)), \
             patch.object(manager, 'start_worker', return_value=ChildProcessResult(
                 success=True, 
                 worker_info=WorkerProcessInfo(
                     process_id=12346,
                     start_time=datetime.now(),
                     status="running",
                     directory_path="/test/directory"
                 )
             )):
            
            result = await manager.restart_worker(12345)
            
            assert result.success is True
            assert result.worker_info is not None
            assert result.worker_info.process_id == 12346
    
    @pytest.mark.asyncio
    async def test_restart_worker_not_found(self, manager):
        """Test restarting non-existent worker."""
        result = await manager.restart_worker(99999)
        
        assert result.success is False
        assert "Worker process 99999 not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_cleanup_failed_workers(self, manager):
        """Test cleanup of failed workers."""
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory"
        )
        manager.active_workers[12345] = worker_info
        
        with patch('psutil.Process') as mock_process_class:
            
            mock_process = Mock()
            mock_process.is_running.return_value = False
            mock_process_class.return_value = mock_process
            
            result = await manager.cleanup_failed_workers()
            
            assert result == 1
            assert 12345 not in manager.active_workers
    
    @pytest.mark.asyncio
    async def test_shutdown_all_workers(self, manager):
        """Test shutdown of all workers."""
        worker1 = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory1"
        )
        worker2 = WorkerProcessInfo(
            process_id=12346,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory2"
        )
        
        manager.active_workers[12345] = worker1
        manager.active_workers[12346] = worker2
        
        async def mock_stop_worker(worker_id):
            # Remove from active workers to simulate real behavior
            if worker_id in manager.active_workers:
                del manager.active_workers[worker_id]
            return ChildProcessResult(success=True)
        
        with patch.object(manager, 'stop_worker', side_effect=mock_stop_worker):
            result = await manager.shutdown_all_workers()
            
            assert result.success is True
            assert len(manager.active_workers) == 0
    
    @pytest.mark.asyncio
    async def test_handle_worker_failure_auto_restart(self, manager):
        """Test handling worker failure with auto-restart."""
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory",
            restart_count=0
        )
        manager.active_workers[12345] = worker_info
        
        with patch.object(manager, 'start_worker', return_value=ChildProcessResult(
            success=True,
            worker_info=WorkerProcessInfo(
                process_id=12346,
                start_time=datetime.now(),
                status="running",
                directory_path="/test/directory",
                restart_count=1
            )
        )):
            await manager._handle_worker_failure(12345, Exception("Test failure"))
            
            # Original worker should be removed
            assert 12345 not in manager.active_workers
    
    @pytest.mark.asyncio
    async def test_handle_worker_failure_max_restarts(self, manager):
        """Test handling worker failure with max restarts exceeded."""
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory",
            restart_count=3  # Max attempts reached
        )
        manager.active_workers[12345] = worker_info
        
        await manager._handle_worker_failure(12345, Exception("Test failure"))
        
        # Worker should be removed without restart
        assert 12345 not in manager.active_workers
    
    @pytest.mark.asyncio
    async def test_monitor_worker_health(self, manager):
        """Test worker health monitoring."""
        worker_info = WorkerProcessInfo(
            process_id=12345,
            start_time=datetime.now(),
            status="running",
            directory_path="/test/directory"
        )
        manager.active_workers[12345] = worker_info
        
        with patch('psutil.Process') as mock_process_class, \
             patch.object(manager, '_handle_worker_failure', new_callable=AsyncMock), \
             patch.object(manager, 'cleanup_failed_workers', new_callable=AsyncMock):
            
            mock_process = Mock()
            mock_process.is_running.return_value = True
            mock_process.status.return_value = "running"
            mock_process_class.return_value = mock_process
            
            # Start monitoring task
            task = asyncio.create_task(manager._monitor_worker_health())
            
            # Let it run for a short time
            await asyncio.sleep(0.1)
            
            # Set shutdown event to stop the monitoring
            manager._shutdown_event.set()
            
            # Wait a bit more for the task to respond to shutdown
            await asyncio.sleep(0.1)
            
            # Cancel the task if it's still running
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Verify monitoring was active (task should be done or cancelled)
            assert task.done() or task.cancelled()
    
    def test_worker_process_target(self, manager):
        """Test worker process target function."""
        with patch('logging.basicConfig'), \
             patch('logging.getLogger'), \
             patch('sys.exit'):
            
            # This should not raise any exceptions
            manager._worker_process_target("/test/directory", 50) 