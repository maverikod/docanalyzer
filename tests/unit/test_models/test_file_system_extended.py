"""
Extended Tests for File System Models

Additional test cases to achieve 90%+ coverage for file system models.

Author: DocAnalyzer Team
Version: 1.0.0
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from docanalyzer.models.file_system import FileInfo, Directory, LockFile


class TestFileInfoExtended:
    """Extended test suite for FileInfo class."""
    
    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.TXT') as f:
            f.write("Test content")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_file_extension_uppercase(self, temp_file):
        """Test file_extension property with uppercase extension."""
        # Arrange
        stat = os.stat(temp_file)
        file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime)
        )
        
        # Act
        extension = file_info.file_extension
        
        # Assert
        assert extension == "txt"  # Should be lowercase
    
    def test_to_dict_with_last_processed(self, temp_file):
        """Test to_dict method with last_processed timestamp."""
        # Arrange
        stat = os.stat(temp_file)
        last_processed = datetime.now()
        file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime),
            last_processed=last_processed
        )
        
        # Act
        data = file_info.to_dict()
        
        # Assert
        assert data["last_processed"] is not None
        assert data["last_processed"] == last_processed.isoformat()
    
    def test_from_dict_with_last_processed(self, temp_file):
        """Test from_dict method with last_processed timestamp."""
        # Arrange
        stat = os.stat(temp_file)
        last_processed = datetime.now()
        original_file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime),
            last_processed=last_processed
        )
        data = original_file_info.to_dict()
        
        # Act
        new_file_info = FileInfo.from_dict(data)
        
        # Assert
        assert new_file_info.last_processed is not None
        assert new_file_info.last_processed == last_processed
    
    def test_from_dict_missing_optional_fields(self, temp_file):
        """Test from_dict method with missing optional fields."""
        # Arrange
        stat = os.stat(temp_file)
        data = {
            "file_path": temp_file,
            "file_size": stat.st_size,
            "modification_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
        
        # Act
        file_info = FileInfo.from_dict(data)
        
        # Assert
        assert file_info.is_directory is False
        assert file_info.processing_status == "pending"
        assert file_info.last_processed is None
        assert file_info.metadata == {}
    
    def test_equality_different_attributes(self, temp_file):
        """Test equality with different attributes."""
        # Arrange
        stat = os.stat(temp_file)
        file_info1 = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime),
            is_directory=False
        )
        file_info2 = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime),
            is_directory=True  # Different attribute
        )
        
        # Act & Assert
        assert file_info1 != file_info2


class TestDirectoryExtended:
    """Extended test suite for Directory class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def temp_file(self, temp_dir):
        """Create temporary file in temp directory."""
        temp_file = os.path.join(temp_dir, "test_file.txt")
        with open(temp_file, 'w') as f:
            f.write("Test content")
        return temp_file
    
    def test_to_dict_with_file_info(self, temp_dir, temp_file):
        """Test to_dict method with FileInfo objects."""
        # Arrange
        stat = os.stat(temp_file)
        file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime)
        )
        
        directory = Directory(temp_dir, 1, stat.st_size)
        directory.add_file(file_info, is_supported=True)
        
        # Act
        data = directory.to_dict()
        
        # Assert
        assert len(data["supported_files"]) == 1
        assert data["supported_files"][0]["file_path"] == temp_file
    
    def test_from_dict_with_file_info(self, temp_dir, temp_file):
        """Test from_dict method with FileInfo objects."""
        # Arrange
        stat = os.stat(temp_file)
        file_info = FileInfo(
            file_path=temp_file,
            file_size=stat.st_size,
            modification_time=datetime.fromtimestamp(stat.st_mtime)
        )
        
        directory = Directory(temp_dir, 1, stat.st_size)
        directory.add_file(file_info, is_supported=True)
        data = directory.to_dict()
        
        # Act
        new_directory = Directory.from_dict(data)
        
        # Assert
        assert len(new_directory.supported_files) == 1
        assert new_directory.supported_files[0].file_path == temp_file
    
    def test_from_dict_with_last_scan_time(self, temp_dir):
        """Test from_dict method with last_scan_time."""
        # Arrange
        last_scan_time = datetime.now()
        directory = Directory(temp_dir, 0, 0, last_scan_time=last_scan_time)
        data = directory.to_dict()
        
        # Act
        new_directory = Directory.from_dict(data)
        
        # Assert
        assert new_directory.last_scan_time == last_scan_time
    
    def test_from_dict_missing_optional_fields(self, temp_dir):
        """Test from_dict method with missing optional fields."""
        # Arrange
        data = {
            "directory_path": temp_dir,
            "file_count": 0,
            "total_size": 0
        }
        
        # Act
        directory = Directory.from_dict(data)
        
        # Assert
        assert directory.last_scan_time is None
        assert directory.processing_status == "pending"
        assert directory.subdirectories == []
        assert directory.supported_files == []
        assert directory.unsupported_files == []
        assert directory.scan_errors == []
    
    def test_equality_different_attributes(self, temp_dir):
        """Test equality with different attributes."""
        # Arrange
        directory1 = Directory(temp_dir, 0, 0)
        directory2 = Directory(temp_dir, 1, 0)  # Different file_count
        
        # Act & Assert
        assert directory1 != directory2


class TestLockFileExtended:
    """Extended test suite for LockFile class."""
    
    def test_is_expired_true(self):
        """Test is_expired method when lock has expired."""
        # Arrange
        created_at = datetime.now() - timedelta(hours=2)  # 2 hours ago
        lock = LockFile(
            process_id=12345,
            created_at=created_at,
            directory="/test/dir",
            timeout_seconds=3600  # 1 hour timeout
        )
        
        # Act
        is_expired = lock.is_expired()
        
        # Assert
        assert is_expired is True
    
    def test_is_expired_false(self):
        """Test is_expired method when lock has not expired."""
        # Arrange
        created_at = datetime.now() - timedelta(minutes=30)  # 30 minutes ago
        lock = LockFile(
            process_id=12345,
            created_at=created_at,
            directory="/test/dir",
            timeout_seconds=3600  # 1 hour timeout
        )
        
        # Act
        is_expired = lock.is_expired()
        
        # Assert
        assert is_expired is False
    
    def test_get_age_seconds(self):
        """Test get_age_seconds method."""
        # Arrange
        created_at = datetime.now() - timedelta(seconds=30)
        lock = LockFile(
            process_id=12345,
            created_at=created_at,
            directory="/test/dir"
        )
        
        # Act
        age = lock.get_age_seconds()
        
        # Assert
        assert age >= 30  # Should be at least 30 seconds
        assert isinstance(age, int)
    
    def test_to_dict_with_metadata(self):
        """Test to_dict method with metadata."""
        # Arrange
        metadata = {"config": "test", "version": "1.0"}
        lock = LockFile(
            process_id=12345,
            created_at=datetime.now(),
            directory="/test/dir",
            metadata=metadata
        )
        
        # Act
        data = lock.to_dict()
        
        # Assert
        assert data["metadata"] == metadata
    
    def test_from_dict_with_metadata(self):
        """Test from_dict method with metadata."""
        # Arrange
        metadata = {"config": "test", "version": "1.0"}
        lock = LockFile(
            process_id=12345,
            created_at=datetime.now(),
            directory="/test/dir",
            metadata=metadata
        )
        data = lock.to_dict()
        
        # Act
        new_lock = LockFile.from_dict(data)
        
        # Assert
        assert new_lock.metadata == metadata
    
    def test_from_dict_with_custom_lock_file_path(self):
        """Test from_dict method with custom lock file path."""
        # Arrange
        lock = LockFile(
            process_id=12345,
            created_at=datetime.now(),
            directory="/test/dir",
            lock_file_path="/custom/lock/path"
        )
        data = lock.to_dict()
        
        # Act
        new_lock = LockFile.from_dict(data)
        
        # Assert
        assert new_lock.lock_file_path == "/custom/lock/path"
    
    def test_from_dict_missing_optional_fields(self):
        """Test from_dict method with missing optional fields."""
        # Arrange
        data = {
            "process_id": 12345,
            "created_at": datetime.now().isoformat(),
            "directory": "/test/dir"
        }
        
        # Act
        lock = LockFile.from_dict(data)
        
        # Assert
        assert lock.status == "active"
        assert lock.lock_file_path is not None  # Should be generated
        assert lock.metadata == {}
        assert lock.timeout_seconds == 3600
    
    def test_equality_different_attributes(self):
        """Test equality with different attributes."""
        # Arrange
        created_at = datetime.now()
        lock1 = LockFile(
            process_id=12345,
            created_at=created_at,
            directory="/test/dir"
        )
        lock2 = LockFile(
            process_id=12346,  # Different process_id
            created_at=created_at,
            directory="/test/dir"
        )
        
        # Act & Assert
        assert lock1 != lock2
    
    def test_repr_with_all_attributes(self):
        """Test string representation with all attributes."""
        # Arrange
        lock = LockFile(
            process_id=12345,
            created_at=datetime.now(),
            directory="/test/dir",
            status="expired"
        )
        
        # Act
        repr_str = repr(lock)
        
        # Assert
        assert "LockFile" in repr_str
        assert "12345" in repr_str
        assert "/test/dir" in repr_str
        assert "expired" in repr_str 