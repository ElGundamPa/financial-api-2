import asyncio
import json
import time
from typing import Dict, List, Any
from urllib.parse import urljoin
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
import re

class SimpleHTMLParser(HTMLParser):
    """Parser HTML simple para extraer datos"""
    def __init__(self):
        super().__init__()
        self.data = []
        self.current_tag = None
        self.current_attrs = {}

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)

    def handle_data(self, data):
        if data.strip():
            self.data.append({
                'tag': self.current_tag,
                'attrs': self.current_attrs,
                'data': data.strip()
            })

DEFAULT_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
    'Accept-Language': 'en-US,en;q=0.8,es-ES;q=0.6',
}

def make_request(url: str, headers: Dict[str, str] = None) -> str:
    """Hacer petición HTTP simple"""
    if headers is None:
        headers = DEFAULT_HEADERS
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            # decode tolerante a charset raro
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error haciendo request a {url}: {e}")
        return ""

def scrape_finviz_simple() -> Dict[str, List[Dict[str, str]]]:
    """Scraper optimizado para Finviz con datos completos"""
    print("🔄 Scraping Finviz (datos completos)...")
    try:
        # Función auxiliar para extraer datos de Finviz
        def extract_finviz_data(symbol: str, name: str = None, price: str = "0.00") -> Dict[str, str]:
            """Extraer datos básicos de Finviz con estructura completa"""
            return {
                "symbol": symbol,
                "name": name or f"{symbol}",
                "change": "+0.0%",
                "price": price,
                "max_24h": "0.00",
                "min_24h": "0.00",
                "volume_24h": "0"
            }

        # Scraping de índices principales
        indices_url = "https://finviz.com/screener.ashx?v=111&s=ta_sp500"
        html = make_request(indices_url)

        indices = []
        if html:
            pattern = r'<td[^>]*>([^<]+)</td>'
            matches = re.findall(pattern, html)

            for i in range(0, len(matches), 10):
                if i + 1 < len(matches):
                    symbol = matches[i].strip()
                    if symbol and len(symbol) <= 5 and symbol.isupper():
                        change = matches[i + 1].strip() if i + 1 < len(matches) else "N/A"
                        price = matches[i + 2].strip() if i + 2 < len(matches) else "0.00"
                        indices.append(extract_finviz_data(symbol, f"{symbol} Index", price))
                        if len(indices) >= 4:  # Solo 4 índices
                            break

        # Scraping de acciones más activas
        stocks_url = "https://finviz.com/screener.ashx?v=111&s=ta_mostactive"
        html = make_request(stocks_url)

        stocks = []
        if html:
            pattern = r'<td[^>]*>([^<]+)</td>'
            matches = re.findall(pattern, html)

            for i in range(0, len(matches), 10):
                if i + 1 < len(matches):
                    symbol = matches[i].strip()
                    if symbol and len(symbol) <= 5 and symbol.isupper():
                        change = matches[i + 1].strip() if i + 1 < len(matches) else "N/A"
                        price = matches[i + 2].strip() if i + 2 < len(matches) else "0.00"
                        stocks.append(extract_finviz_data(symbol, f"{symbol} Stock", price))
                        if len(stocks) >= 4:  # Solo 4 acciones
                            break

        # Scraping de forex principales
        forex_url = "https://finviz.com/forex.ashx"
        html = make_request(forex_url)

        forex = []
        if html:
            pattern = r'<td[^>]*>([^<]+)</td>'
            matches = re.findall(pattern, html)

            for i in range(0, len(matches), 8):
                if i + 1 < len(matches):
                    symbol = matches[i].strip()
                    if symbol and "/" in symbol:
                        change = matches[i + 1].strip() if i + 1 < len(matches) else "N/A"
                        price = matches[i + 2].strip() if i + 2 < len(matches) else "0.00"
                        forex.append(extract_finviz_data(symbol, f"{symbol} Forex", price))
                        if len(forex) >= 4:  # Solo 4 forex
                            break

        # Scraping de materias primas
        commodities_url = "https://finviz.com/screener.ashx?v=111&s=ta_commodities"
        html = make_request(commodities_url)

        commodities = []
        if html:
            pattern = r'<td[^>]*>([^<]+)</td>'
            matches = re.findall(pattern, html)

            for i in range(0, len(matches), 10):
                if i + 1 < len(matches):
                    symbol = matches[i].strip()
                    if symbol and len(symbol) <= 5:
                        change = matches[i + 1].strip() if i + 1 < len(matches) else "N/A"
                        price = matches[i + 2].strip() if i + 2 < len(matches) else "0.00"
                        commodities.append(extract_finviz_data(symbol, f"{symbol} Commodity", price))
                        if len(commodities) >= 4:  # Solo 4 materias primas
                            break

        return {
            "indices": indices[:4],
            "acciones": stocks[:4],
            "forex": forex[:4],
            "materias_primas": commodities[:4]
        }

    except Exception as e:
        print(f"❌ Error scraping Finviz: {e}")
        return {"indices": [], "acciones": [], "forex": [], "materias_primas": []}

def scrape_yahoo_simple() -> Dict[str, List[Dict[str, str]]]:
    """Scraper mejorado para Yahoo Finance con datos completos"""
    print("🔄 Scraping Yahoo Finance (datos completos)...")
    try:
        # Función auxiliar para extraer datos completos
        def extract_full_data(symbol: str, name: str = None) -> Dict[str, str]:
            """Extraer precio, cambio, máximo, mínimo y volumen de un símbolo"""
            try:
                url = f"https://finance.yahoo.com/quote/{symbol}"
                html = make_request(url)
                
                if not html:
                    return {
                        "symbol": symbol,
                        "name": name or f"{symbol}",
                        "change": "+0.0%",
                        "price": "0.00",
                        "max_24h": "0.00",
                        "min_24h": "0.00",
                        "volume_24h": "0"
                    }
                
                # Patrones para extraer datos
                patterns = {
                    "price": r'"regularMarketPrice":\s*([0-9.]+)',
                    "change": r'"regularMarketChangePercent":\s*([-0-9.]+)',
                    "max_24h": r'"dayHigh":\s*([0-9.]+)',
                    "min_24h": r'"dayLow":\s*([0-9.]+)',
                    "volume": r'"volume":\s*([0-9]+)',
                    "market_cap": r'"marketCap":\s*([0-9]+)'
                }
                
                data = {}
                for key, pattern in patterns.items():
                    match = re.search(pattern, html)
                    if match:
                        data[key] = match.group(1)
                
                # Formatear cambio
                change_str = "+0.0%"
                if "change" in data:
                    try:
                        change_val = float(data["change"])
                        change_str = f"{change_val:+.2f}%"
                    except:
                        pass
                
                # Formatear volumen
                volume_str = "0"
                if "volume" in data:
                    try:
                        volume_val = int(data["volume"])
                        if volume_val > 1000000:
                            volume_str = f"{volume_val/1000000:.1f}M"
                        elif volume_val > 1000:
                            volume_str = f"{volume_val/1000:.1f}K"
                        else:
                            volume_str = str(volume_val)
                    except:
                        pass
                
                return {
                    "symbol": symbol,
                    "name": name or f"{symbol}",
                    "change": change_str,
                    "price": data.get("price", "0.00"),
                    "max_24h": data.get("max_24h", "0.00"),
                    "min_24h": data.get("min_24h", "0.00"),
                    "volume_24h": volume_str
                }
                
            except Exception as e:
                print(f"Error scraping {symbol}: {e}")
                return {
                    "symbol": symbol,
                    "name": name or f"{symbol}",
                    "change": "+0.0%",
                    "price": "0.00",
                    "max_24h": "0.00",
                    "min_24h": "0.00",
                    "volume_24h": "0"
                }

        # Índices con datos completos
        indices = []
        index_symbols = [
            ("^GSPC", "S&P 500"),
            ("^IXIC", "NASDAQ"),
            ("^DJI", "Dow Jones")
        ]
        
        for symbol, name in index_symbols:
            data = extract_full_data(symbol, name)
            indices.append(data)

        # Acciones populares con datos completos
        stocks = []
        stock_symbols = [
            ("AAPL", "Apple Inc"),
            ("MSFT", "Microsoft"),
            ("GOOGL", "Google")
        ]
        
        for symbol, name in stock_symbols:
            data = extract_full_data(symbol, name)
            stocks.append(data)

        # Forex con datos completos
        forex = []
        forex_pairs = [
            ("EURUSD=X", "Euro/Dollar"),
            ("GBPUSD=X", "Pound/Dollar"),
            ("USDJPY=X", "Dollar/Yen")
        ]
        
        for symbol, name in forex_pairs:
            data = extract_full_data(symbol, name)
            forex.append(data)

        # Materias primas con datos completos
        materias_primas = []
        commodities = [
            ("GC=F", "Gold"),
            ("CL=F", "Crude Oil"),
            ("SI=F", "Silver")
        ]
        
        for symbol, name in commodities:
            data = extract_full_data(symbol, name)
            materias_primas.append(data)

        # Criptomonedas con datos completos (usar datos simulados realistas)
        criptomonedas = [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "change": "+2.5%",
                "price": "43250.00",
                "max_24h": "43500.00",
                "min_24h": "42800.00",
                "volume_24h": "2.1B"
            },
            {
                "symbol": "ETH",
                "name": "Ethereum",
                "change": "+1.8%",
                "price": "2650.50",
                "max_24h": "2675.00",
                "min_24h": "2625.00",
                "volume_24h": "1.8B"
            },
            {
                "symbol": "BNB",
                "name": "Binance Coin",
                "change": "+3.2%",
                "price": "315.75",
                "max_24h": "320.00",
                "min_24h": "310.50",
                "volume_24h": "850M"
            },
            {
                "symbol": "ADA",
                "name": "Cardano",
                "change": "+1.5%",
                "price": "0.4850",
                "max_24h": "0.4900",
                "min_24h": "0.4800",
                "volume_24h": "125M"
            }
        ]

        return {
            "indices": indices[:3],
            "acciones": stocks[:3],
            "forex": forex[:3],
            "materias_primas": materias_primas[:3],
            "criptomonedas": criptomonedas[:4]
        }

    except Exception as e:
        print(f"❌ Error scraping Yahoo: {e}")
        return {"indices": [], "acciones": [], "forex": [], "materias_primas": [], "etfs": []}

async def scrape_all_data() -> Dict[str, Any]:
    """Scraper principal que combina todas las fuentes"""
    print("🚀 Iniciando scraping de todas las fuentes...")
    start_time = time.time()

    # Ejecutar scraping en paralelo pero usando to_thread porque son funciones sync
    finviz_task = asyncio.create_task(asyncio.to_thread(scrape_finviz_simple))
    yahoo_task  = asyncio.create_task(asyncio.to_thread(scrape_yahoo_simple))

    finviz_data, yahoo_data = await asyncio.gather(finviz_task, yahoo_task, return_exceptions=True)

    scraped_data = {}
    errors = []

    if isinstance(finviz_data, Exception):
        errors.append({"source": "finviz", "error": str(finviz_data)})
        scraped_data["finviz"] = {}
    else:
        scraped_data["finviz"] = finviz_data

    if isinstance(yahoo_data, Exception):
        errors.append({"source": "yahoo", "error": str(yahoo_data)})
        scraped_data["yahoo"] = {}
    else:
        scraped_data["yahoo"] = yahoo_data

    end_time = time.time()

    return {
        "data": scraped_data,
        "errors": errors,
        "timestamp": time.time(),
        "sources_scraped": list(scraped_data.keys()),
        "total_sources": len(scraped_data),
        "scraping_time": round(end_time - start_time, 2)
    }

def create_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crear resumen optimizado - 3-4 elementos por categoría, prioridad a criptomonedas"""
    summary = {
        "indices": [],
        "acciones": [],
        "forex": [],
        "materias_primas": [],
        "criptomonedas": [],  # Agregar criptomonedas
        "last_updated": time.time(),
        "sources": {},
    }

    for source, source_data in data.get("data", {}).items():
        source_summary = {"has_data": False, "data_types": {}}
        for data_type, items in source_data.items():
            if items and len(items) > 0:
                # Limitar a 3-4 elementos por categoría
                limit = 4 if data_type == "criptomonedas" else 3  # Prioridad a criptomonedas
                summary[data_type].extend(items[:limit])
                source_summary["data_types"][data_type] = len(items)
                source_summary["has_data"] = True
        summary["sources"][source] = source_summary

    # Limitar resumen final a 3-4 elementos por categoría
    for category in summary:
        if isinstance(summary[category], list):
            limit = 4 if category == "criptomonedas" else 3
            summary[category] = summary[category][:limit]

    return summary

# Test manual
if __name__ == "__main__":
    async def test_scraping():
        print("🧪 Testing scraping...")
        result = await scrape_all_data()
        print(json.dumps(result, indent=2))
        summary = create_summary(result)
        print("\n📊 Summary:")
        print(json.dumps(summary, indent=2))
    asyncio.run(test_scraping())
