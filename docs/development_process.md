**ВНИМАНИЕ!!!! КРИТИЧНО!!!! Код в данном тексте только для примеров и понимания. **

# Development Process - Step Execution Order

## Общий подход к разработке

### Принцип: "Декларативный код → Продакшн код → Тесты"

Каждый шаг реализации выполняется в строгом порядке с полным покрытием тестами.

## Порядок выполнения шага

### 1. Декларативный код (Declarative Code)

#### 1.1 Структура файла
```
"""
Module Name - Brief Description

Detailed description of the module's purpose, responsibilities, and usage.
Examples of how this module integrates with other components.

Author: Developer Name
Version: 1.0.0
"""

# Imports section
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
import logging

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3

# Main classes and functions with full docstrings
```

#### 1.2 Докстринги для классов
```python
class ClassName:
    """
    Class Name - Detailed Description
    
    Comprehensive description of the class purpose, responsibilities,
    and how it fits into the overall architecture.
    
    Attributes:
        attribute_name (type): Detailed description of the attribute,
            its purpose, constraints, and usage examples.
        another_attribute (Optional[type]): Description with examples
            of when it's None vs when it has a value.
    
    Example:
        >>> instance = ClassName(param1, param2)
        >>> result = await instance.method_name()
    
    Raises:
        SpecificError: When and why this error occurs
        AnotherError: Description of error conditions
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        """
        Initialize ClassName instance.
        
        Args:
            param1 (str): Detailed description of the parameter,
                including valid values, constraints, and examples.
                Must be non-empty string.
            param2 (Optional[int], optional): Description of optional parameter.
                Defaults to None. Must be positive integer if provided.
        
        Raises:
            ValueError: If param1 is empty or param2 is negative
            TypeError: If param1 is not string or param2 is not int
        """
        pass
    
    async def method_name(self, param: str) -> Dict[str, Any]:
        """
        Method Name - Detailed Description
        
        Comprehensive description of what the method does, how it works,
        and what it returns. Include examples of typical usage.
        
        Args:
            param (str): Detailed description of the parameter,
                including format requirements, valid values, and examples.
                Must be valid file path.
        
        Returns:
            Dict[str, Any]: Detailed description of the return value,
                including structure, key names, value types, and examples.
                Format: {"status": "success", "data": {...}}
        
        Raises:
            FileNotFoundError: If the file specified in param doesn't exist
            PermissionError: If access to the file is denied
            ProcessingError: If file processing fails
        
        Example:
            >>> result = await instance.method_name("/path/to/file.txt")
            >>> print(result["status"])  # "success"
        """
        pass
```

#### 1.3 Требования к декларативному коду
- ✅ **Полные докстринги** для всех классов, методов, свойств
- ✅ **Типизация** всех параметров и возвращаемых значений
- ✅ **Описание исключений** с условиями их возникновения
- ✅ **Примеры использования** в докстрингах
- ✅ **Импорты** всех необходимых модулей
- ✅ **Константы** и настройки
- ✅ **Структура классов** с методами (без реализации)
- ❌ **НЕ реализуется** логика методов (только `pass`)

### 2. Продакшн код (Production Code)

#### 2.1 Структура файла
```
"""
Module Name - Brief Description

[Тот же докстринг что и в декларативном коде]
"""

# [Те же импорты что и в декларативном коде]

# [Те же константы что и в декларативном коде]

# [Полная реализация всех классов и методов]
```

#### 2.2 Требования к продакшн коду
- ✅ **Полная реализация** всех методов из декларативного кода
- ✅ **Обработка ошибок** согласно описанию в докстрингах
- ✅ **Логирование** всех важных операций
- ✅ **Валидация** входных параметров
- ✅ **Асинхронность** где требуется
- ✅ **Типизация** соблюдается
- ✅ **Докстринги** остаются без изменений

### 3. Тесты (Tests)

#### 3.1 Структура тестового файла
```python
"""
Tests for Module Name

Comprehensive test suite covering all functionality, edge cases,
and error conditions for the module.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from docanalyzer.module_name import ClassName


class TestClassName:
    """Test suite for ClassName class."""
    
    @pytest.fixture
    def instance(self):
        """Create test instance."""
        return ClassName("test_param")
    
    @pytest.mark.asyncio
    async def test_method_name_success(self, instance):
        """Test successful method execution."""
        # Arrange
        param = "/path/to/existing/file.txt"
        
        # Act
        result = await instance.method_name(param)
        
        # Assert
        assert result["status"] == "success"
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_method_name_file_not_found(self, instance):
        """Test method with non-existent file."""
        # Arrange
        param = "/path/to/nonexistent/file.txt"
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            await instance.method_name(param)
```

#### 3.2 Требования к тестам
- ✅ **Покрытие 90%+** для ВСЕХ файлов проекта (не только текущего шага)
- ✅ **Unit тесты** для всех методов
- ✅ **Интеграционные тесты** для взаимодействия модулей
- ✅ **Тесты ошибок** для всех исключений
- ✅ **Edge cases** тесты граничных условий
- ✅ **Mock тесты** для внешних зависимостей
- ✅ **Async тесты** для асинхронных методов
- ✅ **Фикстуры** для переиспользуемых объектов

## Пример выполнения шага

### Шаг: Lock Management

#### 1. Декларативный код
```python
# docanalyzer/services/lock_manager.py
"""
Lock Manager - Directory Locking Service

Provides functionality for creating, managing, and cleaning up lock files
to prevent concurrent processing of the same directory by multiple processes.

The lock manager creates lock files with process ID and metadata,
checks for orphaned locks, and ensures atomic directory processing.

Author: File Watcher Team
Version: 1.0.0
"""

import os
import json
import psutil
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import logging

from docanalyzer.models.file_system import LockFile

logger = logging.getLogger(__name__)

DEFAULT_LOCK_TIMEOUT = 3600
LOCK_FILE_NAME = ".processing.lock"


class LockManager:
    """
    Lock Manager - Directory Locking Service
    
    Manages lock files to prevent concurrent processing of directories.
    Creates, validates, and cleans up lock files with process metadata.
    
    Attributes:
        lock_timeout (int): Maximum lock duration in seconds.
            Defaults to 3600 seconds (1 hour).
        lock_file_name (str): Name of the lock file in directories.
            Defaults to ".processing.lock".
    
    Example:
        >>> lock_manager = LockManager()
        >>> lock_file = await lock_manager.create_lock("/path/to/directory")
        >>> await lock_manager.remove_lock(lock_file)
    """
    
    def __init__(self, lock_timeout: int = DEFAULT_LOCK_TIMEOUT):
        """
        Initialize LockManager instance.
        
        Args:
            lock_timeout (int): Maximum lock duration in seconds.
                Must be positive integer. Defaults to 3600.
        
        Raises:
            ValueError: If lock_timeout is not positive
        """
        pass
    
    async def create_lock(self, directory: str) -> LockFile:
        """
        Create lock file for directory.
        
        Creates a lock file with current process ID and metadata.
        If lock already exists, validates it and removes if orphaned.
        
        Args:
            directory (str): Path to directory to lock.
                Must be existing directory path.
        
        Returns:
            LockFile: Created lock file with metadata.
        
        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If cannot create lock file
            LockError: If directory is already locked by active process
        """
        pass
    
    async def remove_lock(self, lock_file: LockFile) -> bool:
        """
        Remove lock file from directory.
        
        Validates lock ownership and removes the lock file.
        
        Args:
            lock_file (LockFile): Lock file to remove.
                Must be valid LockFile instance.
        
        Returns:
            bool: True if lock was removed, False otherwise.
        
        Raises:
            PermissionError: If cannot remove lock file
            LockError: If lock file is owned by different process
        """
        pass
```

#### 2. Продакшн код
```python
# [Тот же декларативный код + полная реализация методов]

class LockManager:
    def __init__(self, lock_timeout: int = DEFAULT_LOCK_TIMEOUT):
        if lock_timeout <= 0:
            raise ValueError("lock_timeout must be positive")
        self.lock_timeout = lock_timeout
        self.lock_file_name = LOCK_FILE_NAME
    
    async def create_lock(self, directory: str) -> LockFile:
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        lock_path = Path(directory) / self.lock_file_name
        
        # Check existing lock
        if lock_path.exists():
            existing_lock = await self._read_lock_file(lock_path)
            if await self._is_process_alive(existing_lock.process_id):
                raise LockError(f"Directory already locked by process {existing_lock.process_id}")
            else:
                await self._remove_lock_file(lock_path)
        
        # Create new lock
        lock_data = LockFile(
            process_id=os.getpid(),
            created_at=datetime.now(),
            directory=directory,
            status="active",
            lock_file_path=str(lock_path)
        )
        
        await self._write_lock_file(lock_path, lock_data)
        logger.info(f"Created lock for directory: {directory}")
        return lock_data
```

#### 3. Тесты
```python
# tests/unit/test_lock_manager.py
"""
Tests for Lock Manager

Comprehensive test suite for directory locking functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from docanalyzer.services.lock_manager import LockManager
from docanalyzer.models.file_system import LockFile


class TestLockManager:
    """Test suite for LockManager class."""
    
    @pytest.fixture
    def lock_manager(self):
        """Create test lock manager."""
        return LockManager(lock_timeout=300)
    
    @pytest.fixture
    def test_directory(self, tmp_path):
        """Create test directory."""
        return str(tmp_path / "test_dir")
    
    @pytest.mark.asyncio
    async def test_create_lock_success(self, lock_manager, test_directory):
        """Test successful lock creation."""
        # Arrange
        os.makedirs(test_directory, exist_ok=True)
        
        # Act
        lock_file = await lock_manager.create_lock(test_directory)
        
        # Assert
        assert lock_file.process_id == os.getpid()
        assert lock_file.directory == test_directory
        assert lock_file.status == "active"
    
    @pytest.mark.asyncio
    async def test_create_lock_directory_not_found(self, lock_manager):
        """Test lock creation with non-existent directory."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            await lock_manager.create_lock("/nonexistent/directory")
```

## Критерии завершения шага

### ✅ Шаг считается завершенным когда:
1. **Декларативный код** написан с полными докстрингами
2. **Продакшн код** полностью реализован
3. **Тесты** написаны с покрытием 90%+ для всего проекта
4. **Все тесты** проходят успешно
5. **Документация** обновлена
6. **Код** проходит линтеры (flake8, mypy)

### 📊 Метрики качества:
- **Покрытие тестами**: 90%+ для всего проекта
- **Документация**: 100% методов имеют докстринги
- **Типизация**: 100% методов типизированы
- **Обработка ошибок**: Все исключения покрыты тестами 