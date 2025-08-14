"""
System Stats Command for DocAnalyzer

Command that returns detailed system statistics and performance metrics.
"""

import os
import platform
import sys
import psutil
from datetime import datetime
from typing import Dict, Any, List

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import CommandResult


class SystemStatsResult(CommandResult):
    """
    Result of the system stats command execution.
    """
    
    def __init__(self, system_stats: Dict[str, Any], performance_metrics: Dict[str, Any],
                 docanalyzer_stats: Dict[str, Any], timestamp: str):
        """
        Initialize system stats command result.
        
        Args:
            system_stats: System statistics
            performance_metrics: Performance metrics
            docanalyzer_stats: DocAnalyzer specific statistics
            timestamp: Timestamp of stats collection
        """
        self.system_stats = system_stats
        self.performance_metrics = performance_metrics
        self.docanalyzer_stats = docanalyzer_stats
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.
        
        Returns:
            Dict[str, Any]: Result as dictionary
        """
        return {
            "system_stats": self.system_stats,
            "performance_metrics": self.performance_metrics,
            "docanalyzer_stats": self.docanalyzer_stats,
            "timestamp": self.timestamp,
            "command_type": "system_stats"
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
                "system_stats": {"type": "object"},
                "performance_metrics": {"type": "object"},
                "docanalyzer_stats": {"type": "object"},
                "timestamp": {"type": "string"},
                "command_type": {"type": "string"}
            },
            "required": ["system_stats", "performance_metrics", "docanalyzer_stats", "timestamp", "command_type"]
        }


class SystemStatsCommand(Command):
    """
    System stats command for DocAnalyzer.
    """
    
    name = "system_stats"
    result_class = SystemStatsResult
    
    async def execute(self, detailed: bool = False, **kwargs) -> SystemStatsResult:
        """
        Execute system stats command.
        
        Args:
            detailed: Whether to include detailed statistics
            **kwargs: Additional parameters
            
        Returns:
            SystemStatsResult: System stats command result
        """
        # System statistics
        system_stats = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "python": {
                "version": sys.version,
                "version_info": {
                    "major": sys.version_info.major,
                    "minor": sys.version_info.minor,
                    "micro": sys.version_info.micro
                },
                "executable": sys.executable,
                "path": sys.path[:5] if not detailed else sys.path  # Limit path length
            },
            "cpu": {
                "count": psutil.cpu_count(),
                "count_logical": psutil.cpu_count(logical=True),
                "percent": psutil.cpu_percent(interval=1),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "used": psutil.virtual_memory().used,
                "percent": psutil.virtual_memory().percent,
                "free": psutil.virtual_memory().free
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
            }
        }
        
        # Performance metrics
        process = psutil.Process(os.getpid())
        performance_metrics = {
            "process": {
                "pid": process.pid,
                "name": process.name(),
                "memory_info": {
                    "rss": process.memory_info().rss,
                    "vms": process.memory_info().vms,
                    "percent": process.memory_percent()
                },
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": process.create_time(),
                "status": process.status()
            },
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
            "network": {
                "connections": len(process.net_connections()),
                "interfaces": len(psutil.net_if_addrs())
            }
        }
        
        # DocAnalyzer specific statistics
        docanalyzer_stats = {
            "components": {
                "lock_manager": "available",
                "directory_scanner": "available",
                "processors": ["text", "markdown"],
                "filters": "available"
            },
            "capabilities": {
                "supported_formats": [".txt", ".md", ".py", ".js", ".ts"],
                "processing_modes": ["sync", "async"],
                "lock_management": True,
                "file_filtering": True
            },
            "status": {
                "service_running": True,
                "components_loaded": 5,
                "last_check": datetime.now().isoformat()
            }
        }
        
        # Add detailed stats if requested
        if detailed:
            try:
                # Add more detailed DocAnalyzer stats
                from docanalyzer.services import LockManager, DirectoryScanner
                from docanalyzer.processors import BaseProcessor, TextProcessor, MarkdownProcessor
                
                docanalyzer_stats["detailed"] = {
                    "lock_manager_class": LockManager.__name__,
                    "directory_scanner_class": DirectoryScanner.__name__,
                    "processor_classes": [
                        BaseProcessor.__name__,
                        TextProcessor.__name__,
                        MarkdownProcessor.__name__
                    ]
                }
            except ImportError:
                docanalyzer_stats["detailed"] = {"error": "Components not available"}
        
        return SystemStatsResult(
            system_stats=system_stats,
            performance_metrics=performance_metrics,
            docanalyzer_stats=docanalyzer_stats,
            timestamp=datetime.now().isoformat()
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
            "properties": {
                "detailed": {
                    "type": "boolean",
                    "description": "Include detailed statistics",
                    "default": False
                }
            },
            "description": "Get detailed system statistics and performance metrics"
        } 