import subprocess
import json
import tempfile
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class FFufWrapper:
    def __init__(self):
        self.ffuf_path = "ffuf"
        
    def run_ffuf(self, target: str, wordlist: str, options: Dict) -> Dict:
        """
        Запускает ffuf с указанными параметрами
        """
        cmd = [self.ffuf_path]
        
        # Базовые параметры
        cmd.extend(["-u", target])
        cmd.extend(["-w", wordlist])
        
        # Добавляем опции
        if options.get("method"):
            cmd.extend(["-X", options["method"]])
        
        if options.get("headers"):
            for header in options["headers"]:
                cmd.extend(["-H", header])
        
        if options.get("data"):
            cmd.extend([("-d", options["data"]))])
            
        if options.get("cookies"):
            cmd.extend([("-b", options["cookies"]))])
        
        # Критические параметры для JSON вывода
        cmd.extend(["-o", "-", "-of", "json"])
        
        # Управление потоками
        threads = options.get("threads", 10)
        cmd.extend([("-t", str(threads))])
        
        # Rate limiting
        if options.get("rate"):
            cmd.extend([("-rate", str(options["rate"]))])
        
        logger.info(f"Running ffuf command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=options.get("timeout", 7200)  # 2 часа по умолчанию
            )
            
            if result.returncode == 0:
                return self._parse_ffuf_output(result.stdout)
            else:
                logger.error(f"FFuf error: {result.stderr}")
                return {"error": result.stderr}
                
        except subprocess.TimeoutExpired:
            logger.error("FFuf execution timeout")
            return {"error": "timeout"}
        except Exception as e:
            logger.error(f"FFuf execution failed: {str(e)}")
            return {"error": str(e)}
    
    def _parse_ffuf_output(self, output: str) -> Dict:
        """
        Парсит JSON вывод ffuf
        """
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse FFuf JSON: {str(e)}")
            return {"error": "Invalid JSON output"}
    
    def validate_wordlist(self, wordlist_path: str) -> bool:
        """
        Проверяет доступность словаря
        """
        return os.path.exists(wordlist_path) and os.path.isfile(wordlist_path)
