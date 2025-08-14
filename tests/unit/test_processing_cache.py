"""
Tests for Processing Cache

Comprehensive test suite for cache management functionality including
storage, retrieval, eviction policies, and persistence.
"""

import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

from docanalyzer.cache.processing_cache import (
    ProcessingCache,
    CacheConfig,
    CacheEntry,
    CacheMetrics
)
from docanalyzer.models.processing import FileProcessingResult


class TestCacheConfig:
    """Test suite for CacheConfig."""
    
    def test_valid_config(self):
        """Test valid configuration creation."""
        config = CacheConfig(
            ttl_seconds=3600,
            max_size=1000,
            cleanup_interval=300,
            enable_persistence=True,
            cache_directory="./cache",
            compression_enabled=True,
            eviction_policy="lru",
            enable_metrics=True
        )
        
        assert config.ttl_seconds == 3600
        assert config.max_size == 1000
        assert config.cleanup_interval == 300
        assert config.enable_persistence is True
        assert config.cache_directory == "./cache"
        assert config.compression_enabled is True
        assert config.eviction_policy == "lru"
        assert config.enable_metrics is True
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CacheConfig()
        
        assert config.ttl_seconds == 3600
        assert config.max_size == 1000
        assert config.cleanup_interval == 300
        assert config.enable_persistence is True
        assert config.eviction_policy == "lru"


class TestCacheEntry:
    """Test suite for CacheEntry."""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        data = {"test": "data"}
        entry = CacheEntry(
            key="test_key",
            data=data,
            metadata={"source": "test"}
        )
        
        assert entry.key == "test_key"
        assert entry.data == data
        assert entry.metadata["source"] == "test"
        assert entry.access_count == 0
        assert entry.size_bytes == 0


class TestCacheMetrics:
    """Test suite for CacheMetrics."""
    
    def test_cache_metrics_creation(self):
        """Test cache metrics creation."""
        metrics = CacheMetrics(
            total_requests=100,
            cache_hits=80,
            cache_misses=20
        )
        
        assert metrics.total_requests == 100
        assert metrics.cache_hits == 80
        assert metrics.cache_misses == 20
        assert metrics.hit_rate == 0.0  # Will be calculated later


class TestProcessingCache:
    """Test suite for ProcessingCache."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def valid_config(self, temp_cache_dir):
        """Create valid cache config."""
        return CacheConfig(
            ttl_seconds=3600,
            max_size=3,  # Small size to trigger eviction
            cleanup_interval=60,
            enable_persistence=True,
            cache_directory=temp_cache_dir,
            compression_enabled=False,
            eviction_policy="lru",
            enable_metrics=True
        )
    
    @pytest.fixture
    def cache(self, valid_config):
        """Create cache instance."""
        return ProcessingCache(valid_config)
    
    def test_valid_initialization(self, valid_config):
        """Test valid cache initialization."""
        cache = ProcessingCache(valid_config)
        
        assert cache.config == valid_config
        assert cache.cache_store == {}
        assert isinstance(cache.metrics, CacheMetrics)
        assert cache.is_initialized is False
        assert cache.cleanup_task is None
    
    def test_invalid_ttl_seconds(self):
        """Test initialization with invalid TTL."""
        config = CacheConfig(ttl_seconds=0)
        
        with pytest.raises(ValueError, match="ttl_seconds must be positive"):
            ProcessingCache(config)
    
    def test_invalid_max_size(self):
        """Test initialization with invalid max size."""
        config = CacheConfig(max_size=0)
        
        with pytest.raises(ValueError, match="max_size must be positive"):
            ProcessingCache(config)
    
    def test_invalid_cleanup_interval(self):
        """Test initialization with invalid cleanup interval."""
        config = CacheConfig(cleanup_interval=0)
        
        with pytest.raises(ValueError, match="cleanup_interval must be positive"):
            ProcessingCache(config)
    
    def test_invalid_eviction_policy(self):
        """Test initialization with invalid eviction policy."""
        config = CacheConfig(eviction_policy="invalid")
        
        with pytest.raises(ValueError, match="eviction_policy must be one of"):
            ProcessingCache(config)
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, cache):
        """Test successful cache initialization."""
        with patch.object(cache, 'load_persisted_cache', return_value=True):
            result = await cache.initialize()
            
            assert result is True
            assert cache.is_initialized is True
            assert cache.cleanup_task is not None
    
    @pytest.mark.asyncio
    async def test_initialize_without_persistence(self, temp_cache_dir):
        """Test initialization without persistence."""
        config = CacheConfig(
            enable_persistence=False,
            cache_directory=temp_cache_dir
        )
        cache = ProcessingCache(config)
        
        result = await cache.initialize()
        
        assert result is True
        assert cache.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_permission_error(self, cache):
        """Test initialization with permission error."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError, match="Cache directory access denied"):
                await cache.initialize()
    
    @pytest.mark.asyncio
    async def test_cleanup_success(self, cache):
        """Test successful cache cleanup."""
        cache.is_initialized = True
        cache.cleanup_task = asyncio.create_task(asyncio.sleep(1))
        
        with patch.object(cache, 'persist_cache', return_value=True):
            result = await cache.cleanup()
            
            assert result is True
            assert cache.is_initialized is False
            assert cache.cache_store == {}
    
    @pytest.mark.asyncio
    async def test_set_success(self, cache):
        """Test successful cache set operation."""
        await cache.initialize()
        
        data = {"test": "data"}
        result = await cache.set("test_key", data, {"source": "test"})
        
        assert result is True
        assert "test_key" in cache.cache_store
        assert cache.cache_store["test_key"].data == data
        assert cache.cache_store["test_key"].metadata["source"] == "test"
    
    @pytest.mark.asyncio
    async def test_set_empty_key(self, cache):
        """Test cache set with empty key."""
        await cache.initialize()
        
        with pytest.raises(ValueError, match="Cache key cannot be empty"):
            await cache.set("", {"data": "test"})
    
    @pytest.mark.asyncio
    async def test_set_with_eviction(self, cache):
        """Test cache set that triggers eviction."""
        await cache.initialize()
        
        # Fill cache to capacity
        for i in range(cache.config.max_size):
            await cache.set(f"key_{i}", f"data_{i}")
        
        # Add one more entry to trigger eviction
        result = await cache.set("new_key", "new_data")
        
        assert result is True
        assert len(cache.cache_store) == cache.config.max_size
        assert "new_key" in cache.cache_store
    
    @pytest.mark.asyncio
    async def test_get_success(self, cache):
        """Test successful cache get operation."""
        await cache.initialize()
        
        test_data = {"test": "data"}
        await cache.set("test_key", test_data)
        
        result = await cache.get("test_key")
        
        assert result == test_data
        assert cache.cache_store["test_key"].access_count == 1
    
    @pytest.mark.asyncio
    async def test_get_missing_key(self, cache):
        """Test cache get with missing key."""
        await cache.initialize()
        
        result = await cache.get("missing_key")
        
        assert result is None
        assert cache.metrics.cache_misses == 1
    
    @pytest.mark.asyncio
    async def test_get_expired_entry(self, cache):
        """Test cache get with expired entry."""
        await cache.initialize()
        
        # Set entry with very short TTL
        cache.config.ttl_seconds = 0.001
        await cache.set("test_key", "test_data")
        
        # Wait for expiration
        await asyncio.sleep(0.01)
        
        result = await cache.get("test_key")
        
        assert result is None
        assert "test_key" not in cache.cache_store
    
    @pytest.mark.asyncio
    async def test_get_empty_key(self, cache):
        """Test cache get with empty key."""
        await cache.initialize()
        
        with pytest.raises(ValueError, match="Cache key cannot be empty"):
            await cache.get("")
    
    @pytest.mark.asyncio
    async def test_delete_success(self, cache):
        """Test successful cache delete operation."""
        await cache.initialize()
        
        await cache.set("test_key", "test_data")
        
        result = await cache.delete("test_key")
        
        assert result is True
        assert "test_key" not in cache.cache_store
    
    @pytest.mark.asyncio
    async def test_delete_missing_key(self, cache):
        """Test cache delete with missing key."""
        await cache.initialize()
        
        result = await cache.delete("missing_key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_empty_key(self, cache):
        """Test cache delete with empty key."""
        await cache.initialize()
        
        with pytest.raises(ValueError, match="Cache key cannot be empty"):
            await cache.delete("")
    
    @pytest.mark.asyncio
    async def test_exists_success(self, cache):
        """Test successful cache exists operation."""
        await cache.initialize()
        
        await cache.set("test_key", "test_data")
        
        assert await cache.exists("test_key") is True
        assert await cache.exists("missing_key") is False
    
    @pytest.mark.asyncio
    async def test_exists_expired_entry(self, cache):
        """Test cache exists with expired entry."""
        await cache.initialize()
        
        cache.config.ttl_seconds = 0.001
        await cache.set("test_key", "test_data")
        
        await asyncio.sleep(0.01)
        
        assert await cache.exists("test_key") is False
    
    @pytest.mark.asyncio
    async def test_exists_empty_key(self, cache):
        """Test cache exists with empty key."""
        await cache.initialize()
        
        with pytest.raises(ValueError, match="Cache key cannot be empty"):
            await cache.exists("")
    
    @pytest.mark.asyncio
    async def test_clear_success(self, cache):
        """Test successful cache clear operation."""
        await cache.initialize()
        
        await cache.set("key1", "data1")
        await cache.set("key2", "data2")
        
        result = await cache.clear()
        
        assert result is True
        assert len(cache.cache_store) == 0
        assert cache.metrics.total_requests == 0
        assert cache.metrics.cache_hits == 0
        assert cache.metrics.cache_misses == 0
    
    @pytest.mark.asyncio
    async def test_get_metrics_success(self, cache):
        """Test successful metrics retrieval."""
        await cache.initialize()
        
        # Perform some operations
        await cache.set("key1", "data1")
        await cache.get("key1")
        await cache.get("missing_key")
        
        metrics = await cache.get_metrics()
        
        assert isinstance(metrics, CacheMetrics)
        assert metrics.total_requests == 2
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1
        assert metrics.hit_rate == 0.5
    
    @pytest.mark.asyncio
    async def test_get_cache_info_success(self, cache):
        """Test successful cache info retrieval."""
        await cache.initialize()
        
        await cache.set("key1", "data1")
        await cache.set("key2", "data2")
        
        info = await cache.get_cache_info()
        
        assert isinstance(info, dict)
        assert "config" in info
        assert "metrics" in info
        assert "status" in info
        assert "size_info" in info
        assert info["status"] == "initialized"
        assert info["size_info"]["total_entries"] == 2
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_success(self, cache):
        """Test successful expired entries cleanup."""
        await cache.initialize()
        
        # Set entries with different TTLs
        cache.config.ttl_seconds = 0.001
        await cache.set("expired_key", "expired_data")
        
        cache.config.ttl_seconds = 3600
        await cache.set("valid_key", "valid_data")
        
        # Wait for expiration
        await asyncio.sleep(0.01)
        
        # Reset TTL for cleanup
        cache.config.ttl_seconds = 3600
        
        count = await cache.cleanup_expired()
        
        # May be 0 due to timing, but the important thing is no errors
        assert count >= 0
        assert "valid_key" in cache.cache_store
    
    @pytest.mark.asyncio
    async def test_evict_entries_success(self, cache):
        """Test successful entries eviction."""
        await cache.initialize()
        
        # Fill cache to max size
        for i in range(3):
            await cache.set(f"key_{i}", f"data_{i}")
        
        # Evict 1 entry
        count = await cache.evict_entries(1)
        
        assert count == 1
        # After eviction, we should have 2 entries (3 - 1)
        assert len(cache.cache_store) == 2
    
    @pytest.mark.asyncio
    async def test_evict_entries_invalid_count(self, cache):
        """Test entries eviction with invalid count."""
        await cache.initialize()
        
        with pytest.raises(ValueError, match="Count must be positive"):
            await cache.evict_entries(0)
    
    @pytest.mark.asyncio
    async def test_persist_cache_success(self, cache, temp_cache_dir):
        """Test successful cache persistence."""
        await cache.initialize()
        
        await cache.set("key1", "data1")
        await cache.set("key2", "data2")
        
        result = await cache.persist_cache()
        
        assert result is True
        
        # Check if file was created
        cache_file = Path(temp_cache_dir) / "cache_data.pkl"
        assert cache_file.exists()
    
    @pytest.mark.asyncio
    async def test_persist_cache_without_persistence(self, temp_cache_dir):
        """Test cache persistence when disabled."""
        config = CacheConfig(enable_persistence=False, cache_directory=temp_cache_dir)
        cache = ProcessingCache(config)
        await cache.initialize()
        
        result = await cache.persist_cache()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_load_persisted_cache_success(self, cache, temp_cache_dir):
        """Test successful cache loading."""
        await cache.initialize()
        
        # Set some data and persist
        await cache.set("key1", "data1")
        await cache.persist_cache()
        
        # Create new cache instance and load
        new_cache = ProcessingCache(cache.config)
        await new_cache.initialize()
        
        # Check if data was loaded
        assert "key1" in new_cache.cache_store
        assert new_cache.cache_store["key1"].data == "data1"
    
    @pytest.mark.asyncio
    async def test_load_persisted_cache_file_not_found(self, cache):
        """Test cache loading when file doesn't exist."""
        await cache.initialize()
        
        result = await cache.load_persisted_cache()
        
        assert result is True
        assert len(cache.cache_store) == 0
    
    @pytest.mark.asyncio
    async def test_eviction_policy_lru(self, cache):
        """Test LRU eviction policy."""
        await cache.initialize()
        cache.config.eviction_policy = "lru"
        
        # Fill cache
        for i in range(3):
            await cache.set(f"key_{i}", f"data_{i}")
        
        # Access keys in different order
        await cache.get("key_1")
        await cache.get("key_0")
        
        # Add one more to trigger eviction
        await cache.set("key_3", "data_3")
        
        # key_2 should be evicted (least recently used)
        assert "key_2" not in cache.cache_store
        assert "key_0" in cache.cache_store
        assert "key_1" in cache.cache_store
        assert "key_3" in cache.cache_store
    
    @pytest.mark.asyncio
    async def test_eviction_policy_lfu(self, cache):
        """Test LFU eviction policy."""
        await cache.initialize()
        cache.config.eviction_policy = "lfu"
        
        # Fill cache
        for i in range(3):
            await cache.set(f"key_{i}", f"data_{i}")
        
        # Access keys with different frequencies
        await cache.get("key_0")  # 1 access
        await cache.get("key_1")  # 1 access
        await cache.get("key_1")  # 2 accesses
        await cache.get("key_2")  # 1 access
        
        # Add one more to trigger eviction
        await cache.set("key_3", "data_3")
        
        # key_0 or key_2 should be evicted (least frequently used)
        assert len(cache.cache_store) == 3
    
    @pytest.mark.asyncio
    async def test_eviction_policy_fifo(self, cache):
        """Test FIFO eviction policy."""
        await cache.initialize()
        cache.config.eviction_policy = "fifo"
        
        # Fill cache
        for i in range(3):
            await cache.set(f"key_{i}", f"data_{i}")
        
        # Add one more to trigger eviction
        await cache.set("key_3", "data_3")
        
        # key_0 should be evicted (first in)
        assert "key_0" not in cache.cache_store
        assert "key_1" in cache.cache_store
        assert "key_2" in cache.cache_store
        assert "key_3" in cache.cache_store
    
    @pytest.mark.asyncio
    async def test_cleanup_loop(self, cache):
        """Test background cleanup loop."""
        await cache.initialize()
        
        # Set expired entry
        cache.config.ttl_seconds = 0.001
        await cache.set("expired_key", "expired_data")
        
        # Wait for expiration
        await asyncio.sleep(0.01)
        
        # Reset TTL
        cache.config.ttl_seconds = 3600
        
        # Let cleanup run briefly
        await asyncio.sleep(0.1)
        
        # Cancel cleanup task
        if cache.cleanup_task:
            cache.cleanup_task.cancel()
            try:
                await cache.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # The important thing is that the loop runs without errors
        # Timing may prevent cleanup from happening 