import asyncio
import json
from typing import List, Optional, Tuple
from datetime import datetime
from app.adapters.base import ProviderAdapter, InstrumentRef
from app.models import InstrumentSnapshot

class MockAdapter(ProviderAdapter):
    name = "mock"
    
    def __init__(self, timeout: int = 8):
        self.timeout = timeout
    
    async def list_refs(self, category: str, cursor: Optional[str], page_size: int) -> Tuple[List[InstrumentRef], Optional[str]]:
        """Listar referencias de instrumentos"""
        refs = []
        
        # Datos realistas por categoría
        if category == "forex":
            symbols = [
                ("EURUSD=X", "EUR/USD", "FOREX"),
                ("GBPUSD=X", "GBP/USD", "FOREX"),
                ("USDJPY=X", "USD/JPY", "FOREX"),
                ("USDCHF=X", "USD/CHF", "FOREX"),
                ("AUDUSD=X", "AUD/USD", "FOREX")
            ]
        elif category == "stocks":
            symbols = [
                ("AAPL", "Apple Inc", "NASDAQ"),
                ("MSFT", "Microsoft Corporation", "NASDAQ"),
                ("GOOGL", "Alphabet Inc", "NASDAQ"),
                ("AMZN", "Amazon.com Inc", "NASDAQ"),
                ("TSLA", "Tesla Inc", "NASDAQ"),
                ("META", "Meta Platforms Inc", "NASDAQ"),
                ("NVDA", "NVIDIA Corporation", "NASDAQ"),
                ("NFLX", "Netflix Inc", "NASDAQ")
            ]
        elif category == "crypto":
            symbols = [
                ("BTC-USD", "Bitcoin", "CRYPTO"),
                ("ETH-USD", "Ethereum", "CRYPTO"),
                ("BNB-USD", "Binance Coin", "CRYPTO"),
                ("ADA-USD", "Cardano", "CRYPTO"),
                ("SOL-USD", "Solana", "CRYPTO")
            ]
        elif category == "indices":
            symbols = [
                ("^GSPC", "S&P 500", "SP"),
                ("^IXIC", "NASDAQ Composite", "NASDAQ"),
                ("^DJI", "Dow Jones Industrial Average", "DJ"),
                ("^FTSE", "FTSE 100", "FTSE"),
                ("^N225", "Nikkei 225", "NIKKEI")
            ]
        elif category == "commodities":
            symbols = [
                ("GC=F", "Gold Futures", "COMEX"),
                ("CL=F", "Crude Oil Futures", "NYMEX"),
                ("SI=F", "Silver Futures", "COMEX"),
                ("PL=F", "Platinum Futures", "COMEX"),
                ("PA=F", "Palladium Futures", "COMEX")
            ]
        else:
            return [], None
        
        # Aplicar paginación
        start_idx = 0
        if cursor:
            try:
                cursor_data = json.loads(cursor)
                start_idx = cursor_data.get("offset", 0)
            except:
                pass
        
        end_idx = min(start_idx + page_size, len(symbols))
        current_symbols = symbols[start_idx:end_idx]
        
        for symbol, name, exchange in current_symbols:
            refs.append(InstrumentRef(
                symbol=symbol,
                name=name,
                exchange=exchange,
                currency="USD",
                category=category
            ))
        
        next_cursor = None
        if end_idx < len(symbols):
            next_cursor = json.dumps({"offset": end_idx})
        
        return refs, next_cursor
    
    async def fetch_snapshots(self, refs: List[InstrumentRef], hours_window: int) -> List[InstrumentSnapshot]:
        """Obtener snapshots de precios con datos realistas"""
        if not refs:
            return []
        
        snapshots = []
        
        # Precios realistas actualizados (simulados pero basados en precios reales)
        realistic_prices = {
            # Forex
            "EURUSD=X": {"price": 1.0850, "change": -0.25},
            "GBPUSD=X": {"price": 1.2650, "change": 0.35},
            "USDJPY=X": {"price": 150.25, "change": 0.45},
            "USDCHF=X": {"price": 0.8950, "change": -0.15},
            "AUDUSD=X": {"price": 0.6550, "change": 0.20},
            
            # Stocks
            "AAPL": {"price": 185.50, "change": 1.85},
            "MSFT": {"price": 385.75, "change": 2.15},
            "GOOGL": {"price": 142.25, "change": 1.45},
            "AMZN": {"price": 145.80, "change": 2.80},
            "TSLA": {"price": 245.30, "change": -1.20},
            "META": {"price": 485.90, "change": 3.25},
            "NVDA": {"price": 890.45, "change": 4.50},
            "NFLX": {"price": 485.20, "change": 1.75},
            
            # Crypto
            "BTC-USD": {"price": 43250.00, "change": 2.50},
            "ETH-USD": {"price": 2650.50, "change": 1.80},
            "BNB-USD": {"price": 315.75, "change": 3.20},
            "ADA-USD": {"price": 0.4850, "change": 1.50},
            "SOL-USD": {"price": 98.25, "change": 4.80},
            
            # Indices
            "^GSPC": {"price": 4520.50, "change": 0.85},
            "^IXIC": {"price": 14250.75, "change": 1.25},
            "^DJI": {"price": 35250.00, "change": 0.65},
            "^FTSE": {"price": 7650.25, "change": 0.45},
            "^N225": {"price": 32500.50, "change": 1.15},
            
            # Commodities
            "GC=F": {"price": 2050.50, "change": 0.75},
            "CL=F": {"price": 75.25, "change": -1.85},
            "SI=F": {"price": 23.45, "change": 1.25},
            "PL=F": {"price": 985.75, "change": 0.90},
            "PA=F": {"price": 1250.30, "change": 2.10}
        }
        
        for ref in refs:
            # Obtener datos realistas para el símbolo
            symbol_data = realistic_prices.get(ref.symbol, {"price": 100.0, "change": 0.0})
            
            # Calcular cambios adicionales
            current_price = symbol_data["price"]
            change_24h_pct = symbol_data["change"]
            
            # Simular cambios 1h
            change_1h_pct = change_24h_pct * 0.1 + (asyncio.current_task().get_name().count('b') % 3 - 1) * 0.2
            
            # Simular volumen y market cap
            volume = int(current_price * 1000000 * (0.5 + asyncio.current_task().get_name().count('c') % 10 * 0.1))
            market_cap = int(current_price * 1000000000 * (1 + asyncio.current_task().get_name().count('d') % 5 * 0.2))
            
            snapshot = InstrumentSnapshot(
                provider=self.name,
                category=ref.category,
                symbol=ref.symbol,
                name=ref.name,
                exchange=ref.exchange,
                currency=ref.currency,
                price=current_price,
                change_24h_pct=change_24h_pct,
                change_1h_pct=change_1h_pct,
                ts=datetime.now(),
                meta={
                    "volume": volume,
                    "market_cap": market_cap,
                    "source": "mock_realistic_data"
                }
            )
            snapshots.append(snapshot)
        
        return snapshots
