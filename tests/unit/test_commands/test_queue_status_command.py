"""
Tests for Queue Status Command

Test suite for DocAnalyzer queue status command functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from docanalyzer.commands.auto_commands.queue_status_command import (
    QueueStatusCommand, QueueStatusResult
)


class TestQueueStatusResult:
    """Test suite for QueueStatusResult class."""
    
    def test_queue_status_result_initialization(self):
        """Test QueueStatusResult initialization."""
        # Arrange
        queue_status = {"queue_name": "test_queue"}
        queue_items = [{"id": "task_001", "status": "pending"}]
        performance_metrics = {"throughput": {"items_per_minute": 0.0}}
        timestamp = "2024-01-01T00:00:00"
        
        # Act
        result = QueueStatusResult(
            queue_status=queue_status,
            queue_items=queue_items,
            performance_metrics=performance_metrics,
            timestamp=timestamp
        )
        
        # Assert
        assert result.queue_status == queue_status
        assert result.queue_items == queue_items
        assert result.performance_metrics == performance_metrics
        assert result.timestamp == timestamp
    
    def test_queue_status_result_to_dict(self):
        """Test QueueStatusResult to_dict method."""
        # Arrange
        result = QueueStatusResult(
            queue_status={"queue_name": "test_queue"},
            queue_items=[{"id": "task_001", "status": "pending"}],
            performance_metrics={"throughput": {"items_per_minute": 0.0}},
            timestamp="2024-01-01T00:00:00"
        )
        
        # Act
        result_dict = result.to_dict()
        
        # Assert
        assert result_dict["queue_status"]["queue_name"] == "test_queue"
        assert result_dict["queue_items"][0]["id"] == "task_001"
        assert result_dict["queue_items"][0]["status"] == "pending"
        assert result_dict["performance_metrics"]["throughput"]["items_per_minute"] == 0.0
        assert result_dict["timestamp"] == "2024-01-01T00:00:00"
        assert result_dict["command_type"] == "queue_status"
    
    def test_queue_status_result_get_schema(self):
        """Test QueueStatusResult get_schema method."""
        # Act
        schema = QueueStatusResult.get_schema()
        
        # Assert
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert "queue_status" in schema["properties"]
        assert "queue_items" in schema["properties"]
        assert "performance_metrics" in schema["properties"]
        assert "timestamp" in schema["properties"]
        assert "command_type" in schema["properties"]


class TestQueueStatusCommand:
    """Test suite for QueueStatusCommand class."""
    
    @pytest.fixture
    def command(self):
        """Create test command instance."""
        return QueueStatusCommand()
    
    def test_queue_status_command_initialization(self, command):
        """Test QueueStatusCommand initialization."""
        # Assert
        assert command.name == "queue_status"
        assert command.result_class == QueueStatusResult
    
    def test_queue_status_command_get_schema(self, command):
        """Test QueueStatusCommand get_schema method."""
        # Act
        schema = command.get_schema()
        
        # Assert
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "description" in schema
        assert "include_items" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "Get processing queue status and performance metrics" in schema["description"]
    
    @pytest.mark.asyncio
    async def test_queue_status_command_execute_default(self, command):
        """Test queue status command execution with default parameters."""
        # Act
        result = await command.execute()
        
        # Assert
        assert isinstance(result, QueueStatusResult)
        assert "queue_name" in result.queue_status
        assert "status" in result.queue_status
        assert "total_items" in result.queue_status
        assert "pending_items" in result.queue_status
        assert "processing_items" in result.queue_status
        assert "completed_items" in result.queue_status
        assert "failed_items" in result.queue_status
        assert "queue_size" in result.queue_status
        assert "max_queue_size" in result.queue_status
        assert "workers_active" in result.queue_status
        assert "workers_total" in result.queue_status
        assert "last_activity" in result.queue_status
        assert len(result.queue_items) > 0  # Should include sample items by default
        assert "throughput" in result.performance_metrics
        assert "latency" in result.performance_metrics
        assert "errors" in result.performance_metrics
        assert "resources" in result.performance_metrics
        assert result.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_queue_status_command_execute_without_items(self, command):
        """Test queue status command without including items."""
        # Act
        result = await command.execute(include_items=False)
        
        # Assert
        assert len(result.queue_items) == 0
    
    @pytest.mark.asyncio
    async def test_queue_status_command_execute_with_limit(self, command):
        """Test queue status command with custom limit."""
        # Act
        result = await command.execute(limit=1)
        
        # Assert
        assert len(result.queue_items) <= 1
    
    @pytest.mark.asyncio
    async def test_queue_status_command_execute_with_components(self, command):
        """Test queue status with available components."""
        # Arrange
        mock_lock_manager = Mock()
        mock_lock_manager.__name__ = "LockManager"
        mock_directory_scanner = Mock()
        mock_directory_scanner.__name__ = "DirectoryScanner"
        
        with patch('docanalyzer.services.LockManager', mock_lock_manager):
            with patch('docanalyzer.services.DirectoryScanner', mock_directory_scanner):
                # Act
                result = await command.execute()
                
                # Assert
                assert "components" in result.queue_status
                assert result.queue_status["components"]["lock_manager"] == "available"
                assert result.queue_status["components"]["directory_scanner"] == "available"
                assert result.queue_status["components"]["queue_manager"] == "not_implemented"
    
    @pytest.mark.asyncio
    async def test_queue_status_command_execute_queue_status(self, command):
        """Test queue status includes queue information."""
        # Act
        result = await command.execute()
        
        # Assert
        queue_status = result.queue_status
        assert queue_status["queue_name"] == "docanalyzer_processing_queue"
        assert queue_status["status"] == "active"
        assert queue_status["max_queue_size"] == 1000
        assert queue_status["workers_total"] == 4
    
    @pytest.mark.asyncio
    async def test_queue_status_command_execute_queue_items(self, command):
        """Test queue status includes queue items."""
        # Act
        result = await command.execute(include_items=True)
        
        # Assert
        assert len(result.queue_items) > 0
        
        # Check sample items structure
        for item in result.queue_items:
            assert "id" in item
            assert "type" in item
            assert "status" in item
            assert "priority" in item
            assert "created_at" in item
    
    @pytest.mark.asyncio
    async def test_queue_status_command_execute_performance_metrics(self, command):
        """Test queue status includes performance metrics."""
        # Act
        result = await command.execute()
        
        # Assert
        performance_metrics = result.performance_metrics
        assert "throughput" in performance_metrics
        assert "latency" in performance_metrics
        assert "errors" in performance_metrics
        assert "resources" in performance_metrics
        
        throughput = performance_metrics["throughput"]
        assert "items_per_minute" in throughput
        assert "average_processing_time" in throughput
        assert "peak_throughput" in throughput
        
        latency = performance_metrics["latency"]
        assert "average_wait_time" in latency
        assert "max_wait_time" in latency
        assert "p95_wait_time" in latency
        
        errors = performance_metrics["errors"]
        assert "error_rate" in errors
        assert "retry_rate" in errors
        assert "failed_items" in errors
        
        resources = performance_metrics["resources"]
        assert "memory_usage" in resources
        assert "cpu_usage" in resources
        assert "disk_usage" in resources
    
    @pytest.mark.asyncio
    async def test_queue_status_command_execute_sample_items(self, command):
        """Test queue status includes sample items with correct structure."""
        # Act
        result = await command.execute(include_items=True)
        
        # Assert
        items = result.queue_items
        assert len(items) >= 2  # Should have at least 2 sample items
        
        # Check first item (file processing)
        file_item = items[0]
        assert file_item["id"] == "task_001"
        assert file_item["type"] == "file_processing"
        assert file_item["status"] == "pending"
        assert file_item["priority"] == "normal"
        assert "file_path" in file_item
        assert "file_size" in file_item
        assert "estimated_duration" in file_item
        
        # Check second item (directory scan)
        dir_item = items[1]
        assert dir_item["id"] == "task_002"
        assert dir_item["type"] == "directory_scan"
        assert dir_item["status"] == "processing"
        assert dir_item["priority"] == "high"
        assert "directory_path" in dir_item
        assert "progress" in dir_item
        assert "estimated_duration" in dir_item 