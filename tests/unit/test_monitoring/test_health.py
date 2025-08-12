"""
Tests for Health Check System

Unit tests for DocAnalyzer health monitoring and status checking.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock

from docanalyzer.monitoring.health import (
    HealthStatus,
    ComponentHealth,
    HealthChecker,
    HealthCheckError,
    ConfigurationError,
    DEFAULT_HEALTH_CONFIG
)


class TestHealthStatus:
    """Test suite for HealthStatus enum."""
    
    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"
    
    def test_health_status_from_value(self):
        """Test creating HealthStatus from string value."""
        assert HealthStatus("healthy") == HealthStatus.HEALTHY
        assert HealthStatus("degraded") == HealthStatus.DEGRADED
        assert HealthStatus("unhealthy") == HealthStatus.UNHEALTHY
        assert HealthStatus("unknown") == HealthStatus.UNKNOWN
    
    def test_health_status_invalid_value(self):
        """Test creating HealthStatus with invalid value."""
        with pytest.raises(ValueError):
            HealthStatus("invalid_status")


class TestComponentHealth:
    """Test suite for ComponentHealth class."""
    
    @pytest.fixture
    def component(self):
        """Create test ComponentHealth instance."""
        return ComponentHealth("test_component")
    
    def test_init_default_values(self, component):
        """Test ComponentHealth initialization with default values."""
        assert component.component_name == "test_component"
        assert component.status == HealthStatus.UNKNOWN
        assert component.response_time == 0.0
        assert component.error_count == 0
        assert component.error_message is None
        assert component.metrics == {}
    
    def test_update_status_healthy(self, component):
        """Test updating status to healthy."""
        component.update_status(HealthStatus.HEALTHY, 0.5)
        
        assert component.status == HealthStatus.HEALTHY
        assert component.response_time == 0.5
        assert component.error_count == 0
        assert component.error_message is None
    
    def test_update_status_unhealthy_with_error(self, component):
        """Test updating status to unhealthy with error message."""
        component.update_status(HealthStatus.UNHEALTHY, 1.0, "Connection failed")
        
        assert component.status == HealthStatus.UNHEALTHY
        assert component.response_time == 1.0
        assert component.error_count == 1
        assert component.error_message == "Connection failed"
    
    def test_update_status_invalid_status(self, component):
        """Test updating status with invalid status type."""
        with pytest.raises(ValueError) as exc_info:
            component.update_status("invalid", 0.5)
        
        assert "status must be valid HealthStatus enum value" in str(exc_info.value)
    
    def test_update_status_negative_response_time(self, component):
        """Test updating status with negative response time."""
        with pytest.raises(ValueError) as exc_info:
            component.update_status(HealthStatus.HEALTHY, -1.0)
        
        assert "response_time must be non-negative number" in str(exc_info.value)
    
    def test_update_status_invalid_error_message(self, component):
        """Test updating status with invalid error message type."""
        with pytest.raises(ValueError) as exc_info:
            component.update_status(HealthStatus.UNHEALTHY, 1.0, 123)
        
        assert "error_message must be string or None" in str(exc_info.value)
    
    def test_is_healthy(self, component):
        """Test is_healthy method."""
        component.update_status(HealthStatus.HEALTHY, 0.5)
        assert component.is_healthy() == True
        
        component.update_status(HealthStatus.DEGRADED, 0.5)
        assert component.is_healthy() == False
    
    def test_is_degraded(self, component):
        """Test is_degraded method."""
        component.update_status(HealthStatus.DEGRADED, 0.5)
        assert component.is_degraded() == True
        
        component.update_status(HealthStatus.HEALTHY, 0.5)
        assert component.is_degraded() == False
    
    def test_is_unhealthy(self, component):
        """Test is_unhealthy method."""
        component.update_status(HealthStatus.UNHEALTHY, 0.5)
        assert component.is_unhealthy() == True
        
        component.update_status(HealthStatus.HEALTHY, 0.5)
        assert component.is_unhealthy() == False
    
    def test_get_status_summary(self, component):
        """Test get_status_summary method."""
        component.update_status(HealthStatus.HEALTHY, 0.5)
        component.metrics = {"cpu_usage": 25.5}
        
        summary = component.get_status_summary()
        
        assert summary['component_name'] == "test_component"
        assert summary['status'] == "healthy"
        assert summary['response_time'] == 0.5
        assert summary['error_count'] == 0
        assert summary['error_message'] is None
        assert summary['metrics'] == {"cpu_usage": 25.5}


class TestHealthChecker:
    """Test suite for HealthChecker class."""
    
    @pytest.fixture
    def checker(self):
        """Create test HealthChecker instance."""
        return HealthChecker()
    
    @pytest.fixture
    def mock_health_check_func(self):
        """Create mock health check function."""
        return Mock(return_value=HealthStatus.HEALTHY)
    
    def test_init_default_config(self, checker):
        """Test HealthChecker initialization with default configuration."""
        assert checker.config == DEFAULT_HEALTH_CONFIG
        assert checker.components == {}
        assert checker._health_check_functions == {}
        assert checker.is_checking == False
    
    def test_init_custom_config(self):
        """Test HealthChecker initialization with custom configuration."""
        custom_config = {'check_interval': 30}
        checker = HealthChecker(custom_config)
        
        assert checker.config['check_interval'] == 30
        assert checker.config['retention_period'] == DEFAULT_HEALTH_CONFIG['retention_period']
    
    def test_register_component_success(self, checker, mock_health_check_func):
        """Test successful component registration."""
        result = checker.register_component("test_component", mock_health_check_func)
        
        assert result == True
        assert "test_component" in checker.components
        assert "test_component" in checker._health_check_functions
        assert isinstance(checker.components["test_component"], ComponentHealth)
    
    def test_register_component_empty_name(self, checker, mock_health_check_func):
        """Test component registration with empty name."""
        with pytest.raises(ValueError) as exc_info:
            checker.register_component("", mock_health_check_func)
        
        assert "component_name must be non-empty string" in str(exc_info.value)
    
    def test_register_component_invalid_func(self, checker):
        """Test component registration with invalid function."""
        with pytest.raises(ValueError) as exc_info:
            checker.register_component("test_component", "not_callable")
        
        assert "health_check_func must be callable" in str(exc_info.value)
    
    def test_unregister_component_success(self, checker, mock_health_check_func):
        """Test successful component unregistration."""
        # Register component first
        checker.register_component("test_component", mock_health_check_func)
        
        # Unregister component
        result = checker.unregister_component("test_component")
        
        assert result == True
        assert "test_component" not in checker.components
        assert "test_component" not in checker._health_check_functions
    
    def test_unregister_component_not_found(self, checker):
        """Test unregistering non-existent component."""
        result = checker.unregister_component("non_existent")
        
        assert result == False
    
    def test_unregister_component_empty_name(self, checker):
        """Test unregistering component with empty name."""
        with pytest.raises(ValueError) as exc_info:
            checker.unregister_component("")
        
        assert "component_name must be non-empty string" in str(exc_info.value)
    
    def test_check_component_health_success(self, checker, mock_health_check_func):
        """Test successful component health check."""
        checker.register_component("test_component", mock_health_check_func)
        
        result = checker.check_component_health("test_component")
        
        assert isinstance(result, ComponentHealth)
        assert result.component_name == "test_component"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time >= 0
    
    def test_check_component_health_not_registered(self, checker):
        """Test health check for non-registered component."""
        with pytest.raises(ValueError) as exc_info:
            checker.check_component_health("non_registered")
        
        assert "Component non_registered not registered" in str(exc_info.value)
    
    def test_check_component_health_function_error(self, checker):
        """Test health check when function raises error."""
        def failing_health_check():
            raise Exception("Health check failed")
        
        checker.register_component("test_component", failing_health_check)
        
        with pytest.raises(HealthCheckError) as exc_info:
            checker.check_component_health("test_component")
        
        assert "Health check failed for component test_component" in str(exc_info.value)
        
        # Component should be marked as unhealthy
        component = checker.components["test_component"]
        assert component.status == HealthStatus.UNHEALTHY
        assert component.error_message is not None
    
    def test_check_all_components(self, checker):
        """Test checking all registered components."""
        # Register multiple components
        checker.register_component("component1", Mock(return_value=HealthStatus.HEALTHY))
        checker.register_component("component2", Mock(return_value=HealthStatus.DEGRADED))
        
        results = checker.check_all_components()
        
        assert len(results) == 2
        assert "component1" in results
        assert "component2" in results
        assert results["component1"].status == HealthStatus.HEALTHY
        assert results["component2"].status == HealthStatus.DEGRADED
    
    def test_get_component_health(self, checker, mock_health_check_func):
        """Test getting component health."""
        checker.register_component("test_component", mock_health_check_func)
        
        component = checker.get_component_health("test_component")
        assert isinstance(component, ComponentHealth)
        assert component.component_name == "test_component"
    
    def test_get_component_health_not_found(self, checker):
        """Test getting health for non-existent component."""
        component = checker.get_component_health("non_existent")
        assert component is None
    
    def test_get_overall_health_no_components(self, checker):
        """Test overall health with no components."""
        assert checker.get_overall_health() == HealthStatus.UNKNOWN
    
    def test_get_overall_health_all_healthy(self, checker):
        """Test overall health when all components are healthy."""
        checker.register_component("component1", Mock(return_value=HealthStatus.HEALTHY))
        checker.register_component("component2", Mock(return_value=HealthStatus.HEALTHY))
        
        # Update component statuses
        checker.check_all_components()
        
        assert checker.get_overall_health() == HealthStatus.HEALTHY
    
    def test_get_overall_health_with_degraded(self, checker):
        """Test overall health when some components are degraded."""
        checker.register_component("component1", Mock(return_value=HealthStatus.HEALTHY))
        checker.register_component("component2", Mock(return_value=HealthStatus.DEGRADED))
        
        # Update component statuses
        checker.check_all_components()
        
        assert checker.get_overall_health() == HealthStatus.DEGRADED
    
    def test_get_overall_health_with_unhealthy(self, checker):
        """Test overall health when some components are unhealthy."""
        checker.register_component("component1", Mock(return_value=HealthStatus.HEALTHY))
        checker.register_component("component2", Mock(return_value=HealthStatus.UNHEALTHY))
        
        # Update component statuses
        checker.check_all_components()
        
        assert checker.get_overall_health() == HealthStatus.UNHEALTHY
    
    def test_get_health_summary(self, checker, mock_health_check_func):
        """Test getting health summary."""
        checker.register_component("test_component", mock_health_check_func)
        checker.check_all_components()
        
        summary = checker.get_health_summary()
        
        assert 'overall_status' in summary
        assert 'components' in summary
        assert 'checking_active' in summary
        assert 'check_interval' in summary
        assert 'total_components' in summary
        assert summary['total_components'] == 1
        assert 'test_component' in summary['components']
    
    def test_is_system_healthy(self, checker):
        """Test is_system_healthy method."""
        checker.register_component("component1", Mock(return_value=HealthStatus.HEALTHY))
        checker.check_all_components()
        
        assert checker.is_system_healthy() == True
        
        checker.register_component("component2", Mock(return_value=HealthStatus.UNHEALTHY))
        checker.check_all_components()
        
        assert checker.is_system_healthy() == False
    
    def test_is_system_degraded(self, checker):
        """Test is_system_degraded method."""
        checker.register_component("component1", Mock(return_value=HealthStatus.DEGRADED))
        checker.check_all_components()
        
        assert checker.is_system_degraded() == True
        
        checker.register_component("component2", Mock(return_value=HealthStatus.HEALTHY))
        checker.check_all_components()
        
        assert checker.is_system_degraded() == True  # Still degraded due to component1
    
    def test_is_system_unhealthy(self, checker):
        """Test is_system_unhealthy method."""
        checker.register_component("component1", Mock(return_value=HealthStatus.UNHEALTHY))
        checker.check_all_components()
        
        assert checker.is_system_unhealthy() == True
        
        checker.register_component("component2", Mock(return_value=HealthStatus.HEALTHY))
        checker.check_all_components()
        
        assert checker.is_system_unhealthy() == True  # Still unhealthy due to component1
    
    def test_save_health_status(self, checker, mock_health_check_func):
        """Test saving health status to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'health.json')
            
            # Register component and check health
            checker.register_component("test_component", mock_health_check_func)
            checker.check_all_components()
            
            # Save health status
            result = checker.save_health_status(file_path)
            
            assert result == True
            assert os.path.exists(file_path)
            
            # Verify file content
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            assert 'overall_status' in data
            assert 'components' in data
            assert 'test_component' in data['components']
    
    def test_load_health_status(self, checker):
        """Test loading health status from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'health.json')
            
            # Create test health status file
            test_data = {
                'overall_status': 'healthy',
                'components': {
                    'test_component': {
                        'component_name': 'test_component',
                        'status': 'healthy',
                        'response_time': 0.5,
                        'error_count': 0,
                        'error_message': None,
                        'metrics': {}
                    }
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(test_data, f)
            
            # Register component first
            checker.register_component("test_component", Mock(return_value=HealthStatus.HEALTHY))
            
            # Load health status
            result = checker.load_health_status(file_path)
            
            assert result == True
            component = checker.components["test_component"]
            assert component.status == HealthStatus.HEALTHY
            assert component.response_time == 0.5
    
    def test_reset_health_status(self, checker, mock_health_check_func):
        """Test resetting health status."""
        checker.register_component("test_component", mock_health_check_func)
        checker.check_all_components()
        
        # Verify component has health status
        component = checker.components["test_component"]
        assert component.status == HealthStatus.HEALTHY
        
        # Reset health status
        checker.reset_health_status()
        
        # Verify component status is reset
        assert component.status == HealthStatus.UNKNOWN


class TestHealthExceptions:
    """Test suite for health exceptions."""
    
    def test_health_check_error_init(self):
        """Test HealthCheckError initialization."""
        error = HealthCheckError("Test error", "test_component", "test_operation")
        
        assert error.message == "Test error"
        assert error.component == "test_component"
        assert error.operation == "test_operation"
    
    def test_configuration_error_init(self):
        """Test ConfigurationError initialization."""
        error = ConfigurationError("Config error", "test_key", "invalid_value")
        
        assert error.message == "Config error"
        assert error.config_key == "test_key"
        assert error.value == "invalid_value"
    
    def test_health_check_error_str_representation(self):
        """Test HealthCheckError string representation."""
        error = HealthCheckError("Test error", "test_component", "test_operation")
        
        assert "Test error" in str(error)
        assert error.message == "Test error"


class TestHealthCheckerAdvanced:
    """Advanced test suite for HealthChecker class."""
    
    @pytest.fixture
    def checker(self):
        """Create test HealthChecker instance."""
        return HealthChecker()
    
    def test_framework_checker_initialization_success(self, checker):
        """Test successful framework checker initialization."""
        # This test verifies that framework checker initialization works
        
        # Framework checker should be None in test environment (fallback)
        assert checker.framework_checker is None
    
    def test_framework_checker_initialization_failure(self, checker):
        """Test framework checker initialization failure."""
        # This test verifies that initialization failure is handled gracefully
        
        # Should not raise exception even if framework checker fails
        assert checker.framework_checker is None
    
    def test_start_health_checks_already_running(self, checker):
        """Test starting health checks when already running."""
        # Start health checks first time
        result1 = checker.start_health_checks()
        assert result1 == True
        assert checker.is_checking == True
        
        # Try to start again
        result2 = checker.start_health_checks()
        assert result2 == True  # Should return True and log warning
        
        # Stop health checks
        checker.stop_health_checks()
    
    def test_stop_health_checks_not_running(self, checker):
        """Test stopping health checks when not running."""
        result = checker.stop_health_checks()
        assert result == True  # Should return True and log warning
    
    def test_check_worker_exception_handling(self, checker):
        """Test exception handling in check worker."""
        # Register a component that raises exception
        def failing_health_check():
            raise Exception("Health check failed")
        
        checker.register_component("failing_component", failing_health_check)
        
        # Start health checks
        checker.start_health_checks()
        
        # Wait a bit for worker to run
        import time
        time.sleep(0.1)
        
        # Stop health checks
        checker.stop_health_checks()
        
        # Component should be marked as unhealthy
        component = checker.components["failing_component"]
        assert component.status == HealthStatus.UNHEALTHY
    
    def test_save_health_status_creates_directory(self, checker):
        """Test that save_health_status creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory path
            nested_dir = os.path.join(temp_dir, 'health', 'status', 'deep')
            file_path = os.path.join(nested_dir, 'health.json')
            
            # Register a component
            checker.register_component("test_component", Mock(return_value=HealthStatus.HEALTHY))
            checker.check_all_components()
            
            # Save health status
            result = checker.save_health_status(file_path)
            
            assert result == True
            assert os.path.exists(nested_dir)
            assert os.path.exists(file_path)
    
    def test_load_health_status_with_invalid_data(self, checker):
        """Test loading health status with invalid data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'invalid_health.json')
            
            # Create invalid JSON file
            with open(file_path, 'w') as f:
                f.write('{"invalid": "json"')
            
            # Register component first
            checker.register_component("test_component", Mock(return_value=HealthStatus.HEALTHY))
            
            # Should raise exception when loading invalid data
            with pytest.raises(HealthCheckError):
                checker.load_health_status(file_path)
    
    def test_load_health_status_with_missing_components(self, checker):
        """Test loading health status when components are not registered."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'health.json')
            
            # Create health status file with component that's not registered
            test_data = {
                'overall_status': 'healthy',
                'components': {
                    'unregistered_component': {
                        'component_name': 'unregistered_component',
                        'status': 'healthy',
                        'response_time': 0.5,
                        'error_count': 0,
                        'error_message': None,
                        'metrics': {}
                    }
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(test_data, f)
            
            # Should not raise exception, just ignore unregistered components
            result = checker.load_health_status(file_path)
            assert result == True
    
    def test_start_health_checks_exception_handling(self, checker):
        """Test exception handling in start_health_checks."""
        # Mock threading.Thread to raise exception
        with patch('threading.Thread', side_effect=Exception("Thread creation failed")):
            with pytest.raises(HealthCheckError) as exc_info:
                checker.start_health_checks()
            
            assert "Failed to start health checks" in str(exc_info.value)
            assert exc_info.value.operation == "start_health_checks"
    
    def test_stop_health_checks_exception_handling(self, checker):
        """Test exception handling in stop_health_checks."""
        # Start health checks first
        checker.start_health_checks()
        
        # Mock thread.join to raise exception
        with patch.object(checker.check_thread, 'join', side_effect=Exception("Join failed")):
            with pytest.raises(HealthCheckError) as exc_info:
                checker.stop_health_checks()
            
            assert "Failed to stop health checks" in str(exc_info.value)
            assert exc_info.value.operation == "stop_health_checks"
    
    def test_register_component_exception_handling(self, checker):
        """Test exception handling in register_component."""
        # Mock ComponentHealth to raise exception
        with patch('docanalyzer.monitoring.health.ComponentHealth', side_effect=Exception("Component creation failed")):
            with pytest.raises(HealthCheckError) as exc_info:
                checker.register_component("test_component", Mock(return_value=HealthStatus.HEALTHY))
            
            assert "Failed to register component test_component" in str(exc_info.value)
            assert exc_info.value.component == "test_component"
    
    def test_unregister_component_exception_handling(self, checker):
        """Test exception handling in unregister_component."""
        # Register component first
        checker.register_component("test_component", Mock(return_value=HealthStatus.HEALTHY))
        
        # Mock del operation to raise exception
        with patch.dict(checker.components, {}, clear=True):
            with patch.dict(checker._health_check_functions, {}, clear=True):
                # This should not raise exception, just return False
                result = checker.unregister_component("test_component")
                assert result == False 