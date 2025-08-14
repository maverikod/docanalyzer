"""
Tests for Package Initialization

Comprehensive test suite for the docanalyzer package initialization.
Tests imports, version information, and package structure.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
from unittest.mock import patch, Mock
import importlib
import sys

from docanalyzer import __version__, __version_tuple__, version, version_tuple
from docanalyzer import __author__, __description__


class TestPackageInit:
    """Test suite for package initialization."""
    
    def test_version_imports(self):
        """Test that version information can be imported."""
        assert isinstance(__version__, str)
        assert len(__version__) > 0
        assert isinstance(__version_tuple__, tuple)
        assert len(__version_tuple__) >= 2
        
        assert isinstance(version, str)
        assert isinstance(version_tuple, tuple)
        assert __version__ == version
        assert __version_tuple__ == version_tuple
    
    def test_metadata_imports(self):
        """Test that package metadata can be imported."""
        assert isinstance(__author__, str)
        assert len(__author__) > 0
        assert isinstance(__description__, str)
        assert len(__description__) > 0
    
    def test_version_format(self):
        """Test that version has correct format."""
        # Version should contain at least one dot
        assert '.' in __version__
        
        # Version tuple should have at least major and minor
        assert len(__version_tuple__) >= 2
        assert isinstance(__version_tuple__[0], int)  # Major version
        assert isinstance(__version_tuple__[1], int)  # Minor version
    
    def test_package_structure(self):
        """Test that package has correct structure."""
        import docanalyzer
        
        # Check that package has expected attributes
        assert hasattr(docanalyzer, '__version__')
        assert hasattr(docanalyzer, '__version_tuple__')
        assert hasattr(docanalyzer, 'version')
        assert hasattr(docanalyzer, 'version_tuple')
        assert hasattr(docanalyzer, '__author__')
        assert hasattr(docanalyzer, '__description__')
    
    def test_get_main_function(self):
        """Test the get_main function."""
        from docanalyzer import get_main
        
        # Test that get_main is callable
        assert callable(get_main)
        
        # Test that it returns a function when called
        with patch('docanalyzer.main.main') as mock_main:
            main_func = get_main()
            assert callable(main_func)
    
    def test_get_main_function_import_error(self):
        """Test get_main function when main module import fails."""
        from docanalyzer import get_main
        
        # Mock the import to fail
        with patch('builtins.__import__', side_effect=ImportError("No module named 'uvicorn'")):
            # The function should raise the import error when called
            with pytest.raises(ImportError, match="No module named 'uvicorn'"):
                get_main()
    
    def test_package_reload(self):
        """Test that package can be reloaded."""
        import docanalyzer
        original_version = docanalyzer.__version__
        
        # Reload the package
        importlib.reload(docanalyzer)
        
        # Version should remain the same
        assert docanalyzer.__version__ == original_version
    
    def test_version_consistency(self):
        """Test that version information is consistent."""
        # Version string should contain version tuple elements
        version_str = str(__version_tuple__[0])
        assert version_str in __version__
    
    def test_metadata_values(self):
        """Test that metadata has expected values."""
        assert __author__ == "Document Analyzer Team"
        assert "Document indexing service" in __description__
    
    def test_package_import_performance(self):
        """Test that package import is fast (no heavy operations)."""
        import time
        
        start_time = time.time()
        import docanalyzer
        import_time = time.time() - start_time
        
        # Import should be fast (less than 1 second)
        assert import_time < 1.0
    
    def test_no_circular_imports(self):
        """Test that there are no circular imports."""
        # Clear any existing imports
        if 'docanalyzer' in sys.modules:
            del sys.modules['docanalyzer']
        
        # Import should work without circular dependencies
        import docanalyzer
        
        # Check that all expected attributes are available
        assert hasattr(docanalyzer, '__version__')
        assert hasattr(docanalyzer, '__version_tuple__')
        assert hasattr(docanalyzer, 'version')
        assert hasattr(docanalyzer, 'version_tuple')
        assert hasattr(docanalyzer, '__author__')
        assert hasattr(docanalyzer, '__description__')
    
    def test_package_docstring(self):
        """Test that package has proper docstring."""
        import docanalyzer
        
        assert docanalyzer.__doc__ is not None
        assert len(docanalyzer.__doc__) > 0
        assert "Document Analyzer Service" in docanalyzer.__doc__
    
    def test_version_attributes_immutable(self):
        """Test that version attributes are not accidentally modified."""
        import docanalyzer
        
        original_version = docanalyzer.__version__
        original_tuple = docanalyzer.__version_tuple__
        
        # Try to modify (should not affect the original)
        docanalyzer.__version__ = "test"
        docanalyzer.__version_tuple__ = (999, 999)
        
        # Reload to get original values
        importlib.reload(docanalyzer)
        
        # Values should be back to original
        assert docanalyzer.__version__ == original_version
        assert docanalyzer.__version_tuple__ == original_tuple
    
    def test_package_all_attribute(self):
        """Test that __all__ attribute is properly defined."""
        import docanalyzer
        
        assert hasattr(docanalyzer, '__all__')
        assert isinstance(docanalyzer.__all__, list)
        
        # Check that all exported items are in __all__
        expected_exports = [
            "__version__", "__version_tuple__", "version", "version_tuple",
            "__author__", "__description__"
        ]
        
        for export in expected_exports:
            assert export in docanalyzer.__all__
    
    def test_version_compatibility(self):
        """Test that version is compatible with semantic versioning."""
        # Major and minor versions should be non-negative
        assert __version_tuple__[0] >= 0
        assert __version_tuple__[1] >= 0
        
        # Version string should contain major version
        assert str(__version_tuple__[0]) in __version__ 