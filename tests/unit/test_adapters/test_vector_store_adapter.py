"""
Tests for Vector Store Adapter

Unit tests for vector store adapter functionality including connection
management, chunk operations, and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from docanalyzer.adapters.vector_store_adapter import VectorStoreAdapter
from docanalyzer.config.integration import DocAnalyzerConfig
from docanalyzer.models.processing import ProcessingBlock
from docanalyzer.models.errors import ProcessingError, ValidationError, ConnectionError


class TestVectorStoreAdapter:
    """Test suite for VectorStoreAdapter class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=DocAnalyzerConfig)
        config.get_vector_store_settings.return_value = {
            'base_url': 'http://localhost',
            'port': 8007,
            'timeout': 30.0
        }
        return config
    
    @pytest.fixture
    def adapter(self, mock_config):
        """Create test adapter instance."""
        return VectorStoreAdapter(config=mock_config)
    
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
    
    def test_init_valid_parameters(self, mock_config):
        """Test initialization with valid parameters."""
        adapter = VectorStoreAdapter(
            config=mock_config,
            batch_size=50,
            retry_attempts=2,
            retry_delay=0.5
        )
        
        assert adapter.config == mock_config
        assert adapter.batch_size == 50
        assert adapter.retry_attempts == 2
        assert adapter.retry_delay == 0.5
        assert adapter.is_connected is False
        assert adapter.client is None
    
    def test_init_invalid_batch_size(self, mock_config):
        """Test initialization with invalid batch size."""
        with pytest.raises(ValueError, match="batch_size must be between 1 and 1000"):
            VectorStoreAdapter(config=mock_config, batch_size=0)
        
        with pytest.raises(ValueError, match="batch_size must be between 1 and 1000"):
            VectorStoreAdapter(config=mock_config, batch_size=1001)
    
    def test_init_invalid_retry_attempts(self, mock_config):
        """Test initialization with invalid retry attempts."""
        with pytest.raises(ValueError, match="retry_attempts must be positive"):
            VectorStoreAdapter(config=mock_config, retry_attempts=0)
    
    def test_init_invalid_retry_delay(self, mock_config):
        """Test initialization with invalid retry delay."""
        with pytest.raises(ValueError, match="retry_delay must be positive"):
            VectorStoreAdapter(config=mock_config, retry_delay=0)
    
    @pytest.mark.asyncio
    async def test_connect_success(self, adapter):
        """Test successful connection."""
        # Mock VectorStoreClient.create to prevent real connection
        with patch('docanalyzer.adapters.vector_store_adapter.VectorStoreClient.create') as mock_create:
            # Mock successful client creation
            mock_client = AsyncMock()
            mock_create.return_value = mock_client
            
            # Mock health check response
            mock_health_response = Mock()
            mock_health_response.status = "ok"
            mock_client.health_check.return_value = mock_health_response
            
            result = await adapter.connect()
            
            assert result is True
            assert adapter.is_connected is True
            assert adapter.client is not None
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, adapter):
        """Test connection failure."""
        # Mock config to raise exception
        adapter.config.get_vector_store_settings.side_effect = Exception("Config error")
        
        with pytest.raises(Exception, match="Vector store connection failed"):
            await adapter.connect()
        
        assert adapter.is_connected is False
        assert adapter.client is None
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self, adapter):
        """Test successful disconnection."""
        adapter.client = Mock()
        adapter.is_connected = True
        
        await adapter.disconnect()
        
        assert adapter.client is None
        assert adapter.is_connected is False
    
    @pytest.mark.asyncio
    async def test_disconnect_no_client(self, adapter):
        """Test disconnection when no client exists."""
        adapter.client = None
        adapter.is_connected = False
        
        # Should not raise any exception
        await adapter.disconnect()
        
        assert adapter.client is None
        assert adapter.is_connected is False
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, adapter):
        """Test successful health check."""
        adapter.client = AsyncMock()
        adapter.is_connected = True
        
        # Mock health check response
        mock_response = Mock()
        mock_response.status = "ok"
        adapter.client.health_check.return_value = mock_response
        
        result = await adapter.health_check()
        
        assert result.status == "ok"
    
    @pytest.mark.asyncio
    async def test_health_check_not_connected(self, adapter):
        """Test health check when not connected."""
        adapter.is_connected = False
        
        with pytest.raises(Exception, match="Vector store adapter is not connected"):
            await adapter.health_check()
    
    @pytest.mark.asyncio
    async def test_create_chunks_success(self, adapter, sample_processing_block):
        """Test successful chunk creation."""
        adapter.client = AsyncMock()
        adapter.is_connected = True
        
        # Mock create_chunks response
        mock_response = Mock()
        mock_response.success = True
        mock_response.uuids = ["e587072e-b016-49ef-8a1d-a17cd22d94cb"]
        mock_response.created_count = 1
        mock_response.failed_count = 0
        adapter.client.create_chunks.return_value = mock_response
        
        blocks = [sample_processing_block]
        result = await adapter.create_chunks(blocks, "/test/file.txt")
        
        assert result.success is True
        assert result.created_count == 1
        assert result.failed_count == 0
        assert len(result.uuids) == 1
    
    @pytest.mark.asyncio
    async def test_create_chunks_empty_blocks(self, adapter):
        """Test chunk creation with empty blocks list."""
        with pytest.raises(Exception, match="Processing blocks list cannot be empty"):
            await adapter.create_chunks([], "/test/file.txt")
    
    @pytest.mark.asyncio
    async def test_create_chunks_empty_source_path(self, adapter, sample_processing_block):
        """Test chunk creation with empty source path."""
        with pytest.raises(Exception, match="Source path cannot be empty"):
            await adapter.create_chunks([sample_processing_block], "")
    
    @pytest.mark.asyncio
    async def test_search_by_text_success(self, adapter):
        """Test successful text search."""
        adapter.client = AsyncMock()
        adapter.is_connected = True
        
        # Mock search response
        mock_chunk = Mock()
        mock_chunk.content = "Search result 0 for: test query"
        adapter.client.search_by_text.return_value = [mock_chunk]
        
        result = await adapter.search_by_text("test query")
        
        assert len(result) == 1
        assert result[0].content == "Search result 0 for: test query"
    
    @pytest.mark.asyncio
    async def test_search_by_text_empty_query(self, adapter):
        """Test text search with empty query."""
        with pytest.raises(Exception, match="Search text cannot be empty"):
            await adapter.search_by_text("")
    
    @pytest.mark.asyncio
    async def test_search_by_text_invalid_limit(self, adapter):
        """Test text search with invalid limit."""
        with pytest.raises(Exception, match="Limit must be positive"):
            await adapter.search_by_text("query", limit=0)
    
    @pytest.mark.asyncio
    async def test_search_by_text_invalid_threshold(self, adapter):
        """Test text search with invalid relevance threshold."""
        with pytest.raises(Exception, match="Relevance threshold must be between 0.0 and 1.0"):
            await adapter.search_by_text("query", relevance_threshold=1.5)
    
    @pytest.mark.asyncio
    async def test_search_by_metadata_success(self, adapter):
        """Test successful metadata search."""
        adapter.client = AsyncMock()
        adapter.is_connected = True
        
        # Mock search response
        mock_chunk = Mock()
        mock_chunk.content = "Metadata search result 0"
        adapter.client.search_by_metadata.return_value = [mock_chunk]
        
        metadata_filter = {"source_path": "/test/file.txt"}
        result = await adapter.search_by_metadata(metadata_filter)
        
        assert len(result) == 1
        assert result[0].content == "Metadata search result 0"
    
    @pytest.mark.asyncio
    async def test_search_by_metadata_empty_filter(self, adapter):
        """Test metadata search with empty filter."""
        with pytest.raises(Exception, match="Metadata filter cannot be empty"):
            await adapter.search_by_metadata({})
    
    @pytest.mark.asyncio
    async def test_delete_chunks_success(self, adapter):
        """Test successful chunk deletion."""
        adapter.client = AsyncMock()
        adapter.is_connected = True
        
        # Mock delete response
        mock_response = Mock()
        mock_response.success = True
        mock_response.deleted_count = 2
        mock_response.failed_count = 0
        adapter.client.delete_chunks.return_value = mock_response
        
        chunk_uuids = ["uuid1", "uuid2"]
        result = await adapter.delete_chunks(chunk_uuids)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_chunks_empty_uuids(self, adapter):
        """Test chunk deletion with empty UUIDs list."""
        with pytest.raises(Exception, match="Chunk UUIDs list cannot be empty"):
            await adapter.delete_chunks([])
    
    @pytest.mark.asyncio
    async def test_get_chunk_count_success(self, adapter):
        """Test successful chunk count retrieval."""
        adapter.client = AsyncMock()
        adapter.is_connected = True
        
        # Mock search response for count
        mock_chunk = Mock()
        adapter.client.search_chunks.return_value = [mock_chunk] * 100
        
        result = await adapter.get_chunk_count()
        
        assert result == 100
    
    def test_convert_processing_block_to_chunk(self, adapter, sample_processing_block):
        """Test conversion of processing block to chunk."""
        chunk = adapter._convert_processing_block_to_chunk(
            sample_processing_block,
            "/test/file.txt",
            "e587072e-b016-49ef-8a1d-a17cd22d94cb"
        )
        
        assert chunk.content == "Test content"
        assert chunk.source_id == "e587072e-b016-49ef-8a1d-a17cd22d94cb"
        assert chunk.source_path == "/test/file.txt"
        assert chunk.uuid is not None
    
    def test_validate_connection_success(self, adapter):
        """Test successful connection validation."""
        adapter.is_connected = True
        adapter.client = Mock()
        
        # Should not raise any exception
        adapter._validate_connection()
    
    def test_validate_connection_not_connected(self, adapter):
        """Test connection validation when not connected."""
        adapter.is_connected = False
        
        with pytest.raises(Exception, match="Vector store adapter is not connected"):
            adapter._validate_connection()
    
    def test_validate_connection_no_client(self, adapter):
        """Test connection validation when no client exists."""
        adapter.is_connected = True
        adapter.client = None
        
        with pytest.raises(Exception, match="Vector store adapter is not connected"):
            adapter._validate_connection()
    
    def test_handle_vector_store_error_connection_error(self, adapter):
        """Test handling of connection error."""
        error = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Vector store test_operation failed"):
            adapter._handle_vector_store_error(error, "test_operation") 