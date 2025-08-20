from typing import Protocol, ClassVar, Literal, NamedTuple, List
from datetime import datetime
from app.models import InstrumentSnapshot

Category = Literal["forex", "stocks", "crypto", "indices", "commodities"]

class InstrumentRef(NamedTuple):
    symbol: str
    name: str | None
    exchange: str | None
    currency: str | None
    category: Category
    price: float = 0.0
    change_24h_pct: float | None = None
    change_1h_pct: float | None = None

class ProviderAdapter(Protocol):
    name: ClassVar[str]
    
    async def list_refs(self, category: Category, cursor: str | None, page_size: int) -> tuple[List[InstrumentRef], str | None]:
        """Listar referencias de instrumentos para una categoría"""
        ...
    
    async def fetch_snapshots(self, refs: List[InstrumentRef], hours_window: int) -> List[InstrumentSnapshot]:
        """Obtener snapshots de precios para las referencias"""
        ...
