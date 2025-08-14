"""
Tests for File Processor

Comprehensive test suite for integrated file processing functionality.
Tests file processing workflow, metadata extraction, chunk creation,
and vector store integration with proper error handling.

Author: File Processing Team
Version: 1.0.0
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

from docanalyzer.services.file_processor import FileProcessor, MetadataExtractor
from docanalyzer.services.vector_store_wrapper import VectorStoreWrapper
from docanalyzer.services.database_manager import DatabaseManager
from docanalyzer.models.processing import ProcessingBlock, FileProcessingResult, ProcessingStatus
from docanalyzer.processors.text_processor import TextProcessor
from docanalyzer.processors.markdown_processor import MarkdownProcessor
from docanalyzer.models.errors import ProcessingError


class TestMetadataExtractor:
    """Test suite for MetadataExtractor class."""
    
    @pytest.fixture
    def extractor(self):
        """Create test metadata extractor."""
        return MetadataExtractor()
    
    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create temporary test file."""
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("Test content")
        return str(file_path)
    
    def test_extract_metadata_success(self, extractor, temp_file):
        """Test successful metadata extraction."""
        # Act
        metadata = extractor.extract_metadata(temp_file)
        
        # Assert
        assert isinstance(metadata, dict)
        assert "source_path" in metadata
        assert "source_id" in metadata
        assert "status" in metadata
        assert metadata["source_path"] == str(Path(temp_file).absolute())
        assert metadata["status"] == "NEW"
        # Check UUID4 format
        assert len(metadata["source_id"]) == 36
        assert metadata["source_id"].count("-") == 4
    
    def test_extract_metadata_empty_path(self, extractor):
        """Test metadata extraction with empty path."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_path must be non-empty string"):
            extractor.extract_metadata("")
    
    def test_extract_metadata_none_path(self, extractor):
        """Test metadata extraction with None path."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_path must be non-empty string"):
            extractor.extract_metadata(None)
    
    def test_extract_metadata_invalid_type(self, extractor):
        """Test metadata extraction with invalid type."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_path must be non-empty string"):
            extractor.extract_metadata(123)
    
    def test_extract_metadata_file_not_found(self, extractor):
        """Test metadata extraction with non-existent file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            extractor.extract_metadata("/nonexistent/file.txt")


class TestFileProcessor:
    """Test suite for FileProcessor class."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store wrapper."""
        mock = Mock(spec=VectorStoreWrapper)
        mock.create_chunk = AsyncMock(return_value=True)
        mock.delete_chunk = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def mock_database_manager(self):
        """Create mock database manager."""
        mock = Mock(spec=DatabaseManager)
        mock.record_file_processing = AsyncMock()
        return mock
    
    @pytest.fixture
    def file_processor(self, mock_vector_store, mock_database_manager):
        """Create test file processor."""
        return FileProcessor(
            vector_store=mock_vector_store,
            database_manager=mock_database_manager,
            chunk_size=1000,
            chunk_overlap=200
        )
    
    @pytest.fixture
    def temp_txt_file(self, tmp_path):
        """Create temporary text file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("This is a test file.\nIt has multiple lines.\nFor testing purposes.")
        return str(file_path)
    
    @pytest.fixture
    def temp_md_file(self, tmp_path):
        """Create temporary markdown file."""
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test Document\n\nThis is a **test** document.\n\n## Section\n\nContent here.")
        return str(file_path)
    
    @pytest.fixture
    def sample_blocks(self):
        """Create sample processing blocks."""
        return [
            ProcessingBlock(
                content="Block 1 content",
                block_type="text",
                start_line=1,
                end_line=1,
                start_char=0,
                end_char=15,
                metadata={"line": 1}
            ),
            ProcessingBlock(
                content="Block 2 content",
                block_type="text",
                start_line=2,
                end_line=2,
                start_char=16,
                end_char=31,
                metadata={"line": 2}
            )
        ]
    
    def test_init_success(self, mock_vector_store, mock_database_manager):
        """Test successful FileProcessor initialization."""
        # Act
        processor = FileProcessor(
            vector_store=mock_vector_store,
            database_manager=mock_database_manager
        )
        
        # Assert
        assert processor.vector_store == mock_vector_store
        assert processor.database_manager == mock_database_manager
        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 200
        assert isinstance(processor.metadata_extractor, MetadataExtractor)
        assert ".txt" in processor.processors
        assert ".md" in processor.processors
        assert isinstance(processor.processors[".txt"], TextProcessor)
        assert isinstance(processor.processors[".md"], MarkdownProcessor)
    
    def test_init_invalid_vector_store_type(self, mock_database_manager):
        """Test initialization with invalid vector store type."""
        # Act & Assert
        with pytest.raises(TypeError, match="vector_store must be VectorStoreWrapper instance"):
            FileProcessor(
                vector_store="invalid",
                database_manager=mock_database_manager
            )
    
    def test_init_invalid_database_manager_type(self, mock_vector_store):
        """Test initialization with invalid database manager type."""
        # Act & Assert
        with pytest.raises(TypeError, match="database_manager must be DatabaseManager instance"):
            FileProcessor(
                vector_store=mock_vector_store,
                database_manager="invalid"
            )
    
    def test_init_invalid_chunk_size(self, mock_vector_store, mock_database_manager):
        """Test initialization with invalid chunk size."""
        # Act & Assert
        with pytest.raises(ValueError, match="chunk_size must be positive integer"):
            FileProcessor(
                vector_store=mock_vector_store,
                database_manager=mock_database_manager,
                chunk_size=0
            )
    
    def test_init_invalid_chunk_overlap(self, mock_vector_store, mock_database_manager):
        """Test initialization with negative chunk overlap."""
        # Act & Assert
        with pytest.raises(ValueError, match="chunk_overlap must be non-negative integer"):
            FileProcessor(
                vector_store=mock_vector_store,
                database_manager=mock_database_manager,
                chunk_overlap=-1
            )
    
    def test_init_chunk_overlap_too_large(self, mock_vector_store, mock_database_manager):
        """Test initialization with chunk overlap >= chunk size."""
        # Act & Assert
        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            FileProcessor(
                vector_store=mock_vector_store,
                database_manager=mock_database_manager,
                chunk_size=1000,
                chunk_overlap=1000
            )
    
    def test_get_processor_txt_file(self, file_processor, temp_txt_file):
        """Test getting processor for .txt file."""
        # Act
        processor = file_processor._get_processor(temp_txt_file)
        
        # Assert
        assert isinstance(processor, TextProcessor)
    
    def test_get_processor_md_file(self, file_processor, temp_md_file):
        """Test getting processor for .md file."""
        # Act
        processor = file_processor._get_processor(temp_md_file)
        
        # Assert
        assert isinstance(processor, MarkdownProcessor)
    
    def test_get_processor_unsupported_extension(self, file_processor, tmp_path):
        """Test getting processor for unsupported file extension."""
        # Arrange
        file_path = tmp_path / "test.xyz"
        file_path.write_text("content")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported file extension"):
            file_processor._get_processor(str(file_path))
    
    def test_get_processor_file_not_found(self, file_processor):
        """Test getting processor for non-existent file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            file_processor._get_processor("/nonexistent/file.txt")
    
    def test_get_processor_invalid_path(self, file_processor):
        """Test getting processor with invalid path."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_path must be non-empty string"):
            file_processor._get_processor("")
    
    def test_create_chunks_from_blocks_success(self, file_processor, sample_blocks):
        """Test successful chunk creation from blocks."""
        # Arrange
        metadata = {
            "source_path": "/path/to/file.txt",
            "source_id": str(uuid4()),
            "status": "NEW"
        }
        
        # Act
        chunks = file_processor._create_chunks_from_blocks(sample_blocks, metadata)
        
        # Assert
        assert len(chunks) == 2
        for i, chunk in enumerate(chunks):
            assert "chunk_id" in chunk
            assert "content" in chunk
            assert "metadata" in chunk
            assert chunk["content"] == sample_blocks[i].content
            assert chunk["metadata"]["source_path"] == metadata["source_path"]
            assert chunk["metadata"]["source_id"] == metadata["source_id"]
            assert chunk["metadata"]["status"] == metadata["status"]
            assert chunk["metadata"]["block_type"] == sample_blocks[i].block_type
            assert chunk["metadata"]["block_index"] == i
    
    def test_create_chunks_empty_blocks(self, file_processor):
        """Test chunk creation with empty blocks."""
        # Arrange
        metadata = {
            "source_path": "/path/to/file.txt",
            "source_id": str(uuid4()),
            "status": "NEW"
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="blocks cannot be empty"):
            file_processor._create_chunks_from_blocks([], metadata)
    
    def test_create_chunks_invalid_metadata(self, file_processor, sample_blocks):
        """Test chunk creation with invalid metadata."""
        # Act & Assert
        with pytest.raises(ValueError, match="metadata must be non-empty dictionary"):
            file_processor._create_chunks_from_blocks(sample_blocks, {})
    
    def test_create_chunks_missing_metadata_keys(self, file_processor, sample_blocks):
        """Test chunk creation with missing metadata keys."""
        # Arrange
        metadata = {
            "source_path": "/path/to/file.txt"
            # Missing source_id and status
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="metadata must contain key"):
            file_processor._create_chunks_from_blocks(sample_blocks, metadata)
    
    @pytest.mark.asyncio
    async def test_store_chunks_atomic_success(self, file_processor):
        """Test successful atomic chunk storage."""
        # Arrange
        chunks = [
            {
                "chunk_id": str(uuid4()),
                "content": "Test content 1",
                "metadata": {"test": "data1"}
            },
            {
                "chunk_id": str(uuid4()),
                "content": "Test content 2",
                "metadata": {"test": "data2"}
            }
        ]
        
        # Act
        result = await file_processor._store_chunks_atomic(chunks)
        
        # Assert
        assert result is True
        assert file_processor.vector_store.create_chunk.call_count == 2
    
    @pytest.mark.asyncio
    async def test_store_chunks_atomic_empty_list(self, file_processor):
        """Test atomic chunk storage with empty list."""
        # Act
        result = await file_processor._store_chunks_atomic([])
        
        # Assert
        assert result is True
        file_processor.vector_store.create_chunk.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_store_chunks_atomic_failure(self, file_processor):
        """Test atomic chunk storage with failure."""
        # Arrange
        chunks = [
            {
                "chunk_id": str(uuid4()),
                "content": "Test content",
                "metadata": {"test": "data"}
            }
        ]
        file_processor.vector_store.create_chunk.return_value = False
        
        # Act
        result = await file_processor._store_chunks_atomic(chunks)
        
        # Assert
        assert result is False
        file_processor.vector_store.create_chunk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback_chunks_success(self, file_processor):
        """Test successful chunk rollback."""
        # Arrange
        chunk_ids = [str(uuid4()), str(uuid4())]
        
        # Act
        result = await file_processor._rollback_chunks(chunk_ids)
        
        # Assert
        assert result is True
        assert file_processor.vector_store.delete_chunk.call_count == 2
    
    @pytest.mark.asyncio
    async def test_rollback_chunks_empty_list(self, file_processor):
        """Test chunk rollback with empty list."""
        # Act
        result = await file_processor._rollback_chunks([])
        
        # Assert
        assert result is True
        file_processor.vector_store.delete_chunk.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_rollback_chunks_failure(self, file_processor):
        """Test chunk rollback with failure."""
        # Arrange
        chunk_ids = [str(uuid4())]
        file_processor.vector_store.delete_chunk.return_value = False
        
        # Act
        result = await file_processor._rollback_chunks(chunk_ids)
        
        # Assert
        assert result is False
        file_processor.vector_store.delete_chunk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_file_success(self, file_processor, temp_txt_file):
        """Test successful file processing."""
        # Arrange
        mock_processor = Mock()
        mock_result = Mock(
            success=True,
            blocks=[
                ProcessingBlock(
                    content="Test content",
                    block_type="text",
                    start_line=1,
                    end_line=1,
                    start_char=0,
                    end_char=11,
                    metadata={}
                )
            ],
            error_message=None
        )
        mock_processor.process_file = AsyncMock(return_value=mock_result)
        
        with patch.object(file_processor, '_get_processor', return_value=mock_processor):
            # Act
            result = await file_processor.process_file(temp_txt_file)
            
            # Assert
            assert result.processing_status == ProcessingStatus.COMPLETED
            assert result.file_path == temp_txt_file
            assert result.total_blocks == 1
            assert result.processing_time_seconds > 0
            assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_process_file_no_blocks(self, file_processor, temp_txt_file):
        """Test file processing with no blocks extracted."""
        # Arrange
        mock_processor = Mock()
        mock_result = Mock(
            success=True,
            blocks=[],
            error_message=None
        )
        mock_processor.process_file = AsyncMock(return_value=mock_result)
        
        with patch.object(file_processor, '_get_processor', return_value=mock_processor):
            # Act
            result = await file_processor.process_file(temp_txt_file)
            
            # Assert
            assert result.processing_status == ProcessingStatus.COMPLETED
            assert result.total_blocks == 0
    
    @pytest.mark.asyncio
    async def test_process_file_processor_failure(self, file_processor, temp_txt_file):
        """Test file processing with processor failure."""
        # Arrange
        mock_processor = Mock()
        mock_result = Mock(
            success=False,
            error_message="Processing failed"
        )
        mock_processor.process_file = AsyncMock(return_value=mock_result)
        
        with patch.object(file_processor, '_get_processor', return_value=mock_processor):
            # Act
            result = await file_processor.process_file(temp_txt_file)
            
            # Assert
            assert result.processing_status == ProcessingStatus.FAILED
            assert "Processing failed" in result.error_message
    
    @pytest.mark.asyncio
    async def test_process_file_storage_failure(self, file_processor, temp_txt_file):
        """Test file processing with storage failure."""
        # Arrange
        mock_processor = Mock()
        mock_result = Mock(
            success=True,
            blocks=[
                ProcessingBlock(
                    content="Test content",
                    block_type="text",
                    start_line=1,
                    end_line=1,
                    start_char=0,
                    end_char=11,
                    metadata={}
                )
            ],
            error_message=None
        )
        mock_processor.process_file = AsyncMock(return_value=mock_result)
        
        file_processor.vector_store.create_chunk.return_value = False
        
        with patch.object(file_processor, '_get_processor', return_value=mock_processor):
            # Act
            result = await file_processor.process_file(temp_txt_file)
            
            # Assert
            assert result.processing_status == ProcessingStatus.FAILED
            assert "Failed to store chunks" in result.error_message
    
    @pytest.mark.asyncio
    async def test_process_file_not_found(self, file_processor):
        """Test file processing with non-existent file."""
        # Act
        result = await file_processor.process_file("/nonexistent/file.txt")
        
        # Assert
        assert result.processing_status == ProcessingStatus.FAILED
        assert "File not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_process_files_batch_success(self, file_processor, temp_txt_file, temp_md_file):
        """Test successful batch file processing."""
        # Arrange
        mock_processor = Mock()
        mock_result = Mock(
            success=True,
            blocks=[
                ProcessingBlock(
                    content="Test content",
                    block_type="text",
                    start_line=1,
                    end_line=1,
                    start_char=0,
                    end_char=11,
                    metadata={}
                )
            ],
            error_message=None
        )
        mock_processor.process_file = AsyncMock(return_value=mock_result)
        
        with patch.object(file_processor, '_get_processor', return_value=mock_processor):
            # Act
            results = await file_processor.process_files_batch([temp_txt_file, temp_md_file])
            
            # Assert
            assert len(results) == 2
            assert all(result.processing_status == ProcessingStatus.COMPLETED for result in results)
    
    @pytest.mark.asyncio
    async def test_process_files_batch_empty_list(self, file_processor):
        """Test batch processing with empty list."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_paths cannot be empty"):
            await file_processor.process_files_batch([])
    
    @pytest.mark.asyncio
    async def test_process_files_batch_invalid_type(self, file_processor):
        """Test batch processing with invalid type."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_paths must be a list"):
            await file_processor.process_files_batch("not a list")
    
    @pytest.mark.asyncio
    async def test_process_files_batch_partial_failure(self, file_processor, temp_txt_file):
        """Test batch processing with partial failure."""
        # Arrange
        mock_processor = Mock()
        mock_result1 = Mock(
            success=True, 
            blocks=[ProcessingBlock(
                content="Test",
                block_type="text",
                start_line=1,
                end_line=1,
                start_char=0,
                end_char=4,
                metadata={}
            )], 
            error_message=None
        )
        mock_processor.process_file = AsyncMock(side_effect=[
            mock_result1,
            Exception("Processing error")
        ])
        
        with patch.object(file_processor, '_get_processor', return_value=mock_processor):
            # Act
            results = await file_processor.process_files_batch([temp_txt_file, temp_txt_file])
            
            # Assert
            assert len(results) == 2
            assert results[0].processing_status == ProcessingStatus.COMPLETED
            assert results[1].processing_status == ProcessingStatus.FAILED
            assert "Processing error" in results[1].error_message


class TestFileProcessorIntegration:
    """Integration tests for FileProcessor."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store wrapper."""
        mock = Mock(spec=VectorStoreWrapper)
        mock.create_chunk = AsyncMock(return_value=True)
        mock.delete_chunk = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def mock_database_manager(self):
        """Create mock database manager."""
        mock = Mock(spec=DatabaseManager)
        mock.record_file_processing = AsyncMock()
        return mock
    
    @pytest.fixture
    def file_processor(self, mock_vector_store, mock_database_manager):
        """Create test file processor."""
        return FileProcessor(
            vector_store=mock_vector_store,
            database_manager=mock_database_manager
        )
    
    @pytest.mark.asyncio
    async def test_full_processing_workflow(self, file_processor, tmp_path):
        """Test complete file processing workflow."""
        # Arrange
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test document.\nIt has multiple lines.\nFor testing purposes.")
        
        # Mock processor to return valid result
        mock_processor = Mock()
        mock_result = Mock(
            success=True,
            blocks=[
                ProcessingBlock(
                    content="This is a test document.",
                    block_type="text",
                    start_line=1,
                    end_line=1,
                    start_char=0,
                    end_char=25,
                    metadata={}
                ),
                ProcessingBlock(
                    content="It has multiple lines.",
                    block_type="text",
                    start_line=2,
                    end_line=2,
                    start_char=26,
                    end_char=47,
                    metadata={}
                )
            ],
            error_message=None
        )
        mock_processor.process_file = AsyncMock(return_value=mock_result)
        
        with patch.object(file_processor, '_get_processor', return_value=mock_processor):
            # Act
            result = await file_processor.process_file(str(test_file))
            
            # Assert
            assert result.processing_status == ProcessingStatus.COMPLETED
            assert result.file_path == str(test_file)
            assert result.total_blocks == 2
            assert result.processing_time_seconds > 0
            assert result.error_message is None
            
            # Verify database recording
            file_processor.database_manager.create_file_record.assert_called_once()
            call_args = file_processor.database_manager.create_file_record.call_args
            assert call_args[1]["file_path"] == str(test_file)
            assert call_args[1]["file_info"].processing_status == "completed"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_rollback(self, file_processor, tmp_path):
        """Test error handling and rollback functionality."""
        # Arrange
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Make storage fail after first chunk
        call_count = 0
        def mock_create_chunk(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return call_count == 1  # First call succeeds, second fails
        
        file_processor.vector_store.create_chunk = AsyncMock(side_effect=mock_create_chunk)
        
        # Mock processor to return multiple blocks
        mock_processor = Mock()
        mock_result = Mock(
            success=True,
            blocks=[
                ProcessingBlock(
                    content="Block 1",
                    block_type="text",
                    start_line=1,
                    end_line=1,
                    start_char=0,
                    end_char=7,
                    metadata={}
                ),
                ProcessingBlock(
                    content="Block 2",
                    block_type="text",
                    start_line=2,
                    end_line=2,
                    start_char=8,
                    end_char=15,
                    metadata={}
                )
            ],
            error_message=None
        )
        mock_processor.process_file = AsyncMock(return_value=mock_result)
        
        with patch.object(file_processor, '_get_processor', return_value=mock_processor):
            # Act
            result = await file_processor.process_file(str(test_file))
            
            # Assert
            assert result.processing_status == ProcessingStatus.FAILED
            assert "Failed to store chunks" in result.error_message 