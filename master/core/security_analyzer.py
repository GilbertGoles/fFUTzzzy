import sqlite3
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SecurityAnalyzer:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по безопасности"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Статистика по критичности
                severity_stats = conn.execute('''
                    SELECT severity, COUNT(*) as count 
                    FROM findings 
                    GROUP BY severity
                ''').fetchall()
                
                # Непроверенные находки
                unchecked_count = conn.execute(
                    'SELECT COUNT(*) FROM findings WHERE checked = FALSE'
                ).fetchone()[0]
                
                # Последние критические находки
                critical_findings = conn.execute('''
                    SELECT * FROM findings 
                    WHERE severity = 'critical' 
                    ORDER BY created_at DESC 
                    LIMIT 10
                ''').fetchall()
                
                return {
                    "severity_stats": {row["severity"]: row["count"] for row in severity_stats},
                    "unchecked_count": unchecked_count,
                    "total_findings": sum(row["count"] for row in severity_stats),
                    "recent_critical": [dict(row) for row in critical_findings]
                }
        except sqlite3.Error as e:
            logger.error(f"Database error in get_security_summary: {e}")
            return {
                "severity_stats": {},
                "unchecked_count": 0,
                "total_findings": 0,
                "recent_critical": [],
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in get_security_summary: {e}")
            return {
                "severity_stats": {},
                "unchecked_count": 0,
                "total_findings": 0,
                "recent_critical": [],
                "error": str(e)
            }
    
    def export_findings(self, format_type: str = "json", task_id: str = None) -> str:
        """Экспортирует находки в указанном формате"""
        try:
            findings = self.db.get_findings(task_id=task_id)
            
            if format_type == "json":
                return self._export_json(findings)
            elif format_type == "csv":
                return self._export_csv(findings)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
        except Exception as e:
            logger.error(f"Error exporting findings: {e}")
            raise
    
    def _export_json(self, findings: List[Dict[str, Any]]) -> str:
        """Экспортирует в JSON"""
        try:
            import json
            return json.dumps(findings, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise
    
    def _export_csv(self, findings: List[Dict[str, Any]]) -> str:
        """Экспортирует в CSV"""
        try:
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Заголовки
            writer.writerow([
                'URL', 'Status Code', 'Content Length', 'Severity', 
                'Detected Issues', 'Checked', 'Created At'
            ])
            
            # Данные
            for finding in findings:
                writer.writerow([
                    finding['url'],
                    finding['status_code'],
                    finding['content_length'],
                    finding['severity'],
                    '; '.join(finding['detected_issues']),
                    'Yes' if finding['checked'] else 'No',
                    finding['created_at']
                ])
            
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
