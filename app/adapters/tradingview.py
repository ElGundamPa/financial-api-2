import asyncio
import httpx
import json
import re
from typing import List, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from app.adapters.base import ProviderAdapter, InstrumentRef
from app.models import InstrumentSnapshot
from app.utils import get_headers, parse_number, safe_float, pct_change

class TradingViewAdapter(ProviderAdapter):
    name = "tradingview"
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.base_url = "https://www.tradingview.com"
        # URLs específicas actualizadas según los requerimientos
        self.markets = {
            "indices": "https://www.tradingview.com/markets/indices/quotes-all/",
            "crypto": "https://www.tradingview.com/markets/cryptocurrencies/prices-all/",
            "forex": "https://www.tradingview.com/markets/currencies/rates-all/",
            "commodities": "https://www.tradingview.com/markets/futures/quotes-all/",
            "stocks": "https://www.tradingview.com/markets/stocks-usa/market-movers-large-cap/"
        }
        
        # Configuración de límites por categoría (basado en datos reales de TradingView)
        self.expected_counts = {
            "indices": 80,
            "crypto": 3541,
            "forex": 2586,
            "commodities": 429,
            "stocks": 100
        }
    
    async def _make_request(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Hacer petición HTTP con headers optimizados y retry robusto"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        for attempt in range(3):
            try:
                response = await client.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except httpx.TimeoutException:
                print(f"⏰ Timeout en intento {attempt + 1} para {url}")
                if attempt == 2:
                    raise
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Error en intento {attempt + 1}: {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(1)
    
    def _extract_price_from_cell(self, cell_text: str) -> Optional[float]:
        """Extraer precio de una celda con múltiples formatos"""
        if not cell_text:
            return None
            
        # Limpiar el texto
        clean_text = cell_text.strip()
        
        # Patrones de precio más específicos
        price_patterns = [
            r'[\$]?([\d,]+\.?\d*)',  # $123.45 o 123.45
            r'([\d,]+\.?\d*)\s*USD',  # 123.45 USD
            r'([\d,]+\.?\d*)\s*\$',   # 123.45 $
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, clean_text)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    price = float(price_str)
                    # Validar que sea un precio razonable
                    if 0.0001 <= price <= 1000000:
                        return price
                except (ValueError, TypeError):
                    continue
        
        # Fallback: intentar parsear directamente
        try:
            clean_text = clean_text.replace('$', '').replace(',', '').replace('USD', '').strip()
            if clean_text:
                price = float(clean_text)
                if 0.0001 <= price <= 1000000:
                    return price
        except (ValueError, TypeError):
            pass
            
        return None
    
    def _extract_change_from_cell(self, cell_text: str) -> Optional[float]:
        """Extraer cambio porcentual de una celda"""
        if not cell_text:
            return None
            
        clean_text = cell_text.strip()
        
        # Patrones de cambio porcentual
        change_patterns = [
            r'([+-]?\d+\.?\d*)\s*%',  # +1.23% o -1.23%
            r'([+-]?\d+\.?\d*)',       # +1.23 o -1.23
        ]
        
        for pattern in change_patterns:
            match = re.search(pattern, clean_text)
            if match:
                try:
                    change = float(match.group(1))
                    # Validar que sea un cambio razonable
                    if -100 <= change <= 1000:
                        return change
                except (ValueError, TypeError):
                    continue
        
        return None
    
    async def _scrape_tradingview_page(self, client: httpx.AsyncClient, category: str, max_pages: int = 100) -> List[InstrumentRef]:
        """Scrape páginas de TradingView con extracción optimizada"""
        if category not in self.markets:
            return []
        
        url = self.markets[category]
        expected_count = self.expected_counts.get(category, 100)
        
        print(f"🎯 TradingView {category}: Objetivo {expected_count} elementos")
        print(f"📄 URL: {url}")
        
        refs = []
        page = 1
        consecutive_empty_pages = 0
        max_empty_pages = 3  # Parar después de 3 páginas vacías consecutivas
        
        while page <= max_pages and consecutive_empty_pages < max_empty_pages:
            try:
                page_url = url if page == 1 else f"{url}?page={page}"
                print(f"   📄 Página {page}: {page_url}")
                
                response = await self._make_request(client, page_url)
                if not response:
                    print(f"   ❌ Error obteniendo página {page}")
                    consecutive_empty_pages += 1
                    page += 1
                    continue
                
                soup = BeautifulSoup(response, 'html.parser')
                
                # Buscar tabla con selectores más específicos
                table = None
                table_selectors = [
                    'table[class*="table"]',
                    'table[data-role="table"]',
                    '.tv-data-table__table',
                    '.tv-screener__content-table',
                    '.tv-screener-table__table',
                    '.tv-screener__table',
                    'table.tv-screener-table',
                    'table.tv-data-table',
                    'table',
                    '[data-role="table"]',
                    '.tv-screener__content table',
                    '.tv-screener__content-table table'
                ]
                
                for selector in table_selectors:
                    table = soup.select_one(selector)
                    if table:
                        print(f"   ✅ Tabla encontrada con selector: {selector}")
                        break
                
                if not table:
                    print(f"   ❌ No se encontró tabla en página {page}")
                    consecutive_empty_pages += 1
                    page += 1
                    continue
                
                rows = table.find_all('tr')[1:]  # Saltar header
                if not rows:
                    print(f"   ❌ No se encontraron filas en página {page}")
                    consecutive_empty_pages += 1
                    page += 1
                    continue
                
                print(f"   ✅ Encontradas {len(rows)} filas en página {page}")
                
                page_refs = 0
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 4:  # Necesitamos al menos 4 celdas
                        continue
                    
                    # Extraer símbolo de la primera celda
                    symbol_link = cells[0].find('a')
                    if not symbol_link:
                        continue
                    
                    symbol_text = symbol_link.get_text(strip=True)
                    if not symbol_text:
                        continue
                    
                    # Limpiar símbolo (tomar solo la primera parte)
                    symbol = symbol_text.split()[0] if symbol_text else ""
                    name = symbol_text
                    
                    if not symbol or len(symbol) < 1 or len(symbol) > 20:
                        continue
                    
                    # Extraer precio de las celdas 2-4
                    price = None
                    for i in range(2, min(len(cells), 5)):
                        cell_text = cells[i].get_text(strip=True)
                        price = self._extract_price_from_cell(cell_text)
                        if price:
                            break
                    
                    # Extraer cambio porcentual de la celda 3 (Change % 24h)
                    change_pct = None
                    if len(cells) > 3:
                        cell_text = cells[3].get_text(strip=True)
                        change_pct = self._extract_change_from_cell(cell_text)
                    
                    # Solo agregar si tenemos un precio válido
                    if price and price > 0:
                        refs.append(InstrumentRef(
                            symbol=symbol,
                            name=name,
                            exchange=None,
                            currency="USD" if category in ["stocks", "crypto"] else None,
                            category=category,
                            price=price,
                            change_24h_pct=change_pct,
                            change_1h_pct=None  # No disponible en TradingView
                        ))
                        page_refs += 1
                
                print(f"   📊 Página {page}: {page_refs} símbolos extraídos, total: {len(refs)}")
                
                if page_refs == 0:
                    consecutive_empty_pages += 1
                else:
                    consecutive_empty_pages = 0
                
                page += 1
                
                # Rate limiting optimizado
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"   ❌ Error en página {page}: {e}")
                consecutive_empty_pages += 1
                page += 1
                continue
        
        # Validación de integridad
        scraped_count = len(refs)
        success_rate = (scraped_count / expected_count * 100) if expected_count > 0 else 0
        
        print(f"✅ TradingView {category}:")
        print(f"   📊 Esperado: {expected_count}")
        print(f"   📊 Extraído: {scraped_count}")
        print(f"   📊 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"   ✅ EXCELENTE - Extracción exitosa")
        elif success_rate >= 50:
            print(f"   ⚠️  BUENO - Extracción parcial")
        else:
            print(f"   ❌ BAJO - Extracción limitada")
        
        return refs
    
    async def list_refs(self, category: str, cursor: Optional[str], page_size: int) -> Tuple[List[InstrumentRef], Optional[str]]:
        """Listar referencias de instrumentos con scraping optimizado"""
        if category not in self.markets:
            return [], None
        
        print(f"🚀 TradingView {category}: Iniciando scraping...")
        
        # Determinar número máximo de páginas basado en el page_size
        if page_size <= 50:
            max_pages = 5  # Modo rápido para pocos elementos
        elif page_size <= 200:
            max_pages = 20
        else:
            max_pages = 100  # Máximo para obtener todos los elementos
        
        # Usar scraping real
        async with httpx.AsyncClient() as client:
            refs = await self._scrape_tradingview_page(client, category, max_pages)
        
        # Filtrar elementos con precios válidos
        valid_refs = [ref for ref in refs if ref.price > 0]
        
        print(f"🔍 {category}: {len(refs)} total, {len(valid_refs)} con precios válidos")
        
        # Aplicar paginación
        start_idx = 0
        if cursor:
            try:
                cursor_data = json.loads(cursor)
                start_idx = cursor_data.get("offset", 0)
            except:
                pass
        
        end_idx = start_idx + page_size
        paginated_refs = valid_refs[start_idx:end_idx]
        
        # Generar siguiente cursor
        next_cursor = None
        if end_idx < len(valid_refs):
            next_cursor = json.dumps({"offset": end_idx})
        
        print(f"📤 Devolviendo {len(paginated_refs)} elementos (página {start_idx//page_size + 1})")
        
        return paginated_refs, next_cursor
    
    async def fetch_snapshots(self, refs: List[InstrumentRef], hours_window: int) -> List[InstrumentSnapshot]:
        """Obtener snapshots usando datos ya extraídos"""
        snapshots = []
        
        for ref in refs:
            try:
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
        
        print(f"📊 TradingView: {len(snapshots)} snapshots creados")
        return snapshots