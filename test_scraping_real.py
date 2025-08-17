#!/usr/bin/env python3
"""
Script para probar el scraping real directamente
"""
import requests
import json
import re
import time

def make_request(url: str) -> str:
    """Hacer petición HTTP simple"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.8,es-ES;q=0.6',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return ""

def test_crypto_real():
    """Probar obtención de datos reales de criptomonedas"""
    print("🪙 PROBANDO DATOS REALES DE CRIPTOMONEDAS")
    print("=" * 50)
    
    crypto_symbols = ["bitcoin", "ethereum", "binancecoin", "cardano"]
    
    for symbol in crypto_symbols:
        print(f"\n🔍 Probando {symbol.upper()}:")
        
        # INTENTO 1: CoinGecko API
        try:
            coingecko_url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_24hr_high=true&include_24hr_low=true"
            print(f"  📡 CoinGecko: {coingecko_url}")
            
            html = make_request(coingecko_url)
            if html and symbol in html:
                data = json.loads(html)
                if symbol in data:
                    crypto_data = data[symbol]
                    price = str(crypto_data.get("usd", 0))
                    change_24h = crypto_data.get("usd_24h_change", 0)
                    print(f"  ✅ CoinGecko: ${price} ({change_24h:+.2f}%)")
                    continue
            else:
                print(f"  ❌ CoinGecko: No se obtuvieron datos")
        except Exception as e:
            print(f"  ❌ CoinGecko: Error - {e}")
        
        # INTENTO 2: CoinCap API
        try:
            coincap_url = f"https://api.coincap.io/v2/assets/{symbol}"
            print(f"  📡 CoinCap: {coincap_url}")
            
            html = make_request(coincap_url)
            if html and "data" in html:
                data = json.loads(html)
                if "data" in data:
                    crypto_data = data["data"]
                    price = str(float(crypto_data.get("priceUsd", 0)))
                    change_24h = float(crypto_data.get("changePercent24Hr", 0))
                    print(f"  ✅ CoinCap: ${price} ({change_24h:+.2f}%)")
                    continue
            else:
                print(f"  ❌ CoinCap: No se obtuvieron datos")
        except Exception as e:
            print(f"  ❌ CoinCap: Error - {e}")
        
        # INTENTO 3: CoinMarketCap scraping
        try:
            cmc_url = f"https://coinmarketcap.com/currencies/{symbol}/"
            print(f"  📡 CoinMarketCap: {cmc_url}")
            
            html = make_request(cmc_url)
            if html:
                price_pattern = r'"price":\s*"([0-9,]+\.?[0-9]*)"'
                price_match = re.search(price_pattern, html)
                
                if price_match:
                    price = price_match.group(1).replace(",", "")
                    print(f"  ✅ CoinMarketCap: ${price}")
                    continue
                else:
                    print(f"  ❌ CoinMarketCap: No se encontró precio en HTML")
            else:
                print(f"  ❌ CoinMarketCap: No se obtuvieron datos")
        except Exception as e:
            print(f"  ❌ CoinMarketCap: Error - {e}")
        
        print(f"  ⚠️ Todos los intentos fallaron para {symbol}")

def test_stocks_real():
    """Probar obtención de datos reales de acciones"""
    print("\n📈 PROBANDO DATOS REALES DE ACCIONES")
    print("=" * 50)
    
    stock_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in stock_symbols:
        print(f"\n🔍 Probando {symbol}:")
        
        # INTENTO 1: Alpha Vantage API
        try:
            alpha_vantage_key = "demo"
            alpha_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={alpha_vantage_key}"
            print(f"  📡 Alpha Vantage: {alpha_url}")
            
            html = make_request(alpha_url)
            if html and "Global Quote" in html:
                price_match = re.search(r'"05\. price":\s*"([0-9.]+)"', html)
                change_match = re.search(r'"10\. change percent":\s*"([-0-9.]+)%"', html)
                
                if price_match:
                    price = price_match.group(1)
                    change = change_match.group(1) if change_match else "0.0"
                    print(f"  ✅ Alpha Vantage: ${price} ({change}%)")
                    continue
            else:
                print(f"  ❌ Alpha Vantage: No se obtuvieron datos")
        except Exception as e:
            print(f"  ❌ Alpha Vantage: Error - {e}")
        
        # INTENTO 2: Yahoo Finance
        try:
            yahoo_url = f"https://finance.yahoo.com/quote/{symbol}"
            print(f"  📡 Yahoo Finance: {yahoo_url}")
            
            html = make_request(yahoo_url)
            if html:
                price_pattern = r'"regularMarketPrice":\s*([0-9.]+)'
                price_match = re.search(price_pattern, html)
                
                if price_match:
                    price = price_match.group(1)
                    print(f"  ✅ Yahoo Finance: ${price}")
                    continue
                else:
                    print(f"  ❌ Yahoo Finance: No se encontró precio en HTML")
            else:
                print(f"  ❌ Yahoo Finance: No se obtuvieron datos")
        except Exception as e:
            print(f"  ❌ Yahoo Finance: Error - {e}")
        
        print(f"  ⚠️ Todos los intentos fallaron para {symbol}")

def test_forex_real():
    """Probar obtención de datos reales de forex"""
    print("\n💱 PROBANDO DATOS REALES DE FOREX")
    print("=" * 50)
    
    forex_pairs = ["EURUSD", "GBPUSD", "USDJPY"]
    
    for pair in forex_pairs:
        print(f"\n🔍 Probando {pair}:")
        
        # INTENTO 1: Alpha Vantage API
        try:
            alpha_vantage_key = "demo"
            alpha_url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={pair[:3]}&to_currency={pair[3:]}&apikey={alpha_vantage_key}"
            print(f"  📡 Alpha Vantage: {alpha_url}")
            
            html = make_request(alpha_url)
            if html and "Realtime Currency Exchange Rate" in html:
                price_match = re.search(r'"5\. Exchange Rate":\s*"([0-9.]+)"', html)
                
                if price_match:
                    price = price_match.group(1)
                    print(f"  ✅ Alpha Vantage: {price}")
                    continue
            else:
                print(f"  ❌ Alpha Vantage: No se obtuvieron datos")
        except Exception as e:
            print(f"  ❌ Alpha Vantage: Error - {e}")
        
        print(f"  ⚠️ Todos los intentos fallaron para {pair}")

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DE SCRAPING REAL")
    print("=" * 60)
    
    test_crypto_real()
    test_stocks_real()
    test_forex_real()
    
    print("\n✅ PRUEBAS COMPLETADAS")
