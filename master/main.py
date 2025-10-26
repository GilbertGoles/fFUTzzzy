#!/usr/bin/env python3
import argparse
import logging
import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.master_core import MasterCore
from cli_controller import CLIController

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
    parser.add_argument('--cli', action='store_true', help='Use CLI interface instead of GUI')
    
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
        
        if args.cli:
            # Запускаем CLI интерфейс
            logger.info("Starting CLI interface")
            cli = CLIController(master_core)
            cli.show_menu()
        else:
            # Пробуем запустить GUI
            try:
                from gui.main_window import MainWindow
                logger.info("Starting GUI interface")
                app = MainWindow(master_core)
                app.run()
            except ImportError as e:
                logger.warning(f"GUI not available: {e}. Falling back to CLI.")
                print("GUI not available, falling back to CLI interface.")
                cli = CLIController(master_core)
                cli.show_menu()
        
    except KeyboardInterrupt:
        logger.info("Master stopped by user")
    except Exception as e:
        logger.error(f"Master failed: {str(e)}")
        sys.exit(1)
    finally:
        master_core.stop()

if __name__ == "__main__":
    main()
