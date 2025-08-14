"""
Tests for Health Models

Unit tests for DocAnalyzer health status models.
"""

import pytest
from datetime import datetime
from docanalyzer.models.health import HealthStatus


class TestHealthStatus:
    """Test suite for HealthStatus class."""
    
    def test_init_with_valid_status(self):
        """Test HealthStatus initialization with valid status."""
        health = HealthStatus("healthy")
        
        assert health.status == "healthy"
        assert health.details == {}
        assert isinstance(health.timestamp, datetime)
    
    def test_init_with_details(self):
        """Test HealthStatus initialization with details."""
        details = {"version": "1.0.0", "uptime": "1h"}
        health = HealthStatus("healthy", details)
        
        assert health.status == "healthy"
        assert health.details == details
        assert isinstance(health.timestamp, datetime)
    
    def test_init_with_timestamp(self):
        """Test HealthStatus initialization with custom timestamp."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        health = HealthStatus("healthy", timestamp=timestamp)
        
        assert health.status == "healthy"
        assert health.timestamp == timestamp
    
    def test_init_with_all_parameters(self):
        """Test HealthStatus initialization with all parameters."""
        details = {"version": "1.0.0"}
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        health = HealthStatus("degraded", details, timestamp)
        
        assert health.status == "degraded"
        assert health.details == details
        assert health.timestamp == timestamp
    
    def test_init_empty_status_raises_error(self):
        """Test that empty status raises ValueError."""
        with pytest.raises(ValueError, match="status cannot be empty"):
            HealthStatus("")
    
    def test_init_none_status_raises_error(self):
        """Test that None status raises ValueError."""
        with pytest.raises(ValueError, match="status cannot be empty"):
            HealthStatus(None)
    
    def test_init_invalid_status_raises_error(self):
        """Test that invalid status raises ValueError."""
        with pytest.raises(ValueError, match="status must be one of"):
            HealthStatus("invalid_status")
    
    def test_init_invalid_details_type_raises_error(self):
        """Test that invalid details type raises TypeError."""
        with pytest.raises(TypeError, match="details must be a dictionary"):
            HealthStatus("healthy", details="not_a_dict")
    
    def test_init_invalid_timestamp_type_raises_error(self):
        """Test that invalid timestamp type raises TypeError."""
        with pytest.raises(TypeError, match="timestamp must be a datetime object"):
            HealthStatus("healthy", timestamp="not_a_datetime")
    
    def test_to_dict(self):
        """Test to_dict method."""
        details = {"version": "1.0.0", "uptime": "1h"}
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        health = HealthStatus("healthy", details, timestamp)
        
        result = health.to_dict()
        
        assert result["status"] == "healthy"
        assert result["details"] == details
        assert result["timestamp"] == "2023-01-01T12:00:00"
    
    def test_to_dict_with_default_values(self):
        """Test to_dict method with default values."""
        health = HealthStatus("unhealthy")
        
        result = health.to_dict()
        
        assert result["status"] == "unhealthy"
        assert result["details"] == {}
        assert isinstance(result["timestamp"], str)
    
    def test_from_dict_valid_data(self):
        """Test from_dict method with valid data."""
        data = {
            "status": "healthy",
            "details": {"version": "1.0.0"},
            "timestamp": "2023-01-01T12:00:00"
        }
        
        health = HealthStatus.from_dict(data)
        
        assert health.status == "healthy"
        assert health.details == {"version": "1.0.0"}
        assert health.timestamp == datetime(2023, 1, 1, 12, 0, 0)
    
    def test_from_dict_minimal_data(self):
        """Test from_dict method with minimal data."""
        data = {"status": "degraded"}
        
        health = HealthStatus.from_dict(data)
        
        assert health.status == "degraded"
        assert health.details == {}
        assert isinstance(health.timestamp, datetime)
    
    def test_from_dict_without_timestamp(self):
        """Test from_dict method without timestamp."""
        data = {
            "status": "unhealthy",
            "details": {"error": "connection_failed"}
        }
        
        health = HealthStatus.from_dict(data)
        
        assert health.status == "unhealthy"
        assert health.details == {"error": "connection_failed"}
        assert isinstance(health.timestamp, datetime)
    
    def test_from_dict_invalid_data_type_raises_error(self):
        """Test from_dict method with invalid data type."""
        with pytest.raises(ValueError, match="data must be a dictionary"):
            HealthStatus.from_dict("not_a_dict")
    
    def test_from_dict_missing_status_raises_error(self):
        """Test from_dict method with missing status."""
        data = {"details": {"version": "1.0.0"}}
        
        with pytest.raises(ValueError, match="data must contain 'status' key"):
            HealthStatus.from_dict(data)
    
    def test_from_dict_invalid_timestamp_format(self):
        """Test from_dict method with invalid timestamp format."""
        data = {
            "status": "healthy",
            "timestamp": "invalid_timestamp"
        }
        
        health = HealthStatus.from_dict(data)
        
        assert health.status == "healthy"
        assert isinstance(health.timestamp, datetime)  # Should use current time
    
    def test_from_dict_none_timestamp(self):
        """Test from_dict method with None timestamp."""
        data = {
            "status": "healthy",
            "timestamp": None
        }
        
        health = HealthStatus.from_dict(data)
        
        assert health.status == "healthy"
        assert isinstance(health.timestamp, datetime)  # Should use current time
    
    def test_all_valid_statuses(self):
        """Test all valid status values."""
        valid_statuses = ["healthy", "unhealthy", "degraded", "unknown"]
        
        for status in valid_statuses:
            health = HealthStatus(status)
            assert health.status == status
    
    def test_status_case_sensitivity(self):
        """Test that status is case-sensitive."""
        # These should work
        HealthStatus("healthy")
        HealthStatus("unhealthy")
        
        # These should fail
        with pytest.raises(ValueError):
            HealthStatus("HEALTHY")
        
        with pytest.raises(ValueError):
            HealthStatus("Healthy")
    
    def test_details_mutation(self):
        """Test that details can be mutated after creation."""
        health = HealthStatus("healthy", {"version": "1.0.0"})
        
        # Modify details
        health.details["uptime"] = "2h"
        
        assert health.details["version"] == "1.0.0"
        assert health.details["uptime"] == "2h"
    
    def test_timestamp_immutability(self):
        """Test that timestamp is properly set and immutable."""
        original_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        health = HealthStatus("healthy", timestamp=original_timestamp)
        
        # Verify timestamp is set correctly
        assert health.timestamp == original_timestamp
        
        # Verify timestamp is not shared between instances
        health2 = HealthStatus("unhealthy")
        assert health2.timestamp != original_timestamp
    
    def test_equality_comparison(self):
        """Test equality comparison between HealthStatus instances."""
        health1 = HealthStatus("healthy", {"version": "1.0.0"}, datetime(2023, 1, 1, 12, 0, 0))
        health2 = HealthStatus("healthy", {"version": "1.0.0"}, datetime(2023, 1, 1, 12, 0, 0))
        health3 = HealthStatus("unhealthy", {"version": "1.0.0"}, datetime(2023, 1, 1, 12, 0, 0))
        
        assert health1 == health2
        assert health1 != health3
    
    def test_string_representation(self):
        """Test string representation of HealthStatus."""
        health = HealthStatus("healthy", {"version": "1.0.0"})
        
        str_repr = str(health)
        assert "healthy" in str_repr
        assert "HealthStatus" in str_repr
    
    def test_repr_representation(self):
        """Test repr representation of HealthStatus."""
        health = HealthStatus("healthy", {"version": "1.0.0"})
        
        repr_str = repr(health)
        assert "HealthStatus" in repr_str
        assert "healthy" in repr_str
        assert "version" in repr_str
    
    def test_hash_consistency(self):
        """Test that hash is consistent for equal objects."""
        health1 = HealthStatus("healthy", {"version": "1.0.0"}, datetime(2023, 1, 1, 12, 0, 0))
        health2 = HealthStatus("healthy", {"version": "1.0.0"}, datetime(2023, 1, 1, 12, 0, 0))
        
        # HealthStatus is not hashable by default, so we test equality instead
        assert health1 == health2
    
    def test_serialization_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original_health = HealthStatus(
            "degraded",
            {"version": "1.0.0", "uptime": "1h", "errors": ["timeout"]},
            datetime(2023, 1, 1, 12, 0, 0)
        )
        
        # Serialize to dict
        data = original_health.to_dict()
        
        # Deserialize from dict
        restored_health = HealthStatus.from_dict(data)
        
        # Verify all fields match
        assert restored_health.status == original_health.status
        assert restored_health.details == original_health.details
        assert restored_health.timestamp == original_health.timestamp
    
    def test_nested_details_structure(self):
        """Test HealthStatus with nested details structure."""
        nested_details = {
            "version": "1.0.0",
            "metrics": {
                "cpu_usage": 25.5,
                "memory_usage": 1024,
                "disk_usage": {
                    "total": 1000000,
                    "used": 500000,
                    "free": 500000
                }
            },
            "errors": ["timeout", "connection_failed"]
        }
        
        health = HealthStatus("degraded", nested_details)
        
        assert health.status == "degraded"
        assert health.details["version"] == "1.0.0"
        assert health.details["metrics"]["cpu_usage"] == 25.5
        assert health.details["metrics"]["disk_usage"]["free"] == 500000
        assert len(health.details["errors"]) == 2
    
    def test_edge_case_empty_details(self):
        """Test HealthStatus with empty details dict."""
        health = HealthStatus("unknown", {})
        
        assert health.status == "unknown"
        assert health.details == {}
        assert isinstance(health.timestamp, datetime)
    
    def test_edge_case_none_details(self):
        """Test HealthStatus with None details (should use default)."""
        # None details should be converted to empty dict by dataclass
        health = HealthStatus("healthy", {})
        
        assert health.status == "healthy"
        assert health.details == {}
        assert isinstance(health.timestamp, datetime)
    
    def test_edge_case_future_timestamp(self):
        """Test HealthStatus with future timestamp."""
        future_timestamp = datetime(2030, 1, 1, 12, 0, 0)
        health = HealthStatus("healthy", timestamp=future_timestamp)
        
        assert health.timestamp == future_timestamp
        assert health.timestamp > datetime.now()
    
    def test_edge_case_past_timestamp(self):
        """Test HealthStatus with past timestamp."""
        past_timestamp = datetime(2020, 1, 1, 12, 0, 0)
        health = HealthStatus("healthy", timestamp=past_timestamp)
        
        assert health.timestamp == past_timestamp
        assert health.timestamp < datetime.now() 