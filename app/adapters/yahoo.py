import asyncio
import httpx
import json
import random
from typing import List, Optional, Tuple
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.adapters.base import ProviderAdapter, InstrumentRef
from app.models import InstrumentSnapshot
from app.utils import get_headers, parse_number, safe_float, pct_change
from bs4 import BeautifulSoup

class YahooAdapter(ProviderAdapter):
    name = "yahoo"
    
    def __init__(self, timeout: int = 8):
        self.timeout = timeout
        self.base_url = "https://finance.yahoo.com"
        # URLs específicas actualizadas según los requerimientos
        self.screeners = {
            "forex": "https://finance.yahoo.com/currencies",
            "stocks": "https://finance.yahoo.com/screener/predefined/most_actives",
            "crypto": "https://finance.yahoo.com/cryptocurrencies",
            "indices": "https://finance.yahoo.com/world-indices",
            "commodities": "https://finance.yahoo.com/commodities"
        }
        
        # Headers específicos para Yahoo Finance
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError))
    )
    async def _make_request(self, client: httpx.AsyncClient, url: str, params: dict = None) -> Optional[str]:
        """Hacer petición HTTP con retry y rate limiting"""
        # Delay aleatorio adicional
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Usar headers específicos de Yahoo
        headers = self.headers.copy()
        
        try:
            response = await client.get(
                url, 
                params=params,
                headers=headers, 
                timeout=self.timeout,
                follow_redirects=True
            )
            
            # Manejar códigos de estado específicos
            if response.status_code == 429:
                print("⚠️ Yahoo Finance rate limit hit - waiting longer")
                await asyncio.sleep(random.uniform(5, 15))
                raise httpx.HTTPStatusError("Rate limited", request=response.request, response=response)
            
            response.raise_for_status()
            return response.text
                
        except httpx.HTTPStatusError as e:
            print(f"Yahoo HTTP error {e.response.status_code}: {e}")
            # Para 404, no reintentar
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            print(f"Yahoo request error: {e}")
            raise
    
    async def _scrape_yahoo_page(self, client: httpx.AsyncClient, category: str) -> List[InstrumentRef]:
        """Scrapear página de Yahoo Finance para obtener instrumentos reales"""
        url = self.screeners.get(category)
        if not url:
            print(f"⚠️ URL no encontrada para categoría: {category}")
            return []
        
        print(f"🎯 Objetivo: extraer símbolos de {category} desde {url}")
        
        try:
            html_content = await self._make_request(client, url)
            if not html_content:
                print(f"⚠️ No se pudo obtener contenido de {url}")
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            refs = []
            
            # Buscar tabla con múltiples selectores
            table = None
            table_selectors = [
                'table[data-test="fin-table"]',
                'table[class*="table"]',
                'table[class*="W(100%)"]',
                'table',
                '[data-test="fin-table"]',
                '.fin-table'
            ]
            
            for selector in table_selectors:
                table = soup.select_one(selector)
                if table:
                    print(f"   ✅ Tabla encontrada con selector: {selector}")
                    break
            
            if not table:
                print(f"   ❌ No se encontró tabla en {category}")
                # Intentar buscar elementos de lista como fallback
                list_items = soup.select('[data-test="quoteLink"], .quote-link, a[href*="/quote/"]')
                if list_items:
                    print(f"   ✅ Encontrados {len(list_items)} elementos de lista")
                    for item in list_items:
                        symbol = item.get_text(strip=True)
                        if symbol and len(symbol) > 1 and len(symbol) < 20:
                            refs.append(InstrumentRef(
                                symbol=symbol,
                                name=symbol,
                                exchange=None,
                                currency="USD" if category in ["stocks", "crypto"] else None,
                                category=category,
                                price=0.0,  # Precio por defecto
                                change_24h_pct=None,
                                change_1h_pct=None
                            ))
                    print(f"   📊 {len(refs)} símbolos extraídos de lista")
                    return refs
                else:
                    print(f"   ❌ No se encontraron elementos en {category}")
                    return []
            
            # Buscar filas
            rows = table.select('tr')
            if len(rows) <= 1:
                print(f"   ❌ No se encontraron filas de datos en {category}")
                return []
            
            # Saltar header
            data_rows = rows[1:] if len(rows) > 1 else rows
            print(f"   📊 Procesando {len(data_rows)} filas de datos")
            
            for i, row in enumerate(data_rows):
                cells = row.select('td')
                if len(cells) < 3:
                    continue
                
                # Extraer símbolo (posición varía según categoría)
                symbol = None
                name = None
                
                # Buscar enlace de símbolo
                symbol_link = row.select_one('a[href*="/quote/"]') or row.select_one('[data-test="quoteLink"]')
                if symbol_link:
                    symbol = symbol_link.get_text(strip=True)
                    name = symbol
                else:
                    # Fallback: usar primera celda
                    symbol = cells[0].get_text(strip=True) if len(cells) > 0 else None
                    name = cells[1].get_text(strip=True) if len(cells) > 1 else None
                
                if not symbol or len(symbol) < 1:
                    continue
                
                # Buscar precio en las celdas
                price = 0.0
                change_pct = None
                
                # Debug para los primeros elementos
                if i < 5:
                    print(f"      DEBUG Fila {i+1}: {symbol} - Celdas: {[cell.get_text(strip=True)[:20] for cell in cells[:5]]}")
                
                # Buscar precio en las celdas 1-6
                for j in range(1, min(len(cells), 7)):
                    cell_text = cells[j].get_text(strip=True)
                    
                    if not price:
                        # Intentar extraer precio
                        try:
                            clean_text = cell_text.replace(',', '').replace('$', '').replace('%', '').strip()
                            potential_price = safe_float(clean_text)
                            if potential_price and potential_price > 0 and potential_price < 1000000:
                                price = potential_price
                                if i < 5:
                                    print(f"      ✅ Precio encontrado: {price} en celda {j}")
                                break
                        except:
                            pass
                
                # Buscar cambio porcentual en las celdas siguientes
                for j in range(2, min(len(cells), 8)):
                    cell_text = cells[j].get_text(strip=True)
                    if '%' in cell_text or '+' in cell_text or '-' in cell_text:
                        change_pct = pct_change(cell_text)
                        if change_pct is not None:
                            if i < 5:
                                print(f"      ✅ Cambio encontrado: {change_pct}% en celda {j}")
                            break
                
                # Agregar referencia si tenemos símbolo y precio
                if symbol and price > 0:
                    refs.append(InstrumentRef(
                        symbol=symbol,
                        name=name if name and name != symbol else None,
                        exchange=None,
                        currency="USD" if category in ["stocks", "crypto"] else None,
                        category=category,
                        price=price,
                        change_24h_pct=change_pct,
                        change_1h_pct=None  # No disponible en Yahoo por defecto
                    ))
                    
                    if i < 5:
                        print(f"      📊 Agregando: {symbol} - Precio: {price}, Cambio: {change_pct}")
            
            print(f"✅ Yahoo {category}: extraídos={len(refs)} ✅")
            return refs
            
        except Exception as e:
            print(f"❌ Error scraping Yahoo {category}: {e}")
            return []
    
    async def list_refs(self, category: str, cursor: Optional[str], page_size: int) -> Tuple[List[InstrumentRef], Optional[str]]:
        """Listar referencias de instrumentos con scraping real"""
        if category not in self.screeners:
            return [], None
        
        # Usar scraping real en lugar de símbolos predefinidos
        async with httpx.AsyncClient() as client:
            refs = await self._scrape_yahoo_page(client, category)
        
        # Aplicar paginación
        start_idx = 0
        if cursor:
            try:
                cursor_data = json.loads(cursor)
                start_idx = cursor_data.get("offset", 0)
            except:
                pass
        
        end_idx = start_idx + page_size
        paginated_refs = refs[start_idx:end_idx]
        
        # Generar siguiente cursor
        next_cursor = None
        if end_idx < len(refs):
            next_cursor = json.dumps({"offset": end_idx})
        
        return paginated_refs, next_cursor
    
    async def fetch_snapshots(self, refs: List[InstrumentRef], hours_window: int) -> List[InstrumentSnapshot]:
        """Obtener snapshots de precios - usar datos ya extraídos de las tablas"""
        snapshots = []
        
        for ref in refs:
            try:
                # Usar los datos ya extraídos de la tabla principal
                snapshot = InstrumentSnapshot(
                    provider=self.name,
                    category=ref.category,
                    symbol=ref.symbol,
                    name=ref.name,
                    exchange=ref.exchange,
                    currency=ref.currency,
                    price=ref.price,
                    change_24h_pct=ref.change_24h_pct,
                    change_1h_pct=ref.change_1h_pct,
                    ts=datetime.now()
                )
                
                snapshots.append(snapshot)
                
            except Exception as e:
                print(f"❌ Error creando snapshot para {ref.symbol}: {e}")
                continue
        
        return snapshots
