"""
Health Check Command for DocAnalyzer

Command that returns information about DocAnalyzer health and status.
Uses the HealthChecker service for comprehensive health monitoring.
"""

import os
import platform
import sys
import psutil
from datetime import datetime
from typing import Dict, Any

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import CommandResult

# Import DocAnalyzer health monitoring
from docanalyzer.monitoring.health import HealthChecker
from docanalyzer.config import get_unified_config


class HealthCheckResult(CommandResult):
    """
    Result of the health check command execution.
    """
    
    def __init__(self, status: str, version: str, uptime: float, 
                 components: Dict[str, Any], docanalyzer_metrics: Dict[str, Any]):
        """
        Initialize health check command result.
        
        Args:
            status: Server status ("ok" or "error")
            version: Server version
            uptime: Server uptime in seconds
            components: Dictionary with components status
            docanalyzer_metrics: DocAnalyzer specific metrics
        """
        self.status = status
        self.version = version
        self.uptime = uptime
        self.components = components
        self.docanalyzer_metrics = docanalyzer_metrics
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.
        
        Returns:
            Dict[str, Any]: Result as dictionary
        """
        return {
            "status": self.status,
            "version": self.version,
            "uptime": self.uptime,
            "components": self.components,
            "docanalyzer_metrics": self.docanalyzer_metrics,
            "command_type": "health_check"
        }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Get JSON schema for the result.
        
        Returns:
            Dict[str, Any]: JSON schema
        """
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "version": {"type": "string"},
                "uptime": {"type": "number"},
                "components": {"type": "object"},
                "docanalyzer_metrics": {"type": "object"},
                "command_type": {"type": "string"}
            },
            "required": ["status", "version", "uptime", "components", "docanalyzer_metrics", "command_type"]
        }


class HealthCheckCommand(Command):
    """
    Health check command for DocAnalyzer.
    
    Uses the HealthChecker service for comprehensive health monitoring
    and provides detailed health status information.
    """
    
    name = "health_check"
    result_class = HealthCheckResult
    
    def __init__(self):
        """Initialize health check command with HealthChecker service."""
        super().__init__()
        self.health_checker = HealthChecker()
        self.config = get_unified_config()
    
    async def execute(self, **kwargs) -> HealthCheckResult:
        """
        Execute health check command.
        
        Uses HealthChecker service to get comprehensive health information
        including system health, component health, and DocAnalyzer-specific metrics.
        
        Returns:
            HealthCheckResult: Health check command result
        """
        # Get version from package
        try:
            from docanalyzer import __version__ as version
        except ImportError:
            version = "unknown"
        
        # Get process start time
        process = psutil.Process(os.getpid())
        start_time = datetime.fromtimestamp(process.create_time())
        uptime_seconds = (datetime.now() - start_time).total_seconds()
        
        # Get comprehensive health information using HealthChecker
        try:
            # Initialize health checker if not already initialized
            if not self.health_checker.is_initialized:
                await self.health_checker.initialize()
            
            # Get overall health status
            overall_health = await self.health_checker.get_overall_health()
            
            # Get component health information
            component_health = await self.health_checker.get_component_health()
            
            # Get system health information
            system_health = await self.health_checker.get_system_health()
            
            # Get DocAnalyzer specific health metrics
            docanalyzer_health = await self.health_checker.get_docanalyzer_health()
            
        except Exception as e:
            # Fallback to basic health information if HealthChecker fails
            overall_health = {"status": "unknown", "message": f"HealthChecker error: {str(e)}"}
            component_health = {}
            system_health = {}
            docanalyzer_health = {}
        
        # Get system information
        system_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "health_status": system_health.get("status", "unknown"),
            "health_metrics": system_health.get("metrics", {})
        }
        
        # Get process information
        process_info = {
            "pid": os.getpid(),
            "memory_usage": process.memory_info().rss,
            "cpu_percent": process.cpu_percent(),
            "create_time": process.create_time(),
            "health_status": "running"
        }
        
        # Get DocAnalyzer specific information
        try:
            from docanalyzer.services import LockManager, DirectoryScanner
            from docanalyzer.processors import BaseProcessor, TextProcessor, MarkdownProcessor
            
            docanalyzer_components = {
                "lock_manager": "available",
                "directory_scanner": "available", 
                "base_processor": "available",
                "text_processor": "available",
                "markdown_processor": "available"
            }
            
            # Merge with component health information
            for component_name, health_info in component_health.items():
                if component_name in docanalyzer_components:
                    docanalyzer_components[component_name] = health_info.get("status", "available")
                    
        except ImportError as e:
            docanalyzer_components = {
                "error": f"Import error: {str(e)}"
            }
        
        # DocAnalyzer specific metrics from HealthChecker
        docanalyzer_metrics = {
            "service_status": overall_health.get("status", "unknown"),
            "components_loaded": len(docanalyzer_components),
            "supported_file_types": [".txt", ".md", ".py", ".js", ".ts"],
            "processing_capabilities": ["text", "markdown", "python", "javascript"],
            "lock_management": "enabled",
            "directory_scanning": "enabled",
            "file_processing": "enabled",
            "health_metrics": docanalyzer_health.get("metrics", {}),
            "health_status": docanalyzer_health.get("status", "unknown")
        }
        
        components = {
            "system": system_info,
            "process": process_info,
            "docanalyzer": docanalyzer_components,
            "health_checker": component_health
        }
        
        # Determine overall status
        overall_status = "ok"
        if overall_health.get("status") in ["unhealthy", "degraded"]:
            overall_status = "error"
        
        return HealthCheckResult(
            status=overall_status,
            version=version,
            uptime=uptime_seconds,
            components=components,
            docanalyzer_metrics=docanalyzer_metrics
        )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Get JSON schema for command parameters.
        
        Returns:
            Dict[str, Any]: JSON schema
        """
        return {
            "type": "object",
            "properties": {},
            "description": "Get DocAnalyzer health and status information"
        } 