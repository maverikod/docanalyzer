"""
Commands package for DocAnalyzer

All commands for the DocAnalyzer system.
"""

from .auto_commands import (
    HealthCheckCommand,
    HealthCheckResult,
    SystemStatsCommand,
    SystemStatsResult,
    ProcessingStatsCommand,
    ProcessingStatsResult,
    QueueStatusCommand,
    QueueStatusResult
)

__all__ = [
    # Auto commands
    "HealthCheckCommand",
    "HealthCheckResult", 
    "SystemStatsCommand",
    "SystemStatsResult",
    "ProcessingStatsCommand",
    "ProcessingStatsResult",
    "QueueStatusCommand",
    "QueueStatusResult"
] 