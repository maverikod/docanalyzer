"""
Tests for Vector Store Wrapper Service

Unit tests for vector store wrapper service functionality including
initialization, file processing, search operations, and health monitoring.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
from datetime import datetime

from docanalyzer.services.vector_store_wrapper import VectorStoreWrapper
from docanalyzer.config.integration import DocAnalyzerConfig
from docanalyzer.models.processing import ProcessingBlock
from docanalyzer.models.database import DatabaseFileRecord
from docanalyzer.models.errors import ProcessingError
from docanalyzer.models.health import HealthStatus


class TestVectorStoreWrapper:
    """Test suite for VectorStoreWrapper class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=DocAnalyzerConfig)
        return config
    
    @pytest.fixture
    def wrapper(self, mock_config):
        """Create test wrapper instance."""
        return VectorStoreWrapper(config=mock_config)
    
    @pytest.fixture
    def sample_processing_block(self):
        """Create sample processing block."""
        return ProcessingBlock(
            content="Test content",
            block_type="paragraph",
            start_line=1,
            end_line=1,
            start_char=0,
            end_char=12,
            metadata={"test": "value"}
        )
    
    @pytest.fixture
    def sample_file_record(self):
        """Create sample file record."""
        return DatabaseFileRecord(
            record_id="test-record-id",
            file_path="/test/file.txt",
            file_name="file.txt",
            file_size_bytes=1024,
            file_extension="txt",
            modification_time=datetime.now(),
            status="NEW"
        )
    
    def test_init_valid_parameters(self, mock_config):
        """Test initialization with valid parameters."""
        wrapper = VectorStoreWrapper(
            config=mock_config,
            operation_timeout=60.0,
            health_check_interval=120.0
        )
        
        assert wrapper.config == mock_config
        assert wrapper.operation_timeout == 60.0
        assert wrapper.health_check_interval == 120.0
        assert wrapper.is_initialized is False
    
    def test_init_invalid_operation_timeout(self, mock_config):
        """Test initialization with invalid operation timeout."""
        with pytest.raises(ValueError, match="operation_timeout must be positive"):
            VectorStoreWrapper(config=mock_config, operation_timeout=0)
    
    def test_init_invalid_health_check_interval(self, mock_config):
        """Test initialization with invalid health check interval."""
        with pytest.raises(ValueError, match="health_check_interval must be positive"):
            VectorStoreWrapper(config=mock_config, health_check_interval=0)
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, wrapper):
        """Test successful initialization."""
        with patch.object(wrapper.adapter, 'connect', return_value=True) as mock_connect, \
             patch.object(wrapper.health_checker, 'initialize') as mock_health_init, \
             patch.object(wrapper, 'health_check') as mock_health_check:
            
            mock_health_check.return_value = HealthStatus(
                status="healthy",
                details={},
                timestamp=datetime.now()
            )
            
            result = await wrapper.initialize()
            
            assert result is True
            assert wrapper.is_initialized is True
            mock_connect.assert_called_once()
            mock_health_init.assert_called_once()
            mock_health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_connection_failure(self, wrapper):
        """Test initialization with connection failure."""
        with patch.object(wrapper.adapter, 'connect', return_value=False):
            with pytest.raises(ProcessingError, match="Initialization failed"):
                await wrapper.initialize()
            
            assert wrapper.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_exception(self, wrapper):
        """Test initialization with exception."""
        with patch.object(wrapper.adapter, 'connect', side_effect=Exception("Connection error")):
            with pytest.raises(ProcessingError, match="Initialization failed"):
                await wrapper.initialize()
            
            assert wrapper.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_cleanup_success(self, wrapper):
        """Test successful cleanup."""
        wrapper.is_initialized = True
        
        with patch.object(wrapper.adapter, 'disconnect') as mock_disconnect, \
             patch.object(wrapper.health_checker, 'cleanup') as mock_health_cleanup:
            
            await wrapper.cleanup()
            
            assert wrapper.is_initialized is False
            mock_disconnect.assert_called_once()
            mock_health_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_exception(self, wrapper):
        """Test cleanup with exception."""
        wrapper.is_initialized = True
        
        with patch.object(wrapper.adapter, 'disconnect', side_effect=Exception("Disconnect error")):
            # Should not raise exception during cleanup
            await wrapper.cleanup()
            
            assert wrapper.is_initialized is False
    
    @pytest.mark.asyncio
    async def test_process_file_blocks_success(self, wrapper, sample_processing_block):
        """Test successful file block processing."""
        wrapper.is_initialized = True
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.created_count = 1
        mock_response.failed_count = 0
        mock_response.uuids = ["test-uuid"]
        
        with patch.object(wrapper.adapter, 'create_chunks', return_value=mock_response) as mock_create, \
             patch.object(wrapper, '_collect_operation_metrics') as mock_metrics:
            
            blocks = [sample_processing_block]
            result = await wrapper.process_file_blocks(blocks, "/test/file.txt")
            
            assert result["success"] is True
            assert result["created_count"] == 1
            assert result["failed_count"] == 0
            assert result["chunk_uuids"] == ["test-uuid"]
            assert result["file_path"] == "/test/file.txt"
            assert "processing_time" in result
            
            mock_create.assert_called_once()
            mock_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_file_blocks_with_file_record(self, wrapper, sample_processing_block, sample_file_record):
        """Test file block processing with file record."""
        wrapper.is_initialized = True
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.created_count = 1
        mock_response.failed_count = 0
        mock_response.uuids = ["test-uuid"]
        
        with patch.object(wrapper.adapter, 'create_chunks', return_value=mock_response):
            blocks = [sample_processing_block]
            result = await wrapper.process_file_blocks(blocks, "/test/file.txt", sample_file_record)
            
            assert result["source_id"] == "test-record-id"
    
    @pytest.mark.asyncio
    async def test_process_file_blocks_not_initialized(self, wrapper, sample_processing_block):
        """Test file block processing when not initialized."""
        wrapper.is_initialized = False
        
        with pytest.raises(ProcessingError, match="Vector Store Wrapper Service is not initialized"):
            await wrapper.process_file_blocks([sample_processing_block], "/test/file.txt")
    
    @pytest.mark.asyncio
    async def test_search_documents_text_success(self, wrapper):
        """Test successful text search."""
        wrapper.is_initialized = True
        
        mock_chunk = Mock()
        mock_chunk.uuid = "test-uuid"
        mock_chunk.body = "Test content"
        mock_chunk.source_path = "/test/file.txt"
        mock_chunk.source_id = "test-source-id"
        mock_chunk.type = "DocBlock"
        mock_chunk.language = "en"
        mock_chunk.status = "NEW"
        mock_chunk.created_at = "2023-01-01T00:00:00Z"
        
        with patch.object(wrapper.adapter, 'search_by_text', return_value=[mock_chunk]) as mock_search, \
             patch.object(wrapper, '_collect_operation_metrics') as mock_metrics:
            
            result = await wrapper.search_documents("test query")
            
            assert len(result) == 1
            assert result[0]["chunk_uuid"] == "test-uuid"
            assert result[0]["content"] == "Test content"
            assert result[0]["source_path"] == "/test/file.txt"
            
            mock_search.assert_called_once()
            mock_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_documents_metadata_success(self, wrapper):
        """Test successful metadata search."""
        wrapper.is_initialized = True
        
        mock_chunk = Mock()
        mock_chunk.uuid = "test-uuid"
        mock_chunk.body = "Test content"
        mock_chunk.source_path = "/test/file.txt"
        mock_chunk.source_id = "test-source-id"
        mock_chunk.type = "DocBlock"
        mock_chunk.language = "en"
        mock_chunk.status = "NEW"
        mock_chunk.created_at = "2023-01-01T00:00:00Z"
        
        with patch.object(wrapper.adapter, 'search_by_metadata', return_value=[mock_chunk]) as mock_search:
            metadata_filter = {"source_path": "/test/file.txt"}
            result = await wrapper.search_documents("test query", metadata_filter=metadata_filter)
            
            assert len(result) == 1
            mock_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file_chunks_success(self, wrapper):
        """Test successful file chunk deletion."""
        wrapper.is_initialized = True
        
        mock_chunks = [
            {"chunk_uuid": "uuid1"},
            {"chunk_uuid": "uuid2"}
        ]
        
        with patch.object(wrapper, 'get_file_chunks', return_value=mock_chunks) as mock_get, \
             patch.object(wrapper.adapter, 'delete_chunks', return_value=True) as mock_delete, \
             patch.object(wrapper, '_collect_operation_metrics') as mock_metrics:
            
            result = await wrapper.delete_file_chunks("/test/file.txt")
            
            assert result is True
            mock_get.assert_called_once()
            mock_delete.assert_called_once_with(["uuid1", "uuid2"])
            mock_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file_chunks_no_chunks(self, wrapper):
        """Test file chunk deletion when no chunks exist."""
        wrapper.is_initialized = True
        
        with patch.object(wrapper, 'get_file_chunks', return_value=[]):
            result = await wrapper.delete_file_chunks("/test/file.txt")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_file_chunks_success(self, wrapper):
        """Test successful file chunk retrieval."""
        wrapper.is_initialized = True
        
        mock_chunk = Mock()
        mock_chunk.uuid = "test-uuid"
        mock_chunk.body = "Test content"
        mock_chunk.source_path = "/test/file.txt"
        mock_chunk.source_id = "test-source-id"
        mock_chunk.type = "DocBlock"
        mock_chunk.language = "en"
        mock_chunk.status = "NEW"
        mock_chunk.created_at = "2023-01-01T00:00:00Z"
        mock_chunk.start_line = 1
        mock_chunk.end_line = 1
        mock_chunk.start_char = 0
        mock_chunk.end_char = 12
        
        with patch.object(wrapper.adapter, 'search_by_metadata', return_value=[mock_chunk]) as mock_search, \
             patch.object(wrapper, '_collect_operation_metrics') as mock_metrics:
            
            result = await wrapper.get_file_chunks("/test/file.txt")
            
            assert len(result) == 1
            assert result[0]["chunk_uuid"] == "test-uuid"
            assert result[0]["content"] == "Test content"
            assert result[0]["metadata"]["start_line"] == 1
            
            mock_search.assert_called_once()
            mock_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_vector_store_stats_success(self, wrapper):
        """Test successful vector store statistics retrieval."""
        wrapper.is_initialized = True
        
        mock_health_status = HealthStatus(
            status="healthy",
            details={"version": "1.0.0"},
            timestamp=datetime.now()
        )
        
        with patch.object(wrapper, 'health_check', return_value=mock_health_status) as mock_health, \
             patch.object(wrapper.adapter, 'get_chunk_count', return_value=100) as mock_count, \
             patch.object(wrapper.metrics_collector, 'get_metrics', return_value={"ops": 50}) as mock_metrics, \
             patch.object(wrapper.adapter, 'is_connected', True):
            
            result = await wrapper.get_vector_store_stats()
            
            assert result["chunk_count"] == 100
            assert result["health_status"] == "healthy"
            assert result["health_details"]["version"] == "1.0.0"
            assert result["performance_metrics"]["ops"] == 50
            assert result["connection_status"] == "connected"
            
            mock_health.assert_called_once()
            mock_count.assert_called_once()
            mock_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, wrapper):
        """Test successful health check."""
        wrapper.is_initialized = True
        
        mock_health_response = Mock()
        mock_health_response.status = "ok"
        mock_health_response.version = "1.0.0"
        mock_health_response.uptime = "1h"
        
        with patch.object(wrapper.adapter, 'health_check', return_value=mock_health_response) as mock_adapter_health:
            
            result = await wrapper.health_check()
            
            assert result.status == "healthy"
            assert result.details["vector_store_status"] == "ok"
            assert result.details["version"] == "1.0.0"
            
            mock_adapter_health.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, wrapper):
        """Test health check with unhealthy status."""
        wrapper.is_initialized = True
        
        mock_health_response = Mock()
        mock_health_response.status = "error"
        
        with patch.object(wrapper.adapter, 'health_check', return_value=mock_health_response):
            
            result = await wrapper.health_check()
            
            assert result.status == "unhealthy"
    
    def test_validate_initialization_success(self, wrapper):
        """Test successful initialization validation."""
        wrapper.is_initialized = True
        
        # Should not raise any exception
        wrapper._validate_initialization()
    
    def test_validate_initialization_not_initialized(self, wrapper):
        """Test initialization validation when not initialized."""
        wrapper.is_initialized = False
        
        with pytest.raises(ProcessingError, match="Vector Store Wrapper Service is not initialized"):
            wrapper._validate_initialization()
    
    def test_collect_operation_metrics_success(self, wrapper):
        """Test successful metrics collection."""
        start_time = datetime.now()
        
        with patch.object(wrapper.metrics_collector, 'record_operation') as mock_record:
            wrapper._collect_operation_metrics(
                operation="test_operation",
                start_time=start_time,
                success=True,
                result_count=5
            )
            
            mock_record.assert_called_once()
    
    def test_collect_operation_metrics_exception(self, wrapper):
        """Test metrics collection with exception."""
        start_time = datetime.now()
        
        with patch.object(wrapper.metrics_collector, 'record_operation', side_effect=Exception("Metrics error")):
            # Should not raise exception, just log warning
            wrapper._collect_operation_metrics(
                operation="test_operation",
                start_time=start_time,
                success=True,
                result_count=5
            )
    
    def test_handle_operation_error_processing_error(self, wrapper):
        """Test handling of processing error."""
        from docanalyzer.models.errors import ErrorCategory
        error = ProcessingError("test_error", "Test error", ErrorCategory.PROCESSING)
        
        with pytest.raises(ProcessingError, match="Vector store test_operation failed"):
            wrapper._handle_operation_error(error, "test_operation")
    
    def test_handle_operation_error_with_context(self, wrapper):
        """Test handling of operation error with context."""
        error = Exception("Test error")
        context = {"file_path": "/test/file.txt"}
        
        with pytest.raises(ProcessingError, match="Context: file_path=/test/file.txt"):
            wrapper._handle_operation_error(error, "test_operation", context) 