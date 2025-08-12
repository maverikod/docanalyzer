"""
Tests for Main Application Module

Comprehensive test suite for the main application entry point.
Tests application initialization, configuration loading, and startup procedures.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import tempfile
import json

# Import the main module and its functions
import docanalyzer.main
from docanalyzer.main import register_custom_commands, setup_hooks, main


class TestMainModule:
    """Test suite for main module functions."""
    
    @patch('docanalyzer.main.get_logger')
    def test_register_custom_commands(self, mock_get_logger):
        """Test register_custom_commands function."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Act
        register_custom_commands()
        
        # Assert
        mock_get_logger.assert_called_once_with("docanalyzer")
        mock_logger.info.assert_called()
        assert mock_logger.info.call_count >= 2  # At least 2 info calls
    
    @patch('docanalyzer.main.get_logger')
    def test_setup_hooks(self, mock_get_logger):
        """Test setup_hooks function."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Act
        setup_hooks()
        
        # Assert
        mock_get_logger.assert_called_once_with("docanalyzer")
        mock_logger.info.assert_called()
        assert mock_logger.info.call_count >= 4  # At least 4 info calls for different hooks
    
    @patch('docanalyzer.main.config')
    @patch('docanalyzer.main.setup_logging')
    @patch('docanalyzer.main.get_logger')
    @patch('docanalyzer.main.get_server_host')
    @patch('docanalyzer.main.get_server_port')
    @patch('docanalyzer.main.get_server_debug')
    @patch('docanalyzer.main.Settings.get_logging_settings')
    @patch('docanalyzer.main.Settings.get_commands_settings')
    @patch('docanalyzer.main.register_custom_commands')
    @patch('docanalyzer.main.registry')
    @patch('docanalyzer.main.setup_hooks')
    @patch('docanalyzer.main.create_app')
    @patch('docanalyzer.main.uvicorn.run')
    def test_main_with_config_file(self, mock_uvicorn_run, mock_create_app, mock_setup_hooks,
                                  mock_registry, mock_register_commands, mock_commands_settings,
                                  mock_logging_settings, mock_server_debug, mock_server_port,
                                  mock_server_host, mock_get_logger, mock_setup_logging, mock_config):
        """Test main function with existing config file."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_server_host.return_value = "localhost"
        mock_server_port.return_value = 8000
        mock_server_debug.return_value = False
        mock_logging_settings.return_value = {"level": "INFO", "log_dir": "/tmp/logs"}
        mock_commands_settings.return_value = {"auto_discovery": True, "discovery_path": "test.path"}
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "config"}, f)
            config_file_path = f.name
        
        # Mock os.path.join to return our temp file
        with patch('docanalyzer.main.os.path.join', return_value=config_file_path), \
             patch('docanalyzer.main.os.path.exists', return_value=True):
            
            # Act
            main()
            
            # Assert
            mock_config.load_from_file.assert_called_once_with(config_file_path)
            mock_setup_logging.assert_called_once()
            mock_get_logger.assert_called()
            mock_register_commands.assert_called_once()
            mock_setup_hooks.assert_called_once()
            mock_create_app.assert_called_once()
            mock_uvicorn_run.assert_called_once()
            
            # Clean up
            os.unlink(config_file_path)
    
    @patch('docanalyzer.main.config')
    @patch('docanalyzer.main.setup_logging')
    @patch('docanalyzer.main.get_logger')
    @patch('docanalyzer.main.get_server_host')
    @patch('docanalyzer.main.get_server_port')
    @patch('docanalyzer.main.get_server_debug')
    @patch('docanalyzer.main.Settings.get_logging_settings')
    @patch('docanalyzer.main.Settings.get_commands_settings')
    @patch('docanalyzer.main.register_custom_commands')
    @patch('docanalyzer.main.registry')
    @patch('docanalyzer.main.setup_hooks')
    @patch('docanalyzer.main.create_app')
    @patch('docanalyzer.main.uvicorn.run')
    def test_main_without_config_file(self, mock_uvicorn_run, mock_create_app, mock_setup_hooks,
                                     mock_registry, mock_register_commands, mock_commands_settings,
                                     mock_logging_settings, mock_server_debug, mock_server_port,
                                     mock_server_host, mock_get_logger, mock_setup_logging, mock_config):
        """Test main function without config file."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_server_host.return_value = "localhost"
        mock_server_port.return_value = 8000
        mock_server_debug.return_value = False
        mock_logging_settings.return_value = {"level": "INFO", "log_dir": "/tmp/logs"}
        mock_commands_settings.return_value = {"auto_discovery": True, "discovery_path": "test.path"}
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        # Mock os.path.exists to return False (no config file)
        with patch('docanalyzer.main.os.path.exists', return_value=False):
            
            # Act
            main()
            
            # Assert
            mock_config.load_from_file.assert_not_called()
            mock_setup_logging.assert_called_once()
            mock_get_logger.assert_called()
            mock_register_commands.assert_called_once()
            mock_setup_hooks.assert_called_once()
            mock_create_app.assert_called_once()
            mock_uvicorn_run.assert_called_once()
    
    @patch('docanalyzer.main.config')
    @patch('docanalyzer.main.setup_logging')
    @patch('docanalyzer.main.get_logger')
    @patch('docanalyzer.main.get_server_host')
    @patch('docanalyzer.main.get_server_port')
    @patch('docanalyzer.main.get_server_debug')
    @patch('docanalyzer.main.Settings.get_logging_settings')
    @patch('docanalyzer.main.Settings.get_commands_settings')
    @patch('docanalyzer.main.register_custom_commands')
    @patch('docanalyzer.main.registry')
    @patch('docanalyzer.main.setup_hooks')
    @patch('docanalyzer.main.create_app')
    @patch('docanalyzer.main.uvicorn.run')
    @patch('docanalyzer.main.get_setting')
    def test_main_with_detailed_settings(self, mock_get_setting, mock_uvicorn_run, mock_create_app,
                                        mock_setup_hooks, mock_registry, mock_register_commands,
                                        mock_commands_settings, mock_logging_settings, mock_server_debug,
                                        mock_server_port, mock_server_host, mock_get_logger,
                                        mock_setup_logging, mock_config):
        """Test main function with detailed settings verification."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_server_host.return_value = "0.0.0.0"
        mock_server_port.return_value = 8080
        mock_server_debug.return_value = True
        mock_logging_settings.return_value = {"level": "DEBUG", "log_dir": "/var/logs"}
        mock_commands_settings.return_value = {"auto_discovery": False, "discovery_path": "custom.path"}
        mock_get_setting.return_value = "DEBUG"
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        # Mock os.path.exists to return False
        with patch('docanalyzer.main.os.path.exists', return_value=False):
            
            # Act
            main()
            
            # Assert
            mock_server_host.assert_called_once()
            mock_server_port.assert_called_once()
            mock_server_debug.assert_called_once()
            mock_logging_settings.assert_called_once()
            mock_commands_settings.assert_called_once()
            mock_get_setting.assert_called_once_with("server.log_level", "INFO")
            mock_uvicorn_run.assert_called_once_with(
                mock_app,
                host="0.0.0.0",
                port=8080,
                log_level="debug"
            )
    
    @patch('docanalyzer.main.config')
    @patch('docanalyzer.main.setup_logging')
    @patch('docanalyzer.main.get_logger')
    @patch('docanalyzer.main.get_server_host')
    @patch('docanalyzer.main.get_server_port')
    @patch('docanalyzer.main.get_server_debug')
    @patch('docanalyzer.main.Settings.get_logging_settings')
    @patch('docanalyzer.main.Settings.get_commands_settings')
    @patch('docanalyzer.main.register_custom_commands')
    @patch('docanalyzer.main.registry')
    @patch('docanalyzer.main.setup_hooks')
    @patch('docanalyzer.main.create_app')
    @patch('docanalyzer.main.uvicorn.run')
    def test_main_registry_discovery(self, mock_uvicorn_run, mock_create_app, mock_setup_hooks,
                                   mock_registry, mock_register_commands, mock_commands_settings,
                                   mock_logging_settings, mock_server_debug, mock_server_port,
                                   mock_server_host, mock_get_logger, mock_setup_logging, mock_config):
        """Test main function registry discovery."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_server_host.return_value = "localhost"
        mock_server_port.return_value = 8000
        mock_server_debug.return_value = False
        mock_logging_settings.return_value = {"level": "INFO", "log_dir": "/tmp/logs"}
        mock_commands_settings.return_value = {"auto_discovery": True, "discovery_path": "test.commands"}
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        # Mock os.path.exists to return False
        with patch('docanalyzer.main.os.path.exists', return_value=False):
            
            # Act
            main()
            
            # Assert
            mock_registry.discover_commands.assert_called_once_with("test.commands")
    
    @patch('docanalyzer.main.config')
    @patch('docanalyzer.main.setup_logging')
    @patch('docanalyzer.main.get_logger')
    @patch('docanalyzer.main.get_server_host')
    @patch('docanalyzer.main.get_server_port')
    @patch('docanalyzer.main.get_server_debug')
    @patch('docanalyzer.main.Settings.get_logging_settings')
    @patch('docanalyzer.main.Settings.get_commands_settings')
    @patch('docanalyzer.main.register_custom_commands')
    @patch('docanalyzer.main.registry')
    @patch('docanalyzer.main.setup_hooks')
    @patch('docanalyzer.main.create_app')
    @patch('docanalyzer.main.uvicorn.run')
    def test_main_create_app_parameters(self, mock_uvicorn_run, mock_create_app, mock_setup_hooks,
                                      mock_registry, mock_register_commands, mock_commands_settings,
                                      mock_logging_settings, mock_server_debug, mock_server_port,
                                      mock_server_host, mock_get_logger, mock_setup_logging, mock_config):
        """Test main function create_app parameters."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_server_host.return_value = "localhost"
        mock_server_port.return_value = 8000
        mock_server_debug.return_value = False
        mock_logging_settings.return_value = {"level": "INFO", "log_dir": "/tmp/logs"}
        mock_commands_settings.return_value = {"auto_discovery": True, "discovery_path": "test.path"}
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        # Mock os.path.exists to return False
        with patch('docanalyzer.main.os.path.exists', return_value=False):
            
            # Act
            main()
            
            # Assert
            mock_create_app.assert_called_once_with(
                title="Document Analyzer Service",
                description="Document indexing service that monitors directories from configuration and adds new documents to the database.",
                version="1.0.0"
            )
    
    @patch('docanalyzer.main.config')
    @patch('docanalyzer.main.setup_logging')
    @patch('docanalyzer.main.get_logger')
    @patch('docanalyzer.main.get_server_host')
    @patch('docanalyzer.main.get_server_port')
    @patch('docanalyzer.main.get_server_debug')
    @patch('docanalyzer.main.Settings.get_logging_settings')
    @patch('docanalyzer.main.Settings.get_commands_settings')
    @patch('docanalyzer.main.register_custom_commands')
    @patch('docanalyzer.main.registry')
    @patch('docanalyzer.main.setup_hooks')
    @patch('docanalyzer.main.create_app')
    @patch('docanalyzer.main.uvicorn.run')
    def test_main_logging_calls(self, mock_uvicorn_run, mock_create_app, mock_setup_hooks,
                              mock_registry, mock_register_commands, mock_commands_settings,
                              mock_logging_settings, mock_server_debug, mock_server_port,
                              mock_server_host, mock_get_logger, mock_setup_logging, mock_config):
        """Test main function logging calls."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_server_host.return_value = "localhost"
        mock_server_port.return_value = 8000
        mock_server_debug.return_value = False
        mock_logging_settings.return_value = {"level": "INFO", "log_dir": "/tmp/logs"}
        mock_commands_settings.return_value = {"auto_discovery": True, "discovery_path": "test.path"}
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        # Mock os.path.exists to return False
        with patch('docanalyzer.main.os.path.exists', return_value=False):
            
            # Act
            main()
            
            # Assert
            expected_calls = [
                call("Starting Document Analyzer Service..."),
                call("Server configuration: host=localhost, port=8000, debug=False"),
                call("Logging configuration: {'level': 'INFO', 'log_dir': '/tmp/logs'}"),
                call("Commands configuration: {'auto_discovery': True, 'discovery_path': 'test.path'}"),
                call("Discovering auto-registered commands...")
            ]
            mock_logger.info.assert_has_calls(expected_calls, any_order=True)
    
    @patch('docanalyzer.main.config')
    @patch('docanalyzer.main.setup_logging')
    @patch('docanalyzer.main.get_logger')
    @patch('docanalyzer.main.get_server_host')
    @patch('docanalyzer.main.get_server_port')
    @patch('docanalyzer.main.get_server_debug')
    @patch('docanalyzer.main.Settings.get_logging_settings')
    @patch('docanalyzer.main.Settings.get_commands_settings')
    @patch('docanalyzer.main.register_custom_commands')
    @patch('docanalyzer.main.registry')
    @patch('docanalyzer.main.setup_hooks')
    @patch('docanalyzer.main.create_app')
    @patch('docanalyzer.main.uvicorn.run')
    def test_main_with_default_discovery_path(self, mock_uvicorn_run, mock_create_app, mock_setup_hooks,
                                            mock_registry, mock_register_commands, mock_commands_settings,
                                            mock_logging_settings, mock_server_debug, mock_server_port,
                                            mock_server_host, mock_get_logger, mock_setup_logging, mock_config):
        """Test main function with default discovery path."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_server_host.return_value = "localhost"
        mock_server_port.return_value = 8000
        mock_server_debug.return_value = False
        mock_logging_settings.return_value = {"level": "INFO", "log_dir": "/tmp/logs"}
        # Don't include discovery_path in commands_settings
        mock_commands_settings.return_value = {"auto_discovery": True}
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        # Mock os.path.exists to return False
        with patch('docanalyzer.main.os.path.exists', return_value=False):
            
            # Act
            main()
            
            # Assert
            mock_registry.discover_commands.assert_called_once_with("docanalyzer.commands")
    
    @patch('docanalyzer.main.config')
    @patch('docanalyzer.main.setup_logging')
    @patch('docanalyzer.main.get_logger')
    @patch('docanalyzer.main.get_server_host')
    @patch('docanalyzer.main.get_server_port')
    @patch('docanalyzer.main.get_server_debug')
    @patch('docanalyzer.main.Settings.get_logging_settings')
    @patch('docanalyzer.main.Settings.get_commands_settings')
    @patch('docanalyzer.main.register_custom_commands')
    @patch('docanalyzer.main.registry')
    @patch('docanalyzer.main.setup_hooks')
    @patch('docanalyzer.main.create_app')
    @patch('docanalyzer.main.uvicorn.run')
    @patch('docanalyzer.main.get_setting')
    def test_main_uvicorn_log_level_uppercase(self, mock_get_setting, mock_uvicorn_run, mock_create_app,
                                             mock_setup_hooks, mock_registry, mock_register_commands,
                                             mock_commands_settings, mock_logging_settings, mock_server_debug,
                                             mock_server_port, mock_server_host, mock_get_logger,
                                             mock_setup_logging, mock_config):
        """Test main function with uppercase log level."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_server_host.return_value = "localhost"
        mock_server_port.return_value = 8000
        mock_server_debug.return_value = False
        mock_logging_settings.return_value = {"level": "INFO", "log_dir": "/tmp/logs"}
        mock_commands_settings.return_value = {"auto_discovery": True}
        mock_get_setting.return_value = "WARNING"
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        # Mock os.path.exists to return False
        with patch('docanalyzer.main.os.path.exists', return_value=False):
            
            # Act
            main()
            
            # Assert
            mock_uvicorn_run.assert_called_once_with(
                mock_app,
                host="localhost",
                port=8000,
                log_level="warning"
            )
    
    @patch('docanalyzer.main.config')
    @patch('docanalyzer.main.setup_logging')
    @patch('docanalyzer.main.get_logger')
    @patch('docanalyzer.main.get_server_host')
    @patch('docanalyzer.main.get_server_port')
    @patch('docanalyzer.main.get_server_debug')
    @patch('docanalyzer.main.Settings.get_logging_settings')
    @patch('docanalyzer.main.Settings.get_commands_settings')
    @patch('docanalyzer.main.register_custom_commands')
    @patch('docanalyzer.main.registry')
    @patch('docanalyzer.main.setup_hooks')
    @patch('docanalyzer.main.create_app')
    @patch('docanalyzer.main.uvicorn.run')
    @patch('docanalyzer.main.get_setting')
    def test_main_uvicorn_log_level_mixed_case(self, mock_get_setting, mock_uvicorn_run, mock_create_app,
                                              mock_setup_hooks, mock_registry, mock_register_commands,
                                              mock_commands_settings, mock_logging_settings, mock_server_debug,
                                              mock_server_port, mock_server_host, mock_get_logger,
                                              mock_setup_logging, mock_config):
        """Test main function with mixed case log level."""
        # Arrange
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_server_host.return_value = "localhost"
        mock_server_port.return_value = 8000
        mock_server_debug.return_value = False
        mock_logging_settings.return_value = {"level": "INFO", "log_dir": "/tmp/logs"}
        mock_commands_settings.return_value = {"auto_discovery": True}
        mock_get_setting.return_value = "Error"
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        # Mock os.path.exists to return False
        with patch('docanalyzer.main.os.path.exists', return_value=False):
            
            # Act
            main()
            
            # Assert
            mock_uvicorn_run.assert_called_once_with(
                mock_app,
                host="localhost",
                port=8000,
                log_level="error"
            ) 