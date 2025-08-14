"""
Tests for Unified Configuration

Comprehensive test suite for the unified configuration system that
combines DocAnalyzer-specific settings with mcp_proxy_adapter framework
configuration.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from docanalyzer.config.unified_config import (
    UnifiedConfig,
    ServerConfig,
    LoggingConfig,
    CommandsConfig,
    FileWatcherConfig,
    VectorStoreConfig,
    ChunkerConfig,
    EmbeddingConfig,
    ConfigError,
    ValidationError,
    get_unified_config,
    reload_unified_config
)


class TestServerConfig:
    """Test suite for ServerConfig class."""
    
    def test_server_config_defaults(self):
        """Test ServerConfig with default values."""
        config = ServerConfig()
        
        assert config.host == "0.0.0.0"
        assert config.port == 8015
        assert config.debug is False
        assert config.log_level == "INFO"
    
    def test_server_config_custom_values(self):
        """Test ServerConfig with custom values."""
        config = ServerConfig(
            host="127.0.0.1",
            port=8080,
            debug=True,
            log_level="DEBUG"
        )
        
        assert config.host == "127.0.0.1"
        assert config.port == 8080
        assert config.debug is True
        assert config.log_level == "DEBUG"


class TestLoggingConfig:
    """Test suite for LoggingConfig class."""
    
    def test_logging_config_defaults(self):
        """Test LoggingConfig with default values."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.log_dir == "./logs/docanalyzer"
        assert config.log_file == "docanalyzer.log"
        assert config.error_log_file == "docanalyzer_error.log"
        assert config.access_log_file == "docanalyzer_access.log"
        assert config.max_file_size == "10MB"
        assert config.backup_count == 5
        assert config.console_output is True
        assert config.file_output is True
    
    def test_logging_config_custom_values(self):
        """Test LoggingConfig with custom values."""
        config = LoggingConfig(
            level="DEBUG",
            log_dir="/custom/logs",
            log_file="custom.log",
            backup_count=10,
            console_output=False
        )
        
        assert config.level == "DEBUG"
        assert config.log_dir == "/custom/logs"
        assert config.log_file == "custom.log"
        assert config.backup_count == 10
        assert config.console_output is False


class TestCommandsConfig:
    """Test suite for CommandsConfig class."""
    
    def test_commands_config_defaults(self):
        """Test CommandsConfig with default values."""
        config = CommandsConfig()
        
        assert config.auto_discovery is True
        assert config.discovery_path == "docanalyzer.commands"
        assert config.custom_commands_path is None
    
    def test_commands_config_custom_values(self):
        """Test CommandsConfig with custom values."""
        config = CommandsConfig(
            auto_discovery=False,
            discovery_path="custom.commands",
            custom_commands_path="/custom/path"
        )
        
        assert config.auto_discovery is False
        assert config.discovery_path == "custom.commands"
        assert config.custom_commands_path == "/custom/path"


class TestFileWatcherConfig:
    """Test suite for FileWatcherConfig class."""
    
    def test_file_watcher_config_defaults(self):
        """Test FileWatcherConfig with default values."""
        config = FileWatcherConfig()
        
        assert config.directories == ["./documents", "./docs"]
        assert config.scan_interval == 300
        assert config.lock_timeout == 3600
        assert config.max_processes == 5
    
    def test_file_watcher_config_custom_values(self):
        """Test FileWatcherConfig with custom values."""
        custom_dirs = ["/custom/dir1", "/custom/dir2"]
        config = FileWatcherConfig(
            directories=custom_dirs,
            scan_interval=600,
            lock_timeout=7200,
            max_processes=10
        )
        
        assert config.directories == custom_dirs
        assert config.scan_interval == 600
        assert config.lock_timeout == 7200
        assert config.max_processes == 10


class TestVectorStoreConfig:
    """Test suite for VectorStoreConfig class."""
    
    def test_vector_store_config_defaults(self):
        """Test VectorStoreConfig with default values."""
        config = VectorStoreConfig()
        
        assert config.base_url == "http://localhost"
        assert config.port == 8007
        assert config.timeout == 30
    
    def test_vector_store_config_custom_values(self):
        """Test VectorStoreConfig with custom values."""
        config = VectorStoreConfig(
            base_url="https://custom.host",
            port=9000,
            timeout=60
        )
        
        assert config.base_url == "https://custom.host"
        assert config.port == 9000
        assert config.timeout == 60


class TestChunkerConfig:
    """Test suite for ChunkerConfig class."""
    
    def test_chunker_config_defaults(self):
        """Test ChunkerConfig with default values."""
        config = ChunkerConfig()
        
        assert config.base_url == "http://localhost"
        assert config.port == 8009
        assert config.timeout == 30
    
    def test_chunker_config_custom_values(self):
        """Test ChunkerConfig with custom values."""
        config = ChunkerConfig(
            base_url="https://chunker.host",
            port=9001,
            timeout=45
        )
        
        assert config.base_url == "https://chunker.host"
        assert config.port == 9001
        assert config.timeout == 45


class TestEmbeddingConfig:
    """Test suite for EmbeddingConfig class."""
    
    def test_embedding_config_defaults(self):
        """Test EmbeddingConfig with default values."""
        config = EmbeddingConfig()
        
        assert config.base_url == "http://localhost"
        assert config.port == 8001
        assert config.timeout == 30
    
    def test_embedding_config_custom_values(self):
        """Test EmbeddingConfig with custom values."""
        config = EmbeddingConfig(
            base_url="https://embedding.host",
            port=9002,
            timeout=90
        )
        
        assert config.base_url == "https://embedding.host"
        assert config.port == 9002
        assert config.timeout == 90


class TestUnifiedConfig:
    """Test suite for UnifiedConfig class."""
    
    @pytest.fixture
    def mock_framework_config(self):
        """Create mock framework configuration."""
        return Mock()
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock Settings class."""
        return Mock()
    
    @patch('docanalyzer.config.unified_config.framework_config')
    @patch('docanalyzer.config.unified_config.Settings')
    @patch('docanalyzer.config.unified_config.get_custom_setting_value')
    def test_unified_config_initialization(self, mock_get_custom_setting, mock_settings, mock_framework_config):
        """Test UnifiedConfig initialization."""
        # Mock Settings methods
        mock_settings.get_server_settings.return_value = {
            'host': '127.0.0.1',
            'port': 8080,
            'debug': True,
            'log_level': 'DEBUG'
        }
        mock_settings.get_logging_settings.return_value = {
            'level': 'DEBUG',
            'log_dir': '/custom/logs',
            'log_file': 'custom.log',
            'error_log_file': 'custom_error.log',
            'access_log_file': 'custom_access.log',
            'max_file_size': '20MB',
            'backup_count': 10,
            'format': '%(message)s',
            'date_format': '%Y-%m-%d',
            'console_output': False,
            'file_output': True
        }
        mock_settings.get_commands_settings.return_value = {
            'auto_discovery': False,
            'discovery_path': 'custom.commands',
            'custom_commands_path': '/custom/path'
        }
        
        # Mock custom setting values
        mock_get_custom_setting.side_effect = lambda key, default: {
            'file_watcher': {
                'directories': ['/custom/dir1', '/custom/dir2'],
                'scan_interval': 600,
                'lock_timeout': 7200,
                'max_processes': 10
            },
            'vector_store': {
                'base_url': 'https://vector.host',
                'port': 9000,
                'timeout': 60
            },
            'chunker': {
                'base_url': 'https://chunker.host',
                'port': 9001,
                'timeout': 45
            },
            'embedding': {
                'base_url': 'https://embedding.host',
                'port': 9002,
                'timeout': 90
            }
        }.get(key, default)
        
        config = UnifiedConfig()
        
        # Verify server configuration
        assert config.server.host == '127.0.0.1'
        assert config.server.port == 8080
        assert config.server.debug is True
        assert config.server.log_level == 'DEBUG'
        
        # Verify logging configuration
        assert config.logging.level == 'DEBUG'
        assert config.logging.log_dir == '/custom/logs'
        assert config.logging.log_file == 'custom.log'
        assert config.logging.backup_count == 10
        assert config.logging.console_output is False
        
        # Verify commands configuration
        assert config.commands.auto_discovery is False
        assert config.commands.discovery_path == 'custom.commands'
        assert config.commands.custom_commands_path == '/custom/path'
        
        # Verify file watcher configuration
        assert config.file_watcher.directories == ['/custom/dir1', '/custom/dir2']
        assert config.file_watcher.scan_interval == 600
        assert config.file_watcher.lock_timeout == 7200
        assert config.file_watcher.max_processes == 10
        
        # Verify service configurations
        assert config.vector_store.base_url == 'https://vector.host'
        assert config.vector_store.port == 9000
        assert config.vector_store.timeout == 60
        
        assert config.chunker.base_url == 'https://chunker.host'
        assert config.chunker.port == 9001
        assert config.chunker.timeout == 45
        
        assert config.embedding.base_url == 'https://embedding.host'
        assert config.embedding.port == 9002
        assert config.embedding.timeout == 90
    
    @patch('docanalyzer.config.unified_config.framework_config')
    @patch('docanalyzer.config.unified_config.Settings')
    @patch('docanalyzer.config.unified_config.get_custom_setting_value')
    def test_unified_config_defaults(self, mock_get_custom_setting, mock_settings, mock_framework_config):
        """Test UnifiedConfig with default values."""
        # Mock Settings methods with empty/default values
        mock_settings.get_server_settings.return_value = {}
        mock_settings.get_logging_settings.return_value = {}
        mock_settings.get_commands_settings.return_value = {}
        
        # Mock custom setting values with empty dictionaries
        mock_get_custom_setting.return_value = {}
        
        config = UnifiedConfig()
        
        # Verify default values are used
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8015
        assert config.server.debug is False
        assert config.server.log_level == "INFO"
        
        assert config.logging.level == "INFO"
        assert config.logging.log_dir == "./logs/docanalyzer"
        assert config.logging.backup_count == 5
        assert config.logging.console_output is True
        
        assert config.commands.auto_discovery is True
        assert config.commands.discovery_path == "docanalyzer.commands"
        assert config.commands.custom_commands_path is None
        
        assert config.file_watcher.directories == ["./documents", "./docs"]
        assert config.file_watcher.scan_interval == 300
        assert config.file_watcher.lock_timeout == 3600
        assert config.file_watcher.max_processes == 5
        
        assert config.vector_store.base_url == "http://localhost"
        assert config.vector_store.port == 8007
        assert config.vector_store.timeout == 30
        
        assert config.chunker.base_url == "http://localhost"
        assert config.chunker.port == 8009
        assert config.chunker.timeout == 30
        
        assert config.embedding.base_url == "http://localhost"
        assert config.embedding.port == 8001
        assert config.embedding.timeout == 30
    
    @patch('docanalyzer.config.unified_config.framework_config')
    @patch('docanalyzer.config.unified_config.Settings')
    @patch('docanalyzer.config.unified_config.get_custom_setting_value')
    def test_unified_config_validation_success(self, mock_get_custom_setting, mock_settings, mock_framework_config):
        """Test UnifiedConfig validation with valid configuration."""
        # Mock Settings methods with valid values
        mock_settings.get_server_settings.return_value = {
            'host': '127.0.0.1',
            'port': 8080,
            'debug': False,
            'log_level': 'INFO'
        }
        mock_settings.get_logging_settings.return_value = {
            'level': 'INFO',
            'backup_count': 5
        }
        mock_settings.get_commands_settings.return_value = {}
        
        # Mock custom setting values with valid values
        mock_get_custom_setting.side_effect = lambda key, default: {
            'file_watcher': {
                'scan_interval': 300,
                'lock_timeout': 3600,
                'max_processes': 5
            },
            'vector_store': {
                'port': 8007,
                'timeout': 30
            },
            'chunker': {
                'port': 8009,
                'timeout': 30
            },
            'embedding': {
                'port': 8001,
                'timeout': 30
            }
        }.get(key, default)
        
        config = UnifiedConfig()
        
        # Validation should pass
        assert config.validate_configuration() is True
    
    @patch('docanalyzer.config.unified_config.framework_config')
    @patch('docanalyzer.config.unified_config.Settings')
    @patch('docanalyzer.config.unified_config.get_custom_setting_value')
    def test_unified_config_validation_failure(self, mock_get_custom_setting, mock_settings, mock_framework_config):
        """Test UnifiedConfig validation with invalid configuration."""
        # Mock Settings methods with invalid values
        mock_settings.get_server_settings.return_value = {
            'host': '127.0.0.1',
            'port': 70000,  # Invalid port
            'debug': False,
            'log_level': 'INVALID'  # Invalid log level
        }
        mock_settings.get_logging_settings.return_value = {
            'level': 'INFO',
            'backup_count': -1  # Invalid backup count
        }
        mock_settings.get_commands_settings.return_value = {}
        
        # Mock custom setting values with invalid values
        mock_get_custom_setting.side_effect = lambda key, default: {
            'file_watcher': {
                'scan_interval': -1,  # Invalid scan interval
                'lock_timeout': 3600,
                'max_processes': 5
            },
            'vector_store': {
                'port': 8007,
                'timeout': 30
            },
            'chunker': {
                'port': 8009,
                'timeout': 30
            },
            'embedding': {
                'port': 8001,
                'timeout': 30
            }
        }.get(key, default)
        
        config = UnifiedConfig()
        
        # Set invalid values directly
        config.server.port = 70000  # Invalid port
        config.server.log_level = 'INVALID'  # Invalid log level
        config.logging.backup_count = -1  # Invalid backup count
        config.file_watcher.scan_interval = -1  # Invalid scan interval
        
        # Validation should fail
        with pytest.raises(ValidationError) as exc_info:
            config.validate_configuration()
        
        assert "Configuration validation failed" in str(exc_info.value)
        assert len(exc_info.value.errors) > 0
    
    @patch('docanalyzer.config.unified_config.framework_config')
    @patch('docanalyzer.config.unified_config.Settings')
    @patch('docanalyzer.config.unified_config.get_custom_setting_value')
    def test_get_service_url(self, mock_get_custom_setting, mock_settings, mock_framework_config):
        """Test get_service_url method."""
        # Mock Settings methods
        mock_settings.get_server_settings.return_value = {}
        mock_settings.get_logging_settings.return_value = {}
        mock_settings.get_commands_settings.return_value = {}
        
        # Mock custom setting values
        mock_get_custom_setting.side_effect = lambda key, default: {
            'vector_store': {
                'base_url': 'https://vector.host',
                'port': 9000
            },
            'chunker': {
                'base_url': 'https://chunker.host',
                'port': 9001
            },
            'embedding': {
                'base_url': 'https://embedding.host',
                'port': 9002
            }
        }.get(key, default)
        
        config = UnifiedConfig()
        
        # Test service URLs
        assert config.get_service_url('vector_store') == 'https://vector.host:9000'
        assert config.get_service_url('chunker') == 'https://chunker.host:9001'
        assert config.get_service_url('embedding') == 'https://embedding.host:9002'
        
        # Test invalid service
        with pytest.raises(ValueError, match="Unsupported service: invalid_service"):
            config.get_service_url('invalid_service')
    
    @patch('docanalyzer.config.unified_config.framework_config')
    @patch('docanalyzer.config.unified_config.Settings')
    @patch('docanalyzer.config.unified_config.get_custom_setting_value')
    def test_to_dict(self, mock_get_custom_setting, mock_settings, mock_framework_config):
        """Test to_dict method."""
        # Mock Settings methods
        mock_settings.get_server_settings.return_value = {
            'host': '127.0.0.1',
            'port': 8080,
            'debug': True,
            'log_level': 'DEBUG'
        }
        mock_settings.get_logging_settings.return_value = {
            'level': 'DEBUG',
            'log_dir': '/custom/logs'
        }
        mock_settings.get_commands_settings.return_value = {
            'auto_discovery': False
        }
        
        # Mock custom setting values
        mock_get_custom_setting.side_effect = lambda key, default: {
            'file_watcher': {
                'directories': ['/custom/dir1'],
                'scan_interval': 600
            },
            'vector_store': {
                'base_url': 'https://vector.host',
                'port': 9000
            },
            'chunker': {
                'base_url': 'https://chunker.host',
                'port': 9001
            },
            'embedding': {
                'base_url': 'https://embedding.host',
                'port': 9002
            }
        }.get(key, default)
        
        config = UnifiedConfig()
        config_dict = config.to_dict()
        
        # Verify dictionary structure
        assert 'server' in config_dict
        assert 'logging' in config_dict
        assert 'commands' in config_dict
        assert 'file_watcher' in config_dict
        assert 'vector_store' in config_dict
        assert 'chunker' in config_dict
        assert 'embedding' in config_dict
        
        # Verify some values
        assert config_dict['server']['host'] == '127.0.0.1'
        assert config_dict['server']['port'] == 8080
        assert config_dict['server']['debug'] is True
        assert config_dict['logging']['level'] == 'DEBUG'
        assert config_dict['commands']['auto_discovery'] is False
        assert config_dict['file_watcher']['directories'] == ['/custom/dir1']
        assert config_dict['vector_store']['base_url'] == 'https://vector.host'


class TestConfigError:
    """Test suite for ConfigError class."""
    
    def test_config_error_creation(self):
        """Test ConfigError creation."""
        error = ConfigError("Configuration loading failed")
        
        assert str(error) == "Configuration loading failed"
        assert error.message == "Configuration loading failed"


class TestValidationError:
    """Test suite for ValidationError class."""
    
    def test_validation_error_creation_with_errors(self):
        """Test ValidationError creation with error list."""
        errors = ["Port must be positive", "Host cannot be empty"]
        error = ValidationError("Configuration validation failed", errors)
        
        assert str(error) == "Configuration validation failed"
        assert error.message == "Configuration validation failed"
        assert error.errors == errors
    
    def test_validation_error_creation_without_errors(self):
        """Test ValidationError creation without error list."""
        error = ValidationError("Configuration validation failed")
        
        assert str(error) == "Configuration validation failed"
        assert error.message == "Configuration validation failed"
        assert error.errors == []


class TestGlobalConfig:
    """Test suite for global configuration functions."""
    
    @patch('docanalyzer.config.unified_config._unified_config')
    def test_get_unified_config_existing(self, mock_global_config):
        """Test get_unified_config with existing instance."""
        mock_config = Mock()
        mock_global_config.__class__ = Mock
        mock_global_config.__class__.__name__ = 'UnifiedConfig'
        mock_global_config.__class__.__module__ = 'docanalyzer.config.unified_config'
        
        # Set the global instance
        import docanalyzer.config.unified_config as config_module
        config_module._unified_config = mock_config
        
        result = get_unified_config()
        
        assert result == mock_config
    
    @patch('docanalyzer.config.unified_config.UnifiedConfig')
    def test_get_unified_config_new(self, mock_unified_config_class):
        """Test get_unified_config with new instance."""
        mock_config = Mock()
        mock_unified_config_class.return_value = mock_config
        
        # Clear the global instance
        import docanalyzer.config.unified_config as config_module
        config_module._unified_config = None
        
        result = get_unified_config()
        
        assert result == mock_config
        mock_unified_config_class.assert_called_once()
    
    @patch('docanalyzer.config.unified_config._unified_config')
    def test_reload_unified_config_existing(self, mock_global_config):
        """Test reload_unified_config with existing instance."""
        mock_config = Mock()
        
        # Set the global instance
        import docanalyzer.config.unified_config as config_module
        config_module._unified_config = mock_config
        
        reload_unified_config()
        
        mock_config.reload_configuration.assert_called_once()
    
    @patch('docanalyzer.config.unified_config.UnifiedConfig')
    def test_reload_unified_config_new(self, mock_unified_config_class):
        """Test reload_unified_config with new instance."""
        mock_config = Mock()
        mock_unified_config_class.return_value = mock_config
        
        # Clear the global instance
        import docanalyzer.config.unified_config as config_module
        config_module._unified_config = None
        
        reload_unified_config()
        
        mock_unified_config_class.assert_called_once() 