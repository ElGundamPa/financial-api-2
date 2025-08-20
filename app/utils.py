import time
import base64
import json
from typing import Optional, Any
from datetime import datetime, timedelta

def pct_change(text: str) -> Optional[float]:
    """Parsear cambio porcentual de texto"""
    if not text:
        return None
    
    # Limpiar texto
    text = text.strip().replace(',', '').replace('%', '')
    
    # Manejar paréntesis (valores negativos)
    if '(' in text and ')' in text:
        text = text.replace('(', '').replace(')', '')
        try:
            return -float(text)
        except ValueError:
            return None
    
    # Buscar patrones de cambio porcentual
    import re
    patterns = [
        r'([+-]?\d+\.?\d*)%',  # 1.23% o +1.23% o -1.23%
        r'([+-]?\d+\.?\d*)',   # 1.23 o +1.23 o -1.23
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    return None

def encode_cursor(data: dict[str, Any]) -> str:
    """Codificar cursor para paginación"""
    json_str = json.dumps(data, separators=(',', ':'))
    return base64.urlsafe_b64encode(json_str.encode()).decode()

def decode_cursor(cursor: str) -> Optional[dict[str, Any]]:
    """Decodificar cursor para paginación"""
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        return json.loads(json_str)
    except Exception:
        return None

def format_latency(start_time: float) -> float:
    """Formatear latencia en milisegundos"""
    return round((time.time() - start_time) * 1000, 2)

def get_user_agent() -> str:
    """Obtener User-Agent rotativo"""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    return agents[int(time.time()) % len(agents)]

def get_headers() -> dict[str, str]:
    """Obtener headers HTTP estándar"""
    return {
        "User-Agent": get_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

def parse_number(text: str) -> Optional[float]:
    """Parsear número de texto, manejando formatos comunes"""
    if not text:
        return None
    
    # Limpiar texto
    text = text.strip().replace(',', '').replace('%', '')
    
    # Manejar paréntesis (valores negativos)
    if '(' in text and ')' in text:
        text = text.replace('(', '').replace(')', '')
        try:
            return -float(text)
        except ValueError:
            return None
    
    try:
        return float(text)
    except ValueError:
        return None

def safe_float(value: Any) -> Optional[float]:
    """Convertir valor a float de forma segura"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
