# План реализации DocAnalyzer: Пошаговый подход

## 0. Метрики цели для каждого шага

### 0.1 Критерии успешного выполнения шага
Каждый шаг считается завершенным только при выполнении **ВСЕХ** следующих условий:

#### ✅ **Критерий 1: Продакшн код готов**
- Написан полнофункциональный продакшн код
- Все `pass` заменены на реальную реализацию
- Добавлена обработка ошибок и логирование
- Код соответствует стандартам проекта

#### ✅ **Критерий 2: Покрытие тестами 90%+**
- **Целевое покрытие**: 90% или выше для всего проекта
- **Учет новых файлов**: При добавлении новых файлов процент может временно снизиться
- **Обязательное восстановление**: Покрытие должно быть восстановлено до 90%+ к концу шага
- **Инструмент контроля**: `pytest --cov=docanalyzer --cov-report=term-missing`

#### ✅ **Критерий 3: Все тесты проекта работают**
- **100% прохождение**: Все существующие тесты должны проходить успешно
- **Новые тесты**: Добавленные тесты также должны проходить
- **Интеграционная совместимость**: Новый код не ломает существующую функциональность
- **Инструмент контроля**: `pytest -v --tb=short`

### 0.2 Процедура контроля качества

#### Перед началом шага:
```bash
# Запомнить текущее покрытие
pytest --cov=docanalyzer --cov-report=term | grep "TOTAL.*%" > coverage_before.txt
pytest -v --tb=short > tests_before.txt
```

#### Во время выполнения шага:
```bash
# Периодическая проверка (после каждого значимого изменения)
pytest --cov=docanalyzer --cov-report=term-missing
pytest -v --tb=short
```

#### После завершения шага:
```bash
# Финальная проверка
pytest --cov=docanalyzer --cov-report=term-missing --cov-fail-under=90
pytest -v --tb=short
echo "✅ Шаг завершен успешно" || echo "❌ Шаг требует доработки"
```

### 0.3 Действия при несоответствии критериям

#### Если покрытие < 90%:
1. Добавить недостающие unit-тесты
2. Добавить интеграционные тесты
3. Проверить исключения и edge cases
4. Повторить проверку покрытия

#### Если тесты не проходят:
1. Исправить код или тесты
2. Проверить совместимость с зависимостями
3. Обновить mock-объекты при необходимости
4. Повторить прогон тестов

#### Если код не готов:
1. Завершить реализацию всех методов
2. Добавить обработку ошибок
3. Добавить логирование
4. Проверить соответствие стандартам

### 0.4 Инструменты мониторинга

#### Покрытие тестами:
```bash
# Детальный отчет по покрытию
pytest --cov=docanalyzer --cov-report=html

# Проверка конкретного файла
pytest --cov=docanalyzer/filters/text_filter.py --cov-report=term-missing

# Установка минимального порога
pytest --cov=docanalyzer --cov-fail-under=90
```

#### Качество кода:
```bash
# Статический анализ
mypy docanalyzer/
pylint docanalyzer/
black --check docanalyzer/

# Проверка импортов
isort --check-only docanalyzer/
```

### 0.5 Отчетность по шагам

#### Шаблон отчета о завершении шага:
```markdown
## Отчет по шагу X.Y: [Название компонента]

### ✅ Выполненные работы:
- [ ] Декларативный код создан
- [ ] Продакшн код реализован  
- [ ] Тесты написаны и проходят
- [ ] Покрытие >= 90%

### 📊 Метрики:
- **Покрытие тестами**: XX.X% (было YY.Y%)
- **Тесты пройдено**: XX/XX (100%)
- **Файлы добавлены**: X файлов
- **Строк кода**: +XXX строк

### 🧪 Результаты тестирования:
```bash
pytest --cov=docanalyzer --cov-report=term
# Вывод команды
```

### ✅ Критерии выполнены:
- [x] Продакшн код готов
- [x] Покрытие тестами 90%+  
- [x] Все тесты проекта работают
```

## 1. Обзор плана

### 1.1 Принципы планирования
- **Независимые компоненты сначала**: Базовые классы и утилиты без внешних зависимостей
- **Производные компоненты потом**: Классы, зависящие от базовых
- **Двухэтапная разработка**: Декларативный код → Продакшн код
- **Один класс = один файл**: Модульная структура для легкого тестирования

### 1.2 Структура этапов
```
Этап 1: Базовые компоненты (независимые)
Этап 2: Фильтры файлов (зависят от базовых)
Этап 3: Чанкинг (зависит от фильтров)
Этап 4: Пайплайны (зависят от чанкинга)
Этап 5: Управление каталогами (зависит от пайплайнов)
Этап 6: API и интеграция (зависит от всех)
```

### 1.3 Принцип замещения в одном файле
- **Декларативный код**: Создается с полными докстрингами и `pass`
- **Продакшн код**: Заменяет декларативный в том же файле
- **Цель**: Экономия контекстного окна - архитектура видна в декларативном коде

## 2. Этап 1: Базовые компоненты (независимые)

### 2.1 Модель данных для блоков текста
**Зависимости**: Только стандартные библиотеки + chunk_metadata_adapter

#### Шаг 1.1: BlockTypeExtended
**Файл**: `docanalyzer/filters/block_types.py`

**Подэтап 1.1.1**: Создать декларативный код с полными докстрингами
```python
"""
Extended block types for file parsing.

Defines comprehensive enumeration of text block types that extend
the basic BlockType from chunk_metadata_adapter with additional
types specific to code parsing and document structure.
"""

from enum import Enum
from typing import Optional, Dict, Any, List

class BlockTypeExtended(str, Enum):
    """
    Extended enumeration of block types for file parsing.
    
    Extends basic text blocks with code-specific and structural
    block types for comprehensive document analysis.
    """
    
    # Basic text blocks
    PARAGRAPH: str = "paragraph"
    HEADING: str = "heading" 
    LIST_ITEM: str = "list_item"
    QUOTE: str = "quote"
    
    # Code blocks  
    CODE_BLOCK: str = "code_block"
    FUNCTION: str = "function"
    CLASS: str = "class"
    METHOD: str = "method"
    COMMENT: str = "comment"
    DOCSTRING: str = "docstring"
    
    # Document structure
    SECTION: str = "section"
    CHAPTER: str = "chapter"
    TITLE: str = "title"
    SUBTITLE: str = "subtitle"
    
    # Special blocks
    TABLE: str = "table"
    IMAGE: str = "image"
    LINK: str = "link"
    METADATA: str = "metadata"
    IMPORT: str = "import"
    VARIABLE: str = "variable"
    
    @classmethod
    def get_code_types(cls) -> List['BlockTypeExtended']:
        """
        Get all block types related to code.
        
        Returns:
            List of block types that represent code structures
            like functions, classes, methods, and code blocks.
        """
        pass
    
    @classmethod  
    def get_text_types(cls) -> List['BlockTypeExtended']:
        """
        Get all block types related to text content.
        
        Returns:
            List of block types that represent textual content
            like paragraphs, headings, and quotes.
        """
        pass
```

**Подэтап 1.1.2**: Заменить декларативный код на продакшн в том же файле

#### Шаг 1.2: TextBlock
**Файл**: `docanalyzer/filters/text_block.py`

**Подэтап 1.2.1**: Создать декларативный код с полными докстрингами
```python
"""
Text block data model for structured content representation.

Defines the TextBlock class which represents a structured piece of
content extracted from files, with comprehensive metadata about
position, type, hierarchy, and quality metrics.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from chunk_metadata_adapter.data_types import LanguageEnum, ChunkType, BlockType
from .block_types import BlockTypeExtended

@dataclass
class TextBlock:
    """
    Represents a structured text block extracted from a file.
    
    This is the fundamental unit that gets passed to the chunking system.
    Each block represents a semantically coherent piece of content with
    comprehensive metadata about its position, type, and characteristics.
    
    Attributes:
        content: The actual text content of the block
        block_type: Type classification of the block
        language: Programming or natural language of the content
        start_line: Zero-based line number where block starts
        end_line: Zero-based line number where block ends  
        start_offset: Character offset from file beginning
        end_offset: Character offset where block ends
        level: Nesting level (0 = top level)
        parent_id: ID of parent block for hierarchical structure
        block_id: Unique identifier for this block
        title: Optional title or name for the block
        metadata: Additional metadata specific to block type
        tags: List of classification tags
        complexity_score: Calculated complexity metric (0.0-1.0)
        importance_score: Calculated importance metric (0.0-1.0)
    """
    
    # Core content
    content: str
    block_type: BlockTypeExtended
    language: LanguageEnum = LanguageEnum.UNKNOWN
    
    # Position information
    start_line: int = 0
    end_line: int = 0
    start_offset: int = 0
    end_offset: int = 0
    
    # Hierarchical structure
    level: int = 0
    parent_id: Optional[str] = None
    block_id: str = field(default_factory=lambda: str(hash(datetime.now())))
    
    # Descriptive metadata
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Quality metrics
    complexity_score: float = 0.0
    importance_score: float = 0.5
    
    def __post_init__(self) -> None:
        """
        Post-initialization processing.
        
        Generates block ID based on content and position if not provided,
        validates field values, and performs any necessary data cleanup.
        """
        pass
    
    @property
    def chunk_type(self) -> ChunkType:
        """
        Map block type to chunk type for metadata adapter compatibility.
        
        Returns:
            Appropriate ChunkType enum value based on the block_type.
            Used when creating SemanticChunk objects for vector storage.
        """
        pass
    
    @property
    def block_type_for_metadata(self) -> BlockType:
        """
        Map extended block type to standard BlockType for metadata.
        
        Returns:
            Standard BlockType enum value compatible with chunk_metadata_adapter.
            Used for metadata consistency across the system.
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert block to dictionary for serialization.
        
        Returns:
            Dictionary representation of the block with all fields
            converted to JSON-serializable types.
        """
        pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextBlock':
        """
        Create TextBlock instance from dictionary.
        
        Args:
            data: Dictionary containing block data, typically from
                 JSON deserialization or database retrieval.
        
        Returns:
            New TextBlock instance with data from dictionary.
            
        Raises:
            ValueError: If required fields are missing from data
            TypeError: If field types don't match expected types
        """
        pass
    
    def get_content_preview(self, max_length: int = 100) -> str:
        """
        Get truncated preview of block content.
        
        Args:
            max_length: Maximum length of preview string.
                       Must be positive integer.
        
        Returns:
            Truncated content with ellipsis if longer than max_length.
            Preserves word boundaries when possible.
        """
        pass
    
    def calculate_metrics(self) -> None:
        """
        Calculate and update complexity and importance scores.
        
        Analyzes block content, type, and metadata to determine
        complexity and importance scores. Updates the corresponding
        attributes with calculated values.
        
        Note:
            This method modifies the block's complexity_score and
            importance_score attributes based on content analysis.
        """
        pass
    
    def validate(self) -> bool:
        """
        Validate block data integrity and consistency.
        
        Returns:
            True if block data is valid and consistent,
            False if there are validation errors.
            
        Note:
            Checks content length, position consistency, required fields,
            and data type correctness. Does not raise exceptions.
        """
        pass
```

**Подэтап 1.2.2**: Заменить декларативный код на продакшн в том же файле

#### Шаг 1.3: FileStructure
**Файл**: `docanalyzer/filters/file_structure.py`

**Подэтап 1.3.1**: Создать декларативный код с полными докстрингами
**Подэтап 1.3.2**: Заменить декларативный код на продакшн в том же файле

### 2.2 Базовый класс фильтров
**Зависимости**: TextBlock, FileStructure

#### Шаг 1.4: BaseFileFilter
**Файл**: `docanalyzer/filters/base_filter.py`

**Подэтап 1.4.1**: Создать декларативный код с полными докстрингами
**Подэтап 1.4.2**: Заменить декларативный код на продакшн в том же файле

### 2.3 Конфигурация чанкинга
**Зависимости**: Только стандартные библиотеки

#### Шаг 1.5: ChunkingConfig
**Файл**: `docanalyzer/pipeline/chunking_config.py`

**Подэтап 1.5.1**: Создать декларативный код с полными докстрингами
**Подэтап 1.5.2**: Заменить декларативный код на продакшн в том же файле

## 3. Этап 2: Фильтры файлов (зависят от базовых)

### 3.1 Реестр фильтров
**Зависимости**: BaseFileFilter

#### Шаг 2.1: FilterRegistry
**Файл**: `docanalyzer/filters/registry.py`

**Подэтап 2.1.1**: Создать декларативный код с полными докстрингами
**Подэтап 2.1.2**: Заменить декларативный код на продакшн в том же файле

### 3.2 Конкретные фильтры
**Зависимости**: BaseFileFilter, FilterRegistry

#### Шаг 2.2: TextFileFilter
**Файл**: `docanalyzer/filters/text_filter.py`

**Подэтап 2.2.1**: Создать декларативный код с полными докстрингами
**Подэтап 2.2.2**: Заменить декларативный код на продакшн в том же файле

#### Шаг 2.3: PythonFileFilter
**Файл**: `docanalyzer/filters/python_filter.py`

**Подэтап 2.3.1**: Создать декларативный код с полными докстрингами
**Подэтап 2.3.2**: Заменить декларативный код на продакшн в том же файле

#### Шаг 2.4: MarkdownFileFilter
**Файл**: `docanalyzer/filters/markdown_filter.py`

**Подэтап 2.4.1**: Создать декларативный код с полными докстрингами
**Подэтап 2.4.2**: Заменить декларативный код на продакшн в том же файле

#### Шаг 2.5: JavaScriptFileFilter
**Файл**: `docanalyzer/filters/javascript_filter.py`

**Подэтап 2.5.1**: Создать декларативный код с полными докстрингами
**Подэтап 2.5.2**: Заменить декларативный код на продакшн в том же файле

## 4. Этап 3: Чанкинг (зависит от фильтров)

### 4.1 Чанкер блоков
**Зависимости**: TextBlock, FileStructure, ChunkingConfig, vector_store_client

#### Шаг 3.1: TextBlockChunker
**Файл**: `docanalyzer/pipeline/chunker.py`

**Подэтап 3.1.1**: Создать декларативный код с полными докстрингами
**Подэтап 3.1.2**: Заменить декларативный код на продакшн в том же файле

## 5. Этап 4: Пайплайны (зависят от чанкинга)

### 5.1 Базовый пайплайн
**Зависимости**: TextBlockChunker, FilterRegistry

#### Шаг 4.1: PipelineConfig
**Файл**: `docanalyzer/pipeline/pipeline_config.py`

**Подэтап 4.1.1**: Создать декларативный код с полными докстрингами
**Подэтап 4.1.2**: Заменить декларативный код на продакшн в том же файле

#### Шаг 4.2: PipelineStats
**Файл**: `docanalyzer/pipeline/pipeline_stats.py`

**Подэтап 4.2.1**: Создать декларативный код с полными докстрингами
**Подэтап 4.2.2**: Заменить декларативный код на продакшн в том же файле

#### Шаг 4.3: BasePipeline
**Файл**: `docanalyzer/pipeline/base_pipeline.py`

**Подэтап 4.3.1**: Создать декларативный код с полными докстрингами
**Подэтап 4.3.2**: Заменить декларативный код на продакшн в том же файле

### 5.2 Конкретный пайплайн каталога
**Зависимости**: BasePipeline, TextBlockChunker

#### Шаг 4.4: DirectoryPipeline
**Файл**: `docanalyzer/pipeline/directory_pipeline.py`

**Подэтап 4.4.1**: Создать декларативный код с полными докстрингами
**Подэтап 4.4.2**: Заменить декларативный код на продакшн в том же файле

## 6. Этап 5: Управление каталогами (зависит от пайплайнов)

### 6.1 Менеджер .wdd файлов
**Зависимости**: Только стандартные библиотеки + vector_store_client

#### Шаг 5.1: WatchDirectoryManager
**Файл**: `docanalyzer/wdd/manager.py`

**Подэтап 5.1.1**: Создать декларативный код с полными докстрингами
**Подэтап 5.1.2**: Заменить декларативный код на продакшн в том же файле

### 6.2 Менеджер пайплайнов
**Зависимости**: DirectoryPipeline, WatchDirectoryManager

#### Шаг 5.2: PipelineManager
**Файл**: `docanalyzer/pipeline/manager.py`

**Подэтап 5.2.1**: Создать декларативный код с полными докстрингами
**Подэтап 5.2.2**: Заменить декларативный код на продакшн в том же файле

### 6.3 Файловый наблюдатель
**Зависимости**: PipelineManager

#### Шаг 5.3: FileSystemWatcher
**Файл**: `docanalyzer/watcher/filesystem_watcher.py`

**Подэтап 5.3.1**: Создать декларативный код с полными докстрингами
**Подэтап 5.3.2**: Заменить декларативный код на продакшн в том же файле

## 7. Этап 6: API и интеграция (зависит от всех)

### 7.1 MCP команды
**Зависимости**: PipelineManager, FileSystemWatcher

#### Шаг 6.1: Команды управления мониторингом
**Файлы** (каждый файл: декларативный → продакшн):
- `docanalyzer/commands/start_watching_command.py`
- `docanalyzer/commands/stop_watching_command.py`
- `docanalyzer/commands/get_watch_status_command.py`
- `docanalyzer/commands/add_watch_path_command.py`
- `docanalyzer/commands/remove_watch_path_command.py`

**Подэтап 6.1.1**: Создать декларативный код для всех 5 команд
**Подэтап 6.1.2**: Заменить декларативный код на продакшн для всех 5 команд

#### Шаг 6.2: Команды управления файлами
**Файлы** (каждый файл: декларативный → продакшн):
- `docanalyzer/commands/process_file_command.py`
- `docanalyzer/commands/reprocess_file_command.py`
- `docanalyzer/commands/get_file_status_command.py`
- `docanalyzer/commands/list_processed_files_command.py`

**Подэтап 6.2.1**: Создать декларативный код для всех 4 команд
**Подэтап 6.2.2**: Заменить декларативный код на продакшн для всех 4 команд

#### Шаг 6.3: Команды для .wdd файлов
**Файлы** (каждый файл: декларативный → продакшн):
- `docanalyzer/commands/scan_directory_command.py`
- `docanalyzer/commands/get_wdd_status_command.py`
- `docanalyzer/commands/cleanup_wdd_command.py`
- `docanalyzer/commands/rebuild_wdd_command.py`

**Подэтап 6.3.1**: Создать декларативный код для всех 4 команд
**Подэтап 6.3.2**: Заменить декларативный код на продакшн для всех 4 команд

#### Шаг 6.4: Команды статистики
**Файлы** (каждый файл: декларативный → продакшн):
- `docanalyzer/commands/get_system_stats_command.py`
- `docanalyzer/commands/get_processing_stats_command.py`
- `docanalyzer/commands/get_queue_status_command.py`
- `docanalyzer/commands/health_check_command.py`

**Подэтап 6.4.1**: Создать декларативный код для всех 4 команд
**Подэтап 6.4.2**: Заменить декларативный код на продакшн для всех 4 команд

### 7.2 Главное приложение
**Зависимости**: Все команды, mcp_proxy_adapter

#### Шаг 6.5: DocAnalyzerApp
**Файл**: `docanalyzer/app.py`

**Подэтап 6.5.1**: Создать декларативный код с полными докстрингами
**Подэтап 6.5.2**: Заменить декларативный код на продакшн в том же файле

#### Шаг 6.6: Main entry point
**Файл**: `docanalyzer/main.py`

**Подэтап 6.6.1**: Создать декларативный код с полными докстрингами
**Подэтап 6.6.2**: Заменить декларативный код на продакшн в том же файле

## 8. График выполнения

### 8.1 Временные рамки (в рабочих днях)

| Этап | Декларативный | Замена на продакшн | Тестирование | Итого |
|------|---------------|-------------------|--------------|-------|
| Этап 1: Базовые компоненты (5 файлов) | 2 дня | 4 дня | 2 дня | 8 дней |
| Этап 2: Фильтры файлов (5 файлов) | 2 дня | 4 дня | 2 дня | 8 дней |
| Этап 3: Чанкинг (1 файл) | 0.5 дня | 2 дня | 1 день | 3.5 дня |
| Этап 4: Пайплайны (4 файла) | 1.5 дня | 3 дня | 2 дня | 6.5 дня |
| Этап 5: Управление каталогами (3 файла) | 1 день | 3 дня | 2 дня | 6 дней |
| Этап 6: API и интеграция (19 файлов) | 3 дня | 6 дней | 3 дня | 12 дней |
| **Итого** | **10 дней** | **22 дня** | **12 дней** | **44 дня** |

### 8.2 Критический путь
```
Базовые компоненты → Фильтры → Чанкинг → Пайплайны → Управление → API
```

### 8.3 Новый подход к разработке
- **Декларативный код первым**: Создается архитектура с полными докстрингами
- **Замена на продакшн**: В том же файле заменяется реализация  
- **Экономия контекста**: Архитектура видна в декларативном коде
- **Преимущества**: Лучше помещается в контекстное окно ИИ

### 8.4 Параллельные работы
- Тестирование можно начинать сразу после замены на продакшн код
- Документация остается актуальной (док стринги сохраняются)
- Code review проводится после каждого подэтапа замены
- Можно работать над декларативным кодом следующего этапа параллельно с продакшн кодом текущего

## 9. Контрольные точки и критерии готовности

### 9.1 Критерии готовности декларативного кода
- ✅ Все классы имеют полные докстринги
- ✅ Все методы имеют type hints и документацию параметров
- ✅ Все публичные атрибуты документированы
- ✅ Файл проходит проверку mypy без ошибок
- ✅ Код отформатирован с помощью black
- ✅ Все методы содержат только `pass`

### 9.2 Критерии готовности продакшн кода (замены)
- ✅ Все `pass` заменены на реальную реализацию в том же файле
- ✅ Добавлена обработка ошибок во всех методах
- ✅ Добавлено логирование ключевых операций
- ✅ Код покрыт unit-тестами на >90%
- ✅ Интеграционные тесты проходят успешно
- ✅ Производительность соответствует требованиям
- ✅ Докстринги сохранены и актуальны

### 9.3 Критерии готовности этапа
- ✅ Все компоненты этапа заменены на продакшн код
- ✅ Интеграция между компонентами работает
- ✅ Покрытие тестами > 90%
- ✅ Производительность соответствует SLA
- ✅ Докстринги сохранены во всех файлах
- ✅ Code review пройден для замененного кода

## 10. Управление рисками

### 10.1 Технические риски
**Риск**: Проблемы интеграции с внешними адаптерами
- **Митигация**: Раннее тестирование интеграции
- **План Б**: Создание mock-объектов для тестирования

**Риск**: Производительность чанкинга больших файлов
- **Митигация**: Профилирование на каждом этапе
- **План Б**: Оптимизация алгоритмов или параллельная обработка

**Риск**: Сложность координации через .wdd файлы
- **Митигация**: Подробное тестирование сценариев блокировок
- **План Б**: Использование базы данных вместо файлов

### 10.2 Временные риски
**Риск**: Недооценка сложности реализации
- **Митигация**: Буфер 20% к каждому этапу
- **План Б**: Урезание функциональности до MVP

**Риск**: Блокировки между этапами
- **Митигация**: Четкое определение интерфейсов в декларативном коде
- **План Б**: Параллельная разработка с заглушками

**Риск**: Переполнение контекста при замене
- **Митигация**: Декларативный код экономит контекст
- **План Б**: Разбиение больших файлов на подфайлы

## 11. Инструменты и настройка среды

### 11.1 Обязательные инструменты
```bash
# Статический анализ
pip install mypy pylint black isort

# Тестирование
pip install pytest pytest-cov pytest-mock

# Документация
pip install sphinx sphinx-autodoc-typehints

# Профилирование
pip install cProfile memory_profiler
```

### 11.2 Настройка проекта
```bash
# Создание структуры проекта
mkdir -p docanalyzer/{filters,pipeline,wdd,watcher,commands}
mkdir -p tests/{unit,integration}
mkdir -p docs/{declarative,production}

# Настройка mypy
echo "[mypy]" > mypy.ini
echo "python_version = 3.9" >> mypy.ini
echo "strict = true" >> mypy.ini

# Настройка pytest
echo "[tool:pytest]" > setup.cfg
echo "testpaths = tests" >> setup.cfg
echo "python_files = test_*.py" >> setup.cfg
```

### 11.3 Процесс замены декларативного кода
```bash
# Пример замены в файле
# 1. Создается декларативный код с pass
# 2. Копируется декларативный код
# 3. В том же файле заменяется на продакшн
# 4. Докстринги остаются неизменными

# Шаблон команды для замены pass на реализацию:
sed -i 's/    pass/    # TODO: implement/g' target_file.py
```

### 11.4 Шаблоны файлов
Создать шаблоны для быстрого старта:
- `templates/declarative_class.py.template`
- `templates/test_class.py.template`

## 12. Заключение

Обновленный план с подходом "декларативный → замена на продакшн" обеспечивает:

### 12.1 Ключевые преимущества
- **Экономия контекста**: Декларативный код компактнее для ИИ
- **Четкая архитектура**: Интерфейсы видны сразу в докстрингах  
- **Упрощенная разработка**: Один файл вместо двух
- **Сохранение документации**: Докстринги остаются актуальными
- **Структурированный подход** с четкими зависимостями

### 12.2 Практические выгоды
- **Сокращение времени**: 44 дня вместо 57 дней  
- **Меньше файлов**: 41 файл вместо 82 файлов
- **Лучшая работа с ИИ**: Архитектура помещается в контекст
- **Минимизацию рисков** через раннее тестирование
- **Возможность параллельной работы** команды

### 12.3 Результат
Следование этому плану гарантирует создание высококачественной, хорошо документированной и тестируемой системы DocAnalyzer с оптимальным использованием ресурсов разработки и контекстного окна ИИ-помощников. 