#!/usr/bin/env python3
import argparse
import logging
import sys
import os

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.worker_core import WorkerCore
from utils.config import load_config

def setup_logging(level=logging.INFO):
    """Настройка логирования"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('worker.log')
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='Distributed Fuzzing Worker')
    parser.add_argument('--config', '-c', help='Path to config file')
    parser.add_argument('--worker-id', help='Worker ID')
    parser.add_argument('--redis-host', help='Redis host')
    parser.add_argument('--redis-port', type=int, help='Redis port')
    parser.add_argument('--threads', type=int, help='Number of threads')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Log level')
    
    args = parser.parse_args()
    
    # Настройка логирования
    setup_logging(getattr(logging, args.log_level))
    
    # Загрузка конфигурации
    config = load_config(args.config)
    
    # Переопределение аргументами командной строки
    if args.worker_id:
        config["worker_id"] = args.worker_id
    if args.redis_host:
        config["redis_host"] = args.redis_host
    if args.redis_port:
        config["redis_port"] = args.redis_port
    if args.threads:
        config["threads"] = args.threads
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting worker with config: {config}")
    
    try:
        # Создаем и запускаем воркер
        worker = WorkerCore(config)
        worker.start()
        
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
