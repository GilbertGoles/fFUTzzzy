import json
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class ResultParser:
    def __init__(self):
        self.suspicious_patterns = [
            (r"(password|pwd|pass|key|secret|token)", "high"),
            (r"(backup|dump|archive|old)", "medium"),
            (r"(admin|login|auth|dashboard)", "medium"),
            (r"(config|configuration|setting)", "high"),
            (r"(\.git|\.env|\.bak|\.old)", "critical"),
            (r"(phpinfo|test|debug)", "medium"),
        ]
        
        self.error_patterns = [
            (r"sql.*syntax", "high"),
            (r"database.*error", "medium"),
            (r"undefined.*variable", "low"),
            (r"stack.*trace", "medium"),
        ]
    
    def parse_ffuf_results(self, task_id: str, ffuf_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Парсит результаты ffuf и извлекает security findings
        """
        findings = []
        
        if not ffuf_results or "results" not in ffuf_results:
            return findings
        
        for result in ffuf_results["results"]:
            finding = self._analyze_result(task_id, result)
            if finding:
                findings.append(finding)
        
        logger.info(f"Parsed {len(findings)} findings from task {task_id}")
        return findings
    
    def _analyze_result(self, task_id: str, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Анализирует отдельный результат ffuf
        """
        url = result.get("url", "")
        status = result.get("status", 0)
        length = result.get("length", 0)
        words = result.get("words", 0)
        lines = result.get("lines", 0)
        
        # Пропускаем 404 и подобные
        if status in [404, 400, 500]:
            return None
        
        detected_issues = []
        severity = "low"
        
        # Анализ URL
        url_issues = self._analyze_url(url)
        detected_issues.extend(url_issues)
        
        # Анализ кода ответа
        status_issues = self._analyze_status_code(status)
        detected_issues.extend(status_issues)
        
        # Анализ длины контента
        length_issues = self._analyze_content_length(length)
        detected_issues.extend(length_issues)
        
        # Определяем общую критичность
        if any("critical" in issue.lower() for issue in detected_issues):
            severity = "critical"
        elif any("high" in issue.lower() for issue in detected_issues):
            severity = "high"
        elif any("medium" in issue.lower() for issue in detected_issues):
            severity = "medium"
        elif detected_issues:
            severity = "low"
        else:
            # Если нет особых находок, но статус интересный
            if status in [200, 301, 302, 403]:
                detected_issues.append(f"Interesting status code: {status}")
                severity = "info"
            else:
                return None
        
        return {
            "finding_id": f"finding_{task_id}_{hash(url) % 10**8}",
            "task_id": task_id,
            "url": url,
            "status_code": status,
            "content_length": length,
            "words": words,
            "lines": lines,
            "severity": severity,
            "detected_issues": detected_issues,
            "raw_response": json.dumps(result, indent=2)
        }
    
    def _analyze_url(self, url: str) -> List[str]:
        """Анализирует URL на подозрительные паттерны"""
        issues = []
        
        for pattern, level in self.suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                issues.append(f"{level.upper()}: Suspicious pattern in URL: {pattern}")
        
        # Проверяем расширения файлов
        path = urlparse(url).path
        if any(path.endswith(ext) for ext in ['.git', '.env', '.bak', '.old', '.tar', '.zip']):
            issues.append("CRITICAL: Sensitive file extension detected")
        
        return issues
    
    def _analyze_status_code(self, status_code: int) -> List[str]:
        """Анализирует код ответа"""
        issues = []
        
        if status_code == 200:
            issues.append("Valid resource found")
        elif status_code == 301 or status_code == 302:
            issues.append("Redirect found")
        elif status_code == 403:
            issues.append("Access forbidden - possible privilege escalation")
        elif status_code == 500:
            issues.append("Server error - possible vulnerability")
        
        return issues
    
    def _analyze_content_length(self, length: int) -> List[str]:
        """Анализирует длину контента"""
        issues = []
        
        if length == 0:
            issues.append("Empty response")
        elif length > 1000000:  # 1MB
            issues.append("Large response - possible data exposure")
        elif length < 100:
            issues.append("Very small response - possible error page")
        
        return issues
