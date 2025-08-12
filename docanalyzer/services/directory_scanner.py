"""
Directory Scanner Service

Provides functionality for scanning directories and discovering files.
Includes recursive scanning, file filtering, and metadata extraction.

The directory scanner is responsible for:
- Recursively scanning directories
- Filtering files based on supported types
- Extracting file metadata
- Integration with lock management
- Progress tracking and reporting

Author: DocAnalyzer Team
Version: 1.0.0
"""

from typing import List, Dict, Optional, Set, Callable, Any
from pathlib import Path
import asyncio
import logging
from datetime import datetime, timedelta

from docanalyzer.models.file_system import FileInfo, Directory
from docanalyzer.filters.file_filter import FileFilter, FileFilterResult
from docanalyzer.services.lock_manager import LockManager

logger = logging.getLogger(__name__)

DEFAULT_SCAN_DEPTH = 10
DEFAULT_BATCH_SIZE = 100
DEFAULT_TIMEOUT = 300  # 5 minutes


class ScanProgress:
    """
    Scan Progress - Progress Tracking
    
    Tracks the progress of directory scanning operations.
    Provides information about current status, processed files,
    and estimated completion time.
    
    Attributes:
        total_files (int): Total number of files discovered.
            Updated as scanning progresses.
        processed_files (int): Number of files processed so far.
            Incremented as files are processed.
        current_directory (str): Currently being scanned directory.
            Path to the directory being processed.
        start_time (datetime): When scanning started.
            Timestamp of scan initiation.
        estimated_completion (Optional[datetime]): Estimated completion time.
            Calculated based on current progress rate.
        status (str): Current scan status.
            One of: "scanning", "filtering", "completed", "error"
    
    Example:
        >>> progress = ScanProgress()
        >>> progress.update(processed=10, total=100)
        >>> print(progress.get_percentage())  # 10.0
    """
    
    def __init__(self):
        """
        Initialize ScanProgress instance.
        
        Sets up initial state for tracking scan progress.
        All counters start at 0, status is "scanning".
        """
        self.total_files = 0
        self.processed_files = 0
        self.current_directory = ""
        self.start_time = datetime.now()
        self.estimated_completion = None
        self.status = "scanning"
    
    def update(
        self,
        processed_files: Optional[int] = None,
        total_files: Optional[int] = None,
        current_directory: Optional[str] = None,
        status: Optional[str] = None
    ) -> None:
        """
        Update progress information.
        
        Updates one or more progress fields. Only provided
        parameters are updated, others remain unchanged.
        
        Args:
            processed_files (Optional[int]): Number of processed files.
                Must be non-negative integer if provided.
            total_files (Optional[int]): Total number of files.
                Must be non-negative integer if provided.
            current_directory (Optional[str]): Current directory being scanned.
                Must be valid path string if provided.
            status (Optional[str]): Current scan status.
                Must be valid status string if provided.
        
        Raises:
            ValueError: If parameters are negative or invalid
            TypeError: If parameters are not of expected types
        """
        if processed_files is not None:
            if not isinstance(processed_files, int) or processed_files < 0:
                raise ValueError("processed_files must be non-negative integer")
            self.processed_files = processed_files
        
        if total_files is not None:
            if not isinstance(total_files, int) or total_files < 0:
                raise ValueError("total_files must be non-negative integer")
            self.total_files = total_files
        
        if current_directory is not None:
            if not isinstance(current_directory, str):
                raise TypeError("current_directory must be string")
            self.current_directory = current_directory
        
        if status is not None:
            if not isinstance(status, str):
                raise TypeError("status must be string")
            self.status = status
        
        # Update estimated completion if we have progress data
        if self.processed_files > 0 and self.total_files > 0:
            elapsed = self.get_elapsed_time()
            if elapsed > 0:
                rate = self.processed_files / elapsed
                remaining = (self.total_files - self.processed_files) / rate
                self.estimated_completion = datetime.now() + timedelta(seconds=remaining)
    
    def get_percentage(self) -> float:
        """
        Get completion percentage.
        
        Returns:
            float: Completion percentage (0.0 to 100.0).
                Returns 0.0 if no files discovered yet.
        
        Example:
            >>> progress = ScanProgress()
            >>> progress.update(processed=50, total=100)
            >>> print(progress.get_percentage())  # 50.0
        """
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100.0
    
    def get_elapsed_time(self) -> float:
        """
        Get elapsed time since scan started.
        
        Returns:
            float: Elapsed time in seconds.
                Returns 0.0 if scan hasn't started.
        
        Example:
            >>> progress = ScanProgress()
            >>> await asyncio.sleep(2)
            >>> print(progress.get_elapsed_time())  # 2.0
        """
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_estimated_completion(self) -> Optional[datetime]:
        """
        Get estimated completion time.
        
        Returns:
            Optional[datetime]: Estimated completion time.
                Returns None if not enough data for estimation.
        
        Example:
            >>> progress = ScanProgress()
            >>> progress.update(processed=50, total=100)
            >>> eta = progress.get_estimated_completion()
            >>> print(eta)  # datetime object or None
        """
        return self.estimated_completion
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert progress to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of progress.
                Format: {
                    "total_files": int,
                    "processed_files": int,
                    "current_directory": str,
                    "start_time": str,
                    "estimated_completion": Optional[str],
                    "status": str,
                    "percentage": float,
                    "elapsed_time": float
                }
        
        Example:
            >>> progress = ScanProgress()
            >>> progress.update(processed=25, total=100)
            >>> data = progress.to_dict()
            >>> print(data["percentage"])  # 25.0
        """
        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "current_directory": self.current_directory,
            "start_time": self.start_time.isoformat(),
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "status": self.status,
            "percentage": self.get_percentage(),
            "elapsed_time": self.get_elapsed_time()
        }


class DirectoryScanner:
    """
    Directory Scanner - File Discovery Service
    
    Provides comprehensive directory scanning functionality for discovering
    and filtering files in directory trees. Integrates with lock management
    and file filtering systems.
    
    The scanner supports:
    - Recursive directory traversal
    - File filtering based on extensions and rules
    - Metadata extraction for discovered files
    - Progress tracking and reporting
    - Integration with lock management
    - Batch processing for large directories
    
    Attributes:
        file_filter (FileFilter): File filtering system.
            Used to determine which files should be processed.
        lock_manager (LockManager): Lock management system.
            Used to prevent concurrent processing of directories.
        max_depth (int): Maximum recursion depth.
            Prevents infinite recursion in deep directory structures.
        batch_size (int): Number of files to process in batches.
            Optimizes memory usage for large scans.
        timeout (int): Maximum scan duration in seconds.
            Prevents scans from running indefinitely.
    
    Example:
        >>> scanner = DirectoryScanner(
        ...     file_filter=FileFilter(supported_extensions={".txt", ".md"}),
        ...     lock_manager=LockManager()
        ... )
        >>> files = await scanner.scan_directory("/path/to/directory")
        >>> print(f"Found {len(files)} files")
    """
    
    def __init__(
        self,
        file_filter: FileFilter,
        lock_manager: LockManager,
        max_depth: int = DEFAULT_SCAN_DEPTH,
        batch_size: int = DEFAULT_BATCH_SIZE,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize DirectoryScanner instance.
        
        Args:
            file_filter (FileFilter): File filtering system.
                Must be valid FileFilter instance.
            lock_manager (LockManager): Lock management system.
                Must be valid LockManager instance.
            max_depth (int): Maximum recursion depth.
                Must be positive integer. Defaults to 10.
            batch_size (int): Number of files to process in batches.
                Must be positive integer. Defaults to 100.
            timeout (int): Maximum scan duration in seconds.
                Must be positive integer. Defaults to 300.
        
        Raises:
            ValueError: If parameters are not positive
            TypeError: If parameters are not of expected types
        """
        if not isinstance(file_filter, FileFilter):
            raise TypeError("file_filter must be FileFilter instance")
        
        if not isinstance(lock_manager, LockManager):
            raise TypeError("lock_manager must be LockManager instance")
        
        if max_depth <= 0:
            raise ValueError("max_depth must be positive")
        
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        
        self.file_filter = file_filter
        self.lock_manager = lock_manager
        self.max_depth = max_depth
        self.batch_size = batch_size
        self.timeout = timeout
        
        # Statistics tracking
        self._total_directories_scanned = 0
        self._total_files_discovered = 0
        self._total_files_filtered = 0
        self._scan_times = []
        self._last_scan_time = None
    
    async def scan_directory(
        self,
        directory_path: str,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> List[FileInfo]:
        """
        Scan a directory for files.
        
        Recursively scans the specified directory, applying filters
        and extracting metadata for discovered files. Uses lock management
        to prevent concurrent processing.
        
        Args:
            directory_path (str): Path to directory to scan.
                Must be existing directory path.
            progress_callback (Optional[Callable[[ScanProgress], None]]): Progress callback.
                Called periodically with current progress. Defaults to None.
        
        Returns:
            List[FileInfo]: List of discovered files that pass filters.
                Files are sorted by path for consistent ordering.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If access to directory is denied
            TimeoutError: If scan exceeds timeout
            LockError: If directory is already locked by another process
        
        Example:
            >>> scanner = DirectoryScanner(file_filter, lock_manager)
            >>> files = await scanner.scan_directory("/path/to/directory")
            >>> for file_info in files:
            ...     print(f"Found: {file_info.file_path}")
        """
        if not directory_path or not isinstance(directory_path, str):
            raise ValueError("directory_path must be non-empty string")
        
        # Validate directory exists
        directory_path = Path(directory_path).resolve()
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # Create lock for directory
        try:
            lock_file = await self.lock_manager.create_lock(str(directory_path))
            logger.info(f"Created lock for directory: {directory_path}")
        except Exception as e:
            logger.error(f"Failed to create lock for directory {directory_path}: {e}")
            raise
        
        try:
            # Initialize progress tracking
            progress = ScanProgress()
            progress.update(current_directory=str(directory_path), status="scanning")
            
            # Start timeout timer
            start_time = datetime.now()
            
            # Perform recursive scan
            all_files = await self._scan_directory_recursive(
                str(directory_path), 0, progress
            )
            
            # Update progress for filtering
            progress.update(status="filtering")
            if progress_callback:
                progress_callback(progress)
            
            # Filter files
            filtered_files = await self._filter_files(all_files, progress)
            
            # Update statistics
            scan_time = (datetime.now() - start_time).total_seconds()
            self._scan_times.append(scan_time)
            self._last_scan_time = datetime.now()
            self._total_directories_scanned += 1
            self._total_files_discovered += len(all_files)
            self._total_files_filtered += len(filtered_files)
            
            # Final progress update
            progress.update(
                processed_files=len(filtered_files),
                total_files=len(all_files),
                status="completed"
            )
            if progress_callback:
                progress_callback(progress)
            
            logger.info(f"Scan completed: {len(filtered_files)} files found in {directory_path}")
            return sorted(filtered_files, key=lambda f: f.file_path)
            
        except asyncio.TimeoutError:
            logger.error(f"Scan timeout for directory: {directory_path}")
            raise TimeoutError(f"Scan exceeded timeout of {self.timeout} seconds")
        except Exception as e:
            logger.error(f"Scan error for directory {directory_path}: {e}")
            progress.update(status="error")
            if progress_callback:
                progress_callback(progress)
            raise
        finally:
            # Always remove lock
            try:
                await self.lock_manager.remove_lock(lock_file)
                logger.info(f"Removed lock for directory: {directory_path}")
            except Exception as e:
                logger.error(f"Failed to remove lock for directory {directory_path}: {e}")
    
    async def scan_directories(
        self,
        directory_paths: List[str],
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> Dict[str, List[FileInfo]]:
        """
        Scan multiple directories for files.
        
        Scans multiple directories concurrently, applying filters
        and extracting metadata. Results are grouped by directory.
        
        Args:
            directory_paths (List[str]): List of directory paths to scan.
                Must be list of existing directory paths.
            progress_callback (Optional[Callable[[ScanProgress], None]]): Progress callback.
                Called periodically with current progress. Defaults to None.
        
        Returns:
            Dict[str, List[FileInfo]]: Dictionary mapping directory paths to file lists.
                Each directory contains list of discovered files that pass filters.
        
        Raises:
            FileNotFoundError: If any directory doesn't exist
            PermissionError: If access to any directory is denied
            TimeoutError: If scan exceeds timeout
            LockError: If any directory is already locked
        
        Example:
            >>> scanner = DirectoryScanner(file_filter, lock_manager)
            >>> results = await scanner.scan_directories(["/path1", "/path2"])
            >>> for dir_path, files in results.items():
            ...     print(f"{dir_path}: {len(files)} files")
        """
        if not directory_paths or not isinstance(directory_paths, list):
            raise ValueError("directory_paths must be non-empty list")
        
        # Validate all directories exist
        for path in directory_paths:
            if not path or not isinstance(path, str):
                raise ValueError("All directory paths must be non-empty strings")
            
            dir_path = Path(path).resolve()
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory not found: {dir_path}")
            
            if not dir_path.is_dir():
                raise ValueError(f"Path is not a directory: {dir_path}")
        
        # Scan directories concurrently
        tasks = [
            self.scan_directory(path, progress_callback)
            for path in directory_paths
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            final_results = {}
            for i, result in enumerate(results):
                directory_path = directory_paths[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Failed to scan directory {directory_path}: {result}")
                    final_results[directory_path] = []
                else:
                    final_results[directory_path] = result
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error scanning multiple directories: {e}")
            raise
    
    async def _scan_directory_recursive(
        self,
        directory_path: str,
        current_depth: int,
        progress: ScanProgress
    ) -> List[FileInfo]:
        """
        Recursively scan a directory.
        
        Internal method that performs the actual recursive scanning.
        Respects max_depth limit and applies file filtering.
        
        Args:
            directory_path (str): Path to directory to scan.
                Must be existing directory path.
            current_depth (int): Current recursion depth.
                Must be non-negative integer.
            progress (ScanProgress): Progress tracking object.
                Updated as scanning progresses.
        
        Returns:
            List[FileInfo]: List of discovered files that pass filters.
                Files from current directory and subdirectories.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If access to directory is denied
        """
        if current_depth > self.max_depth:
            logger.debug(f"Max depth reached at {directory_path}")
            return []
        
        try:
            directory = Path(directory_path)
            if not directory.exists():
                logger.warning(f"Directory no longer exists: {directory_path}")
                return []
            
            if not directory.is_dir():
                logger.warning(f"Path is not a directory: {directory_path}")
                return []
            
            # Update progress
            progress.update(current_directory=str(directory))
            
            all_files = []
            
            # Scan current directory
            try:
                for item in directory.iterdir():
                    if item.is_file():
                        try:
                            file_info = await self._extract_file_metadata(item)
                            all_files.append(file_info)
                        except Exception as e:
                            logger.warning(f"Failed to extract metadata for {item}: {e}")
                            continue
                    elif item.is_dir() and current_depth < self.max_depth:
                        # Recursively scan subdirectories
                        sub_files = await self._scan_directory_recursive(
                            str(item), current_depth + 1, progress
                        )
                        all_files.extend(sub_files)
                        
            except PermissionError as e:
                logger.warning(f"Permission denied accessing {directory_path}: {e}")
                return []
            except Exception as e:
                logger.error(f"Error scanning directory {directory_path}: {e}")
                return []
            
            return all_files
            
        except Exception as e:
            logger.error(f"Unexpected error in recursive scan at {directory_path}: {e}")
            return []
    
    async def _extract_file_metadata(self, file_path: Path) -> FileInfo:
        """
        Extract metadata for a single file.
        
        Internal method that creates FileInfo object with
        complete metadata for the specified file.
        
        Args:
            file_path (Path): Path to file to analyze.
                Must be existing file path.
        
        Returns:
            FileInfo: File information with complete metadata.
                Includes size, modification time, permissions, etc.
        
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If access to file is denied
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        try:
            stat = file_path.stat()
            
            # Extract file extension
            extension = file_path.suffix.lower()
            
            # Create FileInfo object
            file_info = FileInfo(
                file_path=str(file_path),
                file_size=stat.st_size,
                modification_time=datetime.fromtimestamp(stat.st_mtime),
                is_directory=False,
                processing_status="pending",
                metadata={
                    "extension": extension,
                    "permissions": oct(stat.st_mode)[-3:],
                    "owner_id": stat.st_uid,
                    "group_id": stat.st_gid
                }
            )
            
            return file_info
            
        except PermissionError:
            raise PermissionError(f"Permission denied accessing file: {file_path}")
        except Exception as e:
            raise Exception(f"Error extracting metadata for {file_path}: {e}")
    
    async def _filter_files(
        self,
        file_infos: List[FileInfo],
        progress: ScanProgress
    ) -> List[FileInfo]:
        """
        Filter list of files using file filter.
        
        Internal method that applies file filtering to a list
        of files and updates progress accordingly.
        
        Args:
            file_infos (List[FileInfo]): List of files to filter.
                Must be list of valid FileInfo instances.
            progress (ScanProgress): Progress tracking object.
                Updated with filtering progress.
        
        Returns:
            List[FileInfo]: List of files that pass all filters.
                Files are sorted by path for consistent ordering.
        
        Raises:
            ValueError: If file_infos contains invalid items
        """
        if not isinstance(file_infos, list):
            raise ValueError("file_infos must be list")
        
        # Update progress
        progress.update(total_files=len(file_infos))
        
        if not file_infos:
            return []
        
        # Apply filtering
        filter_results = self.file_filter.filter_files(file_infos)
        
        # Extract files that pass filters
        filtered_files = []
        processed_count = 0
        
        for file_info, filter_result in zip(file_infos, filter_results):
            processed_count += 1
            
            if filter_result.should_process:
                filtered_files.append(file_info)
            
            # Update progress periodically
            if processed_count % self.batch_size == 0:
                progress.update(processed_files=processed_count)
        
        # Final progress update
        progress.update(processed_files=len(file_infos))
        
        logger.info(f"Filtered {len(file_infos)} files, {len(filtered_files)} passed filters")
        return filtered_files
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """
        Get scanning statistics.
        
        Returns:
            Dict[str, Any]: Dictionary with scanning statistics.
                Format: {
                    "total_directories_scanned": int,
                    "total_files_discovered": int,
                    "total_files_filtered": int,
                    "average_scan_time": float,
                    "last_scan_time": Optional[datetime]
                }
        
        Example:
            >>> scanner = DirectoryScanner(file_filter, lock_manager)
            >>> await scanner.scan_directory("/path/to/directory")
            >>> stats = scanner.get_scan_statistics()
            >>> print(f"Scanned {stats['total_directories_scanned']} directories")
        """
        average_scan_time = 0.0
        if self._scan_times:
            average_scan_time = sum(self._scan_times) / len(self._scan_times)
        
        return {
            "total_directories_scanned": self._total_directories_scanned,
            "total_files_discovered": self._total_files_discovered,
            "total_files_filtered": self._total_files_filtered,
            "average_scan_time": average_scan_time,
            "last_scan_time": self._last_scan_time.isoformat() if self._last_scan_time else None,
            "scan_count": len(self._scan_times)
        }
    
    def reset_statistics(self) -> None:
        """
        Reset scanning statistics.
        
        Clears all accumulated statistics and resets counters
        to initial values.
        
        Example:
            >>> scanner = DirectoryScanner(file_filter, lock_manager)
            >>> scanner.reset_statistics()
            >>> stats = scanner.get_scan_statistics()
            >>> print(stats["total_files_discovered"])  # 0
        """
        self._total_directories_scanned = 0
        self._total_files_discovered = 0
        self._total_files_filtered = 0
        self._scan_times.clear()
        self._last_scan_time = None
        logger.info("Scan statistics reset") 