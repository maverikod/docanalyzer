# Стандарты структуры проекта DocAnalyzer

## 1. Общие принципы структуры

### 1.1 Современный подход к Python пакетам
- **PEP 518** совместимость с `pyproject.toml`
- **Setuptools** с современной конфигурацией
- **Автоматическое обнаружение** пакетов и модулей
- **Включение всех необходимых файлов** для distribution
- **Соответствие PyPI требованиям** для публикации

### 1.2 Принципы организации
- **Плоская структура пакетов**: Избегание глубокой вложенности
- **Логическая группировка**: Модули группируются по функциональности
- **Разделение concerns**: Четкое разделение кода, тестов, документации
- **Масштабируемость**: Легкость добавления новых компонентов
- **Читаемость**: Интуитивно понятная навигация по проекту

## 2. Полная структура проекта

```
docanalyzer/                                    # Корневая директория проекта
├── .git/                                      # Git репозиторий
├── .github/                                   # GitHub специфичные файлы
│   ├── workflows/                             # GitHub Actions
│   │   ├── test.yml                          # CI тестирование
│   │   ├── lint.yml                          # Проверка качества кода
│   │   ├── publish.yml                       # Публикация в PyPI
│   │   └── docs.yml                          # Сборка документации
│   ├── ISSUE_TEMPLATE/                       # Шаблоны Issues
│   │   ├── bug_report.md                     # Шаблон баг-репорта
│   │   ├── feature_request.md                # Шаблон запроса функции
│   │   └── question.md                       # Шаблон вопроса
│   ├── PULL_REQUEST_TEMPLATE.md               # Шаблон Pull Request
│   └── CODEOWNERS                            # Владельцы кода
│
├── docanalyzer/                               # Основной Python пакет
│   ├── __init__.py                           # Инициализация пакета + публичный API
│   ├── main.py                               # Точка входа CLI приложения
│   ├── app.py                                # Главный класс приложения
│   ├── config.py                             # Класс конфигурации
│   ├── constants.py                          # Глобальные константы
│   ├── exceptions.py                         # Пользовательские исключения
│   ├── version.py                            # Информация о версии
│   │
│   ├── filters/                              # Система фильтров файлов
│   │   ├── __init__.py                       # Экспорт основных классов
│   │   ├── base.py                           # BaseFileFilter - абстрактный класс
│   │   ├── registry.py                       # FilterRegistry - реестр фильтров
│   │   ├── block_types.py                    # BlockTypeExtended - типы блоков
│   │   ├── text_block.py                     # TextBlock - модель блока
│   │   ├── file_structure.py                 # FileStructure - структура файла
│   │   │
│   │   ├── implementations/                  # Конкретные реализации фильтров
│   │   │   ├── __init__.py
│   │   │   ├── text_filter.py               # Фильтр текстовых файлов
│   │   │   ├── python_filter.py             # Фильтр Python файлов
│   │   │   ├── markdown_filter.py           # Фильтр Markdown файлов
│   │   │   ├── javascript_filter.py         # Фильтр JavaScript/TypeScript
│   │   │   ├── json_filter.py               # Фильтр JSON файлов
│   │   │   └── yaml_filter.py               # Фильтр YAML файлов
│   │   │
│   │   └── utils/                           # Утилиты для фильтров
│   │       ├── __init__.py
│   │       ├── ast_parser.py                # AST парсинг утилиты
│   │       ├── text_parser.py               # Парсинг текста
│   │       └── language_detector.py         # Определение языка файла
│   │
│   ├── pipeline/                             # Система пайплайнов обработки
│   │   ├── __init__.py                       # Экспорт пайплайн классов
│   │   ├── base.py                           # BasePipeline - базовый класс
│   │   ├── chunker.py                        # TextBlockChunker - чанкер блоков
│   │   ├── chunking_config.py                # ChunkingConfig - конфигурация
│   │   ├── pipeline_config.py                # PipelineConfig - конфигурация
│   │   ├── pipeline_stats.py                 # PipelineStats - статистика
│   │   ├── directory_pipeline.py             # DirectoryPipeline - пайплайн каталога
│   │   ├── manager.py                        # PipelineManager - менеджер пайплайнов
│   │   │
│   │   ├── strategies/                       # Стратегии чанкования
│   │   │   ├── __init__.py
│   │   │   ├── base_strategy.py             # Базовая стратегия
│   │   │   ├── preserve_structure.py        # Сохранение структуры
│   │   │   ├── chunk_by_size.py             # Чанкование по размеру
│   │   │   └── adaptive_chunking.py         # Адаптивное чанкование
│   │   │
│   │   └── processors/                      # Процессоры для разных типов
│   │       ├── __init__.py
│   │       ├── code_processor.py            # Обработка кода
│   │       ├── text_processor.py            # Обработка текста
│   │       └── document_processor.py        # Обработка документов
│   │
│   ├── wdd/                                  # Управление .wdd файлами
│   │   ├── __init__.py                       # Экспорт WDD классов
│   │   ├── manager.py                        # WatchDirectoryManager - основной класс
│   │   ├── models.py                         # WDDFile, ProcessingEntry - модели
│   │   ├── lock_manager.py                   # LockManager - управление блокировками
│   │   ├── sync_manager.py                   # SyncManager - синхронизация с БД
│   │   │
│   │   └── operations/                      # Операции с .wdd файлами
│   │       ├── __init__.py
│   │       ├── scanner.py                   # Сканирование каталогов
│   │       ├── cleanup.py                   # Очистка устаревших записей
│   │       └── recovery.py                  # Восстановление после сбоев
│   │
│   ├── watcher/                              # Мониторинг файловой системы
│   │   ├── __init__.py                       # Экспорт Watcher классов
│   │   ├── filesystem_watcher.py             # FileSystemWatcher - основной класс
│   │   ├── event_handler.py                  # EventHandler - обработчик событий
│   │   ├── filter_rules.py                   # FilterRules - правила фильтрации
│   │   ├── debouncer.py                      # Debouncer - устранение дребезга
│   │   │
│   │   └── handlers/                        # Обработчики событий
│   │       ├── __init__.py
│   │       ├── file_created_handler.py      # Обработка создания файлов
│   │       ├── file_modified_handler.py     # Обработка изменения файлов
│   │       └── file_deleted_handler.py      # Обработка удаления файлов
│   │
│   ├── commands/                             # MCP команды
│   │   ├── __init__.py                       # Экспорт команд и регистрация
│   │   ├── base_command.py                   # BaseCommand - базовый класс
│   │   ├── command_registry.py               # CommandRegistry - реестр команд
│   │   │
│   │   ├── monitoring/                       # Команды мониторинга
│   │   │   ├── __init__.py
│   │   │   ├── start_watching_command.py    # Запуск мониторинга
│   │   │   ├── stop_watching_command.py     # Остановка мониторинга
│   │   │   ├── get_watch_status_command.py  # Статус мониторинга
│   │   │   ├── add_watch_path_command.py    # Добавление пути
│   │   │   └── remove_watch_path_command.py # Удаление пути
│   │   │
│   │   ├── files/                           # Команды управления файлами
│   │   │   ├── __init__.py
│   │   │   ├── process_file_command.py      # Обработка файла
│   │   │   ├── reprocess_file_command.py    # Повторная обработка
│   │   │   ├── get_file_status_command.py   # Статус файла
│   │   │   └── list_processed_files_command.py # Список файлов
│   │   │
│   │   ├── wdd/                             # Команды .wdd управления
│   │   │   ├── __init__.py
│   │   │   ├── scan_directory_command.py    # Сканирование каталога
│   │   │   ├── get_wdd_status_command.py    # Статус .wdd файла
│   │   │   ├── cleanup_wdd_command.py       # Очистка .wdd
│   │   │   └── rebuild_wdd_command.py       # Пересоздание .wdd
│   │   │
│   │   └── stats/                           # Команды статистики
│   │       ├── __init__.py
│   │       ├── get_system_stats_command.py  # Статистика системы
│   │       ├── get_processing_stats_command.py # Статистика обработки
│   │       ├── get_queue_status_command.py  # Статистика очередей
│   │       └── health_check_command.py      # Проверка здоровья
│   │
│   ├── utils/                                # Утилиты и вспомогательные функции
│   │   ├── __init__.py                       # Экспорт утилит
│   │   ├── file_utils.py                     # FileUtils - работа с файлами
│   │   ├── text_utils.py                     # TextUtils - обработка текста
│   │   ├── hash_utils.py                     # HashUtils - хеширование
│   │   ├── logging_utils.py                  # LoggingUtils - настройка логирования
│   │   ├── validation_utils.py               # ValidationUtils - валидация
│   │   ├── async_utils.py                    # AsyncUtils - асинхронные утилиты
│   │   ├── datetime_utils.py                 # DateTimeUtils - работа с временем
│   │   └── path_utils.py                     # PathUtils - работа с путями
│   │
│   └── adapters/                             # Адаптеры внешних сервисов
│       ├── __init__.py                       # Экспорт адаптеров
│       ├── base_adapter.py                   # BaseAdapter - базовый класс
│       ├── vector_store_adapter.py           # VectorStoreAdapter - векторное хранилище
│       ├── metadata_adapter.py               # MetadataAdapter - метаданные чанков
│       ├── mcp_adapter.py                    # MCPAdapter - MCP прокси
│       │
│       └── implementations/                  # Конкретные реализации
│           ├── __init__.py
│           ├── vector_store_client_adapter.py # Адаптер vector_store_client
│           └── chunk_metadata_adapter.py     # Адаптер chunk_metadata_adapter
│
├── tests/                                    # Полная система тестирования
│   ├── __init__.py                           # Инициализация тестов
│   ├── conftest.py                           # Конфигурация pytest + фикстуры
│   ├── pytest.ini                            # Конфигурация pytest
│   │
│   ├── fixtures/                             # Тестовые данные и фикстуры
│   │   ├── __init__.py
│   │   ├── sample_files/                     # Примеры файлов для тестов
│   │   │   ├── python/                       # Python файлы
│   │   │   │   ├── simple_function.py
│   │   │   │   ├── class_with_methods.py
│   │   │   │   └── complex_module.py
│   │   │   ├── markdown/                     # Markdown файлы
│   │   │   │   ├── simple_doc.md
│   │   │   │   ├── complex_doc.md
│   │   │   │   └── multilang_doc.md
│   │   │   ├── text/                         # Текстовые файлы
│   │   │   │   ├── plain_text.txt
│   │   │   │   └── structured_text.txt
│   │   │   └── json/                         # JSON файлы
│   │   │       ├── simple_config.json
│   │   │       └── complex_data.json
│   │   ├── test_data.py                      # Программные тестовые данные
│   │   ├── mock_responses.py                 # Mock ответы от внешних сервисов
│   │   └── factories.py                      # Фабрики для создания тестовых объектов
│   │
│   ├── unit/                                 # Unit тесты
│   │   ├── __init__.py
│   │   ├── test_filters/                     # Тесты фильтров
│   │   │   ├── __init__.py
│   │   │   ├── test_base_filter.py
│   │   │   ├── test_registry.py
│   │   │   ├── test_text_block.py
│   │   │   ├── test_file_structure.py
│   │   │   ├── test_implementations/
│   │   │   │   ├── test_text_filter.py
│   │   │   │   ├── test_python_filter.py
│   │   │   │   ├── test_markdown_filter.py
│   │   │   │   └── test_javascript_filter.py
│   │   │   └── test_utils/
│   │   │       ├── test_ast_parser.py
│   │   │       └── test_language_detector.py
│   │   │
│   │   ├── test_pipeline/                    # Тесты пайплайнов
│   │   │   ├── __init__.py
│   │   │   ├── test_base_pipeline.py
│   │   │   ├── test_chunker.py
│   │   │   ├── test_configs.py
│   │   │   ├── test_directory_pipeline.py
│   │   │   ├── test_manager.py
│   │   │   ├── test_strategies/
│   │   │   │   ├── test_preserve_structure.py
│   │   │   │   └── test_chunk_by_size.py
│   │   │   └── test_processors/
│   │   │       ├── test_code_processor.py
│   │   │       └── test_text_processor.py
│   │   │
│   │   ├── test_wdd/                         # Тесты .wdd управления
│   │   │   ├── __init__.py
│   │   │   ├── test_manager.py
│   │   │   ├── test_models.py
│   │   │   ├── test_lock_manager.py
│   │   │   └── test_operations/
│   │   │       ├── test_scanner.py
│   │   │       ├── test_cleanup.py
│   │   │       └── test_recovery.py
│   │   │
│   │   ├── test_watcher/                     # Тесты наблюдателя
│   │   │   ├── __init__.py
│   │   │   ├── test_filesystem_watcher.py
│   │   │   ├── test_event_handler.py
│   │   │   ├── test_filter_rules.py
│   │   │   └── test_handlers/
│   │   │       ├── test_file_created_handler.py
│   │   │       ├── test_file_modified_handler.py
│   │   │       └── test_file_deleted_handler.py
│   │   │
│   │   ├── test_commands/                    # Тесты команд
│   │   │   ├── __init__.py
│   │   │   ├── test_base_command.py
│   │   │   ├── test_command_registry.py
│   │   │   ├── test_monitoring/
│   │   │   ├── test_files/
│   │   │   ├── test_wdd/
│   │   │   └── test_stats/
│   │   │
│   │   ├── test_utils/                       # Тесты утилит
│   │   │   ├── __init__.py
│   │   │   ├── test_file_utils.py
│   │   │   ├── test_text_utils.py
│   │   │   ├── test_hash_utils.py
│   │   │   ├── test_logging_utils.py
│   │   │   └── test_validation_utils.py
│   │   │
│   │   ├── test_adapters/                    # Тесты адаптеров
│   │   │   ├── __init__.py
│   │   │   ├── test_base_adapter.py
│   │   │   ├── test_vector_store_adapter.py
│   │   │   └── test_implementations/
│   │   │
│   │   ├── test_app.py                       # Тесты главного приложения
│   │   ├── test_config.py                    # Тесты конфигурации
│   │   ├── test_exceptions.py                # Тесты исключений
│   │   └── test_main.py                      # Тесты точки входа
│   │
│   ├── integration/                          # Интеграционные тесты
│   │   ├── __init__.py
│   │   ├── test_full_pipeline.py             # Тест полного пайплайна
│   │   ├── test_vector_store_integration.py  # Интеграция с векторным хранилищем
│   │   ├── test_api_integration.py           # Интеграция API
│   │   ├── test_file_processing_flow.py      # Поток обработки файлов
│   │   ├── test_wdd_coordination.py          # Координация через .wdd файлы
│   │   └── test_error_recovery.py            # Восстановление после ошибок
│   │
│   ├── performance/                          # Тесты производительности
│   │   ├── __init__.py
│   │   ├── test_chunking_speed.py            # Скорость чанкования
│   │   ├── test_memory_usage.py              # Использование памяти
│   │   ├── test_concurrent_processing.py     # Параллельная обработка
│   │   ├── test_large_files.py               # Обработка больших файлов
│   │   └── test_scalability.py               # Тесты масштабируемости
│   │
│   └── e2e/                                  # End-to-end тесты
│       ├── __init__.py
│       ├── test_cli_interface.py             # Тестирование CLI
│       ├── test_api_endpoints.py             # Тестирование API
│       └── test_full_workflow.py             # Полный рабочий процесс
│
├── docs/                                     # Документация
│   ├── EN/                                   # Английская документация
│   │   ├── index.md                          # Главная страница
│   │   ├── quick_start.md                    # Быстрый старт
│   │   ├── installation.md                   # Установка
│   │   ├── configuration.md                  # Конфигурация
│   │   │
│   │   ├── api/                              # API документация
│   │   │   ├── index.md
│   │   │   ├── filters.md                    # API фильтров
│   │   │   ├── pipeline.md                   # API пайплайнов
│   │   │   ├── commands.md                   # API команд
│   │   │   └── adapters.md                   # API адаптеров
│   │   │
│   │   ├── architecture/                     # Архитектурная документация
│   │   │   ├── overview.md                   # Общий обзор
│   │   │   ├── components.md                 # Компоненты системы
│   │   │   ├── data_flow.md                  # Поток данных
│   │   │   └── integration.md                # Интеграция с внешними сервисами
│   │   │
│   │   ├── guides/                           # Руководства
│   │   │   ├── user_guide.md                 # Руководство пользователя
│   │   │   ├── developer_guide.md            # Руководство разработчика
│   │   │   ├── deployment_guide.md           # Руководство по развертыванию
│   │   │   └── troubleshooting.md            # Устранение неполадок
│   │   │
│   │   └── examples/                         # Примеры использования
│   │       ├── basic_usage.md                # Базовое использование
│   │       ├── custom_filters.md             # Пользовательские фильтры
│   │       ├── advanced_configuration.md     # Продвинутая конфигурация
│   │       └── integration_examples.md       # Примеры интеграции
│   │
│   ├── RU/                                   # Русская документация (идентичная структура)
│   │   ├── index.md
│   │   ├── quick_start.md
│   │   ├── installation.md
│   │   ├── configuration.md
│   │   ├── api/
│   │   ├── architecture/
│   │   ├── guides/
│   │   └── examples/
│   │
│   ├── tech_spec.md                          # Техническое задание
│   ├── IMPLEMENTATION_PLAN.md                # План реализации
│   ├── CODING_STANDARDS.md                   # Стандарты кодирования
│   ├── FILE_NAMING_STANDARDS.md              # Стандарты именования файлов
│   ├── PROJECT_STRUCTURE_STANDARDS.md        # Стандарты структуры проекта
│   ├── ARCHITECTURE_STANDARDS.md             # Архитектурные стандарты
│   │
│   └── _build/                               # Сгенерированная документация
│       ├── html/                             # HTML версия
│       └── pdf/                              # PDF версия
│
├── scripts/                                  # Вспомогательные скрипты
│   ├── setup_dev_env.py                      # Настройка среды разработки
│   ├── build_package.py                      # Сборка пакета
│   ├── run_tests.py                          # Запуск тестов
│   ├── check_code_quality.py                 # Проверка качества кода
│   ├── generate_docs.py                      # Генерация документации
│   ├── update_version.py                     # Обновление версии
│   └── deploy_to_pypi.py                     # Развертывание в PyPI
│
├── examples/                                 # Примеры использования
│   ├── __init__.py
│   ├── basic_usage.py                        # Базовое использование
│   ├── custom_filter_example.py              # Пример пользовательского фильтра
│   ├── advanced_configuration.py             # Продвинутая конфигурация
│   ├── async_processing_example.py           # Асинхронная обработка
│   ├── integration_example.py                # Пример интеграции
│   │
│   └── config_examples/                      # Примеры конфигураций
│       ├── basic_config.json                 # Базовая конфигурация
│       ├── production_config.json            # Продакшн конфигурация
│       ├── development_config.json           # Конфигурация разработки
│       └── docker_config.json                # Конфигурация для Docker
│
├── deployment/                               # Файлы развертывания
│   ├── docker/                               # Docker конфигурации
│   │   ├── Dockerfile                        # Основной Dockerfile
│   │   ├── Dockerfile.dev                    # Dockerfile для разработки
│   │   ├── docker-compose.yml                # Docker Compose
│   │   └── docker-compose.dev.yml            # Docker Compose для разработки
│   │
│   ├── kubernetes/                           # Kubernetes манифесты
│   │   ├── deployment.yaml                   # Deployment
│   │   ├── service.yaml                      # Service
│   │   ├── configmap.yaml                    # ConfigMap
│   │   └── ingress.yaml                      # Ingress
│   │
│   └── systemd/                              # Systemd сервисы
│       ├── docanalyzer.service               # Systemd сервис
│       └── docanalyzer.conf                  # Конфигурация сервиса
│
├── .vscode/                                  # VS Code настройки (опционально)
│   ├── settings.json                         # Настройки проекта
│   ├── launch.json                           # Конфигурации запуска
│   └── extensions.json                       # Рекомендуемые расширения
│
├── .idea/                                    # PyCharm настройки (опционально)
│   └── ...                                   # PyCharm конфигурационные файлы
│
├── pyproject.toml                            # Современная конфигурация Python пакета
├── setup.py                                  # Поддержка старых версий pip
├── setup.cfg                                 # Конфигурация инструментов разработки
├── requirements.txt                          # Основные зависимости
├── requirements-dev.txt                      # Зависимости для разработки
├── requirements-test.txt                     # Зависимости для тестирования
├── requirements-docs.txt                     # Зависимости для документации
├── .gitignore                                # Git исключения
├── .gitattributes                            # Git атрибуты
├── .pylintrc                                 # Конфигурация pylint
├── mypy.ini                                  # Конфигурация mypy
├── pytest.ini                               # Конфигурация pytest
├── .pre-commit-config.yaml                   # Pre-commit хуки
├── .editorconfig                             # Настройки редактора
├── tox.ini                                   # Конфигурация tox (опционально)
├── README.md                                 # Основная документация проекта
├── CHANGELOG.md                              # История изменений
├── LICENSE                                   # Файл лицензии
├── CONTRIBUTING.md                           # Руководство для контрибьюторов
├── CODE_OF_CONDUCT.md                        # Кодекс поведения
├── SECURITY.md                               # Политика безопасности
├── AUTHORS.md                                # Авторы проекта
└── MANIFEST.in                               # Манифест для включения файлов в распространение
```

## 3. Конфигурационные файлы для PyPI

### 3.1 pyproject.toml (главная конфигурация)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "docanalyzer"
authors = [
    {name = "Developer Name", email = "developer@example.com"},
]
maintainers = [
    {name = "Maintainer Name", email = "maintainer@example.com"},
]
description = "Automated file monitoring and chunking for vector databases"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Information Technology",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Indexing",
    "Topic :: Scientific/Engineering :: Information Analysis",
    "Typing :: Typed",
]
keywords = [
    "document-analysis",
    "text-chunking", 
    "file-monitoring",
    "vector-database",
    "semantic-search",
    "file-processing",
    "content-extraction"
]
dynamic = ["version"]

dependencies = [
    "watchdog>=2.1.0",
    "pathspec>=0.9.0",
    "fastapi>=0.68.0",
    "uvicorn[standard]>=0.15.0",
    "aiofiles>=0.7.0",
    "pydantic>=1.8.0",
    "httpx>=0.24.0",
    "vector-store-client>=1.0.0",
    "chunk-metadata-adapter>=1.0.0", 
    "mcp-proxy-adapter>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0",
    "pytest-cov>=2.0",
    "pytest-asyncio>=0.18.0",
    "pytest-mock>=3.6.0",
    "mypy>=0.910",
    "black>=21.0",
    "pylint>=2.9",
    "isort>=5.9",
    "pre-commit>=2.15.0",
    "tox>=3.24.0",
]
test = [
    "pytest>=6.0",
    "pytest-cov>=2.0",
    "pytest-asyncio>=0.18.0",
    "pytest-mock>=3.6.0",
    "pytest-xdist>=2.4.0",
    "coverage[toml]>=6.0",
]
docs = [
    "sphinx>=4.0.0",
    "sphinx-autodoc-typehints>=1.12.0",
    "sphinx-rtd-theme>=1.0.0",
    "myst-parser>=0.15.0",
]
performance = [
    "psutil>=5.8.0",
    "memory-profiler>=0.60.0",
    "line-profiler>=3.3.0",
]
all = ["docanalyzer[dev,test,docs,performance]"]

[project.urls]
Homepage = "https://github.com/user/docanalyzer"
Repository = "https://github.com/user/docanalyzer"
Documentation = "https://docanalyzer.readthedocs.io"
"Bug Tracker" = "https://github.com/user/docanalyzer/issues"
Changelog = "https://github.com/user/docanalyzer/blob/main/CHANGELOG.md"

[project.scripts]
docanalyzer = "docanalyzer.main:main"

[project.entry-points."docanalyzer.filters"]
text = "docanalyzer.filters.implementations:TextFilter"
python = "docanalyzer.filters.implementations:PythonFilter"
markdown = "docanalyzer.filters.implementations:MarkdownFilter"
javascript = "docanalyzer.filters.implementations:JavaScriptFilter"

[tool.setuptools]
package-dir = {"" = "."}

[tool.setuptools.packages.find]
include = ["docanalyzer*"]
exclude = ["tests*", "scripts*", "docs*", "examples*"]

[tool.setuptools.package-data]
docanalyzer = ["py.typed", "*.json", "*.yaml", "*.yml"]

[tool.setuptools_scm]
write_to = "docanalyzer/version.py"
version_scheme = "post-release"
local_scheme = "dirty-tag"

[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["docanalyzer"]
known_third_party = ["pytest", "watchdog", "fastapi"]

[tool.mypy]
python_version = "3.9"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "vector_store_client.*",
    "chunk_metadata_adapter.*", 
    "mcp_proxy_adapter.*",
    "watchdog.*",
]
ignore_missing_imports = true

[tool.pylint.messages_control]
disable = [
    "too-few-public-methods",
    "too-many-arguments",
    "too-many-instance-attributes",
    "duplicate-code",
]

[tool.pylint.format]
max-line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=docanalyzer",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=90",
]
markers = [
    "unit: marks tests as unit tests",
    "integration: marks tests as integration tests", 
    "performance: marks tests as performance tests",
    "slow: marks tests as slow running",
    "external: marks tests that require external services",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["docanalyzer"]
omit = [
    "*/tests/*",
    "*/test_*",
    "docanalyzer/version.py",
    "setup.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```

### 3.2 setup.py (обратная совместимость)

```python
"""
Setup script for docanalyzer package.

This file provides backward compatibility for older pip versions
that don't support pyproject.toml.
"""

from setuptools import setup

# Use setup() with minimal configuration
# All metadata is in pyproject.toml
setup()
```

### 3.3 MANIFEST.in (включение дополнительных файлов)

```
# Include metadata and documentation
include README.md
include CHANGELOG.md
include LICENSE
include CONTRIBUTING.md
include CODE_OF_CONDUCT.md
include SECURITY.md
include AUTHORS.md

# Include configuration files
include pyproject.toml
include setup.cfg
include requirements*.txt
include .pylintrc
include mypy.ini
include pytest.ini

# Include type information
include docanalyzer/py.typed

# Include documentation
recursive-include docs *.md *.rst *.txt *.png *.jpg *.gif
recursive-include docs/EN *.md *.rst
recursive-include docs/RU *.md *.rst

# Include examples
recursive-include examples *.py *.json *.yaml *.yml *.md

# Include test data (but not test code)
recursive-include tests/fixtures *.py *.txt *.md *.json *.yaml *.yml
recursive-include tests/fixtures/sample_files *

# Include deployment configurations
recursive-include deployment *.yaml *.yml *.json *.service *.conf
include deployment/docker/Dockerfile*
include deployment/docker/docker-compose*.yml

# Exclude development and cache files
global-exclude *.pyc
global-exclude *.pyo
global-exclude *.pyd
global-exclude __pycache__
global-exclude .git*
global-exclude .DS_Store
global-exclude *.so
global-exclude *.egg-info
global-exclude .tox
global-exclude .coverage
global-exclude htmlcov
global-exclude .pytest_cache
global-exclude .mypy_cache
global-exclude .vscode
global-exclude .idea

# Exclude test code from distribution
recursive-exclude tests *.py
exclude tests/conftest.py
exclude tests/pytest.ini

# Exclude development scripts
exclude scripts/*.py

# Exclude build artifacts
recursive-exclude build *
recursive-exclude dist *
```

## 4. Файлы инициализации пакетов

### 4.1 Главный __init__.py

```python
"""
DocAnalyzer - Automated file monitoring and chunking for vector databases.

This package provides comprehensive file monitoring, intelligent parsing,
and chunking capabilities for various file types, with seamless integration
to vector databases for semantic search.

Main Components:
    - DocAnalyzerApp: Main application class
    - DocAnalyzerConfig: Configuration management
    - FilterRegistry: File filter registration and management
    - PipelineManager: Processing pipeline management
    - WatchDirectoryManager: Directory monitoring coordination

Quick Start:
    from docanalyzer import DocAnalyzerApp, DocAnalyzerConfig
    
    config = DocAnalyzerConfig(
        watch_paths=[Path('./documents')],
        vector_store_url='http://localhost:8007'
    )
    
    app = DocAnalyzerApp(config)
    await app.start()

Author: Developer Name
Email: developer@example.com
License: MIT
"""

# Version information (managed by setuptools_scm)
try:
    from .version import __version__
except ImportError:
    __version__ = "unknown"

# Core imports for public API
from .app import DocAnalyzerApp
from .config import DocAnalyzerConfig
from .exceptions import (
    DocAnalyzerError,
    FilterError,
    ChunkingError,
    PipelineError,
    VectorStoreError,
    ConfigurationError,
)

# Main component imports
from .filters import FilterRegistry, BaseFileFilter
from .pipeline import PipelineManager, TextBlockChunker
from .wdd import WatchDirectoryManager

# Utility imports
from .utils import get_logger, validate_file_path

# Type exports for external usage
from .filters.text_block import TextBlock
from .filters.file_structure import FileStructure
from .filters.block_types import BlockTypeExtended

# Configure package-level logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Public API definition
__all__ = [
    # Version
    "__version__",
    
    # Main classes
    "DocAnalyzerApp",
    "DocAnalyzerConfig",
    
    # Core components
    "FilterRegistry",
    "BaseFileFilter", 
    "PipelineManager",
    "TextBlockChunker",
    "WatchDirectoryManager",
    
    # Data models
    "TextBlock",
    "FileStructure",
    "BlockTypeExtended",
    
    # Exceptions
    "DocAnalyzerError",
    "FilterError",
    "ChunkingError", 
    "PipelineError",
    "VectorStoreError",
    "ConfigurationError",
    
    # Utilities
    "get_logger",
    "validate_file_path",
]

# Package metadata
__author__ = "Developer Name"
__email__ = "developer@example.com"
__license__ = "MIT"
__copyright__ = "Copyright 2024, Developer Name"
__description__ = "Automated file monitoring and chunking for vector databases"
__url__ = "https://github.com/user/docanalyzer"

# Runtime checks
import sys
if sys.version_info < (3, 9):
    raise RuntimeError("DocAnalyzer requires Python 3.9 or higher")

# Optional performance optimizations
try:
    import uvloop
    uvloop.install()
except ImportError:
    pass  # uvloop is optional
```

### 4.2 Примеры модульных __init__.py

#### filters/__init__.py:
```python
"""
File filtering system for DocAnalyzer.

Provides comprehensive file parsing and filtering capabilities
for various file types including text, code, and documentation files.

Components:
    - BaseFileFilter: Abstract base for all filters
    - FilterRegistry: Central registry for filter management
    - TextBlock: Data model for parsed content blocks
    - FileStructure: Container for file parsing results
    - BlockTypeExtended: Extended block type definitions

Filter Implementations:
    - TextFilter: Plain text files
    - PythonFilter: Python source code
    - MarkdownFilter: Markdown documents
    - JavaScriptFilter: JavaScript/TypeScript files
"""

# Core abstractions
from .base import BaseFileFilter
from .registry import FilterRegistry

# Data models
from .text_block import TextBlock
from .file_structure import FileStructure
from .block_types import BlockTypeExtended

# Filter implementations
from .implementations import (
    TextFilter,
    PythonFilter,
    MarkdownFilter,
    JavaScriptFilter,
)

# Utilities
from .utils import detect_file_language, parse_ast_safely

__all__ = [
    # Core classes
    "BaseFileFilter",
    "FilterRegistry",
    
    # Data models
    "TextBlock", 
    "FileStructure",
    "BlockTypeExtended",
    
    # Implementations
    "TextFilter",
    "PythonFilter",
    "MarkdownFilter", 
    "JavaScriptFilter",
    
    # Utilities
    "detect_file_language",
    "parse_ast_safely",
]

# Auto-register standard filters
_registry = FilterRegistry()
_registry.register('.txt', TextFilter)
_registry.register('.py', PythonFilter)
_registry.register('.md', MarkdownFilter)
_registry.register('.js', JavaScriptFilter)
_registry.register('.ts', JavaScriptFilter)

# Export configured registry
get_registry = lambda: _registry
```

#### commands/__init__.py:
```python
"""
MCP Commands for DocAnalyzer API.

Provides comprehensive command interface for file monitoring,
processing control, and system management through MCP protocol.

Command Categories:
    - monitoring: File system monitoring commands
    - files: File processing and management commands  
    - wdd: Watch directory database commands
    - stats: System statistics and health commands

Usage:
    from docanalyzer.commands import CommandRegistry
    
    registry = CommandRegistry()
    registry.register_all_commands()
    
    # Execute command via MCP
    result = await registry.execute('start_watching', {'paths': ['/data']})
"""

# Base command infrastructure
from .base_command import BaseCommand
from .command_registry import CommandRegistry

# Command implementations by category
from .monitoring import (
    StartWatchingCommand,
    StopWatchingCommand,
    GetWatchStatusCommand,
    AddWatchPathCommand,
    RemoveWatchPathCommand,
)

from .files import (
    ProcessFileCommand,
    ReprocessFileCommand,
    GetFileStatusCommand,
    ListProcessedFilesCommand,
)

from .wdd import (
    ScanDirectoryCommand,
    GetWddStatusCommand,
    CleanupWddCommand,
    RebuildWddCommand,
)

from .stats import (
    GetSystemStatsCommand,
    GetProcessingStatsCommand,
    GetQueueStatusCommand,
    HealthCheckCommand,
)

__all__ = [
    # Infrastructure
    "BaseCommand",
    "CommandRegistry",
    
    # Monitoring commands
    "StartWatchingCommand",
    "StopWatchingCommand", 
    "GetWatchStatusCommand",
    "AddWatchPathCommand",
    "RemoveWatchPathCommand",
    
    # File commands
    "ProcessFileCommand",
    "ReprocessFileCommand",
    "GetFileStatusCommand", 
    "ListProcessedFilesCommand",
    
    # WDD commands
    "ScanDirectoryCommand",
    "GetWddStatusCommand",
    "CleanupWddCommand",
    "RebuildWddCommand",
    
    # Stats commands
    "GetSystemStatsCommand",
    "GetProcessingStatsCommand",
    "GetQueueStatusCommand",
    "HealthCheckCommand",
]

# Default command registry with all commands registered
def get_default_registry() -> CommandRegistry:
    """Get default command registry with all commands registered."""
    registry = CommandRegistry()
    
    # Register monitoring commands
    registry.register('start_watching', StartWatchingCommand)
    registry.register('stop_watching', StopWatchingCommand)
    registry.register('get_watch_status', GetWatchStatusCommand)
    registry.register('add_watch_path', AddWatchPathCommand)
    registry.register('remove_watch_path', RemoveWatchPathCommand)
    
    # Register file commands
    registry.register('process_file', ProcessFileCommand)
    registry.register('reprocess_file', ReprocessFileCommand)
    registry.register('get_file_status', GetFileStatusCommand)
    registry.register('list_processed_files', ListProcessedFilesCommand)
    
    # Register WDD commands
    registry.register('scan_directory', ScanDirectoryCommand)
    registry.register('get_wdd_status', GetWddStatusCommand)
    registry.register('cleanup_wdd', CleanupWddCommand)
    registry.register('rebuild_wdd', RebuildWddCommand)
    
    # Register stats commands
    registry.register('get_system_stats', GetSystemStatsCommand)
    registry.register('get_processing_stats', GetProcessingStatsCommand)
    registry.register('get_queue_status', GetQueueStatusCommand)
    registry.register('health_check', HealthCheckCommand)
    
    return registry
```

## 5. Документационная структура

### 5.1 README.md структура

```markdown
# DocAnalyzer

[![PyPI version](https://badge.fury.io/py/docanalyzer.svg)](https://badge.fury.io/py/docanalyzer)
[![Python Support](https://img.shields.io/pypi/pyversions/docanalyzer.svg)](https://pypi.org/project/docanalyzer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/user/docanalyzer/workflows/Tests/badge.svg)](https://github.com/user/docanalyzer/actions)
[![Coverage](https://codecov.io/gh/user/docanalyzer/branch/main/graph/badge.svg)](https://codecov.io/gh/user/docanalyzer)
[![Documentation](https://readthedocs.org/projects/docanalyzer/badge/?version=latest)](https://docanalyzer.readthedocs.io/)

Automated file monitoring and chunking for vector databases. Monitors file systems in real-time, intelligently parses various file types, and creates semantic chunks for vector storage.

## ✨ Features

- 🔍 **Real-time file monitoring** with recursive directory watching
- 📝 **Multi-format support** for text, code, and documentation files
- 🧩 **Intelligent chunking** with semantic boundary preservation
- 🗄️ **Vector database integration** with automatic metadata generation
- ⚡ **Asynchronous processing** for high performance
- 🔒 **Coordination system** preventing duplicate processing
- 🛠️ **Extensible architecture** for custom file types

## 🚀 Quick Start

### Installation

```bash
pip install docanalyzer
```

### Basic Usage

```python
from docanalyzer import DocAnalyzerApp, DocAnalyzerConfig
from pathlib import Path

# Configure
config = DocAnalyzerConfig(
    watch_paths=[Path('./documents')],
    vector_store_url='http://localhost:8007'
)

# Initialize and start
app = DocAnalyzerApp(config)
await app.start_watching()
```

### CLI Usage

```bash
# Start monitoring
docanalyzer start --config config.json

# Check status
docanalyzer status

# Add new path
docanalyzer add-path /path/to/documents
```

## 📚 Documentation

- [📖 Full Documentation](https://docanalyzer.readthedocs.io/)
- [🚀 Quick Start Guide](docs/EN/quick_start.md)
- [⚙️ Configuration](docs/EN/configuration.md)
- [🏗️ Architecture](docs/EN/architecture/overview.md)
- [🔧 Developer Guide](docs/EN/guides/developer_guide.md)

## 🛠️ Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

### 5.2 CONTRIBUTING.md структура

```markdown
# Contributing to DocAnalyzer

Thank you for your interest in contributing to DocAnalyzer! This guide will help you get started.

## 🚀 Development Setup

### Prerequisites

- Python 3.9+
- Git
- Virtual environment manager (venv, conda, etc.)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/user/docanalyzer.git
   cd docanalyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev,test,docs]"
   ```

4. **Setup pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Run tests to verify setup**
   ```bash
   python scripts/run_tests.py
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=docanalyzer --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration
pytest -m performance
```

### Test Structure

- `tests/unit/` - Unit tests (fast, isolated)
- `tests/integration/` - Integration tests (external dependencies)
- `tests/performance/` - Performance benchmarks
- `tests/e2e/` - End-to-end workflow tests

## 📝 Code Standards

### Code Quality Tools

```bash
# Format code
black docanalyzer/
isort docanalyzer/

# Type checking
mypy docanalyzer/

# Linting
pylint docanalyzer/

# Run all checks
python scripts/check_code_quality.py
```

### Standards Overview

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all functions and methods
- Write comprehensive docstrings
- Maintain 90%+ test coverage
- All code in English, documentation bilingual (EN/RU)

## 🏗️ Architecture

### Adding New Components

1. **File Filters**: Extend `BaseFileFilter` in `docanalyzer/filters/implementations/`
2. **Commands**: Extend `BaseCommand` in `docanalyzer/commands/`
3. **Pipeline Processors**: Extend base processors in `docanalyzer/pipeline/processors/`

### Key Principles

- **Declarative First**: Write comprehensive docstrings and interfaces before implementation
- **Async by Default**: All I/O operations should be asynchronous
- **Error Handling**: Comprehensive error handling with proper exception hierarchy
- **Testability**: Design for easy unit testing and mocking

## 📋 Contribution Process

### 1. Issue First

- Check existing issues before creating new ones
- Use issue templates for bugs and feature requests
- Discuss major changes in issues before implementing

### 2. Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### 3. Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat(filters): add support for YAML files
fix(wdd): resolve race condition in file locking
docs(api): update filter documentation
test(pipeline): add performance benchmarks
```

### 4. Pull Request Process

1. **Create pull request** from your feature branch
2. **Fill out PR template** completely
3. **Ensure all checks pass** (tests, linting, coverage)
4. **Request review** from maintainers
5. **Address feedback** promptly
6. **Squash commits** before merge (if requested)

### PR Checklist

- [ ] Tests added/updated and passing
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated
- [ ] Type hints added
- [ ] Code formatted with black/isort
- [ ] No linting errors
- [ ] Coverage maintained at 90%+

## 📖 Documentation

### Building Documentation

```bash
# Install docs dependencies
pip install -e ".[docs]"

# Build documentation
python scripts/generate_docs.py

# Serve locally
cd docs/_build/html && python -m http.server 8000
```

### Documentation Guidelines

- **Bilingual**: Maintain both English and Russian versions
- **Code Examples**: Include working code examples
- **API Documentation**: Auto-generated from docstrings
- **Tutorials**: Step-by-step guides for common use cases

## 🎯 Areas for Contribution

### High Priority

- [ ] Additional file format support (PDF, DOCX, etc.)
- [ ] Performance optimizations for large files
- [ ] Advanced chunking strategies
- [ ] Monitoring and observability improvements

### Medium Priority

- [ ] Web interface for configuration
- [ ] Kubernetes deployment examples
- [ ] Integration with additional vector databases
- [ ] Machine learning based quality scoring

### Documentation

- [ ] More usage examples
- [ ] Video tutorials
- [ ] Translation improvements
- [ ] API reference completeness

## 🆘 Getting Help

- **Documentation**: [docanalyzer.readthedocs.io](https://docanalyzer.readthedocs.io/)
- **Discussions**: [GitHub Discussions](https://github.com/user/docanalyzer/discussions)
- **Issues**: [GitHub Issues](https://github.com/user/docanalyzer/issues)
- **Discord**: [Development Chat](https://discord.gg/docanalyzer)

## 📜 License

By contributing to DocAnalyzer, you agree that your contributions will be licensed under the MIT License.
```

## 6. Инструменты контроля качества

### 6.1 .pre-commit-config.yaml

```yaml
# Pre-commit configuration for code quality
repos:
  # Code formatting
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.9
        args: [--line-length=88]

  # Import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black, --line-length=88]

  # Linting
  - repo: https://github.com/pycqa/pylint
    rev: v2.17.5
    hooks:
      - id: pylint
        args: [--rcfile=.pylintrc]
        additional_dependencies: [
          watchdog, 
          fastapi, 
          aiofiles,
          pydantic,
          httpx
        ]

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-PyYAML]
        args: [--config-file=mypy.ini]

  # General checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: check-added-large-files
        args: [--maxkb=1000]
      - id: debug-statements
      - id: requirements-txt-fixer

  # Security scanning
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, docanalyzer/, -x, tests/]

  # Documentation
  - repo: https://github.com/pycqa/doc8
    rev: v1.1.1
    hooks:
      - id: doc8
        args: [--max-line-length=88]

  # Markdown linting
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.35.0
    hooks:
      - id: markdownlint
        args: [--fix]

ci:
  autofix_commit_msg: |
    [pre-commit.ci] auto fixes from pre-commit hooks

    for more information, see https://pre-commit.ci
  autofix_prs: true
  autoupdate_branch: ''
  autoupdate_commit_msg: '[pre-commit.ci] pre-commit autoupdate'
  autoupdate_schedule: weekly
  skip: []
  submodules: false
```

### 6.2 tox.ini (мультивенное тестирование)

```ini
[tox]
envlist = py39,py310,py311,py312,lint,mypy,docs
isolated_build = True

[testenv]
deps = 
    pytest>=6.0
    pytest-cov>=2.0
    pytest-asyncio>=0.18.0
    pytest-mock>=3.6.0
commands =
    pytest {posargs:tests/}

[testenv:coverage]
deps = 
    {[testenv]deps}
    coverage[toml]>=6.0
commands =
    coverage run -m pytest
    coverage report
    coverage html

[testenv:lint]
deps =
    pylint>=2.9
    black>=21.0
    isort>=5.9
commands =
    black --check docanalyzer/
    isort --check-only docanalyzer/
    pylint docanalyzer/

[testenv:mypy]
deps =
    mypy>=0.910
    types-requests
    types-PyYAML
commands =
    mypy docanalyzer/

[testenv:docs]
deps =
    sphinx>=4.0.0
    sphinx-autodoc-typehints>=1.12.0
    sphinx-rtd-theme>=1.0.0
    myst-parser>=0.15.0
commands =
    sphinx-build -b html docs/ docs/_build/html

[testenv:performance]
deps =
    {[testenv]deps}
    psutil>=5.8.0
    memory-profiler>=0.60.0
commands =
    pytest -m performance tests/performance/

[testenv:security]
deps =
    bandit>=1.7.0
    safety>=2.0.0
commands =
    bandit -r docanalyzer/
    safety check

[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .tox,
    .venv,
    venv
```

## 7. Заключение

### 7.1 Ключевые принципы структуры
- **PyPI готовность**: Полная совместимость с современными стандартами Python пакетов
- **Модульность**: Четкое разделение компонентов по функциональности
- **Расширяемость**: Легкое добавление новых фильтров, команд и процессоров
- **Тестируемость**: Всеобъемлющая структура тестов с высоким покрытием
- **Документированность**: Билингвальная документация с примерами

### 7.2 Преимущества структуры
- **Навигация**: Интуитивно понятная организация файлов и модулей
- **Сопровождение**: Легкость поддержки и развития проекта
- **Публикация**: Готовность к публикации в PyPI без изменений
- **CI/CD**: Полная интеграция с системами непрерывной интеграции
- **Качество**: Автоматический контроль качества кода на всех уровнях

### 7.3 Следующие шаги
После создания структуры проекта можно приступать к реализации компонентов согласно плану реализации, начиная с базовых независимых компонентов и постепенно переходя к более сложным интеграционным частям системы. 