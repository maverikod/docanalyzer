"""
Base pipeline classes and configurations.

Defines the core abstractions for directory processing pipelines.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
import threading
import asyncio
import logging
from datetime import datetime, timezone

from ..filters.base import BaseFileFilter, FileStructure
from ..filters.registry import FilterRegistry


class PipelineStatus(str, Enum):
    """Pipeline status enumeration."""
    
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class PipelineConfig:
    """Configuration for a directory pipeline."""
    
    # Directory settings
    watch_path: Path
    include_patterns: List[str] = field(default_factory=lambda: ["*"])
    exclude_patterns: List[str] = field(default_factory=list)
    use_gitignore: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Processing settings
    batch_size: int = 10
    max_workers: int = 2
    debounce_delay: float = 1.0
    retry_attempts: int = 3
    retry_delay: float = 5.0
    
    # Vector store settings
    vector_store_url: str = "http://localhost:8007"
    vector_store_timeout: int = 30
    
    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 100
    min_chunk_size: int = 50
    
    # Quality filters
    min_complexity_score: float = 0.0
    min_importance_score: float = 0.1
    
    # Callbacks
    on_file_processed: Optional[Callable] = None
    on_error: Optional[Callable] = None
    on_batch_completed: Optional[Callable] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.watch_path.exists():
            raise ValueError(f"Watch path does not exist: {self.watch_path}")
        
        if not self.watch_path.is_dir():
            raise ValueError(f"Watch path is not a directory: {self.watch_path}")
        
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        
        if self.max_workers <= 0:
            raise ValueError("Max workers must be positive")


@dataclass 
class PipelineStats:
    """Statistics for pipeline execution."""
    
    # Timing
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    total_runtime: float = 0.0
    
    # File processing
    files_processed: int = 0
    files_failed: int = 0
    files_skipped: int = 0
    
    # Block and chunk statistics
    blocks_created: int = 0
    chunks_created: int = 0
    chunks_stored: int = 0
    
    # Size statistics
    total_file_size: int = 0
    total_content_size: int = 0
    
    # Error tracking
    last_error: Optional[str] = None
    error_count: int = 0
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)
    
    def record_file_processed(self, file_size: int, blocks: int, chunks: int):
        """Record successful file processing."""
        self.files_processed += 1
        self.total_file_size += file_size
        self.blocks_created += blocks
        self.chunks_created += chunks
        self.update_activity()
    
    def record_file_failed(self, error: str):
        """Record failed file processing."""
        self.files_failed += 1
        self.error_count += 1
        self.last_error = error
        self.update_activity()
    
    def record_file_skipped(self):
        """Record skipped file."""
        self.files_skipped += 1
        self.update_activity()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "total_runtime": self.total_runtime,
            "files_processed": self.files_processed,
            "files_failed": self.files_failed,
            "files_skipped": self.files_skipped,
            "blocks_created": self.blocks_created,
            "chunks_created": self.chunks_created,
            "chunks_stored": self.chunks_stored,
            "total_file_size": self.total_file_size,
            "total_content_size": self.total_content_size,
            "last_error": self.last_error,
            "error_count": self.error_count
        }


class BasePipeline(ABC):
    """
    Abstract base class for directory processing pipelines.
    
    Each pipeline runs in its own thread and processes files from
    a specific directory using the configured filters and chunkers.
    """
    
    def __init__(self, config: PipelineConfig, pipeline_id: str):
        """
        Initialize the pipeline.
        
        Args:
            config: Pipeline configuration
            pipeline_id: Unique identifier for this pipeline
        """
        self.config = config
        self.pipeline_id = pipeline_id
        self.status = PipelineStatus.IDLE
        self.stats = PipelineStats()
        
        # Threading
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # Components
        self.filter_registry = FilterRegistry()
        self.logger = logging.getLogger(f"pipeline.{pipeline_id}")
        
        # Initialize event loop for async operations
        self.loop: Optional[asyncio.AbstractEventLoop] = None
    
    @abstractmethod
    async def process_file(self, file_path: Path) -> bool:
        """
        Process a single file.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            True if processing was successful
        """
        pass
    
    @abstractmethod
    async def scan_directory(self) -> List[Path]:
        """
        Scan the directory and return files to process.
        
        Returns:
            List of file paths to process
        """
        pass
    
    def start(self) -> None:
        """Start the pipeline in a separate thread."""
        if self.status in [PipelineStatus.RUNNING, PipelineStatus.PAUSED]:
            self.logger.warning(f"Pipeline {self.pipeline_id} is already running")
            return
        
        self.status = PipelineStatus.RUNNING
        self.stats.started_at = datetime.now(timezone.utc)
        self.stop_event.clear()
        self.pause_event.clear()
        
        self.thread = threading.Thread(target=self._run, name=f"pipeline-{self.pipeline_id}")
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info(f"Pipeline {self.pipeline_id} started")
    
    def stop(self) -> None:
        """Stop the pipeline."""
        if self.status == PipelineStatus.STOPPED:
            return
        
        self.logger.info(f"Stopping pipeline {self.pipeline_id}")
        self.status = PipelineStatus.STOPPING
        self.stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
        
        self.status = PipelineStatus.STOPPED
        self.logger.info(f"Pipeline {self.pipeline_id} stopped")
    
    def pause(self) -> None:
        """Pause the pipeline."""
        if self.status == PipelineStatus.RUNNING:
            self.status = PipelineStatus.PAUSED
            self.pause_event.set()
            self.logger.info(f"Pipeline {self.pipeline_id} paused")
    
    def resume(self) -> None:
        """Resume the pipeline."""
        if self.status == PipelineStatus.PAUSED:
            self.status = PipelineStatus.RUNNING
            self.pause_event.clear()
            self.logger.info(f"Pipeline {self.pipeline_id} resumed")
    
    def _run(self) -> None:
        """Main pipeline execution loop."""
        try:
            # Create event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Run the async pipeline
            self.loop.run_until_complete(self._async_run())
            
        except Exception as e:
            self.logger.error(f"Pipeline {self.pipeline_id} failed: {e}")
            self.status = PipelineStatus.ERROR
            self.stats.record_file_failed(str(e))
            
            if self.config.on_error:
                self.config.on_error(self.pipeline_id, e)
        
        finally:
            if self.loop:
                self.loop.close()
            self.status = PipelineStatus.STOPPED
    
    async def _async_run(self) -> None:
        """Async pipeline execution."""
        self.logger.info(f"Starting async pipeline {self.pipeline_id}")
        
        while not self.stop_event.is_set():
            try:
                # Check if paused
                if self.pause_event.is_set():
                    await asyncio.sleep(1)
                    continue
                
                # Scan for files to process
                files_to_process = await self.scan_directory()
                
                if not files_to_process:
                    await asyncio.sleep(self.config.debounce_delay)
                    continue
                
                # Process files in batches
                for i in range(0, len(files_to_process), self.config.batch_size):
                    if self.stop_event.is_set():
                        break
                    
                    batch = files_to_process[i:i + self.config.batch_size]
                    await self._process_batch(batch)
                    
                    # Callback for batch completion
                    if self.config.on_batch_completed:
                        self.config.on_batch_completed(self.pipeline_id, len(batch))
                
                # Wait before next scan
                await asyncio.sleep(self.config.debounce_delay)
                
            except Exception as e:
                self.logger.error(f"Error in pipeline {self.pipeline_id}: {e}")
                self.stats.record_file_failed(str(e))
                await asyncio.sleep(self.config.retry_delay)
    
    async def _process_batch(self, files: List[Path]) -> None:
        """Process a batch of files."""
        tasks = []
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def process_with_semaphore(file_path: Path) -> bool:
            async with semaphore:
                return await self.process_file(file_path)
        
        # Create tasks for concurrent processing
        for file_path in files:
            task = asyncio.create_task(process_with_semaphore(file_path))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        successful = sum(1 for result in results if result is True)
        failed = len(results) - successful
        
        self.logger.info(
            f"Batch processed: {successful} successful, {failed} failed"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status and statistics."""
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "config": {
                "watch_path": str(self.config.watch_path),
                "batch_size": self.config.batch_size,
                "max_workers": self.config.max_workers
            },
            "stats": self.stats.to_dict(),
            "thread_alive": self.thread.is_alive() if self.thread else False
        } 