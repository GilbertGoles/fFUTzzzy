import redis
import json
import uuid
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, redis_client, db_manager):
        self.redis = redis_client
        self.db = db_manager
        self.active_tasks = {}
        self.is_running = False
        self.result_thread = None
    
    def start(self):
        """Запускает менеджер задач"""
        self.is_running = True
        self.result_thread = threading.Thread(target=self._result_processor)
        self.result_thread.daemon = True
        self.result_thread.start()
        logger.info("Task manager started")
    
    def stop(self):
        """Останавливает менеджер задач"""
        self.is_running = False
        if self.result_thread:
            self.result_thread.join(timeout=5)
        logger.info("Task manager stopped")
    
    def create_task(self, task_data: Dict[str, Any]) -> str:
        """Создает новую задачу"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Подготавливаем данные задачи
        full_task_data = {
            "task_id": task_id,
            "target": task_data["target"],
            "wordlist_name": task_data["wordlist_name"],
            "wordlist_path": task_data["wordlist_path"],
            "options": task_data.get("options", {}),
            "worker_ids": task_data.get("worker_ids", []),
            "created_at": time.time()
        }
        
        # Сохраняем в БД
        self.db.save_task(full_task_data)
        
        # Распределяем по воркерам
        self._distribute_task(full_task_data)
        
        self.active_tasks[task_id] = {
            "status": "distributed",
            "workers": task_data.get("worker_ids", []),
            "results_received": 0,
            "total_workers": len(task_data.get("worker_ids", []))
        }
        
        logger.info(f"Created task {task_id} for {len(task_data['worker_ids'])} workers")
        return task_id
    
    def _distribute_task(self, task_data: Dict[str, Any]):
        """Распределяет задачу между воркерами"""
        for worker_id in task_data["worker_ids"]:
            worker_task = task_data.copy()
            worker_task["worker_id"] = worker_id
            
            # Отправляем задачу в очередь воркера
            self.redis.rpush(
                f"tasks:{worker_id}",
                json.dumps(worker_task)
            )
            
            logger.debug(f"Sent task {task_data['task_id']} to worker {worker_id}")
    
    def get_workers_status(self) -> Dict[str, Any]:
        """Возвращает статус всех воркеров"""
        workers = {}
        
        try:
            # Активные воркеры
            active_workers = self.redis.hgetall("workers:active")
            health_data = self.redis.hgetall("workers:health")
            
            for worker_id, worker_json in active_workers.items():
                worker_data = json.loads(worker_json)
                worker_health = health_data.get(worker_id)
                
                workers[worker_id] = {
                    **worker_data,
                    "health": json.loads(worker_health) if worker_health else None,
                    "status": "active" if worker_health else "offline"
                }
                
        except Exception as e:
            logger.error(f"Failed to get workers status: {str(e)}")
        
        return workers
    
    def update_worker_threads(self, worker_id: str, threads: int):
        """Обновляет количество потоков воркера"""
        try:
            command = {
                "type": "update_threads",
                "threads": threads,
                "timestamp": time.time()
            }
            
            self.redis.rpush(
                f"control:{worker_id}",
                json.dumps(command)
            )
            
            logger.info(f"Updated worker {worker_id} threads to {threads}")
            
        except Exception as e:
            logger.error(f"Failed to update worker threads: {str(e)}")
    
    def _result_processor(self):
        """Обрабатывает результаты от воркеров"""
        while self.is_running:
            try:
                # Блокирующее получение результата
                result_data = self.redis.blpop("results", 1)
                
                if result_data:
                    _, result_json = result_data
                    result = json.loads(result_json)
                    self._process_worker_result(result)
                    
            except Exception as e:
                logger.error(f"Result processor error: {str(e)}")
                time.sleep(5)
    
    def _process_worker_result(self, result: Dict[str, Any]):
        """Обрабатывает результат от воркера"""
        task_id = result["task_id"]
        worker_id = result["worker_id"]
        status = result["status"]
        
        logger.info(f"Processing result from worker {worker_id} for task {task_id}")
        
        if status == "completed":
            # Парсим результаты
            from .result_parser import ResultParser
            parser = ResultParser()
            findings = parser.parse_ffuf_results(task_id, result["results"])
            
            # Сохраняем находки
            for finding in findings:
                self.db.save_finding(finding)
            
            # Обновляем прогресс задачи
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["results_received"] += 1
                
                progress = (
                    self.active_tasks[task_id]["results_received"] / 
                    self.active_tasks[task_id]["total_workers"] * 100
                )
                
                self.db.update_task_progress(task_id, progress)
                
                # Если все воркеры завершили
                if self.active_tasks[task_id]["results_received"] >= self.active_tasks[task_id]["total_workers"]:
                    self.db.complete_task(task_id, len(findings))
                    del self.active_tasks[task_id]
                    logger.info(f"Task {task_id} completed with {len(findings)} findings")
        
        elif status == "failed":
            logger.error(f"Worker {worker_id} failed task {task_id}: {result.get('error')}")
            # TODO: Реализовать перераспределение задачи
