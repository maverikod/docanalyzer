"""
Tests for DocAnalyzer Configuration Extensions

Comprehensive test suite for DocAnalyzer configuration extension functions
that provide convenient access to configuration settings.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from docanalyzer.config.extensions import (
    get_file_watcher_settings,
    get_vector_store_settings,
    get_chunker_settings,
    get_embedding_settings,
    get_file_watcher_directories,
    get_file_watcher_scan_interval,
    get_file_watcher_lock_timeout,
    get_file_watcher_max_processes,
    get_vector_store_url,
    get_chunker_url,
    get_embedding_url,
    get_service_timeout
)


class TestFileWatcherSettings:
    """Test suite for file watcher settings functions."""
    
    @patch('docanalyzer.config.extensions.get_custom_setting_value')
    def test_get_file_watcher_settings_with_config(self, mock_get_setting):
        """Test getting file watcher settings with configuration."""
        mock_config = {
            'directories': ['/path/to/docs'],
            'scan_interval': 600,
            'lock_timeout': 7200,
            'max_processes': 10
        }
        mock_get_setting.return_value = mock_config
        
        settings = get_file_watcher_settings()
        
        assert settings == mock_config
        mock_get_setting.assert_called_once_with('file_watcher', {})
    
    @patch('docanalyzer.config.extensions.get_custom_setting_value')
    def test_get_file_watcher_settings_without_config(self, mock_get_setting):
        """Test getting file watcher settings without configuration."""
        mock_get_setting.return_value = {}
        
        settings = get_file_watcher_settings()
        
        assert 'directories' in settings
        assert 'scan_interval' in settings
        assert 'lock_timeout' in settings
        assert 'max_processes' in settings
        assert settings['directories'] == ["./documents", "./docs"]
        assert settings['scan_interval'] == 300
        assert settings['lock_timeout'] == 3600
        assert settings['max_processes'] == 5
    
    @patch('docanalyzer.config.extensions.get_file_watcher_settings')
    def test_get_file_watcher_directories(self, mock_get_settings):
        """Test getting file watcher directories."""
        mock_settings = {
            'directories': ['/custom/path'],
            'scan_interval': 300,
            'lock_timeout': 3600,
            'max_processes': 5
        }
        mock_get_settings.return_value = mock_settings
        
        directories = get_file_watcher_directories()
        
        assert directories == ['/custom/path']
    
    @patch('docanalyzer.config.extensions.get_file_watcher_settings')
    def test_get_file_watcher_directories_default(self, mock_get_settings):
        """Test getting file watcher directories with default."""
        mock_settings = {
            'scan_interval': 300,
            'lock_timeout': 3600,
            'max_processes': 5
        }
        mock_get_settings.return_value = mock_settings
        
        directories = get_file_watcher_directories()
        
        assert directories == ["./documents", "./docs"]
    
    @patch('docanalyzer.config.extensions.get_file_watcher_settings')
    def test_get_file_watcher_scan_interval(self, mock_get_settings):
        """Test getting file watcher scan interval."""
        mock_settings = {
            'directories': ["./documents", "./docs"],
            'scan_interval': 600,
            'lock_timeout': 3600,
            'max_processes': 5
        }
        mock_get_settings.return_value = mock_settings
        
        interval = get_file_watcher_scan_interval()
        
        assert interval == 600
    
    @patch('docanalyzer.config.extensions.get_file_watcher_settings')
    def test_get_file_watcher_scan_interval_default(self, mock_get_settings):
        """Test getting file watcher scan interval with default."""
        mock_settings = {
            'directories': ["./documents", "./docs"],
            'lock_timeout': 3600,
            'max_processes': 5
        }
        mock_get_settings.return_value = mock_settings
        
        interval = get_file_watcher_scan_interval()
        
        assert interval == 300
    
    @patch('docanalyzer.config.extensions.get_file_watcher_settings')
    def test_get_file_watcher_lock_timeout(self, mock_get_settings):
        """Test getting file watcher lock timeout."""
        mock_settings = {
            'directories': ["./documents", "./docs"],
            'scan_interval': 300,
            'lock_timeout': 7200,
            'max_processes': 5
        }
        mock_get_settings.return_value = mock_settings
        
        timeout = get_file_watcher_lock_timeout()
        
        assert timeout == 7200
    
    @patch('docanalyzer.config.extensions.get_file_watcher_settings')
    def test_get_file_watcher_lock_timeout_default(self, mock_get_settings):
        """Test getting file watcher lock timeout with default."""
        mock_settings = {
            'directories': ["./documents", "./docs"],
            'scan_interval': 300,
            'max_processes': 5
        }
        mock_get_settings.return_value = mock_settings
        
        timeout = get_file_watcher_lock_timeout()
        
        assert timeout == 3600
    
    @patch('docanalyzer.config.extensions.get_file_watcher_settings')
    def test_get_file_watcher_max_processes(self, mock_get_settings):
        """Test getting file watcher max processes."""
        mock_settings = {
            'directories': ["./documents", "./docs"],
            'scan_interval': 300,
            'lock_timeout': 3600,
            'max_processes': 10
        }
        mock_get_settings.return_value = mock_settings
        
        max_procs = get_file_watcher_max_processes()
        
        assert max_procs == 10
    
    @patch('docanalyzer.config.extensions.get_file_watcher_settings')
    def test_get_file_watcher_max_processes_default(self, mock_get_settings):
        """Test getting file watcher max processes with default."""
        mock_settings = {
            'directories': ["./documents", "./docs"],
            'scan_interval': 300,
            'lock_timeout': 3600
        }
        mock_get_settings.return_value = mock_settings
        
        max_procs = get_file_watcher_max_processes()
        
        assert max_procs == 5


class TestVectorStoreSettings:
    """Test suite for vector store settings functions."""
    
    @patch('docanalyzer.config.extensions.get_custom_setting_value')
    def test_get_vector_store_settings_with_config(self, mock_get_setting):
        """Test getting vector store settings with configuration."""
        mock_config = {
            'base_url': 'http://vector-store',
            'port': 9000,
            'timeout': 60
        }
        mock_get_setting.return_value = mock_config
        
        settings = get_vector_store_settings()
        
        assert settings == mock_config
        mock_get_setting.assert_called_once_with('vector_store', {})
    
    @patch('docanalyzer.config.extensions.get_custom_setting_value')
    def test_get_vector_store_settings_without_config(self, mock_get_setting):
        """Test getting vector store settings without configuration."""
        mock_get_setting.return_value = {}
        
        settings = get_vector_store_settings()
        
        assert 'base_url' in settings
        assert 'port' in settings
        assert 'timeout' in settings
        assert settings['base_url'] == "http://localhost"
        assert settings['port'] == 8007
        assert settings['timeout'] == 30
    
    @patch('docanalyzer.config.extensions.get_vector_store_settings')
    def test_get_vector_store_url(self, mock_get_settings):
        """Test getting vector store URL."""
        mock_settings = {
            'base_url': 'http://vector-store',
            'port': 9000,
            'timeout': 30
        }
        mock_get_settings.return_value = mock_settings
        
        url = get_vector_store_url()
        
        assert url == "http://vector-store:9000"
    
    @patch('docanalyzer.config.extensions.get_vector_store_settings')
    def test_get_vector_store_url_default(self, mock_get_settings):
        """Test getting vector store URL with defaults."""
        mock_settings = {
            'timeout': 30
        }
        mock_get_settings.return_value = mock_settings
        
        url = get_vector_store_url()
        
        assert url == "http://localhost:8007"


class TestChunkerSettings:
    """Test suite for chunker settings functions."""
    
    @patch('docanalyzer.config.extensions.get_custom_setting_value')
    def test_get_chunker_settings_with_config(self, mock_get_setting):
        """Test getting chunker settings with configuration."""
        mock_config = {
            'base_url': 'http://chunker',
            'port': 9001,
            'timeout': 45
        }
        mock_get_setting.return_value = mock_config
        
        settings = get_chunker_settings()
        
        assert settings == mock_config
        mock_get_setting.assert_called_once_with('chunker', {})
    
    @patch('docanalyzer.config.extensions.get_custom_setting_value')
    def test_get_chunker_settings_without_config(self, mock_get_setting):
        """Test getting chunker settings without configuration."""
        mock_get_setting.return_value = {}
        
        settings = get_chunker_settings()
        
        assert 'base_url' in settings
        assert 'port' in settings
        assert 'timeout' in settings
        assert settings['base_url'] == "http://localhost"
        assert settings['port'] == 8009
        assert settings['timeout'] == 30
    
    @patch('docanalyzer.config.extensions.get_chunker_settings')
    def test_get_chunker_url(self, mock_get_settings):
        """Test getting chunker URL."""
        mock_settings = {
            'base_url': 'http://chunker',
            'port': 9001,
            'timeout': 30
        }
        mock_get_settings.return_value = mock_settings
        
        url = get_chunker_url()
        
        assert url == "http://chunker:9001"
    
    @patch('docanalyzer.config.extensions.get_chunker_settings')
    def test_get_chunker_url_default(self, mock_get_settings):
        """Test getting chunker URL with defaults."""
        mock_settings = {
            'timeout': 30
        }
        mock_get_settings.return_value = mock_settings
        
        url = get_chunker_url()
        
        assert url == "http://localhost:8009"


class TestEmbeddingSettings:
    """Test suite for embedding settings functions."""
    
    @patch('docanalyzer.config.extensions.get_custom_setting_value')
    def test_get_embedding_settings_with_config(self, mock_get_setting):
        """Test getting embedding settings with configuration."""
        mock_config = {
            'base_url': 'http://embedding',
            'port': 9002,
            'timeout': 60
        }
        mock_get_setting.return_value = mock_config
        
        settings = get_embedding_settings()
        
        assert settings == mock_config
        mock_get_setting.assert_called_once_with('embedding', {})
    
    @patch('docanalyzer.config.extensions.get_custom_setting_value')
    def test_get_embedding_settings_without_config(self, mock_get_setting):
        """Test getting embedding settings without configuration."""
        mock_get_setting.return_value = {}
        
        settings = get_embedding_settings()
        
        assert 'base_url' in settings
        assert 'port' in settings
        assert 'timeout' in settings
        assert settings['base_url'] == "http://localhost"
        assert settings['port'] == 8001
        assert settings['timeout'] == 30
    
    @patch('docanalyzer.config.extensions.get_embedding_settings')
    def test_get_embedding_url(self, mock_get_settings):
        """Test getting embedding URL."""
        mock_settings = {
            'base_url': 'http://embedding',
            'port': 9002,
            'timeout': 30
        }
        mock_get_settings.return_value = mock_settings
        
        url = get_embedding_url()
        
        assert url == "http://embedding:9002"
    
    @patch('docanalyzer.config.extensions.get_embedding_settings')
    def test_get_embedding_url_default(self, mock_get_settings):
        """Test getting embedding URL with defaults."""
        mock_settings = {
            'timeout': 30
        }
        mock_get_settings.return_value = mock_settings
        
        url = get_embedding_url()
        
        assert url == "http://localhost:8001"


class TestServiceTimeout:
    """Test suite for service timeout functions."""
    
    @patch('docanalyzer.config.extensions.get_vector_store_settings')
    def test_get_service_timeout_vector_store(self, mock_get_settings):
        """Test getting timeout for vector store service."""
        mock_settings = {
            'base_url': 'http://localhost',
            'port': 8007,
            'timeout': 60
        }
        mock_get_settings.return_value = mock_settings
        
        timeout = get_service_timeout('vector_store')
        
        assert timeout == 60
    
    @patch('docanalyzer.config.extensions.get_chunker_settings')
    def test_get_service_timeout_chunker(self, mock_get_settings):
        """Test getting timeout for chunker service."""
        mock_settings = {
            'base_url': 'http://localhost',
            'port': 8009,
            'timeout': 45
        }
        mock_get_settings.return_value = mock_settings
        
        timeout = get_service_timeout('chunker')
        
        assert timeout == 45
    
    @patch('docanalyzer.config.extensions.get_embedding_settings')
    def test_get_service_timeout_embedding(self, mock_get_settings):
        """Test getting timeout for embedding service."""
        mock_settings = {
            'base_url': 'http://localhost',
            'port': 8001,
            'timeout': 90
        }
        mock_get_settings.return_value = mock_settings
        
        timeout = get_service_timeout('embedding')
        
        assert timeout == 90
    
    def test_get_service_timeout_invalid_service(self):
        """Test getting timeout for invalid service."""
        with pytest.raises(ValueError, match="Unsupported service"):
            get_service_timeout('invalid_service')
    
    @patch('docanalyzer.config.extensions.get_vector_store_settings')
    def test_get_service_timeout_default(self, mock_get_settings):
        """Test getting timeout with default value."""
        mock_settings = {
            'base_url': 'http://localhost',
            'port': 8007
        }
        mock_get_settings.return_value = mock_settings
        
        timeout = get_service_timeout('vector_store')
        
        assert timeout == 30 