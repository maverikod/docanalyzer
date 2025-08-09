# Стандарты именования и расположения файлов DocAnalyzer

## 1. Общие принципы

### 1.1 Языковые стандарты
- **Код, комментарии, докстринги**: ТОЛЬКО английский язык
- **Документация**: русский и английский языки (билингвальность)
- **Общение с пользователем**: русский язык
- **Имена файлов и директорий**: английский язык, snake_case

### 1.2 Базовые правила именования
- **snake_case** для всех файлов и директорий
- **PascalCase** для классов
- **UPPER_CASE** для констант и переменных окружения
- **lowercase** для пакетов и модулей
- Использование описательных имен вместо аббревиатур
- Максимальная длина имени файла: 50 символов

## 2. Структура проекта (PyPI-совместимая)

```
docanalyzer/                          # Корневая директория проекта
├── docanalyzer/                      # Основной Python пакет
│   ├── __init__.py                   # Инициализация пакета
│   ├── main.py                       # Точка входа приложения
│   ├── app.py                        # Главный класс приложения
│   ├── config.py                     # Конфигурация проекта
│   ├── constants.py                  # Глобальные константы
│   ├── exceptions.py                 # Пользовательские исключения
│   │
│   ├── filters/                      # Система фильтров файлов
│   │   ├── __init__.py
│   │   ├── base.py                   # Базовый абстрактный фильтр
│   │   ├── registry.py               # Реестр фильтров
│   │   ├── block_types.py            # Расширенные типы блоков
│   │   ├── text_block.py             # Модель данных блока
│   │   ├── file_structure.py         # Структура файла
│   │   ├── text_filter.py            # Фильтр текстовых файлов
│   │   ├── python_filter.py          # Фильтр Python файлов
│   │   ├── markdown_filter.py        # Фильтр Markdown файлов
│   │   └── javascript_filter.py      # Фильтр JavaScript/TypeScript
│   │
│   ├── pipeline/                     # Система пайплайнов обработки
│   │   ├── __init__.py
│   │   ├── base.py                   # Базовый пайплайн
│   │   ├── chunker.py                # Чанкер текстовых блоков
│   │   ├── chunking_config.py        # Конфигурация чанкинга
│   │   ├── pipeline_config.py        # Конфигурация пайплайна
│   │   ├── pipeline_stats.py         # Статистика пайплайна
│   │   ├── directory_pipeline.py     # Пайплайн для каталога
│   │   └── manager.py                # Менеджер пайплайнов
│   │
│   ├── wdd/                          # Управление .wdd файлами
│   │   ├── __init__.py
│   │   ├── manager.py                # Менеджер .wdd файлов
│   │   ├── models.py                 # Модели данных .wdd
│   │   └── lock_manager.py           # Управление блокировками
│   │
│   ├── watcher/                      # Мониторинг файловой системы
│   │   ├── __init__.py
│   │   ├── filesystem_watcher.py     # Наблюдатель файловой системы
│   │   ├── event_handler.py          # Обработчик событий
│   │   └── filter_rules.py           # Правила фильтрации
│   │
│   ├── commands/                     # MCP команды
│   │   ├── __init__.py
│   │   ├── base_command.py           # Базовый класс команд
│   │   │
│   │   ├── monitoring/               # Команды мониторинга
│   │   │   ├── __init__.py
│   │   │   ├── start_watching_command.py
│   │   │   ├── stop_watching_command.py
│   │   │   ├── get_watch_status_command.py
│   │   │   ├── add_watch_path_command.py
│   │   │   └── remove_watch_path_command.py
│   │   │
│   │   ├── files/                    # Команды управления файлами
│   │   │   ├── __init__.py
│   │   │   ├── process_file_command.py
│   │   │   ├── reprocess_file_command.py
│   │   │   ├── get_file_status_command.py
│   │   │   └── list_processed_files_command.py
│   │   │
│   │   ├── wdd/                      # Команды .wdd управления
│   │   │   ├── __init__.py
│   │   │   ├── scan_directory_command.py
│   │   │   ├── get_wdd_status_command.py
│   │   │   ├── cleanup_wdd_command.py
│   │   │   └── rebuild_wdd_command.py
│   │   │
│   │   └── stats/                    # Команды статистики
│   │       ├── __init__.py
│   │       ├── get_system_stats_command.py
│   │       ├── get_processing_stats_command.py
│   │       ├── get_queue_status_command.py
│   │       └── health_check_command.py
│   │
│   ├── utils/                        # Утилиты и вспомогательные функции
│   │   ├── __init__.py
│   │   ├── file_utils.py             # Работа с файлами
│   │   ├── text_utils.py             # Обработка текста
│   │   ├── hash_utils.py             # Хеширование
│   │   ├── logging_utils.py          # Настройка логирования
│   │   └── validation_utils.py       # Валидация данных
│   │
│   └── adapters/                     # Адаптеры внешних сервисов
│       ├── __init__.py
│       ├── vector_store_adapter.py   # Адаптер векторного хранилища
│       ├── metadata_adapter.py       # Адаптер метаданных
│       └── mcp_adapter.py           # Адаптер MCP прокси
│
├── tests/                            # Тестирование
│   ├── __init__.py
│   ├── conftest.py                   # Конфигурация pytest
│   ├── fixtures/                     # Тестовые данные
│   │   ├── __init__.py
│   │   ├── sample_files/             # Примеры файлов для тестов
│   │   └── test_data.py              # Тестовые данные
│   │
│   ├── unit/                         # Unit тесты
│   │   ├── __init__.py
│   │   ├── test_filters/             # Тесты фильтров
│   │   ├── test_pipeline/            # Тесты пайплайнов
│   │   ├── test_wdd/                 # Тесты .wdd управления
│   │   ├── test_watcher/             # Тесты наблюдателя
│   │   ├── test_commands/            # Тесты команд
│   │   └── test_utils/               # Тесты утилит
│   │
│   ├── integration/                  # Интеграционные тесты
│   │   ├── __init__.py
│   │   ├── test_full_pipeline.py     # Тест полного пайплайна
│   │   ├── test_vector_store.py      # Тест векторного хранилища
│   │   └── test_api_integration.py   # Тест API интеграции
│   │
│   └── performance/                  # Тесты производительности
│       ├── __init__.py
│       ├── test_chunking_speed.py    # Скорость чанкинга
│       └── test_memory_usage.py      # Использование памяти
│
├── docs/                             # Документация
│   ├── EN/                           # Английская документация
│   │   ├── api/                      # API документация
│   │   ├── architecture/             # Архитектурная документация
│   │   ├── guides/                   # Руководства пользователя
│   │   └── examples/                 # Примеры использования
│   │
│   ├── RU/                           # Русская документация
│   │   ├── api/                      # API документация
│   │   ├── architecture/             # Архитектурная документация
│   │   ├── guides/                   # Руководства пользователя
│   │   └── examples/                 # Примеры использования
│   │
│   ├── tech_spec.md                  # Техническое задание
│   ├── IMPLEMENTATION_PLAN.md        # План реализации
│   ├── CODING_STANDARDS.md           # Стандарты кодирования
│   ├── FILE_NAMING_STANDARDS.md      # Стандарты именования файлов
│   ├── PROJECT_STRUCTURE_STANDARDS.md # Стандарты структуры проекта
│   └── ARCHITECTURE_STANDARDS.md     # Архитектурные стандарты
│
├── scripts/                          # Вспомогательные скрипты
│   ├── setup.py                      # Скрипт установки (PyPI)
│   ├── build.py                      # Скрипт сборки
│   ├── lint.py                       # Скрипт проверки кода
│   └── test.py                       # Скрипт запуска тестов
│
├── examples/                         # Примеры использования
│   ├── basic_usage.py                # Базовое использование
│   ├── custom_filter.py              # Пользовательский фильтр
│   └── advanced_config.py            # Продвинутая конфигурация
│
├── .github/                          # GitHub Actions и шаблоны
│   ├── workflows/                    # CI/CD конфигурации
│   └── ISSUE_TEMPLATE.md             # Шаблон Issues
│
├── pyproject.toml                    # Современная конфигурация Python пакета
├── setup.py                          # Поддержка старых версий pip
├── setup.cfg                         # Конфигурация инструментов
├── requirements.txt                  # Зависимости для разработки
├── requirements-dev.txt              # Зависимости для разработки
├── .gitignore                        # Git исключения
├── .pylintrc                         # Конфигурация pylint
├── mypy.ini                          # Конфигурация mypy
├── pytest.ini                       # Конфигурация pytest
├── README.md                         # Основная документация
├── CHANGELOG.md                      # История изменений
├── LICENSE                           # Лицензия
└── MANIFEST.in                       # Манифест для сборки пакета
```

## 3. Стандарты именования файлов

### 3.1 Python модули (.py файлы)

#### Основные правила:
- **snake_case** обязательно
- Имя отражает содержимое модуля
- Один основной класс на файл
- Имя файла соответствует основному классу в snake_case

#### Примеры:
```
text_filter.py          → TextFilter (основной класс)
python_filter.py        → PythonFilter (основной класс)
pipeline_config.py      → PipelineConfig (основной класс)
filesystem_watcher.py   → FileSystemWatcher (основной класс)
start_watching_command.py → StartWatchingCommand (основной класс)
```

#### Исключения:
```
__init__.py             → Инициализация пакета
main.py                 → Точка входа приложения
config.py               → Конфигурационные классы
constants.py            → Константы
exceptions.py           → Пользовательские исключения
```

### 3.2 Специальные типы файлов

#### Тестовые файлы:
```
test_text_filter.py           → Тесты для TextFilter
test_pipeline_integration.py  → Интеграционные тесты пайплайна
test_performance_chunking.py  → Тесты производительности чанкинга
```

#### Конфигурационные файлы:
```
pyproject.toml          → Современная конфигурация Python пакета
setup.py                → Сборка пакета для PyPI
setup.cfg               → Конфигурация инструментов
requirements.txt        → Зависимости продакшн
requirements-dev.txt    → Зависимости разработки
```

#### Файлы CI/CD:
```
.github/workflows/test.yml       → CI тестирование
.github/workflows/publish.yml    → Публикация в PyPI
.github/workflows/lint.yml       → Проверка качества кода
```

### 3.3 Документация

#### Структура документации:
```
docs/EN/api/filters.md           → API документация фильтров (англ.)
docs/RU/api/filters.md           → API документация фильтров (рус.)
docs/EN/guides/quick_start.md    → Быстрый старт (англ.)
docs/RU/guides/quick_start.md    → Быстрый старт (рус.)
```

#### Специальные файлы документации:
```
README.md               → Основная документация проекта
CHANGELOG.md            → История изменений
LICENSE                 → Файл лицензии
MANIFEST.in            → Манифест для включения файлов в пакет
```

## 4. Стандарты директорий

### 4.1 Принципы организации

#### Группировка по функциональности:
- **filters/** → Все компоненты системы фильтрации
- **pipeline/** → Компоненты пайплайна обработки
- **commands/** → MCP команды с подкатегориями
- **wdd/** → Управление .wdd файлами
- **watcher/** → Мониторинг файловой системы

#### Группировка по типу:
- **tests/** → Все тесты с подкатегориями
- **docs/** → Вся документация с языковыми версиями
- **utils/** → Вспомогательные утилиты
- **examples/** → Примеры использования

### 4.2 Правила именования директорий

#### Основные правила:
- **snake_case** обязательно
- Множественное число для коллекций (`filters`, `commands`, `tests`)
- Единственное число для концептуальных понятий (`pipeline`, `watcher`)
- Максимум 3 уровня вложенности
- Логическая группировка по назначению

#### Примеры правильного именования:
```
✅ filters/             → Множественное число для коллекции
✅ pipeline/            → Единственное число для концепции
✅ commands/monitoring/ → Логическая группировка
✅ tests/unit/          → Типологическая группировка
✅ docs/EN/api/         → Языковая и типологическая группировка
```

#### Примеры неправильного именования:
```
❌ filter/              → Должно быть множественное число
❌ pipelines/           → Должно быть единственное число
❌ command/             → Должно быть множественное число
❌ test/                → Должно быть множественное число
❌ documentation/       → Слишком длинное, должно быть docs/
```

## 5. PyPI совместимость

### 5.1 Обязательные файлы для PyPI

#### В корне проекта:
```
pyproject.toml          → Современная конфигурация (PEP 518)
setup.py                → Обратная совместимость
README.md               → Описание пакета
LICENSE                 → Лицензия
MANIFEST.in            → Включение дополнительных файлов
```

#### Пример pyproject.toml:
```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "docanalyzer"
authors = [{name = "Developer Name", email = "dev@example.com"}]
description = "Automated file monitoring and chunking for vector databases"
readme = "README.md"
license = {file = "LICENSE"}
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dynamic = ["version"]
dependencies = [
    "watchdog>=2.1.0",
    "pathspec>=0.9.0",
    "fastapi>=0.68.0",
    "vector-store-client>=1.0.0",
    "chunk-metadata-adapter>=1.0.0",
    "mcp-proxy-adapter>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0",
    "pytest-cov>=2.0",
    "mypy>=0.910",
    "black>=21.0",
    "pylint>=2.9",
    "isort>=5.9",
]

[project.urls]
Homepage = "https://github.com/user/docanalyzer"
Repository = "https://github.com/user/docanalyzer"
Documentation = "https://docanalyzer.readthedocs.io"

[project.scripts]
docanalyzer = "docanalyzer.main:main"

[tool.setuptools.packages.find]
include = ["docanalyzer*"]
exclude = ["tests*"]
```

### 5.2 Структура пакета

#### Основной пакет:
```
docanalyzer/                    → Основной пакет
├── __init__.py                → Версия и публичный API
├── main.py                    → Точка входа
└── ...                        → Остальные модули
```

#### Пример __init__.py:
```python
"""
DocAnalyzer - Automated file monitoring and chunking for vector databases.

This package provides automated monitoring of file systems, intelligent
chunking of various file types, and seamless integration with vector
databases for semantic search capabilities.
"""

__version__ = "1.0.0"
__author__ = "Developer Name"
__email__ = "dev@example.com"

# Public API exports
from .app import DocAnalyzerApp
from .config import DocAnalyzerConfig
from .exceptions import DocAnalyzerError

# Configure package-level logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "DocAnalyzerApp",
    "DocAnalyzerConfig", 
    "DocAnalyzerError",
    "__version__",
]
```

## 6. Конвенции именования по типам компонентов

### 6.1 Классы

#### Основные классы:
```python
class TextFilter:              # Фильтр файлов
class PipelineManager:         # Менеджер пайплайнов
class WatchDirectoryManager:   # Менеджер каталогов
class StartWatchingCommand:    # MCP команда
```

#### Абстрактные классы:
```python
class BaseFileFilter:          # Базовый фильтр
class BasePipeline:           # Базовый пайплайн  
class BaseCommand:            # Базовая команда
```

#### Модели данных:
```python
class TextBlock:              # Блок текста
class FileStructure:          # Структура файла
class PipelineConfig:         # Конфигурация пайплайна
```

#### Исключения:
```python
class DocAnalyzerError:       # Базовое исключение
class FilterError:            # Ошибка фильтрации
class PipelineError:         # Ошибка пайплайна
```

### 6.2 Функции и методы

#### Публичные методы:
```python
def process_file(self, path: Path) -> FileStructure:
def start_watching(self, paths: List[Path]) -> None:
def get_status(self) -> Dict[str, Any]:
def validate_config(self, config: Dict[str, Any]) -> bool:
```

#### Приватные методы:
```python
def _parse_content(self, content: str) -> List[TextBlock]:
def _calculate_metrics(self, block: TextBlock) -> float:
def _setup_logging(self) -> None:
def _validate_input(self, input_data: Any) -> None:
```

#### Статические методы:
```python
@staticmethod
def create_from_dict(data: Dict[str, Any]) -> 'ClassName':
@staticmethod
def get_supported_extensions() -> List[str]:
@staticmethod
def validate_file_path(path: Path) -> bool:
```

### 6.3 Переменные и константы

#### Константы модулей:
```python
DEFAULT_CHUNK_SIZE: int = 1000
MAX_FILE_SIZE: int = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS: List[str] = ['.py', '.md', '.txt']
DEFAULT_CONFIG_PATH: str = './config.json'
```

#### Переменные окружения:
```python
DOCANALYZER_CONFIG_PATH = os.getenv('DOCANALYZER_CONFIG_PATH')
DOCANALYZER_LOG_LEVEL = os.getenv('DOCANALYZER_LOG_LEVEL', 'INFO')
DOCANALYZER_VECTOR_STORE_URL = os.getenv('DOCANALYZER_VECTOR_STORE_URL')
```

#### Переменные экземпляра:
```python
self._file_path: Path              # Путь к файлу
self._config: Dict[str, Any]       # Конфигурация
self._is_active: bool              # Состояние активности
self._processed_count: int         # Счетчик обработанных
```

## 7. Соглашения для команд проекта

### 7.1 Скрипты управления

#### В директории scripts/:
```bash
scripts/build.py              # Сборка проекта
scripts/lint.py               # Проверка качества кода
scripts/test.py               # Запуск тестов
scripts/setup.py              # Первоначальная настройка
```

#### Команды разработки:
```bash
# Проверка кода
python scripts/lint.py

# Запуск тестов
python scripts/test.py --coverage

# Сборка пакета
python scripts/build.py --wheel

# Публикация в PyPI
python scripts/publish.py --test-pypi
```

### 7.2 Команды через CLI

#### Основной интерфейс:
```bash
docanalyzer start --config /path/to/config.json
docanalyzer stop
docanalyzer status
docanalyzer add-path /path/to/watch
docanalyzer remove-path /path/to/watch
```

## 8. Контроль качества именования

### 8.1 Автоматические проверки

#### Линтеры и форматтеры:
```bash
# Проверка стиля именования
pylint docanalyzer/ --disable=all --enable=invalid-name,bad-naming-style

# Проверка импортов
isort --check-only docanalyzer/

# Форматирование кода
black docanalyzer/

# Проверка типов
mypy docanalyzer/
```

### 8.2 Pre-commit хуки

#### .pre-commit-config.yaml:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 21.9b0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.9.3
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/pylint
    rev: v2.11.1
    hooks:
      - id: pylint
        args: [--disable=all, --enable=invalid-name,bad-naming-style]
```

## 9. Заключение

### 9.1 Ключевые принципы
- **Последовательность**: Все файлы следуют единым правилам именования
- **Читаемость**: Имена ясно отражают назначение компонентов
- **PyPI совместимость**: Структура готова для публикации
- **Масштабируемость**: Легко добавлять новые компоненты
- **Международность**: Поддержка многоязычной документации

### 9.2 Преимущества структуры
- Автоматическая совместимость с инструментами Python экосистемы
- Простая навигация для разработчиков
- Готовность к публикации в PyPI без изменений
- Четкое разделение функциональности по директориям
- Соответствие современным стандартам Python разработки 