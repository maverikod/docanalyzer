# Integration Tests - DocAnalyzer

Интеграционные тесты для проверки полного workflow системы DocAnalyzer с реальными сервисами.

## 🎯 Назначение

Интеграционные тесты проверяют:
- **Полный пайплайн обработки** файлов от сканирования до сохранения в векторной базе
- **Интеграцию с реальными сервисами** на указанных портах
- **Обработку ошибок** и восстановление системы
- **Конкурентную обработку** файлов
- **Производительность** под нагрузкой
- **MCP команды** мониторинга и статистики

## 🔧 Требуемые сервисы

### Основные сервисы
- **Port 8001**: Embedding Service (Векторизация)
- **Port 8009**: Chunking Service (Семантический чанкинг)
- **Port 8007**: Vector Database (Хранение чанков)

### MCP сервисы
- **Port 8000**: MCP Proxy Server
- **Port 8002**: vstl (Vector Store)
- **Port 8003**: vst1 (Vector Store)
- **Port 8004**: emb (Embedding)
- **Port 8005**: embl (Embedding)
- **Port 8006**: svo (Semantic Chunking)
- **Port 8008**: aiadm (AI Admin)

## 📁 Структура тестов

```
tests/integration/
├── __init__.py                    # Инициализация пакета
├── conftest.py                    # Общие фикстуры и конфигурация
├── test_full_pipeline.py          # Полный пайплайн обработки
├── test_error_handling.py         # Обработка ошибок
├── test_concurrent_processing.py  # Конкурентная обработка
├── test_load_testing.py           # Нагрузочное тестирование
├── test_real_services_integration.py  # Реальные сервисы (8001, 8009, 8007)
├── test_real_mcp_integration.py   # Реальные MCP сервисы
├── requirements.txt               # Зависимости для тестов
├── run_integration_tests.py       # Скрипт запуска
└── README.md                      # Эта документация
```

## 🚀 Запуск тестов

### Быстрый запуск
```bash
# Запуск всех интеграционных тестов
python tests/integration/run_integration_tests.py

# Запуск с подробным выводом
python tests/integration/run_integration_tests.py --verbose

# Запуск с покрытием кода
python tests/integration/run_integration_tests.py --coverage
```

### Запуск конкретных тестов
```bash
# Только тесты с реальными сервисами
python tests/integration/run_integration_tests.py --test-pattern "real_services"

# Только MCP тесты
python tests/integration/run_integration_tests.py --test-pattern "mcp"

# Только тесты производительности
python tests/integration/run_integration_tests.py --test-pattern "load_testing"
```

### Запуск через pytest
```bash
# Все интеграционные тесты
pytest tests/integration/ -v

# Конкретный тест
pytest tests/integration/test_real_services_integration.py::TestRealServicesIntegration::test_complete_real_services_pipeline -v

# С покрытием
pytest tests/integration/ --cov=docanalyzer --cov-report=html
```

## 📊 Категории тестов

### 1. Полный пайплайн (`test_full_pipeline.py`)
- ✅ End-to-end обработка файлов
- ✅ Интеграция всех компонентов
- ✅ Проверка консистентности данных
- ✅ Метрики производительности

### 2. Обработка ошибок (`test_error_handling.py`)
- ✅ Сбои сервисов векторной базы
- ✅ Сбои базы данных
- ✅ Обработка некорректных файлов
- ✅ Восстановление после ошибок

### 3. Конкурентная обработка (`test_concurrent_processing.py`)
- ✅ Одновременная обработка каталогов
- ✅ Управление ресурсами
- ✅ Потокобезопасность
- ✅ Предотвращение deadlock'ов

### 4. Нагрузочное тестирование (`test_load_testing.py`)
- ✅ Высоконагруженная обработка файлов
- ✅ Использование памяти под нагрузкой
- ✅ CPU утилизация
- ✅ Пропускная способность

### 5. Реальные сервисы (`test_real_services_integration.py`)
- ✅ Health check всех сервисов
- ✅ Интеграция с embedding service (8001)
- ✅ Интеграция с chunking service (8009)
- ✅ Интеграция с vector database (8007)
- ✅ Полный pipeline с реальными данными

### 6. MCP интеграция (`test_real_mcp_integration.py`)
- ✅ Health check MCP сервисов
- ✅ Команды мониторинга
- ✅ Системная статистика
- ✅ Статистика обработки
- ✅ Статус очереди

## 🔍 Проверка сервисов

### Автоматическая проверка
Скрипт автоматически проверяет доступность всех сервисов перед запуском тестов:

```bash
python tests/integration/run_integration_tests.py
```

### Ручная проверка
```bash
# Проверка embedding service
curl http://localhost:8001/health

# Проверка chunking service  
curl http://localhost:8009/health

# Проверка vector database
curl http://localhost:8007/health

# Проверка MCP proxy
curl http://localhost:8000/health
```

## 📈 Метрики и отчеты

### Покрытие кода
```bash
# Генерация HTML отчета
python tests/integration/run_integration_tests.py --coverage

# Отчет будет доступен в tests/integration/htmlcov/
```

### Производительность
```bash
# Бенчмарки
python tests/integration/run_integration_tests.py --benchmark

# Параллельное выполнение
python tests/integration/run_integration_tests.py --parallel
```

## 🛠️ Устранение неполадок

### Сервисы недоступны
```bash
# Проверьте статус сервисов
python tests/integration/run_integration_tests.py --skip-service-check

# Запустите недостающие сервисы
# См. документацию по развертыванию сервисов
```

### Тесты падают
```bash
# Подробный вывод для диагностики
python tests/integration/run_integration_tests.py --verbose

# Запуск конкретного теста
pytest tests/integration/test_real_services_integration.py::TestRealServicesIntegration::test_real_services_health_check -v -s
```

### Проблемы с зависимостями
```bash
# Установка зависимостей
pip install -r tests/integration/requirements.txt

# Обновление зависимостей
pip install --upgrade -r tests/integration/requirements.txt
```

## 📋 Требования к окружению

### Системные требования
- Python 3.9+
- 4GB+ RAM для нагрузочных тестов
- Свободное место на диске для тестовых файлов

### Зависимости
```bash
# Основные зависимости
pip install aiohttp psutil pytest-asyncio

# Все зависимости для тестов
pip install -r tests/integration/requirements.txt
```

### Переменные окружения
```bash
# Опционально: настройка таймаутов
export DOCANALYZER_TEST_TIMEOUT=30
export DOCANALYZER_TEST_RETRIES=3

# Опционально: логирование
export DOCANALYZER_LOG_LEVEL=INFO
```

## 🎯 Результаты тестирования

### Успешное выполнение
```
✅ All required services are healthy and ready for testing
🧪 Running integration tests...
✅ Health check completed: healthy
✅ System stats collected: Linux
✅ Processing stats collected: 0 total files
✅ Queue status checked: 0 total items
🎉 All integration tests passed!
```

### Отчет о покрытии
```
📊 INTEGRATION TESTS REPORT
============================================================
📁 Test artifacts available in: tests/integration/htmlcov/
📁 Test artifacts available in: tests/integration/.pytest_cache/

🎯 Next Steps:
1. Review test output above for any failures
2. Check coverage report in tests/integration/htmlcov/
3. Verify all services are still healthy
4. Run specific test categories if needed
```

## 🔄 Непрерывная интеграция

### GitHub Actions
```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]
jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r tests/integration/requirements.txt
      - name: Start services
        run: |
          # Запуск тестовых сервисов
      - name: Run integration tests
        run: |
          python tests/integration/run_integration_tests.py --coverage
```

### Локальная разработка
```bash
# Запуск тестов при разработке
watch -n 30 'python tests/integration/run_integration_tests.py --test-pattern "real_services"'

# Автоматический перезапуск при изменениях
nodemon --exec 'python tests/integration/run_integration_tests.py' --ext py
```

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте статус сервисов** - убедитесь, что все требуемые сервисы запущены
2. **Просмотрите логи** - используйте `--verbose` для подробного вывода
3. **Запустите отдельные тесты** - изолируйте проблему
4. **Проверьте зависимости** - убедитесь, что все пакеты установлены

### Полезные команды
```bash
# Диагностика сервисов
python tests/integration/run_integration_tests.py --skip-service-check

# Быстрая проверка
pytest tests/integration/test_real_services_integration.py::TestRealServicesIntegration::test_real_services_health_check -v

# Полная диагностика
python tests/integration/run_integration_tests.py --verbose --coverage --benchmark
``` 