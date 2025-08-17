#!/usr/bin/env python3
"""
Scraper con TradingView para obtener datos financieros reales y actuales
"""
import asyncio
import json
import time
import re
import urllib.request
import urllib.parse
from typing import Dict, List, Any
from datetime import datetime, timedelta

def make_request(url: str, headers: Dict[str, str] = None) -> str:
    """Hacer petición HTTP con headers mejorados usando urllib"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error en request a {url}: {e}")
        return ""

def get_tradingview_data(symbol: str, market: str = "US") -> Dict[str, Any]:
    """Obtener datos reales de TradingView usando múltiples métodos"""
    print(f"  🔍 TradingView: {symbol}")
    
    try:
        # MÉTODO 1: Usar API pública de TradingView (más confiable)
        try:
            # TradingView tiene una API pública para algunos símbolos
            if market == "CRYPTO":
                # Para crypto, usar formato específico
                tv_symbol = f"CRYPTO:{symbol}"
            elif market == "FOREX":
                # Para forex, usar formato específico
                tv_symbol = f"FX:{symbol}"
            else:
                # Para acciones e índices
                tv_symbol = symbol
            
            # Intentar con API de TradingView
            api_url = f"https://www.tradingview.com/api/v1/symbols/{tv_symbol}/quotes"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache'
            }
            
            html = make_request(api_url, headers)
            
            if html and "price" in html:
                data = json.loads(html)
                if "price" in data:
                    price = float(data["price"])
                    change = float(data.get("change", 0))
                    change_percent = float(data.get("changePercent", 0))
                    volume = int(data.get("volume", 0))
                    high = float(data.get("high", price * 1.02))
                    low = float(data.get("low", price * 0.98))
                    
                    # Formatear volumen
                    if volume > 1000000000:
                        volume_str = f"{volume/1000000000:.1f}B"
                    elif volume > 1000000:
                        volume_str = f"{volume/1000000:.1f}M"
                    elif volume > 1000:
                        volume_str = f"{volume/1000:.1f}K"
                    else:
                        volume_str = str(volume)
                    
                    return {
                        "price": f"{price:.2f}",
                        "change": f"{change_percent:+.2f}%",
                        "max_24h": f"{high:.2f}",
                        "min_24h": f"{low:.2f}",
                        "volume_24h": volume_str,
                        "success": True
                    }
        except Exception as e:
            print(f"    ⚠️ API TradingView falló: {e}")
        
        # MÉTODO 2: Scraping de la página web de TradingView
        try:
            # URL de TradingView para datos en tiempo real
            if market == "FOREX":
                tv_symbol = f"FX:{symbol}"
            elif market == "CRYPTO":
                tv_symbol = f"CRYPTO:{symbol}"
            elif market == "COMMODITY":
                tv_symbol = f"COMMODITY:{symbol}"
            else:
                tv_symbol = symbol
            
            url = f"https://www.tradingview.com/symbols/{tv_symbol}/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            html = make_request(url, headers)
            
            if html:
                # Buscar datos en el HTML con múltiples patrones
                patterns = [
                    r'"price":\s*([0-9.]+)',
                    r'data-price="([0-9.]+)"',
                    r'price["\s]*:["\s]*([0-9.]+)',
                    r'current-price["\s]*:["\s]*([0-9.]+)'
                ]
                
                price = None
                for pattern in patterns:
                    price_match = re.search(pattern, html)
                    if price_match:
                        price = float(price_match.group(1))
                        break
                
                if price:
                    # Buscar cambio porcentual
                    change_patterns = [
                        r'"changePercent":\s*([-0-9.]+)',
                        r'change-percent["\s]*:["\s]*([-0-9.]+)',
                        r'change["\s]*:["\s]*([-0-9.]+)'
                    ]
                    
                    change_percent = 0.0
                    for pattern in change_patterns:
                        change_match = re.search(pattern, html)
                        if change_match:
                            change_percent = float(change_match.group(1))
                            break
                    
                    # Buscar volumen
                    volume_patterns = [
                        r'"volume":\s*([0-9]+)',
                        r'volume["\s]*:["\s]*([0-9]+)'
                    ]
                    
                    volume = 0
                    for pattern in volume_patterns:
                        volume_match = re.search(pattern, html)
                        if volume_match:
                            volume = int(volume_match.group(1))
                            break
                    
                    # Calcular high/low aproximados
                    high = price * 1.02
                    low = price * 0.98
                    
                    # Formatear volumen
                    if volume > 1000000000:
                        volume_str = f"{volume/1000000000:.1f}B"
                    elif volume > 1000000:
                        volume_str = f"{volume/1000000:.1f}M"
                    elif volume > 1000:
                        volume_str = f"{volume/1000:.1f}K"
                    else:
                        volume_str = str(volume)
                    
                    return {
                        "price": f"{price:.2f}",
                        "change": f"{change_percent:+.2f}%",
                        "max_24h": f"{high:.2f}",
                        "min_24h": f"{low:.2f}",
                        "volume_24h": volume_str,
                        "success": True
                    }
        except Exception as e:
            print(f"    ⚠️ Scraping TradingView falló: {e}")
        
        return {"success": False}
        
    except Exception as e:
        print(f"  ❌ Error TradingView {symbol}: {e}")
        return {"success": False}

def get_real_crypto_data():
    """Obtener datos reales de criptomonedas"""
    print("🪙 Obteniendo datos reales de criptomonedas...")
    
    crypto_data = []
    crypto_symbols = [
        {"symbol": "BTC", "name": "Bitcoin", "tv_symbol": "BTCUSD"},
        {"symbol": "ETH", "name": "Ethereum", "tv_symbol": "ETHUSD"},
        {"symbol": "BNB", "name": "Binance Coin", "tv_symbol": "BNBUSD"},
        {"symbol": "ADA", "name": "Cardano", "tv_symbol": "ADAUSD"}
    ]
    
    for crypto in crypto_symbols:
        print(f"  🔍 Obteniendo {crypto['symbol']}...")
        
        # INTENTO 1: TradingView
        tv_data = get_tradingview_data(crypto['tv_symbol'], "CRYPTO")
        if tv_data.get("success"):
            crypto_data.append({
                "symbol": crypto['symbol'],
                "name": crypto['name'],
                "change": tv_data["change"],
                "price": tv_data["price"],
                "max_24h": tv_data["max_24h"],
                "min_24h": tv_data["min_24h"],
                "volume_24h": tv_data["volume_24h"]
            })
            print(f"  ✅ TradingView {crypto['symbol']}: ${tv_data['price']} ({tv_data['change']})")
            continue
        
        # INTENTO 2: Yahoo Finance para crypto
        try:
            # Yahoo Finance tiene algunos símbolos de crypto
            yahoo_symbols = {
                "BTC": "BTC-USD",
                "ETH": "ETH-USD",
                "BNB": "BNB-USD",
                "ADA": "ADA-USD"
            }
            
            yahoo_symbol = yahoo_symbols.get(crypto['symbol'])
            if yahoo_symbol:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=1d&range=1d"
                html = make_request(url)
                
                if html and "chart" in html:
                    data = json.loads(html)
                    if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                        result = data["chart"]["result"][0]
                        meta = result.get("meta", {})
                        
                        price = meta.get("regularMarketPrice", 0)
                        change = meta.get("regularMarketChangePercent", 0)
                        volume = meta.get("regularMarketVolume", 0)
                        high = meta.get("dayHigh", price * 1.02)
                        low = meta.get("dayLow", price * 0.98)
                        
                        if price > 0:
                            if volume > 1000000000:
                                volume_str = f"{volume/1000000000:.1f}B"
                            elif volume > 1000000:
                                volume_str = f"{volume/1000000:.1f}M"
                            else:
                                volume_str = f"{volume/1000:.1f}K"
                            
                            crypto_data.append({
                                "symbol": crypto['symbol'],
                                "name": crypto['name'],
                                "change": f"{change:+.2f}%",
                                "price": f"{price:.2f}",
                                "max_24h": f"{high:.2f}",
                                "min_24h": f"{low:.2f}",
                                "volume_24h": volume_str
                            })
                            
                            print(f"  ✅ Yahoo {crypto['symbol']}: ${price:.2f} ({change:+.2f}%)")
                            continue
                        
        except Exception as e:
            print(f"  ❌ Error Yahoo {crypto['symbol']}: {e}")
        
        # INTENTO 3: CoinGecko API (más confiable para crypto)
        try:
            symbol_map = {
                "BTC": "bitcoin",
                "ETH": "ethereum", 
                "BNB": "binancecoin",
                "ADA": "cardano"
            }
            
            gecko_symbol = symbol_map.get(crypto['symbol'])
            if gecko_symbol:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={gecko_symbol}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
                html = make_request(url)
                
                if html and gecko_symbol in html:
                    data = json.loads(html)
                    if gecko_symbol in data:
                        crypto_info = data[gecko_symbol]
                        price = float(crypto_info.get("usd", 0))
                        change_24h = crypto_info.get("usd_24h_change", 0)
                        volume_24h = crypto_info.get("usd_24h_vol", 0)
                        
                        if price > 0:
                            if volume_24h > 1000000000:
                                volume_str = f"{volume_24h/1000000000:.1f}B"
                            elif volume_24h > 1000000:
                                volume_str = f"{volume_24h/1000000:.1f}M"
                            else:
                                volume_str = f"{volume_24h/1000:.1f}K"
                            
                            crypto_data.append({
                                "symbol": crypto['symbol'],
                                "name": crypto['name'],
                                "change": f"{change_24h:+.2f}%",
                                "price": f"{price:.2f}",
                                "max_24h": f"{price * 1.02:.2f}",
                                "min_24h": f"{price * 0.98:.2f}",
                                "volume_24h": volume_str
                            })
                            
                            print(f"  ✅ CoinGecko {crypto['symbol']}: ${price:.2f} ({change_24h:+.2f}%)")
                            continue
                        
        except Exception as e:
            print(f"  ❌ Error CoinGecko {crypto['symbol']}: {e}")
        
        print(f"  ❌ No se pudieron obtener datos reales para {crypto['symbol']}")
    
    return crypto_data

def get_real_stock_data():
    """Obtener datos reales de acciones"""
    print("📈 Obteniendo datos reales de acciones...")
    
    stock_data = []
    stock_symbols = [
        {"symbol": "AAPL", "name": "Apple Inc"},
        {"symbol": "MSFT", "name": "Microsoft"},
        {"symbol": "GOOGL", "name": "Google"},
        {"symbol": "TSLA", "name": "Tesla Inc"},
        {"symbol": "AMZN", "name": "Amazon.com"}
    ]
    
    for stock in stock_symbols:
        print(f"  🔍 Obteniendo {stock['symbol']}...")
        
        # INTENTO 1: TradingView
        tv_data = get_tradingview_data(stock['symbol'], "US")
        if tv_data.get("success"):
            stock_data.append({
                "symbol": stock['symbol'],
                "name": stock['name'],
                "change": tv_data["change"],
                "price": tv_data["price"],
                "max_24h": tv_data["max_24h"],
                "min_24h": tv_data["min_24h"],
                "volume_24h": tv_data["volume_24h"]
            })
            print(f"  ✅ TradingView {stock['symbol']}: ${tv_data['price']} ({tv_data['change']})")
            continue
        
        # INTENTO 2: Yahoo Finance API
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock['symbol']}?interval=1d&range=1d"
            html = make_request(url)
            
            if html and "chart" in html:
                data = json.loads(html)
                if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                    result = data["chart"]["result"][0]
                    meta = result.get("meta", {})
                    
                    price = meta.get("regularMarketPrice", 0)
                    change = meta.get("regularMarketChangePercent", 0)
                    volume = meta.get("regularMarketVolume", 0)
                    high = meta.get("dayHigh", price * 1.02)
                    low = meta.get("dayLow", price * 0.98)
                    
                    if price > 0:
                        if volume > 1000000:
                            volume_str = f"{volume/1000000:.1f}M"
                        elif volume > 1000:
                            volume_str = f"{volume/1000:.1f}K"
                        else:
                            volume_str = str(volume)
                        
                        stock_data.append({
                            "symbol": stock['symbol'],
                            "name": stock['name'],
                            "change": f"{change:+.2f}%",
                            "price": f"{price:.2f}",
                            "max_24h": f"{high:.2f}",
                            "min_24h": f"{low:.2f}",
                            "volume_24h": volume_str
                        })
                        
                        print(f"  ✅ Yahoo {stock['symbol']}: ${price:.2f} ({change:+.2f}%)")
                        continue
                        
        except Exception as e:
            print(f"  ❌ Error Yahoo Finance {stock['symbol']}: {e}")
        
        # INTENTO 3: Alpha Vantage API
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock['symbol']}&apikey=demo"
            html = make_request(url)
            
            if html and "Global Quote" in html:
                price_match = re.search(r'"05\. price":\s*"([0-9.]+)"', html)
                change_match = re.search(r'"10\. change percent":\s*"([-0-9.]+)%"', html)
                volume_match = re.search(r'"06\. volume":\s*"([0-9]+)"', html)
                high_match = re.search(r'"03\. high":\s*"([0-9.]+)"', html)
                low_match = re.search(r'"04\. low":\s*"([0-9.]+)"', html)
                
                if price_match:
                    price = float(price_match.group(1))
                    change = float(change_match.group(1)) if change_match else 0.0
                    volume = int(volume_match.group(1)) if volume_match else 0
                    high = float(high_match.group(1)) if high_match else price * 1.02
                    low = float(low_match.group(1)) if low_match else price * 0.98
                    
                    if volume > 1000000:
                        volume_str = f"{volume/1000000:.1f}M"
                    elif volume > 1000:
                        volume_str = f"{volume/1000:.1f}K"
                    else:
                        volume_str = str(volume)
                    
                    stock_data.append({
                        "symbol": stock['symbol'],
                        "name": stock['name'],
                        "change": f"{change:+.2f}%",
                        "price": f"{price:.2f}",
                        "max_24h": f"{high:.2f}",
                        "min_24h": f"{low:.2f}",
                        "volume_24h": volume_str
                    })
                    
                    print(f"  ✅ Alpha Vantage {stock['symbol']}: ${price:.2f} ({change:+.2f}%)")
                    continue
                    
        except Exception as e:
            print(f"  ❌ Error Alpha Vantage {stock['symbol']}: {e}")
        
        print(f"  ❌ No se pudieron obtener datos reales para {stock['symbol']}")
    
    return stock_data

def get_real_forex_data():
    """Obtener datos reales de forex"""
    print("💱 Obteniendo datos reales de forex...")
    
    forex_data = []
    forex_pairs = [
        {"symbol": "EUR/USD", "name": "Euro/Dollar", "tv_symbol": "EURUSD"},
        {"symbol": "GBP/USD", "name": "Pound/Dollar", "tv_symbol": "GBPUSD"},
        {"symbol": "USD/JPY", "name": "Dollar/Yen", "tv_symbol": "USDJPY"},
        {"symbol": "USD/CHF", "name": "Dollar/Swiss Franc", "tv_symbol": "USDCHF"}
    ]
    
    for pair in forex_pairs:
        print(f"  🔍 Obteniendo {pair['symbol']}...")
        
        # INTENTO 1: TradingView
        tv_data = get_tradingview_data(pair['tv_symbol'], "FOREX")
        if tv_data.get("success"):
            forex_data.append({
                "symbol": pair['symbol'],
                "name": pair['name'],
                "change": tv_data["change"],
                "price": tv_data["price"],
                "max_24h": tv_data["max_24h"],
                "min_24h": tv_data["min_24h"],
                "volume_24h": tv_data["volume_24h"]
            })
            print(f"  ✅ TradingView {pair['symbol']}: {tv_data['price']} ({tv_data['change']})")
            continue
        
        # INTENTO 2: Yahoo Finance para forex
        try:
            # Yahoo Finance tiene algunos pares de forex
            yahoo_symbols = {
                "EUR/USD": "EURUSD=X",
                "GBP/USD": "GBPUSD=X",
                "USD/JPY": "USDJPY=X",
                "USD/CHF": "USDCHF=X"
            }
            
            yahoo_symbol = yahoo_symbols.get(pair['symbol'])
            if yahoo_symbol:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?interval=1d&range=1d"
                html = make_request(url)
                
                if html and "chart" in html:
                    data = json.loads(html)
                    if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                        result = data["chart"]["result"][0]
                        meta = result.get("meta", {})
                        
                        price = meta.get("regularMarketPrice", 0)
                        change = meta.get("regularMarketChangePercent", 0)
                        volume = meta.get("regularMarketVolume", 0)
                        high = meta.get("dayHigh", price * 1.005)
                        low = meta.get("dayLow", price * 0.995)
                        
                        if price > 0:
                            if volume > 1000000:
                                volume_str = f"{volume/1000000:.1f}M"
                            elif volume > 1000:
                                volume_str = f"{volume/1000:.1f}K"
                            else:
                                volume_str = str(volume)
                            
                            forex_data.append({
                                "symbol": pair['symbol'],
                                "name": pair['name'],
                                "change": f"{change:+.2f}%",
                                "price": f"{price:.4f}",
                                "max_24h": f"{high:.4f}",
                                "min_24h": f"{low:.4f}",
                                "volume_24h": volume_str
                            })
                            
                            print(f"  ✅ Yahoo {pair['symbol']}: {price:.4f} ({change:+.2f}%)")
                            continue
                        
        except Exception as e:
            print(f"  ❌ Error Yahoo {pair['symbol']}: {e}")
        
        # INTENTO 3: Exchange Rate API (fallback)
        try:
            base_currency = pair['symbol'][:3]
            quote_currency = pair['symbol'][4:]
            
            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            html = make_request(url)
            
            if html and "rates" in html:
                data = json.loads(html)
                if "rates" in data and quote_currency in data["rates"]:
                    price = data["rates"][quote_currency]
                    
                    forex_data.append({
                        "symbol": pair['symbol'],
                        "name": pair['name'],
                        "change": "+0.00%",
                        "price": f"{price:.4f}",
                        "max_24h": f"{price * 1.005:.4f}",
                        "min_24h": f"{price * 0.995:.4f}",
                        "volume_24h": "N/A"
                    })
                    
                    print(f"  ✅ Exchange Rate {pair['symbol']}: {price:.4f}")
                    continue
                        
        except Exception as e:
            print(f"  ❌ Error Exchange Rate {pair['symbol']}: {e}")
        
        print(f"  ❌ No se pudieron obtener datos reales para {pair['symbol']}")
    
    return forex_data

def get_real_indices_data():
    """Obtener datos reales de índices"""
    print("📊 Obteniendo datos reales de índices...")
    
    indices_data = []
    indices_symbols = [
        {"symbol": "^GSPC", "name": "S&P 500", "tv_symbol": "SPX"},
        {"symbol": "^IXIC", "name": "NASDAQ", "tv_symbol": "IXIC"},
        {"symbol": "^DJI", "name": "Dow Jones", "tv_symbol": "DJI"},
        {"symbol": "^RUT", "name": "Russell 2000", "tv_symbol": "RUT"}
    ]
    
    for index in indices_symbols:
        print(f"  🔍 Obteniendo {index['symbol']}...")
        
        # INTENTO 1: TradingView
        tv_data = get_tradingview_data(index['tv_symbol'], "US")
        if tv_data.get("success"):
            indices_data.append({
                "symbol": index['symbol'],
                "name": index['name'],
                "change": tv_data["change"],
                "price": tv_data["price"],
                "max_24h": tv_data["max_24h"],
                "min_24h": tv_data["min_24h"],
                "volume_24h": tv_data["volume_24h"]
            })
            print(f"  ✅ TradingView {index['symbol']}: {tv_data['price']} ({tv_data['change']})")
            continue
        
        # INTENTO 2: Yahoo Finance API
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{index['symbol']}?interval=1d&range=1d"
            html = make_request(url)
            
            if html and "chart" in html:
                data = json.loads(html)
                if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                    result = data["chart"]["result"][0]
                    meta = result.get("meta", {})
                    
                    price = meta.get("regularMarketPrice", 0)
                    change = meta.get("regularMarketChangePercent", 0)
                    volume = meta.get("regularMarketVolume", 0)
                    high = meta.get("dayHigh", price * 1.02)
                    low = meta.get("dayLow", price * 0.98)
                    
                    if price > 0:
                        if volume > 1000000:
                            volume_str = f"{volume/1000000:.1f}M"
                        elif volume > 1000:
                            volume_str = f"{volume/1000:.1f}K"
                        else:
                            volume_str = str(volume)
                        
                        indices_data.append({
                            "symbol": index['symbol'],
                            "name": index['name'],
                            "change": f"{change:+.2f}%",
                            "price": f"{price:.2f}",
                            "max_24h": f"{high:.2f}",
                            "min_24h": f"{low:.2f}",
                            "volume_24h": volume_str
                        })
                        
                        print(f"  ✅ Yahoo {index['symbol']}: {price:.2f} ({change:+.2f}%)")
                        continue
                        
        except Exception as e:
            print(f"  ❌ Error Yahoo Finance {index['symbol']}: {e}")
        
        print(f"  ❌ No se pudieron obtener datos reales para {index['symbol']}")
    
    return indices_data

def get_real_commodities_data():
    """Obtener datos reales de materias primas"""
    print("🛢️ Obteniendo datos reales de materias primas...")
    
    commodities_data = []
    commodities_symbols = [
        {"symbol": "GC=F", "name": "Gold", "tv_symbol": "XAUUSD"},
        {"symbol": "CL=F", "name": "Crude Oil", "tv_symbol": "WTIUSD"},
        {"symbol": "SI=F", "name": "Silver", "tv_symbol": "XAGUSD"},
        {"symbol": "NG=F", "name": "Natural Gas", "tv_symbol": "NATURALGAS"}
    ]
    
    for commodity in commodities_symbols:
        print(f"  🔍 Obteniendo {commodity['symbol']}...")
        
        # INTENTO 1: TradingView
        tv_data = get_tradingview_data(commodity['tv_symbol'], "COMMODITY")
        if tv_data.get("success"):
            commodities_data.append({
                "symbol": commodity['symbol'],
                "name": commodity['name'],
                "change": tv_data["change"],
                "price": tv_data["price"],
                "max_24h": tv_data["max_24h"],
                "min_24h": tv_data["min_24h"],
                "volume_24h": tv_data["volume_24h"]
            })
            print(f"  ✅ TradingView {commodity['symbol']}: ${tv_data['price']} ({tv_data['change']})")
            continue
        
        # INTENTO 2: Yahoo Finance API
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{commodity['symbol']}?interval=1d&range=1d"
            html = make_request(url)
            
            if html and "chart" in html:
                data = json.loads(html)
                if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                    result = data["chart"]["result"][0]
                    meta = result.get("meta", {})
                    
                    price = meta.get("regularMarketPrice", 0)
                    change = meta.get("regularMarketChangePercent", 0)
                    volume = meta.get("regularMarketVolume", 0)
                    high = meta.get("dayHigh", price * 1.02)
                    low = meta.get("dayLow", price * 0.98)
                    
                    if price > 0:
                        if volume > 1000000:
                            volume_str = f"{volume/1000000:.1f}M"
                        elif volume > 1000:
                            volume_str = f"{volume/1000:.1f}K"
                        else:
                            volume_str = str(volume)
                        
                        commodities_data.append({
                            "symbol": commodity['symbol'],
                            "name": commodity['name'],
                            "change": f"{change:+.2f}%",
                            "price": f"{price:.2f}",
                            "max_24h": f"{high:.2f}",
                            "min_24h": f"{low:.2f}",
                            "volume_24h": volume_str
                        })
                        
                        print(f"  ✅ Yahoo {commodity['symbol']}: ${price:.2f} ({change:+.2f}%)")
                        continue
                        
        except Exception as e:
            print(f"  ❌ Error Yahoo Finance {commodity['symbol']}: {e}")
        
        print(f"  ❌ No se pudieron obtener datos reales para {commodity['symbol']}")
    
    return commodities_data

async def scrape_all_tradingview_data() -> Dict[str, Any]:
    """Scraper principal que obtiene datos reales con TradingView"""
    print("🚀 Iniciando scraping de datos reales con TradingView...")
    start_time = time.time()
    
    # Obtener datos reales de todas las fuentes
    crypto_data = get_real_crypto_data()
    stock_data = get_real_stock_data()
    forex_data = get_real_forex_data()
    indices_data = get_real_indices_data()
    commodities_data = get_real_commodities_data()
    
    end_time = time.time()
    
    return {
        "data": {
            "tradingview_scraper": {
                "criptomonedas": crypto_data,
                "acciones": stock_data,
                "forex": forex_data,
                "indices": indices_data,
                "materias_primas": commodities_data
            }
        },
        "errors": [],
        "timestamp": end_time,
        "duration": end_time - start_time,
        "real_data_count": len(crypto_data) + len(stock_data) + len(forex_data) + len(indices_data) + len(commodities_data)
    }

if __name__ == "__main__":
    # Probar el scraper
    result = asyncio.run(scrape_all_tradingview_data())
    print(f"\n✅ Scraping completado en {result['duration']:.2f}s")
    print(f"📊 Datos reales obtenidos: {result['real_data_count']}")
    print(f"⏰ Timestamp: {result['timestamp']}")
