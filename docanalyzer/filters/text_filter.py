"""
Text File Filter.

Handles plain text files by splitting them into paragraph blocks.
"""

import re
from pathlib import Path
from typing import List, Optional
import time

from chunk_metadata_adapter.data_types import LanguageEnum

from .base import BaseFileFilter, FileStructure, TextBlock, BlockTypeExtended


class TextFileFilter(BaseFileFilter):
    """
    Filter for plain text files.
    
    Splits text files into logical blocks (paragraphs, sections, etc.)
    based on whitespace and formatting patterns.
    """
    
    name = "text_filter"
    version = "1.0.0"
    supported_extensions = [".txt", ".text", ".log", ".readme"]
    supported_mime_types = ["text/plain", "text/x-log"]
    
    def setup(self) -> None:
        """Setup the text filter."""
        # Configuration options
        self.min_paragraph_length = self.config.get("min_paragraph_length", 20)
        self.max_paragraph_length = self.config.get("max_paragraph_length", 2000)
        self.preserve_line_breaks = self.config.get("preserve_line_breaks", False)
        
        # Compile regex patterns
        self.paragraph_separator = re.compile(r'\n\s*\n+', re.MULTILINE)
        self.section_pattern = re.compile(
            r'^(.*?)(?:\n|^)[-=]{3,}.*?$|^#+\s+(.+)$|^(\d+\.|\*|\-)\s+(.+)$',
            re.MULTILINE
        )
        self.heading_pattern = re.compile(r'^([A-Z][A-Z\s]+)$', re.MULTILINE)
    
    def can_process(self, file_path: Path) -> bool:
        """
        Check if this filter can process the given file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file can be processed
        """
        # Check extension
        if file_path.suffix.lower() in self.supported_extensions:
            return True
        
        # Check if it's a text file without extension
        if not file_path.suffix:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Read first 1KB to check if it's text
                    sample = f.read(1024)
                    # If we can read it as text, it's probably a text file
                    return True
            except (UnicodeDecodeError, IOError):
                return False
        
        return False
    
    def parse(self, file_path: Path, content: Optional[str] = None) -> FileStructure:
        """
        Parse a text file into structured blocks.
        
        Args:
            file_path: Path to the file
            content: Optional pre-loaded content
            
        Returns:
            FileStructure with extracted text blocks
        """
        start_time = time.time()
        
        # Load content if not provided
        if content is None:
            content = self._load_file_content(file_path)
        
        # Create base file structure
        file_structure = self._create_file_structure(file_path, content)
        
        # Extract blocks
        blocks = self._extract_blocks(content, file_path)
        file_structure.blocks = blocks
        
        # Update processing metadata
        file_structure.processing_time = time.time() - start_time
        
        return file_structure
    
    def _extract_blocks(self, content: str, file_path: Path) -> List[TextBlock]:
        """
        Extract text blocks from content.
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            List of text blocks
        """
        blocks = []
        lines = content.split('\n')
        current_line = 0
        current_offset = 0
        
        # Try to detect headings and sections first
        sections = self._detect_sections(content)
        
        if sections:
            # Process content by sections
            for section in sections:
                section_blocks = self._process_section(
                    section, lines, current_line, current_offset
                )
                blocks.extend(section_blocks)
                current_line += section['line_count']
                current_offset += len(section['content'])
        else:
            # Process as simple paragraphs
            paragraphs = self._split_into_paragraphs(content)
            
            for paragraph in paragraphs:
                if self._should_include_paragraph(paragraph):
                    # Calculate line numbers
                    lines_before = content[:current_offset].count('\n')
                    lines_in_paragraph = paragraph.count('\n')
                    
                    block = TextBlock(
                        content=paragraph.strip(),
                        block_type=self._classify_paragraph(paragraph),
                        language=self._detect_language(file_path),
                        start_line=lines_before,
                        end_line=lines_before + lines_in_paragraph,
                        start_offset=current_offset,
                        end_offset=current_offset + len(paragraph),
                        level=0,
                        importance_score=self._calculate_importance(paragraph)
                    )
                    
                    blocks.append(block)
                
                current_offset += len(paragraph) + 2  # +2 for paragraph separator
        
        return blocks
    
    def _detect_sections(self, content: str) -> List[dict]:
        """
        Detect sections in the text based on patterns.
        
        Args:
            content: File content
            
        Returns:
            List of detected sections
        """
        sections = []
        
        # Look for underlined headings (=== or ---)
        underline_pattern = re.compile(
            r'^(.+?)\n([-=]{3,})\n',
            re.MULTILINE
        )
        
        for match in underline_pattern.finditer(content):
            title = match.group(1).strip()
            sections.append({
                'title': title,
                'start': match.start(),
                'type': 'heading',
                'level': 1 if match.group(2)[0] == '=' else 2
            })
        
        # Look for ALL CAPS headings
        for match in self.heading_pattern.finditer(content):
            title = match.group(1).strip()
            if len(title) > 5:  # Avoid false positives
                sections.append({
                    'title': title,
                    'start': match.start(),
                    'type': 'heading',
                    'level': 1
                })
        
        return sorted(sections, key=lambda x: x['start'])
    
    def _split_into_paragraphs(self, content: str) -> List[str]:
        """
        Split content into paragraphs.
        
        Args:
            content: File content
            
        Returns:
            List of paragraphs
        """
        # Split on double newlines or more
        paragraphs = self.paragraph_separator.split(content)
        
        # Clean up paragraphs
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Normalize whitespace if not preserving line breaks
                if not self.preserve_line_breaks:
                    paragraph = re.sub(r'\s+', ' ', paragraph)
                cleaned_paragraphs.append(paragraph)
        
        return cleaned_paragraphs
    
    def _should_include_paragraph(self, paragraph: str) -> bool:
        """
        Determine if a paragraph should be included.
        
        Args:
            paragraph: Paragraph text
            
        Returns:
            True if paragraph should be included
        """
        # Check minimum length
        if len(paragraph) < self.min_paragraph_length:
            return False
        
        # Check maximum length
        if len(paragraph) > self.max_paragraph_length:
            return True  # Large paragraphs might need splitting later
        
        # Skip if mostly whitespace or special characters
        clean_text = re.sub(r'[^\w\s]', '', paragraph)
        if len(clean_text) < self.min_paragraph_length * 0.5:
            return False
        
        return True
    
    def _classify_paragraph(self, paragraph: str) -> BlockTypeExtended:
        """
        Classify the type of paragraph.
        
        Args:
            paragraph: Paragraph text
            
        Returns:
            Block type classification
        """
        # Check for list items
        if re.match(r'^\s*[\*\-\+]\s+', paragraph) or re.match(r'^\s*\d+\.\s+', paragraph):
            return BlockTypeExtended.LIST_ITEM
        
        # Check for quoted text
        if paragraph.startswith('>') or paragraph.startswith('"'):
            return BlockTypeExtended.QUOTE
        
        # Check for all caps (possible heading)
        if paragraph.isupper() and len(paragraph) < 100:
            return BlockTypeExtended.HEADING
        
        # Check for title-like formatting
        words = paragraph.split()
        if (len(words) <= 10 and 
            paragraph.istitle() and 
            not paragraph.endswith('.') and
            len(paragraph) < 100):
            return BlockTypeExtended.TITLE
        
        # Default to paragraph
        return BlockTypeExtended.PARAGRAPH
    
    def _calculate_importance(self, paragraph: str) -> float:
        """
        Calculate importance score for a paragraph.
        
        Args:
            paragraph: Paragraph text
            
        Returns:
            Importance score between 0 and 1
        """
        score = 0.5  # Base score
        
        # Longer paragraphs might be more important
        length_factor = min(len(paragraph) / 500, 1.0)
        score += length_factor * 0.2
        
        # Paragraphs with questions might be important
        if '?' in paragraph:
            score += 0.1
        
        # Paragraphs with exclamations
        if '!' in paragraph:
            score += 0.05
        
        # Paragraphs with keywords
        important_keywords = ['important', 'note', 'warning', 'attention', 'todo', 'fixme']
        for keyword in important_keywords:
            if keyword.lower() in paragraph.lower():
                score += 0.15
                break
        
        return min(score, 1.0)
    
    def _process_section(self, section: dict, lines: List[str], 
                        current_line: int, current_offset: int) -> List[TextBlock]:
        """
        Process a detected section.
        
        Args:
            section: Section information
            lines: All file lines
            current_line: Current line number
            current_offset: Current character offset
            
        Returns:
            List of text blocks for this section
        """
        blocks = []
        
        # Create heading block
        heading_block = TextBlock(
            content=section['title'],
            block_type=BlockTypeExtended.HEADING,
            language=LanguageEnum.EN,
            start_line=current_line,
            end_line=current_line,
            start_offset=current_offset,
            end_offset=current_offset + len(section['title']),
            level=section.get('level', 1),
            title=section['title'],
            importance_score=0.8  # Headings are generally important
        )
        
        blocks.append(heading_block)
        
        return blocks 