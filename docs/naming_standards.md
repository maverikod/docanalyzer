# Стандарты именования DocAnalyzer

**Дата создания:** 2024-12-19  
**Версия:** 1.0.0  
**Статус:** Активный  

---

## 📋 ОБЩИЕ ПРИНЦИПЫ

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

---

## 🏗️ СТРУКТУРА ПРОЕКТА

### 2.1 Именование директорий
```
docanalyzer/                          # Корневая директория проекта
├── docanalyzer/                      # Основной Python пакет
│   ├── filters/                      # Система фильтров файлов
│   ├── pipeline/                     # Система пайплайнов обработки
│   ├── commands/                     # MCP команды
│   │   ├── monitoring/               # Команды мониторинга
│   │   ├── files/                    # Команды управления файлами
│   │   ├── wdd/                      # Команды .wdd управления
│   │   └── stats/                    # Команды статистики
│   ├── wdd/                          # Управление .wdd файлами
│   ├── watcher/                      # Мониторинг файловой системы
│   ├── utils/                        # Утилиты и вспомогательные функции
│   └── adapters/                     # Адаптеры внешних сервисов
├── tests/                            # Тестирование
│   ├── unit/                         # Unit тесты
│   ├── integration/                  # Интеграционные тесты
│   └── performance/                  # Тесты производительности
├── docs/                             # Документация
└── scripts/                          # Вспомогательные скрипты
```

### 2.2 Именование файлов
- **snake_case** обязательно
- Имя отражает содержимое модуля
- Один основной класс на файл
- Имя файла соответствует основному классу в snake_case

**Примеры:**
```
text_filter.py          → TextFilter (основной класс)
python_filter.py        → PythonFilter (основной класс)
pipeline_config.py      → PipelineConfig (основной класс)
filesystem_watcher.py   → FileSystemWatcher (основной класс)
start_watching_command.py → StartWatchingCommand (основной класс)
```

---

## 🐍 PYTHON КОД

### 3.1 Классы
- **PascalCase** для имен классов
- Описательные имена, отражающие назначение
- Избегать аббревиатур

**Примеры:**
```python
class FileProcessor:          # ✅ Правильно
class TextFilter:             # ✅ Правильно
class DirectoryOrchestrator:  # ✅ Правильно
class FileInfo:               # ✅ Правильно

class FP:                     # ❌ Неправильно (аббревиатура)
class file_processor:         # ❌ Неправильно (snake_case)
class Fileprocessor:          # ❌ Неправильно (без разделения)
```

### 3.2 Методы
- **snake_case** для имен методов
- Глаголы или глагольные фразы
- Описательные имена, отражающие действие

**Примеры:**
```python
def process_file(self):           # ✅ Правильно
def get_file_info(self):          # ✅ Правильно
def validate_configuration(self): # ✅ Правильно
def create_semantic_chunk(self):  # ✅ Правильно

def ProcessFile(self):            # ❌ Неправильно (PascalCase)
def processfile(self):            # ❌ Неправильно (без разделения)
def proc(self):                   # ❌ Неправильно (аббревиатура)
```

### 3.3 Переменные и атрибуты
- **snake_case** для переменных и атрибутов
- Описательные имена
- Избегать однобуквенных имен (кроме счетчиков)

**Примеры:**
```python
file_path = "/path/to/file"       # ✅ Правильно
processing_status = "completed"   # ✅ Правильно
max_retry_attempts = 3           # ✅ Правильно
semantic_chunk_data = {}         # ✅ Правильно

filePath = "/path/to/file"        # ❌ Неправильно (camelCase)
fp = "/path/to/file"              # ❌ Неправильно (аббревиатура)
x = 3                            # ❌ Неправильно (однобуквенное)
```

### 3.4 Константы
- **UPPER_CASE** для констант
- Подчеркивания для разделения слов

**Примеры:**
```python
DEFAULT_TIMEOUT = 30              # ✅ Правильно
MAX_FILE_SIZE = 1024 * 1024      # ✅ Правильно
SUPPORTED_EXTENSIONS = [".txt", ".md"]  # ✅ Правильно
DEFAULT_CONFIG_PATH = "/etc/docanalyzer/config.json"  # ✅ Правильно

default_timeout = 30              # ❌ Неправильно (snake_case)
MAXFILESIZE = 1024 * 1024        # ❌ Неправильно (без разделения)
```

### 3.5 Функции
- **snake_case** для имен функций
- Глаголы или глагольные фразы
- Описательные имена

**Примеры:**
```python
def validate_file_path(path):     # ✅ Правильно
def create_processing_pipeline(): # ✅ Правильно
def get_system_metrics():         # ✅ Правильно
def normalize_text_content(text): # ✅ Правильно

def ValidateFilePath(path):       # ❌ Неправильно (PascalCase)
def createProcessingPipeline():   # ❌ Неправильно (camelCase)
def get_metrics():                # ❌ Неправильно (недостаточно описательно)
```

---

## 🗄️ МОДЕЛИ ДАННЫХ

### 4.1 Классы моделей
- **PascalCase** для имен классов моделей
- Суффикс, отражающий тип модели

**Примеры:**
```python
class FileInfo:                   # ✅ Правильно
class ProcessingResult:           # ✅ Правильно
class SemanticChunk:              # ✅ Правильно
class DatabaseRecord:             # ✅ Правильно
class ErrorInfo:                  # ✅ Правильно
```

### 4.2 Поля моделей
- **snake_case** для имен полей
- Описательные имена
- Единообразие в именовании похожих полей

**Примеры:**
```python
class FileInfo:
    file_path: str                # ✅ Правильно
    file_size: int                # ✅ Правильно
    modification_time: datetime   # ✅ Правильно
    processing_status: str        # ✅ Правильно
    metadata: Dict[str, Any]      # ✅ Правильно

class ProcessingResult:
    success: bool                 # ✅ Правильно
    error_message: str            # ✅ Правильно
    processing_time: float        # ✅ Правильно
    result_data: Dict[str, Any]   # ✅ Правильно
```

### 4.3 Enum классы
- **PascalCase** для имен enum классов
- **UPPER_CASE** для значений enum

**Примеры:**
```python
class ProcessingStatus(Enum):
    PENDING = "pending"            # ✅ Правильно
    PROCESSING = "processing"      # ✅ Правильно
    COMPLETED = "completed"        # ✅ Правильно
    FAILED = "failed"              # ✅ Правильно

class ErrorCategory(Enum):
    CONFIGURATION = "configuration"  # ✅ Правильно
    PROCESSING = "processing"        # ✅ Правильно
    SYSTEM = "system"                # ✅ Правильно
```

---

## 🔧 СЕРВИСЫ И КОМПОНЕНТЫ

### 5.1 Классы сервисов
- **PascalCase** для имен классов сервисов
- Суффикс, отражающий тип сервиса

**Примеры:**
```python
class FileProcessor:              # ✅ Правильно
class DirectoryScanner:           # ✅ Правильно
class VectorStoreAdapter:         # ✅ Правильно
class HealthChecker:              # ✅ Правильно
class MetricsCollector:           # ✅ Правильно
```

### 5.2 Методы сервисов
- **snake_case** для имен методов
- Префикс, отражающий действие
- Единообразие в именовании похожих операций

**Примеры:**
```python
class FileProcessor:
    def process_file(self):           # ✅ Правильно
    def validate_file(self):          # ✅ Правильно
    def get_processing_status(self):  # ✅ Правильно
    def update_metadata(self):        # ✅ Правильно

class DirectoryScanner:
    def scan_directory(self):         # ✅ Правильно
    def get_file_list(self):          # ✅ Правильно
    def filter_files(self):           # ✅ Правильно
    def update_scan_status(self):     # ✅ Правильно
```

---

## 📊 КОМАНДЫ И API

### 6.1 Классы команд
- **PascalCase** для имен классов команд
- Суффикс "Command" для команд

**Примеры:**
```python
class HealthCheckCommand:         # ✅ Правильно
class ProcessFileCommand:         # ✅ Правильно
class GetStatsCommand:            # ✅ Правильно
class StartWatchingCommand:       # ✅ Правильно
```

### 6.2 Результаты команд
- **PascalCase** для имен классов результатов
- Суффикс "Result" для результатов

**Примеры:**
```python
class HealthCheckResult:          # ✅ Правильно
class ProcessingResult:           # ✅ Правильно
class StatsResult:                # ✅ Правильно
class WatchingStatusResult:       # ✅ Правильно
```

### 6.3 API методы
- **snake_case** для имен API методов
- HTTP-стиль именования для REST API

**Примеры:**
```python
def get_health_status(self):      # ✅ Правильно
def process_file_content(self):   # ✅ Правильно
def get_processing_stats(self):   # ✅ Правильно
def start_file_watching(self):    # ✅ Правильно
```

---

## 🧪 ТЕСТЫ

### 7.1 Тестовые файлы
- Префикс "test_" для тестовых файлов
- Имя соответствует тестируемому модулю

**Примеры:**
```
test_file_processor.py            # ✅ Правильно
test_directory_scanner.py         # ✅ Правильно
test_vector_store_adapter.py      # ✅ Правильно
test_health_checker.py            # ✅ Правильно
```

### 7.2 Тестовые классы
- Префикс "Test" для тестовых классов
- Имя соответствует тестируемому классу

**Примеры:**
```python
class TestFileProcessor:          # ✅ Правильно
class TestDirectoryScanner:       # ✅ Правильно
class TestVectorStoreAdapter:     # ✅ Правильно
class TestHealthChecker:          # ✅ Правильно
```

### 7.3 Тестовые методы
- Префикс "test_" для тестовых методов
- Описательные имена, отражающие тестируемую функциональность

**Примеры:**
```python
def test_process_file_success(self):      # ✅ Правильно
def test_process_file_invalid_path(self): # ✅ Правильно
def test_get_processing_status(self):     # ✅ Правильно
def test_validate_configuration(self):    # ✅ Правильно
```

---

## 📁 КОНФИГУРАЦИЯ

### 8.1 Конфигурационные классы
- **PascalCase** для имен конфигурационных классов
- Суффикс "Config" для конфигураций

**Примеры:**
```python
class ServerConfig:               # ✅ Правильно
class DatabaseConfig:             # ✅ Правильно
class ProcessingConfig:           # ✅ Правильно
class LoggingConfig:              # ✅ Правильно
```

### 8.2 Конфигурационные поля
- **snake_case** для имен конфигурационных полей
- Описательные имена

**Примеры:**
```python
class ServerConfig:
    host: str                     # ✅ Правильно
    port: int                     # ✅ Правильно
    debug_mode: bool              # ✅ Правильно
    log_level: str                # ✅ Правильно
```

---

## 🚨 ИСКЛЮЧЕНИЯ И ОШИБКИ

### 9.1 Классы исключений
- **PascalCase** для имен классов исключений
- Суффикс "Error" для исключений

**Примеры:**
```python
class ConfigurationError:         # ✅ Правильно
class ProcessingError:            # ✅ Правильно
class ValidationError:            # ✅ Правильно
class ConnectionError:            # ✅ Правильно
```

### 9.2 Поля ошибок
- **snake_case** для имен полей ошибок
- Стандартные имена для общих полей

**Примеры:**
```python
class ProcessingError:
    error_code: str               # ✅ Правильно
    error_message: str            # ✅ Правильно
    error_category: str           # ✅ Правильно
    timestamp: datetime           # ✅ Правильно
```

---

## 📋 ПРОВЕРКА СООТВЕТСТВИЯ

### 10.1 Автоматические проверки
- Использование линтеров (flake8, pylint)
- Проверка типов (mypy)
- Форматирование кода (black)

### 10.2 Ручные проверки
- Код-ревью с фокусом на именование
- Проверка соответствия стандартам
- Документирование отклонений

### 10.3 Инструменты
```bash
# Проверка стиля кода
flake8 docanalyzer/

# Проверка типов
mypy docanalyzer/

# Форматирование кода
black docanalyzer/

# Сортировка импортов
isort docanalyzer/
```

---

## 📝 ПРИМЕРЫ ПРИМЕНЕНИЯ

### 11.1 До применения стандартов
```python
class fileProcessor:              # ❌ Неправильно
    def ProcessFile(self, fp):    # ❌ Неправильно
        self.status = "done"      # ❌ Неправильно
        return self.data          # ❌ Неправильно
```

### 11.2 После применения стандартов
```python
class FileProcessor:              # ✅ Правильно
    def process_file(self, file_path):  # ✅ Правильно
        self.processing_status = "completed"  # ✅ Правильно
        return self.result_data   # ✅ Правильно
```

---

*Стандарты именования DocAnalyzer - версия 1.0.0* 