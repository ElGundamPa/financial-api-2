#!/usr/bin/env python3
"""
Utilidades para evitar detección en scraping
"""
import random
import time
import asyncio
from typing import Dict, List, Optional
from fake_useragent import UserAgent
import httpx

class AntiDetection:
    """Clase para manejar técnicas anti-detección"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]
        
    def get_random_user_agent(self) -> str:
        """Obtener un User-Agent aleatorio"""
        try:
            return self.ua.random
        except:
            return random.choice(self.user_agents)
    
    def get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Generar headers realistas"""
        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
        
        if referer:
            headers["Referer"] = referer
            
        return headers
    
    async def random_delay(self, min_delay: float = 1.0, max_delay: float = 5.0):
        """Delay aleatorio para simular comportamiento humano"""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    def check_robots_txt(self, base_url: str) -> str:
        """Verificar robots.txt de un sitio"""
        try:
            robots_url = f"{base_url.rstrip('/')}/robots.txt"
            response = httpx.get(robots_url, timeout=5)
            return response.text
        except Exception as e:
            print(f"Error checking robots.txt for {base_url}: {e}")
            return ""
    
    def is_allowed_by_robots(self, base_url: str, path: str, user_agent: str = "*") -> bool:
        """Verificar si una ruta está permitida por robots.txt"""
        try:
            robots_content = self.check_robots_txt(base_url)
            if not robots_content:
                return True  # Si no hay robots.txt, asumimos que está permitido
            
            # Análisis básico de robots.txt
            lines = robots_content.split('\n')
            current_user_agent = None
            disallowed_paths = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('User-agent:'):
                    current_user_agent = line.split(':', 1)[1].strip()
                elif line.startswith('Disallow:') and (current_user_agent == "*" or current_user_agent == user_agent):
                    disallow_path = line.split(':', 1)[1].strip()
                    disallowed_paths.append(disallow_path)
            
            # Verificar si el path está deshabilitado
            for disallow_path in disallowed_paths:
                if path.startswith(disallow_path):
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Error parsing robots.txt: {e}")
            return True  # En caso de error, permitir acceso

class RateLimiter:
    """Clase para manejar rate limiting"""
    
    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.last_request_time = 0.0
        
    async def wait(self):
        """Esperar el tiempo necesario para respetar el rate limit"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        
        if time_since_last_request < min_interval:
            wait_time = min_interval - time_since_last_request
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()

class SessionManager:
    """Gestor de sesiones HTTP con anti-detección"""
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        self.anti_detection = AntiDetection()
        self.rate_limiter = rate_limiter or RateLimiter(requests_per_second=0.5)
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request con anti-detección"""
        await self.rate_limiter.wait()
        
        # Añadir delay aleatorio
        await self.anti_detection.random_delay(0.5, 2.0)
        
        # Generar headers realistas
        headers = self.anti_detection.get_headers()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        return await self.session.get(url, **kwargs)

# Instancia global para uso fácil
anti_detection = AntiDetection()
