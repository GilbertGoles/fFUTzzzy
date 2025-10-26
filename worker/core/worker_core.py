import redis
import json
import time
import threading
import logging
from typing import Dict, Any
from .task_processor import TaskProcessor

logger = logging.getLogger(__name__)

class WorkerCore:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.Redis(
            host=config["redis_host"],
            port=config["redis_port"],
            password=config.get("redis_password"),
            decode_responses=True
        )
        self.task_processor = TaskProcessor()
        self.worker_id = config["worker_id"]
        self.is_running = False
        self.threads = config.get("threads", 10)
        
        # Очереди
        self.task_queue = f"tasks:{self.worker_id}"
        self.result_queue = "results"
        self.control_queue = f"control:{self.worker_id}"
        
    def start(self):
        """
        Запускает воркер
        """
        self.is_running = True
        logger.info(f"Worker {self.worker_id} started")
        
        # Регистрируем воркера
        self._register_worker()
        
        # Запускаем потоки для обработки задач и управления
        task_thread = threading.Thread(target=self._task_loop)
        control_thread = threading.Thread(target=self._control_loop)
        health_thread = threading.Thread(target=self._health_loop)
        
        task_thread.daemon = True
        control_thread.daemon = True
        health_thread.daemon = True
        
        task_thread.start()
        control_thread.start()
        health_thread.start()
        
        # Ждем завершения
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """
        Останавливает воркер
        """
        self.is_running = False
        self._unregister_worker()
        logger.info(f"Worker {self.worker_id} stopped")
    
    def _task_loop(self):
        """
        Основной цикл обработки задач
        """
        while self.is_running:
            try:
                # Блокирующее получение задачи (таймаут 1 сек)
                task_data = self.redis_client.blpop(self.task_queue, 1)
                
                if task_data:
                    _, task_json = task_data
                    task = json.loads(task_json)
                    
                    logger.info(f"Received task: {task.get('task_id')}")
                    
                    # Обрабатываем задачу
                    result = self.task_processor.process_task(task)
                    
                    # Отправляем результат
                    self.redis_client.rpush(self.result_queue, json.dumps(result))
                    
            except Exception as e:
                logger.error(f"Task loop error: {str(e)}")
                time.sleep(5)
    
    def _control_loop(self):
        """
        Цикл обработки управляющих команд
        """
        while self.is_running:
            try:
                # Проверяем управляющие команды
                command = self.redis_client.lpop(self.control_queue)
                
                if command:
                    self._handle_control_command(json.loads(command))
                    
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Control loop error: {str(e)}")
                time.sleep(5)
    
    def _health_loop(self):
        """
        Цикл отправки health-check
        """
        while self.is_running:
            try:
                health_data = {
                    "worker_id": self.worker_id,
                    "status": "active",
                    "timestamp": time.time(),
                    "current_threads": self.threads,
                    "processor_status": self.task_processor.get_status()
                }
                
                self.redis_client.hset(
                    "workers:health",
                    self.worker_id,
                    json.dumps(health_data)
                )
                
                time.sleep(30)  # Отправляем каждые 30 секунд
                
            except Exception as e:
                logger.error(f"Health loop error: {str(e)}")
                time.sleep(30)
    
    def _handle_control_command(self, command: Dict[str, Any]):
        """
        Обрабатывает управляющие команды от мастера
        """
        cmd_type = command.get("type")
        
        if cmd_type == "update_threads":
            new_threads = command.get("threads", 10)
            self.threads = max(1, min(100, new_threads))  # Ограничение 1-100
            logger.info(f"Threads updated to {self.threads}")
            
        elif cmd_type == "pause":
            # Реализация паузы (можно добавить флаг)
            logger.info("Pause command received")
            
        elif cmd_type == "resume":
            logger.info("Resume command received")
            
        elif cmd_type == "shutdown":
            logger.info("Shutdown command received")
            self.stop()
    
    def _register_worker(self):
        """
        Регистрирует воркера в системе
        """
        worker_info = {
            "worker_id": self.worker_id,
            "status": "active",
            "start_time": time.time(),
            "threads": self.threads,
            "hostname": self.config.get("hostname", "unknown")
        }
        
        self.redis_client.hset(
            "workers:active",
            self.worker_id,
            json.dumps(worker_info)
        )
    
    def _unregister_worker(self):
        """
        Удаляет воркера из системы
        """
        self.redis_client.hdel("workers:active", self.worker_id)
        self.redis_client.hdel("workers:health", self.worker_id)
