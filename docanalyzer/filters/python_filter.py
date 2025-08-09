"""
Python File Filter.

Handles Python files by parsing AST and extracting functions, classes, and code blocks.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import time

from chunk_metadata_adapter.data_types import LanguageEnum

from .base import BaseFileFilter, FileStructure, TextBlock, BlockTypeExtended


class PythonFileFilter(BaseFileFilter):
    """
    Filter for Python source files.
    
    Parses Python files using AST to extract functions, classes, methods,
    docstrings, and other code structures as semantic blocks.
    """
    
    name = "python_filter"
    version = "1.0.0"
    supported_extensions = [".py", ".pyw", ".py3"]
    supported_mime_types = ["text/x-python", "application/x-python-code"]
    
    def setup(self) -> None:
        """Setup the Python filter."""
        self.include_imports = self.config.get("include_imports", True)
        self.include_docstrings = self.config.get("include_docstrings", True)
        self.include_comments = self.config.get("include_comments", True)
        self.min_function_lines = self.config.get("min_function_lines", 3)
        self.complexity_threshold = self.config.get("complexity_threshold", 10)
    
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
        
        # Check shebang for Python
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!') and 'python' in first_line:
                    return True
        except (IOError, UnicodeDecodeError):
            pass
        
        return False
    
    def parse(self, file_path: Path, content: Optional[str] = None) -> FileStructure:
        """
        Parse a Python file into structured blocks.
        
        Args:
            file_path: Path to the file
            content: Optional pre-loaded content
            
        Returns:
            FileStructure with extracted code blocks
        """
        start_time = time.time()
        
        # Load content if not provided
        if content is None:
            content = self._load_file_content(file_path)
        
        # Create base file structure
        file_structure = self._create_file_structure(file_path, content)
        file_structure.language = LanguageEnum.PYTHON
        
        # Extract blocks using AST
        try:
            blocks = self._extract_blocks_from_ast(content, file_path)
            file_structure.blocks = blocks
        except SyntaxError as e:
            # If AST parsing fails, fall back to text-based parsing
            self.logger.warning(f"AST parsing failed for {file_path}: {e}")
            blocks = self._extract_blocks_fallback(content, file_path)
            file_structure.blocks = blocks
        
        # Update processing metadata
        file_structure.processing_time = time.time() - start_time
        
        return file_structure
    
    def _extract_blocks_from_ast(self, content: str, file_path: Path) -> List[TextBlock]:
        """
        Extract blocks using AST parsing.
        
        Args:
            content: Python source code
            file_path: Path to the file
            
        Returns:
            List of extracted text blocks
        """
        blocks = []
        lines = content.split('\n')
        
        # Parse AST
        tree = ast.parse(content)
        
        # Extract module-level docstring
        if (ast.get_docstring(tree) and self.include_docstrings):
            docstring_node = tree.body[0]
            if isinstance(docstring_node, ast.Expr) and isinstance(docstring_node.value, ast.Str):
                docstring_block = self._create_docstring_block(
                    ast.get_docstring(tree),
                    docstring_node.lineno,
                    docstring_node.end_lineno or docstring_node.lineno,
                    "Module docstring"
                )
                blocks.append(docstring_block)
        
        # Process AST nodes
        for node in ast.walk(tree):
            node_blocks = self._process_ast_node(node, lines, content)
            blocks.extend(node_blocks)
        
        # Extract imports if enabled
        if self.include_imports:
            import_blocks = self._extract_imports(tree, lines)
            blocks.extend(import_blocks)
        
        # Extract comments if enabled
        if self.include_comments:
            comment_blocks = self._extract_comments(content)
            blocks.extend(comment_blocks)
        
        # Sort blocks by line number
        blocks.sort(key=lambda x: x.start_line)
        
        return blocks
    
    def _process_ast_node(self, node: ast.AST, lines: List[str], content: str) -> List[TextBlock]:
        """
        Process a single AST node.
        
        Args:
            node: AST node to process
            lines: File lines
            content: Full file content
            
        Returns:
            List of text blocks for this node
        """
        blocks = []
        
        if isinstance(node, ast.FunctionDef):
            blocks.extend(self._process_function(node, lines, content))
        elif isinstance(node, ast.AsyncFunctionDef):
            blocks.extend(self._process_function(node, lines, content, is_async=True))
        elif isinstance(node, ast.ClassDef):
            blocks.extend(self._process_class(node, lines, content))
        elif isinstance(node, ast.If) and self._is_main_guard(node):
            blocks.extend(self._process_main_guard(node, lines, content))
        
        return blocks
    
    def _process_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], 
                         lines: List[str], content: str, is_async: bool = False) -> List[TextBlock]:
        """
        Process a function definition.
        
        Args:
            node: Function AST node
            lines: File lines
            content: Full file content
            is_async: Whether function is async
            
        Returns:
            List of text blocks for this function
        """
        blocks = []
        
        # Calculate function complexity
        complexity = self._calculate_complexity(node)
        
        # Get function source
        start_line = node.lineno - 1  # Convert to 0-based
        end_line = (node.end_lineno - 1) if node.end_lineno else start_line
        
        if end_line - start_line < self.min_function_lines:
            return blocks  # Skip very small functions
        
        function_lines = lines[start_line:end_line + 1]
        function_content = '\n'.join(function_lines)
        
        # Create function block
        function_block = TextBlock(
            content=function_content,
            block_type=BlockTypeExtended.FUNCTION,
            language=LanguageEnum.PYTHON,
            start_line=start_line,
            end_line=end_line,
            start_offset=self._get_offset(content, start_line),
            end_offset=self._get_offset(content, end_line + 1),
            level=self._get_node_level(node),
            title=f"{'async ' if is_async else ''}def {node.name}",
            complexity_score=min(complexity / self.complexity_threshold, 1.0),
            importance_score=self._calculate_function_importance(node, complexity),
            metadata={
                "function_name": node.name,
                "is_async": is_async,
                "complexity": complexity,
                "args_count": len(node.args.args),
                "has_decorators": len(node.decorator_list) > 0,
                "returns": self._get_return_annotation(node)
            }
        )
        
        blocks.append(function_block)
        
        # Extract function docstring
        if self.include_docstrings and ast.get_docstring(node):
            docstring_block = self._create_docstring_block(
                ast.get_docstring(node),
                node.lineno + 1,  # Docstring is usually on the next line
                node.lineno + 1,  # Single line estimate
                f"Docstring for {node.name}"
            )
            blocks.append(docstring_block)
        
        return blocks
    
    def _process_class(self, node: ast.ClassDef, lines: List[str], content: str) -> List[TextBlock]:
        """
        Process a class definition.
        
        Args:
            node: Class AST node
            lines: File lines
            content: Full file content
            
        Returns:
            List of text blocks for this class
        """
        blocks = []
        
        # Get class source
        start_line = node.lineno - 1
        end_line = (node.end_lineno - 1) if node.end_lineno else start_line
        
        # Create class header block (just the class definition line)
        class_header = lines[start_line]
        
        class_block = TextBlock(
            content=class_header,
            block_type=BlockTypeExtended.CLASS,
            language=LanguageEnum.PYTHON,
            start_line=start_line,
            end_line=start_line,
            start_offset=self._get_offset(content, start_line),
            end_offset=self._get_offset(content, start_line + 1),
            level=self._get_node_level(node),
            title=f"class {node.name}",
            importance_score=0.8,  # Classes are generally important
            metadata={
                "class_name": node.name,
                "base_classes": [self._get_name(base) for base in node.bases],
                "has_decorators": len(node.decorator_list) > 0,
                "methods_count": sum(1 for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)))
            }
        )
        
        blocks.append(class_block)
        
        # Extract class docstring
        if self.include_docstrings and ast.get_docstring(node):
            docstring_block = self._create_docstring_block(
                ast.get_docstring(node),
                node.lineno + 1,
                node.lineno + 1,
                f"Docstring for class {node.name}"
            )
            blocks.append(docstring_block)
        
        return blocks
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity of a code block.
        
        Args:
            node: AST node
            
        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
        
        return complexity
    
    def _calculate_function_importance(self, node: ast.FunctionDef, complexity: int) -> float:
        """
        Calculate importance score for a function.
        
        Args:
            node: Function AST node
            complexity: Function complexity
            
        Returns:
            Importance score between 0 and 1
        """
        score = 0.5  # Base score
        
        # Main function is important
        if node.name == 'main':
            score += 0.3
        
        # Public functions (not starting with _) are more important
        if not node.name.startswith('_'):
            score += 0.1
        
        # Functions with decorators might be important (e.g., @property, @staticmethod)
        if node.decorator_list:
            score += 0.1
        
        # Complex functions might be important
        if complexity > 5:
            score += 0.1
        
        # Functions with type hints are likely well-documented
        if node.returns or any(arg.annotation for arg in node.args.args):
            score += 0.05
        
        return min(score, 1.0)
    
    def _create_docstring_block(self, docstring: str, start_line: int, 
                               end_line: int, title: str) -> TextBlock:
        """
        Create a text block for a docstring.
        
        Args:
            docstring: Docstring content
            start_line: Start line number
            end_line: End line number
            title: Block title
            
        Returns:
            TextBlock for the docstring
        """
        return TextBlock(
            content=docstring,
            block_type=BlockTypeExtended.DOCSTRING,
            language=LanguageEnum.PYTHON,
            start_line=start_line,
            end_line=end_line,
            start_offset=0,  # Approximate
            end_offset=len(docstring),
            level=1,
            title=title,
            importance_score=0.7,  # Docstrings are important for documentation
            metadata={"is_docstring": True}
        )
    
    def _extract_imports(self, tree: ast.AST, lines: List[str]) -> List[TextBlock]:
        """
        Extract import statements.
        
        Args:
            tree: AST tree
            lines: File lines
            
        Returns:
            List of import blocks
        """
        blocks = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_line = lines[node.lineno - 1]
                
                block = TextBlock(
                    content=import_line,
                    block_type=BlockTypeExtended.IMPORT,
                    language=LanguageEnum.PYTHON,
                    start_line=node.lineno - 1,
                    end_line=node.lineno - 1,
                    start_offset=0,
                    end_offset=len(import_line),
                    level=0,
                    importance_score=0.3,  # Imports are less important for content
                    metadata={"is_import": True}
                )
                
                blocks.append(block)
        
        return blocks
    
    def _extract_comments(self, content: str) -> List[TextBlock]:
        """
        Extract comment blocks.
        
        Args:
            content: File content
            
        Returns:
            List of comment blocks
        """
        blocks = []
        lines = content.split('\n')
        
        # Find comment blocks (consecutive comment lines)
        comment_block = []
        start_line = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith('#') and not stripped.startswith('#!'):
                if not comment_block:
                    start_line = i
                comment_block.append(stripped[1:].strip())  # Remove # and leading space
            else:
                if comment_block and len(comment_block) >= 2:  # Multi-line comments only
                    comment_content = '\n'.join(comment_block)
                    
                    block = TextBlock(
                        content=comment_content,
                        block_type=BlockTypeExtended.COMMENT,
                        language=LanguageEnum.PYTHON,
                        start_line=start_line,
                        end_line=i - 1,
                        start_offset=0,
                        end_offset=len(comment_content),
                        level=0,
                        importance_score=0.4,
                        metadata={"is_comment": True, "lines_count": len(comment_block)}
                    )
                    
                    blocks.append(block)
                
                comment_block = []
        
        return blocks
    
    def _extract_blocks_fallback(self, content: str, file_path: Path) -> List[TextBlock]:
        """
        Fallback text-based parsing when AST fails.
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            List of text blocks
        """
        blocks = []
        lines = content.split('\n')
        
        # Simple regex-based function detection
        function_pattern = re.compile(r'^(\s*)(async\s+)?def\s+(\w+)\s*\(', re.MULTILINE)
        class_pattern = re.compile(r'^(\s*)class\s+(\w+).*?:', re.MULTILINE)
        
        for match in function_pattern.finditer(content):
            indent = match.group(1)
            is_async = match.group(2) is not None
            func_name = match.group(3)
            
            # Find function end (very basic heuristic)
            start_line = content[:match.start()].count('\n')
            end_line = self._find_block_end(lines, start_line, len(indent))
            
            if end_line > start_line:
                function_content = '\n'.join(lines[start_line:end_line + 1])
                
                block = TextBlock(
                    content=function_content,
                    block_type=BlockTypeExtended.FUNCTION,
                    language=LanguageEnum.PYTHON,
                    start_line=start_line,
                    end_line=end_line,
                    start_offset=match.start(),
                    end_offset=match.start() + len(function_content),
                    level=len(indent) // 4,  # Estimate indentation level
                    title=f"{'async ' if is_async else ''}def {func_name}",
                    importance_score=0.6,
                    metadata={"function_name": func_name, "is_async": is_async, "fallback_parsing": True}
                )
                
                blocks.append(block)
        
        return blocks
    
    def _find_block_end(self, lines: List[str], start_line: int, base_indent: int) -> int:
        """
        Find the end of a code block based on indentation.
        
        Args:
            lines: File lines
            start_line: Start line of the block
            base_indent: Base indentation level
            
        Returns:
            End line number
        """
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check indentation
            current_indent = len(line) - len(line.lstrip())
            
            # If indentation is less than or equal to base, we've found the end
            if current_indent <= base_indent and line.strip():
                return i - 1
        
        return len(lines) - 1
    
    def _get_offset(self, content: str, line_num: int) -> int:
        """Get character offset for a line number."""
        lines = content.split('\n')
        return sum(len(line) + 1 for line in lines[:line_num])  # +1 for newline
    
    def _get_node_level(self, node: ast.AST) -> int:
        """Get nesting level of an AST node."""
        level = 0
        parent = getattr(node, 'parent', None)
        
        while parent:
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                level += 1
            parent = getattr(parent, 'parent', None)
        
        return level
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)
    
    def _get_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """Get return type annotation."""
        if node.returns:
            return ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        return None
    
    def _is_main_guard(self, node: ast.If) -> bool:
        """Check if this is a main guard (if __name__ == '__main__')."""
        if (isinstance(node.test, ast.Compare) and
            len(node.test.ops) == 1 and
            isinstance(node.test.ops[0], ast.Eq)):
            
            left = node.test.left
            right = node.test.comparators[0]
            
            if (isinstance(left, ast.Name) and left.id == '__name__' and
                isinstance(right, ast.Str) and right.s == '__main__'):
                return True
        
        return False
    
    def _process_main_guard(self, node: ast.If, lines: List[str], content: str) -> List[TextBlock]:
        """Process main guard block."""
        start_line = node.lineno - 1
        end_line = (node.end_lineno - 1) if node.end_lineno else start_line
        
        main_content = '\n'.join(lines[start_line:end_line + 1])
        
        block = TextBlock(
            content=main_content,
            block_type=BlockTypeExtended.CODE_BLOCK,
            language=LanguageEnum.PYTHON,
            start_line=start_line,
            end_line=end_line,
            start_offset=self._get_offset(content, start_line),
            end_offset=self._get_offset(content, end_line + 1),
            level=0,
            title="Main execution block",
            importance_score=0.7,
            metadata={"is_main_guard": True}
        )
        
        return [block] 