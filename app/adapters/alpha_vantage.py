#!/usr/bin/env python3
"""
Adaptador para Alpha Vantage API (datos financieros oficiales)
"""
import asyncio
import httpx
import json
import os
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from app.adapters.base import ProviderAdapter, InstrumentRef
from app.models import InstrumentSnapshot
from app.anti_detection import RateLimiter
from app.validation import validator, cleaner
from app.cache import cache_manager

class AlphaVantageAdapter(ProviderAdapter):
    """Adaptador para Alpha Vantage API"""
    
    name = "alpha_vantage"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 15):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.timeout = timeout
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limiter = RateLimiter(requests_per_second=5/60)  # 5 requests per minute (free tier)
        
        if not self.api_key:
            print("⚠️ Alpha Vantage API key not provided. Using demo key (limited functionality)")
            self.api_key = "demo"
        
        # Símbolos predefinidos por categoría
        self.symbols = {
            "stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX"],
            "forex": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"],
            "crypto": ["BTC", "ETH", "BNB", "ADA", "SOL", "DOT"],
            "indices": [],  # Alpha Vantage no tiene índices gratuitos
            "commodities": []  # Alpha Vantage no tiene commodities gratuitos
        }
    
    async def list_refs(self, category: str, cursor: Optional[str], page_size: int) -> Tuple[List[InstrumentRef], Optional[str]]:
        """Listar referencias de instrumentos"""
        symbols = self.symbols.get(category, [])
        
        if not symbols:
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
        
        refs = []
        for symbol in current_symbols:
            refs.append(InstrumentRef(
                symbol=symbol,
                name=None,  # Se obtendrá en fetch_snapshots
                exchange=None,
                currency="USD",
                category=category
            ))
        
        next_cursor = None
        if end_idx < len(symbols):
            next_cursor = json.dumps({"offset": end_idx})
        
        return refs, next_cursor
    
    async def fetch_snapshots(self, refs: List[InstrumentRef], hours_window: int) -> List[InstrumentSnapshot]:
        """Obtener snapshots de precios usando Alpha Vantage API"""
        if not refs:
            return []
        
        snapshots = []
        
        for ref in refs:
            # Verificar cache primero
            cached_data = cache_manager.get_market_data(self.name, ref.symbol, ref.category)
            if cached_data:
                try:
                    snapshot = InstrumentSnapshot(**cached_data)
                    snapshots.append(snapshot)
                    continue
                except Exception:
                    pass
            
            # Obtener datos frescos
            snapshot_data = await self._fetch_single_snapshot(ref, hours_window)
            if snapshot_data:
                # Validar datos
                if cleaner.validate_instrument_data(snapshot_data, ref.category):
                    snapshot = InstrumentSnapshot(**snapshot_data)
                    snapshots.append(snapshot)
                    
                    # Guardar en cache
                    cache_manager.set_market_data(
                        self.name, 
                        ref.symbol, 
                        ref.category, 
                        snapshot_data
                    )
                else:
                    print(f"⚠️ Alpha Vantage data validation failed for {ref.symbol}")
            
            # Rate limiting entre requests
            await asyncio.sleep(0.5)  # Esperar entre requests
        
        return snapshots
    
    async def _fetch_single_snapshot(self, ref: InstrumentRef, hours_window: int) -> Optional[Dict[str, Any]]:
        """Obtener snapshot de un solo instrumento"""
        await self.rate_limiter.wait()
        
        try:
            if ref.category == "stocks":
                return await self._fetch_stock_data(ref)
            elif ref.category == "forex":
                return await self._fetch_forex_data(ref)
            elif ref.category == "crypto":
                return await self._fetch_crypto_data(ref)
            else:
                print(f"⚠️ Category {ref.category} not supported by Alpha Vantage adapter")
                return None
                
        except Exception as e:
            print(f"Error fetching Alpha Vantage data for {ref.symbol}: {e}")
            return None
    
    async def _fetch_stock_data(self, ref: InstrumentRef) -> Optional[Dict[str, Any]]:
        """Obtener datos de acciones"""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ref.symbol,
            "apikey": self.api_key
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Global Quote" not in data:
                print(f"⚠️ No Global Quote data for {ref.symbol}")
                return None
            
            quote = data["Global Quote"]
            
            # Parsear datos
            current_price = float(quote.get("05. price", 0))
            if current_price <= 0:
                return None
            
            change_pct_str = quote.get("10. change percent", "0%")
            change_24h_pct = validator.sanitize_percentage(change_pct_str)
            
            return {
                "provider": self.name,
                "category": ref.category,
                "symbol": ref.symbol,
                "name": quote.get("01. symbol"),
                "exchange": None,
                "currency": "USD",
                "price": current_price,
                "change_24h_pct": change_24h_pct,
                "change_24h_pct": None,  # No disponible en esta API
                "change_1h_pct": None,   # No disponible en esta API
                "ts": datetime.now(),
                "meta": {
                    "volume": int(quote.get("06. volume", 0)),
                    "high": float(quote.get("03. high", 0)),
                    "low": float(quote.get("04. low", 0)),
                    "open": float(quote.get("02. open", 0)),
                    "previous_close": float(quote.get("08. previous close", 0)),
                    "data_source": "alpha_vantage_global_quote"
                }
            }
    
    async def _fetch_forex_data(self, ref: InstrumentRef) -> Optional[Dict[str, Any]]:
        """Obtener datos de forex"""
        # Para forex, el símbolo debe ser como "EURUSD"
        if len(ref.symbol) != 6:
            return None
        
        from_currency = ref.symbol[:3]
        to_currency = ref.symbol[3:]
        
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Realtime Currency Exchange Rate" not in data:
                print(f"⚠️ No forex data for {ref.symbol}")
                return None
            
            rate_data = data["Realtime Currency Exchange Rate"]
            
            current_price = float(rate_data.get("5. Exchange Rate", 0))
            if current_price <= 0:
                return None
            
            return {
                "provider": self.name,
                "category": ref.category,
                "symbol": f"{from_currency}{to_currency}=X",  # Formato Yahoo
                "name": f"{from_currency}/{to_currency}",
                "exchange": "FOREX",
                "currency": to_currency,
                "price": current_price,
                "change_24h_pct": None,  # No disponible en tiempo real
                "change_1h_pct": None,
                "ts": datetime.now(),
                "meta": {
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "last_refreshed": rate_data.get("6. Last Refreshed"),
                    "data_source": "alpha_vantage_forex"
                }
            }
    
    async def _fetch_crypto_data(self, ref: InstrumentRef) -> Optional[Dict[str, Any]]:
        """Obtener datos de criptomonedas"""
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": ref.symbol,
            "to_currency": "USD",
            "apikey": self.api_key
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Realtime Currency Exchange Rate" not in data:
                print(f"⚠️ No crypto data for {ref.symbol}")
                return None
            
            rate_data = data["Realtime Currency Exchange Rate"]
            
            current_price = float(rate_data.get("5. Exchange Rate", 0))
            if current_price <= 0:
                return None
            
            return {
                "provider": self.name,
                "category": ref.category,
                "symbol": f"{ref.symbol}-USD",
                "name": ref.symbol,
                "exchange": "CRYPTO",
                "currency": "USD",
                "price": current_price,
                "change_24h_pct": None,  # No disponible en tiempo real
                "change_1h_pct": None,
                "ts": datetime.now(),
                "meta": {
                    "from_currency": ref.symbol,
                    "to_currency": "USD",
                    "last_refreshed": rate_data.get("6. Last Refreshed"),
                    "data_source": "alpha_vantage_crypto"
                }
            }
