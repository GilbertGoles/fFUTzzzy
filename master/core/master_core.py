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
        
        # Инициализация базы данных первой
        self.db = DatabaseManager(config.get("db_path", "ffuf_master.db"))
        
        # Инициализация Redis с обработкой ошибок
        try:
            self.redis_client = redis.Redis(
                host=config["redis_host"],
                port=config["redis_port"],
                password=config.get("redis_password"),
                decode_responses=True
            )
            # Проверка подключения
            self.redis_client.ping()
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
            raise
        
        # Инициализация менеджеров
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
        try:
            logger.info("Starting master core")
            self.task_manager.start()
        except Exception as e:
            logger.error(f"Failed to start master core: {e}")
            raise
    
    def stop(self):
        """Останавливает мастер узел"""
        try:
            logger.info("Stopping master core")
            self.task_manager.stop()
        except Exception as e:
            logger.error(f"Error stopping master core: {e}")
            raise
    
    def create_scan_task(self, target: str, wordlist_name: str, 
                        worker_ids: List[str], options: Dict[str, Any] = None) -> str:
        """Создает задачу сканирования"""
        try:
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
        except Exception as e:
            logger.error(f"Failed to create scan task: {e}")
            raise
    
    def get_workers(self) -> Dict[str, Any]:
        """Возвращает информацию о воркерах"""
        try:
            return self.task_manager.get_workers_status()
        except Exception as e:
            logger.error(f"Failed to get workers: {e}")
            return {}
    
    def update_worker_threads(self, worker_id: str, threads: int):
        """Обновляет количество потоков воркера"""
        try:
            self.task_manager.update_worker_threads(worker_id, threads)
        except Exception as e:
            logger.error(f"Failed to update worker threads: {e}")
            raise
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Возвращает список задач"""
        try:
            return self.db.get_tasks()
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []
    
    def get_findings(self, task_id: str = None, checked: bool = None) -> List[Dict[str, Any]]:
        """Возвращает список находок"""
        try:
            return self.db.get_findings(task_id=task_id, checked=checked)
        except Exception as e:
            logger.error(f"Failed to get findings: {e}")
            return []
    
    def mark_finding_checked(self, finding_id: str, checked: bool = True):
        """Отмечает находку как проверенную"""
        try:
            self.db.mark_finding_checked(finding_id, checked)
        except Exception as e:
            logger.error(f"Failed to mark finding as checked: {e}")
            raise
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по безопасности"""
        try:
            return self.security_analyzer.get_security_summary()
        except Exception as e:
            logger.error(f"Failed to get security summary: {e}")
            return {"error": str(e)}
    
    def export_findings(self, format_type: str, task_id: str = None) -> str:
        """Экспортирует находки"""
        try:
            return self.security_analyzer.export_findings(format_type, task_id)
        except Exception as e:
            logger.error(f"Failed to export findings: {e}")
            raise
    
    def add_wordlist(self, name: str, path: str):
        """Добавляет новый словарь"""
        try:
            self.wordlists[name] = path
        except Exception as e:
            logger.error(f"Failed to add wordlist: {e}")
            raise
    
    def get_wordlists(self) -> Dict[str, str]:
        """Возвращает доступные словари"""
        try:
            return self.wordlists.copy()
        except Exception as e:
            logger.error(f"Failed to get wordlists: {e}")
            return {}
