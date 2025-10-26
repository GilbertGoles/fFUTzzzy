#!/usr/bin/env python3
import argparse
import logging
import sys
import os
from core.master_core import MasterCore
from gui.main_window import MainWindow

def setup_logging(level=logging.INFO):
    """Настройка логирования"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('master.log')
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='FFUF Master Controller')
    parser.add_argument('--redis-host', default='localhost', help='Redis host')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis port')
    parser.add_argument('--redis-password', help='Redis password')
    parser.add_argument('--db-path', default='ffuf_master.db', help='Database path')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Log level')
    
    args = parser.parse_args()
    
    # Настройка логирования
    setup_logging(getattr(logging, args.log_level))
    logger = logging.getLogger(__name__)
    
    try:
        # Конфигурация
        config = {
            "redis_host": args.redis_host,
            "redis_port": args.redis_port,
            "redis_password": args.redis_password,
            "db_path": args.db_path
        }
        
        # Создаем мастер core
        master_core = MasterCore(config)
        master_core.start()
        
        logger.info("Master core started successfully")
        
        # Запускаем GUI
        app = MainWindow(master_core)
        logger.info("GUI started successfully")
        
        # Главный цикл
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Master stopped by user")
    except Exception as e:
        logger.error(f"Master failed: {str(e)}")
        sys.exit(1)
    finally:
        master_core.stop()

if __name__ == "__main__":
    main()
