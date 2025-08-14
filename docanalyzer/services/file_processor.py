"""
File Processor - Integrated File Processing Service

Provides comprehensive file processing functionality that integrates
existing processors with vector store and metadata extraction capabilities.
Handles the complete workflow from file reading to chunk creation and storage.

The file processor coordinates between different processors (text, markdown),
extracts metadata, creates chunks, and stores them in the vector database.
It implements the complete processing pipeline with error handling and logging.

Author: File Processing Team
Version: 1.0.0
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from uuid import uuid4
from datetime import datetime

from docanalyzer.models.file_system import FileInfo
from docanalyzer.models.processing import ProcessingBlock, FileProcessingResult, ProcessingStatus
from docanalyzer.processors.base_processor import BaseProcessor
from docanalyzer.processors.text_processor import TextProcessor
from docanalyzer.processors.markdown_processor import MarkdownProcessor
from docanalyzer.services.vector_store_wrapper import VectorStoreWrapper
from docanalyzer.services.database_manager import DatabaseManager
from docanalyzer.models.errors import ProcessingError, ErrorCategory
from docanalyzer.utils.file_processing_logger import file_processing_logger

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


class MetadataExtractor:
    """
    Metadata Extractor - Minimal Metadata Extraction Service
    
    Extracts minimal required metadata from files for vector storage.
    Focuses on essential metadata: source_path, source_id (UUID4), and status.
    
    Attributes:
        None - Stateless service
    
    Example:
        >>> extractor = MetadataExtractor()
        >>> metadata = extractor.extract_metadata("/path/to/file.txt")
        >>> print(metadata.source_id)  # UUID4 string
    """
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract minimal metadata from file.
        
        Extracts only the essential metadata required for vector storage:
        - source_path: Path to the source file
        - source_id: UUID4 identifier for the source file
        - status: Processing status (NEW)
        
        Args:
            file_path (str): Path to the file to extract metadata from.
                Must be valid file path.
        
        Returns:
            Dict[str, Any]: Minimal metadata dictionary with keys:
                - source_path: str - Path to source file
                - source_id: str - UUID4 identifier for source
                - status: str - Processing status (NEW)
        
        Raises:
            ValueError: If file_path is empty or invalid
            FileNotFoundError: If file doesn't exist
        
        Example:
            >>> metadata = extractor.extract_metadata("/path/to/file.txt")
            >>> print(metadata["source_id"])  # "550e8400-e29b-41d4-a716-446655440000"
        """
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path must be non-empty string")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract minimal required metadata
        metadata = {
            "source_path": str(file_path_obj.absolute()),
            "source_id": str(uuid4()),
            "status": "NEW"
        }
        
        logger.debug(f"Extracted metadata for {file_path}: {metadata}")
        return metadata


class FileProcessor:
    """
    File Processor - Integrated File Processing Service
    
    Coordinates the complete file processing workflow from file reading
    to chunk creation and storage in vector database. Integrates existing
    processors with metadata extraction and vector store operations.
    
    The processor handles different file types, extracts blocks, creates
    chunks with minimal metadata, and stores them atomically in the
    vector database with proper error handling and rollback capabilities.
    
    Attributes:
        vector_store (VectorStoreWrapper): Wrapper for vector store operations
        database_manager (DatabaseManager): Manager for database operations
        metadata_extractor (MetadataExtractor): Extractor for minimal metadata
        chunk_size (int): Maximum size of text chunks
        chunk_overlap (int): Overlap between consecutive chunks
        processors (Dict[str, BaseProcessor]): Mapping of file extensions to processors
    
    Example:
        >>> processor = FileProcessor(vector_store, database_manager)
        >>> result = await processor.process_file("/path/to/document.txt")
        >>> print(result.processing_status)  # ProcessingStatus.COMPLETED
    """
    
    def __init__(
        self,
        vector_store: VectorStoreWrapper,
        database_manager: DatabaseManager,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ):
        """
        Initialize FileProcessor instance.
        
        Args:
            vector_store (VectorStoreWrapper): Wrapper for vector store operations.
                Must be initialized and connected.
            database_manager (DatabaseManager): Manager for database operations.
                Must be initialized and connected.
            chunk_size (int): Maximum size of text chunks in characters.
                Must be positive integer. Defaults to 1000.
            chunk_overlap (int): Overlap between consecutive chunks in characters.
                Must be non-negative integer. Defaults to 200.
        
        Raises:
            ValueError: If chunk_size is not positive or chunk_overlap is negative
            TypeError: If vector_store or database_manager are not of correct types
        """
        if not isinstance(vector_store, VectorStoreWrapper):
            raise TypeError("vector_store must be VectorStoreWrapper instance")
        if not isinstance(database_manager, DatabaseManager):
            raise TypeError("database_manager must be DatabaseManager instance")
        
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive integer")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative integer")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        self.vector_store = vector_store
        self.database_manager = database_manager
        self.metadata_extractor = MetadataExtractor()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize processors mapping
        self.processors = {
            ".txt": TextProcessor(),
            ".md": MarkdownProcessor()
        }
        
        logger.info(f"FileProcessor initialized with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    async def process_file(self, file_path: str) -> FileProcessingResult:
        """
        Process a single file completely.
        
        Performs the complete file processing workflow:
        1. Validates file exists and is readable
        2. Determines appropriate processor based on file extension
        3. Extracts blocks from file using processor
        4. Extracts minimal metadata (source_path, source_id, status=NEW)
        5. Creates chunks from blocks with metadata
        6. Stores chunks atomically in vector database
        7. Updates database with processing results
        8. Handles errors with rollback capabilities
        
        Args:
            file_path (str): Path to the file to process.
                Must be valid file path to supported file type.
        
        Returns:
            FileProcessingResult: Result of file processing with status,
                metadata, and processing statistics.
        
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
            ProcessingError: If file processing fails
            VectorStoreError: If vector store operations fail
            DatabaseError: If database operations fail
        
        Example:
            >>> result = await processor.process_file("/path/to/document.txt")
            >>> if result.processing_status == ProcessingStatus.COMPLETED:
            ...     print(f"Processed {result.total_blocks} blocks")
        """
        start_time = datetime.now()
        chunks_stored = []
        processing_id = None
        
        try:
            # Validate file exists and is readable
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            if not file_path_obj.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
            
            # Log processing start
            file_size = file_path_obj.stat().st_size
            file_type = file_path_obj.suffix.lower().lstrip('.') or "unknown"
            processing_id = file_processing_logger.log_processing_start(
                file_path=file_path,
                file_size=file_size,
                file_type=file_type
            )
            
            logger.info(f"Starting processing of file: {file_path}")
            
            # Get appropriate processor
            processor = self._get_processor(file_path)
            
            # Extract blocks from file
            processor_result = await processor.process_file(file_path)
            if not processor_result.success:
                raise ProcessingError(
                    error_type="ProcessingError",
                    error_message=f"Failed to process file: {processor_result.error_message}",
                    error_category=ErrorCategory.PROCESSING
                )
            
            blocks = processor_result.blocks
            if not blocks:
                logger.warning(f"No blocks extracted from file: {file_path}")
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Log processing end with no blocks
                file_processing_logger.log_processing_end(
                    processing_id=processing_id,
                    file_path=file_path,
                    success=True,
                    processing_time=processing_time,
                    chunks_created=0,
                    additional_data={"blocks_extracted": 0}
                )
                
                return FileProcessingResult(
                    file_path=file_path,
                    blocks=[],
                    processing_status=ProcessingStatus.COMPLETED,
                    processing_time_seconds=processing_time,
                    error_message=None
                )
            
            # Extract minimal metadata
            metadata = self.metadata_extractor.extract_metadata(file_path)
            
            # Create chunks from blocks
            chunks = self._create_chunks_from_blocks(blocks, metadata)
            if not chunks:
                logger.warning(f"No chunks created from blocks for file: {file_path}")
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Log processing end with no chunks
                file_processing_logger.log_processing_end(
                    processing_id=processing_id,
                    file_path=file_path,
                    success=True,
                    processing_time=processing_time,
                    chunks_created=0,
                    additional_data={"blocks_extracted": len(blocks), "chunks_created": 0}
                )
                
                return FileProcessingResult(
                    file_path=file_path,
                    blocks=blocks,
                    processing_status=ProcessingStatus.COMPLETED,
                    processing_time_seconds=processing_time,
                    error_message=None
                )
            
            # Store chunks atomically
            chunks_stored = [chunk["chunk_id"] for chunk in chunks]
            storage_success = await self._store_chunks_atomic(chunks)
            
            if not storage_success:
                # Rollback chunks if storage failed
                await self._rollback_chunks(chunks_stored)
                raise ProcessingError(
                    error_type="StorageError",
                    error_message=f"Failed to store chunks for file: {file_path}",
                    error_category=ErrorCategory.DATABASE
                )
            
            # Create FileInfo for database record
            from docanalyzer.models.file_system import FileInfo
            file_info = FileInfo(
                file_path=file_path,
                file_size=file_path_obj.stat().st_size,
                modification_time=datetime.fromtimestamp(file_path_obj.stat().st_mtime),
                processing_status="completed"
            )
            
            # Update database with processing results
            await self.database_manager.create_file_record(
                file_path=file_path,
                file_info=file_info,
                metadata={"chunks_created": len(chunks), "blocks_count": len(blocks)}
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Successfully processed file {file_path}: {len(blocks)} blocks -> {len(chunks)} chunks in {processing_time:.2f}s")
            
            # Log processing end with success
            file_processing_logger.log_processing_end(
                processing_id=processing_id,
                file_path=file_path,
                success=True,
                processing_time=processing_time,
                chunks_created=len(chunks),
                additional_data={
                    "blocks_extracted": len(blocks),
                    "chunks_created": len(chunks),
                    "storage_success": storage_success
                }
            )
            
            return FileProcessingResult(
                file_path=file_path,
                blocks=blocks,
                processing_status=ProcessingStatus.COMPLETED,
                processing_time_seconds=processing_time,
                error_message=None
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_message = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_message)
            
            # Log processing error
            if processing_id:
                file_processing_logger.log_processing_error(
                    processing_id=processing_id,
                    file_path=file_path,
                    error_type=type(e).__name__,
                    error_message=error_message,
                    additional_data={
                        "processing_time_seconds": processing_time,
                        "chunks_stored": len(chunks_stored)
                    }
                )
            
            # Rollback any stored chunks
            if chunks_stored:
                await self._rollback_chunks(chunks_stored)
            
            # Record error in database
            try:
                from docanalyzer.models.file_system import FileInfo
                file_info = FileInfo(
                    file_path=file_path,
                    file_size=0,
                    modification_time=datetime.now(),
                    processing_status="failed"
                )
                await self.database_manager.create_file_record(
                    file_path=file_path,
                    file_info=file_info,
                    metadata={"error": error_message}
                )
            except Exception as db_error:
                logger.error(f"Failed to record error in database: {db_error}")
            
            return FileProcessingResult(
                file_path=file_path,
                blocks=[],
                processing_status=ProcessingStatus.FAILED,
                processing_time_seconds=processing_time,
                error_message=error_message
            )
    
    async def process_files_batch(
        self, 
        file_paths: List[str]
    ) -> List[FileProcessingResult]:
        """
        Process multiple files in batch.
        
        Processes multiple files concurrently with proper error handling.
        Each file is processed independently, and failures in one file
        don't affect processing of other files.
        
        Args:
            file_paths (List[str]): List of file paths to process.
                Must be list of valid file paths.
        
        Returns:
            List[FileProcessingResult]: List of processing results for each file.
                Results are in same order as input file_paths.
        
        Raises:
            ValueError: If file_paths is empty or contains invalid paths
            ProcessingError: If batch processing fails
        
        Example:
            >>> results = await processor.process_files_batch([
            ...     "/path/to/file1.txt",
            ...     "/path/to/file2.md"
            ... ])
            >>> success_count = sum(1 for r in results if r.processing_status == ProcessingStatus.COMPLETED)
        """
        if not file_paths:
            raise ValueError("file_paths cannot be empty")
        
        if not isinstance(file_paths, list):
            raise ValueError("file_paths must be a list")
        
        # Validate all file paths
        for file_path in file_paths:
            if not file_path or not isinstance(file_path, str):
                raise ValueError(f"Invalid file path in list: {file_path}")
        
        # Calculate total size for batch logging
        total_size = 0
        for file_path in file_paths:
            try:
                total_size += Path(file_path).stat().st_size
            except (OSError, FileNotFoundError):
                pass  # Skip files that can't be accessed
        
        # Log batch processing start
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        file_processing_logger.log_batch_processing_start(
            batch_id=batch_id,
            file_count=len(file_paths),
            total_size=total_size
        )
        
        start_time = datetime.now()
        logger.info(f"Starting batch processing of {len(file_paths)} files")
        
        # Process files concurrently
        tasks = [self.process_file(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to FileProcessingResult
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_message = f"Batch processing failed for {file_paths[i]}: {str(result)}"
                logger.error(error_message)
                processed_results.append(FileProcessingResult(
                    file_path=file_paths[i],
                    blocks=[],
                    processing_status=ProcessingStatus.FAILED,
                    processing_time_seconds=0.0,
                    error_message=error_message
                ))
            else:
                processed_results.append(result)
        
        # Calculate batch statistics
        total_processing_time = (datetime.now() - start_time).total_seconds()
        success_count = sum(1 for r in processed_results if r.processing_status == ProcessingStatus.COMPLETED)
        failed_count = len(processed_results) - success_count
        
        # Log batch processing end
        file_processing_logger.log_batch_processing_end(
            batch_id=batch_id,
            processed_count=len(processed_results),
            success_count=success_count,
            failed_count=failed_count,
            total_processing_time=total_processing_time
        )
        
        logger.info(f"Batch processing completed: {success_count}/{len(file_paths)} files successful")
        
        return processed_results
    
    def _get_processor(self, file_path: str) -> BaseProcessor:
        """
        Get appropriate processor for file type.
        
        Determines the correct processor based on file extension.
        Supports .txt files (TextProcessor) and .md files (MarkdownProcessor).
        
        Args:
            file_path (str): Path to file to determine processor for.
                Must be valid file path.
        
        Returns:
            BaseProcessor: Appropriate processor instance for file type.
        
        Raises:
            ValueError: If file extension is not supported
            FileNotFoundError: If file doesn't exist
        
        Example:
            >>> processor = file_processor._get_processor("/path/to/file.txt")
            >>> isinstance(processor, TextProcessor)  # True
        """
        if not file_path or not isinstance(file_path, str):
            raise ValueError("file_path must be non-empty string")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = file_path_obj.suffix.lower()
        if file_extension not in self.processors:
            supported_extensions = list(self.processors.keys())
            raise ValueError(f"Unsupported file extension '{file_extension}'. Supported: {supported_extensions}")
        
        processor = self.processors[file_extension]
        logger.debug(f"Selected processor {type(processor).__name__} for file {file_path}")
        return processor
    
    def _create_chunks_from_blocks(
        self, 
        blocks: List[ProcessingBlock], 
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create chunks from processing blocks with metadata.
        
        Converts processing blocks into chunks suitable for vector storage.
        Each chunk includes the minimal required metadata:
        - source_path: Path to source file
        - source_id: UUID4 identifier for source
        - status: Processing status (NEW)
        - chunk_id: UUID4 identifier for chunk (auto-generated)
        - content: Text content from block
        - metadata: Additional block metadata
        
        Args:
            blocks (List[ProcessingBlock]): Processing blocks from file.
                Must be list of valid ProcessingBlock instances.
            metadata (Dict[str, Any]): Minimal metadata for chunks.
                Must contain source_path, source_id, and status.
        
        Returns:
            List[Dict[str, Any]]: List of chunk dictionaries ready for vector storage.
                Each chunk has content, chunk_id, and metadata fields.
        
        Raises:
            ValueError: If blocks is empty or metadata is invalid
            TypeError: If blocks contains invalid ProcessingBlock instances
        
        Example:
            >>> chunks = processor._create_chunks_from_blocks(blocks, metadata)
            >>> for chunk in chunks:
            ...     print(chunk["chunk_id"])  # UUID4 string
        """
        if not blocks:
            raise ValueError("blocks cannot be empty")
        
        if not isinstance(blocks, list):
            raise ValueError("blocks must be a list")
        
        if not metadata or not isinstance(metadata, dict):
            raise ValueError("metadata must be non-empty dictionary")
        
        required_metadata_keys = ["source_path", "source_id", "status"]
        for key in required_metadata_keys:
            if key not in metadata:
                raise ValueError(f"metadata must contain key: {key}")
        
        chunks = []
        
        for i, block in enumerate(blocks):
            if not isinstance(block, ProcessingBlock):
                raise TypeError(f"Block at index {i} is not ProcessingBlock instance")
            
            # Create chunk with minimal metadata
            chunk = {
                "chunk_id": str(uuid4()),
                "content": block.content,
                "metadata": {
                    "source_path": metadata["source_path"],
                    "source_id": metadata["source_id"],
                    "status": metadata["status"],
                    "block_type": block.block_type,
                    "block_index": i,
                    "block_metadata": block.metadata or {}
                }
            }
            
            chunks.append(chunk)
        
        logger.debug(f"Created {len(chunks)} chunks from {len(blocks)} blocks")
        return chunks
    
    async def _store_chunks_atomic(
        self, 
        chunks: List[Dict[str, Any]]
    ) -> bool:
        """
        Store chunks atomically in vector database.
        
        Stores all chunks in a single atomic transaction. If any chunk
        fails to store, all chunks are rolled back to maintain consistency.
        
        Args:
            chunks (List[Dict[str, Any]]): Chunks to store in vector database.
                Must be list of valid chunk dictionaries.
        
        Returns:
            bool: True if all chunks stored successfully, False otherwise.
        
        Raises:
            VectorStoreError: If vector store operations fail
            DatabaseError: If database operations fail
        
        Example:
            >>> success = await processor._store_chunks_atomic(chunks)
            >>> if success:
            ...     print("All chunks stored successfully")
        """
        if not chunks:
            logger.warning("No chunks to store")
            return True
        
        if not isinstance(chunks, list):
            raise ValueError("chunks must be a list")
        
        stored_chunk_ids = []
        
        try:
            # Store each chunk individually (atomicity handled by rollback)
            for chunk in chunks:
                if not isinstance(chunk, dict):
                    raise ValueError("Each chunk must be a dictionary")
                
                required_chunk_keys = ["chunk_id", "content", "metadata"]
                for key in required_chunk_keys:
                    if key not in chunk:
                        raise ValueError(f"Chunk missing required key: {key}")
                
                # Store chunk in vector database
                success = await self.vector_store.create_chunk(
                    chunk_id=chunk["chunk_id"],
                    content=chunk["content"],
                    metadata=chunk["metadata"]
                )
                
                if not success:
                    logger.error(f"Failed to store chunk {chunk['chunk_id']}")
                    # Rollback all previously stored chunks
                    if stored_chunk_ids:
                        await self._rollback_chunks(stored_chunk_ids)
                    return False
                
                stored_chunk_ids.append(chunk["chunk_id"])
                logger.debug(f"Stored chunk {chunk['chunk_id']}")
            
            logger.info(f"Successfully stored {len(chunks)} chunks atomically")
            return True
            
        except Exception as e:
            logger.error(f"Error storing chunks atomically: {e}")
            # Rollback all stored chunks
            if stored_chunk_ids:
                await self._rollback_chunks(stored_chunk_ids)
            return False
    
    async def _rollback_chunks(
        self, 
        chunk_ids: List[str]
    ) -> bool:
        """
        Rollback chunks from vector database.
        
        Removes chunks from vector database in case of processing failure.
        Used to maintain consistency when atomic storage fails.
        
        Args:
            chunk_ids (List[str]): List of chunk IDs to rollback.
                Must be list of valid UUID4 strings.
        
        Returns:
            bool: True if rollback successful, False otherwise.
        
        Raises:
            VectorStoreError: If vector store operations fail
            DatabaseError: If database operations fail
        
        Example:
            >>> success = await processor._rollback_chunks(chunk_ids)
            >>> if success:
            ...     print("Rollback completed successfully")
        """
        if not chunk_ids:
            logger.warning("No chunk IDs to rollback")
            return True
        
        if not isinstance(chunk_ids, list):
            raise ValueError("chunk_ids must be a list")
        
        rollback_failures = []
        
        try:
            logger.info(f"Starting rollback of {len(chunk_ids)} chunks")
            
            # Delete each chunk individually
            for chunk_id in chunk_ids:
                if not isinstance(chunk_id, str):
                    logger.warning(f"Invalid chunk_id type: {type(chunk_id)}")
                    continue
                
                try:
                    success = await self.vector_store.delete_chunk(chunk_id)
                    if not success:
                        rollback_failures.append(chunk_id)
                        logger.error(f"Failed to rollback chunk {chunk_id}")
                    else:
                        logger.debug(f"Rolled back chunk {chunk_id}")
                        
                except Exception as e:
                    rollback_failures.append(chunk_id)
                    logger.error(f"Error rolling back chunk {chunk_id}: {e}")
            
            if rollback_failures:
                logger.error(f"Rollback completed with {len(rollback_failures)} failures: {rollback_failures}")
                return False
            else:
                logger.info(f"Successfully rolled back all {len(chunk_ids)} chunks")
                return True
                
        except Exception as e:
            logger.error(f"Error during rollback operation: {e}")
            return False 