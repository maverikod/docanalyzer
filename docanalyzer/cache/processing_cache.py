"""
Processing Cache - File Processing Cache Management System

Provides intelligent caching for file processing results, chunking operations,
and vector embeddings to improve performance and reduce redundant processing.

The cache system stores processed file metadata, chunking results, and
embeddings with configurable TTL and eviction policies to optimize
memory usage and processing speed.

Author: Cache Team
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import time
import gzip
import pickle
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import logging

from docanalyzer.models.file_system import FileInfo
from docanalyzer.models.processing import ProcessingBlock, FileProcessingResult

logger = logging.getLogger(__name__)

DEFAULT_CACHE_TTL = 3600  # 1 hour
DEFAULT_MAX_CACHE_SIZE = 1000  # 1000 items
DEFAULT_CLEANUP_INTERVAL = 300  # 5 minutes


@dataclass
class CacheConfig:
    """
    Configuration for processing cache.
    
    Attributes:
        ttl_seconds (int): Time-to-live for cache entries in seconds.
            Must be positive integer. Defaults to 3600 (1 hour).
        max_size (int): Maximum number of cache entries.
            Must be positive integer. Defaults to 1000.
        cleanup_interval (int): Cache cleanup interval in seconds.
            Must be positive integer. Defaults to 300 (5 minutes).
        enable_persistence (bool): Enable cache persistence to disk.
            Defaults to True.
        cache_directory (str): Directory for persistent cache storage.
            Must be valid directory path. Defaults to "./cache".
        compression_enabled (bool): Enable cache compression.
            Defaults to True.
        eviction_policy (str): Cache eviction policy.
            Must be one of: "lru", "lfu", "fifo". Defaults to "lru".
        enable_metrics (bool): Enable cache performance metrics.
            Defaults to True.
    """
    
    ttl_seconds: int = DEFAULT_CACHE_TTL
    max_size: int = DEFAULT_MAX_CACHE_SIZE
    cleanup_interval: int = DEFAULT_CLEANUP_INTERVAL
    enable_persistence: bool = True
    cache_directory: str = "./cache"
    compression_enabled: bool = True
    eviction_policy: str = "lru"
    enable_metrics: bool = True


@dataclass
class CacheEntry:
    """
    Cache entry for processed file data.
    
    Attributes:
        key (str): Unique cache key.
        data (Any): Cached data (FileProcessingResult, ProcessingBlock, etc.).
        created_at (datetime): Entry creation timestamp.
        last_accessed (datetime): Last access timestamp.
        access_count (int): Number of times accessed.
        size_bytes (int): Size of cached data in bytes.
        metadata (Dict[str, Any]): Additional metadata.
    """
    
    key: str
    data: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheMetrics:
    """
    Cache performance metrics.
    
    Attributes:
        total_requests (int): Total cache requests.
        cache_hits (int): Number of cache hits.
        cache_misses (int): Number of cache misses.
        hit_rate (float): Cache hit rate (0.0 to 1.0).
        total_size_bytes (int): Total cache size in bytes.
        entry_count (int): Number of cache entries.
        eviction_count (int): Number of evicted entries.
        average_access_time_ms (float): Average access time in milliseconds.
    """
    
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    total_size_bytes: int = 0
    entry_count: int = 0
    eviction_count: int = 0
    average_access_time_ms: float = 0.0


class ProcessingCache:
    """
    Processing Cache - File Processing Cache Management System
    
    Provides intelligent caching for file processing results, chunking operations,
    and vector embeddings with configurable TTL and eviction policies.
    
    The cache system stores processed file metadata, chunking results, and
    embeddings to avoid redundant processing and improve system performance.
    
    Attributes:
        config (CacheConfig): Cache configuration.
        cache_store (Dict[str, CacheEntry]): In-memory cache store.
        metrics (CacheMetrics): Cache performance metrics.
        is_initialized (bool): Whether cache is initialized.
        cleanup_task (Optional[asyncio.Task]): Background cleanup task.
    """
    
    def __init__(self, config: CacheConfig):
        """
        Initialize ProcessingCache instance.
        
        Args:
            config (CacheConfig): Cache configuration.
                Must be valid CacheConfig instance.
        
        Raises:
            ValueError: If config parameters are invalid
        """
        if config.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if config.max_size <= 0:
            raise ValueError("max_size must be positive")
        if config.cleanup_interval <= 0:
            raise ValueError("cleanup_interval must be positive")
        if config.eviction_policy not in ["lru", "lfu", "fifo"]:
            raise ValueError("eviction_policy must be one of: lru, lfu, fifo")
        
        self.config = config
        self.cache_store: Dict[str, CacheEntry] = {}
        self.metrics = CacheMetrics()
        self.is_initialized = False
        self.cleanup_task: Optional[asyncio.Task] = None
        self._access_times: List[Tuple[datetime, str]] = []  # For LRU tracking
        
        logger.info(f"ProcessingCache initialized with config: {config}")
    
    async def initialize(self) -> bool:
        """
        Initialize cache system.
        
        Sets up cache storage, loads persistent data if enabled,
        and starts background cleanup task.
        
        Returns:
            bool: True if initialization successful, False otherwise.
        
        Raises:
            RuntimeError: If initialization fails
            PermissionError: If cache directory access is denied
        """
        try:
            # Create cache directory if persistence is enabled
            if self.config.enable_persistence:
                cache_path = Path(self.config.cache_directory)
                cache_path.mkdir(parents=True, exist_ok=True)
                
                # Load persisted cache
                await self.load_persisted_cache()
            
            # Start background cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.is_initialized = True
            logger.info("ProcessingCache initialized successfully")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission denied for cache directory: {e}")
            raise PermissionError("Cache directory access denied") from e
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            raise RuntimeError(f"Cache initialization failed: {e}") from e
    
    async def cleanup(self) -> bool:
        """
        Clean up cache resources.
        
        Stops background tasks, saves persistent data if enabled,
        and releases all cache resources.
        
        Returns:
            bool: True if cleanup successful, False otherwise.
        
        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            # Stop cleanup task
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Persist cache if enabled
            if self.config.enable_persistence:
                await self.persist_cache()
            
            # Clear cache store
            self.cache_store.clear()
            self.is_initialized = False
            
            logger.info("ProcessingCache cleanup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")
            raise RuntimeError(f"Cache cleanup failed: {e}") from e
    
    async def set(self, key: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store data in cache.
        
        Stores data with the given key, applying TTL and eviction policies
        as configured. Updates access metrics and metadata.
        
        Args:
            key (str): Unique cache key.
                Must be non-empty string.
            data (Any): Data to cache (FileProcessingResult, ProcessingBlock, etc.).
                Must be serializable.
            metadata (Optional[Dict[str, Any]]): Additional metadata.
                Defaults to None.
        
        Returns:
            bool: True if data stored successfully, False otherwise.
        
        Raises:
            ValueError: If key is empty or data is not serializable
            MemoryError: If cache size limit is exceeded
            RuntimeError: If storage operation fails
        """
        if not key:
            raise ValueError("Cache key cannot be empty")
        
        try:
            # Check if data is serializable
            if self.config.enable_persistence:
                try:
                    pickle.dumps(data)
                except (pickle.PickleError, TypeError) as e:
                    raise ValueError(f"Data is not serializable: {e}")
            
            # Calculate data size
            size_bytes = len(pickle.dumps(data)) if self.config.enable_persistence else 0
            
            # Check cache size limit
            if len(self.cache_store) >= self.config.max_size:
                await self._evict_entries(1)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                data=data,
                size_bytes=size_bytes,
                metadata=metadata or {}
            )
            
            # Store entry
            self.cache_store[key] = entry
            self._update_access_time(key)
            
            # Update metrics
            self.metrics.total_size_bytes += size_bytes
            self.metrics.entry_count = len(self.cache_store)
            
            logger.debug(f"Stored cache entry: {key} ({size_bytes} bytes)")
            return True
            
        except (ValueError, MemoryError):
            raise
        except Exception as e:
            logger.error(f"Failed to store cache entry {key}: {e}")
            raise RuntimeError(f"Cache storage failed: {e}") from e
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from cache.
        
        Retrieves data with the given key, updating access metrics
        and checking TTL validity.
        
        Args:
            key (str): Cache key to retrieve.
                Must be non-empty string.
        
        Returns:
            Optional[Any]: Cached data if found and valid, None otherwise.
        
        Raises:
            ValueError: If key is empty
            RuntimeError: If retrieval operation fails
        """
        if not key:
            raise ValueError("Cache key cannot be empty")
        
        start_time = time.time()
        
        try:
            self.metrics.total_requests += 1
            
            # Check if key exists
            if key not in self.cache_store:
                self.metrics.cache_misses += 1
                self._update_metrics()
                return None
            
            entry = self.cache_store[key]
            
            # Check TTL
            if self._is_expired(entry):
                await self.delete(key)
                self.metrics.cache_misses += 1
                self._update_metrics()
                return None
            
            # Update access metrics
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            self._update_access_time(key)
            
            self.metrics.cache_hits += 1
            self._update_metrics()
            
            access_time_ms = (time.time() - start_time) * 1000
            logger.debug(f"Cache hit: {key} (access time: {access_time_ms:.2f}ms)")
            
            return entry.data
            
        except Exception as e:
            logger.error(f"Failed to retrieve cache entry {key}: {e}")
            raise RuntimeError(f"Cache retrieval failed: {e}") from e
    
    async def delete(self, key: str) -> bool:
        """
        Remove data from cache.
        
        Removes data with the given key from cache and updates metrics.
        
        Args:
            key (str): Cache key to remove.
                Must be non-empty string.
        
        Returns:
            bool: True if data removed successfully, False otherwise.
        
        Raises:
            ValueError: If key is empty
            RuntimeError: If deletion operation fails
        """
        if not key:
            raise ValueError("Cache key cannot be empty")
        
        try:
            if key in self.cache_store:
                entry = self.cache_store[key]
                self.metrics.total_size_bytes -= entry.size_bytes
                del self.cache_store[key]
                self.metrics.entry_count = len(self.cache_store)
                
                # Remove from access times
                self._access_times = [(t, k) for t, k in self._access_times if k != key]
                
                logger.debug(f"Deleted cache entry: {key}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete cache entry {key}: {e}")
            raise RuntimeError(f"Cache deletion failed: {e}") from e
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Checks if the given key exists in cache and is not expired.
        
        Args:
            key (str): Cache key to check.
                Must be non-empty string.
        
        Returns:
            bool: True if key exists and is valid, False otherwise.
        
        Raises:
            ValueError: If key is empty
        """
        if not key:
            raise ValueError("Cache key cannot be empty")
        
        if key not in self.cache_store:
            return False
        
        entry = self.cache_store[key]
        return not self._is_expired(entry)
    
    async def clear(self) -> bool:
        """
        Clear all cache data.
        
        Removes all entries from cache and resets metrics.
        
        Returns:
            bool: True if cache cleared successfully, False otherwise.
        
        Raises:
            RuntimeError: If clear operation fails
        """
        try:
            self.cache_store.clear()
            self._access_times.clear()
            self.metrics = CacheMetrics()
            
            logger.info("Cache cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise RuntimeError(f"Cache clear failed: {e}") from e
    
    async def get_metrics(self) -> CacheMetrics:
        """
        Get cache performance metrics.
        
        Returns current cache performance metrics including
        hit rate, size, and access statistics.
        
        Returns:
            CacheMetrics: Current cache metrics.
        
        Raises:
            RuntimeError: If metrics cannot be retrieved
        """
        try:
            self._update_metrics()
            return self.metrics
            
        except Exception as e:
            logger.error(f"Failed to get cache metrics: {e}")
            raise RuntimeError(f"Failed to get metrics: {e}") from e
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        Get detailed cache information.
        
        Returns comprehensive cache information including
        configuration, metrics, and status.
        
        Returns:
            Dict[str, Any]: Detailed cache information.
                Format: {
                    "config": CacheConfig,
                    "metrics": CacheMetrics,
                    "status": str,
                    "size_info": Dict[str, Any]
                }
        
        Raises:
            RuntimeError: If information cannot be retrieved
        """
        try:
            metrics = await self.get_metrics()
            
            size_info = {
                "total_entries": len(self.cache_store),
                "total_size_mb": self.metrics.total_size_bytes / (1024 * 1024),
                "average_entry_size_bytes": (
                    self.metrics.total_size_bytes / len(self.cache_store) 
                    if len(self.cache_store) > 0 else 0
                ),
                "max_size": self.config.max_size,
                "utilization_percent": (len(self.cache_store) / self.config.max_size) * 100
            }
            
            info = {
                "config": self.config,
                "metrics": metrics,
                "status": "initialized" if self.is_initialized else "not_initialized",
                "size_info": size_info
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            raise RuntimeError(f"Failed to get cache info: {e}") from e
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Removes all expired entries from cache based on TTL
        and returns the number of removed entries.
        
        Returns:
            int: Number of expired entries removed.
        
        Raises:
            RuntimeError: If cleanup operation fails
        """
        try:
            expired_keys = []
            current_time = datetime.now()
            
            for key, entry in self.cache_store.items():
                if self._is_expired(entry):
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                await self.delete(key)
            
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
            raise RuntimeError(f"Cleanup failed: {e}") from e
    
    async def evict_entries(self, count: int) -> int:
        """
        Evict cache entries based on policy.
        
        Evicts the specified number of entries based on the
        configured eviction policy (LRU, LFU, FIFO).
        
        Args:
            count (int): Number of entries to evict.
                Must be positive integer.
        
        Returns:
            int: Number of entries actually evicted.
        
        Raises:
            ValueError: If count is not positive
            RuntimeError: If eviction operation fails
        """
        if count <= 0:
            raise ValueError("Count must be positive")
        
        try:
            return await self._evict_entries(count)
            
        except Exception as e:
            logger.error(f"Failed to evict entries: {e}")
            raise RuntimeError(f"Eviction failed: {e}") from e
    
    async def persist_cache(self) -> bool:
        """
        Persist cache to disk.
        
        Saves cache data to disk if persistence is enabled.
        
        Returns:
            bool: True if persistence successful, False otherwise.
        
        Raises:
            RuntimeError: If persistence operation fails
            PermissionError: If disk access is denied
        """
        if not self.config.enable_persistence:
            return True
        
        try:
            cache_path = Path(self.config.cache_directory)
            cache_file = cache_path / "cache_data.pkl"
            
            # Prepare data for persistence
            cache_data = {
                "entries": {},
                "metrics": self.metrics,
                "timestamp": datetime.now()
            }
            
            # Serialize entries
            for key, entry in self.cache_store.items():
                if not self._is_expired(entry):
                    cache_data["entries"][key] = {
                        "data": entry.data,
                        "created_at": entry.created_at,
                        "last_accessed": entry.last_accessed,
                        "access_count": entry.access_count,
                        "size_bytes": entry.size_bytes,
                        "metadata": entry.metadata
                    }
            
            # Save to file
            with open(cache_file, 'wb') as f:
                if self.config.compression_enabled:
                    pickle.dump(cache_data, gzip.open(f, 'wb'))
                else:
                    pickle.dump(cache_data, f)
            
            logger.info(f"Cache persisted to {cache_file}")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission denied for cache persistence: {e}")
            raise PermissionError("Disk access denied for cache persistence") from e
        except Exception as e:
            logger.error(f"Failed to persist cache: {e}")
            raise RuntimeError(f"Cache persistence failed: {e}") from e
    
    async def load_persisted_cache(self) -> bool:
        """
        Load cache from disk.
        
        Loads cache data from disk if persistence is enabled.
        
        Returns:
            bool: True if loading successful, False otherwise.
        
        Raises:
            RuntimeError: If loading operation fails
            FileNotFoundError: If cache file doesn't exist
        """
        if not self.config.enable_persistence:
            return True
        
        try:
            cache_path = Path(self.config.cache_directory)
            cache_file = cache_path / "cache_data.pkl"
            
            if not cache_file.exists():
                logger.info("No persisted cache file found")
                return True
            
            # Load from file
            with open(cache_file, 'rb') as f:
                if self.config.compression_enabled:
                    cache_data = pickle.load(gzip.open(f, 'rb'))
                else:
                    cache_data = pickle.load(f)
            
            # Restore entries
            for key, entry_data in cache_data["entries"].items():
                entry = CacheEntry(
                    key=key,
                    data=entry_data["data"],
                    created_at=entry_data["created_at"],
                    last_accessed=entry_data["last_accessed"],
                    access_count=entry_data["access_count"],
                    size_bytes=entry_data["size_bytes"],
                    metadata=entry_data["metadata"]
                )
                self.cache_store[key] = entry
                self._update_access_time(key)
            
            # Restore metrics
            if "metrics" in cache_data:
                self.metrics = cache_data["metrics"]
            
            logger.info(f"Loaded {len(cache_data['entries'])} cache entries from {cache_file}")
            return True
            
        except FileNotFoundError:
            logger.info("Cache file not found, starting with empty cache")
            return True
        except Exception as e:
            logger.error(f"Failed to load persisted cache: {e}")
            raise RuntimeError(f"Cache loading failed: {e}") from e
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while self.is_initialized:
            try:
                await self.cleanup_expired()
                await asyncio.sleep(self.config.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _evict_entries(self, count: int) -> int:
        """Internal method to evict entries based on policy."""
        if len(self.cache_store) == 0:
            return 0
        
        # Sort entries based on eviction policy
        if self.config.eviction_policy == "lru":
            # Sort by last access time
            sorted_entries = sorted(
                self.cache_store.items(),
                key=lambda x: x[1].last_accessed
            )
        elif self.config.eviction_policy == "lfu":
            # Sort by access count
            sorted_entries = sorted(
                self.cache_store.items(),
                key=lambda x: x[1].access_count
            )
        else:  # fifo
            # Sort by creation time
            sorted_entries = sorted(
                self.cache_store.items(),
                key=lambda x: x[1].created_at
            )
        
        # Evict entries
        evicted_count = 0
        for key, _ in sorted_entries[:count]:
            if await self.delete(key):
                evicted_count += 1
                self.metrics.eviction_count += 1
        
        return evicted_count
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        current_time = datetime.now()
        expiration_time = entry.created_at + timedelta(seconds=self.config.ttl_seconds)
        return current_time > expiration_time
    
    def _update_access_time(self, key: str):
        """Update access time for LRU tracking."""
        current_time = datetime.now()
        # Remove existing entry
        self._access_times = [(t, k) for t, k in self._access_times if k != key]
        # Add new entry
        self._access_times.append((current_time, key))
    
    def _update_metrics(self):
        """Update cache metrics."""
        if self.metrics.total_requests > 0:
            self.metrics.hit_rate = self.metrics.cache_hits / self.metrics.total_requests 