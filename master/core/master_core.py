import redis
import logging
from typing import Dict, List, Any
from .task_manager import TaskManager
from models.database import DatabaseManager
from .security_analyzer import SecurityAnalyzer

logger = logging.getLogger(__name__)

class MasterCore:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.Redis(
            host=config["redis_host"],
            port=config["redis_port"],
            password=config.get("redis_password"),
            decode_responses=True
        )
        self.db = DatabaseManager(config.get("db_path", "ffuf_master.db"))
        self.task_manager = TaskManager(self.redis_client, self.db)
        self.security_analyzer = SecurityAnalyzer(self.db)
        
        # Available wordlists
        self.wordlists = {
            "common.txt": "/opt/wordlists/common.txt",
            "directory-list.txt": "/opt/wordlists/directory-list.txt", 
            "api-wordlist.txt": "/opt/wordlists/api-wordlist.txt",
            "custom.txt": "/opt/wordlists/custom.txt"
        }
    
    def start(self):
        """Запускает мастер узел"""
        logger.info("Starting master core")
        self.task_manager.start()
    
    def stop(self):
        """Останавливает мастер узел"""
        logger.info("Stopping master core")
        self.task_manager.stop()
    
    def create_scan_task(self, target: str, wordlist_name: str, 
                        worker_ids: List[str], options: Dict[str, Any] = None) -> str:
        """Создает задачу сканирования"""
        
        if wordlist_name not in self.wordlists:
            raise ValueError(f"Wordlist {wordlist_name} not found")
        
        task_data = {
            "target": target,
            "wordlist_name": wordlist_name,
            "wordlist_path": self.wordlists[wordlist_name],
            "worker_ids": worker_ids,
            "options": options or {}
        }
        
        return self.task_manager.create_task(task_data)
    
    def get_workers(self) -> Dict[str, Any]:
        """Возвращает информацию о воркерах"""
        return self.task_manager.get_workers_status()
    
    def update_worker_threads(self, worker_id: str, threads: int):
        """Обновляет количество потоков воркера"""
        self.task_manager.update_worker_threads(worker_id, threads)
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Возвращает список задач"""
        return self.db.get_tasks()
    
    def get_findings(self, task_id: str = None, checked: bool = None) -> List[Dict[str, Any]]:
        """Возвращает список находок"""
        return self.db.get_findings(task_id=task_id, checked=checked)
    
    def mark_finding_checked(self, finding_id: str, checked: bool = True):
        """Отмечает находку как проверенную"""
        self.db.mark_finding_checked(finding_id, checked)
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по безопасности"""
        return self.security_analyzer.get_security_summary()
    
    def export_findings(self, format_type: str, task_id: str = None) -> str:
        """Экспортирует находки"""
        return self.security_analyzer.export_findings(format_type, task_id)
    
    def add_wordlist(self, name: str, path: str):
        """Добавляет новый словарь"""
        self.wordlists[name] = path
    
    def get_wordlists(self) -> Dict[str, str]:
        """Возвращает доступные словари"""
        return self.wordlists.copy()
