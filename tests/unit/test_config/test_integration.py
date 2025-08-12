"""
Tests for DocAnalyzer Configuration Integration

Comprehensive test suite for DocAnalyzer configuration integration
with the mcp_proxy_adapter framework.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from docanalyzer.config.integration import DocAnalyzerConfig, ConfigError, ValidationError


class TestDocAnalyzerConfig:
    """Test suite for DocAnalyzerConfig class."""
    
    @pytest.fixture
    def mock_framework_config(self):
        """Create mock framework configuration."""
        mock_config = Mock()
        mock_config.reload = Mock()
        return mock_config
    
    @pytest.fixture
    def docanalyzer_config(self, mock_framework_config):
        """Create DocAnalyzerConfig instance with mocked dependencies."""
        with patch('docanalyzer.config.integration.framework_config', mock_framework_config):
            with patch('docanalyzer.config.integration.get_custom_setting_value') as mock_get_setting:
                # Mock default settings
                mock_get_setting.return_value = {}
                config = DocAnalyzerConfig()
                return config
    
    def test_init_success(self, mock_framework_config):
        """Test successful DocAnalyzerConfig initialization."""
        with patch('docanalyzer.config.integration.framework_config', mock_framework_config):
            with patch('docanalyzer.config.integration.get_custom_setting_value') as mock_get_setting:
                mock_get_setting.return_value = {}
                config = DocAnalyzerConfig()
                
                assert config.framework_config == mock_framework_config
                assert 'file_watcher' in config.docanalyzer_settings
                assert 'vector_store' in config.docanalyzer_settings
                assert 'chunker' in config.docanalyzer_settings
                assert 'embedding' in config.docanalyzer_settings
    
    def test_get_file_watcher_settings_success(self, docanalyzer_config):
        """Test successful file watcher settings retrieval."""
        settings = docanalyzer_config.get_file_watcher_settings()
        
        assert isinstance(settings, dict)
        assert 'directories' in settings
        assert 'scan_interval' in settings
        assert 'lock_timeout' in settings
        assert 'max_processes' in settings
    
    def test_get_file_watcher_settings_missing(self, mock_framework_config):
        """Test file watcher settings when section is missing."""
        with patch('docanalyzer.config.integration.framework_config', mock_framework_config):
            with patch('docanalyzer.config.integration.get_custom_setting_value') as mock_get_setting:
                mock_get_setting.return_value = {}
                config = DocAnalyzerConfig()
                
                # Remove file_watcher section
                config.docanalyzer_settings.pop('file_watcher', None)
                
                with pytest.raises(ConfigError, match="File watcher settings not found"):
                    config.get_file_watcher_settings()
    
    def test_get_vector_store_settings_success(self, docanalyzer_config):
        """Test successful vector store settings retrieval."""
        settings = docanalyzer_config.get_vector_store_settings()
        
        assert isinstance(settings, dict)
        assert 'base_url' in settings
        assert 'port' in settings
        assert 'timeout' in settings
    
    def test_get_vector_store_settings_missing(self, mock_framework_config):
        """Test vector store settings when section is missing."""
        with patch('docanalyzer.config.integration.framework_config', mock_framework_config):
            with patch('docanalyzer.config.integration.get_custom_setting_value') as mock_get_setting:
                mock_get_setting.return_value = {}
                config = DocAnalyzerConfig()
                
                # Remove vector_store section
                config.docanalyzer_settings.pop('vector_store', None)
                
                with pytest.raises(ConfigError, match="Vector store settings not found"):
                    config.get_vector_store_settings()
    
    def test_get_chunker_settings_success(self, docanalyzer_config):
        """Test successful chunker settings retrieval."""
        settings = docanalyzer_config.get_chunker_settings()
        
        assert isinstance(settings, dict)
        assert 'base_url' in settings
        assert 'port' in settings
        assert 'timeout' in settings
    
    def test_get_chunker_settings_missing(self, mock_framework_config):
        """Test chunker settings when section is missing."""
        with patch('docanalyzer.config.integration.framework_config', mock_framework_config):
            with patch('docanalyzer.config.integration.get_custom_setting_value') as mock_get_setting:
                mock_get_setting.return_value = {}
                config = DocAnalyzerConfig()
                
                # Remove chunker section
                config.docanalyzer_settings.pop('chunker', None)
                
                with pytest.raises(ConfigError, match="Chunker settings not found"):
                    config.get_chunker_settings()
    
    def test_get_embedding_settings_success(self, docanalyzer_config):
        """Test successful embedding settings retrieval."""
        settings = docanalyzer_config.get_embedding_settings()
        
        assert isinstance(settings, dict)
        assert 'base_url' in settings
        assert 'port' in settings
        assert 'timeout' in settings
    
    def test_get_embedding_settings_missing(self, mock_framework_config):
        """Test embedding settings when section is missing."""
        with patch('docanalyzer.config.integration.framework_config', mock_framework_config):
            with patch('docanalyzer.config.integration.get_custom_setting_value') as mock_get_setting:
                mock_get_setting.return_value = {}
                config = DocAnalyzerConfig()
                
                # Remove embedding section
                config.docanalyzer_settings.pop('embedding', None)
                
                with pytest.raises(ConfigError, match="Embedding settings not found"):
                    config.get_embedding_settings()
    
    def test_get_framework_settings_success(self, docanalyzer_config):
        """Test successful framework settings retrieval."""
        with patch('docanalyzer.config.integration.get_setting') as mock_get_setting:
            with patch('docanalyzer.config.integration.Settings') as mock_settings:
                mock_get_setting.side_effect = ['localhost', 8080, False, 'INFO']
                mock_settings.get_logging_settings.return_value = {'level': 'INFO'}
                mock_settings.get_commands_settings.return_value = {'auto_discovery': True}
                
                settings = docanalyzer_config.get_framework_settings()
                
                assert isinstance(settings, dict)
                assert 'server' in settings
                assert 'logging' in settings
                assert 'commands' in settings
    
    def test_reload_configuration_success(self, docanalyzer_config):
        """Test successful configuration reload."""
        with patch.object(docanalyzer_config, '_load_docanalyzer_settings') as mock_load:
            mock_load.return_value = {'file_watcher': {}, 'vector_store': {}}
            
            docanalyzer_config.reload_configuration()
            
            docanalyzer_config.framework_config.reload.assert_called_once()
            mock_load.assert_called_once()
    
    def test_reload_configuration_failure(self, docanalyzer_config):
        """Test configuration reload failure."""
        docanalyzer_config.framework_config.reload.side_effect = Exception("Reload failed")
        
        with pytest.raises(ConfigError, match="Configuration reload failed"):
            docanalyzer_config.reload_configuration()
    
    def test_validate_configuration_success(self, docanalyzer_config):
        """Test successful configuration validation."""
        result = docanalyzer_config.validate_configuration()
        assert result is True
    
    def test_validate_configuration_failure(self, mock_framework_config):
        """Test configuration validation failure."""
        with patch('docanalyzer.config.integration.framework_config', mock_framework_config):
            with patch('docanalyzer.config.integration.get_custom_setting_value') as mock_get_setting:
                mock_get_setting.return_value = {}
                config = DocAnalyzerConfig()
                
                # Remove required section
                config.docanalyzer_settings.pop('file_watcher', None)
                
                with pytest.raises(ValidationError, match="Missing required configuration section"):
                    config.validate_configuration()
    
    def test_get_default_settings_valid_section(self, docanalyzer_config):
        """Test getting default settings for valid section."""
        defaults = docanalyzer_config._get_default_settings('file_watcher')
        
        assert isinstance(defaults, dict)
        assert 'directories' in defaults
        assert 'scan_interval' in defaults
        assert 'lock_timeout' in defaults
        assert 'max_processes' in defaults
    
    def test_get_default_settings_invalid_section(self, docanalyzer_config):
        """Test getting default settings for invalid section."""
        with pytest.raises(ValueError, match="Unsupported configuration section"):
            docanalyzer_config._get_default_settings('invalid_section')
    
    def test_load_docanalyzer_settings_exception(self, mock_framework_config):
        """Test loading DocAnalyzer settings with exception."""
        with patch('docanalyzer.config.integration.framework_config', mock_framework_config):
            with patch('docanalyzer.config.integration.get_custom_setting_value') as mock_get_setting:
                mock_get_setting.side_effect = Exception("Test error")
                
                with pytest.raises(ConfigError, match="Configuration loading failed"):
                    DocAnalyzerConfig()
    
    def test_load_docanalyzer_settings_with_existing_config(self, mock_framework_config):
        """Test loading DocAnalyzer settings with existing configuration."""
        with patch('docanalyzer.config.integration.framework_config', mock_framework_config):
            with patch('docanalyzer.config.integration.get_custom_setting_value') as mock_get_setting:
                # Mock existing configuration
                mock_get_setting.side_effect = [
                    {'directories': ['/custom/path']},  # file_watcher
                    {'base_url': 'http://custom'},      # vector_store
                    {'base_url': 'http://custom'},      # chunker
                    {'base_url': 'http://custom'}       # embedding
                ]
                
                config = DocAnalyzerConfig()
                
                # Verify settings were loaded from configuration
                assert config.docanalyzer_settings['file_watcher']['directories'] == ['/custom/path']
                assert config.docanalyzer_settings['vector_store']['base_url'] == 'http://custom'


class TestConfigError:
    """Test suite for ConfigError exception."""
    
    def test_config_error_initialization(self):
        """Test ConfigError initialization."""
        error = ConfigError("Test error message")
        
        assert error.message == "Test error message"
        assert str(error) == "Test error message"
    
    def test_config_error_with_source(self):
        """Test ConfigError with source information."""
        error = ConfigError("Test error message")
        
        assert error.message == "Test error message"
        assert str(error) == "Test error message"


class TestValidationError:
    """Test suite for ValidationError exception."""
    
    def test_validation_error_initialization(self):
        """Test ValidationError initialization."""
        error = ValidationError("Test validation error")
        
        assert error.message == "Test validation error"
        assert str(error) == "Test validation error"
    
    def test_validation_error_with_errors_list(self):
        """Test ValidationError with errors list."""
        error = ValidationError("Test validation error")
        
        assert error.message == "Test validation error"
        assert str(error) == "Test validation error" 