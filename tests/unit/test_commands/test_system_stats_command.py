"""
Tests for System Stats Command

Test suite for DocAnalyzer system stats command functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from docanalyzer.commands.auto_commands.system_stats_command import (
    SystemStatsCommand, SystemStatsResult
)


class TestSystemStatsResult:
    """Test suite for SystemStatsResult class."""
    
    def test_system_stats_result_initialization(self):
        """Test SystemStatsResult initialization."""
        # Arrange
        system_stats = {"platform": {"system": "Linux"}}
        performance_metrics = {"process": {"pid": 12345}}
        docanalyzer_stats = {"components": {"lock_manager": "available"}}
        timestamp = "2024-01-01T00:00:00"
        
        # Act
        result = SystemStatsResult(
            system_stats=system_stats,
            performance_metrics=performance_metrics,
            docanalyzer_stats=docanalyzer_stats,
            timestamp=timestamp
        )
        
        # Assert
        assert result.system_stats == system_stats
        assert result.performance_metrics == performance_metrics
        assert result.docanalyzer_stats == docanalyzer_stats
        assert result.timestamp == timestamp
    
    def test_system_stats_result_to_dict(self):
        """Test SystemStatsResult to_dict method."""
        # Arrange
        result = SystemStatsResult(
            system_stats={"platform": {"system": "Linux"}},
            performance_metrics={"process": {"pid": 12345}},
            docanalyzer_stats={"components": {"lock_manager": "available"}},
            timestamp="2024-01-01T00:00:00"
        )
        
        # Act
        result_dict = result.to_dict()
        
        # Assert
        assert result_dict["system_stats"]["platform"]["system"] == "Linux"
        assert result_dict["performance_metrics"]["process"]["pid"] == 12345
        assert result_dict["docanalyzer_stats"]["components"]["lock_manager"] == "available"
        assert result_dict["timestamp"] == "2024-01-01T00:00:00"
        assert result_dict["command_type"] == "system_stats"
    
    def test_system_stats_result_get_schema(self):
        """Test SystemStatsResult get_schema method."""
        # Act
        schema = SystemStatsResult.get_schema()
        
        # Assert
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert "system_stats" in schema["properties"]
        assert "performance_metrics" in schema["properties"]
        assert "docanalyzer_stats" in schema["properties"]
        assert "timestamp" in schema["properties"]
        assert "command_type" in schema["properties"]


class TestSystemStatsCommand:
    """Test suite for SystemStatsCommand class."""
    
    @pytest.fixture
    def command(self):
        """Create test command instance."""
        return SystemStatsCommand()
    
    def test_system_stats_command_initialization(self, command):
        """Test SystemStatsCommand initialization."""
        # Assert
        assert command.name == "system_stats"
        assert command.result_class == SystemStatsResult
    
    def test_system_stats_command_get_schema(self, command):
        """Test SystemStatsCommand get_schema method."""
        # Act
        schema = command.get_schema()
        
        # Assert
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "description" in schema
        assert "detailed" in schema["properties"]
        assert "Get detailed system statistics and performance metrics" in schema["description"]
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_basic(self, command):
        """Test basic system stats command execution."""
        # Act
        result = await command.execute()
        
        # Assert
        assert isinstance(result, SystemStatsResult)
        assert "platform" in result.system_stats
        assert "python" in result.system_stats
        assert "cpu" in result.system_stats
        assert "memory" in result.system_stats
        assert "disk" in result.system_stats
        assert "process" in result.performance_metrics
        assert "components" in result.docanalyzer_stats
        assert result.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_detailed(self, command):
        """Test system stats command with detailed flag."""
        # Act
        result = await command.execute(detailed=True)
        
        # Assert
        assert isinstance(result, SystemStatsResult)
        # Check that detailed stats are included
        assert "detailed" in result.docanalyzer_stats or "error" in result.docanalyzer_stats.get("detailed", {})
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_with_components(self, command):
        """Test system stats with available components."""
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
                            result = await command.execute(detailed=True)
                            
                            # Assert
                            detailed = result.docanalyzer_stats.get("detailed", {})
                            if "error" not in detailed:
                                assert "lock_manager_class" in detailed
                                assert "directory_scanner_class" in detailed
                                assert "processor_classes" in detailed
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_platform_info(self, command):
        """Test system stats includes platform information."""
        # Act
        result = await command.execute()
        
        # Assert
        platform_info = result.system_stats["platform"]
        assert "system" in platform_info
        assert "release" in platform_info
        assert "version" in platform_info
        assert "machine" in platform_info
        assert "processor" in platform_info
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_python_info(self, command):
        """Test system stats includes Python information."""
        # Act
        result = await command.execute()
        
        # Assert
        python_info = result.system_stats["python"]
        assert "version" in python_info
        assert "version_info" in python_info
        assert "executable" in python_info
        assert "path" in python_info
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_cpu_info(self, command):
        """Test system stats includes CPU information."""
        # Act
        result = await command.execute()
        
        # Assert
        cpu_info = result.system_stats["cpu"]
        assert "count" in cpu_info
        assert "count_logical" in cpu_info
        assert "percent" in cpu_info
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_memory_info(self, command):
        """Test system stats includes memory information."""
        # Act
        result = await command.execute()
        
        # Assert
        memory_info = result.system_stats["memory"]
        assert "total" in memory_info
        assert "available" in memory_info
        assert "used" in memory_info
        assert "percent" in memory_info
        assert "free" in memory_info
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_disk_info(self, command):
        """Test system stats includes disk information."""
        # Act
        result = await command.execute()
        
        # Assert
        disk_info = result.system_stats["disk"]
        assert "total" in disk_info
        assert "used" in disk_info
        assert "free" in disk_info
        assert "percent" in disk_info
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_process_info(self, command):
        """Test system stats includes process information."""
        # Act
        result = await command.execute()
        
        # Assert
        process_info = result.performance_metrics["process"]
        assert "pid" in process_info
        assert "name" in process_info
        assert "memory_info" in process_info
        assert "cpu_percent" in process_info
        assert "num_threads" in process_info
        assert "create_time" in process_info
        assert "status" in process_info
    
    @pytest.mark.asyncio
    async def test_system_stats_command_execute_docanalyzer_stats(self, command):
        """Test system stats includes DocAnalyzer statistics."""
        # Act
        result = await command.execute()
        
        # Assert
        docanalyzer_stats = result.docanalyzer_stats
        assert "components" in docanalyzer_stats
        assert "capabilities" in docanalyzer_stats
        assert "status" in docanalyzer_stats
        
        components = docanalyzer_stats["components"]
        assert "lock_manager" in components
        assert "directory_scanner" in components
        assert "processors" in components
        assert "filters" in components
        
        capabilities = docanalyzer_stats["capabilities"]
        assert "supported_formats" in capabilities
        assert "processing_modes" in capabilities
        assert "lock_management" in capabilities
        assert "file_filtering" in capabilities 