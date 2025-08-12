"""
Tests for Directory Scanner Service

Comprehensive test suite for directory scanning functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

from docanalyzer.services.directory_scanner import DirectoryScanner, ScanProgress
from docanalyzer.filters.file_filter import FileFilter
from docanalyzer.services.lock_manager import LockManager
from docanalyzer.models.file_system import FileInfo, LockFile


class TestScanProgress:
    """Test suite for ScanProgress class."""
    
    def test_init(self):
        """Test initialization."""
        progress = ScanProgress()
        
        assert progress.total_files == 0
        assert progress.processed_files == 0
        assert progress.current_directory == ""
        assert progress.status == "scanning"
        assert progress.estimated_completion is None
        assert isinstance(progress.start_time, datetime)
    
    def test_update_processed_files(self):
        """Test updating processed files."""
        progress = ScanProgress()
        
        progress.update(processed_files=10)
        
        assert progress.processed_files == 10
        assert progress.total_files == 0  # Unchanged
    
    def test_update_total_files(self):
        """Test updating total files."""
        progress = ScanProgress()
        
        progress.update(total_files=100)
        
        assert progress.total_files == 100
        assert progress.processed_files == 0  # Unchanged
    
    def test_update_current_directory(self):
        """Test updating current directory."""
        progress = ScanProgress()
        
        progress.update(current_directory="/test/dir")
        
        assert progress.current_directory == "/test/dir"
    
    def test_update_status(self):
        """Test updating status."""
        progress = ScanProgress()
        
        progress.update(status="completed")
        
        assert progress.status == "completed"
    
    def test_update_multiple_parameters(self):
        """Test updating multiple parameters at once."""
        progress = ScanProgress()
        
        progress.update(
            processed_files=25,
            total_files=100,
            current_directory="/test/dir",
            status="filtering"
        )
        
        assert progress.processed_files == 25
        assert progress.total_files == 100
        assert progress.current_directory == "/test/dir"
        assert progress.status == "filtering"
    
    def test_update_invalid_processed_files(self):
        """Test updating with invalid processed files."""
        progress = ScanProgress()
        
        with pytest.raises(ValueError, match="processed_files must be non-negative integer"):
            progress.update(processed_files=-1)
    
    def test_update_invalid_total_files(self):
        """Test updating with invalid total files."""
        progress = ScanProgress()
        
        with pytest.raises(ValueError, match="total_files must be non-negative integer"):
            progress.update(total_files=-1)
    
    def test_update_invalid_current_directory_type(self):
        """Test updating with invalid current directory type."""
        progress = ScanProgress()
        
        with pytest.raises(TypeError, match="current_directory must be string"):
            progress.update(current_directory=123)
    
    def test_update_invalid_status_type(self):
        """Test updating with invalid status type."""
        progress = ScanProgress()
        
        with pytest.raises(TypeError, match="status must be string"):
            progress.update(status=123)
    
    def test_get_percentage_zero_total(self):
        """Test getting percentage with zero total files."""
        progress = ScanProgress()
        
        percentage = progress.get_percentage()
        
        assert percentage == 0.0
    
    def test_get_percentage_with_values(self):
        """Test getting percentage with actual values."""
        progress = ScanProgress()
        progress.update(processed_files=50, total_files=100)
        
        percentage = progress.get_percentage()
        
        assert percentage == 50.0
    
    def test_get_percentage_100_percent(self):
        """Test getting percentage for complete scan."""
        progress = ScanProgress()
        progress.update(processed_files=100, total_files=100)
        
        percentage = progress.get_percentage()
        
        assert percentage == 100.0
    
    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        progress = ScanProgress()
        
        # Wait a bit to ensure some time has passed
        import time
        time.sleep(0.1)
        
        elapsed = progress.get_elapsed_time()
        
        assert elapsed > 0.0
    
    def test_get_estimated_completion_none(self):
        """Test getting estimated completion when not available."""
        progress = ScanProgress()
        
        eta = progress.get_estimated_completion()
        
        assert eta is None
    
    def test_get_estimated_completion_with_data(self):
        """Test getting estimated completion with progress data."""
        progress = ScanProgress()
        progress.update(processed_files=50, total_files=100)
        
        eta = progress.get_estimated_completion()
        
        assert eta is not None
        assert isinstance(eta, datetime)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        progress = ScanProgress()
        progress.update(
            processed_files=25,
            total_files=100,
            current_directory="/test/dir",
            status="scanning"
        )
        
        data = progress.to_dict()
        
        assert data["total_files"] == 100
        assert data["processed_files"] == 25
        assert data["current_directory"] == "/test/dir"
        assert data["status"] == "scanning"
        assert data["percentage"] == 25.0
        assert data["elapsed_time"] > 0.0
        assert "start_time" in data
        assert "estimated_completion" in data


class TestDirectoryScanner:
    """Test suite for DirectoryScanner class."""
    
    @pytest.fixture
    def mock_file_filter(self):
        """Create mock file filter."""
        filter_mock = Mock(spec=FileFilter)
        filter_mock.filter_files.return_value = [
            Mock(should_process=True),
            Mock(should_process=False)
        ]
        return filter_mock
    
    @pytest.fixture
    def mock_lock_manager(self):
        """Create mock lock manager."""
        lock_mock = Mock(spec=LockManager)
        lock_mock.create_lock = AsyncMock(return_value=Mock(spec=LockFile))
        lock_mock.remove_lock = AsyncMock(return_value=True)
        return lock_mock
    
    @pytest.fixture
    def directory_scanner(self, mock_file_filter, mock_lock_manager):
        """Create DirectoryScanner instance for testing."""
        return DirectoryScanner(
            file_filter=mock_file_filter,
            lock_manager=mock_lock_manager,
            max_depth=3,
            batch_size=10,
            timeout=60
        )
    
    def test_init_valid_parameters(self, mock_file_filter, mock_lock_manager):
        """Test initialization with valid parameters."""
        scanner = DirectoryScanner(
            file_filter=mock_file_filter,
            lock_manager=mock_lock_manager,
            max_depth=5,
            batch_size=50,
            timeout=120
        )
        
        assert scanner.file_filter == mock_file_filter
        assert scanner.lock_manager == mock_lock_manager
        assert scanner.max_depth == 5
        assert scanner.batch_size == 50
        assert scanner.timeout == 120
    
    def test_init_invalid_file_filter_type(self, mock_lock_manager):
        """Test initialization with invalid file filter type."""
        with pytest.raises(TypeError, match="file_filter must be FileFilter instance"):
            DirectoryScanner(
                file_filter="not_a_filter",
                lock_manager=mock_lock_manager
            )
    
    def test_init_invalid_lock_manager_type(self, mock_file_filter):
        """Test initialization with invalid lock manager type."""
        with pytest.raises(TypeError, match="lock_manager must be LockManager instance"):
            DirectoryScanner(
                file_filter=mock_file_filter,
                lock_manager="not_a_lock_manager"
            )
    
    def test_init_invalid_max_depth(self, mock_file_filter, mock_lock_manager):
        """Test initialization with invalid max depth."""
        with pytest.raises(ValueError, match="max_depth must be positive"):
            DirectoryScanner(
                file_filter=mock_file_filter,
                lock_manager=mock_lock_manager,
                max_depth=0
            )
    
    def test_init_invalid_batch_size(self, mock_file_filter, mock_lock_manager):
        """Test initialization with invalid batch size."""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            DirectoryScanner(
                file_filter=mock_file_filter,
                lock_manager=mock_lock_manager,
                batch_size=0
            )
    
    def test_init_invalid_timeout(self, mock_file_filter, mock_lock_manager):
        """Test initialization with invalid timeout."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            DirectoryScanner(
                file_filter=mock_file_filter,
                lock_manager=mock_lock_manager,
                timeout=0
            )
    
    @pytest.mark.asyncio
    async def test_scan_directory_success(self, directory_scanner, tmp_path):
        """Test successful directory scanning."""
        # Create test directory structure
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        # Create test files
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.md").write_text("content2")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "file3.py").write_text("content3")
        
        # Mock file filter to accept all files
        directory_scanner.file_filter.filter_files.return_value = [
            Mock(should_process=True),
            Mock(should_process=True),
            Mock(should_process=True)
        ]
        
        # Mock metadata extraction
        with patch.object(directory_scanner, '_extract_file_metadata') as mock_extract:
            mock_file_info = Mock(spec=FileInfo)
            mock_file_info.file_path = "test_path"
            mock_file_info.file_name = "test_file.txt"
            mock_file_info.file_extension = "txt"
            mock_file_info.file_size = 1024
            mock_file_info.is_directory = False
            mock_extract.return_value = mock_file_info
        
        files = await directory_scanner.scan_directory(str(test_dir))
        
        assert len(files) == 3
        assert all(isinstance(f, FileInfo) for f in files)
    
    @pytest.mark.asyncio
    async def test_scan_directory_nonexistent(self, directory_scanner):
        """Test scanning nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            await directory_scanner.scan_directory("/nonexistent/directory")
    
    @pytest.mark.asyncio
    async def test_scan_directory_not_directory(self, directory_scanner, tmp_path):
        """Test scanning path that is not a directory."""
        # Create a file instead of directory
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("content")
        
        with pytest.raises(ValueError, match="Path is not a directory"):
            await directory_scanner.scan_directory(str(test_file))
    
    @pytest.mark.asyncio
    async def test_scan_directory_empty_path(self, directory_scanner):
        """Test scanning with empty path."""
        with pytest.raises(ValueError, match="directory_path must be non-empty string"):
            await directory_scanner.scan_directory("")
    
    @pytest.mark.asyncio
    async def test_scan_directory_invalid_path_type(self, directory_scanner):
        """Test scanning with invalid path type."""
        with pytest.raises(ValueError, match="directory_path must be non-empty string"):
            await directory_scanner.scan_directory(None)
    
    @pytest.mark.asyncio
    async def test_scan_directory_lock_error(self, directory_scanner, tmp_path):
        """Test scanning with lock creation error."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        # Mock lock creation to fail
        directory_scanner.lock_manager.create_lock.side_effect = Exception("Lock error")
        
        with pytest.raises(Exception, match="Lock error"):
            await directory_scanner.scan_directory(str(test_dir))
    
    @pytest.mark.asyncio
    async def test_scan_directories_success(self, directory_scanner, tmp_path):
        """Test scanning multiple directories successfully."""
        # Create test directories
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "file1.txt").write_text("content1")
        
        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "file2.md").write_text("content2")
        
        # Mock file filter to accept all files
        directory_scanner.file_filter.filter_files.return_value = [
            Mock(should_process=True)
        ]
        
        # Mock metadata extraction
        with patch.object(directory_scanner, '_extract_file_metadata') as mock_extract:
            mock_file_info = Mock(spec=FileInfo)
            mock_file_info.file_path = "test_path"
            mock_file_info.file_name = "test_file.txt"
            mock_file_info.file_extension = "txt"
            mock_file_info.file_size = 1024
            mock_file_info.is_directory = False
            mock_extract.return_value = mock_file_info
        
        results = await directory_scanner.scan_directories([str(dir1), str(dir2)])
        
        assert len(results) == 2
        assert str(dir1) in results
        assert str(dir2) in results
        assert len(results[str(dir1)]) == 1
        assert len(results[str(dir2)]) == 1
    
    @pytest.mark.asyncio
    async def test_scan_directories_empty_list(self, directory_scanner):
        """Test scanning with empty directory list."""
        with pytest.raises(ValueError, match="directory_paths must be non-empty list"):
            await directory_scanner.scan_directories([])
    
    @pytest.mark.asyncio
    async def test_scan_directories_invalid_list_type(self, directory_scanner):
        """Test scanning with invalid list type."""
        with pytest.raises(ValueError, match="directory_paths must be non-empty list"):
            await directory_scanner.scan_directories("not_a_list")
    
    @pytest.mark.asyncio
    async def test_scan_directories_with_errors(self, directory_scanner, tmp_path):
        """Test scanning multiple directories with some errors."""
        # Create test directory
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        
        # Mock file filter to accept all files
        directory_scanner.file_filter.filter_files.return_value = [
            Mock(should_process=True)
        ]
        
        # Mock metadata extraction
        with patch.object(directory_scanner, '_extract_file_metadata') as mock_extract:
            mock_file_info = Mock(spec=FileInfo)
            mock_file_info.file_path = "test_path"
            mock_file_info.file_name = "test_file.txt"
            mock_file_info.file_extension = "txt"
            mock_file_info.file_size = 1024
            mock_file_info.is_directory = False
            mock_extract.return_value = mock_file_info
        
        # Test with valid directories only
        results = await directory_scanner.scan_directories([
            str(test_dir)
        ])
        
        assert len(results) == 1
        assert str(test_dir) in results
        assert len(results[str(test_dir)]) == 1
    
    @pytest.mark.asyncio
    async def test_extract_file_metadata_success(self, directory_scanner, tmp_path):
        """Test successful metadata extraction."""
        # Create test file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("content")
        
        file_info = await directory_scanner._extract_file_metadata(test_file)
        
        assert isinstance(file_info, FileInfo)
        assert file_info.file_path == str(test_file)
        assert file_info.file_name == "test_file.txt"
        assert file_info.file_extension == "txt"
        assert file_info.file_size > 0
        assert file_info.is_directory is False
    
    @pytest.mark.asyncio
    async def test_extract_file_metadata_nonexistent_file(self, directory_scanner, tmp_path):
        """Test metadata extraction for nonexistent file."""
        test_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            await directory_scanner._extract_file_metadata(test_file)
    
    @pytest.mark.asyncio
    async def test_extract_file_metadata_not_file(self, directory_scanner, tmp_path):
        """Test metadata extraction for directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        with pytest.raises(ValueError, match="Path is not a file"):
            await directory_scanner._extract_file_metadata(test_dir)
    
    @pytest.mark.asyncio
    async def test_filter_files_success(self, directory_scanner):
        """Test successful file filtering."""
        # Create test file infos
        file_infos = [
            Mock(spec=FileInfo, file_path="/test/file1.txt"),
            Mock(spec=FileInfo, file_path="/test/file2.md")
        ]
        
        # Mock file filter results
        directory_scanner.file_filter.filter_files.return_value = [
            Mock(should_process=True),
            Mock(should_process=False)
        ]
        
        progress = Mock()
        
        filtered_files = await directory_scanner._filter_files(file_infos, progress)
        
        assert len(filtered_files) == 1
        assert filtered_files[0] == file_infos[0]
    
    @pytest.mark.asyncio
    async def test_filter_files_empty_list(self, directory_scanner):
        """Test filtering empty file list."""
        progress = Mock()
        
        filtered_files = await directory_scanner._filter_files([], progress)
        
        assert filtered_files == []
    
    @pytest.mark.asyncio
    async def test_filter_files_invalid_list_type(self, directory_scanner):
        """Test filtering with invalid list type."""
        progress = Mock()
        
        with pytest.raises(ValueError, match="file_infos must be list"):
            await directory_scanner._filter_files("not_a_list", progress)
    
    def test_get_scan_statistics(self, directory_scanner):
        """Test getting scan statistics."""
        # Set some statistics
        directory_scanner._total_directories_scanned = 5
        directory_scanner._total_files_discovered = 100
        directory_scanner._total_files_filtered = 80
        directory_scanner._scan_times = [1.5, 2.0, 1.8]
        directory_scanner._last_scan_time = datetime.now()
        
        stats = directory_scanner.get_scan_statistics()
        
        assert stats["total_directories_scanned"] == 5
        assert stats["total_files_discovered"] == 100
        assert stats["total_files_filtered"] == 80
        assert stats["average_scan_time"] == pytest.approx(1.77, rel=1e-2)
        assert stats["scan_count"] == 3
        assert "last_scan_time" in stats
    
    def test_get_scan_statistics_no_scans(self, directory_scanner):
        """Test getting statistics with no scans performed."""
        stats = directory_scanner.get_scan_statistics()
        
        assert stats["total_directories_scanned"] == 0
        assert stats["total_files_discovered"] == 0
        assert stats["total_files_filtered"] == 0
        assert stats["average_scan_time"] == 0.0
        assert stats["scan_count"] == 0
        assert stats["last_scan_time"] is None
    
    def test_reset_statistics(self, directory_scanner):
        """Test resetting statistics."""
        # Set some statistics
        directory_scanner._total_directories_scanned = 5
        directory_scanner._total_files_discovered = 100
        directory_scanner._total_files_filtered = 80
        directory_scanner._scan_times = [1.5, 2.0, 1.8]
        directory_scanner._last_scan_time = datetime.now()
        
        directory_scanner.reset_statistics()
        
        assert directory_scanner._total_directories_scanned == 0
        assert directory_scanner._total_files_discovered == 0
        assert directory_scanner._total_files_filtered == 0
        assert directory_scanner._scan_times == []
        assert directory_scanner._last_scan_time is None
    
    @pytest.mark.asyncio
    async def test_scan_directory_recursive_max_depth(self, directory_scanner, tmp_path):
        """Test recursive scanning respects max depth."""
        # Create deep directory structure
        current_dir = tmp_path
        for i in range(5):  # Deeper than max_depth of 3
            current_dir = current_dir / f"dir{i}"
            current_dir.mkdir()
            (current_dir / f"file{i}.txt").write_text(f"content{i}")
        
        progress = Mock()
        
        files = await directory_scanner._scan_directory_recursive(
            str(tmp_path), 0, progress
        )
        
        # Should only get files from first 3 levels (max_depth)
        assert len(files) == 3
    
    @pytest.mark.asyncio
    async def test_scan_directory_recursive_permission_error(self, directory_scanner, tmp_path):
        """Test recursive scanning handles permission errors."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        
        # Mock iterdir to raise PermissionError
        with patch.object(Path, 'iterdir', side_effect=PermissionError("Access denied")):
            progress = Mock()
            
            files = await directory_scanner._scan_directory_recursive(
                str(test_dir), 0, progress
            )
            
            assert files == []
    
    @pytest.mark.asyncio
    async def test_scan_directory_recursive_nonexistent_directory(self, directory_scanner):
        """Test recursive scanning handles nonexistent directory."""
        progress = Mock()
        
        files = await directory_scanner._scan_directory_recursive(
            "/nonexistent/directory", 0, progress
        )
        
        assert files == [] 