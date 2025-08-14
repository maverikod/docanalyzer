"""
Extended Tests for Vector Store Adapter

Comprehensive test suite covering edge cases, error handling,
and exception scenarios for vector store adapter.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import List, Dict, Any

from docanalyzer.adapters.vector_store_adapter import VectorStoreAdapter
from docanalyzer.models.processing import ProcessingBlock
from docanalyzer.models.semantic_chunk import SemanticChunk, ChunkStatus
from docanalyzer.models.errors import ValidationError, ProcessingError, ConnectionError, ErrorCategory
from vector_store_client.exceptions import ValidationError as VSCValidationError, ConnectionError as VSCConnectionError


class TestVectorStoreAdapterExtended:
    """Extended test suite for VectorStoreAdapter."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock vector store client."""
        client = AsyncMock()
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.close = AsyncMock()
        client.health_check = AsyncMock()
        client.create_chunks = AsyncMock()
        client.search_by_text = AsyncMock()
        client.search_by_metadata = AsyncMock()
        client.delete_chunks = AsyncMock()
        client.search_chunks = AsyncMock()
        return client
    
    @pytest.fixture
    def adapter(self, mock_client):
        """Create test adapter with mock client."""
        with patch('docanalyzer.adapters.vector_store_adapter.VectorStoreClient', return_value=mock_client):
            adapter = VectorStoreAdapter()
            adapter.client = mock_client
            adapter.is_connected = True
            return adapter
    
    @pytest.fixture
    def sample_processing_blocks(self):
        """Create sample processing blocks for testing."""
        return [
            ProcessingBlock(
                content="Test content 1",
                block_type="paragraph",
                metadata={"key": "value1"},
                start_line=1,
                end_line=10,
                start_char=0,
                end_char=100
            ),
            ProcessingBlock(
                content="Test content 2",
                block_type="section",
                metadata={"key": "value2"},
                start_line=11,
                end_line=20,
                start_char=101,
                end_char=200
            )
        ]
    
    @pytest.mark.asyncio
    async def test_disconnect_exception_handling(self, adapter, mock_client):
        """Test disconnect with exception handling."""
        # Arrange
        mock_client.close.side_effect = Exception("Close error")
        
        # Act
        await adapter.disconnect()
        
        # Assert
        assert adapter.client is None
        assert adapter.is_connected is False
    
    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self, adapter, mock_client):
        """Test health_check with exception handling."""
        # Arrange
        mock_client.health_check.side_effect = Exception("Health check error")
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            await adapter.health_check()
    
    @pytest.mark.asyncio
    async def test_create_chunks_batch_failure(self, adapter, mock_client, sample_processing_blocks):
        """Test create_chunks with batch failure."""
        # Arrange
        mock_response = Mock()
        mock_response.success = False
        mock_response.created_count = 0
        mock_response.failed_count = 2
        mock_response.error_message = "Batch creation failed"
        mock_client.create_chunks.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            await adapter.create_chunks(sample_processing_blocks, "/tmp/test.txt")
    
    @pytest.mark.asyncio
    async def test_create_chunks_batch_exception(self, adapter, mock_client, sample_processing_blocks):
        """Test create_chunks with batch exception."""
        # Arrange
        mock_client.create_chunks.side_effect = Exception("Batch creation error")
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            await adapter.create_chunks(sample_processing_blocks, "/tmp/test.txt")
    
    @pytest.mark.asyncio
    async def test_create_chunks_overall_exception(self, adapter, mock_client, sample_processing_blocks):
        """Test create_chunks with overall exception."""
        # Arrange
        mock_client.create_chunks.side_effect = Exception("Overall creation error")
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            await adapter.create_chunks(sample_processing_blocks, "/tmp/test.txt")
    
    @pytest.mark.asyncio
    async def test_search_by_text_exception_handling(self, adapter, mock_client):
        """Test search_by_text with exception handling."""
        # Arrange
        mock_client.search_by_text.side_effect = Exception("Search error")
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            await adapter.search_by_text("test query")
    
    @pytest.mark.asyncio
    async def test_search_by_metadata_exception_handling(self, adapter, mock_client):
        """Test search_by_metadata with exception handling."""
        # Arrange
        mock_client.search_by_metadata.side_effect = Exception("Metadata search error")
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            await adapter.search_by_metadata({"key": "value"})
    
    @pytest.mark.asyncio
    async def test_delete_chunks_batch_failure(self, adapter, mock_client):
        """Test delete_chunks with batch failure."""
        # Arrange
        chunk_uuids = ["uuid1", "uuid2"]
        mock_response = Mock()
        mock_response.success = False
        mock_response.deleted_count = 0
        mock_response.failed_count = 2
        mock_response.error_message = "Batch deletion failed"
        mock_client.delete_chunks.return_value = mock_response
        
        # Act
        result = await adapter.delete_chunks(chunk_uuids)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_chunks_batch_exception(self, adapter, mock_client):
        """Test delete_chunks with batch exception."""
        # Arrange
        chunk_uuids = ["uuid1", "uuid2"]
        mock_client.delete_chunks.side_effect = Exception("Batch deletion error")
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            await adapter.delete_chunks(chunk_uuids)
    
    @pytest.mark.asyncio
    async def test_delete_chunks_overall_exception(self, adapter, mock_client):
        """Test delete_chunks with overall exception."""
        # Arrange
        chunk_uuids = ["uuid1", "uuid2"]
        mock_client.delete_chunks.side_effect = Exception("Overall deletion error")
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            await adapter.delete_chunks(chunk_uuids)
    
    @pytest.mark.asyncio
    async def test_get_chunk_count_exception_handling(self, adapter, mock_client):
        """Test get_chunk_count with exception handling."""
        # Arrange
        mock_client.search_chunks.side_effect = Exception("Count error")
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            await adapter.get_chunk_count()
    
    @pytest.mark.asyncio
    async def test_get_chunk_count_empty_results(self, adapter, mock_client):
        """Test get_chunk_count with empty results."""
        # Arrange
        mock_client.search_chunks.return_value = []
        
        # Act
        result = await adapter.get_chunk_count()
        
        # Assert
        assert result == 0
    
    def test_convert_processing_block_to_chunk_exception(self, adapter):
        """Test _convert_processing_block_to_chunk with exception."""
        # Arrange
        block = ProcessingBlock(
            content="test", 
            block_type="paragraph",
            start_line=1,
            end_line=10,
            start_char=0,
            end_char=100
        )
        
        # Mock SemanticChunk to raise exception
        with patch('docanalyzer.adapters.vector_store_adapter.SemanticChunk', side_effect=Exception("Chunk creation error")):
            # Act & Assert
            with pytest.raises(VSCValidationError, match="Chunk conversion failed"):
                adapter._convert_processing_block_to_chunk(block, "/tmp/test.txt", "test-id")
    
    def test_validate_connection_not_connected(self, adapter):
        """Test _validate_connection when not connected."""
        # Arrange
        adapter.is_connected = False
        adapter.client = None
        
        # Act & Assert
        with pytest.raises(VSCConnectionError, match="Vector store adapter is not connected"):
            adapter._validate_connection()
    
    def test_validate_connection_no_client(self, adapter):
        """Test _validate_connection when client is None."""
        # Arrange
        adapter.is_connected = True
        adapter.client = None
        
        # Act & Assert
        with pytest.raises(VSCConnectionError, match="Vector store adapter is not connected"):
            adapter._validate_connection()
    
    def test_handle_vector_store_error_connection_error(self, adapter):
        """Test _handle_vector_store_error with ConnectionError."""
        # Arrange
        error = VSCConnectionError("Connection failed")
        
        # Act & Assert
        with pytest.raises(VSCConnectionError, match="Vector store test_operation failed"):
            adapter._handle_vector_store_error(error, "test_operation")
    
    def test_handle_vector_store_error_validation_error(self, adapter):
        """Test _handle_vector_store_error with ValidationError."""
        # Arrange
        error = VSCValidationError("Validation failed")
        
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Vector store test_operation failed"):
            adapter._handle_vector_store_error(error, "test_operation")
    
    def test_handle_vector_store_error_generic_error(self, adapter):
        """Test _handle_vector_store_error with generic error."""
        # Arrange
        error = Exception("Generic error")
        
        # Act & Assert
        with pytest.raises(ProcessingError):
            adapter._handle_vector_store_error(error, "test_operation")
    
    @pytest.mark.asyncio
    async def test_create_chunks_empty_blocks(self, adapter):
        """Test create_chunks with empty processing blocks."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Processing blocks list cannot be empty"):
            await adapter.create_chunks([], "/tmp/test.txt")
    
    @pytest.mark.asyncio
    async def test_create_chunks_empty_source_path(self, adapter, sample_processing_blocks):
        """Test create_chunks with empty source path."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Source path cannot be empty"):
            await adapter.create_chunks(sample_processing_blocks, "")
    
    @pytest.mark.asyncio
    async def test_search_by_text_empty_query(self, adapter):
        """Test search_by_text with empty query."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Search text cannot be empty"):
            await adapter.search_by_text("")
    
    @pytest.mark.asyncio
    async def test_search_by_text_invalid_limit(self, adapter):
        """Test search_by_text with invalid limit."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Limit must be positive"):
            await adapter.search_by_text("test", limit=0)
    
    @pytest.mark.asyncio
    async def test_search_by_text_invalid_relevance_threshold(self, adapter):
        """Test search_by_text with invalid relevance threshold."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Relevance threshold must be between 0.0 and 1.0"):
            await adapter.search_by_text("test", relevance_threshold=1.5)
    
    @pytest.mark.asyncio
    async def test_search_by_text_negative_offset(self, adapter):
        """Test search_by_text with negative offset."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Offset must be non-negative"):
            await adapter.search_by_text("test", offset=-1)
    
    @pytest.mark.asyncio
    async def test_search_by_metadata_empty_filter(self, adapter):
        """Test search_by_metadata with empty filter."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Metadata filter cannot be empty"):
            await adapter.search_by_metadata({})
    
    @pytest.mark.asyncio
    async def test_search_by_metadata_invalid_limit(self, adapter):
        """Test search_by_metadata with invalid limit."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Limit must be positive"):
            await adapter.search_by_metadata({"key": "value"}, limit=0)
    
    @pytest.mark.asyncio
    async def test_search_by_metadata_invalid_relevance_threshold(self, adapter):
        """Test search_by_metadata with invalid relevance threshold."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Relevance threshold must be between 0.0 and 1.0"):
            await adapter.search_by_metadata({"key": "value"}, relevance_threshold=-0.1)
    
    @pytest.mark.asyncio
    async def test_search_by_metadata_negative_offset(self, adapter):
        """Test search_by_metadata with negative offset."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Offset must be non-negative"):
            await adapter.search_by_metadata({"key": "value"}, offset=-1)
    
    @pytest.mark.asyncio
    async def test_delete_chunks_empty_uuids(self, adapter):
        """Test delete_chunks with empty UUIDs list."""
        # Act & Assert
        with pytest.raises(VSCValidationError, match="Chunk UUIDs list cannot be empty"):
            await adapter.delete_chunks([])
    
    def test_convert_processing_block_with_optional_fields(self, adapter):
        """Test _convert_processing_block_to_chunk with optional fields."""
        # Arrange
        block = ProcessingBlock(
            content="test content",
            block_type="paragraph",
            metadata={"custom_key": "custom_value"},
            start_line=10,
            end_line=20,
            start_char=100,
            end_char=200
        )
        
        # Mock SemanticChunk to return a mock object
        mock_chunk = Mock()
        mock_chunk.body = "test content"
        mock_chunk.source_id = "test-id"
        mock_chunk.source_path = "/tmp/test.txt"
        mock_chunk.block_type = "paragraph"
        mock_chunk.start_line = 10
        mock_chunk.end_line = 20
        mock_chunk.start_char = 100
        mock_chunk.end_char = 200
        
        with patch('docanalyzer.adapters.vector_store_adapter.SemanticChunk', return_value=mock_chunk):
            # Act
            chunk = adapter._convert_processing_block_to_chunk(block, "/tmp/test.txt", "test-id")
            
            # Assert
            assert chunk.body == "test content"
            assert chunk.source_id == "test-id"
            assert chunk.source_path == "/tmp/test.txt"
            assert chunk.block_type == "paragraph"
            assert chunk.start_line == 10
            assert chunk.end_line == 20
            assert chunk.start_char == 100
            assert chunk.end_char == 200 