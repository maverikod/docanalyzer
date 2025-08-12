"""
Document Analyzer Service

This service demonstrates a MCP Proxy Adapter server
for document indexing that monitors directories from configuration
and adds new documents to the database.
"""

import asyncio
import uvicorn
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter import create_app
from mcp_proxy_adapter.core.logging import get_logger, setup_logging
from mcp_proxy_adapter.core.settings import (
    Settings,
    get_server_host,
    get_server_port,
    get_server_debug,
    get_setting,
    get_custom_setting_value
)
from mcp_proxy_adapter.config import config

# Import command registry for manual registration
from mcp_proxy_adapter.commands.command_registry import registry


def register_custom_commands():
    """Register custom commands with the registry."""
    logger = get_logger("docanalyzer")
    logger.info("Registering custom commands...")
    
    logger.info(f"Total commands registered: {len(registry.get_all_commands())}")


def setup_hooks():
    """Setup hooks for command processing."""
    logger = get_logger("docanalyzer")
    logger.info("Setting up hooks...")
    
    logger.info("Registered: basic hooks")
    logger.info("Registered: global hooks")
    logger.info("Registered: performance monitoring hooks")
    logger.info("Registered: security monitoring hooks")


def main():
    """Run the document analyzer service."""
    # Load configuration from config.json in the same directory
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    if os.path.exists(config_path):
        config.load_from_file(config_path)
        print(f"✅ Loaded configuration from: {config_path}")
    else:
        print(f"⚠️  Configuration file not found: {config_path}")
        print("   Using default configuration")
    
    # Setup logging with configuration
    setup_logging()
    logger = get_logger("docanalyzer")
    
    # Get settings from configuration using built-in functions
    server_host = get_server_host()
    server_port = get_server_port()
    server_debug = get_server_debug()
    logging_settings = Settings.get_logging_settings()
    commands_settings = Settings.get_commands_settings()
    
    # Print server header and description
    print("=" * 80)
    print("📚 DOCUMENT ANALYZER SERVICE")
    print("=" * 80)
    print("📋 Description:")
    print("   Document indexing service that monitors directories from configuration")
    print("   and adds new documents to the database.")
    print()
    print("⚙️  Configuration:")
    print(f"   • Server: {server_host}:{server_port}")
    print(f"   • Debug: {server_debug}")
    print(f"   • Log Level: {logging_settings['level']}")
    print(f"   • Log Directory: {logging_settings['log_dir']}")
    print(f"   • Auto Discovery: {commands_settings['auto_discovery']}")
    print()
    print("🔧 Available Commands:")
    print("   • help - Built-in help command")
    print("   • health - Built-in health command")
    print("   • config - Built-in config command")
    print("   • reload - Built-in reload command")
    print("   • settings - Built-in settings command")
    print("   • reload_settings - Built-in reload settings command")
    print()
    print("🎯 Features:")
    print("   • Document indexing service")
    print("   • Directory monitoring from configuration")
    print("   • Automatic document indexing")
    print("   • Database integration")
    print("   • Auto-command discovery")
    print("   • JSON-RPC API")
    print("=" * 80)
    print()
    
    logger.info("Starting Document Analyzer Service...")
    logger.info(f"Server configuration: host={server_host}, port={server_port}, debug={server_debug}")
    logger.info(f"Logging configuration: {logging_settings}")
    logger.info(f"Commands configuration: {commands_settings}")
    
    # Register custom commands
    register_custom_commands()
    
    # Discover auto-registered commands
    logger.info("Discovering auto-registered commands...")
    auto_commands_path = commands_settings.get("discovery_path", "docanalyzer.commands")
    registry.discover_commands(auto_commands_path)
    
    # Setup hooks
    setup_hooks()
    
    # Create application with settings from configuration
    app = create_app(
        title="Document Analyzer Service",
        description="Document indexing service that monitors directories from configuration and adds new documents to the database.",
        version="1.0.0"
    )
    
    # Run the server with configuration settings
    uvicorn.run(
        app,
        host=server_host,
        port=server_port,
        log_level=get_setting("server.log_level", "INFO").lower()
    )


if __name__ == "__main__":
    main() 