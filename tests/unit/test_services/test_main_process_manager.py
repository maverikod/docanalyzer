"""
Tests for Main Process Manager

Comprehensive test suite for process management functionality,
including process lifecycle, health monitoring, and error handling.
"""

import pytest
import asyncio
import multiprocessing
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

from docanalyzer.services.main_process_manager import (
    MainProcessManager,
    MainProcessConfig,
    ProcessInfo,
    ProcessStatus,
    ProcessManagementResult,
    ProcessManagementError,
    ProcessNotFoundError,
    ResourceLimitError,
    HealthCheckError
)


class TestMainProcessManager:
    """Test suite for MainProcessManager class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MainProcessConfig(
            max_child_processes=2,
            process_timeout=60,
            health_check_interval=5,
            enable_auto_recovery=True,
            max_retry_attempts=2,
            graceful_shutdown_timeout=10
        )
    
    @pytest.fixture
    def manager(self, config):
        """Create test manager instance."""
        with patch('docanalyzer.services.main_process_manager.LockManager'), \
             patch('docanalyzer.services.main_process_manager.DirectoryScanner'), \
             patch('docanalyzer.services.main_process_manager.FileProcessor'), \
             patch('docanalyzer.services.main_process_manager.ChunkingManager'), \
             patch('docanalyzer.services.main_process_manager.HealthChecker'), \
             patch('docanalyzer.services.main_process_manager.MetricsCollector'):
            
            return MainProcessManager(config)
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.mark.asyncio
    async def test_init_success(self, config):
        """Test successful initialization."""
        with patch('docanalyzer.services.main_process_manager.LockManager'), \
             patch('docanalyzer.services.main_process_manager.DirectoryScanner'), \
             patch('docanalyzer.services.main_process_manager.FileProcessor'), \
             patch('docanalyzer.services.main_process_manager.ChunkingManager'), \
             patch('docanalyzer.services.main_process_manager.HealthChecker'), \
             patch('docanalyzer.services.main_process_manager.MetricsCollector'):
            
            manager = MainProcessManager(config)
            
            assert manager.config == config
            assert len(manager.active_processes) == 0
            assert len(manager.process_history) == 0
            assert manager.shutdown_event is not None
            assert manager.health_check_task is None
    
    def test_init_invalid_config(self):
        """Test initialization with invalid configuration."""
        # Test with invalid max_child_processes
        with patch('docanalyzer.services.main_process_manager.LockManager'), \
             patch('docanalyzer.services.main_process_manager.DirectoryScanner'), \
             patch('docanalyzer.services.main_process_manager.FileProcessor'), \
             patch('docanalyzer.services.main_process_manager.ChunkingManager'), \
             patch('docanalyzer.services.main_process_manager.HealthChecker'), \
             patch('docanalyzer.services.main_process_manager.MetricsCollector'):
            
            with pytest.raises(ValueError, match="max_child_processes must be positive"):
                MainProcessManager(MainProcessConfig(max_child_processes=0))
        
        # Test with invalid process_timeout
        with patch('docanalyzer.services.main_process_manager.LockManager'), \
             patch('docanalyzer.services.main_process_manager.DirectoryScanner'), \
             patch('docanalyzer.services.main_process_manager.FileProcessor'), \
             patch('docanalyzer.services.main_process_manager.ChunkingManager'), \
             patch('docanalyzer.services.main_process_manager.HealthChecker'), \
             patch('docanalyzer.services.main_process_manager.MetricsCollector'):
            
            with pytest.raises(ValueError, match="process_timeout must be positive"):
                MainProcessManager(MainProcessConfig(process_timeout=0))
        
        # Test with invalid health_check_interval
        with patch('docanalyzer.services.main_process_manager.LockManager'), \
             patch('docanalyzer.services.main_process_manager.DirectoryScanner'), \
             patch('docanalyzer.services.main_process_manager.FileProcessor'), \
             patch('docanalyzer.services.main_process_manager.ChunkingManager'), \
             patch('docanalyzer.services.main_process_manager.HealthChecker'), \
             patch('docanalyzer.services.main_process_manager.MetricsCollector'):
            
            with pytest.raises(ValueError, match="health_check_interval must be positive"):
                MainProcessManager(MainProcessConfig(health_check_interval=0))
        
        # Test with invalid max_retry_attempts
        with patch('docanalyzer.services.main_process_manager.LockManager'), \
             patch('docanalyzer.services.main_process_manager.DirectoryScanner'), \
             patch('docanalyzer.services.main_process_manager.FileProcessor'), \
             patch('docanalyzer.services.main_process_manager.ChunkingManager'), \
             patch('docanalyzer.services.main_process_manager.HealthChecker'), \
             patch('docanalyzer.services.main_process_manager.MetricsCollector'):
            
            with pytest.raises(ValueError, match="max_retry_attempts must be non-negative"):
                MainProcessManager(MainProcessConfig(max_retry_attempts=-1))
    
    def test_init_component_failure(self):
        """Test initialization when components fail."""
        with patch('docanalyzer.services.main_process_manager.LockManager', side_effect=Exception("Component error")):
            with pytest.raises(ProcessManagementError, match="Failed to initialize components"):
                MainProcessManager()
    
    @pytest.mark.asyncio
    async def test_start_success(self, manager):
        """Test successful start."""
        manager.metrics_collector.start = AsyncMock()
        
        result = await manager.start()
        
        assert result.success is True
        assert "started successfully" in result.message
        assert manager.health_check_task is not None
        manager.metrics_collector.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_failure(self, manager):
        """Test start failure."""
        manager.metrics_collector.start = AsyncMock(side_effect=Exception("Start error"))
        
        with pytest.raises(ProcessManagementError, match="Startup failed"):
            await manager.start()
    
    @pytest.mark.asyncio
    async def test_stop_success(self, manager):
        """Test successful stop."""
        # Setup
        manager.health_check_task = asyncio.create_task(asyncio.sleep(1))
        manager.metrics_collector.stop = AsyncMock()
        
        result = await manager.stop()
        
        assert result.success is True
        assert "stopped successfully" in result.message
        manager.metrics_collector.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_with_active_processes(self, manager):
        """Test stop with active processes."""
        # Setup
        manager.health_check_task = asyncio.create_task(asyncio.sleep(1))
        manager.metrics_collector.stop = AsyncMock()
        
        # Add mock active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch.object(manager, '_stop_all_child_processes', new_callable=AsyncMock):
            result = await manager.stop()
            
            assert result.success is True
            manager._stop_all_child_processes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_child_process_success(self, manager, temp_directory):
        """Test successful child process start."""
        with patch('os.path.exists', return_value=True), \
             patch('multiprocessing.Process') as mock_process_class:
            
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.start = Mock()
            mock_process_class.return_value = mock_process
            
            manager.lock_manager.create_lock = AsyncMock()
            
            result = await manager.start_child_process(temp_directory)
            
            assert result.success is True
            assert result.process_info.process_id == 12345
            assert result.process_info.status == ProcessStatus.RUNNING
            assert result.process_info.directory == temp_directory
            assert 12345 in manager.active_processes
            mock_process.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_child_process_directory_not_found(self, manager):
        """Test child process start with non-existent directory."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="Directory not found"):
                await manager.start_child_process("/nonexistent/directory")
    
    @pytest.mark.asyncio
    async def test_start_child_process_limit_reached(self, manager, temp_directory):
        """Test child process start when limit is reached."""
        # Fill up active processes
        for i in range(manager.config.max_child_processes):
            process_info = ProcessInfo(
                process_id=1000 + i,
                status=ProcessStatus.RUNNING,
                start_time=datetime.now(),
                directory=f"/test/dir{i}"
            )
            manager.active_processes[1000 + i] = process_info
        
        with patch('os.path.exists', return_value=True):
            with pytest.raises(ResourceLimitError, match="Maximum child processes limit reached"):
                await manager.start_child_process(temp_directory)
    
    @pytest.mark.asyncio
    async def test_start_child_process_already_processing(self, manager, temp_directory):
        """Test child process start when directory is already being processed."""
        # Add existing process for the same directory
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory=temp_directory
        )
        manager.active_processes[12345] = process_info
        
        with patch('os.path.exists', return_value=True):
            with pytest.raises(ProcessManagementError, match="Directory already being processed"):
                await manager.start_child_process(temp_directory)
    
    @pytest.mark.asyncio
    async def test_stop_child_process_success(self, manager):
        """Test successful child process stop."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.terminate = Mock()
            mock_process.wait = Mock()
            mock_process_class.return_value = mock_process
            
            manager.lock_manager.remove_lock_by_directory = AsyncMock()
            
            result = await manager.stop_child_process(12345)
            
            assert result.success is True
            assert result.process_info.status == ProcessStatus.TERMINATED
            assert 12345 not in manager.active_processes
            assert len(manager.process_history) == 1
            mock_process.terminate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_child_process_not_found(self, manager):
        """Test stopping non-existent child process."""
        with pytest.raises(ProcessNotFoundError, match="Process 12345 not found"):
            await manager.stop_child_process(12345)
    
    @pytest.mark.asyncio
    async def test_stop_child_process_timeout(self, manager):
        """Test child process stop with timeout."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.terminate = Mock()
            mock_process.wait = Mock(side_effect=Exception("Timeout"))
            mock_process.kill = Mock()
            mock_process_class.return_value = mock_process
            
            manager.lock_manager.remove_lock_by_directory = AsyncMock()
            
            # Should handle timeout gracefully
            result = await manager.stop_child_process(12345)
            
            assert result.success is True
            mock_process.kill.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_process_status_specific(self, manager):
        """Test getting status of specific process."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir",
            memory_usage=100.5,
            cpu_usage=25.0
        )
        manager.active_processes[12345] = process_info
        
        status = await manager.get_process_status(12345)
        
        assert status["process_id"] == 12345
        assert status["status"] == ProcessStatus.RUNNING.value
        assert status["directory"] == "/test/dir"
        assert status["memory_usage"] == 100.5
        assert status["cpu_usage"] == 25.0
    
    @pytest.mark.asyncio
    async def test_get_process_status_all(self, manager):
        """Test getting status of all processes."""
        # Setup multiple active processes
        for i in range(2):
            process_info = ProcessInfo(
                process_id=1000 + i,
                status=ProcessStatus.RUNNING,
                start_time=datetime.now(),
                directory=f"/test/dir{i}"
            )
            manager.active_processes[1000 + i] = process_info
        
        status = await manager.get_process_status()
        
        assert status["total_active"] == 2
        assert status["max_processes"] == 2
        assert len(status["active_processes"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_process_status_not_found(self, manager):
        """Test getting status of non-existent process."""
        with pytest.raises(ProcessNotFoundError, match="Process 12345 not found"):
            await manager.get_process_status(12345)
    
    @pytest.mark.asyncio
    async def test_get_health_status_success(self, manager):
        """Test successful health status retrieval."""
        manager.metrics_collector.get_system_metrics = AsyncMock(return_value={
            "cpu_usage": 50.0,
            "memory_usage": 1024.0
        })
        
        manager.health_checker.get_health_status = AsyncMock(return_value={
            "overall_health": True,
            "components": {}
        })
        
        health_status = await manager.get_health_status()
        
        assert "status" in health_status
        assert "timestamp" in health_status
        assert "system_metrics" in health_status
        assert "process_metrics" in health_status
        assert "health_details" in health_status
    
    @pytest.mark.asyncio
    async def test_get_health_status_failure(self, manager):
        """Test health status retrieval failure."""
        manager.metrics_collector.get_system_metrics = AsyncMock(side_effect=Exception("Metrics error"))
        
        with pytest.raises(HealthCheckError, match="Health check failed"):
            await manager.get_health_status()
    
    @pytest.mark.asyncio
    async def test_restart_failed_processes_success(self, manager):
        """Test successful restart of failed processes."""
        # Setup failed process in history
        failed_process = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.FAILED,
            start_time=datetime.now() - timedelta(minutes=5),
            end_time=datetime.now(),
            directory="/test/dir"
        )
        manager.process_history.append(failed_process)
        
        with patch.object(manager, 'start_child_process', new_callable=AsyncMock) as mock_start:
            result = await manager.restart_failed_processes()
            
            assert result.success is True
            assert "Restarted 1 failed processes" in result.message
            mock_start.assert_called_once_with("/test/dir")
    
    @pytest.mark.asyncio
    async def test_restart_failed_processes_retry_limit(self, manager):
        """Test restart with retry limit reached."""
        # Setup failed process that has reached retry limit
        for i in range(manager.config.max_retry_attempts + 1):
            failed_process = ProcessInfo(
                process_id=12345 + i,
                status=ProcessStatus.FAILED,
                start_time=datetime.now() - timedelta(minutes=5),
                end_time=datetime.now(),
                directory="/test/dir"
            )
            manager.process_history.append(failed_process)
        
        with patch.object(manager, 'start_child_process', new_callable=AsyncMock) as mock_start:
            result = await manager.restart_failed_processes()
            
            assert result.success is True
            assert "Restarted 0 failed processes" in result.message
            mock_start.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_orphaned_processes_success(self, manager):
        """Test successful cleanup of orphaned processes."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.is_running = Mock(return_value=False)
            mock_process_class.return_value = mock_process
            
            with patch.object(manager, 'stop_child_process', new_callable=AsyncMock) as mock_stop:
                result = await manager.cleanup_orphaned_processes()
                
                assert result.success is True
                assert "Cleaned up 1 orphaned processes" in result.message
                mock_stop.assert_called_once_with(12345)
    
    @pytest.mark.asyncio
    async def test_cleanup_orphaned_processes_no_such_process(self, manager):
        """Test cleanup when process no longer exists."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process', side_effect=Exception("No such process")):
            with patch.object(manager, 'stop_child_process', new_callable=AsyncMock) as mock_stop:
                result = await manager.cleanup_orphaned_processes()
                
                assert result.success is True
                assert "Cleaned up 1 orphaned processes" in result.message
                mock_stop.assert_called_once_with(12345)
    
    @pytest.mark.asyncio
    async def test_monitor_process_health_success(self, manager):
        """Test successful health monitoring."""
        manager.shutdown_event.set()  # Trigger immediate shutdown
        
        with patch.object(manager, '_update_process_metrics', new_callable=AsyncMock) as mock_update, \
             patch.object(manager, 'cleanup_orphaned_processes', new_callable=AsyncMock) as mock_cleanup:
            
            await manager._monitor_process_health()
            
            # Should not call these methods due to immediate shutdown
            mock_update.assert_not_called()
            mock_cleanup.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_process_completion_success(self, manager):
        """Test successful process completion handling."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        manager.lock_manager.remove_lock_by_directory = AsyncMock()
        
        await manager._handle_process_completion(12345, 0)
        
        assert 12345 not in manager.active_processes
        assert len(manager.process_history) == 1
        assert manager.process_history[0].status == ProcessStatus.COMPLETED
        assert manager.process_history[0].exit_code == 0
    
    @pytest.mark.asyncio
    async def test_handle_process_completion_failure(self, manager):
        """Test process completion handling with failure."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        manager.lock_manager.remove_lock_by_directory = AsyncMock()
        
        await manager._handle_process_completion(12345, 1)
        
        assert 12345 not in manager.active_processes
        assert len(manager.process_history) == 1
        assert manager.process_history[0].status == ProcessStatus.FAILED
        assert manager.process_history[0].exit_code == 1
        assert "Process exited with code 1" in manager.process_history[0].error_message
    
    @pytest.mark.asyncio
    async def test_handle_process_failure_success(self, manager):
        """Test successful process failure handling."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        manager.lock_manager.remove_lock_by_directory = AsyncMock()
        
        error = Exception("Test error")
        await manager._handle_process_failure(12345, error)
        
        assert 12345 not in manager.active_processes
        assert len(manager.process_history) == 1
        assert manager.process_history[0].status == ProcessStatus.FAILED
        assert "Test error" in manager.process_history[0].error_message
    
    @pytest.mark.asyncio
    async def test_handle_process_failure_auto_recovery(self, manager):
        """Test process failure handling with auto-recovery."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        manager.lock_manager.remove_lock_by_directory = AsyncMock()
        
        with patch.object(manager, 'start_child_process', new_callable=AsyncMock) as mock_start:
            error = Exception("Test error")
            await manager._handle_process_failure(12345, error)
            
            mock_start.assert_called_once_with("/test/dir")
    
    def test_has_reached_retry_limit_enabled(self, manager):
        """Test retry limit check when auto-recovery is enabled."""
        # Setup process info
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.FAILED,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        
        # Add failed processes up to retry limit (but not over)
        for i in range(manager.config.max_retry_attempts - 1):
            failed_process = ProcessInfo(
                process_id=1000 + i,
                status=ProcessStatus.FAILED,
                start_time=datetime.now(),
                directory="/test/dir"
            )
            manager.process_history.append(failed_process)
        
        # Should not have reached limit yet
        assert not manager._has_reached_retry_limit(process_info)
        
        # Add one more failure to reach limit
        failed_process = ProcessInfo(
            process_id=2000,
            status=ProcessStatus.FAILED,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.process_history.append(failed_process)
        
        # Should have reached limit now
        assert manager._has_reached_retry_limit(process_info)
    
    def test_has_reached_retry_limit_disabled(self, config):
        """Test retry limit check when auto-recovery is disabled."""
        config.enable_auto_recovery = False
        
        with patch('docanalyzer.services.main_process_manager.LockManager'), \
             patch('docanalyzer.services.main_process_manager.DirectoryScanner'), \
             patch('docanalyzer.services.main_process_manager.FileProcessor'), \
             patch('docanalyzer.services.main_process_manager.ChunkingManager'), \
             patch('docanalyzer.services.main_process_manager.HealthChecker'), \
             patch('docanalyzer.services.main_process_manager.MetricsCollector'):
            
            manager = MainProcessManager(config)
            
            process_info = ProcessInfo(
                process_id=12345,
                status=ProcessStatus.FAILED,
                start_time=datetime.now(),
                directory="/test/dir"
            )
            
            # Should always return True when auto-recovery is disabled
            assert manager._has_reached_retry_limit(process_info)
    
    @pytest.mark.asyncio
    async def test_update_process_metrics_success(self, manager):
        """Test successful process metrics update."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.memory_info = Mock(return_value=Mock(rss=1024 * 1024 * 100))  # 100MB
            mock_process.cpu_percent = Mock(return_value=25.0)
            mock_process_class.return_value = mock_process
            
            await manager._update_process_metrics()
            
            assert process_info.memory_usage == 100.0
            assert process_info.cpu_usage == 25.0
    
    @pytest.mark.asyncio
    async def test_update_process_metrics_no_such_process(self, manager):
        """Test process metrics update when process no longer exists."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process', side_effect=Exception("No such process")):
            # Should not raise exception
            await manager._update_process_metrics()
            
            # Metrics should remain unchanged
            assert process_info.memory_usage is None
            assert process_info.cpu_usage is None


class TestProcessInfo:
    """Test suite for ProcessInfo dataclass."""
    
    def test_process_info_creation(self):
        """Test ProcessInfo creation."""
        start_time = datetime.now()
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=start_time,
            directory="/test/dir",
            memory_usage=100.5,
            cpu_usage=25.0
        )
        
        assert process_info.process_id == 12345
        assert process_info.status == ProcessStatus.RUNNING
        assert process_info.start_time == start_time
        assert process_info.directory == "/test/dir"
        assert process_info.memory_usage == 100.5
        assert process_info.cpu_usage == 25.0
        assert process_info.end_time is None
        assert process_info.error_message is None
        assert process_info.exit_code is None


class TestMainProcessConfig:
    """Test suite for MainProcessConfig dataclass."""
    
    def test_main_process_config_defaults(self):
        """Test MainProcessConfig with default values."""
        config = MainProcessConfig()
        
        assert config.max_child_processes == 4
        assert config.process_timeout == 300
        assert config.health_check_interval == 30
        assert config.enable_auto_recovery is True
        assert config.max_retry_attempts == 3
        assert config.graceful_shutdown_timeout == 60
    
    def test_main_process_config_custom(self):
        """Test MainProcessConfig with custom values."""
        config = MainProcessConfig(
            max_child_processes=8,
            process_timeout=600,
            health_check_interval=60,
            enable_auto_recovery=False,
            max_retry_attempts=5,
            graceful_shutdown_timeout=120
        )
        
        assert config.max_child_processes == 8
        assert config.process_timeout == 600
        assert config.health_check_interval == 60
        assert config.enable_auto_recovery is False
        assert config.max_retry_attempts == 5
        assert config.graceful_shutdown_timeout == 120


class TestProcessManagementResult:
    """Test suite for ProcessManagementResult dataclass."""
    
    def test_process_management_result_creation(self):
        """Test ProcessManagementResult creation."""
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now()
        )
        
        result = ProcessManagementResult(
            success=True,
            message="Test operation successful",
            process_info=process_info,
            error_details=None
        )
        
        assert result.success is True
        assert result.message == "Test operation successful"
        assert result.process_info == process_info
        assert result.error_details is None
        assert result.timestamp is not None


class TestExceptions:
    """Test suite for custom exceptions."""
    
    def test_process_management_error(self):
        """Test ProcessManagementError."""
        error = ProcessManagementError("Test error")
        assert str(error) == "Test error"
    
    def test_process_not_found_error(self):
        """Test ProcessNotFoundError."""
        error = ProcessNotFoundError("Process not found")
        assert str(error) == "Process not found"
        assert isinstance(error, ProcessManagementError)
    
    def test_resource_limit_error(self):
        """Test ResourceLimitError."""
        error = ResourceLimitError("Resource limit exceeded")
        assert str(error) == "Resource limit exceeded"
        assert isinstance(error, ProcessManagementError)
    
    def test_health_check_error(self):
        """Test HealthCheckError."""
        error = HealthCheckError("Health check failed")
        assert str(error) == "Health check failed"
        assert isinstance(error, ProcessManagementError)


class TestMainProcessManagerExtended:
    """Extended test suite for MainProcessManager to increase coverage."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MainProcessConfig(
            max_child_processes=2,
            process_timeout=60,
            health_check_interval=5,
            enable_auto_recovery=True,
            max_retry_attempts=2,
            graceful_shutdown_timeout=10
        )
    
    @pytest.fixture
    def manager(self, config):
        """Create test manager instance."""
        with patch('docanalyzer.services.main_process_manager.LockManager'), \
             patch('docanalyzer.services.main_process_manager.DirectoryScanner'), \
             patch('docanalyzer.services.main_process_manager.FileProcessor'), \
             patch('docanalyzer.services.main_process_manager.ChunkingManager'), \
             patch('docanalyzer.services.main_process_manager.HealthChecker'), \
             patch('docanalyzer.services.main_process_manager.MetricsCollector'):
            
            return MainProcessManager(config)
    
    @pytest.mark.asyncio
    async def test_stop_child_process_force_kill(self, manager):
        """Test child process stop with force kill."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.terminate = Mock()
            mock_process.wait = Mock(side_effect=Exception("Timeout"))
            mock_process.kill = Mock()
            mock_process.wait = Mock(side_effect=Exception("Kill timeout"))
            mock_process_class.return_value = mock_process
            
            manager.lock_manager.remove_lock_by_directory = AsyncMock()
            
            result = await manager.stop_child_process(12345)
            
            assert result.success is True
            mock_process.kill.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_child_process_no_such_process_after_terminate(self, manager):
        """Test child process stop when process disappears after terminate."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.terminate = Mock()
            mock_process.wait = Mock(side_effect=Exception("No such process"))
            mock_process.kill = Mock(side_effect=Exception("No such process"))
            mock_process_class.return_value = mock_process
            
            manager.lock_manager.remove_lock_by_directory = AsyncMock()
            
            result = await manager.stop_child_process(12345)
            
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_stop_child_process_lock_removal_failure(self, manager):
        """Test child process stop when lock removal fails."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.terminate = Mock()
            mock_process.wait = Mock()
            mock_process_class.return_value = mock_process
            
            manager.lock_manager.remove_lock_by_directory = AsyncMock(side_effect=Exception("Lock error"))
            
            result = await manager.stop_child_process(12345)
            
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_handle_process_completion_not_found(self, manager):
        """Test process completion handling for non-existent process."""
        # Should not raise exception
        await manager._handle_process_completion(12345, 0)
        
        assert len(manager.process_history) == 0
    
    @pytest.mark.asyncio
    async def test_handle_process_completion_lock_removal_failure(self, manager):
        """Test process completion handling when lock removal fails."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        manager.lock_manager.remove_lock_by_directory = AsyncMock(side_effect=Exception("Lock error"))
        
        await manager._handle_process_completion(12345, 0)
        
        assert 12345 not in manager.active_processes
        assert len(manager.process_history) == 1
    
    @pytest.mark.asyncio
    async def test_handle_process_failure_not_found(self, manager):
        """Test process failure handling for non-existent process."""
        # Should not raise exception
        error = Exception("Test error")
        await manager._handle_process_failure(12345, error)
        
        assert len(manager.process_history) == 0
    
    @pytest.mark.asyncio
    async def test_handle_process_failure_lock_removal_failure(self, manager):
        """Test process failure handling when lock removal fails."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        manager.lock_manager.remove_lock_by_directory = AsyncMock(side_effect=Exception("Lock error"))
        
        error = Exception("Test error")
        await manager._handle_process_failure(12345, error)
        
        assert 12345 not in manager.active_processes
        assert len(manager.process_history) == 1
    
    @pytest.mark.asyncio
    async def test_handle_process_failure_auto_recovery_failure(self, manager):
        """Test process failure handling when auto-recovery fails."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        manager.lock_manager.remove_lock_by_directory = AsyncMock()
        
        with patch.object(manager, 'start_child_process', new_callable=AsyncMock, side_effect=Exception("Start error")):
            error = Exception("Test error")
            await manager._handle_process_failure(12345, error)
            
            assert 12345 not in manager.active_processes
            assert len(manager.process_history) == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_orphaned_processes_unresponsive(self, manager):
        """Test cleanup of unresponsive processes."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.is_running = Mock(return_value=True)
            mock_process_class.return_value = mock_process
            
            with patch.object(manager, '_is_process_responsive', return_value=False), \
                 patch.object(manager, 'stop_child_process', new_callable=AsyncMock) as mock_stop:
                
                result = await manager.cleanup_orphaned_processes()
                
                assert result.success is True
                assert "Cleaned up 1 orphaned processes" in result.message
                mock_stop.assert_called_once_with(12345)
    
    @pytest.mark.asyncio
    async def test_cleanup_orphaned_processes_check_error(self, manager):
        """Test cleanup when process check fails."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process', side_effect=Exception("Check error")):
            with patch.object(manager, 'stop_child_process', new_callable=AsyncMock) as mock_stop:
                result = await manager.cleanup_orphaned_processes()
                
                assert result.success is True
                assert "Cleaned up 1 orphaned processes" in result.message
                mock_stop.assert_called_once_with(12345)
    
    @pytest.mark.asyncio
    async def test_cleanup_orphaned_processes_stop_error(self, manager):
        """Test cleanup when process stop fails."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.is_running = Mock(return_value=False)
            mock_process_class.return_value = mock_process
            
            with patch.object(manager, 'stop_child_process', new_callable=AsyncMock, side_effect=Exception("Stop error")):
                result = await manager.cleanup_orphaned_processes()
                
                assert result.success is True
                # The process is not counted as cleaned up if stop fails
                assert "Cleaned up 0 orphaned processes" in result.message
    
    @pytest.mark.asyncio
    async def test_monitor_process_health_with_errors(self, manager):
        """Test health monitoring with errors."""
        manager.shutdown_event.clear()
        
        with patch.object(manager, '_update_process_metrics', new_callable=AsyncMock, side_effect=Exception("Update error")), \
             patch.object(manager, 'cleanup_orphaned_processes', new_callable=AsyncMock), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            # Set shutdown event after first iteration
            mock_sleep.side_effect = lambda x: manager.shutdown_event.set()
            
            await manager._monitor_process_health()
            
            # Should handle errors gracefully
            manager._update_process_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitor_process_health_cancelled(self, manager):
        """Test health monitoring when cancelled."""
        manager.shutdown_event.clear()
        
        with patch.object(manager, '_update_process_metrics', new_callable=AsyncMock), \
             patch.object(manager, 'cleanup_orphaned_processes', new_callable=AsyncMock), \
             patch('asyncio.sleep', new_callable=AsyncMock, side_effect=asyncio.CancelledError):
            
            await manager._monitor_process_health()
            
            # Should handle cancellation gracefully
    
    @pytest.mark.asyncio
    async def test_update_process_metrics_with_errors(self, manager):
        """Test process metrics update with errors."""
        # Setup active process
        process_info = ProcessInfo(
            process_id=12345,
            status=ProcessStatus.RUNNING,
            start_time=datetime.now(),
            directory="/test/dir"
        )
        manager.active_processes[12345] = process_info
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.memory_info = Mock(side_effect=Exception("Memory error"))
            mock_process_class.return_value = mock_process
            
            # Should not raise exception
            await manager._update_process_metrics()
            
            # Metrics should remain unchanged
            assert process_info.memory_usage is None
            assert process_info.cpu_usage is None
    
    def test_is_process_responsive_success(self, manager):
        """Test process responsiveness check success."""
        with patch('psutil.Process') as mock_process_class:
            mock_process = Mock()
            mock_process.status = Mock(return_value="running")
            mock_process_class.return_value = mock_process
            
            assert manager._is_process_responsive(mock_process) is True
    
    def test_is_process_responsive_no_such_process(self, manager):
        """Test process responsiveness check with NoSuchProcess."""
        import psutil
        mock_process = Mock()
        mock_process.status = Mock(side_effect=psutil.NoSuchProcess(12345))
        
        # The method should catch the exception and return False
        result = manager._is_process_responsive(mock_process)
        assert result is False
    
    def test_is_process_responsive_access_denied(self, manager):
        """Test process responsiveness check with AccessDenied."""
        import psutil
        mock_process = Mock()
        mock_process.status = Mock(side_effect=psutil.AccessDenied(12345))
        
        # The method should catch the exception and return False
        result = manager._is_process_responsive(mock_process)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_stop_all_child_processes_with_errors(self, manager):
        """Test stopping all child processes with errors."""
        # Setup active processes
        for i in range(2):
            process_info = ProcessInfo(
                process_id=1000 + i,
                status=ProcessStatus.RUNNING,
                start_time=datetime.now(),
                directory=f"/test/dir{i}"
            )
            manager.active_processes[1000 + i] = process_info
        
        with patch.object(manager, 'stop_child_process', new_callable=AsyncMock) as mock_stop:
            mock_stop.side_effect = [None, Exception("Stop error")]
            
            await manager._stop_all_child_processes()
            
            assert mock_stop.call_count == 2
    
    def test_child_process_worker_success(self, manager):
        """Test child process worker function success."""
        with patch('logging.basicConfig'), \
             patch('logging.getLogger') as mock_get_logger, \
             patch('sys.exit') as mock_exit:
            
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Test successful execution
            manager._child_process_worker("/test/dir")
            
            # Should not call sys.exit
            mock_exit.assert_not_called()
            # Should log info messages
            assert mock_logger.info.call_count >= 2 