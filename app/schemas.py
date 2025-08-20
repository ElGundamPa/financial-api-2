from pydantic import BaseModel, Field
from typing import Literal, Any, Optional, Dict, List
from datetime import datetime


Category = Literal["indices", "crypto", "forex", "futures", "stocks"]


class InstrumentSnapshot(BaseModel):
    provider: Literal["tradingview"]
    category: Category
    symbol: str
    name: Optional[str] = None
    price: float
    change_24h_pct: Optional[float] = None
    price_24h: Optional[float] = None
    ts: datetime
    meta: Dict[str, Any] = Field(default_factory=dict)


class ApiMeta(BaseModel):
    ts: datetime
    provider: Literal["tradingview"]
    category: Category
    limit_per_page: int
    next_cursor: Optional[str] = None
    status: Literal["ok", "degraded", "fail"]


class Price24hResponse(BaseModel):
    meta: ApiMeta
    data: List[InstrumentSnapshot]


