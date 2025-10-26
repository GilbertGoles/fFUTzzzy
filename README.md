# fFUTzzzy

##  Внутренняя архитектура и передача данных

### Схема взаимодействия:

```
Master GUI → Master Core → Redis ← Worker Core → FFUF
     ↓
  SQLite DB
```

### Конкретные файлы и их взаимодействие:

**Master Side:**

- `main.py` → запускает всю систему
- `gui/main_window.py` → интерфейс пользователя
- `core/master_core.py` → основная логика мастера
- `core/task_manager.py` → управление задачами
- `core/result_parser.py` → анализ результатов FFUF
- `models/database.py` → хранение в SQLite
- `utils/exporters.py` → экспорт результатов

**Worker Side:**

- `main.py` → запуск воркера
- `core/worker_core.py` → основная логика воркера
- `core/ffuf_wrapper.py` → запуск FFUF
- `core/task_processor.py` → обработка задач

### Процесс передачи данных:

1. **Создание задачи:**

   ```
   GUI → master_core.create_scan_task() → task_manager.create_task() → Redis (очередь tasks:worker_id)
   ```

2. **Обработка воркером:**

   ```
   worker_core (слушает Redis) → task_processor.process_task() → ffuf_wrapper.run_ffuf()
   ```

3. **Возврат результатов:**

   ```
   worker_core → Redis (очередь results) → task_manager._process_worker_result() → result_parser.parse_ffuf_results() → database.save_finding()
   ```

4. **Обновление GUI:**

   ```
   database.get_findings() → master_core.get_findings() → GUI.refresh_findings()
   ```

##  Рабочие и нерабочие функции

### ✅ Полностью рабочие функции:
- **Создание сканирования** (вкладка New Scan)
- **Просмотр воркеров** (вкладка Workers) 
- **Просмотр задач** (вкладка Tasks)
- **Базовый просмотр находок** (вкладка Findings)
- **Обновление потоков воркеров**
- **Экспорт в JSON/CSV**
- **Автоматическое перераспределение задач**

### ⚠️ Частично рабочие / Требуют доработки:
- **Mark as Checked** - работает, но нет массового выделения
- **Фильтрация findings** - базовая работает, сложные фильтры нужно дорабатывать
- **Dashboard статистика** - отображается, но без графиков
- **Детали findings** - открывается окно, но нет реального HTTP response

### ❌ Не реализованы / Требуют реализации:
- **Пауза/возобновление сканирования**
- **Массовые операции с findings** 
- **Просмотр полных HTTP ответов**
- **Интеграция с другими инструментами (nuclei, etc)**
- **Управление словарями через GUI**
- **Расширенная аналитика и графики**

##  Docker - кому и зачем

### Для Мастера (ваш ПК):

```bash
# ОБЯЗАТЕЛЬНО: Только Redis в Docker
docker run -d -p 6379:6379 --name redis-server redis:alpine

# Master GUI запускается нативно на Python
```

### Для Workers (удаленные серверы):

```bash
# ВАРИАНТ 1: Нативный Python (рекомендуется)
python main.py --worker-id worker01 --redis-host IP_MASTER

# ВАРИАНТ 2: Docker образ worker
docker build -t ffuf-worker .
docker run -d --name worker01 ffuf-worker --redis-host IP_MASTER
```

### Docker-compose для полной системы:

```yaml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    
  master:
    build: ./master
    ports:
      - "5000:5000"  # если будет веб-интерфейс
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis

  worker1:
    build: ./worker  
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - WORKER_ID=worker01
```

##  Что происходит "под капотом" при сканировании

### Пример полного цикла:

1. **Пользователь в GUI:**

   - Target: `https://example.com/FUZZ`
   - Wordlist: `common.txt`
   - Workers: `worker01, worker02`

2. **Master создает задачу:**

```python
# В Redis появляется:
tasks:worker01 = [{
  "task_id": "task_abc123", 
  "target": "https://example.com/FUZZ",
  "wordlist_path": "/opt/wordlists/common.txt",
  "worker_id": "worker01"
}]
```

3. **Worker забирает задачу:**

```bash
# Worker запускает:
ffuf -u "https://example.com/FUZZ" -w /opt/wordlists/common.txt -o - -of json -t 10
```

4. **Результаты возвращаются:**

```python
# В Redis очередь results:
{
  "task_id": "task_abc123",
  "worker_id": "worker01", 
  "results": { ... JSON от FFUF ... }
}
```

5. **Master парсит и сохраняет:**

```python
# В SQLite findings:
{
  "url": "https://example.com/admin",
  "status_code": 200,
  "severity": "high",
  "detected_issues": ["admin panel found"]
}
```

## 5. Рекомендации по запуску

### На вашем ПК (Master):

```bash
# 1. Запустить Redis
docker run -d -p 6379:6379 --name redis redis:alpine

# 2. Запустить Master GUI  
cd master
python main.py --redis-host localhost
```

### На удаленных серверах (Workers):

```bash
# На каждом сервере:
cd worker
python main.py --worker-id server01 --redis-host IP_ВАШЕГО_ПК --threads 20
```

### Проверка связи:

```bash
# На мастере проверяем подключение workers
redis-cli
> KEYS "workers:*"  # Должны быть ключи активных воркеров
> LRANGE results 0 -1  # Можно посмотреть очередь результатов
```

##  Что можно улучшить сразу

1. **Добавить логирование** в файлы для отладки
2. **Настроить wordlists** под ваши нужды
3. **Добавить аутентификацию Redis** если нужно
4. **Настроить количество потоков** по умолчанию
5. **Добавить тестовые цели** для проверки системы

