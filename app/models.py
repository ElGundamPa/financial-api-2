from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Any, Optional, Dict, List

Category = Literal["forex", "stocks", "crypto", "indices", "commodities"]
Provider = Literal["yahoo", "tradingview", "finviz"]
Status = Literal["ok", "degraded", "fail"]

@dataclass
class InstrumentSnapshot:
    provider: str
    category: Category
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    price: float = 0.0
    change_24h_pct: Optional[float] = None
    change_1h_pct: Optional[float] = None
    ts: datetime = field(default_factory=datetime.now)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para JSON"""
        return {
            "provider": self.provider,
            "category": self.category,
            "symbol": self.symbol,
            "name": self.name,
            "exchange": self.exchange,
            "currency": self.currency,
            "price": self.price,
            "change_24h_pct": self.change_24h_pct,
            "change_1h_pct": self.change_1h_pct,
            "ts": self.ts.isoformat(),
            "meta": self.meta
        }

@dataclass
class ProviderStatus:
    status: Status
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "latency_ms": self.latency_ms
        }

@dataclass
class ScrapeMeta:
    ts: datetime
    providers: List[Provider]
    categories: List[Category]
    limit_per_page: int
    hours_window: int
    status: Dict[Provider, ProviderStatus]
    next_cursor: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ts": self.ts.isoformat(),
            "providers": self.providers,
            "categories": self.categories,
            "limit_per_page": self.limit_per_page,
            "hours_window": self.hours_window,
            "status": {k: v.to_dict() for k, v in self.status.items()},
            "next_cursor": self.next_cursor
        }

@dataclass
class ScrapeResponse:
    meta: ScrapeMeta
    data: List[InstrumentSnapshot]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta": self.meta.to_dict(),
            "data": [snapshot.to_dict() for snapshot in self.data]
        }

@dataclass
class HealthResponse:
    status: str
    providers: Dict[Provider, ProviderStatus]
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "providers": {k: v.to_dict() for k, v in self.providers.items()},
            "version": self.version
        }
