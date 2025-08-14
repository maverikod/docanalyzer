#!/usr/bin/env python3
"""
Direct Test for Unified Configuration

Direct test for the unified configuration system without
importing the entire docanalyzer package.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import only the configuration module
sys.path.insert(0, str(project_root / "docanalyzer" / "config"))

# Mock external dependencies
import unittest.mock as mock

# Mock the problematic imports
sys.modules['mcp_proxy_adapter'] = mock.MagicMock()
sys.modules['mcp_proxy_adapter.core.settings'] = mock.MagicMock()
sys.modules['mcp_proxy_adapter.config'] = mock.MagicMock()

# Now import the configuration
from unified_config import (
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


def test_server_config_defaults():
    """Test ServerConfig with default values."""
    config = ServerConfig()
    
    assert config.host == "0.0.0.0"
    assert config.port == 8015
    assert config.debug is False
    assert config.log_level == "INFO"
    print("✅ ServerConfig defaults test passed")


def test_server_config_custom_values():
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
    print("✅ ServerConfig custom values test passed")


def test_logging_config_defaults():
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
    print("✅ LoggingConfig defaults test passed")


def test_logging_config_custom_values():
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
    print("✅ LoggingConfig custom values test passed")


def test_commands_config_defaults():
    """Test CommandsConfig with default values."""
    config = CommandsConfig()
    
    assert config.auto_discovery is True
    assert config.discovery_path == "docanalyzer.commands"
    assert config.custom_commands_path is None
    print("✅ CommandsConfig defaults test passed")


def test_commands_config_custom_values():
    """Test CommandsConfig with custom values."""
    config = CommandsConfig(
        auto_discovery=False,
        discovery_path="custom.commands",
        custom_commands_path="/custom/path"
    )
    
    assert config.auto_discovery is False
    assert config.discovery_path == "custom.commands"
    assert config.custom_commands_path == "/custom/path"
    print("✅ CommandsConfig custom values test passed")


def test_file_watcher_config_defaults():
    """Test FileWatcherConfig with default values."""
    config = FileWatcherConfig()
    
    assert config.directories == ["./documents", "./docs"]
    assert config.scan_interval == 300
    assert config.lock_timeout == 3600
    assert config.max_processes == 5
    print("✅ FileWatcherConfig defaults test passed")


def test_file_watcher_config_custom_values():
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
    print("✅ FileWatcherConfig custom values test passed")


def test_vector_store_config_defaults():
    """Test VectorStoreConfig with default values."""
    config = VectorStoreConfig()
    
    assert config.base_url == "http://localhost"
    assert config.port == 8007
    assert config.timeout == 30
    print("✅ VectorStoreConfig defaults test passed")


def test_vector_store_config_custom_values():
    """Test VectorStoreConfig with custom values."""
    config = VectorStoreConfig(
        base_url="https://custom.host",
        port=9000,
        timeout=60
    )
    
    assert config.base_url == "https://custom.host"
    assert config.port == 9000
    assert config.timeout == 60
    print("✅ VectorStoreConfig custom values test passed")


def test_chunker_config_defaults():
    """Test ChunkerConfig with default values."""
    config = ChunkerConfig()
    
    assert config.base_url == "http://localhost"
    assert config.port == 8009
    assert config.timeout == 30
    print("✅ ChunkerConfig defaults test passed")


def test_chunker_config_custom_values():
    """Test ChunkerConfig with custom values."""
    config = ChunkerConfig(
        base_url="https://chunker.host",
        port=9001,
        timeout=45
    )
    
    assert config.base_url == "https://chunker.host"
    assert config.port == 9001
    assert config.timeout == 45
    print("✅ ChunkerConfig custom values test passed")


def test_embedding_config_defaults():
    """Test EmbeddingConfig with default values."""
    config = EmbeddingConfig()
    
    assert config.base_url == "http://localhost"
    assert config.port == 8001
    assert config.timeout == 30
    print("✅ EmbeddingConfig defaults test passed")


def test_embedding_config_custom_values():
    """Test EmbeddingConfig with custom values."""
    config = EmbeddingConfig(
        base_url="https://embedding.host",
        port=9002,
        timeout=90
    )
    
    assert config.base_url == "https://embedding.host"
    assert config.port == 9002
    assert config.timeout == 90
    print("✅ EmbeddingConfig custom values test passed")


def test_config_error_creation():
    """Test ConfigError creation."""
    error = ConfigError("Configuration loading failed")
    
    assert str(error) == "Configuration loading failed"
    assert error.message == "Configuration loading failed"
    print("✅ ConfigError creation test passed")


def test_validation_error_creation_with_errors():
    """Test ValidationError creation with error list."""
    errors = ["Port must be positive", "Host cannot be empty"]
    error = ValidationError("Configuration validation failed", errors)
    
    assert str(error) == "Configuration validation failed"
    assert error.message == "Configuration validation failed"
    assert error.errors == errors
    print("✅ ValidationError creation with errors test passed")


def test_validation_error_creation_without_errors():
    """Test ValidationError creation without error list."""
    error = ValidationError("Configuration validation failed")
    
    assert str(error) == "Configuration validation failed"
    assert error.message == "Configuration validation failed"
    assert error.errors == []
    print("✅ ValidationError creation without errors test passed")


def test_configuration_objects_work_together():
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
    print("✅ Configuration objects integration test passed")


def test_configuration_serialization():
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
    print("✅ Configuration serialization test passed")


def main():
    """Run all tests."""
    print("🧪 Running Unified Configuration Tests")
    print("=" * 50)
    
    try:
        test_server_config_defaults()
        test_server_config_custom_values()
        test_logging_config_defaults()
        test_logging_config_custom_values()
        test_commands_config_defaults()
        test_commands_config_custom_values()
        test_file_watcher_config_defaults()
        test_file_watcher_config_custom_values()
        test_vector_store_config_defaults()
        test_vector_store_config_custom_values()
        test_chunker_config_defaults()
        test_chunker_config_custom_values()
        test_embedding_config_defaults()
        test_embedding_config_custom_values()
        test_config_error_creation()
        test_validation_error_creation_with_errors()
        test_validation_error_creation_without_errors()
        test_configuration_objects_work_together()
        test_configuration_serialization()
        
        print("=" * 50)
        print("🎉 All tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main()) 