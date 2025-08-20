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

class FinvizAdapter(ProviderAdapter):
    name = "finviz"
    
    def __init__(self, timeout: int = 8):
        self.timeout = timeout
        self.base_url = "https://finviz.com"
        # URLs específicas actualizadas según los requerimientos
        self.screeners = {
            "forex": "https://finviz.com/forex.ashx",
            "crypto": "https://finviz.com/crypto.ashx",
            "stocks": "https://finviz.com/screener.ashx?v=111&s=ta_mostactive",
            "indices": "https://finviz.com/groups.ashx?g=sector&v=110&o=name",  # Corregir URL
            "commodities": "https://finviz.com/futures.ashx"
        }
    
    async def _make_request(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Hacer petición HTTP con retry simple"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        for attempt in range(3):  # Máximo 3 intentos
            try:
                response = await client.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    follow_redirects=True
                )
                response.raise_for_status()
                
                # Usar response.text que maneja la descompresión automáticamente
                content = response.text
                
                # Verificar que el contenido sea HTML válido
                if '<html' not in content.lower() and '<!doctype' not in content.lower():
                    print(f"   ⚠️ Contenido no parece ser HTML válido")
                    print(f"   📄 Primeros 200 caracteres: {content[:200]}")
                    return None
                
                return content
            except Exception as e:
                print(f"Finviz request failed (attempt {attempt + 1}): {e}")
                if attempt == 2:  # Último intento
                    raise
                await asyncio.sleep(2)  # Esperar 2 segundos antes del retry
    
    async def _scrape_finviz_page(self, client: httpx.AsyncClient, category: str) -> List[InstrumentRef]:
        """Scrapear página de Finviz para obtener instrumentos reales"""
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
            
            print(f"   📄 Contenido HTML obtenido: {len(html_content)} caracteres")
            print(f"   📄 Primeros 500 caracteres: {html_content[:500]}")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            refs = []
            
            # Buscar tabla con múltiples selectores
            table = None
            table_selectors = [
                'table.table-light',
                'table.table-light-cp',
                'table.table-light-wl',
                'table.table-light-row-cp',
                'table.table-light-row-wl',
                'table.table-light-row',
                'table.screener-table',
                'table.quotes-table',
                '#screener-content table',
                '.screener-content table',
                '.screener table',
                'table[class*="table"]',
                'table[class*="screener"]',
                'table[class*="quotes"]',
                'table'
            ]
            
            for selector in table_selectors:
                tables = soup.select(selector)
                print(f"   🔍 Selector '{selector}': {len(tables)} tablas encontradas")
                
                for i, t in enumerate(tables):
                    rows = t.select('tr')
                    cells_in_first_row = len(rows[0].select('td')) if rows else 0
                    print(f"      Tabla {i+1}: {len(rows)} filas, {cells_in_first_row} celdas en primera fila")
                    
                    # Buscar una tabla con múltiples celdas en la primera fila (datos reales)
                    if cells_in_first_row >= 5:
                        table = t
                        print(f"   ✅ Tabla encontrada con selector: {selector} (tabla {i+1})")
                        break
                
                if table:
                    break
            
            if not table:
                print(f"   ❌ No se encontró tabla con datos en {category}")
                return []
            
            # Buscar filas con múltiples selectores
            rows = []
            row_selectors = [
                'tr.table-light-row-cp',
                'tr.table-light-row-wl',
                'tr.table-light-row',
                'tr'
            ]
            
            for selector in row_selectors:
                rows = table.select(selector)
                if len(rows) > 1:  # Más de 1 para excluir solo el header
                    print(f"   ✅ Encontradas {len(rows)} filas con selector: {selector}")
                    break
            
            if len(rows) <= 1:
                print(f"   ❌ No se encontraron filas de datos en {category}")
                return []
            
            # Debug: mostrar estructura de las primeras filas
            print(f"   📊 Estructura de las primeras 3 filas:")
            for i, row in enumerate(rows[:3]):
                cells = row.select('td')
                cell_texts = [cell.get_text(strip=True)[:30] for cell in cells]
                print(f"      Fila {i+1}: {len(cells)} celdas - {cell_texts}")
            
            # Saltar header
            data_rows = rows[1:] if len(rows) > 1 else rows
            print(f"   📊 Procesando {len(data_rows)} filas de datos")
            
            for i, row in enumerate(data_rows):
                cells = row.select('td')
                if len(cells) < 3:
                    print(f"      ⚠️ Fila {i+1}: solo {len(cells)} celdas, saltando")
                    continue
                
                # Extraer símbolo (posición varía según categoría)
                symbol = None
                name = None
                
                if category == "forex":
                    symbol = cells[0].get_text(strip=True) if len(cells) > 0 else None
                    name = cells[1].get_text(strip=True) if len(cells) > 1 else None
                elif category == "crypto":
                    symbol = cells[0].get_text(strip=True) if len(cells) > 0 else None
                    name = cells[1].get_text(strip=True) if len(cells) > 1 else None
                elif category == "stocks":
                    symbol = cells[1].get_text(strip=True) if len(cells) > 1 else cells[0].get_text(strip=True)
                    name = cells[2].get_text(strip=True) if len(cells) > 2 else None
                elif category == "indices":
                    symbol = cells[0].get_text(strip=True) if len(cells) > 0 else None
                    name = cells[1].get_text(strip=True) if len(cells) > 1 else None
                elif category == "commodities":
                    symbol = cells[0].get_text(strip=True) if len(cells) > 0 else None
                    name = cells[1].get_text(strip=True) if len(cells) > 1 else None
                
                if not symbol or len(symbol) < 1:
                    print(f"      ⚠️ Fila {i+1}: símbolo inválido '{symbol}'")
                    continue
                
                # Debug para los primeros elementos
                if i < 5:
                    print(f"      DEBUG Fila {i+1}: {symbol} - Celdas: {[cell.get_text(strip=True)[:20] for cell in cells[:5]]}")
                
                # Buscar precio en las celdas
                price = 0.0
                change_pct = None
                
                # Buscar precio en las celdas 2-6
                for j in range(2, min(len(cells), 7)):
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
                for j in range(3, min(len(cells), 8)):
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
                        change_1h_pct=None  # No disponible en Finviz por defecto
                    ))
                    
                    if i < 5:
                        print(f"      📊 Agregando: {symbol} - Precio: {price}, Cambio: {change_pct}")
                else:
                    if i < 5:
                        print(f"      ❌ No se agregó: {symbol} - Precio: {price}")
            
            print(f"✅ Finviz {category}: extraídos={len(refs)} ✅")
            return refs
            
        except Exception as e:
            print(f"❌ Error scraping Finviz {category}: {e}")
            return []
    
    async def list_refs(self, category: str, cursor: Optional[str], page_size: int) -> Tuple[List[InstrumentRef], Optional[str]]:
        """Listar referencias de instrumentos con scraping real"""
        if category not in self.screeners:
            return [], None
        
        # Usar scraping real en lugar de símbolos predefinidos
        async with httpx.AsyncClient() as client:
            refs = await self._scrape_finviz_page(client, category)
        
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
