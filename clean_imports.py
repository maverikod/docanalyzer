#!/usr/bin/env python3
"""
Import Cleanup Script for DocAnalyzer

This script analyzes Python files in the DocAnalyzer project
and identifies potentially unused imports.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import os
import ast
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImportAnalyzer:
    """
    Import Analyzer - Analyze Python File Imports
    
    Analyzes Python files to identify imports and their usage,
    helping to find potentially unused imports.
    """
    
    def __init__(self):
        """Initialize import analyzer."""
        self.imports: Dict[str, Set[str]] = {}
        self.used_names: Set[str] = set()
        self.errors: List[str] = []
    
    def analyze_file(self, file_path: str) -> Dict[str, any]:
        """
        Analyze a single Python file.
        
        Args:
            file_path (str): Path to the Python file to analyze.
        
        Returns:
            Dict[str, any]: Analysis results including imports and usage.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Reset for this file
            self.imports = {}
            self.used_names = set()
            
            # Analyze the AST
            self._analyze_node(tree)
            
            return {
                'file_path': file_path,
                'imports': self.imports.copy(),
                'used_names': self.used_names.copy(),
                'unused_imports': self._find_unused_imports(),
                'error': None
            }
            
        except Exception as e:
            return {
                'file_path': file_path,
                'imports': {},
                'used_names': set(),
                'unused_imports': [],
                'error': str(e)
            }
    
    def _analyze_node(self, node: ast.AST) -> None:
        """
        Recursively analyze AST nodes.
        
        Args:
            node (ast.AST): AST node to analyze.
        """
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                as_name = alias.asname or alias.name.split('.')[-1]
                if module_name not in self.imports:
                    self.imports[module_name] = set()
                self.imports[module_name].add(as_name)
        
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ''
            for alias in node.names:
                name = alias.name
                as_name = alias.asname or name
                if module_name not in self.imports:
                    self.imports[module_name] = set()
                self.imports[module_name].add(as_name)
        
        elif isinstance(node, ast.Name):
            self.used_names.add(node.id)
        
        elif isinstance(node, ast.Attribute):
            # Handle attribute access (e.g., module.function)
            if isinstance(node.value, ast.Name):
                self.used_names.add(node.value.id)
        
        # Recursively analyze child nodes
        for child in ast.iter_child_nodes(node):
            self._analyze_node(child)
    
    def _find_unused_imports(self) -> List[str]:
        """
        Find unused imports.
        
        Returns:
            List[str]: List of unused import names.
        """
        unused = []
        for module, names in self.imports.items():
            for name in names:
                if name not in self.used_names:
                    unused.append(f"{module}.{name}" if module else name)
        return unused


class ImportCleaner:
    """
    Import Cleaner - Clean Up Unused Imports
    
    Provides functionality to clean up unused imports in Python files.
    """
    
    def __init__(self):
        """Initialize import cleaner."""
        self.analyzer = ImportAnalyzer()
    
    def analyze_project(self, project_path: str) -> List[Dict[str, any]]:
        """
        Analyze all Python files in the project.
        
        Args:
            project_path (str): Path to the project root.
        
        Returns:
            List[Dict[str, any]]: Analysis results for all files.
        """
        results = []
        project_path = Path(project_path)
        
        # Find all Python files, excluding .venv and other virtual environments
        python_files = []
        for file_path in project_path.rglob("*.py"):
            # Skip virtual environment directories
            if ".venv" in str(file_path) or "venv" in str(file_path) or "env" in str(file_path):
                continue
            # Skip __pycache__ directories
            if "__pycache__" in str(file_path):
                continue
            python_files.append(file_path)
        
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        for file_path in python_files:
            logger.info(f"Analyzing: {file_path}")
            result = self.analyzer.analyze_file(str(file_path))
            results.append(result)
        
        return results
    
    def generate_report(self, results: List[Dict[str, any]]) -> str:
        """
        Generate analysis report.
        
        Args:
            results (List[Dict[str, any]]): Analysis results.
        
        Returns:
            str: Formatted report.
        """
        report = []
        report.append("=" * 80)
        report.append("IMPORT ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        total_files = len(results)
        files_with_errors = sum(1 for r in results if r['error'])
        files_with_unused = sum(1 for r in results if r['unused_imports'])
        
        report.append(f"Total files analyzed: {total_files}")
        report.append(f"Files with errors: {files_with_errors}")
        report.append(f"Files with unused imports: {files_with_unused}")
        report.append("")
        
        # Files with errors
        if files_with_errors > 0:
            report.append("FILES WITH ERRORS:")
            report.append("-" * 40)
            for result in results:
                if result['error']:
                    report.append(f"  {result['file_path']}: {result['error']}")
            report.append("")
        
        # Files with unused imports
        if files_with_unused > 0:
            report.append("FILES WITH UNUSED IMPORTS:")
            report.append("-" * 40)
            for result in results:
                if result['unused_imports']:
                    report.append(f"  {result['file_path']}:")
                    for unused in result['unused_imports']:
                        report.append(f"    - {unused}")
                    report.append("")
        
        # Summary statistics
        total_unused = sum(len(r['unused_imports']) for r in results)
        report.append("SUMMARY:")
        report.append("-" * 40)
        report.append(f"Total unused imports found: {total_unused}")
        report.append("")
        
        return "\n".join(report)


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python clean_imports.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    if not os.path.exists(project_path):
        print(f"Project path does not exist: {project_path}")
        sys.exit(1)
    
    # Create cleaner and analyze project
    cleaner = ImportCleaner()
    results = cleaner.analyze_project(project_path)
    
    # Generate and print report
    report = cleaner.generate_report(results)
    print(report)
    
    # Save report to file
    report_file = Path(project_path) / "import_analysis_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    main() 