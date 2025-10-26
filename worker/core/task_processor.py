import json
import time
import logging
from typing import Dict, Any
from .ffuf_wrapper import FFufWrapper

logger = logging.getLogger(__name__)

class TaskProcessor:
    def __init__(self):
        self.ffuf = FFufWrapper()
        self.current_task = None
        
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает задачу от мастера
        """
        self.current_task = task_data
        task_id = task_data.get("task_id")
        
        logger.info(f"Processing task {task_id}")
        
        try:
            # Выполняем фаззинг
            result = self.ffuf.run_ffuf(
                target=task_data["target"],
                wordlist=task_data["wordlist_path"],
                options=task_data.get("options", {})
            )
            
            # Формируем ответ
            response = {
                "task_id": task_id,
                "worker_id": task_data.get("worker_id"),
                "status": "completed",
                "results": result,
                "timestamp": time.time(),
                "error": result.get("error")
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Task processing failed: {str(e)}")
            return {
                "task_id": task_id,
                "worker_id": task_data.get("worker_id"),
                "status": "failed",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Возвращает статус воркера
        """
        return {
            "current_task": self.current_task,
            "ffuf_available": self._check_ffuf_availability(),
            "timestamp": time.time()
        }
    
    def _check_ffuf_availability(self) -> bool:
        """
        Проверяет доступность ffuf
        """
        try:
            import subprocess
            result = subprocess.run(["ffuf", "-h"], capture_output=True)
            return result.returncode == 0
        except:
            return False
