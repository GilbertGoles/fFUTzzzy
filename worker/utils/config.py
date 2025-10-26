import os
import json
from typing import Dict, Any

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Загружает конфигурацию воркера
    """
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    
    # Конфигурация по умолчанию
    return {
        "worker_id": os.environ.get("WORKER_ID", f"worker_{os.urandom(4).hex()}"),
        "redis_host": os.environ.get("REDIS_HOST", "localhost"),
        "redis_port": int(os.environ.get("REDIS_PORT", 6379)),
        "redis_password": os.environ.get("REDIS_PASSWORD"),
        "threads": int(os.environ.get("WORKER_THREADS", 10)),
        "hostname": os.environ.get("HOSTNAME", "unknown"),
        "log_level": os.environ.get("LOG_LEVEL", "INFO")
    }
