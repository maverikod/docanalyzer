"""
Tests for Configuration Validation

Comprehensive test suite for DocAnalyzer configuration validation functionality.
Tests all validation functions, error handling, and edge cases.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import re
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from docanalyzer.config.validation import (
    ConfigValidationError,
    validate_docanalyzer_config,
    validate_file_watcher_settings,
    validate_vector_store_settings,
    validate_chunker_settings,
    validate_embedding_settings,
    validate_cross_service_dependencies,
    validate_service_connectivity,
    get_configuration_summary
)
from docanalyzer.config.extensions import (
    get_file_watcher_settings,
    get_vector_store_settings,
    get_chunker_settings,
    get_embedding_settings
)


class TestConfigValidationError:
    """Test suite for ConfigValidationError exception."""
    
    def test_config_validation_error_initialization(self):
        """Test ConfigValidationError initialization."""
        # Arrange & Act
        error = ConfigValidationError("Test error message")
        
        # Assert
        assert str(error) == "Test error message"
        assert error.errors == []  # Changed from None to [] to match implementation
    
    def test_config_validation_error_with_errors_list(self):
        """Test ConfigValidationError with errors list."""
        # Arrange
        errors = ["Error 1", "Error 2"]
        
        # Act
        error = ConfigValidationError("Test error message", errors)
        
        # Assert
        assert str(error) == "Test error message"
        assert error.errors == errors


class TestValidateDocAnalyzerConfig:
    """Test suite for validate_docanalyzer_config function."""
    
    @patch('docanalyzer.config.validation.validate_file_watcher_settings')
    @patch('docanalyzer.config.validation.validate_vector_store_settings')
    @patch('docanalyzer.config.validation.validate_chunker_settings')
    @patch('docanalyzer.config.validation.validate_embedding_settings')
    @patch('docanalyzer.config.validation.validate_cross_service_dependencies')
    def test_validate_docanalyzer_config_success(self, mock_cross, mock_embedding, mock_chunker, mock_vector, mock_file_watcher):
        """Test successful DocAnalyzer configuration validation."""
        # Arrange
        mock_file_watcher.return_value = []
        mock_vector.return_value = []
        mock_chunker.return_value = []
        mock_embedding.return_value = []
        mock_cross.return_value = []
        
        # Act
        is_valid, errors = validate_docanalyzer_config()
        
        # Assert
        assert is_valid is True
        assert errors == []
        mock_file_watcher.assert_called_once()
        mock_vector.assert_called_once()
        mock_chunker.assert_called_once()
        mock_embedding.assert_called_once()
        mock_cross.assert_called_once()
    
    @patch('docanalyzer.config.validation.validate_file_watcher_settings')
    @patch('docanalyzer.config.validation.validate_vector_store_settings')
    @patch('docanalyzer.config.validation.validate_chunker_settings')
    @patch('docanalyzer.config.validation.validate_embedding_settings')
    @patch('docanalyzer.config.validation.validate_cross_service_dependencies')
    def test_validate_docanalyzer_config_with_errors(self, mock_cross, mock_embedding, mock_chunker, mock_vector, mock_file_watcher):
        """Test DocAnalyzer configuration validation with errors."""
        # Arrange
        mock_file_watcher.return_value = ["File watcher error"]
        mock_vector.return_value = ["Vector store error"]
        mock_chunker.return_value = []
        mock_embedding.return_value = []
        mock_cross.return_value = []
        
        # Act
        is_valid, errors = validate_docanalyzer_config()
        
        # Assert
        assert is_valid is False
        assert "File watcher error" in errors
        assert "Vector store error" in errors
        assert len(errors) == 2
    
    @patch('docanalyzer.config.validation.validate_docanalyzer_config')
    def test_validate_docanalyzer_config_exception(self, mock_validate):
        """Test validate_docanalyzer_config with exception."""
        # Arrange
        # Mock the actual function to raise exception
        with patch('docanalyzer.config.validation.validate_file_watcher_settings') as mock_file_watcher, \
             patch('docanalyzer.config.validation.validate_vector_store_settings') as mock_vector_store, \
             patch('docanalyzer.config.validation.validate_chunker_settings') as mock_chunker, \
             patch('docanalyzer.config.validation.validate_embedding_settings') as mock_embedding, \
             patch('docanalyzer.config.validation.validate_cross_service_dependencies') as mock_cross, \
             patch('docanalyzer.config.validation.validate_service_connectivity') as mock_connectivity:
            
            mock_file_watcher.side_effect = Exception("Test exception")
            
            # Act & Assert
            with pytest.raises(ConfigValidationError) as exc_info:
                validate_docanalyzer_config()
            
            # Assert
            assert "Validation process failed: Test exception" in str(exc_info.value)


class TestValidateFileWatcherSettings:
    """Test suite for validate_file_watcher_settings function."""
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_success(self, mock_get_settings):
        """Test successful file watcher settings validation."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': ['/path1', '/path2'],
            'scan_interval': 300,
            'lock_timeout': 3600,
            'max_processes': 5
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert errors == []
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_missing_directories(self, mock_get_settings):
        """Test file watcher settings validation with missing directories."""
        # Arrange
        mock_get_settings.return_value = {
            'scan_interval': 300
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.directories is required" in errors
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_empty_directories(self, mock_get_settings):
        """Test file watcher settings validation with empty directories."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': []
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.directories cannot be empty" in errors
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_invalid_scan_interval(self, mock_get_settings):
        """Test file watcher settings validation with invalid scan interval."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': ['/path1'],
            'scan_interval': -1
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.scan_interval must be positive" in errors
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_invalid_directories_type(self, mock_get_settings):
        """Test file watcher settings validation with invalid directories type."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': "not_a_list"
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.directories must be a list" in errors
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_invalid_directory_item(self, mock_get_settings):
        """Test file watcher settings validation with invalid directory item."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': [123, '/path2']
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.directories[0] must be a string" in errors
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_empty_directory_item(self, mock_get_settings):
        """Test file watcher settings validation with empty directory item."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': ['', '/path2']
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.directories[0] cannot be empty" in errors
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_invalid_scan_interval_type(self, mock_get_settings):
        """Test file watcher settings validation with invalid scan interval type."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': ['/path1'],
            'scan_interval': "not_an_integer"
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.scan_interval must be an integer" in errors
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_invalid_lock_timeout(self, mock_get_settings):
        """Test file watcher settings validation with invalid lock timeout."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': ['/path1'],
            'lock_timeout': 0
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.lock_timeout must be positive" in errors
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_invalid_max_processes(self, mock_get_settings):
        """Test file watcher settings validation with invalid max processes."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': ['/path1'],
            'max_processes': -1
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.max_processes must be positive" in errors
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_exception(self, mock_get_settings):
        """Test file watcher settings validation with exception."""
        # Arrange
        mock_get_settings.side_effect = Exception("Test exception")
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert len(errors) == 1
        assert "Failed to validate file_watcher settings: Test exception" in errors[0]
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_validate_file_watcher_settings_with_empty_string_directory(self, mock_get_settings):
        """Test file watcher settings validation with empty string directory."""
        # Arrange
        mock_get_settings.return_value = {
            'directories': ['/path1', '', '/path3']
        }
        
        # Act
        errors = validate_file_watcher_settings()
        
        # Assert
        assert "file_watcher.directories[1] cannot be empty" in errors


class TestValidateVectorStoreSettings:
    """Test suite for validate_vector_store_settings function."""
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_success(self, mock_get_settings):
        """Test successful vector store settings validation."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': 'http://localhost',
            'port': 8007,
            'timeout': 30
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert errors == []
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_invalid_url(self, mock_get_settings):
        """Test vector store settings validation with invalid URL."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': 'invalid-url'
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.base_url must be valid URL format" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_invalid_port(self, mock_get_settings):
        """Test vector store settings validation with invalid port."""
        # Arrange
        mock_get_settings.return_value = {
            'port': 70000
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.port must be between 1 and 65535" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_invalid_timeout(self, mock_get_settings):
        """Test vector store settings validation with invalid timeout."""
        # Arrange
        mock_get_settings.return_value = {
            'timeout': 0
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.timeout must be positive" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_invalid_timeout_type(self, mock_get_settings):
        """Test vector store settings validation with invalid timeout type."""
        # Arrange
        mock_get_settings.return_value = {
            'timeout': "not_an_integer"
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.timeout must be an integer" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_exception(self, mock_get_settings):
        """Test vector store settings validation with exception."""
        # Arrange
        mock_get_settings.side_effect = Exception("Test exception")
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert len(errors) == 1
        assert "Failed to validate vector_store settings: Test exception" in errors[0]
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_empty_url(self, mock_get_settings):
        """Test vector store settings validation with empty URL."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': ''
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.base_url cannot be empty" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_invalid_url_type(self, mock_get_settings):
        """Test vector store settings validation with invalid URL type."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': 123
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.base_url must be a string" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_invalid_port_type(self, mock_get_settings):
        """Test vector store settings validation with invalid port type."""
        # Arrange
        mock_get_settings.return_value = {
            'port': "not_an_integer"
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.port must be an integer" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_port_too_low(self, mock_get_settings):
        """Test vector store settings validation with port too low."""
        # Arrange
        mock_get_settings.return_value = {
            'port': 0
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.port must be between 1 and 65535" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_port_too_high(self, mock_get_settings):
        """Test vector store settings validation with port too high."""
        # Arrange
        mock_get_settings.return_value = {
            'port': 70000
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.port must be between 1 and 65535" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_negative_timeout(self, mock_get_settings):
        """Test vector store settings validation with negative timeout."""
        # Arrange
        mock_get_settings.return_value = {
            'timeout': -1
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.timeout must be positive" in errors
    
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    def test_validate_vector_store_settings_with_empty_base_url(self, mock_get_settings):
        """Test vector store settings validation with empty base_url."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': ''
        }
        
        # Act
        errors = validate_vector_store_settings()
        
        # Assert
        assert "vector_store.base_url cannot be empty" in errors


class TestValidateChunkerSettings:
    """Test suite for validate_chunker_settings function."""
    
    @patch('docanalyzer.config.validation.get_chunker_settings')
    def test_validate_chunker_settings_success(self, mock_get_settings):
        """Test successful chunker settings validation."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': 'http://localhost',
            'port': 8009,
            'timeout': 30
        }
        
        # Act
        errors = validate_chunker_settings()
        
        # Assert
        assert errors == []
    
    @patch('docanalyzer.config.validation.get_chunker_settings')
    def test_validate_chunker_settings_invalid_url(self, mock_get_settings):
        """Test chunker settings validation with invalid URL."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': 'invalid-url'
        }
        
        # Act
        errors = validate_chunker_settings()
        
        # Assert
        assert "chunker.base_url must be valid URL format" in errors
    
    @patch('docanalyzer.config.validation.get_chunker_settings')
    def test_validate_chunker_settings_invalid_port(self, mock_get_settings):
        """Test chunker settings validation with invalid port."""
        # Arrange
        mock_get_settings.return_value = {
            'port': 70000
        }
        
        # Act
        errors = validate_chunker_settings()
        
        # Assert
        assert "chunker.port must be between 1 and 65535" in errors
    
    @patch('docanalyzer.config.validation.get_chunker_settings')
    def test_validate_chunker_settings_invalid_timeout(self, mock_get_settings):
        """Test chunker settings validation with invalid timeout."""
        # Arrange
        mock_get_settings.return_value = {
            'timeout': 0
        }
        
        # Act
        errors = validate_chunker_settings()
        
        # Assert
        assert "chunker.timeout must be positive" in errors
    
    @patch('docanalyzer.config.validation.get_chunker_settings')
    def test_validate_chunker_settings_exception(self, mock_get_settings):
        """Test chunker settings validation with exception."""
        # Arrange
        mock_get_settings.side_effect = Exception("Test exception")
        
        # Act
        errors = validate_chunker_settings()
        
        # Assert
        assert len(errors) == 1
        assert "Failed to validate chunker settings: Test exception" in errors[0]
    
    @patch('docanalyzer.config.validation.get_chunker_settings')
    def test_validate_chunker_settings_with_empty_base_url(self, mock_get_settings):
        """Test chunker settings validation with empty base_url."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': ''
        }
        
        # Act
        errors = validate_chunker_settings()
        
        # Assert
        assert "chunker.base_url cannot be empty" in errors


class TestValidateEmbeddingSettings:
    """Test suite for validate_embedding_settings function."""
    
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_embedding_settings_success(self, mock_get_settings):
        """Test successful embedding settings validation."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': 'http://localhost',
            'port': 8001,
            'timeout': 30
        }
        
        # Act
        errors = validate_embedding_settings()
        
        # Assert
        assert errors == []
    
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_embedding_settings_invalid_url(self, mock_get_settings):
        """Test embedding settings validation with invalid URL."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': 'invalid-url'
        }
        
        # Act
        errors = validate_embedding_settings()
        
        # Assert
        assert "embedding.base_url must be valid URL format" in errors
    
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_embedding_settings_invalid_port(self, mock_get_settings):
        """Test embedding settings validation with invalid port."""
        # Arrange
        mock_get_settings.return_value = {
            'port': 70000
        }
        
        # Act
        errors = validate_embedding_settings()
        
        # Assert
        assert "embedding.port must be between 1 and 65535" in errors
    
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_embedding_settings_invalid_timeout(self, mock_get_settings):
        """Test embedding settings validation with invalid timeout."""
        # Arrange
        mock_get_settings.return_value = {
            'timeout': 0
        }
        
        # Act
        errors = validate_embedding_settings()
        
        # Assert
        assert "embedding.timeout must be positive" in errors
    
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_embedding_settings_exception(self, mock_get_settings):
        """Test embedding settings validation with exception."""
        # Arrange
        mock_get_settings.side_effect = Exception("Test exception")
        
        # Act
        errors = validate_embedding_settings()
        
        # Assert
        assert len(errors) == 1
        assert "Failed to validate embedding settings: Test exception" in errors[0]
    
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_embedding_settings_with_empty_base_url(self, mock_get_settings):
        """Test embedding settings validation with empty base_url."""
        # Arrange
        mock_get_settings.return_value = {
            'base_url': ''
        }
        
        # Act
        errors = validate_embedding_settings()
        
        # Assert
        assert "embedding.base_url cannot be empty" in errors


class TestValidateCrossServiceDependencies:
    """Test suite for validate_cross_service_dependencies function."""
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    @patch('docanalyzer.config.validation.get_chunker_settings')
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_cross_service_dependencies_success(self, mock_embedding, mock_chunker, mock_vector, mock_file_watcher):
        """Test successful cross-service dependencies validation."""
        # Arrange
        mock_file_watcher.return_value = {'directories': ['/path1']}
        mock_vector.return_value = {'port': 8007}
        mock_chunker.return_value = {'port': 8009}
        mock_embedding.return_value = {'port': 8001}
        
        # Act
        errors = validate_cross_service_dependencies()
        
        # Assert
        assert errors == []
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    @patch('docanalyzer.config.validation.get_chunker_settings')
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_cross_service_dependencies_duplicate_ports(self, mock_embedding, mock_chunker, mock_vector, mock_file_watcher):
        """Test cross-service dependencies validation with duplicate ports."""
        # Arrange
        mock_file_watcher.return_value = {'directories': ['/path1']}
        mock_vector.return_value = {'port': 8007}
        mock_chunker.return_value = {'port': 8007}  # Duplicate port
        mock_embedding.return_value = {'port': 8001}
        
        # Act
        errors = validate_cross_service_dependencies()
        
        # Assert
        assert any("Duplicate port" in error for error in errors)
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    @patch('docanalyzer.config.validation.get_chunker_settings')
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_cross_service_dependencies_reserved_port(self, mock_embedding, mock_chunker, mock_vector, mock_file_watcher):
        """Test cross-service dependencies validation with reserved port."""
        # Arrange
        mock_file_watcher.return_value = {'directories': ['/path1']}
        mock_vector.return_value = {'port': 80}  # Reserved port
        mock_chunker.return_value = {'port': 8009}
        mock_embedding.return_value = {'port': 8001}
        
        # Act
        errors = validate_cross_service_dependencies()
        
        # Assert
        # Check if any error contains information about reserved ports
        assert any("port 80" in error.lower() or "reserved" in error.lower() for error in errors)
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    @patch('docanalyzer.config.validation.get_chunker_settings')
    @patch('docanalyzer.config.validation.get_embedding_settings')
    def test_validate_cross_service_dependencies_exception(self, mock_embedding, mock_chunker, mock_vector, mock_file_watcher):
        """Test cross-service dependencies validation with exception."""
        # Arrange
        mock_file_watcher.side_effect = Exception("Test exception")
        
        # Act
        errors = validate_cross_service_dependencies()
        
        # Assert
        assert len(errors) == 1
        assert "Failed to validate cross-service dependencies: Test exception" in errors[0]


class TestValidateServiceConnectivity:
    """Test suite for validate_service_connectivity function."""
    
    def test_validate_service_connectivity_success(self):
        """Test successful service connectivity validation."""
        # Act
        connectivity = validate_service_connectivity()
        
        # Assert
        assert isinstance(connectivity, dict)
        assert 'vector_store' in connectivity
        assert 'chunker' in connectivity
        assert 'embedding' in connectivity
        assert all(isinstance(accessible, bool) for accessible in connectivity.values())
    
    @patch('docanalyzer.config.validation.logger')
    def test_validate_service_connectivity_exception(self, mock_logger):
        """Test service connectivity validation with exception."""
        # Arrange
        # Mock the logger.debug to raise exception in the main try block
        mock_logger.debug.side_effect = Exception("Test exception")
        
        # Act
        connectivity = validate_service_connectivity()
        
        # Assert
        assert isinstance(connectivity, dict)
        # When exception occurs, all services should be marked as inaccessible
        assert all(not accessible for accessible in connectivity.values())


class TestGetConfigurationSummary:
    """Test suite for get_configuration_summary function."""
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    @patch('docanalyzer.config.validation.get_chunker_settings')
    @patch('docanalyzer.config.validation.get_embedding_settings')
    @patch('docanalyzer.config.validation.validate_docanalyzer_config')
    @patch('docanalyzer.config.validation.validate_service_connectivity')
    def test_get_configuration_summary_success(self, mock_connectivity, mock_validate, mock_embedding, mock_chunker, mock_vector, mock_file_watcher):
        """Test successful configuration summary generation."""
        # Arrange
        mock_file_watcher.return_value = {'directories': ['/path1']}
        mock_vector.return_value = {'port': 8007}
        mock_chunker.return_value = {'port': 8009}
        mock_embedding.return_value = {'port': 8001}
        mock_validate.return_value = (True, [])
        mock_connectivity.return_value = {'vector_store': True, 'chunker': True, 'embedding': True}
        
        # Act
        summary = get_configuration_summary()
        
        # Assert
        assert isinstance(summary, dict)
        assert 'file_watcher' in summary
        assert 'vector_store' in summary
        assert 'chunker' in summary
        assert 'embedding' in summary
        assert 'validation' in summary
        assert 'connectivity' in summary
        assert summary['validation']['is_valid'] is True
        assert summary['validation']['errors'] == []
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    def test_get_configuration_summary_exception(self, mock_get_settings):
        """Test configuration summary generation with exception."""
        # Arrange
        mock_get_settings.side_effect = Exception("Test error")
        
        # Act
        summary = get_configuration_summary()
        
        # Assert
        assert isinstance(summary, dict)
        assert 'error' in summary
        assert 'Test error' in summary['error']
        assert summary['validation']['is_valid'] is False
        assert len(summary['validation']['errors']) == 1 
    
    @patch('docanalyzer.config.validation.get_file_watcher_settings')
    @patch('docanalyzer.config.validation.get_vector_store_settings')
    @patch('docanalyzer.config.validation.get_chunker_settings')
    @patch('docanalyzer.config.validation.get_embedding_settings')
    @patch('docanalyzer.config.validation.validate_docanalyzer_config')
    @patch('docanalyzer.config.validation.validate_service_connectivity')
    @patch('docanalyzer.config.validation.logger')
    def test_get_configuration_summary_exception(self, mock_logger, mock_connectivity, mock_validate, mock_embedding, mock_chunker, mock_vector, mock_file_watcher):
        """Test configuration summary generation with exception."""
        # Arrange
        mock_file_watcher.side_effect = Exception("Test exception")
        
        # Act
        summary = get_configuration_summary()
        
        # Assert
        assert isinstance(summary, dict)
        assert 'error' in summary
        assert 'Test exception' in summary['error']
        assert summary['validation']['is_valid'] is False
        assert len(summary['validation']['errors']) == 1 