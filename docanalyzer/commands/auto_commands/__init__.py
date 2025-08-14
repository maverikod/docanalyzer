"""
Auto Commands for DocAnalyzer

Commands that are automatically discovered and registered by the framework.
"""

from .health_check_command import HealthCheckCommand, HealthCheckResult
from .system_stats_command import SystemStatsCommand, SystemStatsResult
from .processing_stats_command import ProcessingStatsCommand, ProcessingStatsResult
from .queue_status_command import QueueStatusCommand, QueueStatusResult

__all__ = [
    # Health and monitoring commands
    "HealthCheckCommand",
    "HealthCheckResult",
    "SystemStatsCommand", 
    "SystemStatsResult",
    "ProcessingStatsCommand",
    "ProcessingStatsResult",
    "QueueStatusCommand",
    "QueueStatusResult"
] 