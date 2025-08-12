# Object Model - File Watcher Service

## Core Domain Objects

### 1. File System Objects

#### Directory
```python
class Directory:
    path: str                    # Путь к каталогу
    is_watched: bool             # Отслеживается ли каталог
    last_scan_time: datetime     # Время последнего сканирования
    lock_file_path: str          # Путь к lock файлу
    supported_formats: List[str] # Поддерживаемые форматы файлов
```

#### FileInfo
```python
class FileInfo:
    path: str                    # Полный путь к файлу
    filename: str                # Имя файла
    size: int                    # Размер файла в байтах
    modified_time: datetime      # Время последнего изменения
    created_time: datetime       # Время создания
    extension: str               # Расширение файла
    is_supported: bool           # Поддерживается ли формат
```

#### LockFile
```python
class LockFile:
    process_id: int              # PID процесса
    created_at: datetime         # Время создания lock
    directory: str               # Путь к каталогу
    status: str                  # Статус (active, completed, error)
    lock_file_path: str          # Путь к lock файлу
```

### 2. Processing Objects

#### SemanticChunk (Основная модель метаданных)
```python
class SemanticChunk:
    # Идентификаторы
    uuid: ChunkId                    # Уникальный идентификатор чанка
    source_id: ChunkId               # Идентификатор источника
    project: Optional[str]           # Название проекта
    task_id: ChunkId                 # Идентификатор задачи
    subtask_id: ChunkId              # Идентификатор подзадачи
    unit_id: ChunkId                 # Идентификатор единицы обработки
    block_id: ChunkId                # Идентификатор исходного блока
    
    # Основные поля
    type: ChunkType                  # Тип чанка (DocBlock, CodeBlock, Message, etc.)
    role: ChunkRole                  # Роль в системе (system, user, assistant, etc.)
    language: LanguageEnum           # Язык содержимого
    body: str                        # Исходный текст чанка
    text: Optional[str]              # Нормализованный текст для поиска
    summary: Optional[str]           # Краткое описание чанка
    
    # Позиционирование
    ordinal: int                     # Порядок чанка в источнике
    start: int                       # Начальная позиция в источнике
    end: int                         # Конечная позиция в источнике
    source_lines_start: int          # Начальная строка в файле
    source_lines_end: int            # Конечная строка в файле
    block_index: int                 # Индекс блока в документе
    
    # Метаданные файла
    source_path: Optional[str]       # Путь к исходному файлу
    block_type: BlockType            # Тип исходного блока
    chunking_version: Optional[str]  # Версия алгоритма чанкинга
    
    # Бизнес-поля
    category: Optional[str]          # Бизнес-категория
    title: Optional[str]             # Заголовок
    year: Optional[int]              # Год
    is_public: Optional[bool]        # Публичность
    is_deleted: Optional[bool]       # Флаг удаления
    source: Optional[str]            # Источник данных
    
    # Коллекционные поля
    tags: List[str]                  # Теги для классификации
    links: List[str]                 # Ссылки на другие чанки
    block_meta: Dict[str, Any]       # Дополнительные метаданные блока
    
    # Статус и время
    status: ChunkStatus              # Статус обработки
    created_at: str                  # Время создания (ISO8601)
    
    # Метрики качества
    quality_score: Optional[float]   # Оценка качества [0, 1]
    coverage: Optional[float]        # Оценка покрытия [0, 1]
    cohesion: Optional[float]        # Оценка связности [0, 1]
    boundary_prev: Optional[float]   # Схожесть с предыдущим чанком
    boundary_next: Optional[float]   # Схожесть со следующим чанком
    
    # Использование
    used_in_generation: bool         # Использовался ли в генерации
    feedback_accepted: int           # Количество принятий
    feedback_rejected: int           # Количество отклонений
    feedback_modifications: int      # Количество модификаций
    
    # Векторные представления
    embedding: Optional[List[float]] # Векторное представление
    
    # Вычисляемые поля
    is_code_chunk: bool              # Содержит ли код
    sha256: str                      # SHA256 хеш текста
```

#### ProcessingBlock
```python
class ProcessingBlock:
    content: str                 # Содержимое блока
    block_type: BlockType        # Тип блока (paragraph, message, section, other)
    start_position: int          # Начальная позиция в файле
    end_position: int            # Конечная позиция в файле
    source_lines_start: int      # Начальная строка в файле
    source_lines_end: int        # Конечная строка в файле
    block_index: int             # Индекс блока в документе
    metadata: Dict[str, Any]     # Дополнительные метаданные блока
```

#### FileProcessingResult
```python
class FileProcessingResult:
    file_path: str               # Путь к обработанному файлу
    blocks: List[ProcessingBlock] # Список блоков
    processing_time: float       # Время обработки
    status: str                  # Статус обработки
    error_message: Optional[str] # Сообщение об ошибке
```

#### BatchProcessingResult
```python
class BatchProcessingResult:
    batch_id: str                # ID партии
    blocks: List[ProcessingBlock] # Блоки в партии
    chunks: List[SemanticChunk]  # Созданные чанки с полными метаданными
    processing_time: float       # Время обработки
    status: str                  # Статус обработки
    chunk_count: int             # Количество созданных чанков
    total_tokens: int            # Общее количество токенов
```

### 3. Database Objects

#### DatabaseFileRecord
```python
class DatabaseFileRecord:
    file_path: str               # Путь к файлу
    indexed_at: datetime         # Время индексации
    modified_time: datetime      # Время последнего изменения
    file_size: int               # Размер файла
    chunk_count: int             # Количество чанков
    status: str                  # Статус в базе
```

#### ProcessingStatistics
```python
class ProcessingStatistics:
    total_files: int             # Общее количество файлов
    processed_files: int         # Обработанных файлов
    failed_files: int            # Файлов с ошибками
    total_chunks: int            # Общее количество чанков
    processing_time: float       # Общее время обработки
```

### 4. Configuration Objects

#### FileWatcherConfig
```python
class FileWatcherConfig:
    directories: List[str]       # Список каталогов для отслеживания
    scan_interval: int           # Интервал сканирования в секундах
    lock_timeout: int            # Таймаут блокировки в секундах
    max_processes: int           # Максимальное количество процессов
    supported_formats: List[str] # Поддерживаемые форматы
    max_block_size: int          # Максимальный размер блока
    max_blocks_per_batch: int    # Максимальное количество блоков в партии
    recursive_scan: bool         # Рекурсивное сканирование
```

#### ServiceConfig
```python
class ServiceConfig:
    vector_store: ServiceEndpoint # Конфигурация векторной базы
    chunker: ServiceEndpoint      # Конфигурация чанкера
    embedding: ServiceEndpoint    # Конфигурация векторизатора
```

#### ServiceEndpoint
```python
class ServiceEndpoint:
    base_url: str                # Базовый URL
    port: int                    # Порт
    timeout: int                 # Таймаут в секундах
```

## Service Layer Objects

### 1. Lock Manager
```python
class LockManager:
    def create_lock(directory: str) -> LockFile
    def remove_lock(lock_file: LockFile) -> bool
    def check_lock(directory: str) -> Optional[LockFile]
    def cleanup_orphaned_locks() -> List[str]
    def is_process_alive(pid: int) -> bool
```

### 2. Directory Scanner
```python
class DirectoryScanner:
    def scan_directory(directory: str) -> List[FileInfo]
    def filter_new_files(files: List[FileInfo], db_files: List[DatabaseFileRecord]) -> List[FileInfo]
    def is_file_supported(file_info: FileInfo) -> bool
    def get_file_metadata(file_path: str) -> FileInfo
```

### 3. File Processor
```python
class FileProcessor:
    def process_file(file_path: str) -> FileProcessingResult
    def extract_blocks(content: str) -> List[ProcessingBlock]
    def split_blocks(blocks: List[ProcessingBlock], max_size: int) -> List[List[ProcessingBlock]]
    def validate_blocks(blocks: List[ProcessingBlock]) -> bool
```

### 4. Chunking Manager
```python
class ChunkingManager:
    def chunk_blocks(blocks: List[ProcessingBlock]) -> List[SemanticChunk]
    def process_batch(blocks: List[ProcessingBlock]) -> BatchProcessingResult
    def save_chunks(chunks: List[SemanticChunk]) -> bool
    def rollback_file_chunks(file_path: str) -> bool
```

### 5. Database Manager
```python
class DatabaseManager:
    def get_file_records(directory: str) -> List[DatabaseFileRecord]
    def save_file_record(record: DatabaseFileRecord) -> bool
    def delete_file_record(file_path: str) -> bool
    def update_file_record(record: DatabaseFileRecord) -> bool
    def get_processing_statistics() -> ProcessingStatistics
```

### 6. Vector Store Client Wrapper
```python
class VectorStoreClientWrapper:
    def __init__(config: ServiceConfig)
    def create_chunks(chunks: List[SemanticChunk]) -> bool
    def search_chunks(query: str) -> List[SemanticChunk]
    def delete_file_chunks(file_path: str) -> bool
    def health_check() -> Dict[str, Any]
    def chunk_text(text: str, source_id: str, **metadata) -> List[SemanticChunk]
    def get_chunk_statistics(metadata_filter: Dict[str, Any]) -> Dict[str, Any]
```

## Process Management Objects

### 1. Process Manager
```python
class ProcessManager:
    def start_processing(directory: str) -> str
    def stop_processing(process_id: str) -> bool
    def get_process_status(process_id: str) -> ProcessStatus
    def list_active_processes() -> List[ProcessStatus]
    def cleanup_finished_processes() -> List[str]
```

### 2. Process Status
```python
class ProcessStatus:
    process_id: str              # ID процесса
    directory: str               # Обрабатываемый каталог
    status: str                  # Статус (running, completed, failed)
    start_time: datetime         # Время начала
    end_time: Optional[datetime] # Время завершения
    progress: float              # Прогресс (0.0 - 1.0)
    error_message: Optional[str] # Сообщение об ошибке
```

## Error Handling Objects

### 1. ProcessingError
```python
class ProcessingError:
    error_type: str              # Тип ошибки
    file_path: Optional[str]     # Путь к файлу
    error_message: str           # Сообщение об ошибке
    timestamp: datetime          # Время возникновения
    stack_trace: Optional[str]   # Stack trace
```

### 2. Error Handler
```python
class ErrorHandler:
    def handle_file_error(error: ProcessingError) -> bool
    def handle_directory_error(error: ProcessingError) -> bool
    def handle_system_error(error: ProcessingError) -> bool
    def log_error(error: ProcessingError) -> None
    def should_retry(error: ProcessingError) -> bool
```

## Monitoring Objects

### 1. Metrics Collector
```python
class MetricsCollector:
    def record_file_processed(file_path: str, processing_time: float) -> None
    def record_chunks_created(file_path: str, chunk_count: int) -> None
    def record_error(error: ProcessingError) -> None
    def get_metrics() -> Dict[str, Any]
    def reset_metrics() -> None
```

### 2. Health Checker
```python
class HealthChecker:
    def check_vector_store_health() -> HealthStatus
    def check_chunker_health() -> HealthStatus
    def check_embedding_health() -> HealthStatus
    def check_system_health() -> HealthStatus
    def get_overall_health() -> HealthStatus
```

#### HealthStatus
```python
class HealthStatus:
    service_name: str            # Имя сервиса
    status: str                  # Статус (healthy, degraded, down)
    response_time: float         # Время отклика
    last_check: datetime         # Время последней проверки
    error_message: Optional[str] # Сообщение об ошибке
``` 