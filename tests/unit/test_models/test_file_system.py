"""
Tests for File System Models

Comprehensive test suite for file system models including FileInfo,
Directory, and LockFile classes.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock

from docanalyzer.models.file_system import FileInfo, Directory, LockFile


class TestFileInfo:
    """Test suite for FileInfo class."""
    
    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def file_info(self, temp_file):
        """Create FileInfo instance for testing."""
        stat = os.stat(temp_file)
        return FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime)
        )
    
    def test_file_info_creation_success(self, temp_file):
        """Test successful FileInfo creation."""
        # Arrange
        stat = os.stat(temp_file)
        
        # Act
        file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime)
        )
        
        # Assert
        assert file_info.file_path == temp_file
        assert file_info.file_size == stat.st_size
        assert file_info.processing_status == "pending"
        assert file_info.is_directory is False
        assert file_info.metadata == {}
    
    def test_file_info_creation_with_optional_params(self, temp_file):
        """Test FileInfo creation with optional parameters."""
        # Arrange
        stat = os.stat(temp_file)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        last_processed = datetime.now()
        metadata = {"category": "test", "priority": "high"}
        
        # Act
        file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=mod_time,
            is_directory=False,
            processing_status="completed",
            last_processed=last_processed,
            metadata=metadata
        )
        
        # Assert
        assert file_info.processing_status == "completed"
        assert file_info.last_processed == last_processed
        assert file_info.metadata == metadata
    
    def test_file_info_creation_empty_path(self):
        """Test FileInfo creation with empty file path."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_path must be non-empty string"):
            FileInfo("", 1024, datetime.now())
    
    def test_file_info_creation_negative_size(self, temp_file):
        """Test FileInfo creation with negative file size."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_size must be non-negative integer"):
            FileInfo(temp_file, -1024, datetime.now())
    
    def test_file_info_creation_invalid_modification_time(self, temp_file):
        """Test FileInfo creation with invalid modification time."""
        # Act & Assert
        with pytest.raises(TypeError, match="modification_time must be datetime object"):
            FileInfo(temp_file, 1024, "invalid_time")
    
    def test_file_info_creation_nonexistent_file(self):
        """Test FileInfo creation with non-existent file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            FileInfo("/nonexistent/file.txt", 1024, datetime.now())
    
    def test_file_info_creation_invalid_status(self, temp_file):
        """Test FileInfo creation with invalid processing status."""
        # Arrange
        stat = os.stat(temp_file)
        
        # Act & Assert
        with pytest.raises(ValueError, match="processing_status must be one of"):
            FileInfo(
                file_path=temp_file,
                file_size=stat.st_size,
                modification_time=datetime.fromtimestamp(stat.st_mtime),
                processing_status="invalid_status"
            )
    
    def test_file_name_property(self, file_info):
        """Test file_name property."""
        # Act
        file_name = file_info.file_name
        
        # Assert
        assert file_name.endswith(".txt")
        assert len(file_name) > 0
    
    def test_file_extension_property(self, file_info):
        """Test file_extension property."""
        # Act
        extension = file_info.file_extension
        
        # Assert
        assert extension == "txt"
    
    def test_file_extension_property_uppercase(self, temp_file):
        """Test file_extension property with uppercase extension."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.TXT') as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            stat = os.stat(temp_path)
            file_info = FileInfo(
                file_path=temp_path,
                file_size=stat.st_size,
                modification_time=datetime.fromtimestamp(stat.st_mtime)
            )
            
            # Act
            extension = file_info.file_extension
            
            # Assert
            assert extension == "txt"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_to_dict(self, file_info):
        """Test to_dict method."""
        # Act
        data = file_info.to_dict()
        
        # Assert
        assert data["file_path"] == file_info.file_path
        assert data["file_size"] == file_info.file_size
        assert data["file_extension"] == "txt"
        assert data["processing_status"] == "pending"
        assert data["is_directory"] is False
        assert "modification_time" in data
        assert data["last_processed"] is None
    
    def test_to_dict_with_optional_fields(self, temp_file):
        """Test to_dict method with optional fields."""
        # Arrange
        stat = os.stat(temp_file)
        last_processed = datetime.now()
        metadata = {"test": "value"}
        
        file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime),
            last_processed=last_processed,
            metadata=metadata
        )
        
        # Act
        data = file_info.to_dict()
        
        # Assert
        assert data["last_processed"] is not None
        assert data["metadata"] == metadata
    
    def test_from_dict(self, file_info):
        """Test from_dict method."""
        # Arrange
        data = file_info.to_dict()
        
        # Act
        new_file_info = FileInfo.from_dict(data)
        
        # Assert
        assert new_file_info.file_path == file_info.file_path
        assert new_file_info.file_size == file_info.file_size
        assert new_file_info.processing_status == file_info.processing_status
    
    def test_from_dict_missing_required_fields(self):
        """Test from_dict method with missing required fields."""
        # Arrange
        data = {"file_path": "/test/file.txt"}  # Missing file_size and modification_time
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field"):
            FileInfo.from_dict(data)
    
    def test_equality(self, file_info):
        """Test equality comparison."""
        # Arrange
        same_file_info = FileInfo(
            file_path=file_info.file_path,
            file_size=file_info.file_size,
            modification_time=file_info.modification_time
        )
        
        # Act & Assert
        assert file_info == same_file_info
    
    def test_inequality(self, file_info):
        """Test inequality comparison."""
        # Arrange - create a different FileInfo with same size but different path
        # We need to create a real file for this test
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Different content")
            different_path = f.name
        
        try:
            stat = os.stat(different_path)
            different_file_info = FileInfo(
                file_path=different_path,
                file_size=stat.st_size,
                modification_time=datetime.fromtimestamp(stat.st_mtime)
            )
            
            # Act & Assert
            assert file_info != different_file_info
        finally:
            if os.path.exists(different_path):
                os.unlink(different_path)
    
    def test_equality_different_type(self, file_info):
        """Test equality with different type."""
        # Act & Assert
        assert file_info != "not a FileInfo"
    
    def test_repr(self, file_info):
        """Test string representation."""
        # Act
        repr_str = repr(file_info)
        
        # Assert
        assert "FileInfo" in repr_str
        assert file_info.file_path in repr_str
        assert str(file_info.file_size) in repr_str
        assert file_info.processing_status in repr_str


class TestDirectory:
    """Test suite for Directory class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def directory(self, temp_dir):
        """Create Directory instance for testing."""
        return Directory(
            directory_path=temp_dir,
            file_count=0,
            total_size=0
        )
    
    def test_directory_creation_success(self, temp_dir):
        """Test successful Directory creation."""
        # Act
        directory = Directory(
            directory_path=temp_dir,
            file_count=0,
            total_size=0
        )
        
        # Assert
        assert directory.directory_path == temp_dir
        assert directory.file_count == 0
        assert directory.total_size == 0
        assert directory.processing_status == "pending"
        assert directory.subdirectories == []
        assert directory.supported_files == []
        assert directory.unsupported_files == []
        assert directory.scan_errors == []
    
    def test_directory_creation_with_optional_params(self, temp_dir):
        """Test Directory creation with optional parameters."""
        # Arrange
        last_scan_time = datetime.now()
        subdirectories = ["subdir1", "subdir2"]
        supported_files = []
        unsupported_files = []
        scan_errors = ["Error 1", "Error 2"]
        
        # Act
        directory = Directory(
            directory_path=temp_dir,
            file_count=5,
            total_size=1024,
            last_scan_time=last_scan_time,
            processing_status="completed",
            subdirectories=subdirectories,
            supported_files=supported_files,
            unsupported_files=unsupported_files,
            scan_errors=scan_errors
        )
        
        # Assert
        assert directory.file_count == 5
        assert directory.total_size == 1024
        assert directory.last_scan_time == last_scan_time
        assert directory.processing_status == "completed"
        assert directory.subdirectories == subdirectories
        assert directory.scan_errors == scan_errors
    
    def test_directory_creation_empty_path(self):
        """Test Directory creation with empty path."""
        # Act & Assert
        with pytest.raises(ValueError, match="directory_path must be non-empty string"):
            Directory("", 0, 0)
    
    def test_directory_creation_negative_file_count(self, temp_dir):
        """Test Directory creation with negative file count."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_count must be non-negative integer"):
            Directory(temp_dir, -1, 0)
    
    def test_directory_creation_negative_total_size(self, temp_dir):
        """Test Directory creation with negative total size."""
        # Act & Assert
        with pytest.raises(ValueError, match="total_size must be non-negative integer"):
            Directory(temp_dir, 0, -1024)
    
    def test_directory_creation_nonexistent_directory(self):
        """Test Directory creation with non-existent directory."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            Directory("/nonexistent/directory", 0, 0)
    
    def test_directory_creation_file_path(self, temp_dir):
        """Test Directory creation with file path instead of directory."""
        # Create a temporary file in the temp directory
        temp_file = os.path.join(temp_dir, "test_file.txt")
        with open(temp_file, 'w') as f:
            f.write("test content")
        
        # Act & Assert
        with pytest.raises(NotADirectoryError):
            Directory(temp_file, 0, 0)
    
    def test_directory_creation_invalid_status(self, temp_dir):
        """Test Directory creation with invalid processing status."""
        # Act & Assert
        with pytest.raises(ValueError, match="processing_status must be one of"):
            Directory(
                directory_path=temp_dir,
                file_count=0,
                total_size=0,
                processing_status="invalid_status"
            )
    
    def test_directory_name_property(self, directory):
        """Test directory_name property."""
        # Act
        dir_name = directory.directory_name
        
        # Assert
        assert dir_name in directory.directory_path
        assert len(dir_name) > 0
    
    def test_add_file_supported(self, directory, temp_dir):
        """Test adding supported file."""
        # Create a temporary file
        temp_file = os.path.join(temp_dir, "test_file.txt")
        with open(temp_file, 'w') as f:
            f.write("test content")
        
        # Arrange
        stat = os.stat(temp_file)
        file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime)
        )
        
        # Act
        directory.add_file(file_info, is_supported=True)
        
        # Assert
        assert len(directory.supported_files) == 1
        assert directory.supported_files[0] == file_info
        assert len(directory.unsupported_files) == 0
    
    def test_add_file_unsupported(self, directory, temp_dir):
        """Test adding unsupported file."""
        # Create a temporary file
        temp_file = os.path.join(temp_dir, "test_file.txt")
        with open(temp_file, 'w') as f:
            f.write("test content")
        
        # Arrange
        stat = os.stat(temp_file)
        file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime)
        )
        
        # Act
        directory.add_file(file_info, is_supported=False)
        
        # Assert
        assert len(directory.unsupported_files) == 1
        assert directory.unsupported_files[0] == file_info
        assert len(directory.supported_files) == 0
    
    def test_add_file_none(self, directory):
        """Test adding None file."""
        # Act & Assert
        with pytest.raises(ValueError, match="file_info cannot be None"):
            directory.add_file(None)
    
    def test_add_file_invalid_type(self, directory):
        """Test adding invalid file type."""
        # Act & Assert
        with pytest.raises(TypeError, match="file_info must be FileInfo instance"):
            directory.add_file("not a FileInfo")
    
    def test_add_scan_error(self, directory):
        """Test adding scan error."""
        # Arrange
        error_message = "Permission denied"
        
        # Act
        directory.add_scan_error(error_message)
        
        # Assert
        assert len(directory.scan_errors) == 1
        assert directory.scan_errors[0] == error_message
    
    def test_add_scan_error_empty(self, directory):
        """Test adding empty scan error."""
        # Act & Assert
        with pytest.raises(ValueError, match="error_message must be non-empty string"):
            directory.add_scan_error("")
    
    def test_add_scan_error_invalid_type(self, directory):
        """Test adding invalid scan error type."""
        # Act & Assert
        with pytest.raises(TypeError, match="error_message must be string"):
            directory.add_scan_error(123)
    
    def test_equality(self, directory):
        """Test equality comparison."""
        # Arrange
        same_directory = Directory(
            directory_path=directory.directory_path,
            file_count=directory.file_count,
            total_size=directory.total_size
        )
        
        # Act & Assert
        assert directory == same_directory
    
    def test_inequality(self, directory, temp_dir):
        """Test inequality comparison."""
        # Create a different temporary directory
        different_temp_dir = tempfile.mkdtemp()
        try:
            different_directory = Directory(
                directory_path=different_temp_dir,
                file_count=directory.file_count,
                total_size=directory.total_size
            )
            
            # Act & Assert
            assert directory != different_directory
        finally:
            import shutil
            shutil.rmtree(different_temp_dir, ignore_errors=True)


class TestLockFile:
    """Test suite for LockFile class."""
    
    @pytest.fixture
    def lock_file(self):
        """Create LockFile instance for testing."""
        return LockFile(
            process_id=12345,
            created_at=datetime.now(),
            directory="/test/directory"
        )
    
    def test_lock_file_creation_success(self):
        """Test successful LockFile creation."""
        # Arrange
        process_id = 12345
        created_at = datetime.now()
        directory = "/test/directory"
        
        # Act
        lock_file = LockFile(
            process_id=process_id,
            created_at=created_at,
            directory=directory
        )
        
        # Assert
        assert lock_file.process_id == process_id
        assert lock_file.created_at == created_at
        assert lock_file.directory == directory
        assert lock_file.status == "active"
        assert lock_file.timeout_seconds == 3600
        assert lock_file.metadata == {}
    
    def test_lock_file_creation_with_optional_params(self):
        """Test LockFile creation with optional parameters."""
        # Arrange
        process_id = 12345
        created_at = datetime.now()
        directory = "/test/directory"
        lock_file_path = "/test/directory/.lock"
        metadata = {"user": "test", "priority": "high"}
        
        # Act
        lock_file = LockFile(
            process_id=process_id,
            created_at=created_at,
            directory=directory,
            status="expired",
            lock_file_path=lock_file_path,
            metadata=metadata,
            timeout_seconds=1800
        )
        
        # Assert
        assert lock_file.status == "expired"
        assert lock_file.lock_file_path == lock_file_path
        assert lock_file.metadata == metadata
        assert lock_file.timeout_seconds == 1800
    
    def test_lock_file_creation_negative_process_id(self):
        """Test LockFile creation with negative process ID."""
        # Act & Assert
        with pytest.raises(ValueError, match="process_id must be positive integer"):
            LockFile(-12345, datetime.now(), "/test/directory")
    
    def test_lock_file_creation_empty_directory(self):
        """Test LockFile creation with empty directory."""
        # Act & Assert
        with pytest.raises(ValueError, match="directory must be non-empty string"):
            LockFile(12345, datetime.now(), "")
    
    def test_lock_file_creation_invalid_created_at(self):
        """Test LockFile creation with invalid created_at."""
        # Act & Assert
        with pytest.raises(TypeError, match="created_at must be datetime object"):
            LockFile(12345, "invalid_time", "/test/directory")
    
    def test_is_expired_not_expired(self, lock_file):
        """Test is_expired when lock is not expired."""
        # Act
        is_expired = lock_file.is_expired()
        
        # Assert
        assert is_expired is False
    
    def test_is_expired_expired(self):
        """Test is_expired when lock is expired."""
        # Arrange
        old_time = datetime.now() - timedelta(hours=2)  # 2 hours ago
        lock_file = LockFile(
            process_id=12345,
            created_at=old_time,
            directory="/test/directory",
            timeout_seconds=3600  # 1 hour timeout
        )
        
        # Act
        is_expired = lock_file.is_expired()
        
        # Assert
        assert is_expired is True
    
    def test_get_age_seconds(self, lock_file):
        """Test get_age_seconds method."""
        # Act
        age = lock_file.get_age_seconds()
        
        # Assert
        assert isinstance(age, int)
        assert age >= 0
    
    def test_equality(self, lock_file):
        """Test equality comparison."""
        # Arrange
        same_lock_file = LockFile(
            process_id=lock_file.process_id,
            created_at=lock_file.created_at,
            directory=lock_file.directory
        )
        
        # Act & Assert
        assert lock_file == same_lock_file
    
    def test_inequality(self, lock_file):
        """Test inequality comparison."""
        # Arrange
        different_lock_file = LockFile(
            process_id=99999,
            created_at=lock_file.created_at,
            directory=lock_file.directory
        )
        
        # Act & Assert
        assert lock_file != different_lock_file 