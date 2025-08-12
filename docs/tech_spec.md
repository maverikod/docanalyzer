# File Watcher Service - Technical Specification

## Overview
File Watcher Service - сервис для отслеживания файлов в каталогах с механизмом блокировки для предотвращения одновременной обработки одного каталога разными процессами.

**Архитектурная основа**: Сервис построен на базе `mcp_proxy_adapter` фреймворка, который предоставляет:
- Систему конфигурации (`mcp_proxy_adapter.core.settings`)
- Систему логирования (`mcp_proxy_adapter.core.logging`)
- Управление конфигурацией (`mcp_proxy_adapter.config`)
- Базовую инфраструктуру для MCP команд

**Интеграционный подход**: Вместо создания независимых модулей, сервис расширяет существующую инфраструктуру фреймворка специфичной функциональностью для DocAnalyzer.

## Architecture

### Process Architecture

#### Main Process (Master)
- **Роль**: Координатор и мониторинг
- **Функции**:
  - Запуск дочерних процессов сканирования
  - Мониторинг состояния дочерних процессов
  - Управление жизненным циклом процессов
  - Обработка сигналов завершения
  - Предоставление API для управления

#### Child Processes (Workers)
- **Роль**: Выполнение сканирования каталогов
- **Функции**:
  - Сканирование конкретного каталога
  - Обработка файлов (блокировка, чанкинг, сохранение)
  - Отчетность о прогрессе
  - Обработка ошибок на уровне каталога

#### Process Communication
- **Механизм**: IPC (Inter-Process Communication)
- **Протокол**: JSON-RPC через сокеты или pipes
- **Сообщения**:
  - Статус процесса (running, completed, failed)
  - Прогресс обработки (файлы обработаны/всего)
  - Ошибки и предупреждения
  - Запросы на завершение

#### Process Management
- **Параллелизм**: Несколько дочерних процессов одновременно
- **Контроль**: Главный процесс может прервать дочерние
- **Изоляция**: Каждый процесс работает независимо
- **Восстановление**: Автоматический перезапуск при сбоях

### Core Components

#### 1. Configuration Integration Layer
- Интегрируется с `mcp_proxy_adapter.core.settings`
- Расширяет конфигурацию специфичными настройками DocAnalyzer
- Предоставляет валидацию дополнительных параметров
- Обеспечивает совместимость с существующим фреймворком

#### 2. Logging Integration Layer
- Интегрируется с `mcp_proxy_adapter.core.logging`
- Расширяет систему логирования для DocAnalyzer
- Предоставляет специализированные логгеры для компонентов
- Обеспечивает единообразное логирование

#### 3. Lock Manager
- Управляет lock файлами в каталогах
- Создает/удаляет lock файлы с PID процесса
- Проверяет существование процессов по PID
- Очищает orphaned lock файлы

#### 4. Directory Scanner
- Сканирует каталоги из конфигурации
- Проверяет lock файлы перед обработкой
- Составляет список файлов для индексации
- Работает в отдельном процессе

#### 5. Index Manager
- Управляет процессом индексации
- Запрашивает базу данных перед индексацией
- Координирует работу с Directory Scanner
- Обрабатывает результаты индексации

#### 6. Process Manager
- Управляет отдельными процессами сканирования
- Мониторит состояние процессов
- Обрабатывает завершение процессов

## Lock Mechanism

### Lock File Structure
```json
{
  "process_id": 12345,
  "created_at": "2024-01-15T10:30:00Z",
  "directory": "/path/to/directory",
  "status": "active",
  "pid_file": "/path/to/directory/.lock"
}
```

### Lock File Operations

#### Creating Lock
1. Проверяем существование lock файла
2. Если файл существует - читаем PID
3. Проверяем существование процесса с этим PID
4. Если процесс не найден - удаляем lock файл
5. Создаем новый lock файл с текущим PID
6. Устанавливаем файловую блокировку

#### Removing Lock
1. Проверяем владение lock файлом
2. Снимаем файловую блокировку
3. Удаляем lock файл

#### Checking Lock
1. Читаем lock файл
2. Проверяем существование процесса по PID
3. Если процесс не найден - считаем lock недействительным

## Workflow

### Process Management Flow

#### Main Process Workflow
1. **Initialization**
   - Загрузка конфигурации
   - Инициализация сервисов
   - Запуск API сервера

2. **Directory Monitoring**
   - Чтение списка каталогов из конфигурации
   - Запуск дочерних процессов для каждого каталога
   - Мониторинг состояния процессов

3. **Process Control**
   - Обработка запросов на запуск/остановку сканирования
   - Управление жизненным циклом дочерних процессов
   - Обработка сигналов завершения

#### Child Process Workflow
1. **Process Initialization**
   - Получение параметров каталога
   - Инициализация сервисов для обработки
   - Установка связи с главным процессом

2. **Directory Processing**
   - Проверка доступности каталога
   - Создание блокировки
   - Сканирование и обработка файлов

3. **Progress Reporting**
   - Отправка статуса обработки
   - Отчет о прогрессе
   - Уведомления об ошибках

4. **Process Cleanup**
   - Освобождение ресурсов
   - Удаление блокировки
   - Отправка финального статуса

### File Processing Flow

#### 1. Directory Availability Check
- Проверяем свободен ли каталог для обработки
- Проверяем наличие lock файла
- Если lock существует - проверяем PID процесса
- Если процесс не найден - удаляем orphaned lock файл

#### 2. Directory Locking
- Создаем lock файл с текущим PID процесса
- Устанавливаем файловую блокировку для предотвращения конфликтов
- Записываем метаданные в lock файл (время создания, PID, статус)

#### 3. Database File List Retrieval
- Запрашиваем базу данных о файлах в данном каталоге
- Получаем список уже проиндексированных файлов с метаданными
- Извлекаем информацию о датах последнего изменения файлов

#### 4. Recursive Directory Scanning
- Рекурсивно читаем список файлов в каталоге
- Собираем информацию о каждом файле (путь, размер, дата изменения)
- Поддерживаемые форматы: Markdown (.md) и текстовые файлы (.txt)

#### 5. File Filtering
- Отфильтровываем только новые файлы (отсутствующие в базе)
- Отфильтровываем файлы с датой изменения новее даты в базе
- Пропускаем файлы, которые уже актуальны в базе

#### 6. File Block Processing
- Каждый файл пропускается через фильтр
- На выходе получаем дерево блоков (структурированный контент)
- Поддерживаемые форматы: Markdown и текстовые файлы
- Конфигурация: максимальный размер блока и максимальное количество блоков
- **Извлечение метаданных**: только путь к файлу и создание ID источника

#### 7. Block Chunking Configuration
- Настройки в конфиге:
  - `max_block_size` - максимальный размер блока
  - `max_blocks_per_batch` - максимальное количество блоков в партии

#### 8. Batch Processing
- Если количество блоков превышает лимит - разбиваем на части
- Обрабатываем партиями не больше максимального количества блоков
- Чанкуем и записываем блоками
- **Создание SemanticChunk**: только базовые поля (путь к файлу, ID источника, статус NEW)

#### 9. Atomic Processing
- **Фаза 1**: Чанкуем ВСЕ блоки файла (с векторизацией)
- **Фаза 2**: Поблочно записываем в базу (количество чанков не больше лимита в конфиге)
- Процесс атомарен - либо все чанки записываются, либо ни одного
- **Минимальные метаданные**: только source_path, source_id (UUID4 для файла), status=NEW
- **UUID чанков**: назначаются автоматически в процессе чанкинга

#### 10. Error Handling
- Если произошла ошибка на любом этапе:
  - Удаляем весь файл из базы данных
  - Логируем ошибку
  - Продолжаем обработку со следующим файлом
  - Не прерываем обработку всего каталога

#### 11. Lock Cleanup
- После завершения обработки всех файлов:
  - Снимаем файловую блокировку
  - Удаляем lock файл
  - Освобождаем каталог для других процессов

## API Commands

### Health Check Commands
- `health_check` - общая проверка здоровья системы
- `get_system_stats` - статистика системы
- `get_processing_stats` - статистика обработки
- `get_scan_processes_status` - статус сканирующих процессов
- `get_active_directories` - список активных каталогов

#### Health Check Response Structure
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "vector_store": "healthy",
    "chunker": "healthy", 
    "embedding": "healthy"
  },
  "processes": {
    "total_active": 3,
    "scanning_processes": 2,
    "idle_processes": 1,
    "failed_processes": 0
  },
  "directories": {
    "total_configured": 5,
    "currently_scanned": 2,
    "waiting_for_scan": 3,
    "active_directories": [
      {
        "path": "/path/to/dir1",
        "process_id": 12345,
        "status": "scanning",
        "files_processed": 15,
        "total_files": 50,
        "started_at": "2024-01-01T11:30:00Z"
      },
      {
        "path": "/path/to/dir2", 
        "process_id": 12346,
        "status": "scanning",
        "files_processed": 8,
        "total_files": 25,
        "started_at": "2024-01-01T11:35:00Z"
      }
    ]
  },
  "performance": {
    "avg_processing_time": 2.5,
    "files_per_minute": 12.3,
    "error_rate": 0.02
  }
}
```

### Lock Management Commands
- `create_lock` - создать lock файл в каталоге
- `remove_lock` - удалить lock файл
- `check_lock` - проверить существующий lock
- `list_locks` - список всех lock файлов
- `cleanup_orphaned_locks` - очистка orphaned lock файлов

### Directory Management Commands
- `start_watching` - начать отслеживание директории
- `stop_watching` - остановить отслеживание директории
- `get_watch_status` - статус отслеживания
- `list_watched_directories` - список отслеживаемых директорий

### Process Management Commands
- `start_scan_process` - запустить процесс сканирования каталога
- `stop_scan_process` - остановить процесс сканирования
- `get_process_status` - статус процесса
- `list_active_processes` - список активных процессов
- `terminate_process` - принудительно завершить дочерний процесс
- `restart_process` - перезапустить дочерний процесс
- `get_process_logs` - получить логи дочернего процесса

### Database Integration Commands
- `query_database` - запрос к базе данных о файлах
- `update_database` - обновление базы данных
- `get_indexed_files` - получить список проиндексированных файлов

## Configuration

### Server Configuration
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8015,
    "debug": false,
    "log_level": "INFO"
  },
  "file_watcher": {
    "directories": [
      "./documents",
      "./docs"
    ],
    "scan_interval": 300,
    "lock_timeout": 3600,
    "max_processes": 5,
    "scan_period": 3600
    "supported_formats": [".md", ".txt"],
    "max_block_size": 8192,
    "max_blocks_per_batch": 100,
    "recursive_scan": true
  },
  "vector_store": {
    "base_url": "http://localhost",
    "port": 8007,
    "timeout": 30
  },
  "chunker": {
    "base_url": "http://localhost",
    "port": 8009,
    "timeout": 30
  },
  "embedding": {
    "base_url": "http://localhost",
    "port": 8001,
    "timeout": 30
  }
}
```

## Services Architecture

### Core Services

#### 1. Vector Store Service
- **Client**: VectorStoreClient
- **Port**: 8007
- **Purpose**: Основная база данных для хранения чанков
- **Operations**: 
  - Создание чанков
  - Поиск по чанкам
  - Удаление чанков
  - Подсчет статистики

#### 2. Chunking Service (SVO)
- **Client**: SVOChunkerAdapter
- **Port**: 8009
- **Purpose**: Семантический чанкинг текста
- **Operations**:
  - Разбиение текста на семантические чанки
  - Извлечение структуры документа
  - Определение типа контента

#### 3. Embedding Service
- **Client**: EmbeddingAdapter
- **Port**: 8001
- **Purpose**: Векторизация текста
- **Operations**:
  - Автоматическая векторизация при создании чанков
  - Пакетная обработка массивов чанков
  - Интеграция с чанкингом через VectorStoreClient

### Service Integration

#### Document Processing Pipeline
1. **File Reading** → Чтение файла из файловой системы
2. **Text Extraction** → Извлечение текста из документа
3. **Chunking with Embedding** → Разбиение на семантические чанки с автоматической векторизацией (SVO, порт 8009)
4. **Batch Storage** → Пакетное сохранение массива чанков в векторную базу (Vector Store, порт 8007)

#### Service Communication
- **Async Communication**: Все сервисы используют асинхронное взаимодействие
- **JSON-RPC Protocol**: Стандартизированный протокол для всех сервисов
- **Error Handling**: Централизованная обработка ошибок
- **Retry Logic**: Автоматические повторы при сбоях

### Service Dependencies

#### Vector Store Client Dependencies
```python
# Основные зависимости
vector_store_client
svo_client          # Для чанкинга
embed_client        # Для векторизации
chunk_metadata_adapter  # Для метаданных
```

#### Service Configuration
```python
# Конфигурация клиентов
vector_store = VectorStoreClient(
    base_url="http://localhost:8007",
    svo_url="http://localhost:8009",      # Чанкинг
    embedding_url="http://localhost:8001"  # Векторизатор
)

# Пакетная обработка чанков
chunks = await vector_store.chunk_text(text)  # Автоматически с векторизацией
await vector_store.create_chunks(chunks)      # Пакетное сохранение массива
```

### Service Health Monitoring

#### Health Check Endpoints
- `/health` - общий статус сервиса
- `/health/vector_store` - статус векторной базы
- `/health/chunker` - статус чанкера
- `/health/embedding` - статус векторизатора

#### Service Metrics
- Response times для каждого сервиса
- Error rates по типам операций
- Queue lengths для обработки
- Resource usage (CPU, Memory, Disk)

## Metadata Extraction

### Minimal Metadata Requirements

#### File Metadata Extraction
- **source_path**: Полный путь к файлу (обязательно)
- **source_id**: UUID4 для идентификации источника (генерируется автоматически)
- **status**: Статус NEW (из перечисления ChunkStatus)

#### SemanticChunk Creation
```python
# Минимальный набор полей для создания SemanticChunk
# UUID чанка назначается автоматически в процессе чанкинга
semantic_chunk = SemanticChunk(
    source_id=file_source_id,       # UUID4 источника (файла) - генерируем для каждого файла
    source_path=file_path,          # Путь к файлу
    type=ChunkType.DOC_BLOCK,       # Тип по умолчанию
    body=chunk_text,                # Текст чанка
    status=ChunkStatus.NEW,         # Статус NEW
    created_at=datetime.now().isoformat()  # Время создания
)
```

#### Supported ChunkStatus Values
- **NEW**: Начальный статус для новых данных
- **RAW**: Сырые данные, как они поступили в систему
- **CLEANED**: Данные прошли очистку от ошибок и шума
- **VERIFIED**: Данные проверены на соответствие правилам
- **VALIDATED**: Данные прошли валидацию с учетом контекста
- **RELIABLE**: Надежные данные, готовые к использованию
- **INDEXED**: Данные проиндексированы
- **OBSOLETE**: Данные устарели
- **REJECTED**: Данные отклонены из-за критических проблем
- **IN_PROGRESS**: Данные в процессе обработки

### Metadata Processing Pipeline
1. **File Detection**: Определение пути к файлу
2. **Source ID Generation**: Создание UUID4 для файла (source_id)
3. **Chunk Creation**: Создание SemanticChunk с минимальными метаданными
4. **Chunking Process**: UUID чанков назначаются автоматически
5. **Status Assignment**: Установка статуса NEW
6. **Storage**: Сохранение в векторную базу

## Error Handling

### Lock Errors
- Lock file corruption
- Process not found
- File system errors
- Permission denied

### Process Errors
- Process crash
- Timeout
- Resource exhaustion
- Communication errors

### Database Errors
- Connection failure
- Query timeout
- Data corruption
- Transaction rollback

## Monitoring and Logging

### Metrics
- Number of active locks
- Number of active processes
- Files processed per directory
- Processing time per directory
- Error rates
- Active scanning processes count
- Currently scanned directories
- Process status distribution

### Logging
- Lock creation/removal
- Process start/stop
- Database queries
- Error conditions
- Performance metrics

## Security Considerations

### File Permissions
- Lock files should be readable only by the service
- Directory access permissions
- Process isolation

### Process Security
- Process sandboxing
- Resource limits
- Signal handling

### Database Security
- Connection encryption
- Query parameterization
- Access control
