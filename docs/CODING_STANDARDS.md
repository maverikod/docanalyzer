# Стандарты написания кода: Декларативный и Продакшн код

## 1. Определения

### 1.1 Декларативный код
**Декларативный код** - это код с подробными докстрингами и комментариями на английском языке, который содержит объявления классов, переменных, свойств и сигнатур методов без реализации.

**Цель**: Четко определить архитектуру, интерфейсы и контракты системы перед написанием реализации.

### 1.2 Продакшн код  
**Продакшн код** - это полная реализация декларативного кода без `pass` операторов, готовая к использованию в production среде.

**Цель**: Реализовать всю функциональность, описанную в декларативном коде.

## 2. Стандарты декларативного кода

### 2.1 Структура файла

```python
"""
Module Name - Brief Description.

Detailed description of the module purpose, main functionality,
and how it fits into the overall system architecture.

This module provides...
Key components:
- ClassName1: Description
- ClassName2: Description

Example:
    from module_name import ClassName
    instance = ClassName(param1, param2)
    result = instance.method_name()

Author: Developer Name
Email: developer@email.com
Version: 1.0.0
"""

from typing import List, Dict, Optional, Any, Union
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

# Module-level constants
DEFAULT_TIMEOUT: int = 30
MAX_RETRIES: int = 3
```

### 2.2 Класс с декларативным кодом

```python
class ExampleProcessor(ABC):
    """
    Abstract base class for processing data items.
    
    This class defines the interface for all data processors in the system.
    It provides common functionality for validation, error handling, and
    lifecycle management of processing operations.
    
    The processor follows the Template Method pattern, where subclasses
    implement specific processing logic while the base class handles
    common operations like validation and error recovery.
    
    Attributes:
        name: Unique identifier for the processor instance
        config: Configuration dictionary for processor settings
        is_active: Flag indicating if processor is currently active
        processed_count: Number of items successfully processed
        error_count: Number of processing errors encountered
    
    Example:
        class ConcreteProcessor(ExampleProcessor):
            def process_item(self, item):
                # Implementation here
                pass
        
        processor = ConcreteProcessor("my_processor", {"timeout": 30})
        result = processor.process(data_item)
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the processor with name and configuration.
        
        Args:
            name: Unique identifier for this processor instance.
                 Must be non-empty string, max 64 characters.
            config: Configuration dictionary containing processor settings.
                   Required keys: 'timeout', 'max_retries'
                   Optional keys: 'batch_size', 'enable_logging'
        
        Raises:
            ValueError: If name is empty or config is missing required keys
            TypeError: If name is not string or config is not dict
        """
        pass
    
    @property
    def name(self) -> str:
        """
        Get the processor name.
        
        Returns:
            The unique identifier string for this processor instance.
            
        Note:
            This property is read-only after initialization.
        """
        pass
    
    @property
    def is_active(self) -> bool:
        """
        Check if the processor is currently active.
        
        Returns:
            True if processor is running and can accept new items,
            False if processor is stopped, paused, or in error state.
            
        Note:
            Active state is automatically managed based on processor
            lifecycle and error conditions.
        """
        pass
    
    @property
    def processed_count(self) -> int:
        """
        Get the number of successfully processed items.
        
        Returns:
            Integer count of items that were processed without errors
            since the processor was started or last reset.
            
        Note:
            This counter is thread-safe and atomically updated.
        """
        pass
    
    @property
    def error_count(self) -> int:
        """
        Get the number of processing errors encountered.
        
        Returns:
            Integer count of items that failed processing due to
            errors, exceptions, or validation failures.
            
        Note:
            This includes both recoverable and non-recoverable errors.
        """
        pass
    
    def start(self) -> None:
        """
        Start the processor and make it ready to accept items.
        
        Initializes internal state, establishes connections, and
        sets the processor to active state. Must be called before
        any processing operations.
        
        Raises:
            RuntimeError: If processor is already started
            ConnectionError: If required external connections cannot be established
            ConfigurationError: If processor configuration is invalid
            
        Note:
            This method is idempotent - calling it multiple times
            on an already started processor has no effect.
        """
        pass
    
    def stop(self) -> None:
        """
        Stop the processor and cleanup resources.
        
        Gracefully shuts down the processor, completes any pending
        operations, closes connections, and sets processor to inactive state.
        
        Raises:
            RuntimeError: If processor cannot be stopped cleanly
            
        Note:
            After stopping, the processor can be restarted with start().
            Any items in progress will be completed before stopping.
        """
        pass
    
    def reset(self) -> None:
        """
        Reset processor state and clear all counters.
        
        Resets processed_count and error_count to zero, clears any
        cached data, and returns processor to initial state.
        Processor must be stopped before calling reset.
        
        Raises:
            RuntimeError: If processor is currently active
            
        Note:
            This operation cannot be undone. All processing statistics
            and cached data will be permanently lost.
        """
        pass
    
    @abstractmethod
    def process_item(self, item: Any) -> Optional[Any]:
        """
        Process a single data item.
        
        This is the main processing method that must be implemented
        by concrete subclasses. It contains the core business logic
        for transforming input items.
        
        Args:
            item: The data item to process. Type depends on specific
                 processor implementation. Common types: dict, string,
                 custom data objects, file paths.
        
        Returns:
            Processed result or None if processing failed.
            Return type depends on processor implementation.
            None indicates processing failure.
        
        Raises:
            ProcessingError: If item cannot be processed due to data issues
            ValidationError: If item fails validation checks
            TimeoutError: If processing exceeds configured timeout
            
        Note:
            This method should be stateless and thread-safe.
            All error handling and logging should be performed here.
        """
        pass
    
    def validate_item(self, item: Any) -> bool:
        """
        Validate that an item can be processed.
        
        Performs pre-processing validation to ensure the item
        meets requirements for processing. Called automatically
        before process_item().
        
        Args:
            item: The data item to validate. Same type as expected
                 by process_item() method.
        
        Returns:
            True if item is valid and can be processed,
            False if item should be rejected.
            
        Raises:
            ValidationError: If validation cannot be performed
            
        Note:
            Validation should be fast and not modify the item.
            Complex validation logic should be in subclasses.
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current processor status and statistics.
        
        Returns comprehensive information about processor state,
        performance metrics, and configuration for monitoring
        and debugging purposes.
        
        Returns:
            Dictionary containing processor status information:
            {
                'name': str,
                'is_active': bool,
                'processed_count': int,
                'error_count': int,
                'last_error': Optional[str],
                'uptime_seconds': float,
                'config': Dict[str, Any]
            }
            
        Note:
            This method is safe to call at any time and does not
            affect processor state.
        """
        pass
```

### 2.3 Функция с декларативным кодом

```python
def process_file_batch(file_paths: List[Path], 
                      config: Dict[str, Any],
                      callback: Optional[Callable[[Path, bool], None]] = None) -> Dict[str, Any]:
    """
    Process a batch of files with specified configuration.
    
    Processes multiple files in parallel or sequential order based on
    configuration settings. Provides progress reporting through optional
    callback function and returns detailed results.
    
    Args:
        file_paths: List of file paths to process. Each path must point
                   to an existing readable file. Empty list is allowed.
                   Maximum recommended batch size is 1000 files.
        config: Configuration dictionary with processing parameters:
               Required keys:
               - 'max_workers': int (1-10) - number of parallel workers
               - 'timeout': int (1-3600) - timeout per file in seconds
               Optional keys:
               - 'chunk_size': int (100-10000) - characters per chunk
               - 'retry_attempts': int (0-5) - retry failed files
               - 'skip_errors': bool - continue on individual file errors
        callback: Optional progress callback function called for each file.
                 Receives (file_path: Path, success: bool) parameters.
                 Should return quickly to avoid blocking processing.
    
    Returns:
        Dictionary with batch processing results:
        {
            'total_files': int,
            'successful': int,
            'failed': int,
            'processing_time': float,
            'errors': List[Dict[str, str]],  # [{file: str, error: str}]
            'results': Dict[str, Any]        # File-specific results
        }
    
    Raises:
        ValueError: If config is missing required keys or has invalid values
        TypeError: If file_paths is not a list or contains non-Path objects
        PermissionError: If files cannot be accessed due to permissions
        FileNotFoundError: If any file in the batch does not exist
        
    Example:
        config = {
            'max_workers': 4,
            'timeout': 60,
            'chunk_size': 1000,
            'skip_errors': True
        }
        
        def progress_callback(path, success):
            print(f"Processed {path}: {'OK' if success else 'FAILED'}")
        
        results = process_file_batch(
            [Path('file1.txt'), Path('file2.txt')],
            config,
            progress_callback
        )
        
        print(f"Processed {results['successful']}/{results['total_files']} files")
    
    Note:
        - Processing order is not guaranteed when using multiple workers
        - Large batches may consume significant memory
        - Callback function should be thread-safe for parallel processing
        - Failed files are retried according to retry_attempts setting
    """
    pass
```

### 2.4 Переменные и константы

```python
# Global configuration constants
DEFAULT_BATCH_SIZE: int = 100
"""
Default number of items to process in a single batch.

This value provides optimal balance between memory usage and
processing efficiency for most use cases. Can be overridden
in configuration for specific requirements.
"""

MAX_CONCURRENT_WORKERS: int = 10
"""
Maximum number of concurrent worker threads allowed.

Limits resource usage and prevents system overload. Based on
typical system capabilities and thread overhead analysis.
Should not exceed number of CPU cores + 2.
"""

SUPPORTED_FILE_EXTENSIONS: List[str] = ['.txt', '.md', '.py', '.js', '.ts']
"""
List of file extensions supported by the processing system.

Only files with these extensions will be processed. Extensions
should be lowercase and include the leading dot. Additional
extensions can be added through configuration.
"""

# Instance variables (in class context)
class ProcessorManager:
    def __init__(self):
        self._processors: Dict[str, ExampleProcessor] = {}
        """
        Dictionary mapping processor names to processor instances.
        
        Key: str - Unique processor identifier
        Value: ExampleProcessor - Active processor instance
        
        Used for processor lifecycle management and lookup operations.
        Access through get_processor() and add_processor() methods.
        """
        
        self._last_cleanup: Optional[datetime] = None
        """
        Timestamp of the last cleanup operation.
        
        Tracks when expired processors were last removed from the system.
        Used to schedule periodic cleanup operations and prevent memory leaks.
        None indicates no cleanup has been performed yet.
        """
```

## 3. Стандарты продакшн кода

### 3.1 Трансформация декларативного в продакшн

**Из декларативного:**
```python
def process_item(self, item: Any) -> Optional[Any]:
    """Process a single data item..."""
    pass
```

**В продакшн:**
```python
def process_item(self, item: Any) -> Optional[Any]:
    """Process a single data item..."""
    try:
        # Validate input
        if not self.validate_item(item):
            self.logger.warning(f"Item validation failed: {item}")
            return None
        
        # Start processing timer
        start_time = time.time()
        
        # Core processing logic
        if isinstance(item, dict):
            result = self._process_dict_item(item)
        elif isinstance(item, str):
            result = self._process_string_item(item)
        else:
            result = self._process_generic_item(item)
        
        # Update metrics
        processing_time = time.time() - start_time
        self._processed_count += 1
        self._total_processing_time += processing_time
        
        self.logger.debug(f"Item processed in {processing_time:.3f}s")
        return result
        
    except ProcessingError as e:
        self._error_count += 1
        self.logger.error(f"Processing error: {e}")
        return None
    except Exception as e:
        self._error_count += 1
        self.logger.error(f"Unexpected error processing item: {e}")
        return None
```

### 3.2 Принципы продакшн кода

1. **Полная реализация**: Никаких `pass` операторов
2. **Обработка ошибок**: Try-catch блоки для всех потенциальных исключений
3. **Логирование**: Подробное логирование операций и ошибок
4. **Валидация**: Проверка входных данных и предусловий
5. **Метрики**: Сбор статистики производительности
6. **Документация**: Сохранение всех докстрингов из декларативного кода
7. **Типизация**: Строгое соблюдение типов из сигнатур
8. **Тестируемость**: Код должен легко покрываться unit-тестами

### 3.3 Пример полной трансформации

**Декларативный класс:**
```python
class FileProcessor(ABC):
    """Abstract processor for file operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        pass
    
    @abstractmethod
    def process_file(self, path: Path) -> bool:
        """Process single file."""
        pass
```

**Продакшн класс:**
```python
class FileProcessor(ABC):
    """Abstract processor for file operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._validate_config()
        self._setup_logging()
        
    def _validate_config(self) -> None:
        """Validate required configuration parameters."""
        required_keys = ['timeout', 'max_retries']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = self.config.get('log_level', 'INFO')
        self.logger.setLevel(getattr(logging, log_level))
    
    @abstractmethod
    def process_file(self, path: Path) -> bool:
        """Process single file."""
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            return False
        
        if not path.is_file():
            self.logger.error(f"Path is not a file: {path}")
            return False
        
        # Subclass implementation continues...
        pass
```

## 4. Правила именования и структуры

### 4.1 Файлы
- **Декларативный**: `{component_name}_declarative.py`
- **Продакшн**: `{component_name}.py`
- Один класс на файл
- Имя файла соответствует основному классу в snake_case

### 4.2 Классы
- **PascalCase**: `TextBlockChunker`, `FileSystemWatcher`
- Абстрактные классы: префикс `Base` или `Abstract`
- Интерфейсы: префикс `I` (опционально)

### 4.3 Методы и функции
- **snake_case**: `process_file`, `validate_input`
- Приватные методы: префикс `_`
- Защищенные методы: префикс `_`
- Дандер методы: `__init__`, `__str__`

### 4.4 Переменные
- **snake_case**: `file_path`, `chunk_size`
- Константы: **UPPER_CASE**: `MAX_WORKERS`, `DEFAULT_TIMEOUT`
- Приватные атрибуты: префикс `_`

## 5. Порядок разработки

### 5.1 Этап 1: Декларативный код
1. Создание файла с заголовочным докстрингом
2. Определение всех импортов и констант
3. Написание класса с полными докстрингами
4. Определение всех методов с сигнатурами и докстрингами
5. Добавление `pass` во все методы
6. Проверка синтаксиса и типов (mypy)

### 5.2 Этап 2: Продакшн код
1. Копирование декларативного файла
2. Удаление суффикса `_declarative` из имени
3. Замена всех `pass` на реальную реализацию
4. Добавление обработки ошибок
5. Добавление логирования
6. Написание unit-тестов
7. Интеграционное тестирование

### 5.3 Контроль качества
- **Статический анализ**: mypy, pylint, black
- **Тестирование**: pytest с покрытием >90%
- **Документация**: проверка полноты докстрингов
- **Code review**: проверка соответствия стандартам

## 6. Примеры команд

### 6.1 Создание декларативного кода
```bash
# Создание файла
touch src/components/text_chunker_declarative.py

# Проверка типов
mypy src/components/text_chunker_declarative.py

# Форматирование
black src/components/text_chunker_declarative.py
```

### 6.2 Трансформация в продакшн
```bash
# Копирование файла
cp src/components/text_chunker_declarative.py src/components/text_chunker.py

# Реализация методов (ручная работа)
# Удаление всех pass и добавление реализации

# Тестирование
pytest tests/test_text_chunker.py -v --cov=src.components.text_chunker
```

Этот подход обеспечивает четкое разделение между проектированием архитектуры (декларативный код) и её реализацией (продакшн код), что улучшает качество кода и упрощает разработку сложных систем. 