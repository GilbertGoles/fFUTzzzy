import json
import csv
import io
from typing import List, Dict, Any

class Exporters:
    @staticmethod
    def export_to_json(data: List[Dict[str, Any]], indent: int = 2) -> str:
        """Экспортирует данные в JSON"""
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]]) -> str:
        """Экспортирует данные в CSV"""
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        headers = list(data[0].keys())
        writer.writerow(headers)
        
        # Данные
        for item in data:
            row = []
            for header in headers:
                value = item.get(header, "")
                if isinstance(value, (list, dict)):
                    value = str(value)
                row.append(value)
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_to_html(data: List[Dict[str, Any]]) -> str:
        """Экспортирует данные в HTML"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FFUF Scan Results</title>
            <style>
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .critical { background-color: #ffcccc; }
                .high { background-color: #ffebcc; }
                .medium { background-color: #ffffcc; }
                .low { background-color: #e6ffcc; }
            </style>
        </head>
        <body>
            <h1>FFUF Scan Results</h1>
            <table>
                <thead>
                    <tr>
        """
        
        if data:
            headers = list(data[0].keys())
            for header in headers:
                html += f"<th>{header}</th>"
            html += "</tr></thead><tbody>"
            
            for item in data:
                severity_class = item.get('severity', '').lower()
                html += f'<tr class="{severity_class}">'
                for header in headers:
                    value = item.get(header, "")
                    if isinstance(value, (list, dict)):
                        value = str(value)
                    html += f"<td>{value}</td>"
                html += "</tr>"
        
        html += "</tbody></table></body></html>"
        return html
