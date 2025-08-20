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
    
    def __init__(self, timeout: int = 8):
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
    
    async def _make_request(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Hacer petición HTTP con retry simple"""
        headers = get_headers()
        headers.update({
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
        })
        
        for attempt in range(3):  # Máximo 3 intentos
            try:
                response = await client.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"TradingView request failed (attempt {attempt + 1}): {e}")
                if attempt == 2:  # Último intento
                    raise
                await asyncio.sleep(2)  # Esperar 2 segundos antes del retry
    
    async def _scrape_tradingview_page(self, client: httpx.AsyncClient, category: str) -> List[InstrumentRef]:
        """Scrape una página específica de TradingView"""
        if category not in self.markets:
            return []
        
        url = self.markets[category]
        print(f"🎯 Objetivo: extraer símbolos de {category}")
        
        refs = []
        page = 1
        max_pages = 50  # Límite máximo de páginas para evitar loops infinitos
        
        # Si estamos en modo de prueba (pocos elementos), limitar páginas
        if hasattr(self, '_test_mode') and self._test_mode:
            max_pages = 5
        
        while page <= max_pages:
            try:
                page_url = url if page == 1 else f"{url}?page={page}"
                print(f"   📄 Página {page}: {page_url}")
                
                response = await self._make_request(client, page_url)
                if not response:
                    print(f"   ❌ Error obteniendo página {page}")
                    break
                
                soup = BeautifulSoup(response, 'html.parser')
                
                # Buscar tabla principal con múltiples selectores
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
                    '.tv-screener__content table'
                ]
                
                for selector in table_selectors:
                    table = soup.select_one(selector)
                    if table:
                        print(f"   ✅ Tabla encontrada con selector: {selector}")
                        break
                
                if not table:
                    print(f"   ❌ No se encontró tabla en página {page}")
                    # Intentar buscar elementos de lista como fallback
                    list_items = soup.select('.tv-screener__symbol, .tv-data-table__row, [data-symbol-full], tr[data-symbol-full]')
                    if list_items:
                        print(f"   ✅ Encontrados {len(list_items)} elementos de lista")
                        for item in list_items:
                            symbol = item.get('data-symbol-full') or item.get('data-symbol') or item.text.strip()
                            if symbol and len(symbol) > 1 and len(symbol) < 20:
                                refs.append(InstrumentRef(
                                    symbol=symbol,
                                    name=symbol,
                                    exchange=None,
                                    currency="USD" if category in ["stocks", "crypto"] else None,
                                    category=category,
                                    price=0.0,  # Precio por defecto
                                    change_1d_pct=None
                                ))
                        page_refs = len(list_items)
                        print(f"   📊 Página {page}: {page_refs} símbolos extraídos de lista")
                        page += 1
                        continue
                    else:
                        print(f"   ❌ No se encontraron elementos en página {page}")
                        break
                
                rows = table.find_all('tr')[1:]  # Saltar header
                if not rows:
                    print(f"   ❌ No se encontraron filas en página {page}")
                    break
                
                print(f"   ✅ Encontradas {len(rows)} filas en página {page}")
                
                page_refs = 0
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) < 3:
                        continue
                    
                    # Extraer símbolo
                    symbol_link = cells[0].find('a')
                    if not symbol_link:
                        continue
                    
                    symbol = symbol_link.get_text(strip=True).split()[0]
                    name = symbol_link.get_text(strip=True)
                    
                    # Extraer precio de las celdas correctas (no de la primera celda que es el índice)
                    price = 0.0
                    change_pct = None
                    
                    # Buscar precio en las celdas 2-4 (saltando la primera que es el índice)
                    for i in range(2, min(len(cells), 5)):  # Buscar en celdas 2-4
                        cell_text = cells[i].get_text(strip=True)
                        
                        # Debug para los primeros elementos
                        if len(refs) < 10:
                            print(f"      DEBUG Celda {i}: '{cell_text}'")
                        
                        # Buscar precio
                        if not price:
                            # Formato 1: Número simple con USD
                            try:
                                # Limpiar el texto de símbolos de moneda y espacios
                                clean_text = cell_text.replace('USD', '').replace('$', '').replace(',', '').strip()
                                if clean_text and clean_text != cell_text:  # Solo si se limpió algo
                                    potential_price = float(clean_text)
                                    if potential_price > 0 and potential_price < 1000000:  # Precio razonable
                                        price = potential_price
                                        if len(refs) < 10:
                                            print(f"      ✅ Precio encontrado: {price} en celda {i}")
                                        break
                            except:
                                pass
                            
                            # Formato 2: Número con decimales
                            if not price:
                                # Buscar patrones como "123.45" o "1,234.56"
                                price_match = re.search(r'[\d,]+\.?\d*', cell_text)
                                if price_match:
                                    price_str = price_match.group().replace(',', '')
                                    potential_price = safe_float(price_str)
                                    if potential_price and potential_price > 0 and potential_price < 1000000:
                                        price = potential_price
                                        if len(refs) < 10:
                                            print(f"      ✅ Precio encontrado: {price} en celda {i}")
                                        break
                            
                            # Formato 3: Número en formato científico
                            if not price and 'e' in cell_text.lower():
                                try:
                                    potential_price = float(cell_text)
                                    if potential_price > 0 and potential_price < 1000000:
                                        price = potential_price
                                        if len(refs) < 10:
                                            print(f"      ✅ Precio encontrado: {price} en celda {i}")
                                        break
                                except:
                                    pass
                        
                    
                    # Buscar cambio porcentual en la celda 3 (columna "Change % 24h")
                    if len(cells) > 3:
                        cell_text = cells[3].get_text(strip=True)
                        
                        # Debug para los primeros elementos
                        if len(refs) < 10:
                            print(f"      DEBUG Cambio celda 3: '{cell_text}'")
                        
                        # Buscar patrones de cambio porcentual
                        if '%' in cell_text or '+' in cell_text or '-' in cell_text:
                            # Limpiar el texto y extraer el porcentaje
                            clean_text = cell_text.replace('%', '').replace(',', '').strip()
                            
                            # Buscar patrones como "-1.41", "+0.94", etc.
                            change_match = re.search(r'[+-]?\d+\.?\d*', clean_text)
                            if change_match:
                                try:
                                    change_pct = float(change_match.group())
                                    if len(refs) < 10:
                                        print(f"      ✅ Cambio encontrado: {change_pct}% en celda 3")
                                except:
                                    pass
                            
                            # Fallback al método anterior
                            if change_pct is None:
                                change_pct = pct_change(cell_text)
                                if change_pct is not None and len(refs) < 10:
                                    print(f"      ✅ Cambio encontrado (fallback): {change_pct}% en celda 3")
                    
                    if symbol and len(symbol) > 1 and len(symbol) < 20:  # Símbolos razonables
                        # Debug: mostrar información del símbolo que se está agregando
                        if len(refs) < 10:  # Aumentar para ver más elementos
                            print(f"      📊 Agregando: {symbol} - Precio: {price}, Cambio: {change_pct}")
                        
                        refs.append(InstrumentRef(
                             symbol=symbol,
                             name=name,
                             exchange=None,
                             currency="USD" if category in ["stocks", "crypto"] else None,
                             category=category,
                             price=price or 0.0,  # Agregar precio a la referencia
                             change_24h_pct=change_pct,  # Cambio de 24h
                             change_1h_pct=None  # No disponible en TradingView por defecto
                         ))
                        page_refs += 1
                
                print(f"   📊 Página {page}: {page_refs} símbolos extraídos, total acumulado: {len(refs)}")
                
                # Si no encontramos nuevos símbolos en esta página, probablemente hemos terminado
                if page_refs == 0:
                    print(f"   ⚠️ No se encontraron nuevos símbolos en página {page}, terminando")
                    break
                
                page += 1
                
                # Rate limiting entre páginas
                await asyncio.sleep(0.5)  # Reducido de 1 a 0.5 segundos
                
            except Exception as e:
                print(f"   ❌ Error en página {page}: {e}")
                break
        
        print(f"✅ TradingView {category}: extraídos={len(refs)} ✅")
        
        return refs
    
    async def list_refs(self, category: str, cursor: Optional[str], page_size: int) -> Tuple[List[InstrumentRef], Optional[str]]:
        """Listar referencias de instrumentos con scraping real"""
        if category not in self.markets:
            return [], None
        
        # Activar modo de prueba si se solicita un número pequeño de elementos
        if page_size <= 20:
            self._test_mode = True
            print(f"🔍 Modo de prueba activado para {page_size} elementos")
        else:
            self._test_mode = False
        
        # Usar scraping real en lugar de símbolos predefinidos
        async with httpx.AsyncClient() as client:
            refs = await self._scrape_tradingview_page(client, category)
        
        # Debug: mostrar los primeros 10 elementos antes del filtro
        print(f"🔍 DEBUG: Antes del filtro - {len(refs)} elementos")
        for i, ref in enumerate(refs[:10]):
            change_str = f"{ref.change_24h_pct:.2f}%" if ref.change_24h_pct is not None else "N/A"
            print(f"   {i+1}. {ref.symbol}: ${ref.price:.2f} ({change_str})")
        
        # Filtrar elementos con precios válidos
        valid_refs = [ref for ref in refs if ref.price > 0]
        
        print(f"🔍 {category}: {len(refs)} total, {len(valid_refs)} con precios válidos")
        
        # Debug: mostrar los primeros 10 elementos después del filtro
        print(f"🔍 DEBUG: Después del filtro - {len(valid_refs)} elementos")
        for i, ref in enumerate(valid_refs[:10]):
            change_str = f"{ref.change_24h_pct:.2f}%" if ref.change_24h_pct is not None else "N/A"
            print(f"   {i+1}. {ref.symbol}: ${ref.price:.2f} ({change_str})")
        
        # Aplicar paginación a los elementos válidos
        start_idx = 0
        if cursor:
            try:
                cursor_data = json.loads(cursor)
                start_idx = cursor_data.get("offset", 0)
            except:
                pass
        
        end_idx = start_idx + page_size
        paginated_refs = valid_refs[start_idx:end_idx]
        
        # Debug: mostrar los elementos que se van a devolver
        print(f"🔍 DEBUG: Elementos a devolver (paginados): {len(paginated_refs)}")
        for i, ref in enumerate(paginated_refs[:5]):
            change_str = f"{ref.change_24h_pct:.2f}%" if ref.change_24h_pct is not None else "N/A"
            print(f"   {i+1}. {ref.symbol}: ${ref.price:.2f} ({change_str})")
        
        # Generar siguiente cursor
        next_cursor = None
        if end_idx < len(valid_refs):
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