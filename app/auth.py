#!/usr/bin/env python3
"""
Sistema de autenticación con API keys para la API financiera
"""
import os
import hashlib
import secrets
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from flask import request, jsonify
from functools import wraps

class APIKeyManager:
    """Gestor de API keys"""
    
    def __init__(self):
        # API keys desde variables de entorno
        self.api_keys = self._load_api_keys()
        self.rate_limits = {}  # rate limiting per API key
        
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Cargar API keys desde variables de entorno"""
        keys = {}
        
        # API keys desde variable de entorno
        env_keys = os.getenv('API_KEYS', '')
        if env_keys:
            for key_info in env_keys.split(','):
                key_info = key_info.strip()
                if '|' in key_info:
                    # Formato: key|name|rate_limit
                    parts = key_info.split('|')
                    api_key = parts[0].strip()
                    name = parts[1].strip() if len(parts) > 1 else "Unknown"
                    rate_limit = int(parts[2].strip()) if len(parts) > 2 else 100
                else:
                    # Solo la key
                    api_key = key_info
                    name = "Unknown"
                    rate_limit = 100
                
                keys[api_key] = {
                    "name": name,
                    "rate_limit": rate_limit,  # requests per hour
                    "created_at": datetime.now(),
                    "last_used": None,
                    "total_requests": 0
                }
        
        # Si no hay keys definidas, crear una por defecto
        if not keys:
            default_key = os.getenv('DEFAULT_API_KEY', 'demo_key_12345')
            keys[default_key] = {
                "name": "Default Demo Key",
                "rate_limit": 50,  # Límite bajo para demo
                "created_at": datetime.now(),
                "last_used": None,
                "total_requests": 0
            }
        
        return keys
    
    def validate_api_key(self, api_key: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Validar API key"""
        if not api_key:
            return False, {"error": "API key required"}
        
        if api_key not in self.api_keys:
            return False, {"error": "Invalid API key"}
        
        key_info = self.api_keys[api_key]
        
        # Verificar rate limiting
        if not self._check_rate_limit(api_key):
            return False, {
                "error": "Rate limit exceeded",
                "rate_limit": key_info["rate_limit"],
                "reset_time": self._get_reset_time(api_key)
            }
        
        # Actualizar estadísticas
        key_info["last_used"] = datetime.now()
        key_info["total_requests"] += 1
        
        return True, key_info
    
    def _check_rate_limit(self, api_key: str) -> bool:
        """Verificar rate limiting"""
        key_info = self.api_keys[api_key]
        rate_limit = key_info["rate_limit"]
        
        current_time = time.time()
        hour_ago = current_time - 3600  # 1 hora atrás
        
        # Inicializar si es la primera vez
        if api_key not in self.rate_limits:
            self.rate_limits[api_key] = []
        
        # Limpiar requests antiguos (más de 1 hora)
        self.rate_limits[api_key] = [
            req_time for req_time in self.rate_limits[api_key]
            if req_time > hour_ago
        ]
        
        # Verificar si se excede el límite
        if len(self.rate_limits[api_key]) >= rate_limit:
            return False
        
        # Añadir request actual
        self.rate_limits[api_key].append(current_time)
        return True
    
    def _get_reset_time(self, api_key: str) -> str:
        """Obtener tiempo de reset del rate limit"""
        if api_key not in self.rate_limits or not self.rate_limits[api_key]:
            return datetime.now().isoformat()
        
        oldest_request = min(self.rate_limits[api_key])
        reset_time = datetime.fromtimestamp(oldest_request + 3600)
        return reset_time.isoformat()
    
    def get_key_stats(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de una API key"""
        if api_key not in self.api_keys:
            return None
        
        key_info = self.api_keys[api_key].copy()
        
        # Añadir estadísticas de rate limiting
        current_requests = len(self.rate_limits.get(api_key, []))
        key_info["current_hour_requests"] = current_requests
        key_info["remaining_requests"] = max(0, key_info["rate_limit"] - current_requests)
        key_info["reset_time"] = self._get_reset_time(api_key)
        
        return key_info
    
    def generate_api_key(self, name: str = "Generated", rate_limit: int = 100) -> str:
        """Generar una nueva API key"""
        # Generar key segura
        api_key = f"fapi_{secrets.token_urlsafe(32)}"
        
        self.api_keys[api_key] = {
            "name": name,
            "rate_limit": rate_limit,
            "created_at": datetime.now(),
            "last_used": None,
            "total_requests": 0
        }
        
        return api_key

# Instancia global
api_key_manager = APIKeyManager()

def require_api_key(f):
    """Decorador para requerir API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener API key de diferentes fuentes
        api_key = (
            request.headers.get('X-API-Key') or
            request.headers.get('Authorization', '').replace('Bearer ', '') or
            request.args.get('api_key') or
            request.args.get('key')
        )
        
        # Validar API key
        is_valid, result = api_key_manager.validate_api_key(api_key)
        
        if not is_valid:
            return jsonify({
                "error": "Authentication failed",
                "details": result,
                "timestamp": datetime.now().isoformat()
            }), 401
        
        # Añadir información de la key al request
        request.api_key_info = result
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_api_key(f):
    """Decorador para API key opcional (con rate limiting diferente)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener API key si está presente
        api_key = (
            request.headers.get('X-API-Key') or
            request.headers.get('Authorization', '').replace('Bearer ', '') or
            request.args.get('api_key') or
            request.args.get('key')
        )
        
        if api_key:
            # Validar API key si está presente
            is_valid, result = api_key_manager.validate_api_key(api_key)
            
            if not is_valid:
                return jsonify({
                    "error": "Invalid API key",
                    "details": result,
                    "timestamp": datetime.now().isoformat()
                }), 401
            
            request.api_key_info = result
        else:
            # Sin API key - aplicar rate limiting más estricto por IP
            if not _check_ip_rate_limit():
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": "Please provide an API key for higher rate limits",
                    "timestamp": datetime.now().isoformat()
                }), 429
            
            request.api_key_info = {
                "name": "Anonymous",
                "rate_limit": 10,  # Muy limitado sin API key
                "is_anonymous": True
            }
        
        return f(*args, **kwargs)
    
    return decorated_function

# Rate limiting por IP (para usuarios sin API key)
ip_rate_limits = {}

def _check_ip_rate_limit(requests_per_hour: int = 10) -> bool:
    """Verificar rate limiting por IP"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    current_time = time.time()
    hour_ago = current_time - 3600
    
    # Inicializar si es la primera vez
    if client_ip not in ip_rate_limits:
        ip_rate_limits[client_ip] = []
    
    # Limpiar requests antiguos
    ip_rate_limits[client_ip] = [
        req_time for req_time in ip_rate_limits[client_ip]
        if req_time > hour_ago
    ]
    
    # Verificar límite
    if len(ip_rate_limits[client_ip]) >= requests_per_hour:
        return False
    
    # Añadir request actual
    ip_rate_limits[client_ip].append(current_time)
    return True

class AuthMiddleware:
    """Middleware de autenticación para Flask"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar middleware con la app Flask"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Procesar request antes de llegar al endpoint"""
        # Añadir headers CORS
        if request.method == "OPTIONS":
            return self._make_cors_preflight_response()
        
        # Log de request
        print(f"📥 {request.method} {request.path} - IP: {request.remote_addr}")
    
    def after_request(self, response):
        """Procesar response después del endpoint"""
        # Añadir headers CORS
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key, Authorization'
        
        # Añadir headers de rate limiting si hay info de API key
        if hasattr(request, 'api_key_info') and not request.api_key_info.get('is_anonymous'):
            api_key = (
                request.headers.get('X-API-Key') or
                request.headers.get('Authorization', '').replace('Bearer ', '') or
                request.args.get('api_key') or
                request.args.get('key')
            )
            
            if api_key:
                stats = api_key_manager.get_key_stats(api_key)
                if stats:
                    response.headers['X-RateLimit-Limit'] = str(stats['rate_limit'])
                    response.headers['X-RateLimit-Remaining'] = str(stats['remaining_requests'])
                    response.headers['X-RateLimit-Reset'] = stats['reset_time']
        
        return response
    
    def _make_cors_preflight_response(self):
        """Crear respuesta para preflight CORS"""
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type, X-API-Key, Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET, POST, OPTIONS")
        return response
