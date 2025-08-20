#!/usr/bin/env python3
"""
Sistema de cache inteligente para la API financiera
"""
import json
import time
import hashlib
from typing import Any, Optional, Dict, Union
from datetime import datetime, timedelta
import os

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class InMemoryCache:
    """Cache en memoria simple"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """Verificar si un item ha expirado"""
        return time.time() > item['expires_at']
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if key in self.cache:
            item = self.cache[key]
            if not self._is_expired(item):
                return item['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Guardar valor en el cache"""
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
    
    def delete(self, key: str) -> None:
        """Eliminar valor del cache"""
        self.cache.pop(key, None)
    
    def clear(self) -> None:
        """Limpiar todo el cache"""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Limpiar items expirados y retornar cantidad eliminada"""
        expired_keys = [
            key for key, item in self.cache.items()
            if self._is_expired(item)
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)

class RedisCache:
    """Cache usando Redis"""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.redis_client = None
        
        if REDIS_AVAILABLE:
            try:
                redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Redis get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Guardar valor en el cache"""
        if not self.redis_client:
            return
        
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def delete(self, key: str) -> None:
        """Eliminar valor del cache"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Redis delete error: {e}")
    
    def clear(self) -> None:
        """Limpiar todo el cache"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.flushdb()
        except Exception as e:
            print(f"Redis clear error: {e}")

class SmartCache:
    """Cache inteligente que usa Redis si está disponible, sino memoria"""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        self.default_ttl = default_ttl
        
        # Intentar usar Redis primero
        self.redis_cache = RedisCache(redis_url, default_ttl)
        self.memory_cache = InMemoryCache(default_ttl)
        
        self.use_redis = self.redis_cache.redis_client is not None
        
        if self.use_redis:
            print("✅ Using Redis cache")
        else:
            print("⚠️ Using in-memory cache (Redis not available)")
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if self.use_redis:
            return self.redis_cache.get(key)
        else:
            return self.memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Guardar valor en el cache"""
        if self.use_redis:
            self.redis_cache.set(key, value, ttl)
        else:
            self.memory_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> None:
        """Eliminar valor del cache"""
        if self.use_redis:
            self.redis_cache.delete(key)
        else:
            self.memory_cache.delete(key)
    
    def clear(self) -> None:
        """Limpiar todo el cache"""
        if self.use_redis:
            self.redis_cache.clear()
        else:
            self.memory_cache.clear()

class CacheManager:
    """Gestor de cache con funcionalidades específicas para datos financieros"""
    
    def __init__(self, cache: Optional[SmartCache] = None):
        self.cache = cache or SmartCache()
        
        # TTL específicos por tipo de dato
        self.ttl_config = {
            'market_data': 60,      # 1 minuto para datos de mercado
            'instrument_list': 300, # 5 minutos para listas de instrumentos
            'provider_health': 120, # 2 minutos para estado de proveedores
            'api_response': 30,     # 30 segundos para respuestas completas
            'user_session': 3600,   # 1 hora para sesiones de usuario
        }
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generar clave de cache consistente"""
        # Crear string único basado en argumentos
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        
        # Añadir kwargs ordenados
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(json.dumps(sorted_kwargs, sort_keys=True))
        
        key_string = "|".join(key_parts)
        
        # Usar hash para claves muy largas
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        return key_string.replace(" ", "_")
    
    def get_market_data(self, provider: str, symbol: str, category: str) -> Optional[Dict[str, Any]]:
        """Obtener datos de mercado del cache"""
        key = self._generate_key("market_data", provider, symbol, category)
        return self.cache.get(key)
    
    def set_market_data(self, provider: str, symbol: str, category: str, data: Dict[str, Any]) -> None:
        """Guardar datos de mercado en cache"""
        key = self._generate_key("market_data", provider, symbol, category)
        ttl = self.ttl_config['market_data']
        
        # Añadir timestamp de cache
        data_with_meta = {
            **data,
            '_cached_at': datetime.now().isoformat(),
            '_cache_key': key
        }
        
        self.cache.set(key, data_with_meta, ttl)
    
    def get_instrument_list(self, provider: str, category: str, page: int = 0) -> Optional[list]:
        """Obtener lista de instrumentos del cache"""
        key = self._generate_key("instrument_list", provider, category, page)
        return self.cache.get(key)
    
    def set_instrument_list(self, provider: str, category: str, data: list, page: int = 0) -> None:
        """Guardar lista de instrumentos en cache"""
        key = self._generate_key("instrument_list", provider, category, page)
        ttl = self.ttl_config['instrument_list']
        self.cache.set(key, data, ttl)
    
    def get_api_response(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Obtener respuesta completa de API del cache"""
        key = self._generate_key("api_response", endpoint, **params)
        return self.cache.get(key)
    
    def set_api_response(self, endpoint: str, params: Dict[str, Any], response: Dict[str, Any]) -> None:
        """Guardar respuesta completa de API en cache"""
        key = self._generate_key("api_response", endpoint, **params)
        ttl = self.ttl_config['api_response']
        
        # Añadir metadata de cache
        response_with_meta = {
            **response,
            '_cached_at': datetime.now().isoformat(),
            '_cache_ttl': ttl
        }
        
        self.cache.set(key, response_with_meta, ttl)
    
    def get_provider_health(self, provider: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de proveedor del cache"""
        key = self._generate_key("provider_health", provider)
        return self.cache.get(key)
    
    def set_provider_health(self, provider: str, status: Dict[str, Any]) -> None:
        """Guardar estado de proveedor en cache"""
        key = self._generate_key("provider_health", provider)
        ttl = self.ttl_config['provider_health']
        
        status_with_meta = {
            **status,
            '_cached_at': datetime.now().isoformat()
        }
        
        self.cache.set(key, status_with_meta, ttl)
    
    def invalidate_provider_data(self, provider: str) -> None:
        """Invalidar todos los datos de un proveedor específico"""
        # En una implementación real, necesitarías un patrón de claves
        # Por ahora, solo limpiamos el estado del proveedor
        key = self._generate_key("provider_health", provider)
        self.cache.delete(key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        stats = {
            'cache_type': 'redis' if self.cache.use_redis else 'memory',
            'ttl_config': self.ttl_config,
            'timestamp': datetime.now().isoformat()
        }
        
        if not self.cache.use_redis and hasattr(self.cache.memory_cache, 'cache'):
            stats['memory_cache_size'] = len(self.cache.memory_cache.cache)
            expired = self.cache.memory_cache.cleanup_expired()
            stats['expired_items_cleaned'] = expired
        
        return stats

# Instancia global del cache manager
cache_manager = CacheManager()
