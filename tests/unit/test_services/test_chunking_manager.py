"""
Tests for Chunking Manager

Comprehensive test suite for semantic chunk creation and management functionality.
"""

import pytest
import uuid
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List, Dict, Any

from docanalyzer.services.chunking_manager import (
    ChunkingManager, ChunkingResult, BatchProcessor
)
from docanalyzer.models.semantic_chunk import SemanticChunk, ChunkStatus
from docanalyzer.models.processing import ProcessingBlock, FileProcessingResult, ProcessingStatus
from docanalyzer.models.file_system.file_info import FileInfo
from docanalyzer.models.errors import ValidationError
from docanalyzer.services.vector_store_wrapper import VectorStoreWrapper


@pytest.fixture
def test_uuid():
    """Provide a valid UUID4 for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def chunking_manager():
    """Create ChunkingManager instance for testing."""
    mock_vector_store = Mock()
    mock_vector_store.create_chunks = AsyncMock()
    mock_vector_store.delete_chunks = AsyncMock()
    
    return ChunkingManager(mock_vector_store)


@pytest.fixture
def sample_processing_result(tmp_path):
    """Create sample FileProcessingResult for testing."""
    # Create a temporary file for testing
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Test content\nMore content")
    
    file_info = FileInfo(str(test_file), 1024, datetime.now())
    
    blocks = [
        ProcessingBlock(
            content="Test content",
            block_type="paragraph",
            start_line=1,
            end_line=1,
            start_char=0,
            end_char=12
        ),
        ProcessingBlock(
            content="More content",
            block_type="paragraph",
            start_line=2,
            end_line=2,
            start_char=0,
            end_char=12
        )
    ]
    
    return FileProcessingResult(str(test_file), blocks, processing_time_seconds=1.0)


class TestSemanticChunk:
    """Test suite for SemanticChunk class."""
    
    def test_semantic_chunk_creation_success(self, test_uuid):
        """Test successful SemanticChunk creation."""
        # Arrange
        source_path = "/path/to/file.txt"
        content = "Test content"
        
        # Act
        chunk = SemanticChunk(source_path, test_uuid, content)
        
        # Assert
        assert chunk.source_path == source_path
        assert chunk.source_id == test_uuid
        assert chunk.content == content
        assert chunk.status == ChunkStatus.NEW
        assert chunk.uuid is not None
        assert len(chunk.uuid) == 36  # UUID4 length
        assert chunk.metadata == {}
        assert chunk.created_at is not None
        assert chunk.updated_at is not None
    
    def test_semantic_chunk_creation_with_metadata(self, test_uuid):
        """Test SemanticChunk creation with metadata."""
        # Arrange
        metadata = {"key": "value", "number": 42}
        
        # Act
        chunk = SemanticChunk("/path/to/file.txt", test_uuid, "content", metadata=metadata)
        
        # Assert
        assert chunk.metadata == metadata
    
    def test_semantic_chunk_creation_with_custom_status(self, test_uuid):
        """Test SemanticChunk creation with custom status."""
        # Act
        chunk = SemanticChunk("/path/to/file.txt", test_uuid, "content", status=ChunkStatus.PROCESSED)
        
        # Assert
        assert chunk.status == ChunkStatus.PROCESSED
    
    def test_semantic_chunk_creation_empty_source_path(self, test_uuid):
        """Test SemanticChunk creation with empty source_path."""
        # Act & Assert
        with pytest.raises(ValidationError, match="source_path cannot be empty"):
            SemanticChunk("", test_uuid, "content")
        
        with pytest.raises(ValidationError, match="source_path cannot be empty"):
            SemanticChunk("   ", test_uuid, "content")
    
    def test_semantic_chunk_creation_empty_content(self, test_uuid):
        """Test SemanticChunk creation with empty content."""
        # Act & Assert
        with pytest.raises(ValidationError, match="content cannot be empty"):
            SemanticChunk("/path/to/file.txt", test_uuid, "")
        
        with pytest.raises(ValidationError, match="content cannot be empty"):
            SemanticChunk("/path/to/file.txt", test_uuid, "   ")
    
    def test_semantic_chunk_creation_invalid_status(self, test_uuid):
        """Test SemanticChunk creation with invalid status."""
        # Act & Assert
        with pytest.raises(ValidationError, match="Invalid status value"):
            SemanticChunk("/path/to/file.txt", test_uuid, "content", status="INVALID")
    
    def test_semantic_chunk_to_dict(self, test_uuid):
        """Test SemanticChunk to_dict method."""
        # Arrange
        chunk = SemanticChunk("/path/to/file.txt", test_uuid, "Test content")
        
        # Act
        result = chunk.to_dict()
        
        # Assert
        assert result["source_path"] == "/path/to/file.txt"
        assert result["source_id"] == test_uuid
        assert result["content"] == "Test content"
        assert result["status"] == ChunkStatus.NEW.value
        assert result["uuid"] == chunk.uuid
        assert "created_at" in result
        assert "updated_at" in result
        assert "metadata" in result
    
    def test_semantic_chunk_uuid_uniqueness(self, test_uuid):
        """Test that each SemanticChunk has a unique UUID."""
        # Act
        chunk1 = SemanticChunk("/path1.txt", test_uuid, "content1")
        chunk2 = SemanticChunk("/path2.txt", test_uuid, "content2")
        
        # Assert
        assert chunk1.uuid != chunk2.uuid
        assert chunk1.uuid != test_uuid  # UUID should be different from source_id
        assert chunk2.uuid != test_uuid
    
    def test_semantic_chunk_from_dict_success(self, test_uuid):
        """Test SemanticChunk from_dict method success."""
        # Arrange
        data = {
            "source_path": "/path/to/file.txt",
            "source_id": test_uuid,
            "content": "Test content",
            "status": "PROCESSED",
            "metadata": {"key": "value"}
        }
        
        # Act
        chunk = SemanticChunk.from_dict(data)
        
        # Assert
        assert chunk.source_path == "/path/to/file.txt"
        assert chunk.source_id == test_uuid
        assert chunk.content == "Test content"
        assert chunk.status == "PROCESSED"
        assert chunk.metadata == {"key": "value"}
    
    def test_semantic_chunk_from_dict_missing_fields(self):
        """Test SemanticChunk from_dict with missing fields."""
        # Arrange
        data = {"source_path": "/path/to/file.txt"}  # Missing required fields
    
        # Act & Assert
        with pytest.raises(ValidationError, match="Missing required field"):
            SemanticChunk.from_dict(data)
    
    @pytest.mark.asyncio
    async def test_chunk_conversion_with_standard_metadata(self, chunking_manager, sample_processing_result):
        """Test that chunk conversion uses standard metadata keys."""
        # Arrange
        blocks = sample_processing_result.blocks
        source_path = sample_processing_result.file_path
        source_id = str(uuid.uuid4())
        
        # Act
        chunks = await chunking_manager.create_chunks_from_blocks(blocks, source_path, source_id)
        
        # Assert
        assert len(chunks) == 2
        
        for i, chunk in enumerate(chunks):
            # Check standard metadata keys are present
            assert "block_index" in chunk.metadata
            assert "block_type" in chunk.metadata
            assert "start_line" in chunk.metadata
            assert "end_line" in chunk.metadata
            assert "start_char" in chunk.metadata
            assert "end_char" in chunk.metadata
            assert "processing_timestamp" in chunk.metadata
            
            # Check values
            assert chunk.metadata["block_index"] == i
            assert chunk.metadata["block_type"] == "paragraph"
            assert chunk.metadata["start_line"] == i + 1
            assert chunk.metadata["end_line"] == i + 1
            assert chunk.metadata["start_char"] == 0
            assert chunk.metadata["end_char"] == 12
            
            # Check timestamp format
            from datetime import datetime
            datetime.fromisoformat(chunk.metadata["processing_timestamp"])
    
    @pytest.mark.asyncio
    async def test_chunk_conversion_preserves_block_metadata(self, chunking_manager):
        """Test that chunk conversion preserves additional block metadata."""
        # Arrange
        block = ProcessingBlock(
            content="Test content",
            block_type="code",
            metadata={"language": "python", "complexity": "high"},
            start_line=1,
            end_line=10,
            start_char=0,
            end_char=100
        )
        source_path = "/path/to/file.py"
        source_id = str(uuid.uuid4())
        
        # Act
        chunks = await chunking_manager.create_chunks_from_blocks([block], source_path, source_id)
        
        # Assert
        assert len(chunks) == 1
        chunk = chunks[0]
        
        # Check that additional metadata is preserved
        assert chunk.metadata["language"] == "python"
        assert chunk.metadata["complexity"] == "high"
        
        # Check that standard metadata is also present
        assert "block_index" in chunk.metadata
        assert "processing_timestamp" in chunk.metadata
    
    @pytest.mark.asyncio
    async def test_chunks_have_same_source_info(self, chunking_manager, sample_processing_result):
        """Test that all chunks from the same file have the same source_id and source_path."""
        # Arrange
        blocks = sample_processing_result.blocks
        source_path = sample_processing_result.file_path
        source_id = str(uuid.uuid4())
        
        # Act
        chunks = await chunking_manager.create_chunks_from_blocks(blocks, source_path, source_id)
        
        # Assert
        assert len(chunks) == 2
        
        # All chunks should have the same source_path and source_id
        for chunk in chunks:
            assert chunk.source_path == source_path
            assert chunk.source_id == source_id
        
        # But each chunk should have a unique UUID
        chunk_uuids = [chunk.uuid for chunk in chunks]
        assert len(set(chunk_uuids)) == len(chunks)  # All UUIDs are unique
        
        # And different block_index in metadata
        block_indices = [chunk.metadata["block_index"] for chunk in chunks]
        assert len(set(block_indices)) == len(chunks)  # All indices are unique


class TestChunkingResult:
    """Test suite for ChunkingResult class."""
    
    def test_chunking_result_creation_success(self, test_uuid):
        """Test successful ChunkingResult creation."""
        # Arrange
        source_path = "/path/to/file.txt"
        
        # Act
        result = ChunkingResult(source_path, test_uuid)
        
        # Assert
        assert result.source_path == source_path
        assert result.source_id == test_uuid
        assert result.chunks_created == 0
        assert result.chunks_failed == 0
        assert result.total_blocks_processed == 0
        assert result.created_chunks == []
        assert result.errors == []
        assert result.processing_time == 0.0
    
    def test_chunking_result_creation_invalid_source_path(self, test_uuid):
        """Test ChunkingResult creation with invalid source_path."""
        # Act & Assert
        with pytest.raises(ValueError, match="source_path cannot be empty"):
            ChunkingResult("", test_uuid)
    
    def test_chunking_result_creation_invalid_source_id(self, test_uuid):
        """Test ChunkingResult creation with invalid source_id."""
        # Act & Assert
        with pytest.raises(ValueError, match="source_id cannot be empty"):
            ChunkingResult("/path/to/file.txt", "")
    
    def test_chunking_result_to_dict(self, test_uuid):
        """Test ChunkingResult to_dict method."""
        # Arrange
        result = ChunkingResult("/path/to/file.txt", test_uuid)
        
        # Act
        data = result.to_dict()
        
        # Assert
        assert data["source_path"] == "/path/to/file.txt"
        assert data["source_id"] == test_uuid
        assert data["chunks_created"] == 0
        assert data["chunks_failed"] == 0
        assert data["total_blocks_processed"] == 0
        assert data["created_chunks"] == []
        assert data["errors"] == []
        assert data["processing_time"] == 0.0


class TestBatchProcessor:
    """Test suite for BatchProcessor class."""
    
    def test_batch_processor_creation_success(self):
        """Test successful BatchProcessor creation."""
        # Act
        processor = BatchProcessor(batch_size=50)
        
        # Assert
        assert processor.batch_size == 50
        assert processor.max_retry_attempts == 3
    
    def test_batch_processor_creation_invalid_batch_size(self):
        """Test BatchProcessor creation with invalid batch_size."""
        # Act & Assert
        with pytest.raises(ValueError, match="batch_size must be positive"):
            BatchProcessor(batch_size=0)
        
        with pytest.raises(ValueError, match="batch_size must be positive"):
            BatchProcessor(batch_size=-1)
    
    @pytest.mark.asyncio
    async def test_process_batches_success(self):
        """Test successful batch processing."""
        # Arrange
        processor = BatchProcessor(batch_size=2)
        items = [1, 2, 3, 4, 5]
        
        async def mock_process_func(batch, multiplier=1):
            return [item * multiplier for item in batch]
        
        # Act
        result = await processor.process_batches(items, mock_process_func, multiplier=2)
        
        # Assert
        assert result == [2, 4, 6, 8, 10]
    
    @pytest.mark.asyncio
    async def test_process_batches_empty_list(self):
        """Test batch processing with empty list."""
        # Arrange
        processor = BatchProcessor(batch_size=2)
        
        async def mock_process_func(batch):
            return batch
        
        # Act & Assert
        with pytest.raises(ValueError, match="Items list cannot be empty"):
            await processor.process_batches([], mock_process_func)
    
    @pytest.mark.asyncio
    async def test_process_batches_invalid_func(self):
        """Test batch processing with invalid function."""
        # Arrange
        processor = BatchProcessor(batch_size=2)
        items = [1, 2, 3]
        
        # Act & Assert
        with pytest.raises(TypeError, match="process_func must be callable"):
            await processor.process_batches(items, "not_callable")


class TestChunkingManager:
    """Test suite for ChunkingManager class."""
    
    @pytest.fixture
    def mock_vector_store_wrapper(self):
        """Create mock vector store wrapper."""
        mock = Mock(spec=VectorStoreWrapper)
        mock.create_chunks = AsyncMock()
        mock.delete_chunks = AsyncMock()
        return mock
    
    @pytest.fixture
    def chunking_manager(self, mock_vector_store_wrapper):
        """Create ChunkingManager instance."""
        return ChunkingManager(
            vector_store_wrapper=mock_vector_store_wrapper,
            chunk_size=1000,
            batch_size=50
        )
    
    @pytest.fixture
    def sample_processing_result(self, tmp_path):
        """Create sample processing result."""
        # Create a temporary file for testing
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("Test content")
        
        file_info = FileInfo(
            file_path=str(test_file),
            file_size=1024,
            modification_time=datetime.now()
        )
        
        blocks = [
            ProcessingBlock(
                content="Block 1 content",
                block_type="paragraph",
                start_line=1,
                end_line=5,
                start_char=0,
                end_char=15
            ),
            ProcessingBlock(
                content="Block 2 content",
                block_type="paragraph",
                start_line=6,
                end_line=10,
                start_char=0,
                end_char=16
            )
        ]
        
        return FileProcessingResult(
            file_path=str(test_file),
            blocks=blocks,
            processing_time_seconds=1.0,
            processing_status=ProcessingStatus.COMPLETED
        )
    
    def test_chunking_manager_creation_success(self, mock_vector_store_wrapper):
        """Test successful ChunkingManager creation."""
        # Act
        manager = ChunkingManager(
            vector_store_wrapper=mock_vector_store_wrapper,
            chunk_size=1000,
            batch_size=50
        )
        
        # Assert
        assert manager.vector_store_wrapper == mock_vector_store_wrapper
        assert manager.chunk_size == 1000
        assert manager.batch_processor.batch_size == 50
        assert manager.max_retry_attempts == 3
    
    def test_chunking_manager_creation_invalid_wrapper(self):
        """Test ChunkingManager creation with invalid wrapper."""
        # Act & Assert
        with pytest.raises(ValueError, match="vector_store_wrapper cannot be None"):
            ChunkingManager(None)
    
    def test_chunking_manager_creation_invalid_chunk_size(self):
        """Test ChunkingManager creation with invalid chunk_size."""
        mock_wrapper = Mock(spec=VectorStoreWrapper)
        
        # Act & Assert
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            ChunkingManager(mock_wrapper, chunk_size=0)
    
    def test_chunking_manager_creation_invalid_batch_size(self):
        """Test ChunkingManager creation with invalid batch_size."""
        mock_wrapper = Mock(spec=VectorStoreWrapper)
        
        # Act & Assert
        with pytest.raises(ValueError, match="batch_size must be positive"):
            ChunkingManager(mock_wrapper, batch_size=0)
    
    @pytest.mark.asyncio
    async def test_create_chunks_from_blocks_success(self, chunking_manager, test_uuid):
        """Test successful chunk creation from blocks."""
        # Arrange
        from docanalyzer.models.processing import ProcessingBlock
        
        blocks = [
            ProcessingBlock(
                content="Block 1 content",
                block_type="paragraph",
                start_line=1,
                end_line=5,
                start_char=0,
                end_char=15
            ),
            ProcessingBlock(
                content="Block 2 content",
                block_type="paragraph",
                start_line=6,
                end_line=10,
                start_char=0,
                end_char=16
            )
        ]
        
        # Act
        chunks = await chunking_manager.create_chunks_from_blocks(
            blocks, "/path/to/file.txt", test_uuid
        )
        
        # Assert
        assert len(chunks) == 2
        assert chunks[0].content == "Block 1 content"
        assert chunks[0].source_path == "/path/to/file.txt"
        assert chunks[0].source_id == test_uuid
        assert chunks[0].status == "NEW"
        assert chunks[1].content == "Block 2 content"
    
    @pytest.mark.asyncio
    async def test_create_chunks_from_blocks_empty_list(self, chunking_manager, test_uuid):
        """Test chunk creation with empty blocks list."""
        # Act & Assert
        with pytest.raises(ValueError, match="Blocks list cannot be empty"):
            await chunking_manager.create_chunks_from_blocks(
                [], "/path/to/file.txt", test_uuid
            )
    
    @pytest.mark.asyncio
    async def test_create_chunks_from_blocks_empty_source_path(self, chunking_manager, test_uuid):
        """Test chunk creation with empty source_path."""
        # Arrange
        blocks = [ProcessingBlock("content", "paragraph", 1, 1, 0, 7)]
        
        # Act & Assert
        with pytest.raises(ValueError, match="source_path and source_id cannot be empty"):
            await chunking_manager.create_chunks_from_blocks(blocks, "", test_uuid)
    
    @pytest.mark.asyncio
    async def test_create_chunks_from_blocks_empty_source_id(self, chunking_manager):
        """Test chunk creation with empty source_id."""
        # Arrange
        blocks = [ProcessingBlock("content", "paragraph", 1, 1, 0, 7)]
        
        # Act & Assert
        with pytest.raises(ValueError, match="source_path and source_id cannot be empty"):
            await chunking_manager.create_chunks_from_blocks(blocks, "/path/to/file.txt", "")
    
    @pytest.mark.asyncio
    async def test_validate_chunk_success(self, chunking_manager, test_uuid):
        """Test successful chunk validation."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        
        chunk = SemanticChunk(
            source_path="/path/to/file.txt",
            source_id=test_uuid,
            content="Valid content"
        )
        
        # Act
        result = await chunking_manager.validate_chunk(chunk)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_semantic_chunk_uuid4_validation_success(self):
        """Test SemanticChunk creation with valid UUID4."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        import uuid
        
        valid_uuid = str(uuid.uuid4())
        
        # Act
        chunk = SemanticChunk(
            source_path="/path/to/file.txt",
            source_id=valid_uuid,
            content="Valid content"
        )
        
        # Assert
        assert chunk.source_id == valid_uuid
        assert chunk.uuid is not None
        assert len(chunk.uuid) == 36  # UUID4 length
        assert chunk.uuid != valid_uuid  # Different UUIDs
    
    @pytest.mark.asyncio
    async def test_semantic_chunk_uuid4_validation_failure(self):
        """Test SemanticChunk creation with invalid UUID4."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        
        # Test each invalid UUID separately
        with pytest.raises(ValidationError, match="source_id must be a valid UUID4 string"):
            SemanticChunk("/path/to/file.txt", "not-a-uuid", "Valid content")
        
        with pytest.raises(ValidationError, match="source_id cannot be empty"):
            SemanticChunk("/path/to/file.txt", "", "Valid content")
        
        with pytest.raises(ValidationError, match="source_id cannot be empty"):
            SemanticChunk("/path/to/file.txt", "   ", "Valid content")
    
    @pytest.mark.asyncio
    async def test_semantic_chunk_uuid4_validation_edge_cases(self):
        """Test SemanticChunk creation with edge case UUIDs."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        import uuid
        
        # Test with UUID4 that has leading/trailing whitespace
        valid_uuid = str(uuid.uuid4())
        uuid_with_whitespace = f"  {valid_uuid}  "
        
        # Act
        chunk = SemanticChunk(
            source_path="/path/to/file.txt",
            source_id=uuid_with_whitespace,
            content="Valid content"
        )
        
        # Assert
        assert chunk.source_id == valid_uuid  # Should be stripped
        assert chunk.uuid is not None
        assert len(chunk.uuid) == 36
    
    @pytest.mark.asyncio
    async def test_validate_chunk_invalid_instance(self, chunking_manager):
        """Test chunk validation with invalid instance."""
        # Act & Assert
        with pytest.raises(TypeError, match="chunk must be SemanticChunk instance"):
            await chunking_manager.validate_chunk("not a chunk")
    
    @pytest.mark.asyncio
    async def test_validate_chunk_empty_content(self, chunking_manager, test_uuid):
        """Test chunk validation with empty content."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        
        # This should fail at creation time due to content validation
        with pytest.raises(ValidationError, match="content cannot be empty"):
            SemanticChunk("/path/to/file.txt", test_uuid, "")
    
    @pytest.mark.asyncio
    async def test_validate_chunk_empty_source_id(self, chunking_manager):
        """Test chunk validation with empty source_id."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        
        # This should fail at creation time due to UUID validation
        with pytest.raises(ValidationError, match="source_id cannot be empty"):
            SemanticChunk("/path/to/file.txt", "", "content")
    
    @pytest.mark.asyncio
    async def test_validate_chunk_empty_source_path(self, chunking_manager, test_uuid):
        """Test chunk validation with empty source_path."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        
        # This should fail at creation time due to source_path validation
        with pytest.raises(ValidationError, match="source_path cannot be empty"):
            SemanticChunk("", test_uuid, "content")
    
    @pytest.mark.asyncio
    async def test_validate_chunk_content_too_long(self, chunking_manager, test_uuid):
        """Test chunk validation with content too long."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        
        long_content = "x" * 10001  # Exceeds 10000 character limit
        chunk = SemanticChunk("/path/to/file.txt", test_uuid, long_content)
        
        # Act
        result = await chunking_manager.validate_chunk(chunk)
        
        # Assert
        assert result is False
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, mock_client, chunking_manager):
        """Test successful embedding generation."""
        # Arrange
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            "result": {
                "success": True,
                "data": {
                    "embeddings": [[0.1] * 384]  # 384-dimensional vector
                }
            }
        })
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Act
        embedding = await chunking_manager._generate_embedding("Test text")
        
        # Assert
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_embedding_failure(self, mock_client, chunking_manager):
        """Test embedding generation failure."""
        # Arrange
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            "result": {
                "success": False,
                "error": "Embedding failed"
            }
        })
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Act & Assert
        with pytest.raises(Exception, match="Failed to generate embedding"):
            await chunking_manager._generate_embedding("Test text")
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_generate_embedding_invalid_dimensions(self, mock_client, chunking_manager):
        """Test embedding generation with invalid dimensions."""
        # Arrange
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            "result": {
                "success": True,
                "data": {
                    "embeddings": [[0.1] * 100]  # Wrong dimensions
                }
            }
        })
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Act & Assert
        with pytest.raises(Exception, match="Invalid embedding dimensions"):
            await chunking_manager._generate_embedding("Test text")
    
    @pytest.mark.asyncio
    async def test_cleanup_failed_chunks_success(self, chunking_manager, test_uuid):
        """Test successful cleanup of failed chunks."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        
        failed_chunks = [
            SemanticChunk("/path/to/file.txt", test_uuid, "content1"),
            SemanticChunk("/path/to/file.txt", test_uuid, "content2")
        ]
        
        # Act
        await chunking_manager.cleanup_failed_chunks(failed_chunks)
        
        # Assert
        chunking_manager.vector_store_wrapper.delete_chunks.assert_called_once()
        call_args = chunking_manager.vector_store_wrapper.delete_chunks.call_args[0][0]
        assert len(call_args) == 2
        assert all(isinstance(uuid, str) for uuid in call_args)
    
    @pytest.mark.asyncio
    async def test_cleanup_failed_chunks_empty_list(self, chunking_manager):
        """Test cleanup with empty failed chunks list."""
        # Act
        await chunking_manager.cleanup_failed_chunks([])
        
        # Assert
        chunking_manager.vector_store_wrapper.delete_chunks.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_failed_chunks_with_exception(self, chunking_manager, test_uuid):
        """Test cleanup with exception during deletion."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        
        chunking_manager.vector_store_wrapper.delete_chunks.side_effect = Exception("Delete failed")
        failed_chunks = [SemanticChunk("/path/to/file.txt", test_uuid, "content")]
        
        # Act - Should not raise exception
        await chunking_manager.cleanup_failed_chunks(failed_chunks)
        
        # Assert
        chunking_manager.vector_store_wrapper.delete_chunks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_chunks_atomic_success(self, chunking_manager):
        """Test successful atomic saving of chunks."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        import uuid
        
        chunk = SemanticChunk(
            source_path="/path/to/file.txt",
            source_id=str(uuid.uuid4()),
            content="Test content"
        )
        
        chunks = [chunk]
        
        # Mock validation and embedding generation
        chunking_manager.validate_chunk = AsyncMock(return_value=True)
        chunking_manager._generate_embedding = AsyncMock(return_value=[0.1] * 384)
        
        # Mock vector store response
        mock_response = Mock()
        mock_response.success = True
        mock_response.created_count = 1
        chunking_manager.vector_store_wrapper.create_chunks.return_value = mock_response
        
        # Act
        saved_count, errors = await chunking_manager.save_chunks_atomic(chunks)
        
        # Assert
        assert saved_count == 1
        assert errors == []
        chunking_manager.vector_store_wrapper.create_chunks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_chunks_atomic_empty_list(self, chunking_manager):
        """Test atomic saving with empty chunks list."""
        # Act & Assert
        with pytest.raises(ValueError, match="Chunks list cannot be empty"):
            await chunking_manager.save_chunks_atomic([])
    
    @pytest.mark.asyncio
    async def test_save_chunks_atomic_validation_failure(self, chunking_manager):
        """Test atomic saving with validation failure."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        import uuid
        
        chunk = SemanticChunk(
            source_path="/path/to/file.txt",
            source_id=str(uuid.uuid4()),
            content="Test content"
        )
        chunks = [chunk]
        
        chunking_manager.validate_chunk = AsyncMock(return_value=False)
        
        # Act
        saved_count, errors = await chunking_manager.save_chunks_atomic(chunks)
        
        # Assert
        assert saved_count == 0
        assert len(errors) == 1
        assert "Invalid chunk" in errors[0]
    
    @pytest.mark.asyncio
    async def test_save_chunks_atomic_embedding_failure(self, chunking_manager):
        """Test atomic saving with embedding generation failure."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        import uuid
        
        chunk = SemanticChunk(
            source_path="/path/to/file.txt",
            source_id=str(uuid.uuid4()),
            content="Test content"
        )
        
        chunks = [chunk]
        
        chunking_manager.validate_chunk = AsyncMock(return_value=True)
        chunking_manager._generate_embedding = AsyncMock(side_effect=Exception("Embedding failed"))
        
        # Act
        saved_count, errors = await chunking_manager.save_chunks_atomic(chunks)
        
        # Assert
        assert saved_count == 0
        assert len(errors) == 1
        assert "Error converting chunk" in errors[0]
    
    @pytest.mark.asyncio
    async def test_save_chunks_atomic_vector_store_failure(self, chunking_manager):
        """Test atomic saving with vector store failure."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        import uuid
        
        chunk = SemanticChunk(
            source_path="/path/to/file.txt",
            source_id=str(uuid.uuid4()),
            content="Test content"
        )
        
        chunks = [chunk]
        
        chunking_manager.validate_chunk = AsyncMock(return_value=True)
        chunking_manager._generate_embedding = AsyncMock(return_value=[0.1] * 384)
        
        # Mock vector store failure
        mock_response = Mock()
        mock_response.success = False
        mock_response.error = "Vector store error"
        chunking_manager.vector_store_wrapper.create_chunks.return_value = mock_response
        
        # Act
        saved_count, errors = await chunking_manager.save_chunks_atomic(chunks)
        
        # Assert
        assert saved_count == 0
        assert len(errors) == 1
        assert "Failed to save chunks" in errors[0]
    
    @pytest.mark.asyncio
    async def test_create_chunks_success(self, chunking_manager, sample_processing_result, test_uuid):
        """Test successful file blocks processing."""
        # Arrange
        from docanalyzer.services.chunking_manager import SemanticChunk
        
        chunking_manager.create_chunks_from_blocks = AsyncMock(return_value=[
            SemanticChunk("/path/to/file.txt", test_uuid, "content")
        ])
        chunking_manager.save_chunks_atomic = AsyncMock(return_value=(1, []))
        
        # Act
        result = await chunking_manager.create_chunks(sample_processing_result)
        
        # Assert
        assert result.chunks_created == 1
        assert result.chunks_failed == 0
        assert result.total_blocks_processed == 2
        assert result.source_path == sample_processing_result.file_path
        assert result.source_id is not None
        assert result.errors == []
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_create_chunks_invalid_result(self, chunking_manager, tmp_path):
        """Test file blocks processing with invalid result."""
        # Act & Assert
        with pytest.raises(ValueError, match="processing_result must contain valid blocks"):
            await chunking_manager.create_chunks(None)
        
        # Test with empty blocks
        # Create a temporary file for testing
        test_file = tmp_path / "empty_test_file.txt"
        test_file.write_text("")
        
        file_info = FileInfo(str(test_file), 1024, datetime.now())
        empty_result = FileProcessingResult(str(test_file), [], processing_time_seconds=1.0)
        
        with pytest.raises(ValueError, match="processing_result must contain valid blocks"):
            await chunking_manager.create_chunks(empty_result)
    
    @pytest.mark.asyncio
    async def test_create_chunks_with_errors(self, chunking_manager, sample_processing_result):
        """Test file blocks processing with errors."""
        # Arrange
        chunking_manager.create_chunks_from_blocks = AsyncMock(side_effect=Exception("Processing failed"))
        
        # Act
        result = await chunking_manager.create_chunks(sample_processing_result)
        
        # Assert
        assert result.chunks_created == 0
        assert result.chunks_failed == 0
        assert result.total_blocks_processed == 2
        assert len(result.errors) == 1
        assert "Chunking operation failed" in result.errors[0] 