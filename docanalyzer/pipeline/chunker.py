"""
Text Block Chunker.

Converts structured text blocks into semantic chunks suitable for vector storage.
"""

import re
from typing import List, Optional, Dict, Any
import logging
from dataclasses import dataclass
import uuid
from datetime import datetime, timezone

from chunk_metadata_adapter import SemanticChunk, ChunkMetadataBuilder
from chunk_metadata_adapter.data_types import ChunkType, LanguageEnum, ChunkRole, ChunkStatus
from vector_store_client.models import SemanticChunk as VectorSemanticChunk

from ..filters.base import TextBlock, FileStructure


@dataclass
class ChunkingConfig:
    """Configuration for text block chunking."""
    
    # Size constraints
    max_chunk_size: int = 1000
    min_chunk_size: int = 50
    overlap_size: int = 100
    
    # Quality filters
    min_importance_score: float = 0.1
    min_complexity_score: float = 0.0
    
    # Processing options
    preserve_structure: bool = True
    merge_small_blocks: bool = True
    split_large_blocks: bool = True
    
    # Metadata options
    include_surrounding_context: bool = True
    context_lines: int = 3


class TextBlockChunker:
    """
    Chunker that converts structured text blocks into semantic chunks.
    
    Takes the output from file filters (TextBlock objects) and creates
    chunks suitable for vector storage and semantic search.
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        """
        Initialize the chunker.
        
        Args:
            config: Optional chunking configuration
        """
        self.config = config or ChunkingConfig()
        self.logger = logging.getLogger("text_block_chunker")
        self.metadata_builder = ChunkMetadataBuilder()
    
    def chunk_file_structure(self, file_structure: FileStructure, 
                           project_name: Optional[str] = None) -> List[VectorSemanticChunk]:
        """
        Convert a file structure into semantic chunks.
        
        Args:
            file_structure: Parsed file structure with text blocks
            project_name: Optional project name for metadata
            
        Returns:
            List of semantic chunks ready for vector storage
        """
        chunks = []
        
        # Filter blocks based on quality thresholds
        filtered_blocks = self._filter_blocks(file_structure.blocks)
        
        # Process blocks based on configuration
        if self.config.preserve_structure:
            chunks = self._chunk_with_structure(filtered_blocks, file_structure, project_name)
        else:
            chunks = self._chunk_by_size(filtered_blocks, file_structure, project_name)
        
        # Post-process chunks
        chunks = self._post_process_chunks(chunks, file_structure)
        
        self.logger.info(
            f"Created {len(chunks)} chunks from {len(filtered_blocks)} blocks "
            f"in {file_structure.file_path}"
        )
        
        return chunks
    
    def _filter_blocks(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """
        Filter blocks based on quality thresholds.
        
        Args:
            blocks: List of text blocks
            
        Returns:
            Filtered list of blocks
        """
        filtered = []
        
        for block in blocks:
            # Skip blocks below importance threshold
            if block.importance_score < self.config.min_importance_score:
                continue
            
            # Skip blocks below complexity threshold
            if block.complexity_score < self.config.min_complexity_score:
                continue
            
            # Skip very small blocks unless they're important
            if (len(block.content) < self.config.min_chunk_size and 
                block.importance_score < 0.7):
                continue
            
            filtered.append(block)
        
        self.logger.debug(f"Filtered {len(blocks)} blocks to {len(filtered)}")
        return filtered
    
    def _chunk_with_structure(self, blocks: List[TextBlock], 
                             file_structure: FileStructure,
                             project_name: Optional[str]) -> List[VectorSemanticChunk]:
        """
        Create chunks while preserving block structure.
        
        Args:
            blocks: List of text blocks
            file_structure: File structure metadata
            project_name: Optional project name
            
        Returns:
            List of semantic chunks
        """
        chunks = []
        
        for block in blocks:
            if len(block.content) <= self.config.max_chunk_size:
                # Block fits in one chunk
                chunk = self._create_chunk_from_block(block, file_structure, project_name)
                chunks.append(chunk)
            
            elif self.config.split_large_blocks:
                # Split large block into multiple chunks
                block_chunks = self._split_large_block(block, file_structure, project_name)
                chunks.extend(block_chunks)
            
            else:
                # Keep large block as single chunk (truncated if necessary)
                chunk = self._create_chunk_from_block(
                    block, file_structure, project_name, truncate=True
                )
                chunks.append(chunk)
        
        # Merge small adjacent blocks if configured
        if self.config.merge_small_blocks:
            chunks = self._merge_small_chunks(chunks)
        
        return chunks
    
    def _chunk_by_size(self, blocks: List[TextBlock], 
                      file_structure: FileStructure,
                      project_name: Optional[str]) -> List[VectorSemanticChunk]:
        """
        Create chunks based on size constraints only.
        
        Args:
            blocks: List of text blocks
            file_structure: File structure metadata
            project_name: Optional project name
            
        Returns:
            List of semantic chunks
        """
        chunks = []
        current_chunk_content = []
        current_chunk_size = 0
        current_chunk_blocks = []
        
        for block in blocks:
            block_size = len(block.content)
            
            # Check if adding this block would exceed max size
            if (current_chunk_size + block_size > self.config.max_chunk_size and 
                current_chunk_content):
                
                # Create chunk from accumulated content
                chunk = self._create_chunk_from_multiple_blocks(
                    current_chunk_blocks, file_structure, project_name
                )
                chunks.append(chunk)
                
                # Reset accumulator
                current_chunk_content = []
                current_chunk_size = 0
                current_chunk_blocks = []
            
            # Add block to current chunk
            current_chunk_content.append(block.content)
            current_chunk_size += block_size
            current_chunk_blocks.append(block)
        
        # Create final chunk if there's remaining content
        if current_chunk_content:
            chunk = self._create_chunk_from_multiple_blocks(
                current_chunk_blocks, file_structure, project_name
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_large_block(self, block: TextBlock, 
                          file_structure: FileStructure,
                          project_name: Optional[str]) -> List[VectorSemanticChunk]:
        """
        Split a large block into multiple chunks.
        
        Args:
            block: Large text block to split
            file_structure: File structure metadata
            project_name: Optional project name
            
        Returns:
            List of chunks from the split block
        """
        chunks = []
        content = block.content
        
        # Try to split on natural boundaries
        split_points = self._find_split_points(content, block.block_type)
        
        if not split_points:
            # Fall back to character-based splitting
            split_points = list(range(
                self.config.max_chunk_size, 
                len(content), 
                self.config.max_chunk_size - self.config.overlap_size
            ))
        
        start = 0
        for i, split_point in enumerate(split_points):
            end = min(split_point + self.config.overlap_size, len(content))
            chunk_content = content[start:end]
            
            # Create sub-block for this chunk
            sub_block = TextBlock(
                content=chunk_content,
                block_type=block.block_type,
                language=block.language,
                start_line=block.start_line,
                end_line=block.end_line,
                start_offset=block.start_offset + start,
                end_offset=block.start_offset + end,
                level=block.level,
                parent_id=block.block_id,
                title=f"{block.title} (part {i+1})" if block.title else None,
                metadata={**block.metadata, "is_split_chunk": True, "part_number": i+1},
                complexity_score=block.complexity_score,
                importance_score=block.importance_score
            )
            
            chunk = self._create_chunk_from_block(sub_block, file_structure, project_name)
            chunks.append(chunk)
            
            start = split_point
            if start >= len(content):
                break
        
        return chunks
    
    def _find_split_points(self, content: str, block_type) -> List[int]:
        """
        Find natural split points in content.
        
        Args:
            content: Text content to split
            block_type: Type of the text block
            
        Returns:
            List of character positions for splitting
        """
        split_points = []
        
        # For code blocks, split on function/class boundaries
        if block_type.value in ['function', 'class', 'code_block']:
            # Look for function definitions
            func_pattern = re.compile(r'\n\s*(def |class |async def )', re.MULTILINE)
            for match in func_pattern.finditer(content):
                if match.start() > self.config.min_chunk_size:
                    split_points.append(match.start())
        
        # For regular text, split on paragraph boundaries
        else:
            para_pattern = re.compile(r'\n\s*\n', re.MULTILINE)
            for match in para_pattern.finditer(content):
                if match.start() > self.config.min_chunk_size:
                    split_points.append(match.start())
        
        # Ensure splits respect size constraints
        filtered_points = []
        for point in split_points:
            if (point >= self.config.min_chunk_size and 
                point <= len(content) - self.config.min_chunk_size):
                filtered_points.append(point)
        
        return filtered_points
    
    def _create_chunk_from_block(self, block: TextBlock, 
                                file_structure: FileStructure,
                                project_name: Optional[str],
                                truncate: bool = False) -> VectorSemanticChunk:
        """
        Create a semantic chunk from a single text block.
        
        Args:
            block: Text block to convert
            file_structure: File structure metadata
            project_name: Optional project name
            truncate: Whether to truncate content if too large
            
        Returns:
            Semantic chunk for vector storage
        """
        content = block.content
        if truncate and len(content) > self.config.max_chunk_size:
            content = content[:self.config.max_chunk_size]
        
        # Generate source_id from file path
        source_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(file_structure.file_path)))
        
        # Create the chunk using vector_store_client model
        chunk = VectorSemanticChunk(
            body=content,
            source_id=source_id,
            embedding=[],  # Will be filled later by embedding service
            
            # Basic metadata
            text=self._normalize_text(content),
            type=self._determine_chunk_type(block, file_structure),
            language=block.language or file_structure.language,
            role=ChunkRole.USER,
            status=self._determine_chunk_status(block, file_structure),
            
            # Position metadata
            ordinal=block.start_line,
            start=block.start_offset,
            end=block.end_offset,
            source_lines_start=block.start_line,
            source_lines_end=block.end_line,
            source_path=str(file_structure.file_path),
            
            # File metadata
            project=project_name,
            category=self._get_category_from_language(file_structure.language),
            title=block.title,
            
            # Quality metrics
            quality_score=self._calculate_quality_score(block, content),
            coverage=min(len(content) / self.config.max_chunk_size, 1.0),
            cohesion=block.complexity_score,
            
            # Block-specific metadata
            block_type=block.block_type_for_metadata,
            tags=block.tags + [block.block_type.value],
            
            # Additional metadata
            **self._create_additional_metadata(block, file_structure)
        )
        
        return chunk
    
    def _create_chunk_from_multiple_blocks(self, blocks: List[TextBlock],
                                          file_structure: FileStructure,
                                          project_name: Optional[str]) -> VectorSemanticChunk:
        """
        Create a semantic chunk from multiple text blocks.
        
        Args:
            blocks: List of text blocks to combine
            file_structure: File structure metadata
            project_name: Optional project name
            
        Returns:
            Combined semantic chunk
        """
        if not blocks:
            raise ValueError("Cannot create chunk from empty block list")
        
        # Combine content
        combined_content = '\n\n'.join(block.content for block in blocks)
        
        # Use first block for primary metadata
        primary_block = blocks[0]
        last_block = blocks[-1]
        
        # Calculate combined metrics
        avg_importance = sum(b.importance_score for b in blocks) / len(blocks)
        avg_complexity = sum(b.complexity_score for b in blocks) / len(blocks)
        
        # Generate source_id
        source_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(file_structure.file_path)))
        
        chunk = VectorSemanticChunk(
            body=combined_content,
            source_id=source_id,
            embedding=[],
            
            text=self._normalize_text(combined_content),
            type=self._determine_chunk_type(primary_block, file_structure),
            language=primary_block.language or file_structure.language,
            role=ChunkRole.USER,
            status=self._determine_chunk_status(primary_block, file_structure),
            
            ordinal=primary_block.start_line,
            start=primary_block.start_offset,
            end=last_block.end_offset,
            source_lines_start=primary_block.start_line,
            source_lines_end=last_block.end_line,
            source_path=str(file_structure.file_path),
            
            project=project_name,
            category=self._get_category_from_language(file_structure.language),
            title=f"Combined: {', '.join(b.title for b in blocks[:3] if b.title)}",
            
            quality_score=avg_importance,
            coverage=min(len(combined_content) / self.config.max_chunk_size, 1.0),
            cohesion=avg_complexity,
            
            block_type=primary_block.block_type_for_metadata,
            tags=list(set(tag for block in blocks for tag in block.tags)),
            
            **self._create_additional_metadata(primary_block, file_structure, is_combined=True)
        )
        
        return chunk
    
    def _normalize_text(self, content: str) -> str:
        """
        Normalize text for search indexing.
        
        Args:
            content: Raw text content
            
        Returns:
            Normalized text
        """
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', content)
        
        # Remove special characters for code
        if any(keyword in content for keyword in ['def ', 'class ', 'import ', 'function']):
            # Keep code structure but normalize whitespace
            normalized = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        return normalized.strip()
    
    def _calculate_quality_score(self, block: TextBlock, content: str) -> float:
        """
        Calculate quality score for a chunk.
        
        Args:
            block: Original text block
            content: Chunk content (might be truncated)
            
        Returns:
            Quality score between 0 and 1
        """
        score = block.importance_score
        
        # Adjust for content completeness
        if len(content) < len(block.content):
            completeness = len(content) / len(block.content)
            score *= completeness
        
        # Adjust for content length
        ideal_length = self.config.max_chunk_size * 0.7
        length_factor = min(len(content) / ideal_length, 1.0)
        score = (score + length_factor) / 2
        
        return min(score, 1.0)
    
    def _get_category_from_language(self, language: LanguageEnum) -> str:
        """Get category based on language."""
        language_categories = {
            LanguageEnum.PYTHON: "code",
            LanguageEnum.JAVASCRIPT: "code", 
            LanguageEnum.TYPESCRIPT: "code",
            LanguageEnum.JAVA: "code",
            LanguageEnum.CPP: "code",
            LanguageEnum.MARKDOWN: "documentation",
            LanguageEnum.HTML: "web",
            LanguageEnum.CSS: "web",
            LanguageEnum.JSON: "data",
            LanguageEnum.YAML: "configuration",
            LanguageEnum.XML: "data"
        }
        
        return language_categories.get(language, "text")
    
    def _create_additional_metadata(self, block: TextBlock, 
                                   file_structure: FileStructure,
                                   is_combined: bool = False) -> Dict[str, Any]:
        """
        Create additional metadata for the chunk.
        
        Args:
            block: Primary text block
            file_structure: File structure
            is_combined: Whether chunk combines multiple blocks
            
        Returns:
            Additional metadata dictionary
        """
        metadata = {
            # Block metadata
            "block_id": block.block_id,
            "block_type": block.block_type.value,
            "block_level": block.level,
            "is_combined_chunk": is_combined,
            
            # File metadata
            "file_size": file_structure.file_size,
            "file_hash": file_structure.file_hash,
            "filter_name": file_structure.filter_name,
            "filter_version": file_structure.filter_version,
            
            # Processing metadata
            "chunked_at": datetime.now(timezone.utc).isoformat(),
            "chunker_config": {
                "max_chunk_size": self.config.max_chunk_size,
                "overlap_size": self.config.overlap_size,
                "preserve_structure": self.config.preserve_structure
            }
        }
        
        # Add block-specific metadata
        metadata.update(block.metadata)
        
        return metadata
    
    def _merge_small_chunks(self, chunks: List[VectorSemanticChunk]) -> List[VectorSemanticChunk]:
        """
        Merge small adjacent chunks.
        
        Args:
            chunks: List of chunks to potentially merge
            
        Returns:
            List with small chunks merged
        """
        if not chunks:
            return chunks
        
        merged = []
        current_chunk = chunks[0]
        
        for next_chunk in chunks[1:]:
            # Check if chunks should be merged
            combined_size = len(current_chunk.body) + len(next_chunk.body)
            
            if (combined_size <= self.config.max_chunk_size and
                len(current_chunk.body) < self.config.min_chunk_size * 2 and
                self._chunks_are_adjacent(current_chunk, next_chunk)):
                
                # Merge chunks
                current_chunk = self._merge_two_chunks(current_chunk, next_chunk)
            else:
                # Keep current chunk and move to next
                merged.append(current_chunk)
                current_chunk = next_chunk
        
        # Add the last chunk
        merged.append(current_chunk)
        
        return merged
    
    def _chunks_are_adjacent(self, chunk1: VectorSemanticChunk, 
                            chunk2: VectorSemanticChunk) -> bool:
        """Check if two chunks are adjacent in the source."""
        return (chunk1.source_path == chunk2.source_path and
                abs((chunk1.end or 0) - (chunk2.start or 0)) < 100)  # Allow small gaps
    
    def _merge_two_chunks(self, chunk1: VectorSemanticChunk, 
                         chunk2: VectorSemanticChunk) -> VectorSemanticChunk:
        """Merge two chunks into one."""
        # Create new merged chunk
        merged_body = chunk1.body + "\n\n" + chunk2.body
        
        # Use chunk1 as base and update relevant fields
        merged_chunk = VectorSemanticChunk(
            body=merged_body,
            source_id=chunk1.source_id,
            embedding=[],
            
            text=self._normalize_text(merged_body),
            type=chunk1.type,
            language=chunk1.language,
            role=chunk1.role,
            status=chunk1.status,
            
            ordinal=chunk1.ordinal,
            start=chunk1.start,
            end=chunk2.end,
            source_lines_start=chunk1.source_lines_start,
            source_lines_end=chunk2.source_lines_end,
            source_path=chunk1.source_path,
            
            project=chunk1.project,
            category=chunk1.category,
            title=f"Merged: {chunk1.title or ''} + {chunk2.title or ''}".strip(' +'),
            
            quality_score=(chunk1.quality_score + chunk2.quality_score) / 2,
            coverage=min(len(merged_body) / self.config.max_chunk_size, 1.0),
            cohesion=(chunk1.cohesion or 0 + chunk2.cohesion or 0) / 2,
            
            block_type=chunk1.block_type,
            tags=list(set((chunk1.tags or []) + (chunk2.tags or []))),
        )
        
        return merged_chunk
    
    def _determine_chunk_type(self, block: TextBlock, file_structure: FileStructure) -> ChunkType:
        """
        Determine appropriate ChunkType based on block and file context.
        
        Args:
            block: Text block
            file_structure: File structure metadata
            
        Returns:
            Appropriate ChunkType
        """
        # Check for draft/temporary files
        file_name = file_structure.file_path.name.lower()
        if "draft" in file_name or "tmp" in file_name or "temp" in file_name:
            return ChunkType.DRAFT
        
        # Map block types to chunk types
        if block.block_type in [BlockTypeExtended.FUNCTION, BlockTypeExtended.CLASS, 
                               BlockTypeExtended.METHOD, BlockTypeExtended.CODE_BLOCK]:
            return ChunkType.CODE_BLOCK
        elif block.block_type == BlockTypeExtended.COMMENT:
            return ChunkType.COMMENT
        elif block.block_type == BlockTypeExtended.DOCSTRING:
            return ChunkType.MESSAGE
        else:
            # Use block's default chunk type or DOC_BLOCK
            return block.chunk_type
    
    def _determine_chunk_status(self, block: TextBlock, file_structure: FileStructure) -> ChunkStatus:
        """
        Determine appropriate ChunkStatus for new chunks.
        
        Args:
            block: Text block
            file_structure: File structure metadata
            
        Returns:
            Appropriate ChunkStatus (always NEW for new files)
        """
        # All new files start with NEW status
        return ChunkStatus.NEW
    
    def _post_process_chunks(self, chunks: List[VectorSemanticChunk],
                            file_structure: FileStructure) -> List[VectorSemanticChunk]:
        """
        Post-process chunks after creation.
        
        Args:
            chunks: List of chunks to post-process
            file_structure: File structure metadata
            
        Returns:
            Post-processed chunks
        """
        # Add ordinal numbers
        for i, chunk in enumerate(chunks):
            if chunk.ordinal is None:
                chunk.ordinal = i
        
        # Update chunk IDs to ensure uniqueness
        for chunk in chunks:
            if not hasattr(chunk, 'uuid') or not chunk.uuid:
                chunk.uuid = str(uuid.uuid4())
        
        return chunks 