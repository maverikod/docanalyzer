# Стандарты кодирования DocAnalyzer

## 1. Общие принципы кодирования

### 1.1 Языковые стандарты
- **Код, комментарии, докстринги**: ТОЛЬКО английский язык
- **Документация**: билингвальность (русский и английский)
- **Общение с пользователем**: русский язык
- **Переменные, функции, классы**: английские имена

### 1.2 Философия кода
- **Декларативность перед реализацией**: Сначала пишется архитектура с докстрингами
- **Читаемость превыше всего**: Код читается чаще, чем пишется
- **Явное лучше неявного**: Избегать скрытой логики и магических чисел
- **Один способ сделать что-то**: Следовать принципам Python Zen
- **Тестируемость**: Код должен легко покрываться тестами

### 1.3 Архитектурные принципы
- **Асинхронность**: Все операции I/O выполняются асинхронно
- **Модульность**: Четкое разделение ответственности между компонентами
- **Расширяемость**: Возможность добавления новых типов файлов и процессоров
- **Отказоустойчивость**: Обработка ошибок и восстановление после сбоев
- **Наблюдаемость**: Детальное логирование и метрики

## 2. Стандарты именования

### 2.1 Общие правила именования
- **snake_case** для функций, методов, переменных, файлов
- **PascalCase** для классов и исключений
- **UPPER_CASE** для констант и переменных окружения
- **lowercase** для пакетов и модулей
- Использование описательных имен вместо аббревиатур
- Префикс `_` для protected методов/атрибутов
- Префикс `__` для private методов/атрибутов

### 2.2 Классы

#### Основные классы:
```python
class TextBlockChunker:        # Основной функционал
class FileSystemWatcher:       # Составное название
class PipelineManager:         # Менеджер компонентов
class WatchDirectoryManager:   # Длинное но понятное имя
```

#### Абстрактные классы:
```python
class BaseFileFilter(ABC):     # Префикс Base
class AbstractPipeline(ABC):   # Альтернативный префикс
class ICommandHandler(ABC):    # Интерфейс с префиксом I
```

#### Модели данных:
```python
@dataclass
class TextBlock:               # Простое имя сущности
class FileStructure:           # Структура данных  
class ChunkingConfig:          # Конфигурационная модель
class PipelineStats:           # Статистические данные
```

#### Исключения:
```python
class DocAnalyzerError(Exception):         # Базовое исключение
class FilterProcessingError(DocAnalyzerError):  # Специфичное исключение
class VectorStoreConnectionError(DocAnalyzerError):  # Длинное но понятное
```

### 2.3 Методы и функции

#### Публичные методы:
```python
def process_file(self, file_path: Path) -> FileStructure:
def start_watching(self, paths: List[Path]) -> None:
def get_processing_status(self) -> Dict[str, Any]:
def validate_configuration(self, config: Dict[str, Any]) -> bool:
```

#### Приватные методы:
```python
def _parse_file_content(self, content: str) -> List[TextBlock]:
def _calculate_complexity_metrics(self, block: TextBlock) -> float:
def _setup_logging_configuration(self) -> None:
def _validate_input_parameters(self, **kwargs) -> None:
```

#### Специальные методы:
```python
def __init__(self, config: ConfigType) -> None:
def __str__(self) -> str:
def __repr__(self) -> str:
def __enter__(self) -> 'ClassName':
def __exit__(self, exc_type, exc_val, exc_tb) -> None:
```

#### Фабричные методы:
```python
@classmethod
def from_config_file(cls, config_path: Path) -> 'ClassName':
@classmethod
def create_default(cls) -> 'ClassName':

@staticmethod
def parse_configuration(data: Dict[str, Any]) -> ConfigType:
@staticmethod
def validate_file_extension(extension: str) -> bool:
```

### 2.4 Переменные и константы

#### Константы модулей:
```python
# Размеры и лимиты
DEFAULT_CHUNK_SIZE: int = 1000
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
MIN_BLOCK_LENGTH: int = 50
MAX_CONCURRENT_WORKERS: int = 10

# Конфигурационные значения
DEFAULT_CONFIG_FILENAME: str = '.docanalyzer.json'
SUPPORTED_TEXT_EXTENSIONS: List[str] = ['.txt', '.md', '.rst']
SUPPORTED_CODE_EXTENSIONS: List[str] = ['.py', '.js', '.ts', '.java']

# Временные интервалы
DEFAULT_WATCH_DEBOUNCE_SECONDS: float = 1.0
WDD_CLEANUP_INTERVAL_SECONDS: int = 3600
HEALTH_CHECK_TIMEOUT_SECONDS: int = 30
```

#### Переменные окружения:
```python
# Конфигурация приложения
DOCANALYZER_CONFIG_PATH: str = os.getenv('DOCANALYZER_CONFIG_PATH', './config.json')
DOCANALYZER_LOG_LEVEL: str = os.getenv('DOCANALYZER_LOG_LEVEL', 'INFO')
DOCANALYZER_DATA_DIR: str = os.getenv('DOCANALYZER_DATA_DIR', './data')

# Внешние сервисы
VECTOR_STORE_URL: str = os.getenv('VECTOR_STORE_URL', 'http://localhost:8007')
VECTOR_STORE_TIMEOUT: int = int(os.getenv('VECTOR_STORE_TIMEOUT', '30'))

# Режимы работы
DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
DEVELOPMENT_MODE: bool = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
```

#### Переменные экземпляра:
```python
class TextBlockChunker:
    def __init__(self, config: ChunkingConfig):
        # Публичные атрибуты (если необходимы)
        self.config = config
        
        # Защищенные атрибуты (для наследования)
        self._chunk_size: int = config.chunk_size
        self._overlap_size: int = config.overlap_size
        self._quality_threshold: float = config.quality_threshold
        
        # Приватные атрибуты (внутреннее состояние)
        self.__processed_files_count: int = 0
        self.__error_count: int = 0
        self.__last_processing_time: Optional[datetime] = None
```

## 3. Структурные стандарты

### 3.1 Структура файла Python

```python
"""
Module Name - Brief Description.

Detailed description of the module purpose, main functionality,
and how it fits into the overall system architecture.

This module provides:
- Component1: Description of primary functionality
- Component2: Description of secondary functionality  
- Component3: Description of utility functionality

Example:
    from docanalyzer.filters import TextFilter
    
    filter = TextFilter(config)
    result = filter.parse_file(Path('document.txt'))

Dependencies:
    - chunk_metadata_adapter: For metadata creation
    - vector_store_client: For vector operations
    - watchdog: For file system monitoring

Author: Developer Name
Email: developer@example.com
Version: 1.0.0
"""

# Standard library imports (alphabetical order)
import asyncio
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

# Third-party imports (alphabetical order)
import aiofiles
from watchdog.observers import Observer

# Local imports (from general to specific)
from docanalyzer.exceptions import DocAnalyzerError, FilterError
from docanalyzer.utils.logging_utils import get_logger
from docanalyzer.utils.validation_utils import validate_file_path

# Type aliases (after imports, before constants)
ConfigDict = Dict[str, Any]
FilePathType = Union[str, Path]
ProcessingCallback = Callable[[Path, bool], None]

# Module-level constants
DEFAULT_TIMEOUT: int = 30
MAX_RETRIES: int = 3
LOGGER = get_logger(__name__)

# Module-level variables (if absolutely necessary)
_global_config: Optional[ConfigDict] = None


class ExampleClass:
    """Class implementation following standards."""
    pass


def main_function() -> None:
    """Main function for CLI entry point."""
    pass


if __name__ == "__main__":
    main_function()
```

### 3.2 Структура класса

```python
class TextBlockChunker:
    """
    Text block chunker for converting structured blocks to semantic chunks.
    
    This class implements intelligent chunking strategies that preserve
    semantic boundaries while optimizing for vector database storage.
    It supports multiple chunking strategies and quality metrics.
    
    Attributes:
        config: Chunking configuration with size and overlap settings
        strategy: Active chunking strategy ('preserve_structure' | 'chunk_by_size')
        metrics: Quality metrics calculator instance
        
    Example:
        config = ChunkingConfig(max_chunk_size=1000, overlap_size=100)
        chunker = TextBlockChunker(config)
        
        chunks = chunker.chunk_file_structure(file_structure)
        for chunk in chunks:
            print(f"Chunk: {chunk.body[:50]}...")
    """
    
    # Class-level constants
    MAX_CHUNK_SIZE: int = 10000
    MIN_CHUNK_SIZE: int = 100
    DEFAULT_QUALITY_THRESHOLD: float = 0.5
    
    # Class variables (shared across instances)
    _instance_count: int = 0
    
    def __init__(self, config: ChunkingConfig) -> None:
        """
        Initialize chunker with configuration.
        
        Args:
            config: Chunking configuration containing size limits,
                   overlap settings, and quality thresholds.
                   
        Raises:
            ValueError: If config contains invalid values
            TypeError: If config is not ChunkingConfig instance
        """
        # Increment class counter
        TextBlockChunker._instance_count += 1
        
        # Validate input
        if not isinstance(config, ChunkingConfig):
            raise TypeError("config must be ChunkingConfig instance")
            
        # Public attributes
        self.config = config
        
        # Protected attributes (for inheritance)
        self._chunk_size: int = config.max_chunk_size
        self._overlap_size: int = config.overlap_size
        self._quality_threshold: float = config.quality_threshold
        self._logger: logging.Logger = get_logger(self.__class__.__name__)
        
        # Private attributes (internal state)
        self.__chunks_created: int = 0
        self.__processing_time: float = 0.0
        self.__last_processed_file: Optional[Path] = None
        
        # Initialize components
        self._setup_logging()
        self._validate_configuration()
    
    # Properties (grouped together)
    @property
    def chunks_created(self) -> int:
        """Get the number of chunks created by this instance."""
        return self.__chunks_created
    
    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time per file."""
        if self.__chunks_created == 0:
            return 0.0
        return self.__processing_time / self.__chunks_created
        
    @property
    def is_configured(self) -> bool:
        """Check if chunker is properly configured."""
        return self._chunk_size > 0 and self._overlap_size >= 0
    
    # Class methods
    @classmethod
    def from_config_dict(cls, config_data: Dict[str, Any]) -> 'TextBlockChunker':
        """
        Create chunker from configuration dictionary.
        
        Args:
            config_data: Dictionary containing configuration parameters
            
        Returns:
            New TextBlockChunker instance
        """
        config = ChunkingConfig.from_dict(config_data)
        return cls(config)
    
    @classmethod
    def get_instance_count(cls) -> int:
        """Get total number of created instances."""
        return cls._instance_count
    
    # Static methods
    @staticmethod
    def validate_chunk_size(size: int) -> bool:
        """
        Validate chunk size parameter.
        
        Args:
            size: Chunk size to validate
            
        Returns:
            True if size is valid, False otherwise
        """
        return TextBlockChunker.MIN_CHUNK_SIZE <= size <= TextBlockChunker.MAX_CHUNK_SIZE
    
    # Public methods (main interface)
    def chunk_file_structure(self, file_structure: FileStructure) -> List[SemanticChunk]:
        """
        Convert file structure to semantic chunks.
        
        Args:
            file_structure: Parsed file structure with text blocks
            
        Returns:
            List of semantic chunks ready for vector storage
            
        Raises:
            ChunkingError: If chunking process fails
            ValueError: If file_structure is invalid
        """
        start_time = time.time()
        
        try:
            self._logger.info(f"Starting chunking for {file_structure.file_path}")
            
            # Validate input
            self._validate_file_structure(file_structure)
            
            # Apply chunking strategy
            chunks = self._apply_chunking_strategy(file_structure.blocks)
            
            # Post-process chunks
            processed_chunks = self._post_process_chunks(chunks, file_structure)
            
            # Update metrics
            self.__chunks_created += len(processed_chunks)
            self.__processing_time += time.time() - start_time
            self.__last_processed_file = file_structure.file_path
            
            self._logger.info(f"Created {len(processed_chunks)} chunks")
            return processed_chunks
            
        except Exception as e:
            self._logger.error(f"Chunking failed: {e}")
            raise ChunkingError(f"Failed to chunk file {file_structure.file_path}: {e}") from e
    
    def get_chunking_statistics(self) -> Dict[str, Any]:
        """
        Get detailed statistics about chunking performance.
        
        Returns:
            Dictionary with chunking statistics and metrics
        """
        return {
            'chunks_created': self.__chunks_created,
            'average_processing_time': self.average_processing_time,
            'last_processed_file': str(self.__last_processed_file) if self.__last_processed_file else None,
            'configuration': self.config.to_dict(),
            'quality_threshold': self._quality_threshold
        }
    
    # Protected methods (for inheritance)
    def _apply_chunking_strategy(self, blocks: List[TextBlock]) -> List[SemanticChunk]:
        """
        Apply configured chunking strategy to text blocks.
        
        Args:
            blocks: List of text blocks to chunk
            
        Returns:
            List of semantic chunks
        """
        if self.config.strategy == 'preserve_structure':
            return self._preserve_structure_strategy(blocks)
        elif self.config.strategy == 'chunk_by_size':
            return self._chunk_by_size_strategy(blocks)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.config.strategy}")
    
    def _preserve_structure_strategy(self, blocks: List[TextBlock]) -> List[SemanticChunk]:
        """Implement structure-preserving chunking strategy."""
        # Implementation here
        pass
    
    def _chunk_by_size_strategy(self, blocks: List[TextBlock]) -> List[SemanticChunk]:
        """Implement size-based chunking strategy."""
        # Implementation here
        pass
    
    # Private methods (internal implementation)
    def __calculate_chunk_quality(self, chunk: SemanticChunk) -> float:
        """Calculate quality score for a chunk."""
        # Implementation here
        pass
    
    def _setup_logging(self) -> None:
        """Setup logging configuration for this instance."""
        # Implementation here
        pass
    
    def _validate_configuration(self) -> None:
        """Validate chunking configuration."""
        # Implementation here
        pass
    
    def _validate_file_structure(self, file_structure: FileStructure) -> None:
        """Validate file structure before processing."""
        # Implementation here
        pass
        
    # Special methods
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"TextBlockChunker(chunks_created={self.__chunks_created})"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (f"TextBlockChunker(config={self.config!r}, "
                f"chunks_created={self.__chunks_created})")
    
    def __enter__(self) -> 'TextBlockChunker':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self._logger.info(f"Chunker processed {self.__chunks_created} chunks")
```

## 4. Декларативный vs Продакшн код

### 4.1 Этапы разработки

#### Этап 1: Декларативный код
```python
def process_file(self, file_path: Path) -> FileStructure:
    """
    Process single file and extract structured blocks.
    
    Analyzes file content using appropriate filter, extracts
    semantic blocks with metadata, and returns structured
    representation suitable for chunking.
    
    Args:
        file_path: Path to file for processing. Must exist
                  and be readable. Supported extensions: .py, .md, .txt
                  
    Returns:
        FileStructure containing extracted blocks with metadata,
        position information, and quality metrics.
        
    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
        FilterError: If file cannot be parsed
        ValueError: If file extension not supported
        
    Example:
        filter = TextFilter()
        structure = filter.process_file(Path('document.md'))
        print(f"Found {len(structure.blocks)} blocks")
    """
    pass
```

#### Этап 2: Продакшн код (замена в том же файле)
```python
def process_file(self, file_path: Path) -> FileStructure:
    """
    Process single file and extract structured blocks.
    
    [Сохраняется полная документация из декларативного кода]
    """
    start_time = time.time()
    
    try:
        # Validate input parameters
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
            
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
            
        # Log processing start
        self._logger.info(f"Processing file: {file_path}")
        
        # Check file size limits
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file_size} bytes")
            
        # Read file content
        content = self._read_file_safely(file_path)
        
        # Apply appropriate filter
        blocks = self._extract_blocks_from_content(content, file_path)
        
        # Create file structure
        file_structure = FileStructure(
            file_path=file_path,
            blocks=blocks,
            metadata=self._extract_file_metadata(file_path),
            processed_at=datetime.now(timezone.utc)
        )
        
        # Calculate metrics
        processing_time = time.time() - start_time
        self._update_processing_metrics(processing_time, len(blocks))
        
        self._logger.info(f"Processed {len(blocks)} blocks in {processing_time:.3f}s")
        return file_structure
        
    except FileNotFoundError:
        self._logger.error(f"File not found: {file_path}")
        raise
    except PermissionError:
        self._logger.error(f"Permission denied: {file_path}")
        raise
    except Exception as e:
        self._logger.error(f"Failed to process file {file_path}: {e}")
        raise FilterError(f"Processing failed for {file_path}") from e
```

### 4.2 Принципы трансформации

1. **Сохранение документации**: Полные докстринги остаются неизменными
2. **Добавление логирования**: Ключевые операции логируются
3. **Обработка ошибок**: Try-catch блоки для всех потенциальных исключений
4. **Валидация входных данных**: Проверка параметров и предусловий
5. **Метрики**: Сбор статистики производительности
6. **Строгая типизация**: Соблюдение типов из сигнатур

## 5. Асинхронное программирование

### 5.1 Стандарты async/await

#### Асинхронные методы:
```python
async def process_file_async(self, file_path: Path) -> FileStructure:
    """
    Asynchronously process file and extract blocks.
    
    Args:
        file_path: Path to file for processing
        
    Returns:
        FileStructure with extracted blocks
    """
    loop = asyncio.get_event_loop()
    
    # I/O operations should be async
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        content = await file.read()
    
    # CPU-bound operations can run in executor
    blocks = await loop.run_in_executor(
        None, 
        self._extract_blocks_from_content, 
        content, 
        file_path
    )
    
    return FileStructure(file_path=file_path, blocks=blocks)

async def process_multiple_files(self, file_paths: List[Path]) -> List[FileStructure]:
    """Process multiple files concurrently."""
    tasks = [self.process_file_async(path) for path in file_paths]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

#### Синхронные обертки:
```python
def process_file(self, file_path: Path) -> FileStructure:
    """Synchronous wrapper for async file processing."""
    if asyncio.iscoroutinefunction(self.process_file_async):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Running in async context
            raise RuntimeError("Use process_file_async in async context")
        else:
            # Running in sync context
            return loop.run_until_complete(self.process_file_async(file_path))
    else:
        return self.process_file_async(file_path)
```

### 5.2 Паттерны конкурентности

#### Worker Pool Pattern:
```python
class AsyncWorkerPool:
    """Asynchronous worker pool for file processing."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        self._active_tasks: Set[asyncio.Task] = set()
    
    async def submit_task(self, coro) -> Any:
        """Submit coroutine to worker pool."""
        async with self.semaphore:
            task = asyncio.create_task(coro)
            self._active_tasks.add(task)
            try:
                return await task
            finally:
                self._active_tasks.discard(task)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown worker pool."""
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
```

#### Producer-Consumer Pattern:
```python
class AsyncFileProcessor:
    """Asynchronous file processor with queue."""
    
    def __init__(self, queue_size: int = 100):
        self.file_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self.result_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
    
    async def producer(self, file_paths: List[Path]) -> None:
        """Produce file paths for processing."""
        for path in file_paths:
            await self.file_queue.put(path)
        await self.file_queue.put(None)  # Sentinel value
    
    async def consumer(self) -> None:
        """Consume and process files."""
        while self._running:
            file_path = await self.file_queue.get()
            if file_path is None:  # Sentinel value
                break
                
            try:
                result = await self.process_file_async(file_path)
                await self.result_queue.put(result)
            except Exception as e:
                await self.result_queue.put(e)
            finally:
                self.file_queue.task_done()
```

## 6. Обработка ошибок

### 6.1 Иерархия исключений

```python
class DocAnalyzerError(Exception):
    """Base exception for all DocAnalyzer errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

class FilterError(DocAnalyzerError):
    """Errors related to file filtering and parsing."""
    pass

class ChunkingError(DocAnalyzerError):
    """Errors related to text chunking process."""
    pass

class PipelineError(DocAnalyzerError):
    """Errors related to pipeline execution."""
    pass

class VectorStoreError(DocAnalyzerError):
    """Errors related to vector store operations."""
    pass

class ConfigurationError(DocAnalyzerError):
    """Errors related to configuration validation."""
    pass
```

### 6.2 Обработка ошибок в методах

```python
def process_file_with_retry(self, file_path: Path, max_retries: int = 3) -> FileStructure:
    """
    Process file with automatic retry on failures.
    
    Args:
        file_path: Path to file for processing
        max_retries: Maximum number of retry attempts
        
    Returns:
        FileStructure with processed content
        
    Raises:
        FilterError: If all retry attempts fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                wait_time = 2 ** attempt  # Exponential backoff
                self._logger.warning(f"Retry {attempt}/{max_retries} for {file_path} "
                                   f"after {wait_time}s delay")
                time.sleep(wait_time)
            
            return self.process_file(file_path)
            
        except FileNotFoundError:
            # Don't retry for file not found
            self._logger.error(f"File not found: {file_path}")
            raise
            
        except PermissionError:
            # Don't retry for permission errors
            self._logger.error(f"Permission denied: {file_path}")
            raise
            
        except (FilterError, IOError) as e:
            # Retry for recoverable errors
            last_exception = e
            self._logger.warning(f"Attempt {attempt + 1} failed for {file_path}: {e}")
            
        except Exception as e:
            # Log unexpected errors but don't retry
            self._logger.error(f"Unexpected error processing {file_path}: {e}")
            raise FilterError(f"Unexpected error: {e}") from e
    
    # All retries exhausted
    self._logger.error(f"All {max_retries} retries failed for {file_path}")
    raise FilterError(f"Failed to process {file_path} after {max_retries} retries") from last_exception
```

### 6.3 Контекстные менеджеры для ресурсов

```python
class FileProcessingContext:
    """Context manager for safe file processing."""
    
    def __init__(self, file_path: Path, logger: logging.Logger):
        self.file_path = file_path
        self.logger = logger
        self.start_time: Optional[float] = None
        self.temp_files: List[Path] = []
    
    def __enter__(self) -> 'FileProcessingContext':
        self.start_time = time.time()
        self.logger.info(f"Starting processing: {self.file_path}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Cleanup temporary files
        for temp_file in self.temp_files:
            try:
                temp_file.unlink(missing_ok=True)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {temp_file}: {e}")
        
        # Log completion/failure
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is None:
            self.logger.info(f"Processing completed in {duration:.3f}s: {self.file_path}")
        else:
            self.logger.error(f"Processing failed after {duration:.3f}s: {self.file_path} - {exc_val}")
    
    def add_temp_file(self, temp_path: Path) -> None:
        """Register temporary file for cleanup."""
        self.temp_files.append(temp_path)

# Usage example
def process_file_safely(self, file_path: Path) -> FileStructure:
    """Process file with automatic resource cleanup."""
    with FileProcessingContext(file_path, self._logger) as context:
        # Processing logic here
        result = self._do_file_processing(file_path)
        return result
```

## 7. Логирование и мониторинг

### 7.1 Конфигурация логирования

```python
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: str = 'INFO',
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup application logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file for log output
        format_string: Custom format string for log messages
        
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(funcName)s - %(message)s'
        )
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module/class."""
    return logging.getLogger(name)
```

### 7.2 Структурированное логирование

```python
import json
from datetime import datetime, timezone
from typing import Any, Dict

class StructuredLogger:
    """Structured logger for machine-readable log output."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_structured(
        self, 
        level: str, 
        message: str, 
        **kwargs: Any
    ) -> None:
        """
        Log structured message with metadata.
        
        Args:
            level: Log level (info, warning, error, etc.)
            message: Human-readable message
            **kwargs: Additional structured data
        """
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level.upper(),
            'message': message,
            'data': kwargs
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_data))
    
    def log_processing_start(self, file_path: Path, **kwargs) -> None:
        """Log start of file processing."""
        self.log_structured(
            'info',
            'Processing started',
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            **kwargs
        )
    
    def log_processing_complete(
        self, 
        file_path: Path, 
        blocks_count: int, 
        duration: float,
        **kwargs
    ) -> None:
        """Log completion of file processing."""
        self.log_structured(
            'info',
            'Processing completed',
            file_path=str(file_path),
            blocks_count=blocks_count,
            duration_seconds=duration,
            **kwargs
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with full context."""
        self.log_structured(
            'error',
            str(error),
            error_type=error.__class__.__name__,
            error_details=getattr(error, 'details', {}),
            context=context
        )
```

## 8. Тестирование

### 8.1 Структура тестов

```python
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from docanalyzer.filters.text_filter import TextFilter
from docanalyzer.exceptions import FilterError

class TestTextFilter:
    """Comprehensive tests for TextFilter class."""
    
    @pytest.fixture
    def text_filter(self):
        """Create TextFilter instance for testing."""
        config = {'chunk_size': 1000, 'overlap': 100}
        return TextFilter(config)
    
    @pytest.fixture
    def sample_text_file(self):
        """Create temporary text file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Sample text content\nfor testing purposes.")
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        temp_path.unlink(missing_ok=True)
    
    def test_process_file_success(self, text_filter, sample_text_file):
        """Test successful file processing."""
        # Act
        result = text_filter.process_file(sample_text_file)
        
        # Assert
        assert isinstance(result, FileStructure)
        assert result.file_path == sample_text_file
        assert len(result.blocks) > 0
        assert all(isinstance(block, TextBlock) for block in result.blocks)
    
    def test_process_file_not_found(self, text_filter):
        """Test processing non-existent file."""
        non_existent_file = Path("/path/that/does/not/exist.txt")
        
        with pytest.raises(FileNotFoundError):
            text_filter.process_file(non_existent_file)
    
    def test_process_file_permission_denied(self, text_filter, tmp_path):
        """Test processing file without read permissions."""
        restricted_file = tmp_path / "restricted.txt"
        restricted_file.write_text("content")
        restricted_file.chmod(0o000)  # No permissions
        
        try:
            with pytest.raises(PermissionError):
                text_filter.process_file(restricted_file)
        finally:
            restricted_file.chmod(0o644)  # Restore permissions for cleanup
    
    @pytest.mark.parametrize("file_content,expected_blocks", [
        ("Single line", 1),
        ("Line 1\nLine 2\nLine 3", 3),
        ("", 0),
    ])
    def test_process_different_content_types(
        self, 
        text_filter, 
        file_content, 
        expected_blocks, 
        tmp_path
    ):
        """Test processing files with different content types."""
        test_file = tmp_path / "test.txt"
        test_file.write_text(file_content)
        
        result = text_filter.process_file(test_file)
        
        assert len(result.blocks) == expected_blocks
    
    @patch('docanalyzer.filters.text_filter.time.time')
    def test_processing_time_tracking(self, mock_time, text_filter, sample_text_file):
        """Test that processing time is tracked correctly."""
        mock_time.side_effect = [1000.0, 1005.0]  # 5 second duration
        
        result = text_filter.process_file(sample_text_file)
        
        assert hasattr(result, 'metadata')
        # Verify timing was calculated (exact assertion depends on implementation)
    
    def test_process_file_with_invalid_encoding(self, text_filter, tmp_path):
        """Test processing file with invalid encoding."""
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_bytes(b'\xFF\xFE\x00\x00')  # Invalid UTF-8
        
        with pytest.raises(FilterError):
            text_filter.process_file(invalid_file)
    
    @pytest.mark.asyncio
    async def test_async_processing(self, text_filter, sample_text_file):
        """Test asynchronous file processing."""
        if hasattr(text_filter, 'process_file_async'):
            result = await text_filter.process_file_async(sample_text_file)
            assert isinstance(result, FileStructure)
    
    def test_thread_safety(self, text_filter, sample_text_file):
        """Test that filter is thread-safe."""
        import threading
        import concurrent.futures
        
        def process_file():
            return text_filter.process_file(sample_text_file)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_file) for _ in range(10)]
            results = [future.result() for future in futures]
        
        assert len(results) == 10
        assert all(isinstance(result, FileStructure) for result in results)
```

### 8.2 Интеграционные тесты

```python
import pytest
import asyncio
from pathlib import Path
from docanalyzer.app import DocAnalyzerApp
from docanalyzer.config import DocAnalyzerConfig

class TestFullPipeline:
    """Integration tests for complete processing pipeline."""
    
    @pytest.fixture
    async def app_instance(self, tmp_path):
        """Create configured DocAnalyzer app instance."""
        config = DocAnalyzerConfig(
            watch_paths=[tmp_path],
            vector_store_url="http://localhost:8007",
            log_level="DEBUG"
        )
        
        app = DocAnalyzerApp(config)
        await app.initialize()
        yield app
        await app.shutdown()
    
    @pytest.fixture
    def test_files(self, tmp_path):
        """Create test files in various formats."""
        files = {}
        
        # Python file
        py_file = tmp_path / "test.py"
        py_file.write_text('''
def hello_world():
    """Say hello to the world."""
    print("Hello, World!")

class TestClass:
    def method(self):
        return "test"
''')
        files['python'] = py_file
        
        # Markdown file
        md_file = tmp_path / "test.md"
        md_file.write_text('''
# Test Document

This is a test document with **bold** text.

## Section 2

- Item 1
- Item 2
''')
        files['markdown'] = md_file
        
        return files
    
    @pytest.mark.integration
    async def test_complete_file_processing(self, app_instance, test_files):
        """Test complete pipeline from file detection to vector storage."""
        # Start watching
        await app_instance.start_watching()
        
        # Wait for files to be processed
        await asyncio.sleep(2)
        
        # Verify processing results
        stats = await app_instance.get_processing_stats()
        assert stats['processed_files'] >= len(test_files)
        assert stats['chunks_created'] > 0
        
        # Verify files are tracked
        for file_path in test_files.values():
            status = await app_instance.get_file_status(file_path)
            assert status['status'] == 'processed'
    
    @pytest.mark.integration
    async def test_error_recovery(self, app_instance, tmp_path):
        """Test error recovery in processing pipeline."""
        # Create problematic file
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("invalid python syntax !!!")
        
        # Start watching
        await app_instance.start_watching()
        await asyncio.sleep(2)
        
        # Verify error handling
        status = await app_instance.get_file_status(bad_file)
        assert status['status'] in ['error', 'failed']
        assert 'error_message' in status
```

### 8.3 Тесты производительности

```python
import pytest
import time
import psutil
import gc
from pathlib import Path

class TestPerformance:
    """Performance and memory tests."""
    
    @pytest.mark.performance
    def test_large_file_processing(self, text_filter, tmp_path):
        """Test processing of large files."""
        # Create large test file (1MB)
        large_file = tmp_path / "large.txt"
        content = "Line of text content.\n" * 50000  # ~1MB
        large_file.write_text(content)
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = text_filter.process_file(large_file)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        processing_time = end_time - start_time
        memory_usage = (end_memory - start_memory) / 1024 / 1024  # MB
        
        # Performance assertions
        assert processing_time < 5.0, f"Processing took {processing_time:.2f}s"
        assert memory_usage < 100, f"Memory usage: {memory_usage:.2f}MB"
        assert len(result.blocks) > 0
        
        # Cleanup
        del result
        gc.collect()
    
    @pytest.mark.performance
    def test_memory_leak_prevention(self, text_filter, tmp_path):
        """Test for memory leaks in repeated processing."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content for memory leak detection.")
        
        initial_memory = psutil.Process().memory_info().rss
        
        # Process file multiple times
        for _ in range(100):
            result = text_filter.process_file(test_file)
            del result
            gc.collect()
        
        final_memory = psutil.Process().memory_info().rss
        memory_growth = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Should not grow significantly
        assert memory_growth < 50, f"Memory grew by {memory_growth:.2f}MB"
```

## 9. Конфигурация и настройки

### 9.1 Класс конфигурации

```python
@dataclass
class DocAnalyzerConfig:
    """
    Main configuration class for DocAnalyzer application.
    
    Contains all configuration parameters with validation
    and default values. Supports loading from files and
    environment variables.
    
    Attributes:
        watch_paths: List of paths to monitor for changes
        vector_store_url: URL of the vector store service
        chunk_size: Maximum size of text chunks in characters
        overlap_size: Overlap between consecutive chunks
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        max_workers: Maximum number of concurrent workers
        file_size_limit: Maximum file size to process in bytes
    """
    
    # Required configuration
    watch_paths: List[Path] = field(default_factory=list)
    vector_store_url: str = "http://localhost:8007"
    
    # Chunking configuration
    chunk_size: int = 1000
    overlap_size: int = 100
    quality_threshold: float = 0.5
    
    # Processing configuration
    max_workers: int = 4
    batch_size: int = 50
    retry_attempts: int = 3
    
    # File handling
    file_size_limit: int = 10 * 1024 * 1024  # 10MB
    supported_extensions: List[str] = field(default_factory=lambda: [
        '.py', '.js', '.ts', '.md', '.txt', '.rst'
    ])
    
    # System configuration
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    debug_mode: bool = False
    
    # External services
    vector_store_timeout: int = 30
    vector_store_retries: int = 3
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_configuration()
        self._normalize_paths()
    
    def _validate_configuration(self) -> None:
        """Validate all configuration parameters."""
        # Validate watch paths
        if not self.watch_paths:
            raise ConfigurationError("At least one watch path must be specified")
        
        for path in self.watch_paths:
            if not path.exists():
                raise ConfigurationError(f"Watch path does not exist: {path}")
            if not path.is_dir():
                raise ConfigurationError(f"Watch path is not a directory: {path}")
        
        # Validate numeric parameters
        if self.chunk_size <= 0:
            raise ConfigurationError("chunk_size must be positive")
        if self.overlap_size < 0:
            raise ConfigurationError("overlap_size cannot be negative")
        if self.overlap_size >= self.chunk_size:
            raise ConfigurationError("overlap_size must be less than chunk_size")
        
        # Validate quality threshold
        if not 0.0 <= self.quality_threshold <= 1.0:
            raise ConfigurationError("quality_threshold must be between 0.0 and 1.0")
        
        # Validate worker configuration
        if self.max_workers <= 0:
            raise ConfigurationError("max_workers must be positive")
        if self.batch_size <= 0:
            raise ConfigurationError("batch_size must be positive")
        
        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_levels:
            raise ConfigurationError(f"Invalid log_level: {self.log_level}")
    
    def _normalize_paths(self) -> None:
        """Normalize and resolve all path configurations."""
        self.watch_paths = [path.resolve() for path in self.watch_paths]
        if self.log_file:
            self.log_file = self.log_file.resolve()
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'DocAnalyzerConfig':
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            DocAnalyzerConfig instance loaded from file
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return cls.from_dict(config_data)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {config_path}: {e}")
    
    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> 'DocAnalyzerConfig':
        """
        Create configuration from dictionary.
        
        Args:
            config_data: Dictionary containing configuration parameters
            
        Returns:
            DocAnalyzerConfig instance
        """
        # Convert string paths to Path objects
        if 'watch_paths' in config_data:
            config_data['watch_paths'] = [Path(p) for p in config_data['watch_paths']]
        if 'log_file' in config_data and config_data['log_file']:
            config_data['log_file'] = Path(config_data['log_file'])
        
        return cls(**config_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        config_dict = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, Path):
                config_dict[field.name] = str(value)
            elif isinstance(value, list) and value and isinstance(value[0], Path):
                config_dict[field.name] = [str(p) for p in value]
            else:
                config_dict[field.name] = value
        return config_dict
    
    def save_to_file(self, config_path: Path) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config_path: Path where to save configuration
        """
        try:
            config_dict = self.to_dict()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config to {config_path}: {e}")
    
    @classmethod
    def from_environment(cls) -> 'DocAnalyzerConfig':
        """
        Load configuration from environment variables.
        
        Environment variables:
            DOCANALYZER_WATCH_PATHS: Comma-separated list of paths
            DOCANALYZER_VECTOR_STORE_URL: Vector store URL
            DOCANALYZER_LOG_LEVEL: Logging level
            DOCANALYZER_CHUNK_SIZE: Chunk size in characters
            [... other environment variables ...]
            
        Returns:
            DocAnalyzerConfig instance from environment
        """
        config_data = {}
        
        # Map environment variables to config fields
        env_mapping = {
            'DOCANALYZER_WATCH_PATHS': ('watch_paths', lambda x: [Path(p.strip()) for p in x.split(',')]),
            'DOCANALYZER_VECTOR_STORE_URL': ('vector_store_url', str),
            'DOCANALYZER_LOG_LEVEL': ('log_level', str),
            'DOCANALYZER_CHUNK_SIZE': ('chunk_size', int),
            'DOCANALYZER_OVERLAP_SIZE': ('overlap_size', int),
            'DOCANALYZER_MAX_WORKERS': ('max_workers', int),
            'DOCANALYZER_DEBUG_MODE': ('debug_mode', lambda x: x.lower() == 'true'),
        }
        
        for env_var, (field_name, converter) in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    config_data[field_name] = converter(env_value)
                except Exception as e:
                    raise ConfigurationError(f"Invalid value for {env_var}: {env_value} - {e}")
        
        return cls(**config_data)
```

## 10. Заключение

### 10.1 Ключевые принципы
- **Последовательность**: Единые стандарты во всем проекте
- **Читаемость**: Код должен быть самодокументируемым
- **Надежность**: Обработка ошибок и graceful degradation
- **Производительность**: Асинхронность и оптимизация ресурсов
- **Тестируемость**: Высокое покрытие тестами и легкость тестирования
- **Наблюдаемость**: Подробное логирование и метрики

### 10.2 Инструменты контроля качества
- **mypy**: Статическая проверка типов
- **pylint**: Анализ качества кода
- **black**: Автоматическое форматирование
- **isort**: Сортировка импортов
- **pytest**: Тестирование с покрытием
- **pre-commit**: Автоматические проверки

### 10.3 Результат
Следование этим стандартам обеспечивает создание высококачественного, поддерживаемого и расширяемого кода, готового для production использования и совместимого с экосистемой Python и PyPI. 