"""
Tests for Processing Stats Command

Test suite for DocAnalyzer processing stats command functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from docanalyzer.commands.auto_commands.processing_stats_command import (
    ProcessingStatsCommand, ProcessingStatsResult
)


class TestProcessingStatsResult:
    """Test suite for ProcessingStatsResult class."""
    
    def test_processing_stats_result_initialization(self):
        """Test ProcessingStatsResult initialization."""
        # Arrange
        processing_stats = {"overall": {"total_files": 0}}
        file_stats = {"total_files_scanned": 0}
        performance_stats = {"processing_speed": {"files_per_minute": 0.0}}
        timestamp = "2024-01-01T00:00:00"
        
        # Act
        result = ProcessingStatsResult(
            processing_stats=processing_stats,
            file_stats=file_stats,
            performance_stats=performance_stats,
            timestamp=timestamp
        )
        
        # Assert
        assert result.processing_stats == processing_stats
        assert result.file_stats == file_stats
        assert result.performance_stats == performance_stats
        assert result.timestamp == timestamp
    
    def test_processing_stats_result_to_dict(self):
        """Test ProcessingStatsResult to_dict method."""
        # Arrange
        result = ProcessingStatsResult(
            processing_stats={"overall": {"total_files": 0}},
            file_stats={"total_files_scanned": 0},
            performance_stats={"processing_speed": {"files_per_minute": 0.0}},
            timestamp="2024-01-01T00:00:00"
        )
        
        # Act
        result_dict = result.to_dict()
        
        # Assert
        assert result_dict["processing_stats"]["overall"]["total_files"] == 0
        assert result_dict["file_stats"]["total_files_scanned"] == 0
        assert result_dict["performance_stats"]["processing_speed"]["files_per_minute"] == 0.0
        assert result_dict["timestamp"] == "2024-01-01T00:00:00"
        assert result_dict["command_type"] == "processing_stats"
    
    def test_processing_stats_result_get_schema(self):
        """Test ProcessingStatsResult get_schema method."""
        # Act
        schema = ProcessingStatsResult.get_schema()
        
        # Assert
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert "processing_stats" in schema["properties"]
        assert "file_stats" in schema["properties"]
        assert "performance_stats" in schema["properties"]
        assert "timestamp" in schema["properties"]
        assert "command_type" in schema["properties"]


class TestProcessingStatsCommand:
    """Test suite for ProcessingStatsCommand class."""
    
    @pytest.fixture
    def command(self):
        """Create test command instance."""
        return ProcessingStatsCommand()
    
    def test_processing_stats_command_initialization(self, command):
        """Test ProcessingStatsCommand initialization."""
        # Assert
        assert command.name == "processing_stats"
        assert command.result_class == ProcessingStatsResult
    
    def test_processing_stats_command_get_schema(self, command):
        """Test ProcessingStatsCommand get_schema method."""
        # Act
        schema = command.get_schema()
        
        # Assert
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "description" in schema
        assert "time_range" in schema["properties"]
        assert "Get file processing statistics and performance metrics" in schema["description"]
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_default(self, command):
        """Test processing stats command execution with default parameters."""
        # Act
        result = await command.execute()
        
        # Assert
        assert isinstance(result, ProcessingStatsResult)
        assert "time_range" in result.processing_stats
        assert "overall" in result.processing_stats
        assert "by_file_type" in result.processing_stats
        assert "total_files_scanned" in result.file_stats
        assert "files_by_size" in result.file_stats
        assert "files_by_extension" in result.file_stats
        assert "processing_queue" in result.file_stats
        assert "processing_speed" in result.performance_stats
        assert "memory_usage" in result.performance_stats
        assert "errors" in result.performance_stats
        assert "locks" in result.performance_stats
        assert result.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_1h(self, command):
        """Test processing stats command with 1h time range."""
        # Act
        result = await command.execute(time_range="1h")
        
        # Assert
        time_range = result.processing_stats["time_range"]
        assert time_range["duration_hours"] == 1.0
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_24h(self, command):
        """Test processing stats command with 24h time range."""
        # Act
        result = await command.execute(time_range="24h")
        
        # Assert
        time_range = result.processing_stats["time_range"]
        assert time_range["duration_hours"] == 24.0
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_7d(self, command):
        """Test processing stats command with 7d time range."""
        # Act
        result = await command.execute(time_range="7d")
        
        # Assert
        time_range = result.processing_stats["time_range"]
        assert time_range["duration_hours"] == 168.0  # 7 * 24
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_30d(self, command):
        """Test processing stats command with 30d time range."""
        # Act
        result = await command.execute(time_range="30d")
        
        # Assert
        time_range = result.processing_stats["time_range"]
        assert time_range["duration_hours"] == 720.0  # 30 * 24
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_invalid_time_range(self, command):
        """Test processing stats command with invalid time range."""
        # Act
        result = await command.execute(time_range="invalid")
        
        # Assert
        time_range = result.processing_stats["time_range"]
        assert time_range["duration_hours"] == 24.0  # Default to 24h
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_with_components(self, command):
        """Test processing stats with available components."""
        # Arrange
        mock_lock_manager = Mock()
        mock_lock_manager.__name__ = "LockManager"
        mock_directory_scanner = Mock()
        mock_directory_scanner.__name__ = "DirectoryScanner"
        mock_base_processor = Mock()
        mock_base_processor.__name__ = "BaseProcessor"
        mock_text_processor = Mock()
        mock_text_processor.__name__ = "TextProcessor"
        mock_markdown_processor = Mock()
        mock_markdown_processor.__name__ = "MarkdownProcessor"
        
        with patch('docanalyzer.services.LockManager', mock_lock_manager):
            with patch('docanalyzer.services.DirectoryScanner', mock_directory_scanner):
                with patch('docanalyzer.processors.BaseProcessor', mock_base_processor):
                    with patch('docanalyzer.processors.TextProcessor', mock_text_processor):
                        with patch('docanalyzer.processors.MarkdownProcessor', mock_markdown_processor):
                            # Act
                            result = await command.execute()
                            
                            # Assert
                            assert "components" in result.processing_stats
                            assert result.processing_stats["components"]["lock_manager"] == "available"
                            assert result.processing_stats["components"]["directory_scanner"] == "available"
                            assert result.processing_stats["components"]["text_processor"] == "available"
                            assert result.processing_stats["components"]["markdown_processor"] == "available"
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_file_types(self, command):
        """Test processing stats includes file type statistics."""
        # Act
        result = await command.execute()
        
        # Assert
        by_file_type = result.processing_stats["by_file_type"]
        assert "text" in by_file_type
        assert "markdown" in by_file_type
        assert "python" in by_file_type
        assert "javascript" in by_file_type
        assert "typescript" in by_file_type
        
        for file_type in by_file_type.values():
            assert "count" in file_type
            assert "success" in file_type
            assert "failed" in file_type
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_file_stats(self, command):
        """Test processing stats includes file statistics."""
        # Act
        result = await command.execute()
        
        # Assert
        file_stats = result.file_stats
        assert "files_by_size" in file_stats
        assert "files_by_extension" in file_stats
        assert "processing_queue" in file_stats
        
        files_by_size = file_stats["files_by_size"]
        assert "small" in files_by_size
        assert "medium" in files_by_size
        assert "large" in files_by_size
        assert "very_large" in files_by_size
        
        files_by_extension = file_stats["files_by_extension"]
        assert ".txt" in files_by_extension
        assert ".md" in files_by_extension
        assert ".py" in files_by_extension
        assert ".js" in files_by_extension
        assert ".ts" in files_by_extension
        
        processing_queue = file_stats["processing_queue"]
        assert "pending" in processing_queue
        assert "processing" in processing_queue
        assert "completed" in processing_queue
        assert "failed" in processing_queue
    
    @pytest.mark.asyncio
    async def test_processing_stats_command_execute_performance_stats(self, command):
        """Test processing stats includes performance statistics."""
        # Act
        result = await command.execute()
        
        # Assert
        performance_stats = result.performance_stats
        assert "processing_speed" in performance_stats
        assert "memory_usage" in performance_stats
        assert "errors" in performance_stats
        assert "locks" in performance_stats
        
        processing_speed = performance_stats["processing_speed"]
        assert "files_per_minute" in processing_speed
        assert "bytes_per_second" in processing_speed
        assert "average_file_size" in processing_speed
        
        memory_usage = performance_stats["memory_usage"]
        assert "peak_memory" in memory_usage
        assert "average_memory" in memory_usage
        assert "memory_per_file" in memory_usage
        
        errors = performance_stats["errors"]
        assert "total_errors" in errors
        assert "error_rate" in errors
        assert "common_errors" in errors
        
        locks = performance_stats["locks"]
        assert "active_locks" in locks
        assert "lock_wait_time" in locks
        assert "lock_conflicts" in locks 