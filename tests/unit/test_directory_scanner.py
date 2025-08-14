"""
Tests for Directory Scanner Service

Comprehensive test suite for directory scanning functionality.
Tests file discovery, filtering, progress tracking, and metadata extraction.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import os

from docanalyzer.services.directory_scanner import DirectoryScanner, ScanProgress
from docanalyzer.filters.file_filter import FileFilter
from docanalyzer.services.lock_manager import LockManager
from docanalyzer.models.file_system import FileInfo


class TestScanProgress:
    """Test suite for ScanProgress class."""
    
    @pytest.fixture
    def progress(self):
        """Create test progress tracker."""
        return ScanProgress()
    
    def test_init_default_values(self, progress):
        """Test initialization with default values."""
        assert progress.total_files == 0
        assert progress.processed_files == 0
        assert progress.current_directory == ""
        assert progress.status == "scanning"
        assert progress.estimated_completion is None
        assert isinstance(progress.start_time, datetime)
    
    def test_update_processed_files(self, progress):
        """Test updating processed files count."""
        progress.update(processed_files=10)
        assert progress.processed_files == 10
        
        progress.update(processed_files=25)
        assert progress.processed_files == 25
    
    def test_update_total_files(self, progress):
        """Test updating total files count."""
        progress.update(total_files=100)
        assert progress.total_files == 100
        
        progress.update(total_files=200)
        assert progress.total_files == 200
    
    def test_update_current_directory(self, progress):
        """Test updating current directory."""
        progress.update(current_directory="/test/path")
        assert progress.current_directory == "/test/path"
    
    def test_update_status(self, progress):
        """Test updating status."""
        progress.update(status="completed")
        assert progress.status == "completed"
        
        progress.update(status="error")
        assert progress.status == "error"
    
    def test_update_multiple_fields(self, progress):
        """Test updating multiple fields at once."""
        progress.update(
            processed_files=50,
            total_files=100,
            current_directory="/test",
            status="filtering"
        )
        
        assert progress.processed_files == 50
        assert progress.total_files == 100
        assert progress.current_directory == "/test"
        assert progress.status == "filtering"
    
    def test_update_invalid_processed_files(self, progress):
        """Test updating with invalid processed files."""
        with pytest.raises(ValueError, match="processed_files must be non-negative integer"):
            progress.update(processed_files=-1)
        
        with pytest.raises(ValueError, match="processed_files must be non-negative integer"):
            progress.update(processed_files="invalid")
    
    def test_update_invalid_total_files(self, progress):
        """Test updating with invalid total files."""
        with pytest.raises(ValueError, match="total_files must be non-negative integer"):
            progress.update(total_files=-1)
        
        with pytest.raises(ValueError, match="total_files must be non-negative integer"):
            progress.update(total_files="invalid")
    
    def test_update_invalid_current_directory(self, progress):
        """Test updating with invalid current directory."""
        with pytest.raises(TypeError, match="current_directory must be string"):
            progress.update(current_directory=123)
    
    def test_update_invalid_status(self, progress):
        """Test updating with invalid status."""
        with pytest.raises(TypeError, match="status must be string"):
            progress.update(status=123)
    
    def test_get_percentage_zero_total(self, progress):
        """Test percentage calculation with zero total files."""
        assert progress.get_percentage() == 0.0
        
        progress.update(processed_files=10)
        assert progress.get_percentage() == 0.0
    
    def test_get_percentage_with_data(self, progress):
        """Test percentage calculation with data."""
        progress.update(processed_files=25, total_files=100)
        assert progress.get_percentage() == 25.0
        
        progress.update(processed_files=50, total_files=100)
        assert progress.get_percentage() == 50.0
        
        progress.update(processed_files=100, total_files=100)
        assert progress.get_percentage() == 100.0
    
    def test_get_elapsed_time(self, progress):
        """Test elapsed time calculation."""
        # Should be very small initially
        elapsed = progress.get_elapsed_time()
        assert elapsed >= 0.0
        assert elapsed < 1.0  # Should be very small
    
    def test_get_estimated_completion_no_data(self, progress):
        """Test estimated completion with no progress data."""
        assert progress.get_estimated_completion() is None
    
    def test_get_estimated_completion_with_data(self, progress):
        """Test estimated completion with progress data."""
        progress.update(processed_files=50, total_files=100)
        estimated = progress.get_estimated_completion()
        assert estimated is not None
        assert isinstance(estimated, datetime)
        assert estimated > datetime.now()
    
    def test_to_dict(self, progress):
        """Test conversion to dictionary."""
        progress.update(
            processed_files=30,
            total_files=100,
            current_directory="/test/path",
            status="scanning"
        )
        
        data = progress.to_dict()
        
        assert data["total_files"] == 100
        assert data["processed_files"] == 30
        assert data["current_directory"] == "/test/path"
        assert data["status"] == "scanning"
        assert data["percentage"] == 30.0
        assert data["elapsed_time"] >= 0.0
        assert "start_time" in data
        assert "estimated_completion" in data


class TestDirectoryScanner:
    """Test suite for DirectoryScanner class."""
    
    @pytest.fixture
    def file_filter(self):
        """Create test file filter."""
        filter_mock = Mock(spec=FileFilter)
        filter_mock.filter_files.return_value = [
            Mock(should_process=True),
            Mock(should_process=False),
            Mock(should_process=True)
        ]
        return filter_mock
    
    @pytest.fixture
    def lock_manager(self):
        """Create test lock manager."""
        lock_mock = Mock(spec=LockManager)
        lock_mock.create_lock = AsyncMock()
        lock_mock.remove_lock = AsyncMock()
        return lock_mock
    
    @pytest.fixture
    def scanner(self, file_filter, lock_manager):
        """Create test directory scanner."""
        return DirectoryScanner(
            file_filter=file_filter,
            lock_manager=lock_manager,
            max_depth=3,
            batch_size=10,
            timeout=60
        )
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_dir = Path(temp_dir)
            
            # Create subdirectories
            subdir1 = test_dir / "subdir1"
            subdir1.mkdir()
            
            subdir2 = test_dir / "subdir2"
            subdir2.mkdir()
            
            # Create test files
            (test_dir / "file1.txt").write_text("Test content 1")
            (test_dir / "file2.txt").write_text("Test content 2")
            (subdir1 / "file3.txt").write_text("Test content 3")
            (subdir2 / "file4.txt").write_text("Test content 4")
            
            yield temp_dir
    
    def test_init_success(self, file_filter, lock_manager):
        """Test successful initialization."""
        scanner = DirectoryScanner(
            file_filter=file_filter,
            lock_manager=lock_manager,
            max_depth=5,
            batch_size=50,
            timeout=120
        )
        
        assert scanner.file_filter == file_filter
        assert scanner.lock_manager == lock_manager
        assert scanner.max_depth == 5
        assert scanner.batch_size == 50
        assert scanner.timeout == 120
    
    def test_init_invalid_file_filter(self, lock_manager):
        """Test initialization with invalid file filter."""
        with pytest.raises(TypeError, match="file_filter must be FileFilter instance"):
            DirectoryScanner(file_filter="invalid", lock_manager=lock_manager)
    
    def test_init_invalid_lock_manager(self, file_filter):
        """Test initialization with invalid lock manager."""
        with pytest.raises(TypeError, match="lock_manager must be LockManager instance"):
            DirectoryScanner(file_filter=file_filter, lock_manager="invalid")
    
    def test_init_invalid_max_depth(self, file_filter, lock_manager):
        """Test initialization with invalid max depth."""
        with pytest.raises(ValueError, match="max_depth must be positive"):
            DirectoryScanner(file_filter=file_filter, lock_manager=lock_manager, max_depth=0)
        
        with pytest.raises(ValueError, match="max_depth must be positive"):
            DirectoryScanner(file_filter=file_filter, lock_manager=lock_manager, max_depth=-1)
    
    def test_init_invalid_batch_size(self, file_filter, lock_manager):
        """Test initialization with invalid batch size."""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            DirectoryScanner(file_filter=file_filter, lock_manager=lock_manager, batch_size=0)
    
    def test_init_invalid_timeout(self, file_filter, lock_manager):
        """Test initialization with invalid timeout."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            DirectoryScanner(file_filter=file_filter, lock_manager=lock_manager, timeout=0)
    
    @pytest.mark.asyncio
    async def test_scan_directory_success(self, scanner, temp_directory, lock_manager):
        """Test successful directory scanning."""
        # Mock lock creation
        lock_file = Mock()
        lock_manager.create_lock.return_value = lock_file
        
        # Mock file filter to return all files as processable
        scanner.file_filter.filter_files.return_value = [
            Mock(should_process=True) for _ in range(4)
        ]
        
        # Scan directory
        files = await scanner.scan_directory(temp_directory)
        
        # Verify results
        assert len(files) == 4
        assert all(isinstance(f, FileInfo) for f in files)
        
        # Verify lock was created and removed
        lock_manager.create_lock.assert_called_once_with(temp_directory)
        lock_manager.remove_lock.assert_called_once_with(lock_file)
    
    @pytest.mark.asyncio
    async def test_scan_directory_not_found(self, scanner):
        """Test scanning non-existent directory."""
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            await scanner.scan_directory("/nonexistent/directory")
    
    @pytest.mark.asyncio
    async def test_scan_directory_invalid_path(self, scanner):
        """Test scanning with invalid path."""
        with pytest.raises(ValueError, match="directory_path must be non-empty string"):
            await scanner.scan_directory("")
        
        with pytest.raises(ValueError, match="directory_path must be non-empty string"):
            await scanner.scan_directory(None)
    
    @pytest.mark.asyncio
    async def test_scan_directory_path_not_directory(self, scanner):
        """Test scanning path that is not a directory."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Path is not a directory"):
                await scanner.scan_directory(temp_file)
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_scan_directory_lock_failure(self, scanner, temp_directory, lock_manager):
        """Test scanning when lock creation fails."""
        lock_manager.create_lock.side_effect = Exception("Lock failed")
        
        with pytest.raises(Exception, match="Lock failed"):
            await scanner.scan_directory(temp_directory)
    
    @pytest.mark.asyncio
    async def test_scan_directory_with_progress_callback(self, scanner, temp_directory, lock_manager):
        """Test scanning with progress callback."""
        lock_file = Mock()
        lock_manager.create_lock.return_value = lock_file
        
        scanner.file_filter.filter_files.return_value = [
            Mock(should_process=True) for _ in range(4)
        ]
        
        progress_calls = []
        
        def progress_callback(progress):
            progress_calls.append(progress)
        
        files = await scanner.scan_directory(temp_directory, progress_callback)
        
        assert len(files) == 4
        assert len(progress_calls) > 0
        
        # Verify progress updates
        for progress in progress_calls:
            assert isinstance(progress, ScanProgress)
    
    @pytest.mark.asyncio
    async def test_scan_directories_success(self, scanner, temp_directory, lock_manager):
        """Test scanning multiple directories."""
        lock_file = Mock()
        lock_manager.create_lock.return_value = lock_file
        
        scanner.file_filter.filter_files.return_value = [
            Mock(should_process=True) for _ in range(4)
        ]
        
        # Create second temp directory
        with tempfile.TemporaryDirectory() as temp_dir2:
            test_dir2 = Path(temp_dir2)
            (test_dir2 / "file5.txt").write_text("Test content 5")
            
            results = await scanner.scan_directories([temp_directory, temp_dir2])
            
            assert len(results) == 2
            assert temp_directory in results
            assert temp_dir2 in results
            assert len(results[temp_directory]) == 4
            assert len(results[temp_dir2]) == 1
    
    @pytest.mark.asyncio
    async def test_scan_directories_invalid_input(self, scanner):
        """Test scanning with invalid input."""
        with pytest.raises(ValueError, match="directory_paths must be non-empty list"):
            await scanner.scan_directories([])
        
        with pytest.raises(ValueError, match="directory_paths must be non-empty list"):
            await scanner.scan_directories(None)
    
    @pytest.mark.asyncio
    async def test_extract_file_metadata(self, scanner, temp_directory):
        """Test file metadata extraction."""
        file_path = Path(temp_directory) / "file1.txt"
        
        file_info = await scanner._extract_file_metadata(file_path)
        
        assert isinstance(file_info, FileInfo)
        assert file_info.file_path == str(file_path)
        assert file_info.file_size > 0
        assert file_info.is_directory is False
        assert file_info.processing_status == "pending"
        assert "extension" in file_info.metadata
        assert file_info.metadata["extension"] == ".txt"
    
    @pytest.mark.asyncio
    async def test_extract_file_metadata_not_found(self, scanner):
        """Test metadata extraction for non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            await scanner._extract_file_metadata(Path("/nonexistent/file.txt"))
    
    @pytest.mark.asyncio
    async def test_extract_file_metadata_not_file(self, scanner, temp_directory):
        """Test metadata extraction for directory."""
        with pytest.raises(ValueError, match="Path is not a file"):
            await scanner._extract_file_metadata(Path(temp_directory))
    
    @pytest.mark.asyncio
    async def test_filter_files(self, scanner, temp_directory):
        """Test file filtering."""
        # Create real files for testing
        file1 = Path(temp_directory) / "test1.txt"
        file1.write_text("test content 1")
        
        file2 = Path(temp_directory) / "test2.txt"
        file2.write_text("test content 2")
        
        file3 = Path(temp_directory) / "test3.txt"
        file3.write_text("test content 3")
        
        file_infos = [
            FileInfo(file_path=str(file1), file_size=100, modification_time=datetime.now(), is_directory=False),
            FileInfo(file_path=str(file2), file_size=200, modification_time=datetime.now(), is_directory=False),
            FileInfo(file_path=str(file3), file_size=300, modification_time=datetime.now(), is_directory=False)
        ]
        
        progress = ScanProgress()
        
        # Mock filter results
        scanner.file_filter.filter_files.return_value = [
            Mock(should_process=True),
            Mock(should_process=False),
            Mock(should_process=True)
        ]
        
        filtered_files = await scanner._filter_files(file_infos, progress)
        
        assert len(filtered_files) == 2
        assert filtered_files[0].file_path == str(file1)
        assert filtered_files[1].file_path == str(file3)
    
    @pytest.mark.asyncio
    async def test_filter_files_empty_list(self, scanner):
        """Test filtering empty file list."""
        progress = ScanProgress()
        
        filtered_files = await scanner._filter_files([], progress)
        
        assert filtered_files == []
        assert progress.total_files == 0
    
    @pytest.mark.asyncio
    async def test_filter_files_invalid_input(self, scanner):
        """Test filtering with invalid input."""
        progress = ScanProgress()
        
        with pytest.raises(ValueError, match="file_infos must be list"):
            await scanner._filter_files("invalid", progress)
    
    def test_get_scan_statistics(self, scanner):
        """Test getting scan statistics."""
        # Set some statistics
        scanner._total_directories_scanned = 5
        scanner._total_files_discovered = 100
        scanner._total_files_filtered = 80
        scanner._scan_times = [1.0, 2.0, 3.0]
        scanner._last_scan_time = datetime.now()
        
        stats = scanner.get_scan_statistics()
        
        assert stats["total_directories_scanned"] == 5
        assert stats["total_files_discovered"] == 100
        assert stats["total_files_filtered"] == 80
        assert stats["average_scan_time"] == 2.0
        assert stats["scan_count"] == 3
        assert "last_scan_time" in stats
    
    def test_get_scan_statistics_empty(self, scanner):
        """Test getting statistics when no scans performed."""
        stats = scanner.get_scan_statistics()
        
        assert stats["total_directories_scanned"] == 0
        assert stats["total_files_discovered"] == 0
        assert stats["total_files_filtered"] == 0
        assert stats["average_scan_time"] == 0.0
        assert stats["scan_count"] == 0
        assert stats["last_scan_time"] is None
    
    def test_reset_statistics(self, scanner):
        """Test resetting statistics."""
        # Set some statistics
        scanner._total_directories_scanned = 5
        scanner._total_files_discovered = 100
        scanner._total_files_filtered = 80
        scanner._scan_times = [1.0, 2.0, 3.0]
        scanner._last_scan_time = datetime.now()
        
        scanner.reset_statistics()
        
        stats = scanner.get_scan_statistics()
        assert stats["total_directories_scanned"] == 0
        assert stats["total_files_discovered"] == 0
        assert stats["total_files_filtered"] == 0
        assert stats["average_scan_time"] == 0.0
        assert stats["scan_count"] == 0
        assert stats["last_scan_time"] is None
    
    @pytest.mark.asyncio
    async def test_scan_directory_recursive_max_depth(self, scanner, temp_directory):
        """Test recursive scanning with max depth limit."""
        progress = ScanProgress()
        
        # Create deep directory structure
        deep_dir = Path(temp_directory) / "deep1" / "deep2" / "deep3" / "deep4" / "deep5"
        deep_dir.mkdir(parents=True)
        (deep_dir / "file.txt").write_text("Deep content")
        
        files = await scanner._scan_directory_recursive(temp_directory, 0, progress)
        
        # Should find files up to max_depth (3)
        assert len(files) > 0
    
    @pytest.mark.asyncio
    async def test_scan_directory_recursive_permission_error(self, scanner, temp_directory):
        """Test recursive scanning with permission error."""
        progress = ScanProgress()
        
        with patch('pathlib.Path.iterdir', side_effect=PermissionError("Permission denied")):
            files = await scanner._scan_directory_recursive(temp_directory, 0, progress)
            
            assert files == []
    
    @pytest.mark.asyncio
    async def test_scan_directory_recursive_metadata_error(self, scanner, temp_directory):
        """Test recursive scanning with metadata extraction error."""
        progress = ScanProgress()
        
        with patch.object(scanner, '_extract_file_metadata', side_effect=Exception("Metadata error")):
            files = await scanner._scan_directory_recursive(temp_directory, 0, progress)
            
            # Should continue scanning other files despite metadata error
            assert len(files) == 0 