from typing import Optional, List, Any
from app.utils import encode_cursor, decode_cursor

class PaginationManager:
    """Gestiona la paginación por lotes"""
    
    def __init__(self, limit_per_page: int = 200):
        self.limit_per_page = limit_per_page
        self.current_offset = 0
        self.total_processed = 0
        self.has_more = True
    
    def create_cursor(self, provider: str, category: str, offset: int) -> str:
        """Crear cursor para la siguiente página"""
        data = {
            "provider": provider,
            "category": category,
            "offset": offset,
            "limit": self.limit_per_page
        }
        return encode_cursor(data)
    
    def parse_cursor(self, cursor: Optional[str]) -> Optional[dict[str, Any]]:
        """Parsear cursor existente"""
        if not cursor:
            return None
        return decode_cursor(cursor)
    
    def should_continue(self, items_processed: int) -> bool:
        """Determinar si debe continuar con más páginas"""
        return items_processed >= self.limit_per_page
    
    def get_next_cursor(self, provider: str, category: str, current_offset: int) -> Optional[str]:
        """Obtener cursor para la siguiente página"""
        return self.create_cursor(provider, category, current_offset + self.limit_per_page)
    
    def update_progress(self, items_count: int):
        """Actualizar progreso de paginación"""
        self.total_processed += items_count
        if items_count < self.limit_per_page:
            self.has_more = False
