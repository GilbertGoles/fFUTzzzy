#!/usr/bin/env python3
import argparse
import logging
import sys
import time
import os

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.master_core import MasterCore

class CLIController:
    def __init__(self, master_core: MasterCore):
        self.master_core = master_core
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def show_menu(self):
        """Показывает главное меню"""
        while True:
            print("\n" + "="*50)
            print("FFUF Master Controller - CLI Version")
            print("="*50)
            print("1. Start New Scan")
            print("2. Show Workers Status") 
            print("3. Show Tasks")
            print("4. Show Findings")
            print("5. Update Worker Threads")
            print("6. Export Findings")
            print("7. Security Summary")
            print("8. Add Wordlist")
            print("0. Exit")
            print("="*50)
            
            choice = input("Enter your choice: ").strip()
            
            if choice == "1":
                self.start_scan()
            elif choice == "2":
                self.show_workers()
            elif choice == "3":
                self.show_tasks()
            elif choice == "4":
                self.show_findings()
            elif choice == "5":
                self.update_worker_threads()
            elif choice == "6":
                self.export_findings()
            elif choice == "7":
                self.security_summary()
            elif choice == "8":
                self.add_wordlist()
            elif choice == "0":
                self.logger.info("Exiting...")
                break
            else:
                print("Invalid choice!")
    
    def start_scan(self):
        """Запускает новое сканирование через CLI"""
        print("\n--- New Scan Configuration ---")
        
        target = input("Target URL (with FUZZ): ").strip()
        if not target:
            print("Target is required!")
            return
        
        # Показываем доступные словари
        wordlists = self.master_core.get_wordlists()
        print("\nAvailable wordlists:")
        for i, name in enumerate(wordlists.keys(), 1):
            print(f"{i}. {name}")
        
        try:
            wordlist_choice = int(input("Select wordlist (number): ")) - 1
            wordlist_name = list(wordlists.keys())[wordlist_choice]
        except (ValueError, IndexError):
            print("Invalid wordlist selection!")
            return
        
        # Выбор воркеров
        workers = self.master_core.get_workers()
        active_workers = [wid for wid, info in workers.items() if info.get("status") == "active"]
        
        if not active_workers:
            print("No active workers available!")
            return
        
        print("\nActive workers:")
        for i, worker_id in enumerate(active_workers, 1):
            print(f"{i}. {worker_id}")
        
        try:
            worker_choice = input("Select workers (comma-separated numbers or 'all'): ").strip()
            if worker_choice.lower() == 'all':
                selected_workers = active_workers
            else:
                indices = [int(x.strip())-1 for x in worker_choice.split(',')]
                selected_workers = [active_workers[i] for i in indices]
        except (ValueError, IndexError):
            print("Invalid worker selection!")
            return
        
        # Дополнительные опции
        print("\nAdvanced options:")
        threads = input("Threads per worker (default: 10): ").strip()
        threads = int(threads) if threads else 10
        
        options = {
            "threads": threads
        }
        
        # Запуск сканирования
        try:
            task_id = self.master_core.create_scan_task(
                target=target,
                wordlist_name=wordlist_name,
                worker_ids=selected_workers,
                options=options
            )
            print(f"\n✅ Scan started successfully!")
            print(f"Task ID: {task_id}")
            print(f"Workers: {', '.join(selected_workers)}")
            print(f"Target: {target}")
            
        except Exception as e:
            print(f"❌ Failed to start scan: {str(e)}")
    
    def show_workers(self):
        """Показывает статус воркеров"""
        workers = self.master_core.get_workers()
        
        print("\n--- Workers Status ---")
        if not workers:
            print("No workers connected")
            return
        
        for worker_id, info in workers.items():
            status = info.get('status', 'unknown')
            threads = info.get('threads', 0)
            last_seen = info.get('last_seen', 'never')
            current_task = info.get('current_task', 'idle')
            
            status_icon = "🟢" if status == "active" else "🔴" if status == "offline" else "🟡"
            
            print(f"{status_icon} {worker_id}")
            print(f"   Status: {status}")
            print(f"   Threads: {threads}")
            print(f"   Current Task: {current_task}")
            print(f"   Last Seen: {last_seen}")
            print()
    
    def show_tasks(self):
        """Показывает список задач"""
        tasks = self.master_core.get_tasks()
        
        print("\n--- Tasks ---")
        if not tasks:
            print("No tasks found")
            return
        
        for task in tasks:
            task_id = task['task_id']
            target = task['target']
            status = task['status']
            progress = task['progress']
            findings_count = task['findings_count']
            
            status_icon = "🟢" if status == "completed" else "🟡" if status == "in_progress" else "⚪"
            
            print(f"{status_icon} {task_id}")
            print(f"   Target: {target}")
            print(f"   Status: {status} ({progress}%)")
            print(f"   Findings: {findings_count}")
            print(f"   Created: {task['created_at']}")
            print()
    
    def show_findings(self):
        """Показывает находки"""
        findings = self.master_core.get_findings()
        
        print("\n--- Findings ---")
        if not findings:
            print("No findings yet")
            return
        
        # Группируем по критичности
        by_severity = {}
        for finding in findings:
            severity = finding['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(finding)
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            if severity in by_severity:
                findings_list = by_severity[severity]
                print(f"\n{severity.upper()} ({len(findings_list)}):")
                print("-" * 50)
                
                for finding in findings_list[:10]:  # Показываем первые 10
                    checked = "✓" if finding['checked'] else "✗"
                    print(f"[{checked}] {finding['url']} ({finding['status_code']})")
                
                if len(findings_list) > 10:
                    print(f"... and {len(findings_list) - 10} more")
    
    def update_worker_threads(self):
        """Обновляет количество потоков воркера"""
        workers = self.master_core.get_workers()
        active_workers = [wid for wid, info in workers.items() if info.get("status") == "active"]
        
        if not active_workers:
            print("No active workers available!")
            return
        
        print("\nActive workers:")
        for i, worker_id in enumerate(active_workers, 1):
            print(f"{i}. {worker_id}")
        
        try:
            choice = int(input("Select worker: ")) - 1
            worker_id = active_workers[choice]
            
            threads = int(input("New thread count (1-100): "))
            if not 1 <= threads <= 100:
                print("Threads must be between 1 and 100!")
                return
            
            self.master_core.update_worker_threads(worker_id, threads)
            print(f"✅ Updated {worker_id} threads to {threads}")
            
        except (ValueError, IndexError):
            print("Invalid selection!")
    
    def export_findings(self):
        """Экспортирует находки"""
        print("\nExport format:")
        print("1. JSON")
        print("2. CSV")
        
        try:
            choice = int(input("Select format: "))
            format_type = "json" if choice == 1 else "csv"
            
            export_data = self.master_core.export_findings(format_type)
            
            filename = f"findings_export_{int(time.time())}.{format_type}"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(export_data)
            
            print(f"✅ Findings exported to {filename}")
            
        except (ValueError, IndexError):
            print("Invalid choice!")
        except Exception as e:
            print(f"❌ Export failed: {str(e)}")
    
    def security_summary(self):
        """Показывает сводку безопасности"""
        summary = self.master_core.get_security_summary()
        
        print("\n--- Security Summary ---")
        print(f"Total Findings: {summary['total_findings']}")
        print(f"Unchecked Findings: {summary['unchecked_count']}")
        
        print("\nFindings by Severity:")
        for severity, count in summary['severity_stats'].items():
            print(f"  {severity.upper()}: {count}")
        
        if summary['recent_critical']:
            print(f"\nRecent Critical Findings ({len(summary['recent_critical'])}):")
            for finding in summary['recent_critical'][:5]:
                print(f"  - {finding['url']}")
    
    def add_wordlist(self):
        """Добавляет новый словарь"""
        print("\n--- Add New Wordlist ---")
        
        name = input("Wordlist name: ").strip()
        if not name:
            print("Name is required!")
            return
        
        path = input("Wordlist file path: ").strip()
        if not path:
            print("Path is required!")
            return
        
        try:
            self.master_core.add_wordlist(name, path)
            print(f"✅ Wordlist '{name}' added successfully!")
        except Exception as e:
            print(f"❌ Failed to add wordlist: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='FFUF Master CLI Controller')
    parser.add_argument('--redis-host', default='localhost', help='Redis host')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis port')
    parser.add_argument('--redis-password', help='Redis password')
    parser.add_argument('--db-path', default='ffuf_master.db', help='Database path')
    
    args = parser.parse_args()
    
    try:
        config = {
            "redis_host": args.redis_host,
            "redis_port": args.redis_port,
            "redis_password": args.redis_password,
            "db_path": args.db_path
        }
        
        master_core = MasterCore(config)
        master_core.start()
        
        print("🚀 FFUF Master Controller started!")
        print("📊 Connected to Redis:", args.redis_host)
        
        cli = CLIController(master_core)
        cli.show_menu()
        
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"💥 Error: {str(e)}")
    finally:
        master_core.stop()

if __name__ == "__main__":
    main()
