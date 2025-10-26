import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
import time
import uuid
import json
import os
import sys

# Добавляем родительскую директорию в путь Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Теперь импортируем абсолютным путем
from core.master_core import MasterCore

logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self, master_core: MasterCore):
        self.master_core = master_core
        self.root = tk.Tk()
        self.root.title("FFUF Master Controller")
        self.root.geometry("1400x900")
        
        # Стили
        self.setup_styles()
        
        # Основной интерфейс
        self.setup_ui()
        
        # Обновление данных
        self.setup_data_refresh()
    
    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цвета для критичности
        style.configure("Critical.TLabel", foreground="red", font=('Arial', 9, 'bold'))
        style.configure("High.TLabel", foreground="orange", font=('Arial', 9, 'bold'))
        style.configure("Medium.TLabel", foreground="yellow", font=('Arial', 9))
        style.configure("Low.TLabel", foreground="green", font=('Arial', 9))
        style.configure("Info.TLabel", foreground="blue", font=('Arial', 9))
    
    def setup_ui(self):
        """Настройка основного интерфейса"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Создаем вкладки
        self.setup_dashboard_tab()
        self.setup_scan_tab()
        self.setup_findings_tab()
        self.setup_workers_tab()
        self.setup_tasks_tab()
        
        # Статус бар
        self.setup_status_bar()
    
    def setup_dashboard_tab(self):
        """Вкладка дашборда"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Верхняя панель с общей статистикой
        stats_frame = ttk.LabelFrame(dashboard_frame, text="Overall Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Статистика
        self.stats_labels = {}
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        stats_data = [
            ("Total Tasks", "total_tasks"),
            ("Active Workers", "active_workers"),
            ("Total Findings", "total_findings"),
            ("Critical Findings", "critical_findings"),
            ("Unchecked Findings", "unchecked_findings")
        ]
        
        for i, (label, key) in enumerate(stats_data):
            frame = ttk.Frame(stats_grid)
            frame.grid(row=0, column=i, padx=20, pady=10, sticky=tk.W)
            
            ttk.Label(frame, text=label, font=('Arial', 10)).pack()
            self.stats_labels[key] = ttk.Label(frame, text="0", font=('Arial', 14, 'bold'))
            self.stats_labels[key].pack()
        
        # График распределения по критичности
        severity_frame = ttk.LabelFrame(dashboard_frame, text="Findings by Severity", padding=10)
        severity_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.severity_tree = ttk.Treeview(severity_frame, columns=("count",), show="tree headings", height=5)
        self.severity_tree.heading("#0", text="Severity")
        self.severity_tree.heading("count", text="Count")
        self.severity_tree.pack(fill=tk.BOTH, expand=True)
        
        # Последние критические находки
        critical_frame = ttk.LabelFrame(dashboard_frame, text="Recent Critical Findings", padding=10)
        critical_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("url", "status_code", "created_at")
        self.critical_tree = ttk.Treeview(critical_frame, columns=columns, show="headings", height=8)
        
        self.critical_tree.heading("url", text="URL")
        self.critical_tree.heading("status_code", text="Status")
        self.critical_tree.heading("created_at", text="Found At")
        
        self.critical_tree.column("url", width=400)
        self.critical_tree.column("status_code", width=80)
        self.critical_tree.column("created_at", width=150)
        
        self.critical_tree.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки быстрых действий
        action_frame = ttk.Frame(dashboard_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(action_frame, text="Quick Scan", 
                  command=self.quick_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Export All Findings", 
                  command=self.export_all_findings).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Refresh All", 
                  command=self.refresh_all_data).pack(side=tk.LEFT, padx=5)
    
    def setup_scan_tab(self):
        """Вкладка создания сканирования"""
        scan_frame = ttk.Frame(self.notebook)
        self.notebook.add(scan_frame, text="New Scan")
        
        # Конфигурация сканирования
        config_frame = ttk.LabelFrame(scan_frame, text="Scan Configuration", padding=15)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Цель
        ttk.Label(config_frame, text="Target URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.target_var = tk.StringVar(value="https://example.com/FUZZ")
        target_entry = ttk.Entry(config_frame, textvariable=self.target_var, width=60)
        target_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        
        # Словарь
        ttk.Label(config_frame, text="Wordlist:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.wordlist_var = tk.StringVar()
        wordlists = list(self.master_core.get_wordlists().keys())
        self.wordlist_combo = ttk.Combobox(config_frame, textvariable=self.wordlist_var, 
                                          values=wordlists, state="readonly", width=57)
        self.wordlist_combo.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        if wordlists:
            self.wordlist_combo.set(wordlists[0])
        
        # Дополнительные опции
        options_frame = ttk.LabelFrame(config_frame, text="Advanced Options", padding=10)
        options_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W+tk.E, pady=10)
        
        # Метод HTTP
        ttk.Label(options_frame, text="HTTP Method:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.method_var = tk.StringVar(value="GET")
        method_combo = ttk.Combobox(options_frame, textvariable=self.method_var,
                                   values=["GET", "POST", "PUT", "DELETE", "HEAD"], width=10)
        method_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Рекурсивное сканирование
        self.recursive_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Recursive", 
                       variable=self.recursive_var).grid(row=0, column=2, sticky=tk.W, padx=20)
        
        # Следовать редиректам
        self.follow_redirects_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Follow Redirects", 
                       variable=self.follow_redirects_var).grid(row=0, column=3, sticky=tk.W)
        
        # Заголовки
        ttk.Label(options_frame, text="Custom Headers:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.headers_text = tk.Text(options_frame, width=50, height=3)
        self.headers_text.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=2, padx=5)
        
        # Выбор воркеров
        workers_frame = ttk.LabelFrame(scan_frame, text="Worker Selection", padding=15)
        workers_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.worker_vars = {}
        workers = self.master_core.get_workers()
        
        worker_selection_frame = ttk.Frame(workers_frame)
        worker_selection_frame.pack(fill=tk.X)
        
        ttk.Button(worker_selection_frame, text="Select All", 
                  command=self.select_all_workers).pack(side=tk.LEFT, padx=5)
        ttk.Button(worker_selection_frame, text="Deselect All", 
                  command=self.deselect_all_workers).pack(side=tk.LEFT, padx=5)
        
        # Сетка воркеров
        workers_grid = ttk.Frame(workers_frame)
        workers_grid.pack(fill=tk.X, pady=10)
        
        row, col = 0, 0
        for worker_id in workers.keys():
            var = tk.BooleanVar(value=True)
            self.worker_vars[worker_id] = var
            
            cb = ttk.Checkbutton(workers_grid, text=worker_id, variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
            
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        # Кнопка запуска
        action_frame = ttk.Frame(scan_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(action_frame, text="Start Scan", 
                  command=self.start_scan).pack(pady=10)
    
    def setup_findings_tab(self):
        """Вкладка просмотра находок"""
        findings_frame = ttk.Frame(self.notebook)
        self.notebook.add(findings_frame, text="Findings")
        
        # Панель управления
        control_frame = ttk.Frame(findings_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Фильтры
        ttk.Label(control_frame, text="Filter by:").pack(side=tk.LEFT, padx=5)
        
        self.severity_filter_var = tk.StringVar(value="all")
        severity_combo = ttk.Combobox(control_frame, textvariable=self.severity_filter_var,
                                     values=["all", "critical", "high", "medium", "low", "info"],
                                     state="readonly", width=10)
        severity_combo.pack(side=tk.LEFT, padx=5)
        
        self.checked_filter_var = tk.StringVar(value="all")
        checked_combo = ttk.Combobox(control_frame, textvariable=self.checked_filter_var,
                                    values=["all", "checked", "unchecked"],
                                    state="readonly", width=10)
        checked_combo.pack(side=tk.LEFT, padx=5)
        
        # Кнопки
        ttk.Button(control_frame, text="Apply Filters", 
                  command=self.apply_findings_filters).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Export Selected", 
                  command=self.export_selected_findings).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Mark as Checked", 
                  command=self.mark_selected_checked).pack(side=tk.LEFT, padx=5)
        
        # Таблица находок
        columns = ("finding_id", "url", "status_code", "content_length", "severity", 
                  "checked", "created_at", "task_id")
        
        self.findings_tree = ttk.Treeview(findings_frame, columns=columns, show="headings", height=20)
        
        # Заголовки
        headings = {
            "finding_id": "ID",
            "url": "URL",
            "status_code": "Status",
            "content_length": "Size",
            "severity": "Severity",
            "checked": "Checked",
            "created_at": "Found At",
            "task_id": "Task ID"
        }
        
        for col, text in headings.items():
            self.findings_tree.heading(col, text=text)
        
        # Ширина колонок
        self.findings_tree.column("finding_id", width=80)
        self.findings_tree.column("url", width=400)
        self.findings_tree.column("status_code", width=60)
        self.findings_tree.column("content_length", width=80)
        self.findings_tree.column("severity", width=80)
        self.findings_tree.column("checked", width=60)
        self.findings_tree.column("created_at", width=120)
        self.findings_tree.column("task_id", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(findings_frame, orient=tk.VERTICAL, command=self.findings_tree.yview)
        self.findings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.findings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Двойной клик для деталей
        self.findings_tree.bind("<Double-1>", self.show_finding_details)
    
    def setup_workers_tab(self):
        """Вкладка управления воркерами"""
        workers_frame = ttk.Frame(self.notebook)
        self.notebook.add(workers_frame, text="Workers")
        
        # Таблица воркеров
        columns = ("worker_id", "status", "hostname", "threads", "current_task", "last_seen", "tasks_completed")
        self.workers_tree = ttk.Treeview(workers_frame, columns=columns, show="headings", height=15)
        
        headings = {
            "worker_id": "Worker ID",
            "status": "Status",
            "hostname": "Hostname",
            "threads": "Threads",
            "current_task": "Current Task",
            "last_seen": "Last Seen",
            "tasks_completed": "Tasks Completed"
        }
        
        for col, text in headings.items():
            self.workers_tree.heading(col, text=text)
        
        # Ширина колонок
        self.workers_tree.column("worker_id", width=120)
        self.workers_tree.column("status", width=80)
        self.workers_tree.column("hostname", width=150)
        self.workers_tree.column("threads", width=80)
        self.workers_tree.column("current_task", width=120)
        self.workers_tree.column("last_seen", width=120)
        self.workers_tree.column("tasks_completed", width=100)
        
        # Панель управления воркерами
        control_frame = ttk.Frame(workers_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Threads:").pack(side=tk.LEFT, padx=5)
        self.threads_var = tk.IntVar(value=10)
        threads_spinbox = ttk.Spinbox(control_frame, from_=1, to=100, 
                                     textvariable=self.threads_var, width=5)
        threads_spinbox.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Update Selected Worker", 
                  command=self.update_worker_threads).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Refresh Workers", 
                  command=self.refresh_workers).pack(side=tk.LEFT, padx=5)
        
        self.workers_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_tasks_tab(self):
        """Вкладка просмотра задач"""
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text="Tasks")
        
        # Таблица задач
        columns = ("task_id", "target", "wordlist_name", "status", "progress", 
                  "findings_count", "created_at", "completed_at")
        
        self.tasks_tree = ttk.Treeview(tasks_frame, columns=columns, show="headings", height=15)
        
        headings = {
            "task_id": "Task ID",
            "target": "Target",
            "wordlist_name": "Wordlist",
            "status": "Status",
            "progress": "Progress",
            "findings_count": "Findings",
            "created_at": "Created",
            "completed_at": "Completed"
        }
        
        for col, text in headings.items():
            self.tasks_tree.heading(col, text=text)
        
        # Ширина колонок
        self.tasks_tree.column("task_id", width=100)
        self.tasks_tree.column("target", width=250)
        self.tasks_tree.column("wordlist_name", width=120)
        self.tasks_tree.column("status", width=80)
        self.tasks_tree.column("progress", width=80)
        self.tasks_tree.column("findings_count", width=80)
        self.tasks_tree.column("created_at", width=120)
        self.tasks_tree.column("completed_at", width=120)
        
        self.tasks_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_status_bar(self):
        """Настройка статус бара"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.pack(fill=tk.X, padx=2, pady=2)
    
    def setup_data_refresh(self):
        """Настройка автоматического обновления данных"""
        def refresh_loop():
            while True:
                try:
                    self.root.after(0, self.refresh_all_data)
                except Exception as e:
                    logger.error(f"Refresh error: {str(e)}")
                time.sleep(30)  # Ждем 30 секунд
        
        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()
    
    # Методы бизнес-логики
    def start_scan(self):
        """Запускает новое сканирование"""
        try:
            target = self.target_var.get().strip()
            wordlist = self.wordlist_var.get()
            
            if not target:
                messagebox.showerror("Error", "Please enter target URL")
                return
            
            if not wordlist:
                messagebox.showerror("Error", "Please select wordlist")
                return
            
            # Выбранные воркеры
            selected_workers = [wid for wid, var in self.worker_vars.items() if var.get()]
            
            if not selected_workers:
                messagebox.showerror("Error", "Please select at least one worker")
                return
            
            # Опции сканирования
            options = {
                "method": self.method_var.get(),
                "recursive": self.recursive_var.get(),
                "follow_redirects": self.follow_redirects_var.get(),
            }
            
            # Заголовки
            headers_text = self.headers_text.get("1.0", tk.END).strip()
            if headers_text:
                options["headers"] = [h.strip() for h in headers_text.split('\n') if h.strip()]
            
            # Создаем задачу
            task_id = self.master_core.create_scan_task(
                target=target,
                wordlist_name=wordlist,
                worker_ids=selected_workers,
                options=options
            )
            
            messagebox.showinfo("Success", f"Scan started with task ID: {task_id}")
            self.status_var.set(f"Scan started: {task_id}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start scan: {str(e)}")
            logger.error(f"Scan start error: {str(e)}")
    
    def refresh_all_data(self):
        """Обновляет все данные в интерфейсе"""
        try:
            self.refresh_dashboard()
            self.refresh_findings()
            self.refresh_workers()
            self.refresh_tasks()
            self.status_var.set("Data refreshed")
        except Exception as e:
            logger.error(f"Refresh error: {str(e)}")
            self.status_var.set("Refresh failed")
    
    def refresh_dashboard(self):
        """Обновляет дашборд"""
        try:
            summary = self.master_core.get_security_summary()
            
            # Общая статистика
            self.stats_labels["total_findings"].config(text=summary["total_findings"])
            self.stats_labels["critical_findings"].config(
                text=summary["severity_stats"].get("critical", 0)
            )
            self.stats_labels["unchecked_findings"].config(text=summary["unchecked_count"])
            
            # Распределение по критичности
            self.severity_tree.delete(*self.severity_tree.get_children())
            for severity, count in summary["severity_stats"].items():
                self.severity_tree.insert("", tk.END, text=severity.upper(), values=(count,))
            
            # Критические находки
            self.critical_tree.delete(*self.critical_tree.get_children())
            for finding in summary["recent_critical"]:
                self.critical_tree.insert("", tk.END, values=(
                    finding["url"],
                    finding["status_code"],
                    finding["created_at"]
                ))
                
        except Exception as e:
            logger.error(f"Dashboard refresh error: {str(e)}")
    
    def refresh_findings(self):
        """Обновляет список находок"""
        try:
            # Применяем фильтры
            severity = self.severity_filter_var.get()
            checked = self.checked_filter_var.get()
            
            findings = self.master_core.get_findings()
            
            # Фильтрация
            filtered_findings = []
            for finding in findings:
                if severity != "all" and finding["severity"] != severity:
                    continue
                if checked == "checked" and not finding["checked"]:
                    continue
                if checked == "unchecked" and finding["checked"]:
                    continue
                filtered_findings.append(finding)
            
            # Обновление таблицы
            self.findings_tree.delete(*self.findings_tree.get_children())
            for finding in filtered_findings:
                self.findings_tree.insert("", tk.END, values=(
                    finding["finding_id"],
                    finding["url"],
                    finding["status_code"],
                    finding["content_length"],
                    finding["severity"],
                    "Yes" if finding["checked"] else "No",
                    finding["created_at"],
                    finding["task_id"]
                ))
                
        except Exception as e:
            logger.error(f"Findings refresh error: {str(e)}")
    
    def refresh_workers(self):
        """Обновляет список воркеров"""
        try:
            workers = self.master_core.get_workers()
            
            self.workers_tree.delete(*self.workers_tree.get_children())
            for worker_id, info in workers.items():
                self.workers_tree.insert("", tk.END, values=(
                    worker_id,
                    info.get("status", "unknown"),
                    info.get("hostname", "unknown"),
                    info.get("threads", 0),
                    info.get("current_task", ""),
                    info.get("last_seen", ""),
                    info.get("tasks_completed", 0)
                ))
                
        except Exception as e:
            logger.error(f"Workers refresh error: {str(e)}")
    
    def refresh_tasks(self):
        """Обновляет список задач"""
        try:
            tasks = self.master_core.get_tasks()
            
            self.tasks_tree.delete(*self.tasks_tree.get_children())
            for task in tasks:
                self.tasks_tree.insert("", tk.END, values=(
                    task["task_id"],
                    task["target"],
                    task["wordlist_name"],
                    task["status"],
                    f"{task['progress']}%",
                    task["findings_count"],
                    task["created_at"],
                    task.get("completed_at", "")
                ))
                
        except Exception as e:
            logger.error(f"Tasks refresh error: {str(e)}")
    
    def apply_findings_filters(self):
        """Применяет фильтры к находкам"""
        self.refresh_findings()
    
    def export_selected_findings(self):
        """Экспортирует выбранные находки"""
        try:
            selected = self.findings_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select findings to export")
                return
            
            format_type = messagebox.askquestion("Export Format", 
                                               "Export as JSON?", 
                                               icon='question')
            format_type = "json" if format_type == "yes" else "csv"
            
            # В реальной реализации здесь должна быть логика экспорта выбранных записей
            export_data = self.master_core.export_findings(format_type)
            
            # Сохраняем в файл
            filename = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=[(f"{format_type.upper()} files", f"*.{format_type}")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(export_data)
                
                messagebox.showinfo("Success", f"Findings exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def mark_selected_checked(self):
        """Отмечает выбранные находки как проверенные"""
        try:
            selected = self.findings_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select findings to mark")
                return
            
            for item in selected:
                finding_id = self.findings_tree.item(item)["values"][0]
                self.master_core.mark_finding_checked(finding_id, True)
            
            messagebox.showinfo("Success", f"Marked {len(selected)} findings as checked")
            self.refresh_findings()
            
        except Exception as e:
            messagebox.showerror("Error", f"Marking failed: {str(e)}")
    
    def update_worker_threads(self):
        """Обновляет количество потоков выбранного воркера"""
        try:
            selected = self.workers_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a worker")
                return
            
            worker_id = self.workers_tree.item(selected[0])["values"][0]
            threads = self.threads_var.get()
            
            self.master_core.update_worker_threads(worker_id, threads)
            messagebox.showinfo("Success", f"Updated {worker_id} threads to {threads}")
            self.refresh_workers()
            
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {str(e)}")
    
    def show_finding_details(self, event):
        """Показывает детали находки"""
        try:
            selected = self.findings_tree.selection()
            if not selected:
                return
            
            item = selected[0]
            values = self.findings_tree.item(item)["values"]
            finding_id = values[0]
            
            # Создаем окно с деталями
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Finding Details - {finding_id}")
            details_window.geometry("800x600")
            
            # Основной фрейм
            main_frame = ttk.Frame(details_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Информация о находке
            info_frame = ttk.LabelFrame(main_frame, text="Finding Information", padding="10")
            info_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(info_frame, text=f"URL: {values[1]}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Status Code: {values[2]}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Content Length: {values[3]}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Severity: {values[4]}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Checked: {values[5]}").pack(anchor=tk.W)
            
            # Детальный просмотр
            details_frame = ttk.LabelFrame(main_frame, text="Raw Response", padding="10")
            details_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            details_text = tk.Text(details_frame, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=details_text.yview)
            details_text.configure(yscrollcommand=scrollbar.set)
            
            # Здесь можно добавить логику для получения полного ответа
            details_text.insert(tk.END, "Full HTTP response would be displayed here...")
            
            details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Кнопки
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(button_frame, text="Mark as Checked", 
                      command=lambda: self.mark_finding_and_close(finding_id, details_window)).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", 
                      command=details_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            logger.error(f"Error showing details: {str(e)}")
            messagebox.showerror("Error", f"Failed to show details: {str(e)}")
    
    def mark_finding_and_close(self, finding_id: str, window: tk.Toplevel):
        """Отмечает находку и закрывает окно"""
        try:
            self.master_core.mark_finding_checked(finding_id, True)
            self.refresh_findings()
            window.destroy()
            messagebox.showinfo("Success", "Finding marked as checked")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark finding: {str(e)}")
    
    def select_all_workers(self):
        """Выбирает всех воркеров"""
        for var in self.worker_vars.values():
            var.set(True)
    
    def deselect_all_workers(self):
        """Снимает выбор со всех воркеров"""
        for var in self.worker_vars.values():
            var.set(False)
    
    def quick_scan(self):
        """Быстрое сканирование с настройками по умолчанию"""
        self.notebook.select(1)  # Переключаем на вкладку сканирования
    
    def export_all_findings(self):
        """Экспортирует все находки"""
        try:
            format_type = messagebox.askquestion("Export Format", 
                                               "Export as JSON?", 
                                               icon='question')
            format_type = "json" if format_type == "yes" else "csv"
            
            export_data = self.master_core.export_findings(format_type)
            
            filename = filedialog.asksaveasfilename(
                defaultextension=f".{format_type}",
                filetypes=[(f"{format_type.upper()} files", f"*.{format_type}")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(export_data)
                
                messagebox.showinfo("Success", f"All findings exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def run(self):
        """Запускает главный цикл"""
        try:
            # Первоначальное обновление данных
            self.refresh_all_data()
            self.root.mainloop()
        except KeyboardInterrupt:
            self.master_core.stop()
        except Exception as e:
            logger.error(f"GUI error: {str(e)}")
            self.master_core.stop()
