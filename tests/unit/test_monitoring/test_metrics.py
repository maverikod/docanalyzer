"""
Tests for Metrics System

Unit tests for DocAnalyzer metrics collection and monitoring.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock

from docanalyzer.monitoring.metrics import (
    ProcessingMetrics,
    SystemMetrics,
    MetricsCollector,
    MetricsError,
    SystemMetricsError,
    DEFAULT_METRICS_CONFIG
)


class TestProcessingMetrics:
    """Test suite for ProcessingMetrics class."""
    
    @pytest.fixture
    def metrics(self):
        """Create test ProcessingMetrics instance."""
        return ProcessingMetrics()
    
    def test_init_default_values(self, metrics):
        """Test ProcessingMetrics initialization with default values."""
        assert metrics.files_processed == 0
        assert metrics.files_failed == 0
        assert metrics.processing_time_total == 0.0
        assert metrics.processing_time_avg == 0.0
        assert metrics.chunks_created == 0
        assert metrics.bytes_processed == 0
        assert metrics.last_processed_file is None
        assert metrics.processing_errors == {}
    
    def test_record_file_processed_success(self, metrics):
        """Test successful file processing recording."""
        metrics.record_file_processed("/test/file.txt", 1024, 1.5)
        
        assert metrics.files_processed == 1
        assert metrics.processing_time_total == 1.5
        assert metrics.bytes_processed == 1024
        assert metrics.last_processed_file == "/test/file.txt"
        assert metrics.processing_time_avg == 1.5
    
    def test_record_file_processed_multiple(self, metrics):
        """Test recording multiple file processing."""
        metrics.record_file_processed("/test/file1.txt", 512, 1.0)
        metrics.record_file_processed("/test/file2.txt", 1024, 2.0)
        
        assert metrics.files_processed == 2
        assert metrics.processing_time_total == 3.0
        assert metrics.bytes_processed == 1536
        assert metrics.processing_time_avg == 1.5
    
    def test_record_file_processed_empty_path(self, metrics):
        """Test recording with empty file path."""
        with pytest.raises(ValueError) as exc_info:
            metrics.record_file_processed("", 1024, 1.5)
        
        assert "file_path must be non-empty string" in str(exc_info.value)
    
    def test_record_file_processed_invalid_size(self, metrics):
        """Test recording with invalid file size."""
        with pytest.raises(ValueError) as exc_info:
            metrics.record_file_processed("/test/file.txt", -1, 1.5)
        
        assert "file_size must be non-negative integer" in str(exc_info.value)
    
    def test_record_file_processed_invalid_time(self, metrics):
        """Test recording with invalid processing time."""
        with pytest.raises(ValueError) as exc_info:
            metrics.record_file_processed("/test/file.txt", 1024, -1.0)
        
        assert "processing_time must be non-negative number" in str(exc_info.value)
    
    def test_record_file_failed_success(self, metrics):
        """Test successful file failure recording."""
        metrics.record_file_failed("/test/file.txt", "FileNotFoundError")
        
        assert metrics.files_failed == 1
        assert metrics.processing_errors["FileNotFoundError"] == 1
    
    def test_record_file_failed_multiple_errors(self, metrics):
        """Test recording multiple file failures with different error types."""
        metrics.record_file_failed("/test/file1.txt", "FileNotFoundError")
        metrics.record_file_failed("/test/file2.txt", "PermissionError")
        metrics.record_file_failed("/test/file3.txt", "FileNotFoundError")
        
        assert metrics.files_failed == 3
        assert metrics.processing_errors["FileNotFoundError"] == 2
        assert metrics.processing_errors["PermissionError"] == 1
    
    def test_record_file_failed_empty_path(self, metrics):
        """Test recording failure with empty file path."""
        with pytest.raises(ValueError) as exc_info:
            metrics.record_file_failed("", "FileNotFoundError")
        
        assert "file_path must be non-empty string" in str(exc_info.value)
    
    def test_record_file_failed_empty_error_type(self, metrics):
        """Test recording failure with empty error type."""
        with pytest.raises(ValueError) as exc_info:
            metrics.record_file_failed("/test/file.txt", "")
        
        assert "error_type must be non-empty string" in str(exc_info.value)
    
    def test_record_chunks_created_success(self, metrics):
        """Test successful chunks creation recording."""
        metrics.record_chunks_created(5)
        
        assert metrics.chunks_created == 5
    
    def test_record_chunks_created_multiple(self, metrics):
        """Test recording multiple chunks creation."""
        metrics.record_chunks_created(3)
        metrics.record_chunks_created(7)
        
        assert metrics.chunks_created == 10
    
    def test_record_chunks_created_negative(self, metrics):
        """Test recording chunks with negative count."""
        with pytest.raises(ValueError) as exc_info:
            metrics.record_chunks_created(-1)
        
        assert "chunk_count must be non-negative integer" in str(exc_info.value)
    
    def test_get_processing_rate_no_files(self, metrics):
        """Test processing rate calculation with no files."""
        assert metrics.get_processing_rate() == 0.0
    
    def test_get_processing_rate_with_files(self, metrics):
        """Test processing rate calculation with files."""
        metrics.record_file_processed("/test/file.txt", 1024, 60.0)  # 1 minute
        
        rate = metrics.get_processing_rate()
        assert rate == 1.0  # 1 file per minute
    
    def test_get_error_rate_no_files(self, metrics):
        """Test error rate calculation with no files."""
        assert metrics.get_error_rate() == 0.0
    
    def test_get_error_rate_with_files(self, metrics):
        """Test error rate calculation with files."""
        metrics.record_file_processed("/test/file1.txt", 1024, 1.0)
        metrics.record_file_processed("/test/file2.txt", 1024, 1.0)
        metrics.record_file_failed("/test/file3.txt", "FileNotFoundError")
        
        error_rate = metrics.get_error_rate()
        assert error_rate == 33.33333333333333  # 1 failed out of 3 total
    
    def test_reset(self, metrics):
        """Test metrics reset."""
        # Add some data
        metrics.record_file_processed("/test/file.txt", 1024, 1.5)
        metrics.record_file_failed("/test/file2.txt", "FileNotFoundError")
        metrics.record_chunks_created(5)
        
        # Reset
        metrics.reset()
        
        # Check all values are reset
        assert metrics.files_processed == 0
        assert metrics.files_failed == 0
        assert metrics.processing_time_total == 0.0
        assert metrics.processing_time_avg == 0.0
        assert metrics.chunks_created == 0
        assert metrics.bytes_processed == 0
        assert metrics.last_processed_file is None
        assert metrics.processing_errors == {}


class TestSystemMetrics:
    """Test suite for SystemMetrics class."""
    
    @pytest.fixture
    def metrics(self):
        """Create test SystemMetrics instance."""
        return SystemMetrics()
    
    @patch('docanalyzer.monitoring.metrics.psutil')
    def test_update_system_stats_success(self, mock_psutil, metrics):
        """Test successful system stats update."""
        # Mock psutil responses
        mock_memory = Mock()
        mock_memory.used = 1024 * 1024 * 512  # 512MB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.disk_usage.return_value = Mock(used=500, total=1000)
        mock_psutil.boot_time.return_value = 1000000
        
        with patch('time.time', return_value=1000060):  # 60 seconds after boot
            metrics.update_system_stats()
        
        assert metrics.memory_usage == 512.0
        assert metrics.cpu_usage == 25.5
        assert metrics.disk_usage == 50.0
        assert metrics.uptime_seconds == 60.0
    
    @patch('docanalyzer.monitoring.metrics.psutil')
    def test_update_system_stats_psutil_error(self, mock_psutil, metrics):
        """Test system stats update with psutil error."""
        mock_psutil.virtual_memory.side_effect = Exception("psutil error")
        
        with pytest.raises(SystemMetricsError) as exc_info:
            metrics.update_system_stats()
        
        assert "Failed to update system stats" in str(exc_info.value)
        assert exc_info.value.resource == "system_stats"
    
    def test_get_memory_usage_mb(self, metrics):
        """Test memory usage getter."""
        metrics.memory_usage = 1024.5
        assert metrics.get_memory_usage_mb() == 1024.5
    
    def test_get_cpu_usage_percent(self, metrics):
        """Test CPU usage getter."""
        metrics.cpu_usage = 75.2
        assert metrics.get_cpu_usage_percent() == 75.2
    
    def test_get_disk_usage_percent(self, metrics):
        """Test disk usage getter."""
        metrics.disk_usage = 85.7
        assert metrics.get_disk_usage_percent() == 85.7
    
    def test_get_uptime_hours(self, metrics):
        """Test uptime getter."""
        metrics.uptime_seconds = 7200  # 2 hours
        assert metrics.get_uptime_hours() == 2.0


class TestMetricsCollector:
    """Test suite for MetricsCollector class."""
    
    @pytest.fixture
    def collector(self):
        """Create test MetricsCollector instance."""
        return MetricsCollector()
    
    def test_init_default_config(self, collector):
        """Test MetricsCollector initialization with default configuration."""
        assert collector.config == DEFAULT_METRICS_CONFIG
        assert isinstance(collector.processing_metrics, ProcessingMetrics)
        assert isinstance(collector.system_metrics, SystemMetrics)
        assert collector.is_collecting == False
    
    def test_init_custom_config(self):
        """Test MetricsCollector initialization with custom configuration."""
        custom_config = {'collection_interval': 30}
        collector = MetricsCollector(custom_config)
        
        assert collector.config['collection_interval'] == 30
        assert collector.config['retention_period'] == DEFAULT_METRICS_CONFIG['retention_period']
    
    def test_record_file_processed(self, collector):
        """Test recording file processed through collector."""
        collector.record_file_processed("/test/file.txt", 1024, 1.5)
        
        assert collector.processing_metrics.files_processed == 1
        assert collector.processing_metrics.processing_time_total == 1.5
    
    def test_record_file_failed(self, collector):
        """Test recording file failed through collector."""
        collector.record_file_failed("/test/file.txt", "FileNotFoundError")
        
        assert collector.processing_metrics.files_failed == 1
        assert collector.processing_metrics.processing_errors["FileNotFoundError"] == 1
    
    def test_record_chunks_created(self, collector):
        """Test recording chunks created through collector."""
        collector.record_chunks_created(5)
        
        assert collector.processing_metrics.chunks_created == 5
    
    @patch('docanalyzer.monitoring.metrics.psutil')
    def test_update_system_metrics(self, mock_psutil, collector):
        """Test system metrics update through collector."""
        # Mock psutil responses
        mock_memory = Mock()
        mock_memory.used = 1024 * 1024 * 256  # 256MB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 15.0
        mock_psutil.disk_usage.return_value = Mock(used=300, total=1000)
        mock_psutil.boot_time.return_value = 1000000
        
        with patch('time.time', return_value=1000030):  # 30 seconds after boot
            collector.update_system_metrics()
        
        assert collector.system_metrics.memory_usage == 256.0
        assert collector.system_metrics.cpu_usage == 15.0
    
    def test_get_metrics_summary(self, collector):
        """Test getting metrics summary."""
        # Add some data
        collector.record_file_processed("/test/file.txt", 1024, 1.5)
        collector.record_file_failed("/test/file2.txt", "FileNotFoundError")
        collector.record_chunks_created(3)
        
        summary = collector.get_metrics_summary()
        
        assert 'processing' in summary
        assert 'system' in summary
        assert 'collection' in summary
        assert summary['processing']['files_processed'] == 1
        assert summary['processing']['files_failed'] == 1
        assert summary['processing']['chunks_created'] == 3
    
    def test_get_processing_metrics(self, collector):
        """Test getting processing metrics."""
        metrics = collector.get_processing_metrics()
        assert isinstance(metrics, ProcessingMetrics)
    
    def test_get_system_metrics(self, collector):
        """Test getting system metrics."""
        metrics = collector.get_system_metrics()
        assert isinstance(metrics, SystemMetrics)
    
    def test_save_metrics(self, collector):
        """Test saving metrics to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'metrics.json')
            
            # Add some data
            collector.record_file_processed("/test/file.txt", 1024, 1.5)
            
            # Save metrics
            result = collector.save_metrics(file_path)
            
            assert result == True
            assert os.path.exists(file_path)
            
            # Verify file content
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            assert 'processing' in data
            assert data['processing']['files_processed'] == 1
    
    def test_load_metrics(self, collector):
        """Test loading metrics from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'metrics.json')
            
            # Create test metrics file
            test_data = {
                'processing': {
                    'files_processed': 5,
                    'files_failed': 2,
                    'processing_time_total': 10.5,
                    'processing_time_avg': 2.1,
                    'chunks_created': 15,
                    'bytes_processed': 5120,
                    'last_processed_file': '/test/file.txt',
                    'processing_errors': {'FileNotFoundError': 2}
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(test_data, f)
            
            # Load metrics
            result = collector.load_metrics(file_path)
            
            assert result == True
            assert collector.processing_metrics.files_processed == 5
            assert collector.processing_metrics.files_failed == 2
            assert collector.processing_metrics.chunks_created == 15
    
    def test_reset_metrics(self, collector):
        """Test resetting all metrics."""
        # Add some data
        collector.record_file_processed("/test/file.txt", 1024, 1.5)
        collector.record_chunks_created(5)
        
        # Reset
        collector.reset_metrics()
        
        # Check all values are reset
        assert collector.processing_metrics.files_processed == 0
        assert collector.processing_metrics.chunks_created == 0


class TestMetricsExceptions:
    """Test suite for metrics exceptions."""
    
    def test_metrics_error_init(self):
        """Test MetricsError initialization."""
        error = MetricsError("Test error", "test_operation", "test_metric")
        
        assert error.message == "Test error"
        assert error.operation == "test_operation"
        assert error.metric_type == "test_metric"
    
    def test_system_metrics_error_init(self):
        """Test SystemMetricsError initialization."""
        error = SystemMetricsError("System error", "memory", "update_stats")
        
        assert error.message == "System error"
        assert error.resource == "memory"
        assert error.operation == "update_stats"
    
    def test_metrics_error_str_representation(self):
        """Test MetricsError string representation."""
        error = MetricsError("Test error", "test_operation", "test_metric")
        
        assert "Test error" in str(error)
        assert error.message == "Test error"


class TestMetricsAdvanced:
    """Advanced test suite for metrics system."""
    
    def test_import_error_fallback_values(self):
        """Test fallback values when mcp_proxy_adapter is not available."""
        # This test verifies that fallback values are properly set
        from docanalyzer.monitoring import metrics
        
        # Verify fallback values are available
        assert hasattr(metrics, 'FrameworkMetricsCollector')
        assert hasattr(metrics, 'MetricType')
        assert hasattr(metrics, 'MetricValue')
        
        # Verify fallback types
        assert metrics.FrameworkMetricsCollector is object
        assert metrics.MetricType is str
        # MetricValue should be a type annotation
        assert hasattr(metrics, 'MetricValue')
    
    def test_metric_types_definition(self):
        """Test metric types definition."""
        from docanalyzer.monitoring import metrics
        
        expected_types = ['COUNTER', 'GAUGE', 'HISTOGRAM', 'SUMMARY']
        for metric_type in expected_types:
            assert metric_type in metrics.METRIC_TYPES
            assert isinstance(metrics.METRIC_TYPES[metric_type], str)
    
    def test_default_metrics_config(self):
        """Test default metrics configuration."""
        from docanalyzer.monitoring import metrics
        
        config = metrics.DEFAULT_METRICS_CONFIG
        
        assert 'collection_interval' in config
        assert 'retention_period' in config
        assert 'max_metrics_count' in config
        assert 'enable_persistence' in config
        assert 'persistence_file' in config
        
        assert isinstance(config['collection_interval'], int)
        assert isinstance(config['retention_period'], int)
        assert isinstance(config['max_metrics_count'], int)
        assert isinstance(config['enable_persistence'], bool)
        assert isinstance(config['persistence_file'], str)
    
    def test_metrics_collector_framework_integration(self):
        """Test metrics collector framework integration."""
        collector = MetricsCollector()
        
        # Framework collector should be None in test environment (fallback)
        assert collector.framework_collector is None
    
    def test_start_collection_already_running(self):
        """Test starting collection when already running."""
        collector = MetricsCollector()
        
        # Start collection first time
        result1 = collector.start_collection()
        assert result1 == True
        assert collector.is_collecting == True
        
        # Try to start again
        result2 = collector.start_collection()
        assert result2 == True  # Should return True and log warning
        
        # Stop collection
        collector.stop_collection()
    
    def test_stop_collection_not_running(self):
        """Test stopping collection when not running."""
        collector = MetricsCollector()
        result = collector.stop_collection()
        assert result == True  # Should return True and log warning
    
    def test_collection_worker_exception_handling(self):
        """Test exception handling in collection worker."""
        collector = MetricsCollector()
        
        # Start collection
        collector.start_collection()
        
        # Wait a bit for worker to run
        import time
        time.sleep(0.1)
        
        # Stop collection
        collector.stop_collection()
        
        # Should not raise exceptions during worker execution
    
    def test_save_metrics_creates_directory(self):
        """Test that save_metrics creates directory if it doesn't exist."""
        collector = MetricsCollector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory path
            nested_dir = os.path.join(temp_dir, 'metrics', 'deep', 'nested')
            file_path = os.path.join(nested_dir, 'metrics.json')
            
            # Add some data
            collector.record_file_processed("/test/file.txt", 1024, 1.5)
            
            # Save metrics
            result = collector.save_metrics(file_path)
            
            assert result == True
            assert os.path.exists(nested_dir)
            assert os.path.exists(file_path)
    
    def test_load_metrics_with_invalid_data(self):
        """Test loading metrics with invalid data."""
        collector = MetricsCollector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'invalid_metrics.json')
            
            # Create invalid JSON file
            with open(file_path, 'w') as f:
                f.write('{"invalid": "json"')
            
            # Should raise exception when loading invalid data
            with pytest.raises(MetricsError):
                collector.load_metrics(file_path)
    
    def test_load_metrics_with_missing_processing_data(self):
        """Test loading metrics when processing data is missing."""
        collector = MetricsCollector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, 'metrics.json')
            
            # Create metrics file without processing data
            test_data = {
                'system': {
                    'memory_usage_mb': 512.0,
                    'cpu_usage_percent': 25.5
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(test_data, f)
            
            # Should not raise exception, just ignore missing processing data
            result = collector.load_metrics(file_path)
            assert result == True
    
    def test_start_collection_exception_handling(self):
        """Test exception handling in start_collection."""
        collector = MetricsCollector()
        
        # Mock threading.Thread to raise exception
        with patch('threading.Thread', side_effect=Exception("Thread creation failed")):
            with pytest.raises(MetricsError) as exc_info:
                collector.start_collection()
            
            assert "Failed to start metrics collection" in str(exc_info.value)
            assert exc_info.value.operation == "start_collection"
    
    def test_stop_collection_exception_handling(self):
        """Test exception handling in stop_collection."""
        collector = MetricsCollector()
        
        # Start collection first
        collector.start_collection()
        
        # Mock thread.join to raise exception
        with patch.object(collector.collection_thread, 'join', side_effect=Exception("Join failed")):
            with pytest.raises(MetricsError) as exc_info:
                collector.stop_collection()
            
            assert "Failed to stop metrics collection" in str(exc_info.value)
            assert exc_info.value.operation == "stop_collection"
    
    def test_record_file_processed_exception_handling(self):
        """Test exception handling in record_file_processed."""
        collector = MetricsCollector()
        
        # Mock processing_metrics.record_file_processed to raise exception
        with patch.object(collector.processing_metrics, 'record_file_processed', side_effect=Exception("Recording failed")):
            with pytest.raises(MetricsError) as exc_info:
                collector.record_file_processed("/test/file.txt", 1024, 1.5)
            
            assert "Failed to record file processed" in str(exc_info.value)
            assert exc_info.value.operation == "record_file_processed"
    
    def test_record_file_failed_exception_handling(self):
        """Test exception handling in record_file_failed."""
        collector = MetricsCollector()
        
        # Mock processing_metrics.record_file_failed to raise exception
        with patch.object(collector.processing_metrics, 'record_file_failed', side_effect=Exception("Recording failed")):
            with pytest.raises(MetricsError) as exc_info:
                collector.record_file_failed("/test/file.txt", "FileNotFoundError")
            
            assert "Failed to record file failed" in str(exc_info.value)
            assert exc_info.value.operation == "record_file_failed"
    
    def test_record_chunks_created_exception_handling(self):
        """Test exception handling in record_chunks_created."""
        collector = MetricsCollector()
        
        # Mock processing_metrics.record_chunks_created to raise exception
        with patch.object(collector.processing_metrics, 'record_chunks_created', side_effect=Exception("Recording failed")):
            with pytest.raises(MetricsError) as exc_info:
                collector.record_chunks_created(5)
            
            assert "Failed to record chunks created" in str(exc_info.value)
            assert exc_info.value.operation == "record_chunks_created"
    
    def test_update_system_metrics_exception_handling(self):
        """Test exception handling in update_system_metrics."""
        collector = MetricsCollector()
        
        # Mock system_metrics.update_system_stats to raise exception
        with patch.object(collector.system_metrics, 'update_system_stats', side_effect=Exception("Update failed")):
            with pytest.raises(MetricsError) as exc_info:
                collector.update_system_metrics()
            
            assert "Failed to update system metrics" in str(exc_info.value)
            assert exc_info.value.operation == "update_system_metrics" 