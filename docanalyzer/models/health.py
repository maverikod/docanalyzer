"""
Health Models - DocAnalyzer Health Status Models

This module provides health status models for DocAnalyzer services,
including HealthStatus class for representing health information.

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class HealthStatus:
    """
    Health Status - Service Health Information
    
    Represents the health status of a service with status,
    details, and timestamp information.
    
    Attributes:
        status (str): Health status string.
            Values: "healthy", "unhealthy", "degraded", "unknown".
        details (Dict[str, Any]): Additional health details.
            Can contain version, uptime, and other metrics.
        timestamp (datetime): Timestamp when health was checked.
            Used for determining freshness of health data.
    
    Example:
        >>> health = HealthStatus(
        ...     status="healthy",
        ...     details={"version": "1.0.0", "uptime": "1h"},
        ...     timestamp=datetime.now()
        ... )
        >>> print(health.status)  # "healthy"
    """
    
    status: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate health status after initialization."""
        if not self.status:
            raise ValueError("status cannot be empty")
        
        valid_statuses = ["healthy", "unhealthy", "degraded", "unknown"]
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of: {valid_statuses}")
        
        if not isinstance(self.details, dict):
            raise TypeError("details must be a dictionary")
        
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime object")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert health status to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of health status.
        """
        return {
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthStatus':
        """
        Create HealthStatus from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with health status data.
                Must contain 'status' key.
        
        Returns:
            HealthStatus: Created health status instance.
        
        Raises:
            ValueError: If required data is missing or invalid.
        """
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        
        if "status" not in data:
            raise ValueError("data must contain 'status' key")
        
        status = data["status"]
        details = data.get("details", {})
        timestamp_str = data.get("timestamp")
        
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        return cls(status=status, details=details, timestamp=timestamp) 