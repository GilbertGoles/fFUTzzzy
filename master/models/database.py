import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "ffuf_master.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Инициализирует таблицы БД"""
        with sqlite3.connect(self.db_path) as conn:
            # Таблица задач
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    wordlist_name TEXT NOT NULL,
                    wordlist_path TEXT NOT NULL,
                    options TEXT NOT NULL,
                    worker_ids TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0,
                    findings_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
            # Таблица находок
            conn.execute('''
                CREATE TABLE IF NOT EXISTS findings (
                    finding_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    content_length INTEGER NOT NULL,
                    words INTEGER NOT NULL,
                    lines INTEGER NOT NULL,
                    severity TEXT NOT NULL,
                    detected_issues TEXT NOT NULL,
                    raw_response TEXT,
                    checked BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                )
            ''')
            
            # Таблица воркеров
            conn.execute('''
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    hostname TEXT NOT NULL,
                    status TEXT NOT NULL,
                    threads INTEGER DEFAULT 10,
                    current_task TEXT,
                    last_seen TIMESTAMP,
                    tasks_completed INTEGER DEFAULT 0,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица конфигураций сканирования
            conn.execute('''
                CREATE TABLE IF NOT EXISTS scan_configs (
                    config_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    target TEXT NOT NULL,
                    wordlist TEXT NOT NULL,
                    threads_per_worker INTEGER DEFAULT 10,
                    rate_limit INTEGER,
                    follow_redirects BOOLEAN DEFAULT TRUE,
                    recursive BOOLEAN DEFAULT FALSE,
                    extensions TEXT,
                    headers TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def save_task(self, task_data: Dict[str, Any]) -> bool:
        """Сохраняет задачу в БД"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO tasks 
                    (task_id, target, wordlist_name, wordlist_path, options, worker_ids, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_data['task_id'],
                    task_data['target'],
                    task_data['wordlist_name'],
                    task_data['wordlist_path'],
                    json.dumps(task_data['options']),
                    json.dumps(task_data['worker_ids']),
                    'pending'
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save task: {str(e)}")
            return False
    
    def update_task_progress(self, task_id: str, progress: float):
        """Обновляет прогресс задачи"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE tasks SET progress = ? WHERE task_id = ?',
                (progress, task_id)
            )
            conn.commit()
    
    def complete_task(self, task_id: str, findings_count: int):
        """Отмечает задачу как завершенную"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE tasks 
                SET status = 'completed', progress = 100, 
                    completed_at = CURRENT_TIMESTAMP, findings_count = ?
                WHERE task_id = ?
            ''', (findings_count, task_id))
            conn.commit()
    
    def save_finding(self, finding_data: Dict[str, Any]) -> bool:
        """Сохраняет находку в БД"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO findings 
                    (finding_id, task_id, url, status_code, content_length, words, lines, 
                     severity, detected_issues, raw_response)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    finding_data['finding_id'],
                    finding_data['task_id'],
                    finding_data['url'],
                    finding_data['status_code'],
                    finding_data['content_length'],
                    finding_data['words'],
                    finding_data['lines'],
                    finding_data['severity'],
                    json.dumps(finding_data['detected_issues']),
                    finding_data.get('raw_response')
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save finding: {str(e)}")
            return False
    
    def get_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Возвращает список задач"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM tasks 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_findings(self, task_id: str = None, checked: bool = None) -> List[Dict[str, Any]]:
        """Возвращает список находок"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = '''
                SELECT f.*, t.target, t.wordlist_name 
                FROM findings f 
                LEFT JOIN tasks t ON f.task_id = t.task_id
            '''
            params = []
            
            if task_id is not None:
                query += ' WHERE f.task_id = ?'
                params.append(task_id)
            elif checked is not None:
                query += ' WHERE f.checked = ?'
                params.append(checked)
            
            query += ' ORDER BY f.created_at DESC'
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_finding_checked(self, finding_id: str, checked: bool = True):
        """Отмечает находку как проверенную"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE findings SET checked = ? WHERE finding_id = ?',
                (checked, finding_id)
            )
            conn.commit()
