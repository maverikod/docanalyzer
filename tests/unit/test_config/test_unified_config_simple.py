"""
Simple Tests for Unified Configuration

Basic test suite for the unified configuration system without
importing problematic external dependencies.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Test only the configuration classes without external dependencies
from docanalyzer.config.unified_config import (
    ServerConfig,
    LoggingConfig,
    CommandsConfig,
    FileWatcherConfig,
    VectorStoreConfig,
    ChunkerConfig,
    EmbeddingConfig,
    ConfigError,
    ValidationError
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


class TestConfigurationIntegration:
    """Test suite for configuration integration."""
    
    def test_configuration_objects_work_together(self):
        """Test that configuration objects work together properly."""
        # Create all configuration objects
        server_config = ServerConfig(host="127.0.0.1", port=8080)
        logging_config = LoggingConfig(level="DEBUG")
        commands_config = CommandsConfig(auto_discovery=False)
        file_watcher_config = FileWatcherConfig(directories=["/test/dir"])
        vector_store_config = VectorStoreConfig(base_url="https://vector.host", port=9000)
        chunker_config = ChunkerConfig(base_url="https://chunker.host", port=9001)
        embedding_config = EmbeddingConfig(base_url="https://embedding.host", port=9002)
        
        # Verify they work together
        assert server_config.host == "127.0.0.1"
        assert logging_config.level == "DEBUG"
        assert commands_config.auto_discovery is False
        assert file_watcher_config.directories == ["/test/dir"]
        assert vector_store_config.base_url == "https://vector.host"
        assert chunker_config.base_url == "https://chunker.host"
        assert embedding_config.base_url == "https://embedding.host"
    
    def test_configuration_serialization(self):
        """Test that configuration objects can be serialized."""
        config = ServerConfig(host="127.0.0.1", port=8080)
        
        # Test that we can access all attributes
        config_dict = {
            'host': config.host,
            'port': config.port,
            'debug': config.debug,
            'log_level': config.log_level
        }
        
        assert config_dict['host'] == "127.0.0.1"
        assert config_dict['port'] == 8080
        assert config_dict['debug'] is False
        assert config_dict['log_level'] == "INFO" 